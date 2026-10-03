# Protfolio-website

Data Engineer portfolio website built as a modular static source with a generated entry page.

## Project Structure

- `index.html`: Generated deployable output. Do not edit this directly for normal content/style updates.
- `src/index.template.html`: Page shell (head, stylesheet link, section placeholders).
- `src/404.html`: Standalone "page not found" page, copied to root `404.html` by the build.
- `404.html`, `robots.txt`, `sitemap.xml`: Generated deployable output.
- `sections/*.html`: Top-level content fragments.
- `tailwind.config.js`: Tailwind v3.4 config (color tokens, fonts, zeroed radius scale, content globs).
- `css/design-tokens.css`: Tailwind input: `@tailwind` directives, `:root` tokens, and shared custom CSS atoms (`.blueprint-grid`, `.param-input`, selection).
- `css/site.css`: Generated, minified stylesheet the page loads. Do not edit it directly.
- `js/form-handler.js`: Shared client-side form behavior.
- `scripts/build_site.py`: Build script that compiles `css/site.css` with Tailwind, assembles template + section fragments into `index.html`, copies `src/404.html`, and writes `robots.txt` and `sitemap.xml`.

## Section Source Files

- `sections/header-nav.html`
- `sections/hero.html`
- `sections/selected-work.html`
- `sections/philosophy.html`
- `sections/metrics.html`
- `sections/contact.html`
- `sections/footer.html`

Each section file starts with an exact section marker comment and should remain focused on that region only.

## Build Workflow

### 1) Edit source files

Edit one or more of:

- `src/index.template.html`
- `sections/*.html`
- `tailwind.config.js`
- `css/design-tokens.css`
- `js/form-handler.js`

### 2) Rebuild generated output

Requires Python 3 and Node.js with npm (the build runs a pinned `npx --yes tailwindcss@3.4.17`; there is no `package.json`, and the first run downloads the CLI into the npm cache). Run:

```powershell
python scripts/build_site.py
```

If you are using the workspace virtual environment, run:

```powershell
& ".venv/Scripts/python.exe" scripts/build_site.py
```

### 3) Verify

