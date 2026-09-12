#!/usr/bin/env python3
"""Post-process MyST static HTML for public-site SEO.

Adds absolute canonical URLs, absolute Open Graph image URLs, and JSON-LD
that MyST does not emit. Does not mark Paper notes as ScholarlyArticle.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ORIGIN = "https://shishirshakya.github.io"

HOME_JSONLD = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "name": "Dr. Shishir Shakya",
            "url": f"{ORIGIN}/",
        },
        {
            "@type": "ProfilePage",
            "name": "Dr. Shishir Shakya",
            "url": f"{ORIGIN}/",
            "mainEntity": {
                "@type": "Person",
                "name": "Shishir Shakya",
                "url": f"{ORIGIN}/",
                "jobTitle": "Assistant Professor of Economics",
                "affiliation": {
                    "@type": "Organization",
                    "name": "Appalachian State University",
                },
                "image": f"{ORIGIN}/files/headshot.webp",
                "sameAs": [
                    "https://orcid.org/0000-0002-6272-6654",
                    "https://scholar.google.com/citations?user=mvYtqK8AAAAJ&hl=en",
                    "https://economics.appstate.edu/directory/shishir-shakya-phd",
                ],
            },
        },
    ],
}


def public_url(html_dir: Path, html_path: Path) -> str:
    rel = html_path.relative_to(html_dir).as_posix()
    if rel == "index.html":
        return f"{ORIGIN}/"
    if rel.endswith("/index.html"):
        return f"{ORIGIN}/{rel[: -len('index.html')]}"
    return f"{ORIGIN}/{rel}"


def inject_head(html: str, snippet: str) -> str:
    if snippet in html:
        return html
    if "</head>" not in html:
        return html
    return html.replace("</head>", snippet + "</head>", 1)


def jsonld_script(data: object) -> str:
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    return f'<script type="application/ld+json">{payload}</script>'


def article_jsonld(url: str, title: str, date: str, description: str) -> dict:
    article: dict = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "url": url,
        "datePublished": date,
        "author": {
            "@type": "Person",
            "name": "Shishir Shakya",
            "url": f"{ORIGIN}/",
        },
    }
    if description:
        article["description"] = description
    return article


def process_file(html_dir: Path, html_path: Path) -> bool:
    html = html_path.read_text(encoding="utf-8")
    original = html
    url = public_url(html_dir, html_path)
    rel = html_path.relative_to(html_dir).as_posix()

    html = html.replace('content="/build/', f'content="{ORIGIN}/build/')
    html = html.replace('content="/favicon', f'content="{ORIGIN}/favicon')

    if 'rel="canonical"' not in html:
        html = inject_head(html, f'<link rel="canonical" href="{url}"/>')

    if rel == "index.html":
        html = inject_head(html, jsonld_script(HOME_JSONLD))

    grain = re.match(
        r"book/grain-of-salt/(\d{4}-\d{2}-\d{2})-[^/]+/index.html$", rel
    )
    if grain:
        title_m = re.search(r"<title>([^<]+)</title>", html)
        title = (title_m.group(1) if title_m else "").split(" - ")[0].strip()
        desc_m = re.search(
            r'<meta name="description" content="([^"]*)"', html
        )
        description = desc_m.group(1) if desc_m else ""
        html = inject_head(
            html,
            jsonld_script(
                article_jsonld(url, title, grain.group(1), description)
            ),
        )

    if html != original:
        html_path.write_text(html, encoding="utf-8")
        return True
    return False


def main() -> int:
    html_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_build/html")
    if not html_dir.is_dir():
        print(f"Error: {html_dir} is not a directory")
        return 1
    changed = 0
    for path in html_dir.rglob("*.html"):
        if process_file(html_dir, path):
            changed += 1
    print(f"seo html files updated: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
