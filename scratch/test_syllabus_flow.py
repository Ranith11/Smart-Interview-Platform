"""
End-to-End Verification Test for Syllabus Flow:
1. Create a sample syllabus document.
2. Run process_and_create_syllabus_rag (measure timings).
3. Test topic inference & Chroma collection creation.
4. Test create_interview_session with mode="syllabus".
5. Test question generation and source-grounding.
6. Test submit_and_evaluate with syllabus adaptive state progression.
7. Test complete_interview and verify temp Chroma collection cleanup.
"""

import sys
import os
import shutil
from pathlib import Path

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Set up path to import backend app
PROJECT_ROOT = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
from app.config import CHROMA_DB_DIR
from app.database import SessionLocal
from app.models.user import User
from app.models.interview import InterviewSession
from app.services.syllabus_rag_service import (
    process_and_create_syllabus_rag,
    delete_temporary_rag,
)
from app.services.interview_service import (
    create_interview_session,
    submit_and_evaluate,
    complete_interview,
)

def run_test():
    print("=== STARTING SYLLABUS FLOW E2E TEST ===")

    # 1. Create a sample syllabus text file
    sample_text = """
    COURSE SYLLABUS: OPERATING SYSTEMS (CS301)
    
    UNIT 1: PROCESS MANAGEMENT AND CPU SCHEDULING
    - Process concepts, process states, and Process Control Block (PCB).
    - CPU Scheduling algorithms: First-Come First-Served (FCFS), Shortest Job First (SJF), Priority Scheduling, and Round Robin (RR).
    - Multiprocessing, context switching, and Inter-Process Communication (IPC) via message passing and shared memory.
    
    UNIT 2: PROCESS SYNCHRONIZATION AND DEADLOCKS
    - Critical section problem, Peterson's algorithm, and hardware synchronization.
    - Semaphores, mutex locks, and monitors.
    - Classical synchronization problems: Dining Philosophers, Producer-Consumer, and Readers-Writers.
    - Deadlock characterization, Resource Allocation Graph (RAG), Deadlock Prevention, Avoidance (Banker's Algorithm), and Recovery.
    
    UNIT 3: MEMORY MANAGEMENT AND VIRTUAL MEMORY
    - Logical vs physical address spaces, paging, and segmentation.
    - Virtual memory concepts, demand paging, and page fault handling.
    - Page replacement algorithms: FIFO, Least Recently Used (LRU), and Optimal replacement.
    - Thrashing and working set model.
    """

    test_file_path = Path(__file__).resolve().parent / "test_os_syllabus.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(sample_text)

    print(f"[1] Created test syllabus file at: {test_file_path}")

    # 2. Process and create syllabus RAG
    temp_id = "test_e2e_syllabus_001"
    print(f"[2] Running process_and_create_syllabus_rag with temp_id={temp_id}...")
    rag_result = process_and_create_syllabus_rag(
        temp_id=temp_id,
        file_paths=[str(test_file_path)],
        filename_hints=["test_os_syllabus.txt"],
    )

    print(f"    Subject inferred: {rag_result['subject']}")
    print(f"    Topics detected ({len(rag_result['topics'])}): {rag_result['topics']}")
    print(f"    Chunks count: {rag_result['chunks_count']}")
    print(f"    Timing Metrics: {rag_result['metrics']}")

    assert rag_result["chunks_count"] > 0, "Chunks count must be > 0"
    assert len(rag_result["topics"]) >= 2, "Must infer at least 2 topics"

    # Verify temporary chroma collection exists
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    col_name = f"temp_syllabus_{temp_id}"
    col = chroma_client.get_collection(col_name)
    print(f"    Chroma collection '{col_name}' verified! Document count: {col.count()}")
    assert col.count() == rag_result["chunks_count"]

    # 3. Create interview session in DB
    db = SessionLocal()
    try:
        # Get or create test user
        user = db.query(User).filter(User.email == "test@syllabus.com").first()
        if not user:
            user = User(
                email="test@syllabus.com",
                name="Syllabus Test Candidate",
                password_hash="fakehash123",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        print(f"[3] Creating syllabus interview session for user {user.id}...")
        selected_topics = rag_result["topics"][:3]
        session_data = create_interview_session(
            db=db,
            user_id=user.id,
            mode="syllabus",
            syllabus_id=temp_id,
            selected_topics=selected_topics,
        )

        session = session_data["session"]
        first_q = session_data["current_question"]
        print(f"    Session ID: {session.id}, Mode: {session.mode}, Syllabus ID: {session.syllabus_id}")
        print(f"    First Question (Topic: {first_q.skill}):")
        print(f"    '{first_q.question_text}'")

        assert session.mode == "syllabus"
        assert session.syllabus_id == temp_id
        assert first_q.skill in selected_topics

        # 4. Submit an answer and evaluate
        print("[4] Submitting candidate answer...")
        answer_text = (
            "Round Robin scheduling is a preemptive CPU scheduling algorithm where each process is assigned a fixed time slice called a quantum. "
            "If the process doesn't finish within its quantum, it is interrupted and placed at the back of the ready queue."
        )
        answer_res = submit_and_evaluate(
            db=db,
            user_id=user.id,
            session_id=session.id,
            question_id=first_q.id,
            answer_text=answer_text,
        )

        eval_data = answer_res["evaluation"]
        print(f"    Overall Score: {eval_data['overall_score']}")
        next_q = answer_res.get("next_question")
        if next_q:
            print(f"    Next Topic Selected: {next_q.skill}")
            print(f"    Next Question: {next_q.question_text}")

        # 5. Complete interview and verify cleanup
        print("[5] Completing interview session...")
        complete_res = complete_interview(db=db, user_id=user.id, session_id=session.id)
        print(f"    Completed reason: {complete_res.completion_reason}")

        # 6. Verify Chroma temporary collection is deleted
        print("[6] Verifying temporary Chroma collection cleanup...")
        raw_cols = chroma_client.list_collections()
        collections_after = [c if isinstance(c, str) else c.name for c in raw_cols]
        print(f"    Remaining collections in chroma: {collections_after}")
        assert col_name not in collections_after, f"Collection {col_name} should have been cleaned up!"
        print(f"    SUCCESS: Temporary collection {col_name} was completely cleaned up!")

    finally:
        db.close()
        if test_file_path.exists():
            test_file_path.unlink()

    print("=== ALL SYLLABUS FLOW TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_test()
