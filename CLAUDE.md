# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static Data Engineer portfolio site with a small PHP contact-form backend, hosted on Namecheap cPanel (MySQL + PHP). No frontend framework, no package manager, no test suite or linter.

## Commands

```bash
python scripts/build_site.py
```

Regenerates root `index.html` from the template and section fragments. It is stdlib-only Python 3, so any interpreter works (the repo `.venv` is optional). The build is deterministic: rebuilding unchanged sources reproduces the committed `index.html` byte-for-byte.

There is no local backend setup; `api/contact.php` is exercised against the deployed host with the PowerShell smoke test in README.md. `index.html` references `/favicon.png` and `/api/contact.php` by absolute path, so the page must be served from a web root — over `file://` the favicon and form submission break.

## Build architecture

- `src/index.template.html` is the page shell: `<head>` (title, meta description, canonical, Open Graph tags, and a JSON-LD `Person` block, all using absolute `https://hornsloth.com/` URLs), fonts, Tailwind CDN script, the inline `tailwind.config`, and `<!-- SECTION:<name> -->` placeholders.
- `sections/<name>.html` fragments are substituted into those placeholders in the order of `SECTION_ORDER` in `scripts/build_site.py`. `header-nav` and `footer` sit outside `<main class="blueprint-grid">`; all other sections are inside it.
- Root `index.html` is generated but committed, and is the deployed artifact. Never hand-edit it — edit sources, rebuild, and commit the regenerated `index.html` alongside the source change.
- Adding a section requires a new fragment, a placeholder in the template, and an entry in `SECTION_ORDER` (the build raises if a placeholder is missing). Also update the fragment lists in `.github/instructions/section-fragments.instructions.md` and `.github/prompts/*.prompt.md`.
- Each fragment must begin with its exact marker comment — `<!-- Header/nav -->`, `<!-- Hero -->`, `<!-- Selected work -->`, `<!-- Philosophy -->`, `<!-- Metrics -->`, `<!-- Contact -->`, `<!-- Footer -->` — which differ from the `SECTION:` placeholder names. Fragments never contain `<html>`/`<head>`/`<body>`, the Tailwind config, font links, or global `<script>` tags.
- Section structure: `<section>` → `<div class="max-w-7xl mx-auto">` → content.

## Editing scope

- Treat section fragments as hard edit boundaries: a request about one section changes only that fragment unless a template-level or global change is genuinely required. If a request is ambiguous or spans sections, ask; if an edit must touch several fragments, say so explicitly.
- Resume-driven updates use `refrence docs/Animesh's Resume.pdf` (directory name is misspelled) as the source of truth. Change factual text only (names, roles, dates, metrics, skills, links) — never classes, layout, or structure. Facts such as years of experience and employers also appear in the template `<head>` (meta description, `og:description`, JSON-LD), so update them there too. Where the resume and page conflict, the resume wins; if the resume doesn't support a requested change, stop and say what's missing.

## Design system ("The Kinetic Blueprint" — full spec in DESIGN.md)

Non-negotiable rules:

- 0px radius everywhere: no `rounded-*`, no `border-radius` (the Tailwind config also zeroes the radius scale).
- No dividers/`<hr>` between sections — separate regions with tonal surface shifts (`bg-surface`, `bg-surface-container-low`, `bg-surface-container-lowest`, …).
- Dark mode only (`<html class="dark">`); no light variants.
- Typography: `font-headline` (Space Grotesk, uppercase, tight tracking), `font-body` (Inter), `font-mono` (JetBrains Mono, uppercase, `tracking-widest`) for data/metadata. Metadata labels are `text-[9px]`/`text-[10px]` mono with `tracking-[0.2em]`.
- Use named Tailwind color tokens, not raw hex.
- Form fields use the `.param-input` class — never Tailwind `ring-*`/`border-*` on inputs.
- Icons: `<span aria-hidden="true" class="material-symbols-outlined" data-icon="name">name</span>` (thin stroke via `wght 300`, set by the `@24,300,0,0` part of the font URL; the subset font is static, so CSS `font-variation-settings` has no effect). The icon font is subset: the template's Material Symbols link lists every icon in use in `icon_names=` (alphabetical). A new icon must be added there, or it renders as its literal name. Icon-only links/buttons need an `aria-label`. Buttons get `active:translate-y-1 transition-transform`. No placeholder `href="#"` links.
- Tailwind utilities only. Custom CSS lives solely in `css/design-tokens.css` (`.blueprint-grid`, `.param-input`, `::selection`) — no new CSS files, `<style>` blocks, or inline `style=`.

