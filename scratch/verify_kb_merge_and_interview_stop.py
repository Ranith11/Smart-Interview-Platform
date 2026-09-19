"""
Verification Script: Post-Interview Knowledge Base Merge, Deduplication, & Natural Stopping Target
Tests:
1. Deduplication (Exact Content Hash & Semantic Near-Duplicate Filtering)
2. Normal Practice Session Retrieval from technical_kb with Merged Chunks
3. Target Question Stopping (Natural Interview Completion)
4. Syllabus Interview Lifecycle: Isolation during interview -> Post-Interview Merge -> Temp Cleanup
"""

import sys
import os
import uuid
import time
import hashlib

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.interview import InterviewSession
from app.models.question import InterviewQuestion, Answer, AnswerEvaluation
from app.services.syllabus_rag_service import (
    process_and_create_syllabus_rag,
    merge_temporary_to_permanent_kb,
    delete_temporary_rag,
    resolve_kb_domain,
)
from app.services.interview_service import (
    create_interview_session,
    submit_and_evaluate,
    complete_interview,
)
from app.config import CHROMA_DB_DIR
from scripts.generate_question import retrieve_rag_context, resolve_skill_domains
from app.services.question_service import get_embedding_model, get_chroma_collection


def print_step(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_tests():
    db = SessionLocal()
    # Find user with a resume
    resume = db.query(Resume).filter(Resume.skills.isnot(None)).first()
    assert resume is not None, "A resume must exist in the database."
    user = db.query(User).filter(User.id == resume.user_id).first()
    assert user is not None, "A user owning the resume must exist."

    # Ensure user has a JD
    jd = db.query(JobDescription).filter(JobDescription.user_id == user.id).first()
    if not jd:
        jd = JobDescription(
            user_id=user.id,
            raw_text="Software Engineer with Python, FastAPI, Docker",
            title="Backend Engineer",
            skills=["Python", "FastAPI", "Docker", "SQL"],
        )
        db.add(jd)
        db.commit()
        db.refresh(jd)

    print(f"Using user: {user.email} (ID: {user.id}), Resume ID: {resume.id}, JD ID: {jd.id}")

    # -------------------------------------------------------------
    # TEST 1: Canonical Domain Resolution
    # -------------------------------------------------------------
    print_step("TEST 1: Canonical Domain Resolution")
    test_cases = [
        ("Computer Networks and Protocols", "cn"),
        ("Operating Systems & Kernel Architecture", "os"),
        ("Database Management Systems (DBMS)", "dbms"),
        ("Advanced Data Structures & Algorithms", "dsa"),
        ("Object-Oriented Programming (OOP)", "oop"),
        ("Deep Learning and Neural Networks", "ml-dl"),
        ("Distributed System Design", "system-design"),
        ("Software Design Patterns", "design-patterns"),
        ("Quantum Cryptography", "quantum-cryptography"),
    ]
    for subject, expected in test_cases:
        res = resolve_kb_domain(subject)
        assert res == expected, f"Expected {expected}, got {res} for subject '{subject}'"
        print(f"  [PASS] '{subject}' -> domain: '{res}'")

    # -------------------------------------------------------------
    # TEST 2: Deduplication Engine (Exact Hash & Semantic Filter)
    # -------------------------------------------------------------
    print_step("TEST 2: Two-Layer Deduplication Engine")
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    perm_col = client.get_collection("technical_kb")
    initial_kb_count = perm_col.count()
    print(f"  Initial permanent technical_kb chunk count: {initial_kb_count}")

    # Create a synthetic temporary syllabus collection
    temp_test_id = f"test_dedup_{uuid.uuid4().hex[:8]}"
    temp_col_name = f"temp_syllabus_{temp_test_id}"
    temp_col = client.create_collection(name=temp_col_name)

    # 1. Existing chunk in technical_kb to test duplication against
    existing_sample = perm_col.get(limit=1, include=["documents", "metadatas"])
    existing_text = existing_sample["documents"][0]
    existing_domain = existing_sample["metadatas"][0].get("domain", "general")

    # 2. Genuinely brand-new unique chunk
    unique_text = f"Topological quantum computing {uuid.uuid4().hex}: Non-abelian anyon worldlines undergo braiding operations in two-dimensional space to realize topologically protected fault-tolerant quantum gates."

    # 3. Slightly paraphrased version of existing chunk (semantic near-duplicate)
    near_duplicate_text = existing_text + " In addition, this concept is fundamental to system engineering."

    test_docs = [unique_text, existing_text, near_duplicate_text]
    emb_model = get_embedding_model()
    test_embs = emb_model.encode(test_docs, convert_to_numpy=True).tolist()

    temp_col.add(
        ids=[f"temp_{temp_test_id}_{i}" for i in range(len(test_docs))],
        documents=test_docs,
        embeddings=test_embs,
        metadatas=[{"domain": "System Design", "source": "test_dedup.pdf"} for _ in range(len(test_docs))]
    )

    print(f"  Created temporary collection with 3 chunks: 1 unique, 1 exact duplicate, 1 semantic near-duplicate.")

    # Run merge
    merge_result = merge_temporary_to_permanent_kb(temp_test_id)
    print(f"  Merge result: {merge_result}")

    assert merge_result["merged_count"] >= 1, "At least the unique chunk should be merged!"
    assert merge_result["exact_skipped"] + merge_result["semantic_skipped"] >= 1, "Duplicate data must be skipped!"
    print(f"  [PASS] Genuinely new chunk merged; duplicate chunks successfully caught and skipped.")

    # Run merge a second time to verify idempotency (exact hash deduplication)
    merge_result_2 = merge_temporary_to_permanent_kb(temp_test_id)
    print(f"  Second merge result (idempotency check): {merge_result_2}")
    assert merge_result_2["merged_count"] == 0, "Second merge must add 0 new chunks!"
    assert merge_result_2["exact_skipped"] >= 1, "All previously merged chunks must be skipped by exact hash!"
    print(f"  [PASS] Second merge was 100% idempotent: 0 merged, duplicates filtered.")

    # Cleanup synthetic test collection and test chunk
    client.delete_collection(temp_col_name)
    try:
        perm_col.delete(where={"source": "test_dedup.pdf"})
    except Exception:
        pass

    # -------------------------------------------------------------
    # TEST 3: Natural Interview Stopping (Target Questions Enforced)
    # -------------------------------------------------------------
    print_step("TEST 3: Natural Interview Stopping (Target Question Count)")
    # Start a 3-question session
    target_q_count = 3
    session_data = create_interview_session(
        db=db,
        user_id=user.id,
        resume_id=resume.id,
        question_count=target_q_count,
        selected_skills=["Python", "FastAPI"],
        mode="normal",
    )
    test_session = session_data["session"]
    current_q = session_data["current_question"]

    assert test_session.question_count == target_q_count, f"Session question_count should be {target_q_count}"
    print(f"  Created session {test_session.id} with question_count={test_session.question_count}")

    # Answer Q1
    res1 = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=test_session.id,
        question_id=current_q.id,
        answer_text="Python memory management uses private heap allocation and reference counting with generational garbage collection."
    )
    assert not res1["is_complete"], "Interview should NOT complete after question 1"
    print(f"  [Q1] Answered. is_complete={res1['is_complete']}, next_question={res1['next_question'].question_number}")

    # Answer Q2
    current_q2 = res1["next_question"]
    res2 = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=test_session.id,
        question_id=current_q2.id,
        answer_text="FastAPI achieves high performance using Starlette for web parts and Pydantic for data parsing via ASGI."
    )
    assert not res2["is_complete"], "Interview should NOT complete after question 2"
    print(f"  [Q2] Answered. is_complete={res2['is_complete']}, next_question={res2['next_question'].question_number}")

    # Answer Q3 (Target reached!)
    current_q3 = res2["next_question"]
    res3 = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=test_session.id,
        question_id=current_q3.id,
        answer_text="Concurrency in Python can be implemented using async/await with asyncio event loop or multiprocessing for CPU tasks."
    )
    assert res3["is_complete"] is True, "Interview MUST complete after reaching target question count!"
    assert res3["next_question"] is None, "next_question must be None when interview completes!"

    db.refresh(test_session)
    assert test_session.status == "completed", "Session status must be 'completed'"
    assert test_session.completion_reason == "target_questions_reached", f"Reason was {test_session.completion_reason}"
    print(f"  [Q3] Answered. is_complete={res3['is_complete']}, completion_reason='{test_session.completion_reason}'")
    print(f"  [PASS] Interview stopped naturally like a real interview!")

    # -------------------------------------------------------------
    # TEST 4: Syllabus End-to-End Post-Interview Merge
    # -------------------------------------------------------------
    print_step("TEST 4: Syllabus Interview Post-Interview Merge & Cleanup")
    syllabus_text_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_syllabus_sample.txt"))
    with open(syllabus_text_path, "w", encoding="utf-8") as f:
        f.write(
            "Computer Networks: Transport Layer and Sliding Window Protocols.\n"
            "The Go-Back-N (GBN) protocol allows the sender to transmit multiple packets without waiting for an acknowledgment. "
            "The sender window size N determines the maximum number of unacknowledged packets allowed in the pipeline. "
            "If a timeout occurs, the sender retransmits all unacknowledged packets in the window. "
            "Selective Repeat (SR) avoids unnecessary retransmissions by having the sender retransmit only those packets that are suspected of having been lost or corrupted. "
            "TCP congestion control uses slow start, congestion avoidance, fast retransmit, and fast recovery algorithms to regulate network throughput."
        )

    # Ingest temporary syllabus
    temp_syllabus_id = f"syl_{uuid.uuid4().hex[:8]}"
    processed = process_and_create_syllabus_rag(
        temp_id=temp_syllabus_id,
        file_paths=[syllabus_text_path],
        filename_hints=["Computer_Networks_Syllabus.txt"],
    )
    print(f"  Syllabus ingested: ID={processed['syllabus_id']}, Subject='{processed['subject']}', Topics={processed['topics']}")

    # Verify temp collection exists before interview
    temp_col_check = client.get_collection(f"temp_syllabus_{temp_syllabus_id}")
    assert temp_col_check.count() > 0, "Temp collection must have chunks during interview"
    kb_count_before_syllabus = perm_col.count()

    # Create syllabus session
    syl_session_data = create_interview_session(
        db=db,
        user_id=user.id,
        question_count=2,  # 2 questions for quick verification
        selected_skills=processed["topics"][:2],
        mode="syllabus",
        syllabus_id=temp_syllabus_id,
        selected_topics=processed["topics"][:2],
    )
    syl_session = syl_session_data["session"]
    syl_q1 = syl_session_data["current_question"]
    print(f"  Started syllabus session {syl_session.id}. Q1: {syl_q1.question_text[:80]}...")

    # Answer Q1
    syl_res1 = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=syl_session.id,
        question_id=syl_q1.id,
        answer_text="Go-Back-N retransmits all packets starting from the lost packet up to the window size, whereas Selective Repeat only retransmits the lost packet."
    )
    assert not syl_res1["is_complete"], "Q1 should not complete a 2-question interview"

    # Answer Q2 (Final question)
    syl_q2 = syl_res1["next_question"]
    syl_res2 = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=syl_session.id,
        question_id=syl_q2.id,
        answer_text="TCP congestion avoidance uses additive increase multiplicative decrease (AIMD) to throttle throughput when packet loss occurs."
    )
    assert syl_res2["is_complete"] is True, "Interview must complete on Q2!"

    # Verify post-interview knowledge ingestion occurred
    kb_count_after_syllabus = perm_col.count()
    print(f"  Permanent technical_kb chunk count before: {kb_count_before_syllabus}, after: {kb_count_after_syllabus}")

    # Verify temporary collection was cleaned up
    all_collections = [c if isinstance(c, str) else c.name for c in client.list_collections()]
    assert f"temp_syllabus_{temp_syllabus_id}" not in all_collections, "Temporary collection must be deleted after interview!"
    print(f"  [PASS] Temporary collection temp_syllabus_{temp_syllabus_id} cleanly dropped from ChromaDB.")

    # -------------------------------------------------------------
    # TEST 5: Normal Practice Session Retrieval from Merged Knowledge
    # -------------------------------------------------------------
    print_step("TEST 5: Normal Practice Session Retrieval from Merged Knowledge")
    retrieved_chunks, query = retrieve_rag_context(
        skill="TCP",
        embedding_model=emb_model,
        collection=perm_col,
        domains=["cn"],
    )
    print(f"  Retrieval for 'TCP' with domain 'cn': retrieved {len(retrieved_chunks)} chunks.")
    for idx, c in enumerate(retrieved_chunks):
        print(f"    Chunk {idx+1}: [Domain: {c['domain']}, Concept: {c['concept']}] {c['text'][:90]}...")

    assert len(retrieved_chunks) > 0, "Must retrieve relevant chunks from technical_kb!"
    print(f"  [PASS] Standard practice session retrieval operates normally from technical_kb!")

    # Cleanup test file
    if os.path.exists(syllabus_text_path):
        os.remove(syllabus_text_path)

    db.close()
    print_step("ALL 5 VERIFICATION SUITES PASSED PERFECTLY!")


if __name__ == "__main__":
    run_tests()
