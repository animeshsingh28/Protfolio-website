---
description: "Use when editing css/design-tokens.css. Covers custom CSS atoms, grid styling, form input styling, and global visual tokens for the portfolio source."
applyTo: "css/design-tokens.css"
---
# Design Tokens CSS Rules

- Keep `css/design-tokens.css` limited to shared custom CSS atoms and global selectors.
- Preserve `.blueprint-grid`, `.material-symbols-outlined`, `::selection`, and `.param-input` as the primary custom styling hooks.
- Do not introduce rounded corners or border-radius values that conflict with the zero-radius design rule.
- Prefer existing Tailwind tokens and design-system values when adding new CSS declarations.
- Avoid component-specific layout styling here when the same change belongs in a section fragment.
- If a CSS change affects rendered output, rebuild and review `index.html` afterward.
