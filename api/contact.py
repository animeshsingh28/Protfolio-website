"""Contact form endpoint: POST /api/contact (Vercel Python Function).

Flow: validate -> per-IP rate limit -> store the row -> send the notification
email -> mark the row emailed / email_failed. Once the row is stored the
response is 200 success even if the email fails, so visitors don't resend.

Environment (set in the Vercel project):
  DATABASE_URL      Postgres connection string (Neon via the Vercel Marketplace
                    sets it; POSTGRES_URL is accepted as a fallback)
  RESEND_API_KEY    API key for https://resend.com
  CONTACT_MAIL_TO   Where notifications go
  CONTACT_MAIL_FROM Sender, on a domain verified in Resend,
                    e.g. "Hornsloth Portfolio <contact@hornsloth.com>"
  CONTACT_IP_HASH_SECRET
                    Key for the HMAC-SHA256 of the visitor IP used for rate
                    limiting (mark it Sensitive). If unset, a plain SHA-256 is
                    used and a warning is logged once per function instance.
                    Changing it resets every rate-limit window once.

Only application/json bodies are processed; nothing else reaches validation or
the database. A no-JS / failed-JS browser submit (a navigation, i.e.
Sec-Fetch-Mode: navigate or Accept containing text/html, with a urlencoded,
multipart, or empty content type) gets a 400 HTML page saying the message was
not sent, with an email link. Every other non-JSON request is a 415 JSON error.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

import psycopg

MIN_FILL_SECONDS = 3
RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_REQUESTS = 5
MAX_BODY_BYTES = 64 * 1024
# Keep the worst case well under maxDuration (20s in vercel.json): a killed
# invocation after the INSERT leaves the visitor unsure whether it was sent.
# Worst case: connect (5s) + the insert transaction (each statement capped at
# DB_STATEMENT_TIMEOUT_MS) + the mail call, which is cut off
# REQUEST_BUDGET_SECONDS after the request started, + the status update (one
# more statement cap) = about 16s.
DB_CONNECT_TIMEOUT_SECONDS = 5
DB_STATEMENT_TIMEOUT_MS = 2000
MAIL_TIMEOUT_SECONDS = 4
REQUEST_BUDGET_SECONDS = 14
MIN_MAIL_SECONDS = 1.5

# Mirror the column sizes in db/schema.sql and the inputs' maxlength in
# sections/contact.html; change all three together.
MAX_LENGTHS = {"name": 100, "email": 254, "subject": 150, "message": 5000}

RESEND_URL = "https://api.resend.com/emails"
SUCCESS_MESSAGE = "Message received. I will get back to you soon."

# The WHATWG rule browsers use for <input type="email">, plus a dotted domain
# and no leading, trailing, or doubled dots in the local part (RFC 5321; Resend
# rejects those as reply_to, which would silently lose the notification).
EMAIL_RE = re.compile(
    r"^(?!\.)(?!.*\.\.)[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+(?<!\.)"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+\Z"
)
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
LINE_BREAK_RE = re.compile(r"\r\n|\r|\u2028|\u2029|\x85")


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def log(message: str) -> None:
    # Function stdout lands in the Vercel runtime logs.
    print(f"contact: {message}", flush=True)


def clean_text(value: object) -> str:
    text = LINE_BREAK_RE.sub("\n", str(value if value is not None else "").strip())
    return CONTROL_CHARS_RE.sub("", text)


def header_safe(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").strip()


FORM_CONTENT_TYPES = ("application/x-www-form-urlencoded", "multipart/form-data")

# Shown when the native form submit reaches the API (JS off, or form-handler.js
# failed to load or threw). Plain HTML: no inline styles or scripts. It points
# to the Back button rather than linking to /#contact: a fresh page load would
# empty the form, while Back restores the visitor's text so they can copy it.
# The email address also appears in sections/contact.html; change both together.
NO_JS_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Message not sent</title>
</head>
<body>
<main>
<h1>Your message was not sent</h1>
<p>The contact form needs JavaScript, which did not run in your browser, so nothing was delivered.</p>
<p>Please email me instead at <a href="mailto:animeshsingh5770@gmail.com">animeshsingh5770@gmail.com</a>.</p>
<p>Your text is not lost: use your browser's Back button to return to the form, copy your message, and paste it into an email.</p>
</main>
</body>
</html>
""".encode("utf-8")


def is_browser_navigation(sec_fetch_mode: str, accept: str) -> bool:
    # A native form submit is a top-level navigation; fetch() and API clients
    # (curl, urllib, Invoke-RestMethod) are not and don't ask for HTML.
    return sec_fetch_mode.strip().lower() == "navigate" or "text/html" in accept.lower()


