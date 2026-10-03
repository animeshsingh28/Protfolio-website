# Portfolio Website — Architecture Review & Improvement Plan

_Review date: 2026-10-03 · Scope: every tracked file (template, sections, CSS, JS, PHP API, schema, build script, docs, AI-agent instructions)._

## 1. Executive summary

The site has a sound foundation: content is split into fragments assembled by a small, dependency-free build; the PHP API uses real prepared statements; and secrets are kept out of git. The design system is documented and applied consistently.

It falls short of production best practice in five areas:

1. **It ships a development-only toolchain to visitors.** It uses the Tailwind Play CDN (a JavaScript compiler that runs in the browser) and a 1.14 MB icon font, of which only 4 icons are used.
2. **The page is not discoverable or shareable.** There is no `<title>`, meta description, Open Graph tags or structured data, so LinkedIn and Google previews are blank.
3. **Accessibility and UX have gaps.** Form labels aren't linked to their inputs, the form fields fail the contrast minimum, the main call-to-action buttons do nothing, and there is no navigation on mobile.
4. **The contact pipeline is weaker than it looks.** The bot checks can be bypassed with one spoofed field. Mail goes through PHP `mail()` even though Zoho SMTP is configured, and failures are swallowed without being logged.
5. **There is no deployment boundary or CI.** The repo root is the web root, nothing gates a change before it ships, and the AI and human docs duplicate each other and have started to disagree.

None of these require a framework. The recommended target keeps the current architecture (static HTML assembled by Python, plus one PHP endpoint) and adds a real CSS build, a `dist/` output folder, and a CI/CD pipeline.

### Scorecard

| Area | Current | Main gap |
|---|---|---|
| Architecture & maintainability | 🟡 Fair | Facts hardcoded in several places; split token sources; build output committed at repo root |
| Performance | 🔴 Needs work | Tailwind Play CDN; 1.14 MB icon font; hotlinked unsized image |
| Accessibility (WCAG 2.2 AA) | 🔴 Needs work | Unlabelled inputs, form contrast 1.31:1, no title, heading skips, no skip link |
| SEO & social sharing | 🔴 Poor | No title, description, OG/Twitter, canonical, JSON-LD, sitemap |
| UX / conversion | 🔴 Needs work | Dead CTAs and icon buttons, no mobile nav, no résumé download |
| Backend security | 🟡 Fair | Spoofable bot checks, no Origin check, web-root exposure, unencoded mail headers |
| Privacy | 🟡 Needs work | Phone number in a **public** repo; PII kept indefinitely; reversible IP hash |
| DevOps / CI/CD | 🔴 Missing | No CI, no automated deploy, no quality gates |
| Documentation | 🟡 Fair | Thorough but duplicated across 10 AI-instruction files and drifting; README is UTF-16 |

## 2. How this was evaluated

Most findings were confirmed by running something, not just by reading code:

- **Build:** ran `scripts/build_site.py`. The output is byte-identical to the committed `index.html`, so there is no drift today.
- **API:** ran `php -l` on every file (all clean, PHP 8.3), then drove `api/contact.php` on a local `php -S` server:
  - GET → `405` ✅
  - Honeypot filled → `429 {"message":"blocked_honeypot"}`
  - **Cross-origin form-encoded POST with `form_started_at=1` passed both bot checks** and reached the DB layer.
- **File exposure:** with the repo root as web root, a plain web server serves `api/schema.sql`, `api/config.local.php.example`, `scripts/`, `.gemini/` and the résumé PDF.
- **Third-party assets:** the Material Symbols variable font is **1,137,972 bytes**; a subset of the 4 icons used is **4,164 bytes**. Google Fonts serves Space Grotesk only at **300/400/700**, so the 800 weight requested (and used by `font-extrabold`/`font-black`) doesn't exist.
- **Contrast:** computed WCAG ratios for the design tokens. Text passes (≥10:1). Form controls fail (§4.3).
- **Repo:** GitHub reports the repo as **public**, with default branch `copilot`. `git log --numstat` shows `README.md` as binary because it is UTF-16LE.
- **Not verified:** the live site (`hornsloth.com`) was unreachable from the review sandbox, so live response headers, TLS version and the deployed file layout are unconfirmed.

## 3. What's already good (keep these)

