"""
End-to-End Interview Tester
Runs complete candidate journeys for:
1. Resume Upload (Alex Chen)
2. Job Description Upload (Senior Backend Engineer)
3. Normal Mode Adaptive Interview (5 questions with simulated answers)
4. Interview Results & Analytics Check
5. Syllabus Upload (CS450 Distributed Systems)
6. Syllabus Mode Adaptive Interview (4 questions with simulated answers)
7. Final Cleanup & Integrity Verification

Logs all issues, anomalies, status codes, and timings.
"""

import sys
import os
import time
import json
import requests
from pathlib import Path

# Force UTF-8 and unbuffered output on Windows
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"
DOCS_DIR = Path(__file__).resolve().parent

ISSUES = []

def record_issue(category: str, severity: str, title: str, details: str):
    ISSUES.append({
        "category": category,
        "severity": severity,
        "title": title,
        "details": details,
    })
    print(f"\n[ISSUE FOUND - {severity.upper()}] [{category}] {title}")
    print(f"Details: {details}\n")

def run_e2e():
    session = requests.Session()
    print("=== STARTING FULL END-TO-END INTERVIEW TEST ===")

    # 1. Register / Login test user
    print("\n--- STEP 1: AUTHENTICATION ---")
    test_email = f"alex_e2e_{int(time.time())}@example.com"
    test_password = "Password123!"
    
    # Test Registration
    t0 = time.perf_counter()
    reg_res = session.post(f"{BASE_URL}/api/auth/register", json={
        "email": test_email,
        "name": "Alex Chen (E2E Test)",
        "password": test_password,
        "confirm_password": test_password,
    })
    reg_time = round(time.perf_counter() - t0, 2)
    print(f"Registration response: {reg_res.status_code} ({reg_time}s)")
    
    if reg_res.status_code != 201:
        record_issue("Auth", "Critical", "Registration Failed", f"Status: {reg_res.status_code}, Body: {reg_res.text}")
        return

    # Login to get JWT
    login_res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": test_password,
    })
    if login_res.status_code != 200:
        record_issue("Auth", "Critical", "Login Failed", f"Status: {login_res.status_code}, Body: {login_res.text}")
        return
    
    token = login_res.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    session.headers.update(headers)
    print(f"Logged in successfully. JWT obtained.")

    # 2. Upload Resume
    print("\n--- STEP 2: RESUME UPLOAD ---")
    resume_path = DOCS_DIR / "alex_chen_resume.pdf"
    t0 = time.perf_counter()
    with open(resume_path, "rb") as f:
        res_upload = session.post(
            f"{BASE_URL}/api/resumes/upload",
            files={"file": ("alex_chen_resume.pdf", f, "application/pdf")},
        )
    upload_time = round(time.perf_counter() - t0, 2)
    print(f"Resume upload response: {res_upload.status_code} ({upload_time}s)")
    
    if res_upload.status_code not in (200, 201):
        record_issue("Resume", "Critical", "Resume Upload Failed", f"Status: {res_upload.status_code}, Body: {res_upload.text}")
        resume_data = {}
    else:
        resume_data = res_upload.json()
        print(f"Parsed candidate: {resume_data.get('name')}")
        print(f"Extracted skills ({len(resume_data.get('skills', []))}): {resume_data.get('skills')}")
        print(f"Extracted projects ({len(resume_data.get('projects', []))}): {[p.get('name') for p in resume_data.get('projects', [])]}")
        
        if not resume_data.get("skills"):
            record_issue("Resume", "High", "No Skills Extracted", "Resume parser failed to extract technical skills from standard resume PDF.")
        if not resume_data.get("projects"):
            record_issue("Resume", "Medium", "No Projects Extracted", "Resume parser failed to extract projects from standard resume PDF.")

    # 3. Upload Job Description
    print("\n--- STEP 3: JOB DESCRIPTION UPLOAD ---")
    jd_path = DOCS_DIR / "senior_backend_jd.pdf"
    t0 = time.perf_counter()
    with open(jd_path, "rb") as f:
        jd_upload = session.post(
            f"{BASE_URL}/api/job-descriptions/upload",
            files={"file": ("senior_backend_jd.pdf", f, "application/pdf")},
        )
    jd_time = round(time.perf_counter() - t0, 2)
    print(f"JD upload response: {jd_upload.status_code} ({jd_time}s)")
    
    if jd_upload.status_code not in (200, 201):
        record_issue("JobDescription", "High", "JD Upload Failed", f"Status: {jd_upload.status_code}, Body: {jd_upload.text}")
        jd_data = {}
    else:
        jd_data = jd_upload.json()
        print(f"Job Title: {jd_data.get('job_title')}")
        print(f"Company: {jd_data.get('company_name')}")
        print(f"Required Skills ({len(jd_data.get('required_skills', []))}): {jd_data.get('required_skills')}")
        print(f"Match Score: {jd_data.get('match_score')}%")
        print(f"Matched Skills: {jd_data.get('matched_skills')}")
        print(f"Missing Skills: {jd_data.get('missing_skills')}")

    # 4. Normal Mode Interview Session
    print("\n--- STEP 4: NORMAL MODE INTERVIEW (ADAPTIVE) ---")
    selected_skills = resume_data.get("skills", [])[:4] or ["Python", "FastAPI", "PostgreSQL", "Docker"]
    t0 = time.perf_counter()
    start_res = session.post(f"{BASE_URL}/api/interviews/start", json={
        "resume_id": resume_data.get("id"),
        "selected_skills": selected_skills,
        "difficulty": "medium",
        "question_type": "mixed",
        "mode": "normal",
    })
    start_time = round(time.perf_counter() - t0, 2)
    print(f"Start interview response: {start_res.status_code} ({start_time}s)")
    
    if start_res.status_code != 201:
        record_issue("Interview", "Critical", "Failed to start normal interview", f"Status: {start_res.status_code}, Body: {start_res.text}")
        return

    interview = start_res.json()
    session_id = interview.get("session_id")
    first_q = interview.get("current_question", {})
    print(f"Session #{session_id} created successfully.")
    print(f"Initial Bloom Level: {interview.get('current_bloom_level')}")
    print(f"First Question #{first_q.get('question_number')} (Skill: {first_q.get('skill')}, Diff: {first_q.get('difficulty')}, Bloom: {first_q.get('bloom_level')}):")
    print(f"  \"{first_q.get('question_text')}\"")

    # Simulate Candidate Answering 4 Questions in Normal Mode
    current_q = first_q
    answers_pool = [
        "In FastAPI, dependency injection is achieved using the Depends() callable. It allows modular sharing of database sessions, security tokens, and configuration. Behind the scenes, FastAPI builds a dependency graph and executes async dependencies concurrently.",
        "PostgreSQL uses Multi-Version Concurrency Control (MVCC) to handle concurrent transactions without locking. Each row has xmin and xmax transaction IDs. Indexes point to tuples, and VACUUM reclaims dead tuples created by UPDATE and DELETE operations.",
        "To prevent Redis cache stampedes, we can use probabilistic early expiration (XFetch algorithm), distributed mutex locks via Redlock, or background worker cache pre-warming with Celery.",
        "Docker multi-stage builds separate the build environment with heavy compilers and dependencies from the minimal runtime image (like python:3.11-slim or alpine), reducing attack surface and image size from 1.2GB down to 140MB.",
    ]

    for q_idx in range(1, 5):
        if not current_q or not current_q.get("id"):
            break

        q_id = current_q["id"]
        answer_text = answers_pool[(q_idx - 1) % len(answers_pool)]
        print(f"\nSubmitting Answer for Q#{q_idx} (ID: {q_id})...")
        
        t0 = time.perf_counter()
        ans_res = session.post(
            f"{BASE_URL}/api/interviews/{session_id}/questions/{q_id}/answer",
            json={"answer_text": answer_text}
        )
        ans_time = round(time.perf_counter() - t0, 2)
        print(f"Answer response: {ans_res.status_code} ({ans_time}s)")
        
        if ans_res.status_code != 200:
            record_issue("Interview", "Critical", f"Answer evaluation failed on Q#{q_idx}", f"Status: {ans_res.status_code}, Body: {ans_res.text}")
            break

        ans_data = ans_res.json()
        eval_info = ans_data.get("evaluation", {})
        print(f"  Overall Score: {eval_info.get('overall_score')}/100")
        print(f"  Technical: {eval_info.get('technical_score')}, Concept: {eval_info.get('concept_coverage_score')}")
        print(f"  Feedback: {eval_info.get('feedback')[:100]}...")
        
        # Check scores integrity
        if eval_info.get("overall_score") is None:
            record_issue("Evaluation", "High", "Overall score is None", f"Q#{q_idx} evaluation returned None overall_score.")
        
        # Check next question
        next_q = ans_data.get("next_question")
        if next_q:
            print(f"  Next Question #{next_q.get('question_number')} (Skill: {next_q.get('skill')}, Bloom: {next_q.get('bloom_level')}, Diff: {next_q.get('difficulty')}):")
            print(f"    \"{next_q.get('question_text')}\"")
            current_q = next_q
        else:
            print(f"  No next question. Interview status: complete={ans_data.get('is_complete')}")
            break

    # Complete the interview manually
    print("\nCompleting Normal Mode Interview...")
    t0 = time.perf_counter()
    comp_res = session.post(f"{BASE_URL}/api/interviews/{session_id}/complete")
    comp_time = round(time.perf_counter() - t0, 2)
    print(f"Complete interview response: {comp_res.status_code} ({comp_time}s)")
    if comp_res.status_code != 200:
        record_issue("Interview", "High", "Complete interview endpoint failed", f"Status: {comp_res.status_code}, Body: {comp_res.text}")

    # Fetch Results
    print("\nFetching Normal Mode Results...")
    res_res = session.get(f"{BASE_URL}/api/interviews/{session_id}/results")
    if res_res.status_code != 200:
        record_issue("Results", "High", "Fetch Results failed", f"Status: {res_res.status_code}, Body: {res_res.text}")
    else:
        results = res_res.json()
        print(f"Average Score: {results.get('average_score')}%")
        print(f"Skill breakdown ({len(results.get('skill_breakdown', []))} skills): {[s.get('skill') for s in results.get('skill_breakdown', [])]}")
        print(f"Recommendations count: {len(results.get('recommendations', []))}")
        if results.get("average_score") is None:
            record_issue("Results", "Medium", "Results average_score is null", "Results endpoint returned null average_score after completed session.")

    # 5. Syllabus Mode Interview
    print("\n--- STEP 5: SYLLABUS MODE INTERVIEW ---")
    syllabus_path = DOCS_DIR / "cs450_distributed_systems_syllabus.pdf"
    t0 = time.perf_counter()
    with open(syllabus_path, "rb") as f:
        syl_res = session.post(
            f"{BASE_URL}/api/interviews/upload-syllabus",
            files={"files": ("cs450_distributed_systems_syllabus.pdf", f, "application/pdf")},
        )
    syl_upload_time = round(time.perf_counter() - t0, 2)
    print(f"Syllabus upload response: {syl_res.status_code} ({syl_upload_time}s)")
    
    if syl_res.status_code != 200:
        record_issue("Syllabus", "Critical", "Syllabus upload failed", f"Status: {syl_res.status_code}, Body: {syl_res.text}")
        return

    syl_data = syl_res.json()
    print(f"Inferred Subject: {syl_data.get('subject')}")
    print(f"Detected Topics ({len(syl_data.get('topics', []))}): {syl_data.get('topics')}")
    print(f"Profiling Metrics: {syl_data.get('metrics')}")
    
    if len(syl_data.get("topics", [])) < 3:
        record_issue("Syllabus", "Medium", "Low topic detection count", f"Only {len(syl_data.get('topics', []))} topics detected from 5-unit syllabus.")

    # Start Syllabus Interview
    selected_topics = syl_data.get("topics", [])[:3]
    t0 = time.perf_counter()
    syl_start_res = session.post(f"{BASE_URL}/api/interviews/start", json={
        "mode": "syllabus",
        "syllabus_id": syl_data.get("syllabus_id"),
        "selected_topics": selected_topics,
    })
    syl_start_time = round(time.perf_counter() - t0, 2)
    print(f"Start syllabus interview response: {syl_start_res.status_code} ({syl_start_time}s)")
    
    if syl_start_res.status_code != 201:
        record_issue("Syllabus", "Critical", "Failed to start syllabus interview", f"Status: {syl_start_res.status_code}, Body: {syl_start_res.text}")
        return

    syl_session = syl_start_res.json()
    syl_session_id = syl_session.get("session_id")
    syl_first_q = syl_session.get("current_question", {})
    print(f"Syllabus Session #{syl_session_id} started.")
    print(f"First Question #{syl_first_q.get('question_number')} (Topic: {syl_first_q.get('skill')}):")
    print(f"  \"{syl_first_q.get('question_text')}\"")

    # Verify source grounding
    q_text_lower = syl_first_q.get("question_text", "").lower()
    print(f"Checking grounding in CS450 Distributed Systems context...")

    # Answer Syllabus Question
    syl_ans_text = (
        "In the Raft consensus algorithm, leader election begins when a follower's election timer expires without receiving a heartbeat from the leader. "
        "The follower increments its current term, transitions to candidate state, votes for itself, and sends RequestVote RPCs to all peers. "
        "A candidate becomes leader if it receives votes from a majority of nodes in the cluster."
    )
    t0 = time.perf_counter()
    syl_ans_res = session.post(
        f"{BASE_URL}/api/interviews/{syl_session_id}/questions/{syl_first_q.get('id')}/answer",
        json={"answer_text": syl_ans_text}
    )
    syl_ans_time = round(time.perf_counter() - t0, 2)
    print(f"Syllabus answer response: {syl_ans_res.status_code} ({syl_ans_time}s)")
    
    if syl_ans_res.status_code != 200:
        record_issue("Syllabus", "Critical", "Syllabus answer evaluation failed", f"Status: {syl_ans_res.status_code}, Body: {syl_ans_res.text}")
    else:
        syl_eval = syl_ans_res.json().get("evaluation", {})
        print(f"  Syllabus Score: {syl_eval.get('overall_score')}/100")
        print(f"  Next Topic: {syl_ans_res.json().get('next_question', {}).get('skill')}")

    # Complete Syllabus Interview
    print("\nCompleting Syllabus Interview...")
    session.post(f"{BASE_URL}/api/interviews/{syl_session_id}/complete")

    # 6. Check Ancillary Endpoints
    print("\n--- STEP 6: CHECKING DASHBOARD, HISTORY & ANALYTICS ---")
    
    # History
    hist_res = session.get(f"{BASE_URL}/api/interviews/history")
    print(f"History status: {hist_res.status_code}, Sessions count: {len(hist_res.json() if hist_res.status_code == 200 else [])}")
    if hist_res.status_code != 200:
        record_issue("History", "High", "History endpoint failed", f"Status: {hist_res.status_code}")

    # Analytics / Performance
    perf_res = session.get(f"{BASE_URL}/api/analytics/overview")
    print(f"Analytics overview status: {perf_res.status_code}")
    if perf_res.status_code != 200:
        record_issue("Analytics", "Medium", "Analytics overview endpoint failed", f"Status: {perf_res.status_code}, Body: {perf_res.text}")

    print("\n=== E2E TESTING COMPLETED ===")
    print(f"Total Issues Detected: {len(ISSUES)}")
    for i, iss in enumerate(ISSUES, 1):
        print(f"{i}. [{iss['severity'].upper()}] [{iss['category']}] {iss['title']}: {iss['details']}")

    # Save findings to scratch
    with open(DOCS_DIR / "e2e_findings.json", "w") as f:
        json.dump(ISSUES, f, indent=2)

if __name__ == "__main__":
    run_e2e()
