#!/usr/bin/env python3
"""
Generate themed publication pages from book/cv/publications.md (four themes).

Usage:
    python scripts/generate_publications_md.py          # Generate files
    python scripts/generate_publications_md.py --check  # Check if files are up-to-date (for CI)
"""

import html
import re
import sys
from pathlib import Path
from typing import Dict, List

# MyST turns Markdown links to DOI-like URLs into citations and appends a References
# section. Raw <a href="..."> avoids that while keeping the same target URL.
_MD_LINK = re.compile(r"\[([^\]]*)\]\((https?://[^)]+)\)")


def _url_triggers_myst_citation(url: str) -> bool:
    u = url.lower()
    if "doi.org" in u:
        return True
    if "/doi/" in u:
        return True
    if "link.springer.com/article" in u:
        return True
    return False


def _myst_safe_publication_line(text: str) -> str:
    def repl(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        if not _url_triggers_myst_citation(url):
            return m.group(0)
        return (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape(label)}</a>"
        )

    return _MD_LINK.sub(repl, text)


_PUB_LINE_START = re.compile(r"^(\d+\.\s+)(.+)$")


def sanitize_publications_master_file(text: str) -> str:
    """Rewrite DOI-like Markdown links on numbered publication lines in publications.md."""
    out: List[str] = []
    for line in text.splitlines(keepends=True):
        if line.endswith("\r\n"):
            body, ending = line[:-2], "\r\n"
        elif line.endswith("\n"):
            body, ending = line[:-1], "\n"
        else:
            body, ending = line, ""
        m = _PUB_LINE_START.match(body)
        if m:
            prefix, rest = m.group(1), m.group(2)
            out.append(prefix + _myst_safe_publication_line(rest) + ending)
        else:
            out.append(line)
    return "".join(out)


# SUD: matched in the same max-count pass as the other three themes. On ties, SUD
# is preferred over healthcare (see TIE priority) so opioid/SUD work lists here.
SUD_KEYWORDS = [
    'substance use disorder', 'substance use and addiction', 'journal of substance use',
    'substance use certificate',  # e.g. CoN and SUD treatment
    'opioid', 'addiction', 'alcohol depend', 'drug and alcohol',
    'prescription drug monitoring', 'retail opioid', 'opioid sales', 'opioid supply',
    'opioid spillover', 'opioid prescribing', 'medicaid expansion and opioid',
    'pdmp', 'must access prescription', 'county-level opioid', 'retail pharmacy',
]

# Category mapping based on keywords in titles/journals
HEALTHCARE_KEYWORDS = [
    'health', 'nurse', 'physician', 'pharmacist', 'hospital',
    'medicare', 'medicaid', 'medical', 'maternity', 'mental health',
    'prescription', 'care', 'provider', 'clinical', 'pharmacy',
    'treatment', 'patient', 'doctor', 'nursing', 'practitioner',
    'primary care', 'hospital ownership', 'maternity', 'rural health',
]

INSTITUTIONAL_KEYWORDS = [
    'revolution', 'corruption', 'institutional', 'public choice',
    'political economy', 'regime', 'market legitimacy', 'library',
    'energy', 'shale', 'fracking', 'entrepreneurship', 'economic freedom',
    'startup', 'lumber', 'abortion', 'regulation', 'polyarchy', 'democracy',
    'governance', 'transparency', 'certificate-of-need', 'licensing'
]

EDUCATION_KEYWORDS = [
    'replicability', 'reproducibility', 'grading', 'teaching', 'education',
    'test scores', 'gender gap', 'university entrance', 'score', 'student',
    'learning', 'assessment', 'exam', 'classroom'
]

# When scores tie, pick the first in this list (specific themes before broad).
_TIE_PRIORITY = ['sud', 'education', 'healthcare', 'institutional']