- **Source/output separation** with a zero-dependency build that fails loudly on a missing fragment or placeholder (`scripts/build_site.py`).
- **PDO done right:** `ERRMODE_EXCEPTION`, `EMULATE_PREPARES=false`, `utf8mb4`, named parameters everywhere (`api/db.php`).
- **Secrets pattern:** committed placeholder config + env vars + git-ignored `config.local.php` (`api/config.php:30-36`, `.gitignore`).
- **Defense in depth on the form:** honeypot, fill-time check, per-IP rate limit, length limits that match the column sizes, CR/LF stripping in mail headers, IP stored hashed rather than raw.
- **Good accessibility basics:** `lang="en"`, `color-scheme: dark`, `aria-live` on the form status, `rel="noopener noreferrer"` on external links, and strong text contrast (10.9:1 for body copy).
- **A coherent, written design system** ("Kinetic Blueprint") that the code actually follows.

## 4. Findings

Severity: **H** = fix before anything else / user- or security-visible · **M** = clear best-practice gap · **L** = polish.

### 4.1 Performance & front-end delivery

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| P1 | H | **Tailwind Play CDN in production.** Tailwind's docs say the Play CDN is for development only. It downloads a JS compiler, blocks rendering, compiles CSS in the browser on every visit, causes a flash of unstyled content, and forces `'unsafe-inline'` + a third-party script into any CSP. | `src/index.template.html:10-80` | Compile CSS at build time with the **Tailwind v4 standalone CLI** (single binary, no Node required). Move tokens into CSS `@theme`. Ship one minified, content-hashed stylesheet. |
| P2 | H | **1.14 MB icon font for 4 icons.** Before it loads, the ligature text (`settings_input_component`) renders as words and shifts the layout. | `src/index.template.html:8`; icons used: `terminal`, `settings_input_component`, `check_circle`, `database` | Replace with **inline SVGs** (≈1 KB total; no flash of text, no third-party request). Fallback: append `&icon_names=…` (4 KB). |
| P3 | M | **Fonts: no fallback stacks; non-existent weight requested.** `["Space Grotesk"]` with no generic fallback means the browser default (often a serif) shows while loading or if the font fails. Weight 800 doesn't exist, so `font-extrabold`/`font-black` silently render at 700. | `src/index.template.html:7, 71-76` | Self-host latin-subset WOFF2 (Inter, Space Grotesk 300–700, JetBrains Mono). `preload` the headline font. Use stacks such as `"Space Grotesk", system-ui, sans-serif`. Use `font-bold` or accept 700. This also removes a third-party call to Google (an EU privacy concern). |
| P4 | M | **Hotlinked, unsized, AI-generated image.** The image is served from `lh3.googleusercontent.com/aida-public/…`, a generator asset URL that can expire. It has no `width`/`height` (layout shift), no lazy loading, no modern format, and a leftover `data-alt`. | `sections/philosophy.html:8` | Self-host as AVIF/WebP via `<picture>`, with `width`/`height`, `loading="lazy"` and `decoding="async"`. Remove `data-alt`. |
| P5 | L | 32 of 47 colour tokens in the Tailwind config are unused (a Material 3 export). Two token sources: 5 in `css/design-tokens.css`, the rest inline in the template. | `src/index.template.html:16-64`, `css/design-tokens.css:1-8` | One source: CSS custom properties in `@theme` (P1). Delete unused tokens. |
| P6 | L | Generator leftovers: classes `docked`, `full-width` (not Tailwind classes); `data-icon` attributes. | `sections/header-nav.html:2` | Remove when touching these files. |

**Target budgets:** Lighthouse mobile Performance ≥ 95; LCP < 2.5 s; CLS < 0.1; INP < 200 ms; total transfer < 200 KB on first load.

### 4.2 SEO & social sharing

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| S1 | H | **No `<title>`.** The browser tab shows the URL. It also fails WCAG 2.4.2. | `src/index.template.html:2-9` | `<title>Animesh Singh — Data Engineer (ETL, SQL, Informatica)</title>` |
| S2 | H | **No meta description, canonical, Open Graph or Twitter card tags.** Shared links on LinkedIn, Slack and WhatsApp show no title, description or image. That matters a lot for a job-seeking portfolio. | same | Add `description`, `canonical`, `og:*` and `twitter:card` tags, plus a 1200×630 `og-image.png` in the brand style. |
| S3 | M | No structured data. | — | JSON-LD `Person` (name, jobTitle, worksFor, address locality, `sameAs` LinkedIn/GitHub). |
| S4 | L | No `robots.txt`, `sitemap.xml`, 404 page, `theme-color`, apple-touch-icon; favicon is a 512×512 PNG (30 KB). | repo root | Add a static folder with these; ship 32 px/SVG favicons and a 180 px apple-touch icon. |

