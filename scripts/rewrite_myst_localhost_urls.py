#!/usr/bin/env python3
"""Rewrite MyST static-build localhost URLs to the public GitHub Pages origin.

MyST writes http://localhost:3000 into robots.txt and sitemap.xml (mystmd#2695).
This site is served at https://shishirshakya.github.io/ with no BASE_URL.
"""

from pathlib import Path
import sys

ORIGIN = "https://shishirshakya.github.io"
OLD = "http://localhost:3000"
FILES = ("robots.txt", "sitemap.xml", "sitemap_style.xsl")


def main() -> int:
    html_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_build/html")
    sitemap = html_dir / "sitemap.xml"
    robots = html_dir / "robots.txt"
    if not sitemap.is_file() or not robots.is_file():
        print(f"Error: expected robots.txt and sitemap.xml under {html_dir}")
        return 1

    rewritten = []
    for name in FILES:
        path = html_dir / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if OLD not in text:
            continue
        path.write_text(text.replace(OLD, ORIGIN), encoding="utf-8")
        rewritten.append(name)

    leftover = []
    for name in FILES:
        path = html_dir / name
        if path.is_file() and OLD in path.read_text(encoding="utf-8"):
            leftover.append(name)
    if leftover:
        print(f"Error: still contains {OLD}: {leftover}")
        return 1

    print(f"rewritten: {rewritten or 'none (already public origin)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
