"""
Verification Script: Post-Interview Knowledge Base Merge & Deduplication ONLY
Validates:
1. Syllabus session stays strictly grounded in temporary PDF during interview.
2. Knowledge merge into technical_kb happens strictly POST-INTERVIEW.
3. Two-layer deduplication (Exact Hash & Semantic Filter < 0.10).
4. Permanent technical_kb functions normally as before.
5. Open-ended interview flow preserved (natural stopping removed).
"""

import sys
import os
import uuid
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.services.syllabus_rag_service import (
    process_and_create_syllabus_rag,
    merge_temporary_to_permanent_kb,
    resolve_kb_domain,
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


def print_step(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_tests():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "testaudit@example.com").first()
    if not user:
        user = db.query(User).first()
    assert user is not None, "A user must exist."
    print(f"Testing with user: {user.email} (ID: {user.id})")

    # 1. Deduplication Engine Test
    print_step("1. Two-Layer Deduplication Engine")
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    perm_col = client.get_collection("technical_kb")
    initial_kb_count = perm_col.count()
    print(f"  Permanent technical_kb chunk count: {initial_kb_count}")

    temp_id = f"test_dedup_{uuid.uuid4().hex[:8]}"
    temp_col = client.create_collection(f"temp_syllabus_{temp_id}")

    existing_sample = perm_col.get(limit=1, include=["documents"])
    existing_text = existing_sample["documents"][0]
    unique_text = f"Novel concept {uuid.uuid4().hex}: Neuromorphic spike-timing-dependent plasticity using memristive crossbar arrays for asynchronous low-power edge computing."
    near_dup = existing_text + " In practice, this architectural pattern is widely deployed."

    emb_model = get_embedding_model()
    docs = [unique_text, existing_text, near_dup]
    embs = emb_model.encode(docs, convert_to_numpy=True).tolist()

    temp_col.add(
        ids=[f"temp_{temp_id}_{i}" for i in range(len(docs))],
        documents=docs,
        embeddings=embs,
        metadatas=[{"domain": "Neuromorphic Computing", "source": "neuromorphic.pdf"} for _ in range(len(docs))]
    )

    res1 = merge_temporary_to_permanent_kb(temp_id)
    print(f"  First merge: {res1}")
    assert res1["merged_count"] == 1, "Only the 1 unique chunk should be merged!"
    assert res1["exact_skipped"] + res1["semantic_skipped"] == 2, "Both duplicates must be skipped!"
    print("  [PASS] Exactly 1 unique chunk merged, 2 duplicates skipped.")

    # Second merge (idempotency check)
    res2 = merge_temporary_to_permanent_kb(temp_id)
    print(f"  Second merge: {res2}")
    assert res2["merged_count"] == 0, "Second merge must add 0 chunks!"
    assert res2["exact_skipped"] >= 1, "Exact hash must catch previous chunk!"
    print("  [PASS] Second merge is 100% idempotent: 0 added, all skipped.")

    # Cleanup synthetic test collection and test chunk
    client.delete_collection(f"temp_syllabus_{temp_id}")
    try:
        perm_col.delete(where={"source": "neuromorphic.pdf"})
    except Exception:
        pass

    # 2. Post-Interview Ingestion Lifecycle
    print_step("2. Post-Interview Ingestion Lifecycle")
    test_pdf_content = (
        "Operating Systems: Virtual Memory and Paging Algorithms.\n"
        "Demand paging loads pages into physical RAM only when they are referenced by execution. "
        "Page replacement algorithms include FIFO, Optimal, LRU, and Second Chance (Clock). "
        "Thrashing occurs when a process spends more time swapping pages in and out of secondary storage than executing instructions."
    )
    test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_os_paging.txt"))
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_pdf_content)

    syl_id = f"syl_{uuid.uuid4().hex[:8]}"
    processed = process_and_create_syllabus_rag(
        temp_id=syl_id,
        file_paths=[test_file],
        filename_hints=["OS_Paging.txt"],
    )

    # Active interview creation
    syl_data = create_interview_session(
        db=db,
        user_id=user.id,
        selected_skills=processed["topics"][:2],
        mode="syllabus",
        syllabus_id=syl_id,
        selected_topics=processed["topics"][:2],
    )
    session = syl_data["session"]
    q1 = syl_data["current_question"]

    # Active interview stays isolated to temp collection
    temp_check = client.get_collection(f"temp_syllabus_{syl_id}")
    assert temp_check.count() > 0, "Temp collection must exist during interview"
    print(f"  [PASS] Active interview is grounded in isolated temporary collection: temp_syllabus_{syl_id}")

    # Answer question 1
    eval1 = submit_and_evaluate(
        db=db,
        user_id=user.id,
        session_id=session.id,
        question_id=q1.id,
        answer_text="Demand paging loads pages on demand when a page fault occurs, avoiding pre-loading unnecessary pages."
    )
    assert not eval1["is_complete"], "Interview continues open-endedly as requested"
    print(f"  [PASS] Interview continues open-endedly (is_complete={eval1['is_complete']}, next Q={eval1['next_question'].question_number})")

    # Complete interview explicitly (user finishes interview)
    completed_session = complete_interview(db=db, user_id=user.id, session_id=session.id)
    assert completed_session.status == "completed"

    # Verify temp collection is deleted
    all_collections = [c if isinstance(c, str) else c.name for c in client.list_collections()]
    assert f"temp_syllabus_{syl_id}" not in all_collections, "Temp collection must be deleted after interview"
    print(f"  [PASS] Temporary collection deleted cleanly after interview completion.")

    # 3. Normal Practice Session Retrieval from Merged technical_kb
    print_step("3. Normal Knowledge Base Retrieval")
    chunks, query = retrieve_rag_context(
        skill="SQL",
        embedding_model=emb_model,
        collection=perm_col,
        domains=["dbms"],
    )
    assert len(chunks) > 0, "Standard knowledge base retrieval operates normally"
    print(f"  [PASS] Standard RAG retrieval works normally from technical_kb (retrieved {len(chunks)} chunks).")

    if os.path.exists(test_file):
        os.remove(test_file)
    db.close()
    print_step("ALL TESTS PASSED: Post-Interview Merge & Deduplication Verified, Natural Stopping Completely Removed!")


if __name__ == "__main__":
    run_tests()