### 4.3 Accessibility (target: WCAG 2.2 AA)

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| A1 | H | **Labels aren't tied to inputs.** `<label>` has no `for` and the inputs have no `id`, so screen readers announce only the placeholder (WCAG 1.3.1, 4.1.2). | `sections/contact.html:40-55` | Add `for`/`id` pairs; add `required`, `maxlength` (100/254/150/5000, matching the server) and `autocomplete`. |
| A2 | H | **Form controls fail contrast.** Input underline is **1.31:1** (needs 3:1, WCAG 1.4.11); placeholder is **1.40:1** (needs 4.5:1). Fields are close to invisible until focused. | `css/design-tokens.css:28, 47` | Use the existing `outline` token `#ad897e` (**5.41:1**) for the resting border and placeholder. Keep `primary` for focus (10.05:1). |
| A3 | M | **Heading hierarchy skips.** The metrics section has no `h2` and jumps to `h4`/`h5`. | `sections/metrics.html:5, 25` | `h2` for "System metrics", `h3` for "Expansion potential". Add `id` + `aria-labelledby` to each section. |
| A4 | M | No skip link. The sticky header covers anchor targets (no `scroll-padding-top`). Nav has no `aria-current`, and "Systems" is styled as active permanently. | `src/index.template.html:83`, `sections/header-nav.html:7` | Add a skip link to `#main`, `html { scroll-padding-top: 5rem }`, and a small scroll-spy that sets `aria-current`. |
| A5 | M | **Motion ignores user preference.** `animate-pulse` runs forever on status dots and the footer text; there are hover transitions on images (WCAG 2.2.2, 2.3.3). | `sections/contact.html:25`, `sections/footer.html:14`, `sections/philosophy.html:8` | Use the `motion-safe:` variant; guard smooth scrolling with `prefers-reduced-motion`. |
| A6 | M | **Very small type:** 50 uses of 8–11 px text (1× 8 px, 18× 9 px, 22× 10 px, 9× 11 px). | `sections/*.html` | Set a floor of 11–12 px and use letter-spacing for the "label" look. Keep 10 px only for decoration. |
| A7 | L | No consistent `:focus-visible` style; `.param-input` removes the outline. | `css/design-tokens.css:29, 40-44` | Add a global `:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px }`. |

### 4.4 UX & content

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| U1 | H | **The hero CTAs do nothing.** `INITIALIZE_PROTOCOL` and `VIEW_SCHEMATICS` are `<button>`s with no handler. They are the primary conversion path. | `sections/hero.html:17-22` | Make them links: `<a href="#contact">` and `<a href="#architectures">` (or the résumé). |
| U2 | H | **No navigation on mobile.** The nav is `hidden md:flex` with no alternative, and most recruiter traffic is mobile. | `sections/header-nav.html:6` | Add an accessible disclosure menu (`<button aria-expanded>` + panel, or `<details>`). |
| U3 | M | **False affordances.** The two header icon buttons have no action and no `aria-label`. Project cards use `cursor-pointer` but aren't links. | `sections/header-nav.html:12-17`, `sections/selected-work.html:15, 42, 69` | Remove the icon buttons or give them a real purpose (e.g., résumé, GitHub). Remove `cursor-pointer` or link the cards to case studies. |
| U4 | M | **Facts are hardcoded and already inconsistent.** "3.4 years" appears in 4 places, while the committed résumé says "2.7 years". The résumé lists a current L'Oréal engagement (10/2025–present). "2026" is hardcoded in two places. | `sections/hero.html:6, 14, 37`, `sections/metrics.html:8`, `sections/philosophy.html:19`, `sections/footer.html:6` | Keep facts in one `content/site.json` that the build reads. Compute years from a start date and the copyright year at build time. |
| U5 | M | No résumé download. For a portfolio, this is the most-wanted CTA. | — | Publish a redacted PDF at `/resume.pdf` (see PR1) and link it from the hero and header. |
| U6 | L | The email is plain text, not a `mailto:` link. "ENCRYPTION: TLS_1.3" is a claim the host must actually honour. The footer "GITHUB" link points to this repo rather than the profile. | `sections/contact.html:16, 57`, `sections/footer.html:10` | Use `mailto:`, verify the TLS claim or soften it, and decide which GitHub link is intended. |