def is_form_submit(content_type: str) -> bool:
    # What a browser sends for the plain HTML form (no enctype -> urlencoded).
    content_type = content_type.strip().lower()
    return content_type == "" or any(kind in content_type for kind in FORM_CONTENT_TYPES)


def parse_body(content_type: str, raw: bytes) -> dict:
    if "application/json" in content_type.lower():
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            data = None
        if not isinstance(data, dict):
            raise ApiError(400, "Invalid JSON payload")
        return data
    raise ApiError(415, "Unsupported payload type")


_ip_secret_warned = False


def warn_ip_secret_missing_once() -> None:
    # Once per process, not per request, so the logs stay readable. No lock:
    # at worst two concurrent requests log the line twice.
    global _ip_secret_warned
    if not _ip_secret_warned:
        _ip_secret_warned = True
        log("CONTACT_IP_HASH_SECRET is not set; using unkeyed SHA-256 for the IP hash")


def hash_ip(ip: str) -> str:
    # Keyed, so the stored hash can't be reversed by hashing every IPv4 address.
    secret = (os.environ.get("CONTACT_IP_HASH_SECRET") or "").strip()
    if secret:
        return hmac.new(secret.encode("utf-8"), ip.encode("utf-8"), hashlib.sha256).hexdigest()
    # A privacy setting must not take the form down: fall back, but say so.
    warn_ip_secret_missing_once()
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def validate(data: dict) -> dict:
    fields = {key: clean_text(data.get(key)) for key in MAX_LENGTHS}

    if clean_text(data.get("company_website")):
        raise ApiError(429, "blocked_honeypot")

    # Elapsed time is measured on the client, so the visitor's clock being off
    # from the server's can't block (or pass) a submission.
    try:
        fill_seconds = float(str(data.get("form_fill_seconds") or "0").strip())
    except ValueError:
        fill_seconds = 0
    if not fill_seconds >= MIN_FILL_SECONDS:
        raise ApiError(429, "blocked_fill_time")

    if any(value == "" for value in fields.values()):
        raise ApiError(400, "All fields are required")
    if not EMAIL_RE.match(fields["email"]):
        raise ApiError(400, "Invalid email address")
    if any(len(fields[key]) > limit for key, limit in MAX_LENGTHS.items()):
        raise ApiError(400, "Input exceeds allowed limits")

    return fields


def database_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def send_mail(fields: dict, request_id: str, timeout: float) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    to = os.environ.get("CONTACT_MAIL_TO")
    sender = os.environ.get("CONTACT_MAIL_FROM")
    if not (api_key and to and sender):
        log("mail not configured (RESEND_API_KEY, CONTACT_MAIL_TO, CONTACT_MAIL_FROM)")
        return False

    subject = header_safe(fields["subject"])
    if not re.search(r"[A-Za-z0-9]", subject):
        subject = "New Inquiry"
    body = "\n".join([
        "New contact form submission",
        "",
        f"Name: {header_safe(fields['name'])}",
        f"Email: {fields['email']}",
        f"Subject: {subject}",
        f"Request ID: {request_id}",
        "",
        "Message:",
        fields["message"],
        "",
    ])
    payload = {
        "from": sender,
        "to": [to],
        "reply_to": fields["email"],
        "subject": f"Portfolio Contact | {subject}",
        "text": body,
    }
    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "hornsloth-contact/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as error:
        log(f"resend returned HTTP {error.code} for request {request_id}")
    except Exception as error:
        # Any failure here is an email failure, never a 500: the row is stored.
        log(f"resend call failed for request {request_id}: {type(error).__name__}")
    return False


def send_mail_within(fields: dict, request_id: str, seconds: float) -> bool:
    """send_mail with a hard wall-clock limit. urlopen's timeout covers the
    connect and each read, but not the DNS lookup, so the call runs in a daemon
    thread that is abandoned (counted as failed) when the time is up. An
    abandoned call can still deliver later; the row then says email_failed."""
    result: list[bool] = []
    worker = threading.Thread(
        target=lambda: result.append(
            send_mail(fields, request_id, min(MAIL_TIMEOUT_SECONDS, seconds))
        ),
        daemon=True,
    )
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        log(f"resend call for request {request_id} ran out of time and was abandoned")
        return False
    return bool(result) and result[0]


def limit_statement_time(conn: psycopg.Connection) -> None:
    # Like SET LOCAL: ends with the transaction, so the setting can't leak to
    # other clients through Neon's transaction-mode pooler.
    conn.execute(
        "SELECT set_config('statement_timeout', %s, true)", (f"{DB_STATEMENT_TIMEOUT_MS}ms",)
    )


