import os
import re
import sys
import pymupdf

sys.path.insert(0, os.path.abspath("scripts"))
from generate_question import match_skills_in_text, CANONICAL_SKILL_NAMES

def clean_document_pages(pages: list[str]) -> tuple[str, list[str]]:
    """
    Generic cleanup across PDF pages:
    - Detects repeated page headers and footers across pages.
    - Removes pagination lines ("Page 1 of 2", "Page 2", etc.).
    - Removes continuation headers ("PROFESSIONAL EXPERIENCE (CONTINUED)", etc.).
    - Normalizes unicode artifacts and excessive whitespace.
    """
    if not pages:
        return "", []

    cleaned_page_lines = []
    
    # 1. Detect candidate repeated headers/footers across pages
    # Check top 3 lines and bottom 3 lines of each page
    header_counts = {}
    footer_counts = {}
    num_pages = len(pages)

    for p in pages:
        lines = [l.strip() for l in p.split("\n") if l.strip()]
        top_lines = lines[:3]
        bottom_lines = lines[-3:] if len(lines) >= 3 else lines
        
        for l in top_lines:
            header_counts[l] = header_counts.get(l, 0) + 1
        for l in bottom_lines:
            footer_counts[l] = footer_counts.get(l, 0) + 1

    # Lines repeated on multiple pages as header or footer
    repeated_headers = {l for l, count in header_counts.items() if num_pages > 1 and count >= 2}
    repeated_footers = {l for l, count in footer_counts.items() if num_pages > 1 and count >= 2}

    # Patterns for pagination and continuation
    PAGINATION_PATTERNS = [
        re.compile(r"^\s*page\s+\d+(\s*(?:of|/)\s*\d+)?\s*$", re.IGNORECASE),
        re.compile(r"^\s*\d+\s*(?:of|/)\s*\d+\s*$", re.IGNORECASE),
        re.compile(r"^\s*-\s*\d+\s*-\s*$", re.IGNORECASE),
        re.compile(r"^.*?\bcontinued\b.*$", re.IGNORECASE),
    ]

    for p in pages:
        lines = p.split("\n")
        kept_lines = []
        for line in lines:
            s = line.strip()
            if not s:
                kept_lines.append("")
                continue

            # Check if line is a repeated header/footer
            if s in repeated_headers or s in repeated_footers:
                continue

            # Check if line matches pagination or continuation
            if any(patt.match(s) for patt in PAGINATION_PATTERNS):
                continue

            kept_lines.append(line)

        cleaned_page_lines.append("\n".join(kept_lines))

    full_text = "\n".join(cleaned_page_lines)
    # Normalize common characters
    full_text = re.sub(r"\r\n", "\n", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = re.sub(r"[ \t]+", " ", full_text)

    return full_text.strip(), cleaned_page_lines

# Test on Marcus Chen resume
doc = pymupdf.open("uploads/2_31cde0f5.pdf")
pages = [p.get_text() for p in doc]
doc.close()

cleaned_full, cleaned_pages = clean_document_pages(pages)

# Check skills match
skills = match_skills_in_text(cleaned_full)
print("Skills detected on Marcus Chen resume (total: %d):" % len(skills))
import pprint
pprint.pprint(skills)

# Check that pagination is gone
assert "Page 1 of 2" not in cleaned_full
assert "Page 2 of 2" not in cleaned_full
assert "PROFESSIONAL EXPERIENCE (CONTINUED)" not in cleaned_full
assert "Marcus Chen \ufffd Resume & Curriculum Vitae" not in cleaned_full
print("CLEANUP ASSERTIONS PASSED!")
