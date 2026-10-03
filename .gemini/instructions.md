# Antigravity Agent Instructions — Portfolio Website

## 0. Branch Protection — MANDATORY

> **Never commit directly to the `main` branch.**

All changes — no matter how small — MUST be made on a separate branch.

- Before making any edits, check the current branch with `git branch --show-current`.
- If on `main`, create and switch to a new branch first:
  ```powershell
  git checkout -b <descriptive-branch-name>
  ```
- Use clear, descriptive branch names (e.g., `feat/add-skills-section`,
  `fix/contact-form-validation`, `style/update-hero-colors`).
- Keep `main` as the clean, deployable baseline — it is only updated via
  merge after review.
- If you are already on a non-main working branch, continue using it unless
  the new task is unrelated (in which case, create a fresh branch from `main`).

---

## 1. Project Identity

This is Animesh Singh's Data Engineer portfolio website. It uses a modular
static-site architecture assembled by a Python build script, with a Python
Vercel Function for contact form submissions (Neon Postgres for storage,
Resend for email notifications). It is hosted on Vercel.

---

## 2. Architecture: Source → Build → Output

### Golden Rule
**`index.html` is generated output. Never edit it directly.**

All content/structure changes MUST be made in the source files, then rebuilt:

```
src/index.template.html     ← page shell (head, Tailwind config, placeholders)
sections/*.html              ← 7 content fragments (see Section Order below)
css/design-tokens.css        ← custom CSS atoms and variables
js/form-handler.js           ← contact form client-side controller
```

### Section Order & Placeholder Mapping

| Placeholder in template          | Source fragment                   |
|:---------------------------------|:---------------------------------|
| `<!-- SECTION:header-nav -->`    | `sections/header-nav.html`       |
| `<!-- SECTION:hero -->`          | `sections/hero.html`             |
| `<!-- SECTION:selected-work -->` | `sections/selected-work.html`    |
| `<!-- SECTION:philosophy -->`    | `sections/philosophy.html`       |
| `<!-- SECTION:metrics -->`       | `sections/metrics.html`          |
| `<!-- SECTION:contact -->`       | `sections/contact.html`          |
| `<!-- SECTION:footer -->`        | `sections/footer.html`           |

### Build Command

```powershell
python scripts/build_site.py
```

Always rebuild `index.html` after editing any source file. The build script
uses only Python standard library (`pathlib`) — no `pip install` needed.

---

## 3. Design System — "The Kinetic Blueprint"

Full spec lives in `DESIGN.md`. These rules are **non-negotiable**:

### 3.1 Visual Absolutes

- **0px border-radius everywhere.** Never add `rounded-*` classes or CSS
  `border-radius`. Not even `2px`. Zero tolerance.
- **No dividers / horizontal rules.** Section separation uses tonal surface
  color shifts only (e.g., `bg-surface-container-low` vs `bg-background`).
- **Dark mode only.** `<html class="dark">` is permanently set. Do not add
  light-mode variants.
- **Blueprint grid.** Main content wraps in `.blueprint-grid` (48px offset
  pattern defined in `css/design-tokens.css`).

### 3.2 Typography

| Semantic Role      | Tailwind Class   | Font Family     | Style Rules                         |
|:-------------------|:-----------------|:----------------|:------------------------------------|
| Headlines / Labels | `font-headline`  | Space Grotesk   | uppercase, `tracking-tight`         |
| Body copy          | `font-body`      | Inter           | Normal case                         |
| Metadata / Code    | `font-mono`      | JetBrains Mono  | uppercase, `tracking-widest`        |

- Metadata labels use `text-[9px]` or `text-[10px]` with `tracking-[0.2em]`.

### 3.3 Color Tokens

Always use named Tailwind tokens — never raw hex. Key tokens:

| Token                     | Hex       | Use                              |
|:--------------------------|:----------|:---------------------------------|
| `background`              | `#111316` | Page background                  |
| `surface-container-low`   | `#1A1C1F` | Default card/section containers  |
| `surface-container-high`  | `#282A2D` | Interactive element surfaces     |
| `primary`                 | `#FFB59E` | Brand accent / active highlights |
| `primary-container`       | `#FF571A` | High-energy CTA buttons          |
| `tertiary`                | `#00DAF3` | Electric Cyan — status, uplinks  |
| `error`                   | `#FFB4AB` | Error states                     |
| `secondary`               | `#B8C8DA` | Muted labels and secondary copy  |
| `outline-variant`         | `#5C4037` | Grid lines and subtle borders    |

### 3.4 Component Patterns

- **Buttons (Actuators):** Sharp corners, `active:translate-y-1
  transition-transform` for mechanical press feedback.
- **Cards (Data Modules):** `bg-surface-container-low` with
  `hover:border-primary-container/30` — border appears on hover only.
- **Status chips:** Rectangular, `text-tertiary` for active/live, `text-error`
  for failure states.
- **Section labels:** Monospace, 10px, all-caps (e.g., `BUILD: SUCCESSFUL`).
- **Breadcrumbs:** `/` separator in monospace, mimicking file paths.
- **Form inputs:** Use `.param-input` class (defined in
  `css/design-tokens.css`). Never use Tailwind `ring-*` or `border-*` on
  forms.
