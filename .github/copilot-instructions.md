# Portfolio Website — Copilot Instructions

## Project Overview

Modular static Data Engineer portfolio website with a generated entry page (`index.html`). Source content is split across a template, section fragments, shared CSS, and shared JS.

## Architecture

- **Generated entry page**: `index.html` is the deployable output, built from source files
- **Template source**: `src/index.template.html` contains the page shell, head, Tailwind config, and section placeholders
- **Section fragments**: `sections/*.html` contain the top-level content regions (`header-nav`, `hero`, `selected-work`, `philosophy`, `metrics`, `contact`, `footer`)
- **Shared assets**: `css/design-tokens.css` contains custom CSS atoms and `js/form-handler.js` contains contact form behavior
- **Build script**: `scripts/build_site.py` assembles the template and section fragments into `index.html`
- **Tailwind via CDN**: `https://cdn.tailwindcss.com?plugins=container-queries` — do not add the `forms` plugin; its base input styles load after `css/design-tokens.css` and override `.param-input`
- **Tailwind config** remains inlined in the template `<head>` via `<script id="tailwind-config">`
- **No frontend framework**: keep the architecture static and minimal; rebuild with `python scripts/build_site.py`

## Design System — "The Kinetic Blueprint"

Full spec is in `DESIGN.md`. Key rules that must never be violated:

### Colors (all defined as Tailwind tokens in the inline config)
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

- Tailwind utility classes only — no additional CSS files, no inline `style=` attributes unless a value is not expressible as a utility
- Use `src/index.template.html`, `sections/*.html`, `css/design-tokens.css`, and `js/form-handler.js` as the editable source files; treat root `index.html` as generated output
- Custom CSS atoms live in `css/design-tokens.css`; extend them there instead of reintroducing inline `<style>` blocks
- Section fragments must keep their top-level exact comment markers: `<!-- Header/nav -->`, `<!-- Hero -->`, `<!-- Selected work -->`, `<!-- Philosophy -->`, `<!-- Metrics -->`, `<!-- Contact -->`, `<!-- Footer -->`
- Section structure: `<section>` → `<div class="max-w-7xl mx-auto">` → content
- Icons: `<span class="material-symbols-outlined" data-icon="...">icon_name</span>`
- `data-icon` attribute mirrors the icon name for easy search/replace
- After editing source fragments or shared assets, rebuild `index.html` with `python scripts/build_site.py`