### 4.5 Contact API — security & reliability

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| B1 | H | **Bot checks are client-controlled.** `form_started_at` comes from the browser, so any bot sends an old timestamp (verified: `form_started_at=1` passes). There is no Origin/Referer check, so cross-site form-encoded posts are accepted (verified). | `api/contact.php:58-74`, `js/form-handler.js:12-14` | ① Allow-list the `Origin` header (fall back to `Referer`). ② Replace the timestamp with a **server-signed token** (`api/form-token.php` returns `ts.HMAC(ts)`; accept if 3 s ≤ age ≤ 2 h). ③ Add Cloudflare Turnstile only if spam appears. |
| B2 | H | **The honeypot tells the bot it was caught.** It returns `429 blocked_honeypot`, and the fill-time check returns `429 blocked_fill_time` (429 means rate-limited). The UI shows these codes to humans in uppercase. | `api/contact.php:61-74` | Trapped bots get a **silent `200 {"success":true}`** with nothing stored. Humans get a friendly message. Reserve 429 for the rate limiter. |
| B3 | H | **The configured SMTP is never used.** `config.php` defines Zoho SMTP settings, but `mailer.php` calls `mail()`. The host's local mail server sends as `@hornsloth.com` while that domain's mail is at Zoho, so SPF/DMARC alignment is likely to fail. Messages may go to spam, and `mail()` still returns `true`, so failures are invisible. | `api/mailer.php:45` vs `api/config.php:14-21` | Use **PHPMailer over Zoho SMTP** (port 465, SSL) with the existing config. Verify SPF, DKIM and DMARC for `hornsloth.com`. |
| B4 | M | **Mail headers aren't RFC-encoded.** Subject and display names aren't MIME-encoded (`mb_encode_mimeheader`), so non-ASCII names (e.g., Devanagari) produce invalid headers. The display name isn't quoted, so a name like `Acme, Inc` splits `Reply-To` into two addresses. | `api/mailer.php:19-43` | PHPMailer handles both (`addReplyTo($email, $name)`). |
| B5 | M | **A failed email becomes a 500 after the data is saved.** The user is told to "try again later", which creates duplicates and uses up their rate limit. Every exception is swallowed without a log line. | `api/contact.php:140-155` | The message is stored, so return success. Mark the row `email_failed` and retry from a cPanel cron script. `error_log()` every failure with its `requestId`. |
| B6 | M | **Input type and encoding.** Arrays are cast with `(string)` → `"Array"` plus a PHP warning. On invalid UTF-8, `preg_replace(/u)` returns `null` and the `?? $value` fallback keeps the **unsanitized** string. | `api/contact.php:19-20, 53-58` | Reject values that aren't strings; reject `!mb_check_encoding($v, 'UTF-8')`. Return field-level error codes. |
| B7 | M | **Deployment exposure.** The repo root is the web root, so a full upload publishes `schema.sql`, `config.local.php.example`, `scripts/`, `sections/`, `.github/`, `.gemini/`, the docs and the résumé (verified locally). `config.local.php` sits inside the web root, protected only by PHP execution. | repo layout; README "cPanel setup" | Deploy only `dist/` + `api/`. Put the real config **above `public_html`**. Add an `api/.htaccess` that denies everything except `contact.php` and `form-token.php`. Make sure `.git/` is never deployed. |
| B8 | L | Missing response hardening: no `Cache-Control: no-store`, no `X-Content-Type-Options`; `X-Powered-By: PHP/8.x` is exposed. | `api/contact.php:3` | Add the headers; set `expose_php = Off` (cPanel ▸ MultiPHP INI). |
| B9 | L | `REMOTE_ADDR` becomes the proxy IP if a CDN such as Cloudflare is added later, which would collapse the rate limit into one bucket. | `api/contact.php:98` | If you add a CDN, read `CF-Connecting-IP` only when the request comes from Cloudflare's IP ranges. |