- Confirm the build outputs (`css/site.css`, `index.html`, `404.html`, `robots.txt`, `sitemap.xml`) were regenerated, and commit them (Vercel serves the committed files as-is).
- Serve the repo root (the page uses absolute paths like `/favicon.png`, so `file://` won't work), then check the changed sections at `http://localhost:8765`:

```powershell
python -m http.server 8765
```

## Design System Rules (Summary)

- Use named Tailwind tokens instead of ad hoc colors where possible.
- Keep 0px radius styling.
- Avoid divider-based section separation; use tonal surfaces.
- Use `font-headline`, `font-body`, and `font-mono` consistently.
- Use `param-input` for form controls.

See `DESIGN.md` and `.github` instructions for full project conventions.

## Notes

- Tailwind is compiled at build time into `css/site.css`; the page loads no Tailwind script.
- Root `index.html`, `404.html`, `robots.txt`, `sitemap.xml`, and `css/site.css` are generated from source and should be treated as build output.

## Deployment (Vercel)

The site is a Git-connected Vercel project: pushing to `main` deploys production, and every other branch gets a preview deployment (behind Vercel login). There is no build step on Vercel; the committed build outputs are served as-is. The production domain is `hornsloth.com` (DNS on Vercel; `www` redirects to the apex).

- `.vercelignore` is an allowlist: only `index.html`, `404.html`, `robots.txt`, `sitemap.xml`, `css/` (except the Tailwind input `css/design-tokens.css`), `js/`, `favicon.png`, `api/`, `requirements.txt`, and `vercel.json` are deployed. Sources (including `tailwind.config.js`), docs, and the resume PDF stay private. Allow any new runtime file there.
- `vercel.json` sets `cleanUrls`, the `www` → apex redirect, security headers (including a strict Content-Security-Policy), and the function's `maxDuration`. The CSP allows only same-origin scripts, styles, and fetches, plus Google Fonts (`fonts.googleapis.com` styles, `fonts.gstatic.com` fonts) and `lh3.googleusercontent.com` images. Inline scripts, `<style>` blocks, and `style=` attributes are blocked; add any new external host to the policy.

## Contact Backend (Vercel Function)

The contact form posts to `/api/contact`, a Python Vercel Function (`api/contact.py`) that stores each submission in Postgres and sends a notification email through Resend.

### Backend files

- `api/contact.py`: the endpoint
- `requirements.txt`: function dependencies (`psycopg`)
- `db/schema.sql`: Postgres table definition

### One-time setup

1. **Database:** in the Vercel dashboard, open the project's **Storage** tab and add **Neon** (Postgres) from the Marketplace, connected to all environments. Pick the US East (`us-east-1`) region so it sits next to the function (`iad1`). This injects `DATABASE_URL`.
2. **Schema:** open the Neon SQL editor (from the Storage tab) and run `db/schema.sql`.
3. **Email:** create a Resend account, verify your sending domain (`hornsloth.com`), and create an API key.
4. **Environment variables** (Project → Settings → Environment Variables, all environments):
   - `RESEND_API_KEY`: the Resend key (mark it Sensitive)
   - `CONTACT_MAIL_TO`: where notifications go
   - `CONTACT_MAIL_FROM`: e.g. `Hornsloth Portfolio <contact@hornsloth.com>` (must be on the verified domain)
   - `CONTACT_IP_HASH_SECRET`: a long random string (mark it Sensitive), e.g. from `python -c "import secrets; print(secrets.token_hex(32))"`. It keys the HMAC-SHA256 of the visitor IP used for rate limiting, so hashes stored after the secret is set can't be reversed by hashing every IPv4 address. Rows written before that keep their plain SHA-256 hash and stay reversible. If it is unset the function falls back to plain SHA-256 and logs a warning once per instance. Changing it resets every rate-limit window once.
5. Redeploy so the function picks up the variables.

### Secrets management

- All secrets live in Vercel environment variables; nothing secret is committed.
- For local `vercel dev`, `vercel env pull .env.local` writes them to a gitignored file.

### API behavior

- Method: `POST` only (anything else is 405)
- Content type: `application/json` only; nothing else is validated or stored. No-JS / failed-JS browser submits (a navigation, i.e. `Sec-Fetch-Mode: navigate` or `Accept` containing `text/html`, with a urlencoded, multipart, or empty content type) get a `400` HTML page saying the message was not sent, with an email link and a link back to `/#contact`. Every other non-JSON request, including API clients that forget `-ContentType "application/json"`, gets a `415` JSON error. The page also has a `<noscript>` note with the email address.
- Required fields: `name`, `email`, `subject`, `message`
- Abuse controls: honeypot (`company_website`), fill-time (`form_fill_seconds`), and 5 requests per 5 minutes per IP hash (HMAC-SHA256 keyed by `CONTACT_IP_HASH_SECRET`; plain SHA-256 if it is unset). The raw IP is never stored.
- Once a submission is stored the response is success even if the email fails; check the Vercel runtime logs and rows with `status = 'email_failed'`

### Frontend hook

- `js/form-handler.js` sends payload to `/api/contact`
- Submit button is disabled during request
- Inline status updates are rendered in `#contact-form-status`

### Quick smoke test (PowerShell)

Use the production domain. Until `hornsloth.com` points at Vercel it still reaches the old cPanel host, so use `https://protfolio-website-gray-theta.vercel.app` meanwhile. Preview deployments sit behind Vercel login; test those through the form in a signed-in browser.

```powershell
$u = "https://hornsloth.com/api/contact"
$ok = @{
	name = "Integration Test"
	email = "you@example.com"
	subject = "Contact API test"
	message = "Testing from PowerShell"
	company_website = ""
	form_fill_seconds = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri $u -Method Post -ContentType "application/json" -Body $ok
```
