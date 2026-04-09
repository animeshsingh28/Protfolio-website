---
description: "Use when syncing resume, CV, work history, dates, skills, links, achievements, or project facts into one named section of the modular portfolio source without changing layout or styling."
name: "Resume Sync Section"
argument-hint: "Section name + resume-driven content update"
agent: "agent"
---
Sync resume facts into exactly one section in the modular portfolio source, using the existing top-level HTML comment headers as hard edit boundaries.

Primary source:
- [refrence docs/Animesh's Resume.pdf](../../refrence docs/Animesh's Resume.pdf)

Valid source targets:
- `sections/header-nav.html` with `<!-- Header/nav -->`
- `sections/hero.html` with `<!-- Hero -->`
- `sections/selected-work.html` with `<!-- Selected work -->`
- `sections/philosophy.html` with `<!-- Philosophy -->`
- `sections/metrics.html` with `<!-- Metrics -->`
- `sections/contact.html` with `<!-- Contact -->`
- `sections/footer.html` with `<!-- Footer -->`

Rules:
- Update content only: names, titles, dates, summaries, project details, metrics, skills, links, and factual labels.
- Do not change layout, spacing, class names, typography, colors, structure, or component patterns.
- Match my requested section to one of the exact source files and comment labels above before making changes.
- Edit only the matching section fragment unless I explicitly ask for multi-section syncing.
- Do not modify any other section unless I explicitly ask for multi-section syncing.
- If resume facts conflict with the current page, prefer the resume and make the wording internally consistent within the target section.
- If the resume does not clearly support the requested change, stop and say what is missing.
- Follow [portfolio-html.instructions.md](../instructions/portfolio-html.instructions.md).

Workflow:
1. Find the exact matching section file in [sections](../../sections) and confirm its top-level comment marker.
2. Read the relevant resume facts from [refrence docs/Animesh's Resume.pdf](../../refrence docs/Animesh's Resume.pdf).
3. Identify only the factual text that should change.
4. Edit only the target section fragment.
5. Verify that structure and styling were left untouched.
6. Note that `python scripts/build_site.py` should be run after source edits.
7. Summarize what facts were updated.

Output format:
- Target section: <section name>
- Resume facts applied: <bullet-style sentence or short list>
- Text changed: <what was updated>
- Unchanged sections: <list>
- Notes: <only if facts were ambiguous or incomplete>