### 4.6 Privacy & data protection

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| PR1 | H | **A phone number is published in a public repo.** The committed résumé contains a personal phone number, and the repo is public. Deleting the file leaves it in git history. | `refrence docs/Animesh's Resume.pdf` | Decide whether it should be public. If not: remove it, purge it from history (`git filter-repo`), force-push, and publish a redacted copy as `/resume.pdf`. |
| PR2 | M | **The IP "hash" is reversible.** Unsalted SHA-256 over 2³² IPv4 addresses can be brute-forced in minutes, so it is pseudonymous, not anonymous. | `api/contact.php:99` | `hash_hmac('sha256', $ip, $pepper)` with a server-side secret. |
| PR3 | M | **No retention policy or privacy notice.** Name, email, message and user agent are kept forever. India's DPDP Act 2023 (and GDPR for EU visitors) expects notice and purpose limitation. | `api/schema.sql` | Add one line of notice under the form and a cron purge (e.g., rows older than 12 months). Drop the unused `idx_email` index and the unused `rejected` status, or start using them. |

### 4.7 Build, tooling & CI/CD

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| T1 | H | **No CI and no automated deploy.** Nothing checks that `index.html` was rebuilt, that PHP parses, that links work or that accessibility holds. Deployment is a manual cPanel upload. | no `.github/workflows/` | GitHub Actions: CI on every PR (§5, Phase 4), and deploy on merge to `main` over SSH/FTPS with secrets in GitHub. |
| T2 | M | **Build output is committed at the repo root, mixed with sources.** It is in sync today, but only by discipline. | `index.html`, `scripts/build_site.py:7` | Build into `dist/` (git-ignored). Copy static files and hash asset filenames. Assert no `<!-- SECTION:` remains. Add a `--check` mode for CI. |
| T3 | M | **No linters or formatters**, and indentation in the fragments is inconsistent (generator output). | — | `.editorconfig`, Prettier (HTML/CSS/JS), `html-validate`, Ruff (Python), PHP-CS-Fixer + PHPStan level 6. |
| T4 | L | **No automated tests for the API.** | — | PHPUnit for validation and token logic; a CI smoke test against `php -S` with a MySQL service container. |

### 4.8 Documentation & repo hygiene

