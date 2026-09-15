"""
SmartInterview — Job Description Service

Deterministic JD parsing (no LLM) that reuses PyMuPDF text extraction,
generic document cleanup, and the central skill taxonomy matching from
scripts/generate_question.py.

Skill mapping priority:
    Priority 1 (Group A): JD skills that ARE in Resume  → verify claimed experience
    Priority 2 (Group B): JD skills NOT in Resume       → test role requirement/gap
    Resume-only skills   → NOT included in default interview plan
"""

import os
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    pymupdf = None

from app.config import SCRIPTS_DIR

# ── Import central taxonomy and matching engine from generate_question.py ──────
import importlib.util

_gen_path = str(Path(SCRIPTS_DIR) / "generate_question.py")
_spec = importlib.util.spec_from_file_location("_gen_mod", _gen_path)
_gen_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen_mod)

SKILL_DOMAIN_MAP: dict = _gen_mod.SKILL_DOMAIN_MAP
match_skills_in_text = _gen_mod.match_skills_in_text
CANONICAL_SKILL_NAMES = _gen_mod.CANONICAL_SKILL_NAMES

# ── Import generic document cleanup from parse_resume.py ───────────────────────
_parser_path = str(Path(SCRIPTS_DIR) / "parse_resume.py")
_p_spec = importlib.util.spec_from_file_location("_p_mod", _parser_path)
_p_mod = importlib.util.module_from_spec(_p_spec)
_p_spec.loader.exec_module(_p_mod)

clean_document_pages = _p_mod.clean_document_pages


# ── Section filtering patterns ────────────────────────────────────────────────

# Non-technical sections to exclude completely
_EXCLUDE_HEADING_PATTERNS = [
    r"compensation|salary|benefits|pay|equity",
    r"employment(?:\s+type)?|work\s+model|location|seniority(?:\s+level)?",
    r"requisition(?:\s+file)?|effective|status",
    r"candidate\s+evaluation(?:\s+rubric)?|evaluation\s+dimension|scoring|weight",
    r"hiring\s+process(?:\s+note)?|application\s+instructions|interview\s+process",
    r"about\s+(?:us|the\s+company)|company\s+overview|equal\s+opportunity|eeo|disclaimer",
]

# Technically relevant sections to prioritize
_TECH_HEADING_PATTERNS = [
    r"(?:key\s+)?(?:technical\s+)?(?:skills?|competencies?|requirements?|qualifications?)",
    r"(?:required|preferred|desired|minimum|must(?:\s+have)?)\s+(?:skills?|qualifications?|experience)",
    r"technologies",
    r"tech(?:nical)?\s+stack",
    r"tools?\s*(?:&|and)?\s*technologies",
    r"programming\s+(?:languages?|skills?)",
    r"(?:key\s+)?responsibilities|duties",
    r"what\s+(?:we|you)\s+(?:need|require|will\s+do)",
    r"job\s+requirements?",
    r"role\s+overview",
]


# ── Text Extraction with Generic Cleanup ──────────────────────────────────────

def _extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    """Extract all text from a PDF using PyMuPDF and apply generic cleanup."""
    if pymupdf is None:
        raise RuntimeError("pymupdf is required: pip install pymupdf")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    doc = pymupdf.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()

    cleaned_text, _ = clean_document_pages(pages)
    return cleaned_text, len(pages)


# ── Section Filtering ─────────────────────────────────────────────────────────

def _find_technical_sections(text: str) -> str:
    """
    Split the JD text into sections and extract content from technically relevant
    sections (Requirements, Qualifications, Skills, Responsibilities, Role Overview)
    while explicitly excluding non-technical sections (Salary, Benefits, Requisition
    metadata, Evaluation Rubrics, Hiring Process Notes).
    """
    sections: list[tuple[str, str]] = []
    current_heading = "HEADER"
    current_lines: list[str] = []

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            current_lines.append("")
            continue

        # Detect heading-like line: numbered (e.g. "1. ROLE OVERVIEW") or short uppercase
        is_heading = False
        if len(s) < 80 and (
            re.match(r"^\s*\d+[\.\)]\s+[A-Z]", s)
            or (s == s.upper() and len(s.split()) <= 6 and not s.endswith("."))
        ):
            is_heading = True

        if is_heading:
            sections.append((current_heading, "\n".join(current_lines)))
            current_heading = s
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_heading, "\n".join(current_lines)))

    tech_text_parts: list[str] = []
    for heading, content in sections:
        is_excluded = any(re.search(p, heading, re.IGNORECASE) for p in _EXCLUDE_HEADING_PATTERNS)
        if is_excluded:
            continue

        is_tech = any(re.search(p, heading, re.IGNORECASE) for p in _TECH_HEADING_PATTERNS)
        if is_tech:
            tech_text_parts.append(content)

    if tech_text_parts:
        return "\n".join(tech_text_parts)

    # Fallback: if no specific technical sections matched, filter out excluded sections and return rest
    fallback_parts: list[str] = []
    for heading, content in sections:
        if not any(re.search(p, heading, re.IGNORECASE) for p in _EXCLUDE_HEADING_PATTERNS):
            fallback_parts.append(content)
    return "\n".join(fallback_parts) if fallback_parts else text


# ── Public API ────────────────────────────────────────────────────────────────

def parse_jd_file(file_path: str) -> dict:
    """
    Parse a JD PDF and return structured data with validated canonical skills.
    Returns: { raw_text, page_count, skills }
    """
    raw_text, page_count = _extract_text_from_pdf(file_path)
    if not raw_text.strip():
        return {"raw_text": "", "page_count": page_count, "skills": []}

    tech_text = _find_technical_sections(raw_text)
    skills = match_skills_in_text(tech_text)

    # If section filtering yielded nothing, fall back to full-text scan
    if not skills:
        skills = match_skills_in_text(raw_text)

    return {
        "raw_text": raw_text,
        "page_count": page_count,
        "skills": skills,
    }


def map_skills(resume_skills: list[str], jd_skills: list[str]) -> dict:
    """
    Map Resume skills against JD skills using the approved priority order.

    Priority 1 — Group A: JD skills present in Resume (verify claimed experience).
    Priority 2 — Group B: JD skills NOT in Resume (test role requirement/gap).
    Resume-only skills: NOT included in interview_skills.

    Returns:
        matched_skills   — Group A (in JD and Resume)
        gap_skills       — Group B (in JD but not in Resume)
        resume_only      — Resume skills not required by JD (excluded from plan)
        interview_skills — ordered list: Group A first, then Group B
    """
    # Normalize for comparison (lowercase, stripped)
    resume_lower = {s.lower().strip(): s for s in resume_skills}
    jd_lower = {s.lower().strip(): s for s in jd_skills}

    matched_keys = [k for k in jd_lower if k in resume_lower]
    gap_keys = [k for k in jd_lower if k not in resume_lower]
    resume_only_keys = [k for k in resume_lower if k not in jd_lower]

    # Preserve display name from JD (authoritative source for role requirements)
    matched_skills = [jd_lower[k] for k in matched_keys]
    gap_skills = [jd_lower[k] for k in gap_keys]
    resume_only = [resume_lower[k] for k in resume_only_keys]

    # Ordered priority list: Group A then Group B
    interview_skills = matched_skills + gap_skills

    return {
        "matched_skills": matched_skills,
        "gap_skills": gap_skills,
        "resume_only": resume_only,
        "interview_skills": interview_skills,
    }
