---
description: "Use when editing the portfolio HTML source, section fragments, template, typography, colors, or layout. Enforces the Kinetic Blueprint design rules across the modular source files."
applyTo: "index.html, src/**/*.html, sections/**/*.html"
---
# Portfolio HTML Rules

- Use named Tailwind tokens instead of raw hex classes where possible.
- Do not use rounded classes or border-radius.
- Do not add dividers for section separation.
- Use font-headline, font-body, and font-mono consistently.
- Preserve the modular source architecture: `src/index.template.html` is the page shell and `sections/*.html` are the editable content sources.
- Treat root `index.html` as generated output; make source edits in the template or the relevant section fragment first.
- Keep the exact top-level section comment markers at the start of each fragment.
- Do not duplicate the document `<head>`, Tailwind config, or global script tags inside section fragments.
- Use the param-input class for form fields.
- Keep Material Symbols thin and technical.