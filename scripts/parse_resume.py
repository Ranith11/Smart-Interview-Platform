"""
SmartInterview — Resume Parser
Week 6: Parse a PDF resume and extract a structured candidate profile.

Usage:
    python scripts/parse_resume.py data/resumes/candidate.pdf
"""

import os
import re
import sys
import json

try:
    import pymupdf
except ImportError:
    print("ERROR: pymupdf is required. Install with: pip install pymupdf")
    sys.exit(1)

# Import central matching engine and taxonomy from generate_question
try:
    from scripts.generate_question import match_skills_in_text, CANONICAL_SKILL_NAMES
except ImportError:
    try:
        from generate_question import match_skills_in_text, CANONICAL_SKILL_NAMES
    except ImportError:
        import importlib.util
        from pathlib import Path
        _gq_path = str(Path(__file__).parent / "generate_question.py")
        _spec = importlib.util.spec_from_file_location("_gq_mod", _gq_path)
        _gq_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_gq_mod)
        match_skills_in_text = _gq_mod.match_skills_in_text
        CANONICAL_SKILL_NAMES = _gq_mod.CANONICAL_SKILL_NAMES


# Common section heading patterns (case-insensitive)
SECTION_PATTERNS = {
    "skills": [
        r"(?:core\s+)?(?:technical\s+)?competencies",
        r"(?:technical\s+)?skills",
        r"technical\s+expertise",
        r"technologies",
        r"tech(?:nical)?\s+stack",
        r"tools?\s*(?:&|and)?\s*technologies",
        r"programming\s+(?:languages|skills)",
    ],
    "projects": [
        r"(?:(?:academic|personal|technical|selected|key)\s+)*projects?.*",
        r"project\s+(?:experience|work)",
    ],
    "experience": [
        r"(?:work|professional|relevant)?\s*experience",
        r"employment(?:\s+history)?",
        r"internships?",
    ],
    "education": [
        r"education(?:al)?\s*(?:background|qualifications?)?",
        r"academic\s+background",
        r"qualifications?",
    ],
    "certifications": [
        r"(?:professional\s+)?certifications?",
        r"licenses?\s*(?:&|and)?\s*certifications?",
    ],
}


