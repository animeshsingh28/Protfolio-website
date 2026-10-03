---
description: "Use when editing section fragment files under sections/. Covers fragment boundaries, section ownership, and modular HTML rules for the portfolio source."
applyTo: "sections/**/*.html"
---
# Section Fragment Rules

- Each fragment must begin with its exact top-level section marker comment.
- Allowed fragment names are `header-nav.html`, `hero.html`, `selected-work.html`, `philosophy.html`, `metrics.html`, `contact.html`, and `footer.html`.
- Keep fragments self-contained, but do not add document-level tags such as `<html>`, `<head>`, or `<body>`.
- Do not duplicate the Tailwind config, global font links, or global script tags inside a fragment.
- Preserve the established section structure and Kinetic Blueprint visual language.
- If a change spans multiple fragments, make that explicit rather than silently editing adjacent sections.
- Rebuild `index.html` with `python scripts/build_site.py` after fragment edits.
