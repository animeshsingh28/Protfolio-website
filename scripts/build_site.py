from __future__ import annotations

import os
import subprocess
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

# Tailwind is compiled with a pinned CLI fetched by npx (Node.js required);
# there is no package.json. Change the version here only, and rebuild.
TAILWIND_VERSION = "3.4.17"
# Autoprefixer target, set explicitly so a BROWSERSLIST env var or a
# browserslist config in a parent directory can't change the output.
BROWSERSLIST_QUERY = "defaults"
TAILWIND_CONFIG = ROOT / "tailwind.config.js"
CSS_INPUT = ROOT / "css" / "design-tokens.css"
CSS_OUTPUT = ROOT / "css" / "site.css"


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def build_css() -> None:
    for path in (TAILWIND_CONFIG, CSS_INPUT):
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")

    npx = "npx.cmd" if os.name == "nt" else "npx"
    command = [
        npx,
        "--yes",
        # Use the cached CLI without a registry round-trip, so a warm cache
        # builds offline; the exact version pin keeps this safe.
        "--prefer-offline",
        f"tailwindcss@{TAILWIND_VERSION}",
        "--config", str(TAILWIND_CONFIG.relative_to(ROOT)),
        "--input", str(CSS_INPUT.relative_to(ROOT)),
        "--output", str(CSS_OUTPUT.relative_to(ROOT)),
        "--minify",
    ]
    # The CLI bundles its own autoprefixer/caniuse data, but which browsers it
    # targets comes from the environment (BROWSERSLIST, .browserslistrc or a
    # package.json "browserslist" key in any parent directory). Pin the query
    # so the output depends only on TAILWIND_VERSION and the sources, and
    # silence the "caniuse-lite is outdated" nag about the bundled data.
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("BROWSERSLIST_CONFIG", "BROWSERSLIST_ENV")
    }
    env["BROWSERSLIST"] = BROWSERSLIST_QUERY
    env["BROWSERSLIST_IGNORE_OLD_DATA"] = "1"
    try:
        # cwd=ROOT so the config's relative content globs resolve to the repo.
        subprocess.run(command, cwd=ROOT, env=env, check=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Tailwind build failed: '{npx}' not found. Install Node.js (with npm) and retry."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"Tailwind build failed (exit code {exc.returncode}): {' '.join(command)}"
        ) from exc

    if not CSS_OUTPUT.exists() or CSS_OUTPUT.stat().st_size == 0:
        raise SystemExit(f"Tailwind build produced no output at {CSS_OUTPUT}")


def build_html() -> None:
    html = read_text(TEMPLATE_PATH)

    for marker, filename in SECTION_ORDER:
        placeholder = f"<!-- SECTION:{marker} -->"
        section_html = read_text(SECTION_DIR / filename).rstrip()
        if placeholder not in html:
            raise ValueError(f"Template placeholder not found: {placeholder}")
        html = html.replace(placeholder, section_html)

    OUTPUT_PATH.write_text(f"{html.rstrip()}\n", encoding="utf-8")


def build_site() -> None:
    build_css()
    build_html()


if __name__ == "__main__":
    build_site()
    print(f"Built {CSS_OUTPUT}")
    print(f"Built {OUTPUT_PATH}")
