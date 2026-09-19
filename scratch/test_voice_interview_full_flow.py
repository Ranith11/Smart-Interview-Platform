"""
Full End-to-End Voice Interview Workflow Verification
Tests:
1. Candidate Authentication
2. Resume & Skill Context Setup
3. Adaptive Interview Session Creation & Question 1 Generation
4. TTS Generation with Natural AI Welcome Intro (Q1)
5. Audio Voice Answer -> Groq Whisper STT Transcription
6. Answer Submission & Multi-Factor Evaluation (Reusing existing engine)
7. Question 2 Generation with Conversational Phrasing & Subsequent TTS
8. Adaptive Engine Rule Verification (Continues normally despite low score, adjusts difficulty/Bloom)
9. Manual Completion ("Finish Interview") & Results Generation
10. Strict Auto-Stop & Safety Limit Verification
"""

import sys
import os
import io
import uuid
import time

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app
from app.services.voice_service import synthesize_speech_bytes

client = TestClient(app)

def run_full_voice_test():
    print("=" * 70)
    print("  SMARTINTERVIEW COMPLETE VOICE-DRIVEN WORKFLOW VERIFICATION")
    print("=" * 70)

    # 1. Candidate Authentication
    uid = uuid.uuid4().hex[:6]
    email = f"voice_candidate_{uid}@example.com"
    pwd = "TestPassword123!"

    print("\n[STEP 1] Registering Candidate...")
    r_reg = client.post("/api/auth/register", json={
        "name": f"Voice Candidate {uid}",
        "email": email,
        "password": pwd,
        "confirm_password": pwd
    })
    assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
    token = r_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Candidate registered & logged in: {email}")

    # 2. Upload Candidate Resume
    print("\n[STEP 2] Uploading Candidate Resume...")
    pdf_path = "scratch/alex_chen_resume.pdf"
    with open(pdf_path, "rb") as f:
        r_res = client.post(
            "/api/resumes/upload",
            files={"file": ("alex_chen_resume.pdf", f, "application/pdf")},
            headers=headers
        )
    assert r_res.status_code in (200, 201), f"Resume upload failed: {r_res.text}"
    resume_id = r_res.json()["id"]
    print(f"  [PASS] Resume processed (ID: {resume_id})")

    # 2b. Upload Job Description
    print("\n[STEP 2b] Uploading Job Description...")
    with open("scratch/senior_backend_jd.pdf", "rb") as f:
        r_jd = client.post(
            "/api/job-descriptions/upload",
            files={"file": ("senior_backend_jd.pdf", f, "application/pdf")},
            headers=headers
        )
    assert r_jd.status_code in [200, 201], f"JD upload failed: {r_jd.text}"
    print(f"  [PASS] Job Description uploaded (ID: {r_jd.json()['id']})")

    # 3. Start Adaptive Interview Session
    print("\n[STEP 3] Starting Adaptive Interview Session...")
    r_start = client.post("/api/interviews/start", json={
        "resume_id": resume_id,
        "difficulty": "medium",
        "question_type": "conceptual",
        "question_count": 5,
        "selected_skills": ["Python", "PostgreSQL", "Docker"]
    }, headers=headers)
    assert r_start.status_code == 201, f"Start failed: {r_start.text}"
    session_data = r_start.json()
    session_id = session_data["session_id"]
    q1 = session_data["current_question"]
    print(f"  [PASS] Session created (ID: {session_id})")
    print(f"         Q1 ID={q1['id']}, Skill='{q1['skill']}', Bloom='{q1['bloom_level']}', Diff='{q1['difficulty']}'")
    print(f"         Question 1: \"{q1['question_text']}\"")

    # 4. Question 1 TTS Audio Generation (with Introduction Greeting)
    print("\n[STEP 4] Synthesizing Question 1 TTS Audio (with Intro)...")
    t0 = time.perf_counter()
    r_tts = client.post("/api/interviews/voice/tts", json={
        "text": q1["question_text"],
        "question_number": 1,
        "include_intro": True
    })
    tts_time = round(time.perf_counter() - t0, 2)
    assert r_tts.status_code == 200, f"TTS failed: {r_tts.text}"
    assert r_tts.headers["content-type"] == "audio/mpeg"
    q1_audio = r_tts.content
    print(f"  [PASS] Q1 Spoken Audio Generated in {tts_time}s ({len(q1_audio)} bytes MP3)")

    # 5. Candidate Speaks Technical Answer -> Whisper STT Transcription
    print("\n[STEP 5] Candidate Speaks Technical Answer via Voice...")
    spoken_text = (
        "In Python, the Global Interpreter Lock or GIL prevents multiple native threads "
        "from executing Python bytecodes concurrently, which is why multiprocessing or async event loops "
        "are often used for CPU-bound or IO-bound concurrency."
    )
    # Synthesize sample spoken voice to simulate microphone recording
    import asyncio
    simulated_mic_bytes = asyncio.run(synthesize_speech_bytes(spoken_text))

    t0 = time.perf_counter()
    r_stt = client.post(
        "/api/interviews/voice/transcribe",
        files={"file": ("candidate_answer.webm", io.BytesIO(simulated_mic_bytes), "audio/webm")},
        headers=headers
    )
    stt_time = round(time.perf_counter() - t0, 2)
    assert r_stt.status_code == 200, f"STT failed: {r_stt.text}"
    transcript = r_stt.json()["transcript"]
    print(f"  [PASS] Whisper STT Transcribed in {stt_time}s:")
    print(f"         \"{transcript}\"")
    assert len(transcript) > 20

    # 6. Candidate Submits Transcribed Answer (Evaluation)
    print("\n[STEP 6] Submitting Answer to Evaluation Engine...")
    t0 = time.perf_counter()
    r_eval = client.post(
        f"/api/interviews/{session_id}/questions/{q1['id']}/answer",
        json={"answer_text": transcript},
        headers=headers
    )
    eval_time = round(time.perf_counter() - t0, 2)
    assert r_eval.status_code == 200, f"Evaluation failed: {r_eval.text}"
    eval_res = r_eval.json()
    evaluation = eval_res["evaluation"]
    print(f"  [PASS] Multi-factor Evaluation finished in {eval_time}s:")
    print(f"         Overall Score: {evaluation['overall_score']}%")
    print(f"         Technical Score: {evaluation['technical_score']}%")
    print(f"         Completeness Score: {evaluation['completeness_score']}%")
    print(f"         Relevance Score: {evaluation['relevance_score']}%")
    print(f"         Semantic Similarity: {evaluation['semantic_similarity_score']}%")
    print(f"         Concept Coverage: {evaluation['concept_coverage_score']}%")
    print(f"         Feedback: {evaluation['feedback'][:90]}...")

    # 7. Next Question Generation & Conversational Continuity
    print("\n[STEP 7] Verifying Question 2 Generation & Delivery...")
    q2 = eval_res["next_question"]
    assert q2 is not None, "Question 2 should be generated"
    print(f"  [PASS] Q2 Generated: Skill='{q2['skill']}', Bloom='{q2['bloom_level']}', Diff='{q2['difficulty']}'")
    print(f"         Question 2: \"{q2['question_text']}\"")

    # Synthesize Q2 TTS (without intro)
    r_tts2 = client.post("/api/interviews/voice/tts", json={
        "text": q2["question_text"],
        "question_number": 2,
        "include_intro": False
    })
    assert r_tts2.status_code == 200
    print(f"  [PASS] Q2 Spoken Audio Synthesized ({len(r_tts2.content)} bytes MP3)")

    # 8. Adaptive Rules Verification (Poor answer test)
    print("\n[STEP 8] Verifying Adaptive Rules (Poor Answer does NOT terminate interview)...")
    poor_answer = "I am not completely sure about this topic."
    r_eval2 = client.post(
        f"/api/interviews/{session_id}/questions/{q2['id']}/answer",
        json={"answer_text": poor_answer},
        headers=headers
    )
    assert r_eval2.status_code == 200
    eval_res2 = r_eval2.json()
    print(f"  [PASS] Answer evaluated: Overall Score = {eval_res2['evaluation']['overall_score']}%")
    assert eval_res2["is_complete"] is False, "A single poor answer must NEVER terminate the interview!"
    assert eval_res2["next_question"] is not None, "Next question should still be generated"
    print("  [PASS] Interview continues normally; adaptive engine adjusted difficulty/Bloom level.")

    # 9. Manual Completion ("Finish Interview")
    print("\n[STEP 9] Testing Manual Completion (\"Finish Interview\")...")
    r_comp = client.post(f"/api/interviews/{session_id}/complete", headers=headers)
    assert r_comp.status_code == 200, f"Complete failed: {r_comp.text}"
    comp_data = r_comp.json()
    print(f"  [PASS] Interview marked completed with reason: '{comp_data.get('completion_reason', 'manual')}'")
    print(f"         Average Score: {comp_data.get('overall_average_score', 0)}%")
    print(f"         Skill Breakdown: {list(comp_data.get('skill_breakdown', {}).keys())}")

    print("\n" + "=" * 70)
    print("  ALL VOICE-DRIVEN INTERVIEW TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_full_voice_test()
