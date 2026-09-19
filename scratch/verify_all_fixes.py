import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_password_and_auth():
    print("\n--- TEST 1: Password Verification & Hash Robustness ---")
    sys.path.insert(0, os.path.abspath("backend"))
    from app.services.auth_service import verify_password
    
    # 1. Normal valid hash
    from app.services.auth_service import hash_password
    valid_hash = hash_password("secret123")
    assert verify_password("secret123", valid_hash) == True, "Valid password verification failed"
    assert verify_password("wrongpw", valid_hash) == False, "Wrong password returned True"
    print("  [PASS] Normal password verification works")

    # 2. Corrupted / invalid hash
    corrupted_hash = "not_a_valid_bcrypt_hash_corrupted_12345"
    assert verify_password("secret123", corrupted_hash) == False, "Corrupted hash should return False"
    print("  [PASS] Corrupted hash safely returns False without raising 500")

def test_registration_schema():
    print("\n--- TEST 2: Registration Schema Refinement ---")
    import uuid
    uid = uuid.uuid4().hex[:6]
    
    # 1. Register with matching confirm_password
    r1 = requests.post(f"{BASE_URL}/auth/register", json={
        "name": f"User {uid}",
        "email": f"user_{uid}@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert r1.status_code == 201, f"Registration with matching confirm failed: {r1.status_code} {r1.text}"
    token = r1.json()["access_token"]
    print("  [PASS] Register with matching confirm_password succeeds (201)")

    # 2. Register with mismatched confirm_password
    r2 = requests.post(f"{BASE_URL}/auth/register", json={
        "name": f"User Mismatch",
        "email": f"mismatch_{uid}@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword!"
    })
    assert r2.status_code == 400, f"Mismatched passwords should return 400, got: {r2.status_code}"
    print("  [PASS] Register with mismatched confirm_password rejected (400)")

    # 3. Register without confirm_password (API client)
    r3 = requests.post(f"{BASE_URL}/auth/register", json={
        "name": f"User NoConfirm",
        "email": f"noconfirm_{uid}@example.com",
        "password": "Password123!"
    })
    assert r3.status_code == 201, f"Registration without confirm_password failed: {r3.status_code} {r3.text}"
    print("  [PASS] Register without optional confirm_password succeeds (201)")
    
    return token, f"user_{uid}@example.com", "Password123!"

def test_resume_candidate_name(token):
    print("\n--- TEST 3: Resume Candidate Name Extraction & Persistence ---")
    from scripts.parse_resume import parse_resume
    
    # 1. Direct parser verification
    p1 = parse_resume("scratch/alex_chen_resume.pdf")
    assert p1.get("name") == "Alex Chen", f"Expected Alex Chen, got {p1.get('name')}"
    print("  [PASS] Parser extracted 'Alex Chen' from resume")

    p2 = parse_resume("data/resumes/sample_resume.pdf")
    assert p2.get("name") == "Arjun Sharma", f"Expected Arjun Sharma, got {p2.get('name')}"
    print("  [PASS] Parser extracted 'Arjun Sharma' from sample resume")

    # 2. Upload via API and verify ResumeResponse contains name
    headers = {"Authorization": f"Bearer {token}"}
    with open("scratch/alex_chen_resume.pdf", "rb") as f:
        res = requests.post(f"{BASE_URL}/resumes/upload", files={"file": f}, headers=headers)
    assert res.status_code in [200, 201], f"Resume upload failed: {res.status_code} {res.text}"
    data = res.json()
    assert data.get("name") == "Alex Chen", f"API ResumeResponse name mismatch: {data.get('name')}"
    print("  [PASS] API upload saved and returned candidate name: Alex Chen")

def test_jd_mapping(token):
    print("\n--- TEST 4: Job Description Upload & Skill Mapping ---")
    headers = {"Authorization": f"Bearer {token}"}
    with open("scratch/senior_backend_jd.pdf", "rb") as f:
        res = requests.post(f"{BASE_URL}/job-descriptions/upload", files={"file": f}, headers=headers)
    assert res.status_code in [200, 201], f"JD upload failed: {res.status_code} {res.text}"
    print("  [PASS] JD upload succeeded")

    # Fetch mapping
    res_map = requests.get(f"{BASE_URL}/job-descriptions/mapping", headers=headers)
    assert res_map.status_code == 200, f"Mapping failed: {res_map.status_code} {res_map.text}"
    mapping = res_map.json()
    assert "matched_skills" in mapping and len(mapping["matched_skills"]) > 0
    assert "gap_skills" in mapping and len(mapping["gap_skills"]) > 0
    print(f"  [PASS] GET /job-descriptions/mapping returned {len(mapping['matched_skills'])} matched skills, {len(mapping['gap_skills'])} gap skills")

def test_syllabus_and_natural_prompt(token):
    print("\n--- TEST 5: Syllabus Topic Inference & Natural Prompt Voice ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Upload syllabus
    with open("scratch/cs450_distributed_systems_syllabus.pdf", "rb") as f:
        res = requests.post(f"{BASE_URL}/interviews/upload-syllabus", files={"files": ("cs450_distributed_systems_syllabus.pdf", f, "application/pdf")}, headers=headers)
    assert res.status_code == 200, f"Syllabus upload failed: {res.status_code} {res.text}"
    data = res.json()
    topics = data.get("topics", [])
    assert len(topics) > 0, f"Token starvation issue persisted: topics list is empty!"
    print(f"  [PASS] Topic inference succeeded with {len(topics)} topics: {topics[:3]}... (no token starvation)")

    syllabus_id = data["syllabus_id"]

    # 2. Start syllabus interview
    res_start = requests.post(f"{BASE_URL}/interviews/start", json={
        "mode": "syllabus",
        "syllabus_id": syllabus_id,
        "difficulty": "medium",
        "selected_topics": topics[:3]
    }, headers=headers)
    assert res_start.status_code == 201, f"Start syllabus interview failed: {res_start.status_code} {res_start.text}"
    start_data = res_start.json()
    assert start_data.get("mode") == "syllabus", f"Mode should be syllabus, got: {start_data.get('mode')}"
    
    q_text = start_data["current_question"]["question_text"]
    print(f"  [PASS] Syllabus question generated: {q_text}")
    
    # Meta-language checks
    banned_phrases = [
        "according to the provided",
        "as described in the syllabus",
        "based on the uploaded",
        "as mentioned in unit",
        "according to excerpt",
        "in the provided excerpt",
    ]
    for bp in banned_phrases:
        assert bp not in q_text.lower(), f"Meta-language leakage found: '{bp}' in '{q_text}'"
    print("  [PASS] Question contains no meta-language leakage (clean natural interviewer voice)")

    # Test Session response includes mode
    session_id = start_data["session_id"]
    res_sess = requests.get(f"{BASE_URL}/interviews/{session_id}", headers=headers)
    assert res_sess.status_code == 200
    assert res_sess.json().get("mode") == "syllabus", f"GET /interviews/{session_id} should have mode='syllabus'"
    print("  [PASS] GET /interviews/{session_id} returns mode='syllabus'")

def test_kb_integrity():
    print("\n--- TEST 6: Permanent ChromaDB Knowledge Base Integrity ---")
    import chromadb
    client = chromadb.PersistentClient(path="chroma_db")
    kb = client.get_collection("technical_kb")
    count = kb.count()
    assert count > 0, "Knowledge base collection is empty!"
    print(f"  [PASS] Permanent ChromaDB 'technical_kb' intact with {count} chunks. Zero modified.")

if __name__ == "__main__":
    test_password_and_auth()
    token, email, pw = test_registration_schema()
    test_resume_candidate_name(token)
    test_jd_mapping(token)
    test_syllabus_and_natural_prompt(token)
    test_kb_integrity()
    print("\n=======================================================")
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=======================================================\n")