- **Icons:** `<span aria-hidden="true" class="material-symbols-outlined"
  data-icon="icon_name">icon_name</span>` — thin stroke (`wght: 300`).
  The icon font is subset: add any new icon to `icon_names=` (alphabetical)
  in the template's Material Symbols link, or it renders as plain text.

---

## 4. Fragment Editing Rules

- Each fragment MUST begin with its exact top-level comment marker:
  `<!-- Header/nav -->`, `<!-- Hero -->`, `<!-- Selected work -->`,
  `<!-- Philosophy -->`, `<!-- Metrics -->`, `<!-- Contact -->`,
  `<!-- Footer -->`.
- Fragments are self-contained. Do NOT add `<html>`, `<head>`, `<body>`, or
  duplicate the Tailwind config / global scripts inside them.
- Section structure pattern: `<section>` → `<div class="max-w-7xl mx-auto">`
  → content.
- If a change spans multiple fragments, touch each one explicitly rather than
  silently editing adjacent sections.

---

## 5. CSS & Styling Rules

- `css/design-tokens.css` holds shared custom atoms only: `.blueprint-grid`,
  `.material-symbols-outlined`, `::selection`, `.param-input`, and `:root`
  CSS variables.
- Prefer Tailwind utility classes everywhere else.
- Do not introduce inline `style=` attributes unless the value truly cannot
  be expressed as a utility class.
- Do not add component-specific layout CSS to `design-tokens.css` when it
  belongs in a section fragment's Tailwind classes.

---

## 6. Backend API (`api/`)

### Files

| File                        | Role                                                    |
|:----------------------------|:--------------------------------------------------------|
| `api/contact.py`            | Vercel Function `POST /api/contact` — validation, rate-limit, insert, email via Resend |
| `requirements.txt`          | Function dependencies (`psycopg`)                       |
| `db/schema.sql`             | Postgres DDL for `contact_submissions` (run once in Neon) |
| `vercel.json`               | Function `maxDuration`, security headers, `cleanUrls`   |
| `.vercelignore`             | Allowlist of files that get deployed                    |

### Security Layers

1. **Honeypot:** Hidden `company_website` field must be empty.
2. **Fill-time check:** client-measured `form_fill_seconds ≥ 3`.
3. **Rate limit:** Max 5 requests per 300 seconds per IP hash.
4. **Input validation:** Required fields, length limits, email validation.
5. **IP hashing:** HMAC-SHA256 keyed by `CONTACT_IP_HASH_SECRET` stored, never
   raw IP (plain SHA-256 fallback, logged once per process, if the secret is unset).
6. **Header injection:** `\r` and `\n` stripped from mail headers.
7. **JSON only:** a no-JS form submit (urlencoded or no content type) stores
   nothing and gets a 303 to `/#contact`, where a `<noscript>` note offers
   email; other content types get 415.

### Secrets Management

- All secrets are Vercel project environment variables: `DATABASE_URL`
  (set by the Neon integration), `RESEND_API_KEY`, `CONTACT_MAIL_TO`,
  `CONTACT_MAIL_FROM`, `CONTACT_IP_HASH_SECRET`.
- **Never commit secrets or `.env*` files to git.**

---

## 7. Frontend Contact Form (`js/form-handler.js`)

- On page load: stores `performance.now()` in hidden `form_started_at`; on
  submit it sends the elapsed `form_fill_seconds`, never the timestamp.
- On submit: collects JSON payload → `POST /api/contact`.
- Status updates rendered in `#contact-form-status` (`aria-live="polite"`).
- Status codes: `TRANSMITTING...` → `MESSAGE_ACCEPTED` (success, tertiary)
  or `TRANSMISSION_FAILED` / `NETWORK_ERROR_TRY_AGAIN` (error, red).
- Submit button disabled during request, re-enabled in `finally`.

---

## 8. Key Reference Documents

| Document                          | Contents                                     |
|:----------------------------------|:---------------------------------------------|
| `README.md`                       | Full dev guide, build workflow, Vercel setup  |
| `DESIGN.md`                       | Kinetic Blueprint design manifesto            |
| `.github/copilot-instructions.md` | Global AI agent coding rules                  |
| `refrence docs/Animesh's Resume.pdf` | Career data grounding portfolio content    |

---

## 9. Workflow Checklist

When making any change to this project, follow this sequence:

1. **Identify the correct source file.** Never edit `index.html` directly.
2. **Apply the Kinetic Blueprint rules.** 0px radius, named tokens, no
   dividers, correct font families, `.param-input` for forms.
3. **Rebuild.** Run `python scripts/build_site.py`.
4. **Verify.** Confirm `index.html` was regenerated and check in browser.
5. **Backend changes.** If touching `api/`, ensure the security layers
   remain intact and no secrets are committed. A new deployed file must be
   allowed in `.vercelignore`.

---

## 10. Common Pitfalls to Avoid

- ❌ Editing `index.html` directly (it gets overwritten on rebuild)
- ❌ Adding `rounded-*` classes or any `border-radius` > 0px
- ❌ Using raw hex colors instead of Tailwind tokens
- ❌ Adding `<hr>` or border-based section dividers
- ❌ Using `ring-*` or `border-*` on form inputs (use `.param-input`)
- ❌ Committing secrets or `.env*` files to git
- ❌ Adding `<html>`, `<head>`, or `<body>` tags inside section fragments
- ❌ Forgetting to rebuild after editing source files
- ❌ Using friendly/rounded icons (must be Material Symbols thin stroke)
