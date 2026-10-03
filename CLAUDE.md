# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static Data Engineer portfolio site with a Python contact-form function, hosted on Vercel (project `protfolio-website`, Git-connected: pushes to `main` deploy production, other branches get previews behind Vercel login). Storage is Neon Postgres, email is Resend. No frontend framework, no `package.json` (Tailwind runs through a pinned `npx`), no test suite or linter.

## Commands

```bash
python scripts/build_site.py
```

Compiles `css/design-tokens.css` + `tailwind.config.js` into the minified `css/site.css` (via `npx --yes tailwindcss@<TAILWIND_VERSION>`, pinned to 3.4.17 in the script), then regenerates root `index.html` from the template and section fragments, builds root `404.html` from `src/404.html`, and writes `robots.txt` and `sitemap.xml` from `SITE_URL`. The script is stdlib-only Python 3, so any interpreter works (the repo `.venv` is optional), but it needs Node.js with npm on `PATH`; it exits non-zero if the Tailwind step fails. The first run downloads the CLI into the npm cache. The build is deterministic: rebuilding unchanged sources reproduces every committed output byte-for-byte (the sitemap deliberately has no `<lastmod>` date for this reason) (the CLI bundles its autoprefixer/browserslist data, so output depends only on the pinned version).

`python -m http.server` previews the static page, but the form needs the function: run `vercel dev` (Vercel CLI, with env vars pulled via `vercel env pull`) or test against a preview deployment with the PowerShell smoke test in README.md. `index.html` references `/css/site.css`, `/favicon.png`, and `/api/contact` by absolute path, so the page must be served from a web root — over `file://` the page renders unstyled and the favicon and form submission break. `http.server` does not send the `vercel.json` headers, so CSP problems only show up on a Vercel deployment (or a local server that adds the header).

## Deployment (Vercel)

- No build step on Vercel: the committed build outputs (`index.html`, `css/site.css`, `404.html`, `robots.txt`, `sitemap.xml`) are served as-is, so always rebuild and commit them.
- `.vercelignore` is an allowlist (`/*` then `!index.html`, `!404.html`, `!robots.txt`, `!sitemap.xml`, `!css` minus `/css/design-tokens.css`, `!js`, `!favicon.png`, `!api`, `!requirements.txt`, `!vercel.json`). Everything else — sources (including `tailwind.config.js` and the Tailwind input `css/design-tokens.css`), docs, agent config, the resume PDF — is deliberately not deployed. A new file the live site needs must be allowed there, or it 404s in production.
- Production domain is `hornsloth.com` on Vercel DNS (registrar: Zoho; mail: Zoho Mail India, so MX records are `mx*.zoho.in`, never `.com`). `vercel.json` 308-redirects `www.hornsloth.com` to the apex, matching the canonical URLs.
- `vercel.json`: `cleanUrls`, the www redirect, security headers on every path, and `maxDuration` for `api/contact.py`. Every `.py` file in `api/` becomes a public function, so keep helpers out of `api/`.
- The headers include a strict `Content-Security-Policy`: `default-src 'self'`; scripts, styles, and `connect-src`/`form-action` same-origin only, plus Google Fonts (`style-src https://fonts.googleapis.com`, `font-src https://fonts.gstatic.com`) and `img-src 'self' data: https://lh3.googleusercontent.com` (the philosophy image). No `'unsafe-inline'`: inline `<script>` code, `<style>` blocks, and `style=` attributes are blocked (the JSON-LD `application/ld+json` block is data, not script, so it is unaffected). A new external host for any resource must be added to the matching directive, or the browser blocks it in production. The CSP also blocks the Vercel toolbar (`vercel.live`) on preview deployments, so preview comments don't load there; that is accepted — don't loosen `script-src` for it.

## Build architecture

