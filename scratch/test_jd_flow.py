import io
import fitz  # PyMuPDF
import requests

BASE_URL = "http://localhost:8000"

def create_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=11)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def run_tests():
    print("--- 1. Register / Login test user ---")
    email = "jd_tester_99@example.com"
    password = "Password123!"
    
    # Try login first, or register
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    if res.status_code != 200:
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "confirm_password": password,
            "name": "JD Tester"
        })
        assert res.status_code in (200, 201), f"Register failed: {res.text}"
        res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, f"Login failed: {res.text}"

    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("User authenticated successfully!")

    print("\n--- 2. Upload Sample Resume ---")
    resume_text = """
    Alex Morgan
    Software Engineer

    SKILLS
    Python, Docker, React, Git, SQL, Java

    EXPERIENCE
    Senior Developer at TechCorp (2021 - Present)
    Built backend microservices using Python and Docker containers.
    """
    resume_pdf = create_pdf(resume_text)
    files = {"file": ("Alex_Resume.pdf", resume_pdf, "application/pdf")}
    res = requests.post(f"{BASE_URL}/api/resumes/upload", headers=headers, files=files)
    assert res.status_code in (200, 201), f"Resume upload failed: {res.text}"
    resume_data = res.json()
    print(f"Resume uploaded: id={resume_data['id']}, skills={resume_data.get('skills')}")

    print("\n--- 3. Upload Sample Job Description ---")
    # Notice: JD includes: Python, Docker (in Resume -> Matched, Priority 1)
    # Plus: FastAPI, PostgreSQL, AWS (not in Resume -> Gaps, Priority 2)
    # Resume has: React, Git, Java, SQL (not in JD -> Excluded, Priority 3)
    jd_text = """
    Senior Python Backend Engineer

    ROLE OVERVIEW
    We are seeking a talented Senior Backend Engineer to join our core cloud platform team.

    REQUIREMENTS & TECHNICAL SKILLS:
    • Strong proficiency in Python and FastAPI
    • Hands-on experience with Docker and AWS cloud deployments
    • In-depth knowledge of PostgreSQL database design and query optimization
    """
    jd_pdf = create_pdf(jd_text)
    files = {"file": ("Backend_Engineer_JD.pdf", jd_pdf, "application/pdf")}
    res = requests.post(f"{BASE_URL}/api/job-descriptions/upload", headers=headers, files=files)
    assert res.status_code in (200, 201), f"JD upload failed: {res.text}"
    jd_data = res.json()
    print(f"JD uploaded: id={jd_data['id']}, skills={jd_data.get('skills')}")

    print("\n--- 4. Verify GET /api/job-descriptions/current ---")
    res = requests.get(f"{BASE_URL}/api/job-descriptions/current", headers=headers)
    assert res.status_code == 200, f"GET current JD failed: {res.text}"
    current_jd = res.json()
    assert current_jd["id"] == jd_data["id"]
    print(f"Current JD matches: id={current_jd['id']}, filename={current_jd['filename']}")

    print("\n--- 5. Verify GET /api/job-descriptions/mapping ---")
    res = requests.get(f"{BASE_URL}/api/job-descriptions/mapping", headers=headers)
    assert res.status_code == 200, f"Mapping failed: {res.text}"
    mapping = res.json()
    print("Skill mapping result:")
    print(f"  Matched (Priority 1): {mapping['matched_skills']}")
    print(f"  Gaps (Priority 2):    {mapping['gap_skills']}")
    print(f"  Resume Only (P3 - excluded): {mapping['resume_only']}")
    print(f"  Final Interview Skills:      {mapping['interview_skills']}")

    # Validation:
    # 1. Matched skills must be in both
    for s in mapping["matched_skills"]:
        assert s.lower() in [rs.lower() for rs in resume_data["skills"]]
        assert s.lower() in [js.lower() for js in jd_data["skills"]]

    # 2. Gap skills must be in JD but NOT in resume
    for s in mapping["gap_skills"]:
        assert s.lower() in [js.lower() for js in jd_data["skills"]]
        assert s.lower() not in [rs.lower() for rs in resume_data["skills"]]

    # 3. interview_skills must be matched_skills followed by gap_skills
    assert mapping["interview_skills"] == mapping["matched_skills"] + mapping["gap_skills"]

    # 4. Resume-only skills must NOT be in interview_skills
    for s in mapping["resume_only"]:
        assert s.lower() not in [is_s.lower() for is_s in mapping["interview_skills"]]

    print("ALL MAPPING ASSERTIONS PASSED!")

    print("\n--- 6. Test Starting Adaptive Interview with Mapped Skills ---")
    res = requests.post(f"{BASE_URL}/api/interviews/start", headers=headers, json={
        "resume_id": resume_data["id"],
        "difficulty": "medium",
        "question_type": "technical",
        "question_count": 5,
        "selected_skills": mapping["interview_skills"]
    })
    assert res.status_code in (200, 201), f"Interview start failed: {res.text}"
    session_data = res.json()
    print(f"Interview session created successfully! Session ID: {session_data.get('session_id')}")
    print(f"First question: {session_data.get('current_question', {}).get('question_text')[:100]}...")

    print("\n--- ALL BACKEND E2E TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()