def update_status_best_effort(conn: psycopg.Connection, request_id: str, status: str) -> None:
    # The row is already stored, so a failed status update must not turn the
    # response into an error and invite a duplicate resend.
    try:
        with conn.transaction():
            limit_statement_time(conn)
            if status == "emailed":
                conn.execute(
                    "UPDATE contact_submissions SET status = %s, email_sent_at = now() WHERE request_id = %s",
                    (status, request_id),
                )
            else:
                conn.execute(
                    "UPDATE contact_submissions SET status = %s WHERE request_id = %s",
                    (status, request_id),
                )
    except Exception as error:
        log(f"status update to {status} failed for request {request_id}: {type(error).__name__}")


def mail_seconds_left(started: float) -> float | None:
    """What is left of the request budget for the mail call, or None when too
    little is left to try (the row is then marked email_failed)."""
    remaining = REQUEST_BUDGET_SECONDS - (time.monotonic() - started)
    return remaining if remaining >= MIN_MAIL_SECONDS else None


def handle_submission(fields: dict, ip: str, user_agent: str, started: float) -> dict:
    request_id = secrets.token_hex(16)
    ip_hash = hash_ip(ip)

    # autocommit outside the transaction block: the row must be committed
    # before the email goes out.
    with psycopg.connect(
        database_url(), autocommit=True, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS
    ) as conn:
        with conn.transaction():
            # Covers the lock wait too, so a stalled pooler or a stuck lock
            # holder fails fast (500, nothing stored) instead of running into
            # maxDuration.
            limit_statement_time(conn)
            # Serialize count-then-insert per IP, so a parallel burst can't
            # all see the same count. Transaction-scoped, so it is safe
            # behind Neon's transaction-mode pooler.
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (ip_hash,))
            recent = conn.execute(
                "SELECT count(*) FROM contact_submissions"
                " WHERE ip_hash = %s AND created_at >= now() - %s * interval '1 second'",
                (ip_hash, RATE_LIMIT_WINDOW_SECONDS),
            ).fetchone()[0]
            if recent >= RATE_LIMIT_MAX_REQUESTS:
                raise ApiError(429, "Too many requests. Please try again later.")

            conn.execute(
                "INSERT INTO contact_submissions"
                " (request_id, name, email, subject, message, ip_hash, user_agent, status)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, 'received')",
                (
                    request_id,
                    fields["name"],
                    fields["email"],
                    fields["subject"],
                    fields["message"],
                    ip_hash,
                    user_agent,
                ),
            )

        seconds = mail_seconds_left(started)
        if seconds is None:
            log(f"skipping email for request {request_id}: request time budget used up")
        if seconds is not None and send_mail_within(fields, request_id, seconds):
            update_status_best_effort(conn, request_id, "emailed")
        else:
            update_status_best_effort(conn, request_id, "email_failed")
            log(f"notification email failed for request {request_id} (row saved with status email_failed)")

    return {"success": True, "message": SUCCESS_MESSAGE, "requestId": request_id}


class handler(BaseHTTPRequestHandler):
    def respond(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        if status == 405:
            self.send_header("Allow", "POST")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def respond_no_js_page(self) -> None:
        # 400, not a redirect: the visitor must see that nothing was sent.
        body = NO_JS_PAGE
        self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def method_not_allowed(self) -> None:
        self.respond(405, {"success": False, "message": "Method not allowed"})

    do_GET = do_HEAD = do_OPTIONS = do_PUT = do_PATCH = do_DELETE = method_not_allowed

    def client_ip(self) -> str:
        # Vercel sets x-real-ip / x-forwarded-for itself and overwrites any
        # client-supplied value, so they can be trusted here.
        forwarded = self.headers.get("x-real-ip") or self.headers.get("x-forwarded-for") or ""
        return forwarded.split(",")[0].strip() or self.client_address[0]

    def do_POST(self) -> None:
        started = time.monotonic()
        try:
            content_type = self.headers.get("Content-Type") or ""
            # Without JS there is no fill-time value, so a native form submit
            # can't pass the bot checks; store nothing and tell the visitor so.
            # Checked before the size check (and without reading the body), so
            # an oversized native submit also gets the readable page rather
            # than a bare JSON 413.
            if is_form_submit(content_type) and is_browser_navigation(
                self.headers.get("Sec-Fetch-Mode") or "", self.headers.get("Accept") or ""
            ):
                self.respond_no_js_page()
                return

            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                raise ApiError(413, "Payload too large")

            # Anything that isn't JSON (API clients included) is a 415 here.
            data = parse_body(content_type, self.rfile.read(length))
            fields = validate(data)
            user_agent = clean_text((self.headers.get("User-Agent") or "")[:255])
            self.respond(200, handle_submission(fields, self.client_ip(), user_agent, started))
        except ApiError as error:
            self.respond(error.status, {"success": False, "message": error.message})
        except Exception as error:
            # Class only: driver messages can name the DB user and host.
            log(f"unhandled {type(error).__name__}")
            self.respond(500, {"success": False, "message": "Server error"})