- `src/index.template.html` is the page shell: `<head>` (title, meta description, canonical, Open Graph tags, and a JSON-LD `Person` block, all using absolute `https://hornsloth.com/` URLs), fonts via `<!-- PARTIAL:fonts -->` (the Google Fonts links live in `src/partials/fonts.html`, shared with the 404 page; they request only the weights in use: Inter 400, Space Grotesk 300/400/700 — the family has no 800/900, so `font-extrabold`/`font-black` render at 700 — and JetBrains Mono 400; add a weight there before using a new one), the Material Symbols icon link, the `/css/site.css` link, and `<!-- SECTION:<name> -->` placeholders. It loads no Tailwind script.
- Tailwind v3.4 is compiled at build time. `tailwind.config.js` (root) holds the theme — color tokens, fonts, the zeroed `borderRadius` scale, `darkMode: "class"`, no plugins — plus `content` globs (`src/**/*.html`, `sections/**/*.html`, `js/**/*.js`) and a `safelist` for the status-line tone classes `js/form-handler.js` adds at runtime. A class that appears only in a file outside those globs, or is assembled from string pieces, is not generated.
- `css/design-tokens.css` is the Tailwind input: the three `@tailwind` directives, `:root` tokens and `::selection` in `@layer base`, `.blueprint-grid` and `.param-input` in `@layer components` (so utilities on the same element still win). `css/site.css` is the generated, minified output; never hand-edit it.
- `sections/<name>.html` fragments are substituted into those placeholders in the order of `SECTION_ORDER` in `scripts/build_site.py`. `header-nav` and `footer` sit outside `<main class="blueprint-grid">`; all other sections are inside it.
- `src/404.html` is a standalone page (its own `<head>` plus the shared `PARTIAL:fonts`, no sections, no JS, `noindex`) that the build writes to root `404.html`; the build replaces every `<!-- PARTIAL:<name> -->` in the template and the 404 page with `src/partials/<name>.html`; Vercel serves it for unknown paths, so every link and asset in it must be an absolute path.
- Root `index.html`, `404.html`, `robots.txt`, `sitemap.xml`, and `css/site.css` are generated but committed, and are the deployed artifacts. Never hand-edit them — edit sources, rebuild, and commit the regenerated files alongside the source change.
- Adding a section requires a new fragment, a placeholder in the template, and an entry in `SECTION_ORDER` (the build raises if a placeholder is missing). Also update the fragment lists in `.github/instructions/section-fragments.instructions.md` and `.github/prompts/*.prompt.md`.
- Each fragment must begin with its exact marker comment — `<!-- Header/nav -->`, `<!-- Hero -->`, `<!-- Selected work -->`, `<!-- Philosophy -->`, `<!-- Metrics -->`, `<!-- Contact -->`, `<!-- Footer -->` — which differ from the `SECTION:` placeholder names. Fragments never contain `<html>`/`<head>`/`<body>`, the Tailwind config, font links, or global `<script>` tags.
- Section structure: `<section>` → `<div class="max-w-7xl mx-auto">` → content.

## Editing scope

- Treat section fragments as hard edit boundaries: a request about one section changes only that fragment unless a template-level or global change is genuinely required. If a request is ambiguous or spans sections, ask; if an edit must touch several fragments, say so explicitly.
- Resume-driven updates use `refrence docs/Animesh's Resume.pdf` (directory name is misspelled) as the source of truth. Change factual text only (names, roles, dates, metrics, skills, links) — never classes, layout, or structure. Facts such as years of experience and employers also appear in the template `<head>` (meta description, `og:description`, JSON-LD), so update them there too. The contact email appears twice in `sections/contact.html` (the contact details and the `<noscript>` note) and once in `api/contact.py` (`NO_JS_PAGE`); change all three together. Where the resume and page conflict, the resume wins; if the resume doesn't support a requested change, stop and say what's missing.

## Design system ("The Kinetic Blueprint" — full spec in DESIGN.md)

Non-negotiable rules:

- 0px radius everywhere: no `rounded-*`, no `border-radius` (the Tailwind config also zeroes the radius scale).
- No dividers/`<hr>` between sections — separate regions with tonal surface shifts (`bg-surface`, `bg-surface-container-low`, `bg-surface-container-lowest`, …).
- Dark mode only (`<html class="dark">`); no light variants.
- Typography: `font-headline` (Space Grotesk, uppercase, tight tracking), `font-body` (Inter), `font-mono` (JetBrains Mono, uppercase, `tracking-widest`) for data/metadata. Metadata labels are `text-[9px]`/`text-[10px]` mono with `tracking-[0.2em]`.
- Use named Tailwind color tokens, not raw hex.
- Form fields use the `.param-input` class — never Tailwind `ring-*`/`border-*` on inputs.
- Icons: `<span aria-hidden="true" class="material-symbols-outlined" data-icon="name">name</span>` (thin stroke via `wght 300`, set by the `@24,300,0,0` part of the font URL; the subset font is static, so CSS `font-variation-settings` has no effect). The icon font is subset: the template's Material Symbols link lists every icon in use in `icon_names=` (alphabetical). A new icon must be added there, or it renders as its literal name. Icon-only links/buttons need an `aria-label`. Buttons get `active:translate-y-1 transition-transform`. No placeholder `href="#"` links.
- Tailwind utilities only. Custom CSS lives solely in `css/design-tokens.css` (`.blueprint-grid`, `.param-input`, `::selection`) — no new CSS files, `<style>` blocks, or inline `style=` (the CSP blocks the last two anyway).

### Color token gotcha

Most tokens are hex values in `tailwind.config.js`. Five — `primary`, `primary-container`, `on-primary-container`, `outline-variant`, `on-background` — are `rgb(var(--token-*) / <alpha-value>)` references whose values live in `:root` of `css/design-tokens.css` as space-separated RGB channels (e.g. `255 87 26`); change those there and keep the channel format.

Opacity modifiers (`border-outline-variant/10`, `hover:border-primary-container/30`) work on every token. Keep the `<alpha-value>` form: a plain `var(--token-*)` color makes Tailwind (v3.4) silently generate **no CSS** for opacity modifiers, and a bare `border` then falls back to Tailwind's default light-gray border. In custom CSS, write `rgb(var(--token-*))` or `rgb(var(--token-*) / N%)`; a bare `var(--token-*)` is not a valid color.

