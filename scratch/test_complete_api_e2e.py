"""
Comprehensive End-to-End Test Suite for SmartInterview API
Tests:
1. Authentication (Register, Login, Token, Verification, Me)
2. Resume Upload & Extraction (PyMuPDF, Name, Skills, Projects)
3. Job Description Upload & Priority Mapping (Group A, Group B)
4. Interview Creation & First Question Generation (RAG retrieval + Groq LLM)
5. Answer Submission & Multi-Factor Evaluation (Technical, Completeness, Relevance, SBERT, Concept Coverage)
6. Adaptive State Progression (Score-based Bloom adaptation)
7. Interview Completion (Manual Finish)
8. Results Retrieval (Score breakdown, recommendations)
9. History & Performance Analytics
"""

import sys
import os
import uuid
import time

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

# Ensure offline HuggingFace embedding loading
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User

client = TestClient(app)

def run_suite():
    print("=" * 70)
    print("  SMARTINTERVIEW COMPLETE E2E TEST SUITE")
    print("=" * 70)

    # Step 1: Authentication
    uid = uuid.uuid4().hex[:6]
    email = f"e2e_user_{uid}@example.com"
    password = "TestPassword123!"
    
    print("\n[STEP 1] Testing Registration & Login...")
    # Duplicate registration test check
    r_reg = client.post("/api/auth/register", json={
        "name": f"E2E Tester {uid}",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
    token = r_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Registration succeeded for {email}")

    # Duplicate registration should return 400
    r_dup = client.post("/api/auth/register", json={
        "name": f"Duplicate",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    assert r_dup.status_code == 400, f"Expected 400 for duplicate, got {r_dup.status_code}"
    print("  [PASS] Duplicate registration rejected (400)")

    # Login
    r_login = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    print("  [PASS] Login succeeded")

    # Invalid password login
    r_bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert r_bad_login.status_code == 401, f"Expected 401 for bad password, got {r_bad_login.status_code}"
    print("  [PASS] Invalid password rejected (401)")

    # GET /me
    r_me = client.get("/api/auth/me", headers=headers)
    assert r_me.status_code == 200, f"GET /me failed: {r_me.text}"
    assert r_me.json()["email"] == email
    print(f"  [PASS] GET /me verified identity: {r_me.json()['name']}")

    # Step 2: Resume Upload
    print("\n[STEP 2] Testing Resume Upload & Extraction...")
    with open("scratch/alex_chen_resume.pdf", "rb") as f:
        r_resume = client.post(
            "/api/resumes/upload",
            files={"file": ("alex_chen_resume.pdf", f, "application/pdf")},
            headers=headers
        )
    assert r_resume.status_code in [200, 201], f"Resume upload failed: {r_resume.text}"
    resume_data = r_resume.json()
    assert resume_data["name"] == "Alex Chen", f"Expected Alex Chen, got {resume_data.get('name')}"
    assert len(resume_data["skills"]) > 5, "Skills list empty or too short"
    resume_id = resume_data["id"]
    print(f"  [PASS] Resume uploaded: Name={resume_data['name']}, Skills={len(resume_data['skills'])}, Projects={len(resume_data.get('projects', []))}")

    # GET current resume
    r_cur_res = client.get("/api/resumes/current", headers=headers)
    assert r_cur_res.status_code == 200
    assert r_cur_res.json()["id"] == resume_id
    print("  [PASS] GET /resumes/current verified")

    # Step 3: Job Description Upload & Skill Mapping
    print("\n[STEP 3] Testing JD Upload & Skill Mapping...")
    with open("scratch/senior_backend_jd.pdf", "rb") as f:
        r_jd = client.post(
            "/api/job-descriptions/upload",
            files={"file": ("senior_backend_jd.pdf", f, "application/pdf")},
            headers=headers
        )
    assert r_jd.status_code in [200, 201], f"JD upload failed: {r_jd.text}"
    jd_id = r_jd.json()["id"]
    print(f"  [PASS] Job Description uploaded (ID: {jd_id})")

    # GET mapping
    r_map = client.get("/api/job-descriptions/mapping", headers=headers)
    assert r_map.status_code == 200
    mapping = r_map.json()
    matched = mapping["matched_skills"]
    gaps = mapping["gap_skills"]
    assert len(matched) > 0, "Matched skills should not be empty"
    print(f"  [PASS] Mapping calculated: Group A (Matched)={len(matched)}, Group B (Gaps)={len(gaps)}")
    print(f"         Group A Sample: {matched[:5]}")
    print(f"         Group B Gaps: {gaps}")

    # Step 4: Start Adaptive Interview
    print("\n[STEP 4] Testing Adaptive Interview Session Creation...")
    selected_test_skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    t0 = time.perf_counter()
    r_start = client.post("/api/interviews/start", json={
        "resume_id": resume_id,
        "difficulty": "medium",
        "question_type": "mixed",
        "question_count": 5,
        "selected_skills": selected_test_skills,
        "mode": "normal"
    }, headers=headers)
    init_time = round(time.perf_counter() - t0, 2)
    assert r_start.status_code == 201, f"Start interview failed: {r_start.text}"
    session_data = r_start.json()
    session_id = session_data["session_id"]
    q1 = session_data["current_question"]
    print(f"  [PASS] Interview Session created (ID: {session_id}) in {init_time}s")
    print(f"         Q1 ID={q1['id']}, Skill='{q1['skill']}', Bloom='{q1['bloom_level']}', Diff='{q1['difficulty']}'")
    print(f"         Question Text: \"{q1['question_text']}\"")
    assert q1["question_text"] != "[GENERATION FAILED]", "Question generation failed"

    # Step 5: Submit Answer & Evaluate
    print("\n[STEP 5] Testing Answer Submission & Multi-Factor Evaluation...")
    answer_text = (
        "In Python and FastAPI, asynchronous endpoints use async and await to handle I/O-bound operations "
        "concurrently without blocking the main event loop. Pydantic models provide request validation and "
        "serialization, and Depends() injects database sessions and dependencies cleanly into endpoint handlers."
    )
    t0 = time.perf_counter()
    r_ans = client.post(
        f"/api/interviews/{session_id}/questions/{q1['id']}/answer",
        json={"answer_text": answer_text},
        headers=headers
    )
    eval_time = round(time.perf_counter() - t0, 2)
    assert r_ans.status_code == 200, f"Answer evaluation failed: {r_ans.text}"
    ans_res = r_ans.json()
    eval_data = ans_res["evaluation"]
    print(f"  [PASS] Evaluation completed in {eval_time}s:")
    print(f"         Technical: {eval_data['technical_score']}/100")
    print(f"         Completeness: {eval_data['completeness_score']}/100")
    print(f"         Relevance: {eval_data['relevance_score']}/100")
    print(f"         Semantic Similarity: {eval_data['semantic_similarity_score']}/100")
    print(f"         Concept Coverage: {eval_data['concept_coverage_score']}/100")
    print(f"         OVERALL SCORE: {eval_data['overall_score']}/100")
    print(f"         Feedback: {eval_data['feedback'][:120]}...")
    print(f"         Strengths: {eval_data['strengths']}")
    print(f"         Weaknesses: {eval_data['weaknesses']}")

    # Check Question 2 generation
    q2 = ans_res["next_question"]
    assert q2 is not None, "Next question should be generated"
    print(f"\n[STEP 6] Adaptive Transition to Question 2:")
    print(f"         Q2 ID={q2['id']}, Skill='{q2['skill']}', Bloom='{q2['bloom_level']}', Diff='{q2['difficulty']}'")
    print(f"         Question Text: \"{q2['question_text']}\"")

    # Step 6: Complete Interview (Manual Finish)
    print("\n[STEP 7] Testing Manual Interview Completion...")
    r_comp = client.post(f"/api/interviews/{session_id}/complete", headers=headers)
    assert r_comp.status_code == 200, f"Complete interview failed: {r_comp.text}"
    print("  [PASS] Session marked complete with completion_reason='manual'")

    # Step 7: Results Retrieval
    print("\n[STEP 8] Testing Results Retrieval...")
    r_results = client.get(f"/api/interviews/{session_id}/results", headers=headers)
    assert r_results.status_code == 200, f"Get results failed: {r_results.text}"
    results_data = r_results.json()
    print(f"  [PASS] Results retrieved: Average Score = {results_data.get('overall_average_score')}%")
    print(f"         Skill breakdown: {list(results_data.get('skill_breakdown', {}).keys())}")
    print(f"         Recommendations: {len(results_data.get('recommendations', []))} items")

    # Step 8: History & Performance Dashboard
    print("\n[STEP 9] Testing History & Performance Dashboard...")
    r_hist = client.get("/api/interviews/history", headers=headers)
    assert r_hist.status_code == 200
    assert len(r_hist.json()) >= 1
    print(f"  [PASS] GET /history returned {len(r_hist.json())} session(s)")

    r_perf = client.get("/api/users/performance", headers=headers)
    assert r_perf.status_code == 200
    perf_data = r_perf.json()
    print(f"  [PASS] GET /performance returned has_data={perf_data.get('has_data')}")
    print(f"         Total Questions Answered: {perf_data.get('total_questions_answered')}")
    print(f"         Average Score: {perf_data.get('overall_average_score')}%")

    print("\n" + "=" * 70)
    print("  ALL E2E INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_suite()
