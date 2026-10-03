# Portfolio Website — Copilot Instructions

## Project Overview

Modular static Data Engineer portfolio website with a generated entry page (`index.html`). Source content is split across a template, section fragments, shared CSS, and shared JS.

## Architecture

- **Generated entry page**: `index.html` is the deployable output, built from source files
- **Template source**: `src/index.template.html` contains the page shell, head, the `/css/site.css` link, and section placeholders
- **Section fragments**: `sections/*.html` contain the top-level content regions (`header-nav`, `hero`, `selected-work`, `philosophy`, `metrics`, `contact`, `footer`)
- **Shared assets**: `css/design-tokens.css` is the Tailwind input (`@tailwind` directives, `:root` tokens, custom CSS atoms) and `js/form-handler.js` contains contact form behavior
- **Tailwind config**: root `tailwind.config.js` (Tailwind v3.4: colors, fonts, zeroed radius scale, `content` globs, safelist). No plugins — do not add the `forms` plugin; its base input styles would override `.param-input`
- **Build script**: `scripts/build_site.py` compiles `css/design-tokens.css` into the minified, committed `css/site.css` (pinned `npx tailwindcss@3.4.17`, so Node.js is required) and assembles the template and section fragments into `index.html`; it also copies `src/404.html` (standalone, absolute links) to `404.html` and writes `robots.txt` and `sitemap.xml`
- **Content-Security-Policy** (in `vercel.json`): no inline scripts, inline styles, or `style=` attributes; new external hosts (scripts, styles, fonts, images, fetch targets) must be added to the policy
- **No frontend framework**: keep the architecture static and minimal; rebuild with `python scripts/build_site.py`

## Design System — "The Kinetic Blueprint"

Full spec is in `DESIGN.md`. Key rules that must never be violated:

### Colors (all defined as Tailwind tokens in `tailwind.config.js`)
| Role | Token | Hex |
|------|-------|-----|
| Background | `bg-background` | `#111316` |
| Primary accent | `text-primary` / `bg-primary` | `#FFB59E` |
| CTA / Highlight | `bg-primary-container` | `#FF571A` |
| Cyan accent | `text-tertiary` | `#00DAF3` |
| Surface cards | `bg-surface-container-low` | `#1A1C1F` |

Always use the named Tailwind tokens (`bg-surface-container-high`, `text-on-surface`, etc.) rather than raw hex values, except where a token does not exist.

### Typography
- **Headlines / Labels**: `font-headline` → Space Grotesk, tracked tight, uppercase
- **Body copy**: `font-body` → Inter
- **Technical data, metadata, code**: `font-mono` → JetBrains Mono, `uppercase`, `tracking-widest`
- Metadata labels use `text-[9px]` or `text-[10px]` with `tracking-[0.2em]`

### Non-negotiable visual rules
- **0px border-radius everywhere** — no `rounded-*` classes, no `border-radius` CSS
- **No dividers/horizontal rules** — section separation is done through tonal surface color shifts only
- **No friendly/rounded icons** — use Material Symbols Outlined with `wght=300` (thin stroke)
- **Blueprint grid** — main content sits on `.blueprint-grid` (48px offset grid defined in `css/design-tokens.css`)
- **Dark mode only** — `<html class="dark">` is always set; do not add light-mode variants

### Component patterns
- **Buttons**: sharp corners, `active:translate-y-1 transition-transform` for press feedback
- **Cards**: `bg-surface-container-low hover:border-primary-container/30` — border appears on hover only
- **Status chips**: rectangular, `text-tertiary` for active/live, `text-error` for failure
- **Section labels**: monospace, 10px, all-caps, e.g. `DEPLOYMENT_LOG.XLSX`, `BUILD: SUCCESSFUL`
- **Breadcrumbs**: use `/` separator in monospace, mimicking file paths
- **Form inputs** (`param-input` CSS class — defined in `css/design-tokens.css`): `background: transparent`, no border except `border-bottom: 2px solid outline-variant/50`; focus shifts bottom border to `primary`. Placeholders are uppercase monospace. Apply to both `<input>` and `<textarea>`. **Never** use Tailwind's `ring-*` or `border-*` on form elements — use this class instead.

## Conventions

- Tailwind utility classes only — no additional CSS files and no inline `style=` attributes (the CSP blocks them); use an arbitrary-value utility such as `text-[10px]` instead
- Use `src/index.template.html`, `sections/*.html`, `css/design-tokens.css`, `tailwind.config.js`, and `js/form-handler.js` as the editable source files; treat root `index.html`, `404.html`, `robots.txt`, `sitemap.xml`, and `css/site.css` as generated output
- Custom CSS atoms live in `css/design-tokens.css`; extend them there instead of reintroducing inline `<style>` blocks
- Section fragments must keep their top-level exact comment markers: `<!-- Header/nav -->`, `<!-- Hero -->`, `<!-- Selected work -->`, `<!-- Philosophy -->`, `<!-- Metrics -->`, `<!-- Contact -->`, `<!-- Footer -->`
- Section structure: `<section>` → `<div class="max-w-7xl mx-auto">` → content
- Icons: `<span aria-hidden="true" class="material-symbols-outlined" data-icon="...">icon_name</span>`
- `data-icon` attribute mirrors the icon name for easy search/replace
- The icon font is subset: add any new icon to `icon_names=` (alphabetical) in the template's Material Symbols link, or it renders as plain text
- After editing source fragments or shared assets, rebuild with `python scripts/build_site.py` and commit every regenerated output (Vercel serves the committed files; it has no build step)