def clean_document_pages(pages: list[str]) -> tuple[str, list[str]]:
    """
    Generic cleanup across PDF pages:
    - Detects repeated page headers and footers across pages generically.
    - Removes pagination lines ("Page 1 of 2", "Page 2", etc.).
    - Removes continuation headers ("PROFESSIONAL EXPERIENCE (CONTINUED)", etc.).
    - Normalizes unicode artifacts and excessive whitespace.
    """
    if not pages:
        return "", []

    num_pages = len(pages)
    header_counts: dict[str, int] = {}
    footer_counts: dict[str, int] = {}

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

    cleaned_page_lines = []
    for p in pages:
        lines = p.split("\n")
        kept_lines = []
        for line in lines:
            s = line.strip()
            if not s:
                kept_lines.append("")
                continue

            if s in repeated_headers or s in repeated_footers:
                continue

            if any(patt.match(s) for patt in PAGINATION_PATTERNS):
                continue

            kept_lines.append(line)

        cleaned_page_lines.append("\n".join(kept_lines))

    full_text = "\n".join(cleaned_page_lines)
    # Normalize whitespace
    full_text = re.sub(r"\r\n", "\n", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = re.sub(r"[ \t]+", " ", full_text)

    return full_text.strip(), cleaned_page_lines


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file using PyMuPDF with generic cleanup."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    if not any(p.strip() for p in pages):
        print("ERROR: This PDF appears to contain no extractable text.")
        print("OCR support is not enabled. Please provide a text-based PDF.")
        sys.exit(1)

    cleaned_text, _ = clean_document_pages(pages)
    return cleaned_text, len(pages)


def find_sections(text):
    """Identify section boundaries in the resume text."""
    lines = text.split("\n")
    sections = {}
    section_order = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 80:
            continue

        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(r"^" + pattern + r"[\s:]*$", stripped, re.IGNORECASE):
                    section_order.append((section_name, i))
                    break

    # Determine end boundaries
    for idx, (name, start) in enumerate(section_order):
        if idx + 1 < len(section_order):
            end = section_order[idx + 1][1]
        else:
            end = len(lines)
        sections[name] = "\n".join(lines[start + 1 : end]).strip()

    return sections


def parse_skills(text):
    """Extract skills from a skills section using the central canonical taxonomy."""
    return match_skills_in_text(text)


def parse_projects(text):
    """Extract projects from a projects section."""
    projects = []
    lines = text.split("\n")
    current_project = None

    for line in lines:
        stripped = line.strip().lstrip("•-–—*·▪▸►").strip()
        if not stripped:
            continue

        if len(stripped) < 80 and (
            stripped[0].isupper()
            and not stripped.endswith(".")
            and len(stripped.split()) <= 10
        ):
            if current_project and not current_project["description"]:
                current_project["name"] += " | " + stripped
            else:
                if current_project:
                    projects.append(current_project)
                current_project = {"name": stripped, "description": "", "technologies": []}
        elif current_project:
            current_project["description"] += (" " + stripped).strip()
        else:
            current_project = {"name": stripped[:60], "description": stripped, "technologies": []}

    if current_project:
        projects.append(current_project)

    for p in projects:
        # Extract explicit technologies mentioned in project name or description
        p["technologies"] = match_skills_in_text(p["name"] + " " + p["description"])

    return projects


def parse_experience(text):
    """Extract experience entries from an experience section."""
    experiences = []
    lines = text.split("\n")
    current_exp = None

    for line in lines:
        stripped = line.strip().lstrip("•-–—*·▪▸►").strip()
        if not stripped:
            continue

        # Heuristic: role/company headers tend to be short and title-cased
        if len(stripped) < 80 and (
            stripped[0].isupper()
            and not stripped.endswith(".")
            and len(stripped.split()) <= 12
        ):
            # If current_exp has not accumulated description yet, it's part of the header block
            if current_exp and not current_exp["description"]:
                current_exp["role"] += " | " + stripped
            else:
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {"role": stripped, "description": ""}
        elif current_exp:
            current_exp["description"] += (" " + stripped).strip()
        else:
            current_exp = {"role": stripped[:60], "description": stripped}

    if current_exp:
        experiences.append(current_exp)

    return experiences


def parse_education(text):
    """Extract education entries."""
    entries = []
    for line in text.split("\n"):
        stripped = line.strip().lstrip("•-–—*·▪▸►").strip()
        if stripped and len(stripped) > 3:
            entries.append(stripped)
    return entries


def parse_resume(pdf_path):
    """Parse a PDF resume into a structured candidate profile."""
    raw_text, page_count = extract_text_from_pdf(pdf_path)

    if not raw_text.strip():
        return {
            "raw_text": "",
            "page_count": page_count,
            "skills": [],
            "projects": [],
            "experience": [],
            "education": [],
        }

    sections = find_sections(raw_text)

    # Extract structured data from detected sections
    skills_from_sec = parse_skills(sections.get("skills", ""))
    projects = parse_projects(sections.get("projects", ""))
    experience = parse_experience(sections.get("experience", ""))
    education = parse_education(sections.get("education", ""))

    # High-recall: also scan experience, projects, and certifications for explicit technical skills
    other_sections_text = "\n".join([
        sections.get("experience", ""),
        sections.get("projects", ""),
        sections.get("certifications", ""),
        sections.get("summary", ""),
    ])
    skills_from_other = match_skills_in_text(other_sections_text)

    # Combine: dedicated skills section first, followed by additional explicit skills found
    seen: set[str] = set()
    combined_skills: list[str] = []
    for s in skills_from_sec + skills_from_other:
        lk = s.lower()
        if lk not in seen:
            seen.add(lk)
            combined_skills.append(s)

    profile = {
        "raw_text": raw_text,
        "page_count": page_count,
        "skills": combined_skills,
        "projects": projects,
        "experience": experience,
        "education": education,
    }

    return profile


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_resume.py <path_to_resume.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not pdf_path.lower().endswith(".pdf"):
        print(f"ERROR: Expected a PDF file, got: {pdf_path}")
        sys.exit(1)

    try:
        profile = parse_resume(pdf_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to parse resume: {e}")
        sys.exit(1)

    print("=" * 50)
    print("CANDIDATE PROFILE")
    print("=" * 50)
    print(f"Pages: {profile['page_count']}")
    print(f"Text length: {len(profile['raw_text'])} characters")

    print(f"\nSkills ({len(profile['skills'])}):")
    for s in profile["skills"]:
        print(f"  - {s}")

    print(f"\nProjects ({len(profile['projects'])}):")
    for p in profile["projects"]:
        print(f"  - {p['name']}")
        if p["technologies"]:
            print(f"    Tech: {', '.join(p['technologies'])}")
        if p["description"]:
            print(f"    {p['description'][:120]}")

    print(f"\nExperience ({len(profile['experience'])}):")
    for e in profile["experience"]:
        print(f"  - {e['role']}")
        if e["description"]:
            print(f"    {e['description'][:120]}")

    print(f"\nEducation ({len(profile['education'])}):")
    for e in profile["education"]:
        print(f"  - {e}")

    print("=" * 50)


if __name__ == "__main__":
    main()