### Color token gotcha

Most tokens are hex values in the template's inline `tailwind.config`. Five — `primary`, `primary-container`, `on-primary-container`, `outline-variant`, `on-background` — are `rgb(var(--token-*) / <alpha-value>)` references whose values live in `:root` of `css/design-tokens.css` as space-separated RGB channels (e.g. `255 87 26`); change those there and keep the channel format.

Opacity modifiers (`border-outline-variant/10`, `hover:border-primary-container/30`) work on every token. Keep the `<alpha-value>` form: a plain `var(--token-*)` color makes Tailwind CDN (v3.4) silently generate **no CSS** for opacity modifiers, and a bare `border` then falls back to Tailwind's default light-gray border. In custom CSS, write `rgb(var(--token-*))` or `rgb(var(--token-*) / N%)`; a bare `var(--token-*)` is not a valid color.

## Contact form backend (`api/`)

Flow: `js/form-handler.js` POSTs JSON to `/api/contact.php` → validation → rate-limit check and insert into `contact_submissions` (`db.php`, `schema.sql`) → notification via `mailer.php` → row status updated `received` → `emailed` / `email_failed`. Once the row is stored the API returns 200 success even if the email fails (the failure goes to the PHP error log), so visitors don't resend.

- The JS binds to `#contact form`, its `button[type=submit]`, `#contact-form-status`, and hidden `input[name=form_started_at]`, and silently no-ops if any is missing. Field names (`name`, `email`, `subject`, `message`, honeypot `company_website`, `form_started_at`) must stay in sync across `sections/contact.html`, the JS, and `contact.php`.
- Responses are `{success, message, requestId?}`. The JS maps machine codes (`blocked_*`) to plain-language text in `ERROR_MESSAGES` and shows other messages as-is; the status line is upper-cased by CSS, so keep messages sentence case. The JS also validates the `required` fields client-side and sets `aria-invalid` before sending.
- Abuse controls: non-empty honeypot → 429; filled in under `min_fill_seconds` → 429; more than `rate_limit_max_requests` per window per SHA-256 IP hash → 429. Field length limits in `contact.php` mirror `schema.sql` column sizes and the inputs' `maxlength` in `sections/contact.html` — change all three together.
- Config layering: `api/config.php` (committed placeholders) ← `CONTACT_*` env vars ← `api/config.local.php` (server-only, gitignored, merged via `array_replace_recursive`; template in `config.local.php.example`).
- `api/.htaccess` denies every file in `api/` except `contact.php` (config, helpers, schema, and cPanel's per-directory `error_log`). A new public endpoint must be allowed there. Don't log exception messages: PDO messages can name the DB user and host.
- `mailer.php` sends with PHP `mail()`; the `mail.smtp` config block is not currently read by any code.

## Git and PR workflow

- Never commit directly to `main`. Work on a branch and merge through a pull request.
- Before merging any PR, run `/code-review <PR#>` on it and report the findings. Don't merge while correctness findings are unresolved unless the user explicitly says to; fix them on the PR branch and review again.
- Only merge a PR when the user asks.
- If a PR conflicts with `main`, or two branches changed overlapping code, use the `merge-manager` agent (`.claude/agents/merge-manager.md`). It merges `main` into the PR branch and never merges into `main` itself. Its conflict resolution is new code, so run `/code-review` on the PR again afterwards.

## Copilot agent config

`.github/agents/` (Design Review, Codebase Health, Resume Sync) and `.github/prompts/` hold the review checklists and edit-boundary workflows summarized above; consult them when asked for a design or codebase-health review.
