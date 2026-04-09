---
description: "Use when editing one section of the modular portfolio source without affecting other sections. Good for header, hero, selected work, philosophy, metrics, contact, or footer updates."
name: "Edit Single Section"
argument-hint: "Section name + requested change"
agent: "agent"
---
Edit exactly one section in the modular portfolio source.

Use the existing top-level HTML comment headers as hard edit boundaries. The source files are:
- `sections/header-nav.html` with `<!-- Header/nav -->`
- `sections/hero.html` with `<!-- Hero -->`
- `sections/selected-work.html` with `<!-- Selected work -->`
- `sections/philosophy.html` with `<!-- Philosophy -->`
- `sections/metrics.html` with `<!-- Metrics -->`
- `sections/contact.html` with `<!-- Contact -->`
- `sections/footer.html` with `<!-- Footer -->`

Requirements:
- Identify the target section from my request before editing.
- Match my requested section to one of the exact source files and comment labels above before making changes.
- Edit only the corresponding section fragment unless the request explicitly requires a template-level change.
- Do not modify any other section unless the change is truly global and necessary.
- Preserve the existing layout, class structure, and design language unless I explicitly ask for structural or styling changes.
- Follow [portfolio-html.instructions.md](../instructions/portfolio-html.instructions.md).
- If my request is ambiguous or spans multiple sections, ask me to narrow it down.
- When finished, summarize exactly what changed, confirm which sections were intentionally left untouched, and note whether `index.html` should be rebuilt.

Preferred workflow:
1. Find the exact matching section file in [sections](../../sections) and confirm its top-level comment marker.
2. State the target section and the planned change.
3. Edit only that fragment.
4. Verify no unrelated section fragments were changed.
5. Note that `python scripts/build_site.py` should be run after source edits.
6. Return a concise summary.

Output format:
- Target section: <section name>
- Change made: <what changed>
- Unchanged sections: <list>
- Notes: <only if something required clarification, a global edit, or a rebuild>