| ID | Sev | Finding | Evidence | Recommended fix |
|---|---|---|---|---|
| D1 | M | **README is UTF-16LE with CRLF line endings.** Git treats it as binary (no diffs, no grep, no blame). It also contains Windows-only absolute paths (`d:/Protfolio website/.venv/...`). | `README.md` | Re-save as UTF-8 with LF. Add `.gitattributes` (`* text=auto eol=lf`). Use repo-relative commands. |
| D2 | M | **DESIGN.md is wrapped in a ```` ```markdown ```` fence**, so GitHub renders it as one raw code block. Its values contradict the code (`primary #FF4D00` vs `#FFB59E`/`#FF571A`; it describes gradient CTAs, but the code uses flat colours). | `DESIGN.md:1, 84` | Remove the fence. Make the token table generated from, or checked against, the CSS. |
| D3 | M | **AI instructions are duplicated across 10 files (~530 lines) and already drift.** `.gemini/instructions.md` says mail goes through Zoho SMTP (it doesn't). `copilot-instructions.md` says "no additional CSS files" while `css/design-tokens.css` exists. Each rule change needs 5+ edits. | `.gemini/`, `.github/copilot-instructions.md`, `.github/instructions/*`, `.github/agents/*`, `.github/prompts/*` | One canonical **`AGENTS.md`**. Tool-specific files (`copilot-instructions.md`, `.gemini/…`, `CLAUDE.md`) become one-line pointers. Keep the agent/prompt files, but have them reference `AGENTS.md` instead of restating rules. |
| D4 | L | Repo hygiene: `refrence docs/` is misspelled and has spaces and an apostrophe in the filename; `screen.png` (230 KB) is unreferenced; no `LICENSE`; the default branch is `copilot` although the docs treat `main` as the deployable baseline. | repo root, GitHub settings | Rename to `docs/reference/resume.pdf` (or remove, see PR1). Move the screenshot into `docs/`. Add a licence (or state "all rights reserved"). Make `main` the default and protect it. |

## 5. Implementation plan

The phases are ordered for the most user-visible value with the least rework. Phases 1 and 2 are independent and can run in parallel. Phase 3 should land before Phase 4, so CI gates the new build rather than the old one. Effort assumes one developer who knows the codebase.

### Phase 0 — Decisions & quick hygiene (≈ 1–2 h)

| # | Task | Findings |
|---|---|---|
| 0.1 | Decide on the résumé's public exposure. If redacting: remove it, run `git filter-repo`, force-push, and publish a redacted `/resume.pdf`. | PR1 |
| 0.2 | Confirm the correct years of experience and current role, to feed `content/site.json` later. | U4 |
| 0.3 | Re-encode README to UTF-8 + LF; add `.gitattributes` and `.editorconfig`; remove the fence from DESIGN.md. | D1, D2, T3 |
| 0.4 | Make `main` the default branch with branch protection; rename `refrence docs/`; move `screen.png` into `docs/`; add a LICENSE. | D4 |

**Done when:** `git diff` works on README; DESIGN.md renders as formatted text on GitHub; `main` is protected.

### Phase 1 — Front-end correctness: a11y, SEO, UX (≈ 1 day)

Fragment- and template-level edits only; no new tooling.

| # | Task | Findings |
|---|---|---|
| 1.1 | Head: `<title>`, description, canonical, OG/Twitter tags + `og-image.png`, `theme-color`, JSON-LD `Person`. | S1–S3 |
| 1.2 | Contact form: `for`/`id`, `required`, `maxlength`, `autocomplete`; `aria-describedby` for errors; `outline` token for the resting border and placeholder. | A1, A2 |
| 1.3 | Turn the hero CTAs into anchors; remove or repurpose the header icon buttons (with `aria-label`); drop `cursor-pointer` on non-link cards; `mailto:` link. | U1, U3, U6 |
| 1.4 | Mobile nav disclosure, skip link, `scroll-padding-top`, `aria-current` scroll-spy. | U2, A4 |
| 1.5 | Fix heading levels; use `motion-safe:` on pulses and transitions; 11–12 px type floor; global `:focus-visible`. | A3, A5–A7 |
| 1.6 | Replace Material Symbols with inline SVG; add font fallback stacks; stop requesting weight 800. | P2, P3 |
| 1.7 | Self-host and optimize the philosophy image (`<picture>`, dimensions, lazy). | P4 |
| 1.8 | Add `robots.txt`, `sitemap.xml`, `404.html`, proper favicons. | S4 |

**Done when:** axe/pa11y reports 0 violations; Lighthouse Accessibility and SEO are 100; every visible control does something; the nav works at 375 px width.

### Phase 2 — Contact pipeline hardening (≈ 1–1.5 days)

| # | Task | Findings |
|---|---|---|
| 2.1 | PHPMailer over Zoho SMTP using the existing `mail.smtp` config. Verify SPF/DKIM/DMARC on `hornsloth.com` (Zoho admin ▸ Email authentication). | B3, B4 |
| 2.2 | Request guardrails: Origin allow-list; strict string and UTF-8 validation; field-level error codes. | B1, B6 |
| 2.3 | `api/form-token.php` with an HMAC-signed timestamp, replacing the client `form_started_at`. Silent 200 for honeypot hits. | B1, B2 |
| 2.4 | Reliability: return success once stored; cron script retries `email_failed` rows; `error_log` with `requestId`. | B5 |
| 2.5 | Privacy: HMAC the IP with a pepper; one-line notice under the form; cron purge after N months; tidy the schema (migration file). | PR2, PR3 |
| 2.6 | Hardening: move the real config above `public_html`; `api/.htaccess` allow-list; `no-store`/`nosniff` headers; `expose_php=Off`. | B7, B8 |
| 2.7 | Client: map error codes to human copy; native + inline validation; `AbortController` timeout (15 s); disabled-button styling. | B2, A1 |
| 2.8 | Tests: PHPUnit for validation and the token; a curl smoke script (also used in CI). | T4 |

**Done when:** a scripted bot (spoofed timestamp, foreign Origin, filled honeypot) gets nothing stored and nothing emailed; a real submission arrives in the inbox (not spam) with valid UTF-8 headers; an SMTP outage still returns success, and the cron job delivers later.

### Phase 3 — Build pipeline modernization (≈ 1 day)

| # | Task | Findings |
|---|---|---|
| 3.1 | Add the Tailwind v4 standalone CLI (pinned version). Create `src/styles/main.css` with `@import "tailwindcss"`, an `@theme` block holding the **15 used tokens**, and the existing atoms (`.blueprint-grid`, `.param-input`, …) in `@layer components`. Delete the inline config and the CDN script. | P1, P5 |
| 3.2 | Self-host WOFF2 fonts under `static/fonts/` with `@font-face` and `font-display: swap`; preload the headline font. | P3 |
| 3.3 | `content/site.json` holds the facts (start dates, roles, metrics, links, projects). The build substitutes `{{ … }}` and computes years and copyright year. | U4 |
| 3.4 | `build_site.py`: render to `dist/`, run Tailwind, copy `static/`, add content-hashed asset names, fail on leftover placeholders or `{{`, add a `--check` flag. Git-ignore `dist/`; delete the root `index.html` (after the deploy pipeline is live). | T2 |
| 3.5 | Root `.htaccess` (shipped from `static/`): HTTPS redirect, HSTS, a strict CSP (now possible with no CDN script or inline config), `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors 'none'`, compression, and long-cache headers for hashed assets. | P1, B8 |

Target CSP once 3.1 and 3.2 land:
```
default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:;
connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'
```
Browser floor for Tailwind v4: Safari 16.4+, Chrome 111+, Firefox 128+. That matches what the site already needs for `color-mix()`.

**Done when:** first-load transfer is under 200 KB; Lighthouse Performance is ≥ 95 on mobile; securityheaders.com gives an A; nothing is requested from a third-party origin.

### Phase 4 — CI/CD & quality gates (≈ 0.5–1 day)

| # | Task | Findings |
|---|---|---|
| 4.1 | `.github/workflows/ci.yml` on every PR: `build_site.py --check`, `php -l` + PHPStan, `html-validate`, Ruff, lychee link check, pa11y-ci, and Lighthouse CI with the budgets from §4.1. | T1, T3 |
| 4.2 | `.github/workflows/deploy.yml` on push to `main`: build, then upload `dist/` + `api/` (never `config.local.php` or `.git`) via SSH/rsync or FTPS. Credentials come from GitHub Actions secrets. | T1, B7 |
| 4.3 | Require CI to pass in branch protection; add a PR template; Dependabot for Actions and Composer. | T1 |

**Done when:** a PR that breaks a link, the build or the a11y checks cannot merge, and merging to `main` deploys with no manual steps.

### Phase 5 — Docs & AI-instruction consolidation (≈ 2–3 h)

| # | Task | Findings |
|---|---|---|
| 5.1 | Write one `AGENTS.md` (architecture, design rules, workflow, API security layers). Reduce `.github/copilot-instructions.md`, `.gemini/instructions.md` and a new `CLAUDE.md` to pointers. Point the agents and prompts at it. | D3 |
| 5.2 | Rewrite README for the new flow: prerequisites, `build`, `--check`, deploy, server setup (config above web root, cron jobs, DNS auth records). | D1 |
| 5.3 | Reconcile DESIGN.md token values with `@theme`. | D2 |

### Phase 6 — Growth (optional, ongoing)

- **Case-study pages** per project: problem → architecture diagram → stack → measurable result. This is the biggest credibility lever for a data-engineering portfolio, and the current cards have nowhere to link.
- Privacy-friendly analytics (Cloudflare Web Analytics, Plausible or Umami) and an uptime monitor on the contact endpoint.
- Links to public code samples (SQL/dbt/Spark snippets) to back up the "SQL optimization" claims.

### Target layout after Phases 3–4

```
├─ content/site.json          # single source of facts
├─ src/
│  ├─ index.template.html
│  └─ styles/main.css         # @import "tailwindcss"; @theme {…}; atoms
├─ sections/*.html            # unchanged location
├─ js/form-handler.js
├─ static/                    # .htaccess, robots.txt, sitemap.xml, 404.html, favicons, og-image, fonts/, img/
├─ api/                       # contact.php, form-token.php, .htaccess, lib/, cli/ (cron: retry-mail, purge)
├─ scripts/build_site.py      # → dist/
├─ dist/                      # git-ignored; the only static thing deployed
├─ .github/workflows/{ci,deploy}.yml
└─ AGENTS.md
```

## 6. Open decisions for the owner

1. **Résumé exposure (PR1):** keep the phone number public, publish a redacted copy, or rewrite history to remove it.
2. **Years of experience (U4):** the site says 3.4, the résumé says 2.7. Which is correct, and from which start date should it be computed?
3. **Bot defense level (B1):** a signed token plus Origin check only, or also Cloudflare Turnstile from day one.
4. **Deploy transport (4.2):** SSH/rsync (requires SSH access on the Namecheap plan) or FTPS.
5. **Header icon buttons (U3):** remove them, or repurpose them (e.g., résumé download / GitHub).
