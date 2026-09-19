"""
SmartInterview: End-to-End Live Demonstration
Shows:
1. Upload & Ingest Syllabus Material (isolated temporary collection created)
2. Active Interview: Question generated strictly from uploaded material
3. Answer submission & real-time evaluation (interview continues open-endedly)
4. Interview Completion: Post-interview deduplicated merge into permanent technical_kb
5. Lifecycle Cleanup: Temporary ChromaDB collection deleted
6. Future Practice Session: technical_kb queried directly, demonstrating normal retrieval of merged knowledge
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User
from app.models.interview import InterviewSession
from app.services.syllabus_rag_service import (
    process_and_create_syllabus_rag,
    merge_temporary_to_permanent_kb,
    delete_temporary_rag,
)
from app.services.interview_service import (
    create_interview_session,
    submit_and_evaluate,
    complete_interview,
)
from app.config import CHROMA_DB_DIR
from scripts.generate_question import retrieve_rag_context
from app.services.question_service import get_embedding_model
import chromadb


def main():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "jd_tester_99@example.com").first()
    if not user:
        user = db.query(User).first()

    print("=" * 80)
    print("      SMARTINTERVIEW: LIVE END-TO-END DEMONSTRATION")
    print("=" * 80)
    print(f"Candidate: {user.email} (ID: {user.id})")

    # Step 1: Upload & Process Syllabus Material
    print("\n[STEP 1] Uploading and Ingesting Course Syllabus Material...")
    syllabus_sample_text = (
        "Course: Advanced Computer Networking and Distributed Systems\n"
        "Topic 1: Stop-and-Wait ARQ Protocol\n"
        "In the Stop-and-Wait ARQ protocol, the sender transmits a single frame and stops to wait for an acknowledgment (ACK) "
        "before sending the next frame. It cannot employ pipelining because the sender window size is strictly 1, which underutilizes "
        "high bandwidth-delay product links.\n\n"
        "Topic 2: Sliding Window Protocols (Go-Back-N vs Selective Repeat)\n"
        "Pipelining protocols allow multiple in-flight packets. Go-Back-N uses cumulative acknowledgments and retransmits all packets "
        "starting from the oldest unacknowledged packet upon timeout. Selective Repeat acknowledges individual packets and retransmits "
        "only the specifically lost packet using individual ACK timers."
    )
    test_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "demo_syllabus.txt"))
    with open(test_filepath, "w", encoding="utf-8") as f:
        f.write(syllabus_sample_text)

    temp_id = f"demo_{int(time.time())}"
    t0 = time.time()
    processed = process_and_create_syllabus_rag(
        temp_id=temp_id,
        file_paths=[test_filepath],
        filename_hints=["Advanced_Networking_Syllabus.txt"],
    )
    print(f"  -> Processed in {(time.time() - t0):.2f}s")
    print(f"  -> Syllabus ID: {processed['syllabus_id']}")
    print(f"  -> Inferred Subject: {processed['subject']}")
    print(f"  -> Detected Topics: {processed['topics']}")
    print(f"  -> Isolated Chunks Created: {processed['chunks_count']}")

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    perm_col = client.get_collection("technical_kb")
    kb_count_before = perm_col.count()
    print(f"\n[INFO] Permanent technical_kb count BEFORE interview: {kb_count_before} chunks")

    # Step 2: Start Interview (Strictly Isolated to Uploaded PDF)
    print("\n[STEP 2] Starting Syllabus Interview Session...")
    session_data = create_interview_session(
        db=db,
        user_id=user.id,
        mode="syllabus",
        syllabus_id=temp_id,
        selected_topics=processed["topics"][:2],
    )
    session = session_data["session"]
    q1 = session_data["current_question"]
    print(f"  -> Session Created: ID={session.id}, Mode={session.mode}")
    print(f"  -> Status: {session.status}")
    print(f"  -> Question 1 (Grounded in uploaded syllabus):")
    print(f"     \"{q1.question_text}\"")

    # Step 3: Submit Answer and Evaluate (Open-Ended Flow)
    print("\n[STEP 3] Candidate Submits Answer to Question 1...")
    answer_text = (
        "Stop-and-Wait protocol cannot employ pipelining because the sender window size is limited to 1. "
        "The sender must wait for an acknowledgment (ACK) for the transmitted frame before sending any further frames, "
        "which results in significant link underutilization."
    )
    t0 = time.time()
    eval_data = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=session.id,
        question_id=q1.id,
        answer_text=answer_text,
    )
    print(f"  -> Evaluated in {(time.time() - t0):.2f}s")
    ev = eval_data["evaluation"]
    print(f"  -> Overall Score: {ev['overall_score']}% (Technical: {ev['technical_score']}%, Relevance: {ev['relevance_score']}%)")
    print(f"  -> Feedback: {ev['feedback'][:120]}...")
    print(f"  -> Is Complete: {eval_data['is_complete']} (Interview is open-ended, ready for Question {eval_data['next_question'].question_number})")
    print(f"  -> Next Question Generated: \"{eval_data['next_question'].question_text[:80]}...\"")

    # Verify temp collection is still intact during interview
    temp_col_check = client.get_collection(f"temp_syllabus_{temp_id}")
    print(f"  -> Temporary collection still active during interview with {temp_col_check.count()} chunks.")

    # Step 4: Candidate Concludes Interview -> Post-Interview Ingestion Triggered
    print("\n[STEP 4] Candidate Clicks 'Finish Interview' (Post-Interview Ingestion Triggered)...")
    completed_session = complete_interview(
        db=db,
        user_id=user.id,
        session_id=session.id,
        completion_reason="candidate_finished",
    )
    print(f"  -> Session Status: {completed_session.status}")
    print(f"  -> Completion Reason: {completed_session.completion_reason}")

    # Check permanent knowledge base count after merge
    kb_count_after = perm_col.count()
    print(f"\n[STEP 5] Checking Permanent Knowledge Base After Ingestion...")
    print(f"  -> Permanent technical_kb count AFTER interview: {kb_count_after} chunks")
    print(f"  -> New distinct chunks absorbed into technical_kb: {kb_count_after - kb_count_before}")

    # Verify temporary collection was cleaned up
    all_collections = [c if isinstance(c, str) else c.name for c in client.list_collections()]
    is_temp_deleted = f"temp_syllabus_{temp_id}" not in all_collections
    print(f"  -> Temporary collection deleted: {is_temp_deleted}")

    # Step 6: Test Deduplication by re-merging identical data
    print("\n[STEP 6] Testing Deduplication (Simulating duplicate data submission)...")
    temp_dup_col = client.create_collection(f"temp_syllabus_{temp_id}_dup")
    temp_dup_col.add(
        ids=[f"dup_1"],
        documents=[syllabus_sample_text[:300]],
        metadatas=[{"domain": "Computer Networks", "source": "Advanced_Networking_Syllabus.txt"}],
        embeddings=get_embedding_model().encode([syllabus_sample_text[:300]], convert_to_numpy=True).tolist()
    )
    dup_merge_res = merge_temporary_to_permanent_kb(f"{temp_id}_dup")
    print(f"  -> Deduplication Result on duplicate text:")
    print(f"     Merged Count: {dup_merge_res['merged_count']}")
    print(f"     Exact Skipped: {dup_merge_res['exact_skipped']}")
    print(f"     Semantic Skipped: {dup_merge_res['semantic_skipped']}")
    client.delete_collection(f"temp_syllabus_{temp_id}_dup")

    # Step 7: Future Practice Session Retrieval from Merged technical_kb
    print("\n[STEP 7] Future Practice Session: Querying technical_kb for 'Stop-and-Wait'...")
    retrieved, query = retrieve_rag_context(
        skill="Stop-and-Wait Protocol",
        embedding_model=get_embedding_model(),
        collection=perm_col,
        domains=["cn"],
    )
    print(f"  -> Retrieval Query: '{query}'")
    print(f"  -> Retrieved {len(retrieved)} chunks from technical_kb:")
    for idx, chunk in enumerate(retrieved):
        print(f"     [{idx+1}] (Domain: {chunk['domain']}, Concept: {chunk['concept']})")
        print(f"         {chunk['text'][:140]}...")

    if os.path.exists(test_filepath):
        os.remove(test_filepath)
    db.close()

    print("\n" + "=" * 80)
    print("      END-TO-END DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
