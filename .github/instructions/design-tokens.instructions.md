---
description: "Use when editing css/design-tokens.css. Covers custom CSS atoms, grid styling, form input styling, and global visual tokens for the portfolio source."
applyTo: "css/design-tokens.css"
---
# Design Tokens CSS Rules

- Keep `css/design-tokens.css` limited to shared custom CSS atoms and global selectors.
- This file is the Tailwind input: keep the three `@tailwind` directives, put `:root` tokens and global selectors in `@layer base` and custom classes in `@layer components` (so utilities on the same element still win). Never edit the compiled `css/site.css`.
- Preserve `.blueprint-grid`, `::selection`, and `.param-input` as the primary custom styling hooks.
- Do not introduce rounded corners or border-radius values that conflict with the zero-radius design rule.
- Prefer existing Tailwind tokens and design-system values when adding new CSS declarations.
- Avoid component-specific layout styling here when the same change belongs in a section fragment.
- After any change, run `python scripts/build_site.py` (regenerates `css/site.css`, `index.html`, and the other build outputs; needs Node.js for `npx`) and commit every regenerated file.
