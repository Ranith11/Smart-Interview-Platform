"""
SmartInterview — Resume Service
Uses the EXISTING Week 6 parse_resume.py without modification.
"""

import sys
import importlib.util
from pathlib import Path

from app.config import SCRIPTS_DIR

# ── Import the existing Week 6 resume parser ──────────────
_parser_path = str(Path(SCRIPTS_DIR) / "parse_resume.py")
_spec = importlib.util.spec_from_file_location("parse_resume_mod", _parser_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_resume = _mod.parse_resume  # The exact function from Week 6


def parse_resume_file(file_path: str) -> dict:
    """
    Parse a PDF resume using the existing Week 6 parser.
    Returns the structured profile dict:
      {raw_text, page_count, skills, projects, experience, education}
    """
    profile = parse_resume(file_path)
    return profile
