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


# Common section heading patterns (case-insensitive)
SECTION_PATTERNS = {
    "skills": [
        r"(?:technical\s+)?skills",
        r"technical\s+expertise",
        r"technologies",
        r"tech(?:nical)?\s+stack",
        r"tools?\s*(?:&|and)?\s*technologies",
        r"programming\s+(?:languages|skills)",
        r"core\s+competencies",
    ],
    "projects": [
        r"(?:academic|personal|technical|selected|key)?\s*projects?",
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
}


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file using PyMuPDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    full_text = "\n".join(pages)
    
    if not full_text.strip():
        print("ERROR: This PDF appears to contain no extractable text.")
        print("OCR support is not enabled. Please provide a text-based PDF.")
        sys.exit(1)

    # Normalize whitespace
    full_text = re.sub(r"\r\n", "\n", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = re.sub(r"[ \t]+", " ", full_text)

    return full_text.strip(), len(pages)


def find_sections(text):
    """Identify section boundaries in the resume text."""
    lines = text.split("\n")
    sections = {}  # {section_name: (start_line_idx, end_line_idx)}
    section_order = []  # [(section_name, start_line_idx)]

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
    """Extract skills from a skills section."""
    skills = []
    # Remove common noise
    text = re.sub(r"(?i)(technical\s+skills?|skills?|technologies)\s*:?\s*", "", text)

    # Split by common delimiters
    for line in text.split("\n"):
        line = line.strip().lstrip("•-–—*·▪▸►")
        if not line:
            continue
        # Remove category labels like "Languages:", "Frameworks:", "Tools:", etc.
        line = re.sub(r"^(?:Languages|Frameworks|Databases|Tools|Concepts|Libraries|Platforms|ML|AI|DevOps|Cloud|Other)\s*:?\s*", "", line, flags=re.IGNORECASE)
        if not line.strip():
            continue
        # Try comma/pipe splitting
        parts = re.split(r"[,|/;]", line)
        for part in parts:
            part = part.strip().strip("•-–—*·▪▸►").strip()
            # Remove sub-category labels within parts
            part = re.sub(r"^(?:Languages|Frameworks|Databases|Tools|Concepts|Libraries|Platforms|ML|AI|DevOps|Cloud|Other)\s*:\s*", "", part, flags=re.IGNORECASE).strip()
            # Filter out noise
            if part and 1 < len(part) < 60 and not re.match(r"^[\d\W]+$", part):
                skills.append(part)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in skills:
        key = s.lower().strip()
        if key not in seen and key:
            seen.add(key)
            unique.append(s)

    return unique


def extract_technologies(text):
    """Dynamically extract known technologies from text."""
    tech_keywords = [
        "Java", "Python", "C++", "C#", "JavaScript", "TypeScript",
        "React", "Angular", "Node.js", "Spring Boot", "Django", "Flask",
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQL",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP",
        "Git", "Linux", "REST API", "GraphQL", "Microservices",
        "Kafka", "Rust", "TensorFlow", "PyTorch"
    ]
    found = []
    for kw in tech_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            found.append(kw)
    return found


def parse_projects(text):
    """Extract projects from a projects section."""
    projects = []
    lines = text.split("\n")
    current_project = None

    for line in lines:
        stripped = line.strip().lstrip("•-–—*·▪▸►").strip()
        if not stripped:
            continue

        # Heuristic: short bold-like lines or lines with special markers are project names
        if len(stripped) < 80 and (
            stripped[0].isupper()
            and not stripped.endswith(".")
            and len(stripped.split()) <= 10
        ):
            if current_project:
                projects.append(current_project)
            current_project = {"name": stripped, "description": "", "technologies": []}
        elif current_project:
            current_project["description"] += (" " + stripped).strip()
        else:
            # First line might be a project name
            current_project = {"name": stripped[:60], "description": stripped, "technologies": []}

    if current_project:
        projects.append(current_project)
        
    for p in projects:
        p["technologies"] = extract_technologies(p["description"])

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

        # Heuristic: role-like lines tend to be short and title-cased
        if len(stripped) < 80 and (
            stripped[0].isupper()
            and not stripped.endswith(".")
            and len(stripped.split()) <= 12
        ):
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
    skills = parse_skills(sections.get("skills", ""))
    projects = parse_projects(sections.get("projects", ""))
    experience = parse_experience(sections.get("experience", ""))
    education = parse_education(sections.get("education", ""))

    # If no skills were found via section detection, attempt to find
    # skill-like keywords from the full text as a fallback
    if not skills:
        # Common technical keywords to look for
        tech_keywords = [
            "Java", "Python", "C++", "C#", "JavaScript", "TypeScript",
            "React", "Angular", "Node.js", "Spring Boot", "Django", "Flask",
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQL",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "Git", "Linux", "REST API", "GraphQL", "Microservices",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Data Structures", "Algorithms", "System Design",
            "HTML", "CSS", "Vue.js", "Express.js", "FastAPI",
        ]
        for kw in tech_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", raw_text, re.IGNORECASE):
                skills.append(kw)

    profile = {
        "raw_text": raw_text,
        "page_count": page_count,
        "skills": skills,
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
