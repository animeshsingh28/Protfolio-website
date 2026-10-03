from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "src" / "index.template.html"
OUTPUT_PATH = ROOT / "index.html"
SECTION_DIR = ROOT / "sections"
SECTION_ORDER = [
    ("header-nav", "header-nav.html"),
    ("hero", "hero.html"),
    ("selected-work", "selected-work.html"),
    ("philosophy", "philosophy.html"),
    ("metrics", "metrics.html"),
    ("contact", "contact.html"),
    ("footer", "footer.html"),
]


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def build_site() -> None:
    html = read_text(TEMPLATE_PATH)

    for marker, filename in SECTION_ORDER:
        placeholder = f"<!-- SECTION:{marker} -->"
        section_html = read_text(SECTION_DIR / filename).rstrip()
        if placeholder not in html:
            raise ValueError(f"Template placeholder not found: {placeholder}")
        html = html.replace(placeholder, section_html)

    OUTPUT_PATH.write_text(f"{html.rstrip()}\n", encoding="utf-8")


if __name__ == "__main__":
    build_site()
    print(f"Built {OUTPUT_PATH}")
