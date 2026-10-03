# Protfolio-website

Data Engineer portfolio website built as a modular static source with a generated entry page.

## Project Structure

- `index.html`: Generated deployable output. Do not edit this directly for normal content/style updates.
- `src/index.template.html`: Page shell (head, Tailwind config, section placeholders).
- `sections/*.html`: Top-level content fragments.
- `css/design-tokens.css`: Shared custom CSS atoms (`.blueprint-grid`, `.param-input`, selection, icon settings).
- `js/form-handler.js`: Shared client-side form behavior.
- `scripts/build_site.py`: Build script that assembles template + section fragments into `index.html`.

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
- `css/design-tokens.css`
- `js/form-handler.js`

### 2) Rebuild generated output

Run:

```powershell
python scripts/build_site.py
```

If you are using the workspace virtual environment, run:

```powershell
& ".venv/Scripts/python.exe" scripts/build_site.py
```

### 3) Verify

- Confirm `index.html` was regenerated.
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

- Tailwind is loaded via CDN in the template.
- Root `index.html` is generated from source and should be treated as build output.

## Deployment (Vercel)

The site is a Git-connected Vercel project: pushing to `main` deploys production, and every other branch gets a preview deployment (behind Vercel login). There is no build step on Vercel; the committed `index.html` is served as-is.

- `.vercelignore` is an allowlist: only `index.html`, `css/`, `js/`, `favicon.png`, `api/`, `requirements.txt`, and `vercel.json` are deployed. Sources, docs, and the resume PDF stay private. Allow any new runtime file there.
- `vercel.json` sets `cleanUrls`, security headers, and the function's `maxDuration`.

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
5. Redeploy so the function picks up the variables.

### Secrets management

- All secrets live in Vercel environment variables; nothing secret is committed.
- For local `vercel dev`, `vercel env pull .env.local` writes them to a gitignored file.

### API behavior

- Method: `POST` only (anything else is 405)
- Content types: `application/json`, `application/x-www-form-urlencoded` (the no-JS form fallback)
- Required fields: `name`, `email`, `subject`, `message`
- Abuse controls: honeypot (`company_website`), fill-time (`form_started_at`), and 5 requests per 5 minutes per hashed IP
- Once a submission is stored the response is success even if the email fails; check the Vercel runtime logs and rows with `status = 'email_failed'`

### Frontend hook

- `js/form-handler.js` sends payload to `/api/contact`
- Submit button is disabled during request
- Inline status updates are rendered in `#contact-form-status`

### Quick smoke test (PowerShell)

```powershell
$u = "https://hornsloth.com/api/contact"
$ok = @{
	name = "Integration Test"
	email = "you@example.com"
	subject = "Contact API test"
	message = "Testing from PowerShell"
	company_website = ""
	form_started_at = [string]([int](Get-Date -UFormat %s) - 10)
} | ConvertTo-Json

Invoke-RestMethod -Uri $u -Method Post -ContentType "application/json" -Body $ok
```
