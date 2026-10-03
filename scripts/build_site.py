from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "src" / "index.template.html"
OUTPUT_PATH = ROOT / "index.html"
# Standalone page Vercel serves for unknown paths (partials applied).
NOT_FOUND_SOURCE = ROOT / "src" / "404.html"
NOT_FOUND_OUTPUT = ROOT / "404.html"
# Canonical origin, matching the template's canonical/og:url/JSON-LD URLs.
SITE_URL = "https://hornsloth.com/"
ROBOTS_OUTPUT = ROOT / "robots.txt"
SITEMAP_OUTPUT = ROOT / "sitemap.xml"
SECTION_DIR = ROOT / "sections"
# Shared <head> snippets: <!-- PARTIAL:<name> --> -> src/partials/<name>.html,
# so the page and the 404 page can't drift apart (e.g. font weights).
PARTIAL_DIR = ROOT / "src" / "partials"
PARTIAL_RE = re.compile(r"<!-- PARTIAL:([a-z0-9-]+) -->")
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


def apply_partials(html: str) -> str:
    return PARTIAL_RE.sub(lambda match: read_text(PARTIAL_DIR / f"{match.group(1)}.html").rstrip(), html)


def build_html() -> None:
    html = apply_partials(read_text(TEMPLATE_PATH))

    for marker, filename in SECTION_ORDER:
        placeholder = f"<!-- SECTION:{marker} -->"
        section_html = read_text(SECTION_DIR / filename).rstrip()
        if placeholder not in html:
            raise ValueError(f"Template placeholder not found: {placeholder}")
        html = html.replace(placeholder, section_html)

    OUTPUT_PATH.write_text(f"{html.rstrip()}\n", encoding="utf-8")


def build_not_found() -> None:
    html = apply_partials(read_text(NOT_FOUND_SOURCE))
    NOT_FOUND_OUTPUT.write_text(f"{html.rstrip()}\n", encoding="utf-8")


def build_seo_files() -> None:
    # No <lastmod>: a build date would make every rebuild differ, and search
    # engines ignore lastmod values that aren't accurate anyway.
    ROBOTS_OUTPUT.write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8"
    )
    SITEMAP_OUTPUT.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}</loc></url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )


OUTPUTS = (CSS_OUTPUT, OUTPUT_PATH, NOT_FOUND_OUTPUT, ROBOTS_OUTPUT, SITEMAP_OUTPUT)


def build_site() -> None:
    build_css()
    build_html()
    build_not_found()
    build_seo_files()


if __name__ == "__main__":
    build_site()
    for path in OUTPUTS:
        print(f"Built {path}")
