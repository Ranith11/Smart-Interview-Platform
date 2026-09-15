import os
import io
import re
import pymupdf
import requests

BASE_URL = "http://localhost:8000"

def text_to_pdf_pages(file_path: str) -> bytes:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The transcript output had "=== RESUME ===" or "=== JD ===" and "\n--- PAGE ---\n"
    content = re.sub(r"^.*?===\s*(?:RESUME|JD)\s*===\s*", "", content, flags=re.DOTALL)
    pages_text = content.split("--- PAGE ---")

    doc = pymupdf.open()
    for page_str in pages_text:
        page_str = page_str.strip()
        if not page_str:
            continue
        page = doc.new_page()
        # insert text
        page.insert_text((40, 50), page_str, fontsize=9)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def test_real_files():
    print("=== Testing Real Documents E2E (Marcus Chen & StrataFlow JD) ===")
    
    # 1. Login
    email = "jd_tester_99@example.com"
    password = "Password123!"
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("User authenticated successfully.")

    # 2. Upload Marcus Chen Resume
    resume_bytes = text_to_pdf_pages("data/resumes/marcus_chen_resume.txt")
    files = {"file": ("marcus_chen_resume.pdf", resume_bytes, "application/pdf")}
    res = requests.post(f"{BASE_URL}/api/resumes/upload", headers=headers, files=files)
    assert res.status_code in (200, 201), f"Resume upload failed: {res.text}"
    resume_data = res.json()
    print(f"\n[Marcus Chen Resume Extracted Skills] ({len(resume_data['skills'])} skills):")
    print(resume_data["skills"])
    print(f"Projects detected: {len(resume_data.get('projects', []))}")
    print(f"Experience detected: {len(resume_data.get('experience', []))}")

    # 3. Upload StrataFlow JD
    jd_bytes = text_to_pdf_pages("data/resumes/strataflow_jd.txt")
    files = {"file": ("strataflow_lead_backend_jd.pdf", jd_bytes, "application/pdf")}
    res = requests.post(f"{BASE_URL}/api/job-descriptions/upload", headers=headers, files=files)
    assert res.status_code in (200, 201), f"JD upload failed: {res.text}"
    jd_data = res.json()
    print(f"\n[StrataFlow JD Extracted Skills] ({len(jd_data['skills'])} skills):")
    print(jd_data["skills"])

    # 4. Get Mapping
    res = requests.get(f"{BASE_URL}/api/job-descriptions/mapping", headers=headers)
    assert res.status_code == 200, f"Mapping failed: {res.text}"
    mapping = res.json()
    print(f"\n[Skill Mapping Result]")
    print(f"  Matched (Priority 1) ({len(mapping['matched_skills'])}): {mapping['matched_skills']}")
    print(f"  Gaps (Priority 2)    ({len(mapping['gap_skills'])}):    {mapping['gap_skills']}")
    print(f"  Resume Only (P3)     ({len(mapping['resume_only'])}):     {mapping['resume_only']}")
    print(f"  Final Interview Plan ({len(mapping['interview_skills'])}): {mapping['interview_skills']}")

    # Check for unwanted artifacts in skills
    unwanted = ["compensation", "$185,000", "401k", "equity", "page 1", "page 2", "strataflow", "candidate", "san francisco", "hybrid", "pto"]
    for s in jd_data["skills"] + resume_data["skills"]:
        for bad in unwanted:
            assert bad not in s.lower(), f"Unwanted artifact found in skills: {s}"
    print("\nVerified: ZERO metadata, compensation, pagination, or noise tokens found in extracted skills!")

    # 5. Start Interview
    res = requests.post(f"{BASE_URL}/api/interviews/start", headers=headers, json={
        "resume_id": resume_data["id"],
        "difficulty": "hard",
        "question_type": "technical",
        "question_count": 5,
        "selected_skills": mapping["interview_skills"]
    })
    assert res.status_code in (200, 201), f"Start interview failed: {res.text}"
    session = res.json()
    print(f"\nAdaptive Interview Started! Session ID: {session['session_id']}")
    print(f"First question skill: {session['current_question']['skill']}")
    print(f"First question Bloom level: {session['current_question']['bloom_level']}")
    print(f"First question text:\n{session['current_question']['question_text']}")
    print("\n=== ALL REAL-DOCUMENT TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    test_real_files()
