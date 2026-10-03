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
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

import psycopg

MIN_FILL_SECONDS = 3
RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_REQUESTS = 5
MAX_BODY_BYTES = 64 * 1024
DB_CONNECT_TIMEOUT_SECONDS = 5
MAIL_TIMEOUT_SECONDS = 8

# Mirror the column sizes in db/schema.sql and the inputs' maxlength in
# sections/contact.html; change all three together.
MAX_LENGTHS = {"name": 100, "email": 254, "subject": 150, "message": 5000}

RESEND_URL = "https://api.resend.com/emails"
SUCCESS_MESSAGE = "Message received. I will get back to you soon."

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
LINE_BREAK_RE = re.compile(r"\r\n|\r| | |\x85")


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


def parse_body(content_type: str, raw: bytes) -> dict:
    content_type = content_type.lower()
    if "application/json" in content_type:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            data = None
        if not isinstance(data, dict):
            raise ApiError(400, "Invalid JSON payload")
        return data
    # A no-JS form submit arrives urlencoded.
    if "application/x-www-form-urlencoded" in content_type or content_type == "":
        parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        return {key: values[0] for key, values in parsed.items()}
    raise ApiError(415, "Unsupported payload type")


def validate(data: dict) -> dict:
    fields = {key: clean_text(data.get(key)) for key in MAX_LENGTHS}

    if clean_text(data.get("company_website")):
        raise ApiError(429, "blocked_honeypot")

    try:
        started_at = int(str(data.get("form_started_at") or "0").strip())
    except ValueError:
        started_at = 0
    if started_at <= 0 or time.time() - started_at < MIN_FILL_SECONDS:
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


def send_mail(fields: dict, request_id: str) -> bool:
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
        with urllib.request.urlopen(request, timeout=MAIL_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as error:
        log(f"resend returned HTTP {error.code} for request {request_id}")
    except Exception as error:
        # Any failure here is an email failure, never a 500: the row is stored.
        log(f"resend call failed for request {request_id}: {type(error).__name__}")
    return False


def update_status_best_effort(conn: psycopg.Connection, request_id: str, status: str) -> None:
    # The row is already stored, so a failed status update must not turn the
    # response into an error and invite a duplicate resend.
    try:
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


def handle_submission(fields: dict, ip: str, user_agent: str) -> dict:
    request_id = secrets.token_hex(16)
    ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()

    # autocommit: the row must be durable before the email goes out.
    with psycopg.connect(
        database_url(), autocommit=True, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS
    ) as conn:
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

        if send_mail(fields, request_id):
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
        self.wfile.write(body)

    def method_not_allowed(self) -> None:
        self.respond(405, {"success": False, "message": "Method not allowed"})

    do_GET = do_PUT = do_PATCH = do_DELETE = method_not_allowed

    def client_ip(self) -> str:
        # Vercel sets x-real-ip / x-forwarded-for itself and overwrites any
        # client-supplied value, so they can be trusted here.
        forwarded = self.headers.get("x-real-ip") or self.headers.get("x-forwarded-for") or ""
        return forwarded.split(",")[0].strip() or self.client_address[0]

    def do_POST(self) -> None:
        try:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                raise ApiError(413, "Payload too large")

            data = parse_body(self.headers.get("Content-Type") or "", self.rfile.read(length))
            fields = validate(data)
            user_agent = clean_text((self.headers.get("User-Agent") or "")[:255])
            self.respond(200, handle_submission(fields, self.client_ip(), user_agent))
        except ApiError as error:
            self.respond(error.status, {"success": False, "message": error.message})
        except Exception as error:
            # Class only: driver messages can name the DB user and host.
            log(f"unhandled {type(error).__name__}")
            self.respond(500, {"success": False, "message": "Server error"})
