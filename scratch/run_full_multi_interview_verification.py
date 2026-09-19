import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import uuid
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def run_test():
    print("==================================================================")
    print("STARTING 2 FULL NORMAL INTERVIEWS + 2 FULL SYLLABUS INTERVIEWS")
    print("==================================================================")

    # 1. Register test user
    uid = uuid.uuid4().hex[:6]
    email = f"candidate_{uid}@example.com"
    pw = "Password123!"
    r_reg = requests.post(f"{BASE_URL}/auth/register", json={
        "name": f"Candidate {uid}",
        "email": email,
        "password": pw,
        "confirm_password": pw
    })
    assert r_reg.status_code == 201, f"Register failed: {r_reg.status_code} {r_reg.text}"
    token = r_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[OK] User registered: {email}")

    # 2. Upload Resume & JD
    with open("scratch/alex_chen_resume.pdf", "rb") as f:
        r_res = requests.post(f"{BASE_URL}/resumes/upload", files={"file": f}, headers=headers)
    assert r_res.status_code in [200, 201], f"Resume upload failed: {r_res.status_code} {r_res.text}"
    resume_id = r_res.json()["id"]
    candidate_name = r_res.json().get("name")
    print(f"[OK] Resume uploaded (ID: {resume_id}, Name: {candidate_name})")

    with open("scratch/senior_backend_jd.pdf", "rb") as f:
        r_jd = requests.post(f"{BASE_URL}/job-descriptions/upload", files={"file": f}, headers=headers)
    assert r_jd.status_code in [200, 201], f"JD upload failed: {r_jd.status_code} {r_jd.text}"
    print(f"[OK] Job Description uploaded")

    # Verify Mapping
    r_map = requests.get(f"{BASE_URL}/job-descriptions/mapping", headers=headers)
    assert r_map.status_code == 200
    mapping = r_map.json()
    print(f"[OK] Skill mapping verified: {len(mapping['matched_skills'])} matched, {len(mapping['gap_skills'])} gaps")

    normal_answers = [
        "In FastAPI, dependency injection is declared using Depends(). It allows sharing database sessions, authentication contexts, and service classes across endpoints. FastAPI resolves dependency graphs and executes async dependencies concurrently.",
        "PostgreSQL uses Multi-Version Concurrency Control (MVCC). Each row contains xmin and xmax transaction IDs, ensuring readers do not block writers and writers do not block readers. Dead tuples are reclaimed by autovacuum.",
        "To mitigate Redis cache stampedes, we implement probabilistic early expiration (XFetch algorithm) or use distributed locking via Redlock to ensure only one worker regenerates the cache entry while others wait or serve stale data.",
        "Docker multi-stage builds enable compiling code in a heavy build container and copying only the final binary or runtime artifacts into a lean image like python:3.11-slim, significantly reducing image size and attack surface."
    ]

    # ================================================================
    # INTERVIEW 1: NORMAL MODE (FULL RUN)
    # ================================================================
    print("\n------------------------------------------------------------------")
    print(">>> INTERVIEW 1: NORMAL MODE (Full 3-Question Interview)")
    print("------------------------------------------------------------------")
    r_start1 = requests.post(f"{BASE_URL}/interviews/start", json={
        "resume_id": resume_id,
        "mode": "normal",
        "difficulty": "medium",
        "question_type": "mixed",
        "selected_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
    }, headers=headers)
    assert r_start1.status_code == 201, f"Start failed: {r_start1.status_code} {r_start1.text}"
    s1_data = r_start1.json()
    s1_id = s1_data["session_id"]
    assert s1_data.get("mode") == "normal"
    curr_q = s1_data["current_question"]

    for q_idx in range(1, 4):
        print(f"\n[Interview 1 - Q{q_idx}] ({curr_q['skill']}, {curr_q['difficulty']}, {curr_q.get('bloom_level')}):")
        print(f"  Question: {curr_q['question_text']}")
        assert curr_q['question_text'] != "[GENERATION FAILED]", "Question generation failed!"
        
        # Submit answer
        ans_text = normal_answers[(q_idx - 1) % len(normal_answers)]
        t0 = time.perf_counter()
        r_ans = requests.post(
            f"{BASE_URL}/interviews/{s1_id}/questions/{curr_q['id']}/answer",
            json={"answer_text": ans_text},
            headers=headers
        )
        elapsed = round(time.perf_counter() - t0, 2)
        assert r_ans.status_code == 200, f"Answer failed: {r_ans.status_code} {r_ans.text}"
        ans_data = r_ans.json()
        eval_data = ans_data["evaluation"]
        print(f"  Answer evaluated in {elapsed}s: Score {eval_data['overall_score']}/100")
        print(f"  Feedback: {eval_data['feedback'][:100]}...")
        assert eval_data['overall_score'] > 0, "Evaluation produced 0 score on technical answer"
        
        if q_idx < 3:
            curr_q = ans_data["next_question"]
            assert curr_q is not None, f"Expected next question for Q{q_idx+1}"

    # Finish Interview 1
    r_finish1 = requests.post(f"{BASE_URL}/interviews/{s1_id}/complete", headers=headers)
    assert r_finish1.status_code == 200
    r_res1 = requests.get(f"{BASE_URL}/interviews/{s1_id}/results", headers=headers)
    assert r_res1.status_code == 200
    print(f"[OK] Interview 1 Completed Successfully! Avg score: {r_res1.json().get('overall_average_score')}%")

    # ================================================================
    # INTERVIEW 2: NORMAL MODE (SECOND FULL RUN)
    # ================================================================
    print("\n------------------------------------------------------------------")
    print(">>> INTERVIEW 2: NORMAL MODE (Second Full 3-Question Interview)")
    print("------------------------------------------------------------------")
    r_start2 = requests.post(f"{BASE_URL}/interviews/start", json={
        "resume_id": resume_id,
        "mode": "normal",
        "difficulty": "hard",
        "question_type": "technical_reasoning",
        "selected_skills": ["PostgreSQL", "Redis"]
    }, headers=headers)
    assert r_start2.status_code == 201
    s2_data = r_start2.json()
    s2_id = s2_data["session_id"]
    curr_q = s2_data["current_question"]

    for q_idx in range(1, 4):
        print(f"\n[Interview 2 - Q{q_idx}] ({curr_q['skill']}, {curr_q['difficulty']}, {curr_q.get('bloom_level')}):")
        print(f"  Question: {curr_q['question_text']}")
        assert curr_q['question_text'] != "[GENERATION FAILED]"
        
        ans_text = normal_answers[(q_idx + 1) % len(normal_answers)]
        r_ans = requests.post(
            f"{BASE_URL}/interviews/{s2_id}/questions/{curr_q['id']}/answer",
            json={"answer_text": ans_text},
            headers=headers
        )
        assert r_ans.status_code == 200
        ans_data = r_ans.json()
        eval_data = ans_data["evaluation"]
        print(f"  Answer Score: {eval_data['overall_score']}/100 | Feedback: {eval_data['feedback'][:80]}...")
        
        if q_idx < 3:
            curr_q = ans_data["next_question"]
            assert curr_q is not None

    r_finish2 = requests.post(f"{BASE_URL}/interviews/{s2_id}/complete", headers=headers)
    assert r_finish2.status_code == 200
    print(f"[OK] Interview 2 Completed Successfully!")

    # ================================================================
    # UPLOAD SYLLABUS FOR SYLLABUS INTERVIEWS
    # ================================================================
    print("\n------------------------------------------------------------------")
    print(">>> UPLOADING SYLLABUS (Distributed Systems)")
    print("------------------------------------------------------------------")
    with open("scratch/cs450_distributed_systems_syllabus.pdf", "rb") as f:
        r_syl = requests.post(
            f"{BASE_URL}/interviews/upload-syllabus",
            files={"files": ("cs450_distributed_systems_syllabus.pdf", f, "application/pdf")},
            headers=headers
        )
    assert r_syl.status_code == 200
    syl_res = r_syl.json()
    syllabus_id = syl_res["syllabus_id"]
    topics = syl_res["topics"]
    print(f"[OK] Syllabus processed: {len(topics)} topics inferred: {topics[:3]}...")

    banned_meta_phrases = [
        "according to the provided",
        "as described in the syllabus",
        "based on the uploaded",
        "as mentioned in unit",
        "in the provided excerpt",
        "according to excerpt",
        "provided syllabus"
    ]

    syllabus_answers = [
        "A socket is an endpoint abstraction for bidirectional network communication across a computer network. In client-server architectures, the server binds a socket to an IP and port to listen for incoming connections, while the client initiates a socket connection to transmit and receive byte streams.",
        "Client-server architecture features centralized servers responding to request-response cycles, offering strong consistency but single-point failure bottlenecks. In contrast, Peer-to-Peer (P2P) systems distribute resource sharing equally among all participating nodes, providing high fault tolerance and decentralization at the expense of coordination complexity.",
        "Lamport logical clocks establish a happened-before relationship using monotonically increasing scalar counters. If event A causes event B, clock(A) < clock(B). When a message is sent, the timestamp is attached, and the receiver updates its clock to max(local_clock, msg_timestamp) + 1.",
        "In Stop-and-Wait ARQ, pipelining cannot be employed because the sender must wait for an explicit acknowledgment (ACK) of the previous frame before transmitting the next frame. This limits channel utilization on high bandwidth-delay product links."
    ]

    # ================================================================
    # INTERVIEW 3: SYLLABUS MODE (FIRST FULL RUN)
    # ================================================================
    print("\n------------------------------------------------------------------")
    print(">>> INTERVIEW 3: SYLLABUS MODE (First Full 3-Question Interview)")
    print("------------------------------------------------------------------")
    r_syl_start1 = requests.post(f"{BASE_URL}/interviews/start", json={
        "mode": "syllabus",
        "syllabus_id": syllabus_id,
        "difficulty": "medium",
        "selected_topics": topics[:4]
    }, headers=headers)
    assert r_syl_start1.status_code == 201
    s3_data = r_syl_start1.json()
    s3_id = s3_data["session_id"]
    assert s3_data.get("mode") == "syllabus"
    curr_q = s3_data["current_question"]

    for q_idx in range(1, 4):
        q_text = curr_q['question_text']
        print(f"\n[Interview 3 - Q{q_idx}] Topic: {curr_q['skill']} ({curr_q['difficulty']}, {curr_q.get('bloom_level')}):")
        print(f"  Question: {q_text}")
        assert q_text != "[GENERATION FAILED]"
        for bp in banned_meta_phrases:
            assert bp not in q_text.lower(), f"Meta-language leakage found in Q{q_idx}: '{bp}' in '{q_text}'"

        ans_text = syllabus_answers[(q_idx - 1) % len(syllabus_answers)]
        t0 = time.perf_counter()
        r_ans = requests.post(
            f"{BASE_URL}/interviews/{s3_id}/questions/{curr_q['id']}/answer",
            json={"answer_text": ans_text},
            headers=headers
        )
        elapsed = round(time.perf_counter() - t0, 2)
        assert r_ans.status_code == 200
        ans_data = r_ans.json()
        eval_data = ans_data["evaluation"]
        print(f"  Answer evaluated in {elapsed}s: Score {eval_data['overall_score']}/100")
        print(f"  Feedback: {eval_data['feedback'][:90]}...")
        assert eval_data['overall_score'] > 0

        if q_idx < 3:
            curr_q = ans_data["next_question"]
            assert curr_q is not None

    r_finish3 = requests.post(f"{BASE_URL}/interviews/{s3_id}/complete", headers=headers)
    assert r_finish3.status_code == 200
    r_res3 = requests.get(f"{BASE_URL}/interviews/{s3_id}/results", headers=headers)
    assert r_res3.status_code == 200
    print(f"[OK] Interview 3 (Syllabus) Completed Successfully! Avg score: {r_res3.json().get('overall_average_score')}%")

    # ================================================================
    # INTERVIEW 4: SYLLABUS MODE (SECOND FULL RUN)
    # ================================================================
    print("\n------------------------------------------------------------------")
    print(">>> INTERVIEW 4: SYLLABUS MODE (Second Full 3-Question Interview)")
    print("------------------------------------------------------------------")
    # Ingest fresh syllabus session
    with open("scratch/cs450_distributed_systems_syllabus.pdf", "rb") as f:
        r_syl2 = requests.post(
            f"{BASE_URL}/interviews/upload-syllabus",
            files={"files": ("cs450_distributed_systems_syllabus.pdf", f, "application/pdf")},
            headers=headers
        )
    assert r_syl2.status_code == 200
    syl2_id = r_syl2.json()["syllabus_id"]
    
    r_syl_start2 = requests.post(f"{BASE_URL}/interviews/start", json={
        "mode": "syllabus",
        "syllabus_id": syl2_id,
        "difficulty": "hard",
        "selected_topics": topics[2:5]
    }, headers=headers)
    assert r_syl_start2.status_code == 201
    s4_data = r_syl_start2.json()
    s4_id = s4_data["session_id"]
    curr_q = s4_data["current_question"]

    for q_idx in range(1, 4):
        q_text = curr_q['question_text']
        print(f"\n[Interview 4 - Q{q_idx}] Topic: {curr_q['skill']} ({curr_q['difficulty']}, {curr_q.get('bloom_level')}):")
        print(f"  Question: {q_text}")
        assert q_text != "[GENERATION FAILED]"
        for bp in banned_meta_phrases:
            assert bp not in q_text.lower(), f"Meta-language leakage found in Q{q_idx}: '{bp}' in '{q_text}'"

        ans_text = syllabus_answers[(q_idx + 1) % len(syllabus_answers)]
        r_ans = requests.post(
            f"{BASE_URL}/interviews/{s4_id}/questions/{curr_q['id']}/answer",
            json={"answer_text": ans_text},
            headers=headers
        )
        assert r_ans.status_code == 200
        ans_data = r_ans.json()
        eval_data = ans_data["evaluation"]
        print(f"  Answer Score: {eval_data['overall_score']}/100 | Feedback: {eval_data['feedback'][:90]}...")
        assert eval_data['overall_score'] > 0

        if q_idx < 3:
            curr_q = ans_data["next_question"]
            assert curr_q is not None

    r_finish4 = requests.post(f"{BASE_URL}/interviews/{s4_id}/complete", headers=headers)
    assert r_finish4.status_code == 200
    print(f"[OK] Interview 4 (Syllabus) Completed Successfully!")

    # Verify history
    r_hist = requests.get(f"{BASE_URL}/interviews/history", headers=headers)
    assert r_hist.status_code == 200
    history = r_hist.json()
    print(f"\n[OK] History verified: {len(history)} total interviews recorded for user.")
    assert len(history) == 4, f"Expected 4 interviews in history, got {len(history)}"

    print("\n==================================================================")
    print("ALL 4 FULL INTERVIEWS (2 NORMAL + 2 SYLLABUS) PASSED WITH ZERO ISSUES!")
    print("==================================================================")

if __name__ == "__main__":
    run_test()