## Contact form backend (`api/`)

Flow: `js/form-handler.js` POSTs JSON to `/api/contact` (`api/contact.py`, a `BaseHTTPRequestHandler` Vercel Function) → validation → rate-limit check and insert into `contact_submissions` (`db/schema.sql`, Postgres) → notification email via the Resend HTTP API → row status updated `received` → `emailed` / `email_failed`. Once the row is stored the API returns 200 success even if the email or the status update fails (the failure goes to the Vercel runtime logs), so visitors don't resend.

- The JS binds to `#contact form`, its `button[type=submit]`, `#contact-form-status`, and hidden `input[name=form_started_at]`, and silently no-ops if any is missing. Field names (`name`, `email`, `subject`, `message`, honeypot `company_website`) must stay in sync across `sections/contact.html`, the JS, and `contact.py`. `form_started_at` holds the client-side start time (`performance.now()`, monotonic) and is never sent; the JS sends the elapsed `form_fill_seconds` instead, so client/server clock skew can't affect the fill-time check.
- Responses are `{success, message, requestId?}`. The JS maps machine codes (`blocked_*`) to plain-language text in `ERROR_MESSAGES` and shows other messages as-is; the status line is upper-cased by CSS, so keep messages sentence case. The JS also validates the `required` fields client-side and sets `aria-invalid` before sending.
- Abuse controls: non-empty honeypot → 429; filled in under `MIN_FILL_SECONDS` → 429; more than `RATE_LIMIT_MAX_REQUESTS` per window per IP hash → 429 (count and insert run under a per-IP `pg_advisory_xact_lock`, so parallel bursts can't slip past). The IP hash is HMAC-SHA256 keyed by `CONTACT_IP_HASH_SECRET`; if that is unset it falls back to plain SHA-256 and logs a warning once per process. Only `application/json` reaches validation or the DB: no-JS / failed-JS browser submits (a navigation — `Sec-Fetch-Mode: navigate` or `Accept` containing `text/html` — with a urlencoded, multipart, or empty content type) get a 400 HTML page (`NO_JS_PAGE`) saying the message was not sent, with an email link; every other non-JSON request → 415 JSON. `sections/contact.html` also has a `<noscript>` email note. Server email validation is the WHATWG `type=email` rule (what the browser checks) plus a dotted domain and no leading/trailing/doubled dots in the local part, which Resend would reject as `reply_to`. The mail call runs in a daemon thread with a hard wall-clock limit (urlopen's timeout doesn't cover DNS) of whatever is left of `REQUEST_BUDGET_SECONDS` measured from request start, so a slow DB wake-up leaves the email skipped (`email_failed`) rather than the invocation killed; an abandoned call that still delivers logs a `late delivery` line with the request id. DB statements are capped by `DB_STATEMENT_TIMEOUT_MS` via transaction-local `set_config` (safe behind Neon's transaction-mode pooler), which only lasts inside an explicit transaction — that is why the insert and the status update each run in `conn.transaction()`; don't remove it. The cap is server-side, so it bounds slow queries and lock waits, not a pooler queue wait or a stalled connection. The IP comes from Vercel's `x-real-ip` / `x-forwarded-for`, which Vercel overwrites, so they can't be spoofed. `MAX_LENGTHS` in `contact.py` mirror `db/schema.sql` column sizes and the inputs' `maxlength` in `sections/contact.html` — change all three together.
- The JS timeout (`REQUEST_TIMEOUT_MS`, 25s) must stay above the function's `maxDuration` in `vercel.json` (20s).
- Config is Vercel environment variables only: `DATABASE_URL` (injected by the Neon Marketplace integration; `POSTGRES_URL` also accepted), `RESEND_API_KEY`, `CONTACT_MAIL_TO`, `CONTACT_MAIL_FROM` (on a Resend-verified domain), `CONTACT_IP_HASH_SECRET` (HMAC key for the IP hash; optional but should be set). Missing mail vars mean rows are stored as `email_failed`; a missing `DATABASE_URL` is a 500.
- Log exception class names only, never messages: driver messages can name the DB user and host.

## Git and PR workflow

- Never commit directly to `main`. Work on a branch and merge through a pull request.
- Before merging any PR, run `/code-review <PR#>` on it and report the findings. Don't merge while correctness findings are unresolved unless the user explicitly says to; fix them on the PR branch and review again.
- Only merge a PR when the user asks.
- If a PR conflicts with `main`, or two branches changed overlapping code, use the `merge-manager` agent (`.claude/agents/merge-manager.md`). It merges `main` into the PR branch and never merges into `main` itself. Its conflict resolution is new code, so run `/code-review` on the PR again afterwards.

## Copilot agent config

`.github/agents/` (Design Review, Codebase Health, Resume Sync) and `.github/prompts/` hold the review checklists and edit-boundary workflows summarized above; consult them when asked for a design or codebase-health review.