def classify_publication(text: str) -> str:
    """Classify a publication by keyword counts; ties use _TIE_PRIORITY."""
    text_lower = text.lower()

    if 'opioid' in text_lower:
        return 'sud'

    sud_count = sum(1 for kw in SUD_KEYWORDS if kw in text_lower)
    healthcare_count = sum(1 for kw in HEALTHCARE_KEYWORDS if kw in text_lower)
    institutional_count = sum(1 for kw in INSTITUTIONAL_KEYWORDS if kw in text_lower)
    education_count = sum(1 for kw in EDUCATION_KEYWORDS if kw in text_lower)

    counts = {
        'sud': sud_count,
        'healthcare': healthcare_count,
        'institutional': institutional_count,
        'education': education_count,
    }
    best = max(counts.values())
    if best == 0:
        return 'institutional'
    top = [k for k, v in counts.items() if v == best]
    if len(top) == 1:
        return top[0]
    for key in _TIE_PRIORITY:
        if key in top:
            return key
    return top[0]

def parse_publications(content: str) -> List[str]:
    """Extract numbered publications from markdown content"""
    # Find the publications list (starts after the main heading in publications.md)
    match = re.search(r'# All publications\n\n(.+)', content, re.DOTALL)
    if not match:
        return []

    pub_section = match.group(1)

    # Split on line-start "N. " so item 1 is not dropped (it has no leading newline).
    items = re.split(r'(?m)^\d+\.\s+', pub_section)
    return [p.strip() for p in items if p.strip()]

def categorize_publications(publications: List[str]) -> Dict[str, List[str]]:
    """Categorize publications into four themes."""
    categorized = {
        'healthcare': [],
        'sud': [],
        'institutional': [],
        'education': [],
    }

    for pub in publications:
        category = classify_publication(pub)
        categorized[category].append(pub)

    return categorized

def generate_category_file(category: str, publications: List[str], output_path: Path):
    """Generate a themed publication markdown file"""

    titles = {
        'healthcare': 'Healthcare and Labor Economics',
        'sud': 'Substance Use Disorder',
        'institutional': 'Institutional Economics',
        'education': 'Education and Teaching Economics',
    }

    t = titles[category]
    # Frontmatter must be the first bytes in the file (no HTML comment above it), or MyST
    # will not parse YAML and will render "title: ..." as visible content.
    content = f"""---
title: {t}
---

<!-- Generated by scripts/generate_publications_md.py. Do not edit by hand. -->

"""

    for i, pub in enumerate(publications, 1):
        content += f"{i}. {_myst_safe_publication_line(pub)}\n\n"

    output_path.write_text(content, encoding='utf-8')

def main():
    check_mode = '--check' in sys.argv

    # Paths
    base = Path(__file__).parent.parent
    source = base / 'book' / 'cv' / 'publications.md'
    output_dir = base / 'book' / 'cv'

    # Read source
    if not source.exists():
        print(f"Error: {source} not found")
        sys.exit(1)

    content = source.read_text(encoding='utf-8')
    master_sanitized = sanitize_publications_master_file(content)
    if master_sanitized != content:
        if check_mode:
            print("Error: book/cv/publications.md needs link sanitization for MyST.")
            print("Run: python scripts/generate_publications_md.py (without --check)")
            sys.exit(1)
        source.write_text(master_sanitized, encoding='utf-8')
        print(f"Updated: {source}")
        content = master_sanitized

    # Parse and categorize
    publications = parse_publications(content)
    categorized = categorize_publications(publications)

    # Generate files
    files = {
        'healthcare': output_dir / 'publications-healthcare-labor-economics.md',
        'sud': output_dir / 'publications-substance-use-disorder.md',
        'institutional': output_dir / 'publications-institutional-economics.md',
        'education': output_dir / 'publications-education-teaching-economics.md',
    }

    if check_mode:
        # Check if files are up-to-date
        all_match = True
        for category, filepath in files.items():
            if not filepath.exists():
                print(f"Error: {filepath} does not exist")
                all_match = False
                continue

            # Generate expected content
            import tempfile
            temp_path = Path(tempfile.mktemp())
            generate_category_file(category, categorized[category], temp_path)
            expected = temp_path.read_text(encoding='utf-8')
            actual = filepath.read_text(encoding='utf-8')
            temp_path.unlink()

            if expected != actual:
                print(f"Error: {filepath} is out of date")
                print("Run: python scripts/generate_publications_md.py")
                all_match = False

        if not all_match:
            sys.exit(1)
        else:
            print("All publication files are up-to-date")
    else:
        # Generate files
        for category, filepath in files.items():
            generate_category_file(category, categorized[category], filepath)
            print(f"Generated: {filepath}")

if __name__ == '__main__':
    main()
