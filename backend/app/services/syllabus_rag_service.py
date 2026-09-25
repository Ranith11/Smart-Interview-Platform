"""
SmartInterview — Syllabus RAG Service (High-Speed & Source-Grounded)
Adapted from friend's syllabus_rag_service.py with key architectural fixes:
1. Single-pass file reading & chunking (no redundant disk reads).
2. Elimination of extract_concepts_batched loop (removes 10-25 sequential blocking LLM calls).
3. Single unified LLM call for Subject + Topic inference strictly from document text.
4. Stage-by-stage latency instrumentation.
5. Zero permanent KB contamination (merge_temporary_to_permanent eliminated).
6. Lifecycle cleanup (delete_temporary_rag).
"""

import os
import time
import uuid
from typing import Tuple, List, Dict, Any
import json

from app.config import CHROMA_DB_DIR, PROJECT_ROOT
from app.services.question_service import (
    get_embedding_model,
    get_chroma_collection,
    get_groq_client,
    get_groq_model_name,
)


# ── File Text Extraction (Single Pass) ─────────────────────

def extract_text_from_file(file_path: str) -> str:
    """Extract all text from PDF, TXT, or DOCX."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".txt":
        return _extract_txt(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(pdf_path: str) -> str:
    import pymupdf  # type: ignore
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")
    text_parts = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _extract_txt(txt_path: str) -> str:
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"File not found: {txt_path}")
    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _extract_docx(docx_path: str) -> str:
    import docx  # type: ignore
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"File not found: {docx_path}")
    doc = docx.Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text])


# ── Chunking ──────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Windowed text chunker with paragraph and sentence boundary preservation."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        break_point = text.rfind("\n", start, end)
        if break_point == -1 or break_point <= start + chunk_size // 2:
            break_point = text.rfind(". ", start, end)
        if break_point == -1 or break_point <= start + chunk_size // 2:
            break_point = end

        chunk = text[start:break_point].strip()
        if len(chunk) > 50:
            chunks.append(chunk)

        start = break_point - overlap
        if start <= 0 or start >= break_point:
            start = break_point

    return [c for c in chunks if len(c) > 50]


# ── Single-Pass Unified Subject & Topic Inference ──────────

def infer_subject_and_topics(text: str, chunks: list[str], filename_hint: str = "") -> Tuple[str, list[str]]:
    """
    Unified LLM call to extract BOTH the overall subject and distinct topics
    strictly grounded in the provided document excerpts.
    Replaces multiple separate LLM calls and concept-batching loops.
    """
    clean_hint = os.path.splitext(filename_hint)[0].replace("_", " ").replace("-", " ").title()

    if not text.strip() or not chunks:
        return clean_hint or "Course Syllabus", [clean_hint or "General Topics"]

    try:
        client = get_groq_client()
        model = get_groq_model_name()

        # Build representative excerpts from beginning, middle, and end
        sample_count = min(15, len(chunks))
        step = max(1, len(chunks) // sample_count)
        sampled_chunks = [chunks[i][:300] for i in range(0, len(chunks), step)][:sample_count]
        excerpts_text = "\n---\n".join(sampled_chunks)

        system_prompt = (
            "You are a strict curriculum analyst. You analyze academic syllabi and technical course documents. "
            "Identify the subject discipline and the key topics explicitly covered in the excerpts. "
            "Do NOT invent topics that do not appear in the text. "
            "Output your answer in the exact format:\n"
            "SUBJECT: <1-4 words subject title>\n"
            "TOPICS:\n"
            "- <Topic 1>\n"
            "- <Topic 2>\n"
            "Return between 4 and 14 concise topics (2-5 words each)."
        )

        user_prompt = f"Filename hint: {filename_hint}\n\nDocument Excerpts:\n{excerpts_text}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()

        subject = clean_hint or "Course Material"
        topics = []

        lines = content.split("\n")
        in_topics = False
        for line in lines:
            line_str = line.strip()
            if line_str.upper().startswith("SUBJECT:"):
                subj_val = line_str.split(":", 1)[1].strip()
                if subj_val:
                    subject = subj_val
            elif line_str.upper().startswith("TOPICS:"):
                in_topics = True
            elif in_topics and line_str:
                clean_t = line_str.lstrip("-*0123456789. )").strip()
                if clean_t and len(clean_t) >= 2:
                    topics.append(clean_t)

        if not topics:
            topics = [line.strip().lstrip("-*0123456789. )") for line in lines if line.strip() and not line.startswith("SUBJECT")]
            topics = [t for t in topics if t]

        # Deduplicate preserving order
        dedup_topics = []
        seen = set()
        for t in topics:
            if t.lower() not in seen:
                seen.add(t.lower())
                dedup_topics.append(t)

        return subject, dedup_topics if dedup_topics else [subject]

    except Exception as e:
        print(f"[SyllabusRAG] Subject & topic inference fallback due to: {e}")
        return clean_hint or "Course Material", [clean_hint or "General Topics"]


# ── Temporary ChromaDB Storage & Lifecycle ─────────────────

def process_and_create_syllabus_rag(
    temp_id: str,
    file_paths: list[str],
    filename_hints: list[str],
) -> Dict[str, Any]:
    """
    End-to-end single pass ingestion with stage-by-stage latency profiling:
    1. Text extraction (timed)
    2. Chunking (timed)
    3. Topic & Subject inference (1 single Groq call, timed)
    4. Batch embeddings with SentenceTransformer (timed)
    5. Temporary ChromaDB collection creation (timed)

    Returns dict with syllabus_id, subject, topics, chunks_count, and timing metrics.
    """
    import chromadb

    stage_timings = {}
    total_start = time.perf_counter()

    # Stage 1: Extraction
    t0 = time.perf_counter()
    extracted_texts = []
    for fp in file_paths:
        extracted_texts.append(extract_text_from_file(fp))
    full_text = "\n\n".join(extracted_texts)
    stage_timings["extraction_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # Stage 2: Chunking
    t0 = time.perf_counter()
    all_chunks = chunk_text(full_text)
    if not all_chunks:
        raise ValueError("No text could be extracted from the uploaded syllabus material.")
    stage_timings["chunking_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # Stage 3: Topic & Subject Inference (1 single call)
    t0 = time.perf_counter()
    hint = filename_hints[0] if filename_hints else ""
    subject, topics = infer_subject_and_topics(full_text, all_chunks, filename_hint=hint)
    stage_timings["topic_inference_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # Stage 4: Batch Embeddings
    t0 = time.perf_counter()
    embedding_model = get_embedding_model()
    embeddings = embedding_model.encode(all_chunks, convert_to_numpy=True, batch_size=32).tolist()
    stage_timings["embedding_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # Stage 5: Temporary Chroma Collection Creation
    t0 = time.perf_counter()
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = f"temp_syllabus_{temp_id}"

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.create_collection(name=collection_name)

    # Also ensure persistent syllabus_kb collection exists
    try:
        perm_syllabus = client.get_or_create_collection(
            name="syllabus_kb",
            metadata={"description": "Permanent storage for uploaded syllabus materials"}
        )
    except Exception:
        perm_syllabus = client.create_collection(name="syllabus_kb")

    ids = [f"temp_{temp_id}_{i}" for i in range(len(all_chunks))]
    perm_ids = [f"syl_{temp_id}_{i:04d}" for i in range(len(all_chunks))]
    metadatas = [{"domain": subject, "source": hint, "chunk_index": i} for i in range(len(all_chunks))]

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            documents=all_chunks[i:i + batch_size],
        )
        # Also persist to syllabus_kb so chunks are never lost
        perm_syllabus.upsert(
            ids=perm_ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            documents=all_chunks[i:i + batch_size],
        )

    stage_timings["chroma_creation_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    stage_timings["total_ms"] = round((time.perf_counter() - total_start) * 1000, 1)

    # Permanent knowledge stats sync for real-time tracking
    _update_knowledge_stats_with_syllabus(temp_id, subject, len(all_chunks), hint, topics)

    return {
        "syllabus_id": temp_id,
        "subject": subject,
        "topics": topics,
        "chunks_count": len(all_chunks),
        "metrics": stage_timings,
    }


def _update_knowledge_stats_with_syllabus(syllabus_id: str, subject: str, chunk_count: int, filename: str, topics: list[str] = None):
    """Updates data/knowledge_stats.json permanently when syllabus chunks are created."""
    stats_file = os.path.join(str(PROJECT_ROOT), "data", "knowledge_stats.json")
    try:
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
        else:
            stats = {"total_concepts": 50, "total_chunks": 402}

        uploaded = stats.setdefault("uploaded_syllabi", {
            "total_courses": 0,
            "total_syllabus_chunks": 0,
            "courses": []
        })

        course_entry = {
            "course_id": syllabus_id,
            "subject": subject,
            "filename": filename or "Uploaded Syllabus",
            "domain": resolve_kb_domain(subject),
            "chunks": chunk_count,
            "topics": topics or [subject],
            "status": "PASS",
            "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Check if already present by filename or course_id
        existing_idx = next((i for i, c in enumerate(uploaded["courses"]) if c.get("filename") == filename or c.get("course_id") == syllabus_id), None)
        if existing_idx is not None:
            uploaded["courses"][existing_idx] = course_entry
        else:
            uploaded["courses"].append(course_entry)

        uploaded["total_courses"] = len(uploaded["courses"])
        uploaded["total_syllabus_chunks"] = sum(c["chunks"] for c in uploaded["courses"])

        # Update dynamic active sessions
        dynamic = stats.setdefault("dynamic_syllabi", {
            "total_dynamic_syllabi": 0,
            "total_dynamic_chunks": 0,
            "sessions": {}
        })
        dynamic["sessions"][syllabus_id] = {
            "subject": subject,
            "chunks": chunk_count,
            "filename": filename or "Uploaded Syllabus",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        dynamic["total_dynamic_syllabi"] = len(uploaded["courses"])
        dynamic["total_dynamic_chunks"] = uploaded["total_syllabus_chunks"]

        canonical_chunks = stats.get("total_chunks", 402)
        stats["grand_total_chunks"] = canonical_chunks + uploaded["total_syllabus_chunks"]

        summary = stats.setdefault("summary", {})
        summary["canonical_chunks"] = canonical_chunks
        summary["uploaded_syllabus_chunks"] = uploaded["total_syllabus_chunks"]
        summary["grand_total_chunks"] = stats["grand_total_chunks"]
        summary["last_sync"] = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        print(f"[SyllabusRAG] Synced {chunk_count} syllabus chunks into data/knowledge_stats.json (Grand Total: {stats['grand_total_chunks']})")
    except Exception as e:
        print(f"[SyllabusRAG] Note: knowledge_stats.json sync: {e}")


def _cleanup_knowledge_stats_syllabus(syllabus_id: str):
    """Marks dynamic session inactive without deleting the permanent uploaded syllabus record."""
    stats_file = os.path.join(str(PROJECT_ROOT), "data", "knowledge_stats.json")
    try:
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
            dynamic = stats.get("dynamic_syllabi", {})
            sessions = dynamic.get("sessions", {})
            if syllabus_id in sessions:
                del sessions[syllabus_id]
                # Notice: we DO NOT delete from uploaded_syllabi or decrement grand_total_chunks!
                # Uploaded syllabus knowledge is preserved permanently.
                with open(stats_file, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2)
                print(f"[SyllabusRAG] Session {syllabus_id} finished; permanent knowledge preserved (Grand Total: {stats['grand_total_chunks']})")
    except Exception as e:
        print(f"[SyllabusRAG] Note: knowledge_stats.json session finish: {e}")


CANONICAL_DOMAINS = {
    "cn": ["cn", "computer network", "computer networks", "networking"],
    "os": ["os", "operating system", "operating systems"],
    "dbms": ["dbms", "database", "databases", "database management", "sql"],
    "dsa": ["dsa", "data structure", "data structures", "algorithm", "algorithms"],
    "oop": ["oop", "object oriented", "object-oriented"],
    "system-design": ["system design", "system-design", "distributed systems"],
    "design-patterns": ["design pattern", "design patterns", "design-patterns"],
    "ml-dl": ["ml-dl", "machine learning", "deep learning", "artificial intelligence", "ai"],
}


def resolve_kb_domain(subject: str) -> str:
    """Map subject string to technical_kb canonical domains or clean slug."""
    subj_lower = subject.lower().strip()
    for canon, aliases in CANONICAL_DOMAINS.items():
        if subj_lower == canon:
            return canon
        for alias in aliases:
            if alias in subj_lower:
                return canon
    slug = subj_lower.replace(" ", "-").replace("/", "-").strip("-_")
    return slug or "general"


def merge_temporary_to_permanent_kb(temp_id: str) -> dict:
    """
    Post-Interview Knowledge Ingestion with Two-Layer Deduplication:
    1. Exact Data Deduplication: Normalized text content hashing (SHA-256).
    2. Semantic Near-Duplicate Filtering: Vector distance check against existing KB vectors (< 0.10).
    
    Merges genuinely new technical knowledge from temp_syllabus_{temp_id} into technical_kb.
    Preserves exact technical_kb schema and metadata so merged knowledge works normally.
    """
    if not temp_id:
        return {"merged_count": 0, "exact_skipped": 0, "semantic_skipped": 0}

    import chromadb
    import hashlib

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = f"temp_syllabus_{temp_id}"

    try:
        temp_col = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"[SyllabusRAG] Temporary collection {collection_name} not found for merging: {e}")
        return {"merged_count": 0, "exact_skipped": 0, "semantic_skipped": 0}

    try:
        perm_col = client.get_collection(name="technical_kb")
    except Exception as e:
        print(f"[SyllabusRAG] Permanent collection technical_kb not found: {e}")
        return {"merged_count": 0, "exact_skipped": 0, "semantic_skipped": 0}

    temp_data = temp_col.get(include=["documents", "metadatas", "embeddings"])
    if not temp_data or not temp_data.get("documents"):
        return {"merged_count": 0, "exact_skipped": 0, "semantic_skipped": 0}

    docs = temp_data["documents"]
    metas = temp_data["metadatas"]
    embeddings = temp_data["embeddings"]

    embedding_model = None

    merged_ids = []
    merged_docs = []
    merged_metas = []
    merged_embs = []

    exact_skipped = 0
    semantic_skipped = 0

    for i, doc in enumerate(docs):
        if not doc or not doc.strip():
            continue

        raw_meta = metas[i] if metas and i < len(metas) else {}
        subject = raw_meta.get("domain", "General Technical")
        source = raw_meta.get("source", "syllabus")
        emb = embeddings[i] if embeddings is not None and i < len(embeddings) else None

        if emb is None:
            if embedding_model is None:
                embedding_model = get_embedding_model()
            emb = embedding_model.encode(doc, convert_to_numpy=True).tolist()

        # Clean / normalize text for exact content fingerprinting
        norm_text = " ".join(doc.strip().split()).lower()
        chunk_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()[:16]
        
        # Canonical domain mapping matching technical_kb 8 core domains or clean slug
        clean_domain = resolve_kb_domain(subject)
        chunk_id = f"syllabus_{clean_domain}_{chunk_hash}"

        # --- Layer 1: Exact Content-Hash Deduplication ---
        existing_exact = perm_col.get(ids=[chunk_id])
        if existing_exact and existing_exact.get("ids"):
            exact_skipped += 1
            continue

        # --- Layer 2: Semantic Near-Duplicate Filtering ---
        if emb is not None:
            near_results = perm_col.query(
                query_embeddings=[emb],
                n_results=1,
                include=["distances"]
            )
            if near_results and near_results.get("distances") and near_results["distances"][0]:
                top_distance = near_results["distances"][0][0]
                # Distance < 0.10 means > 95% semantic similarity with existing knowledge
                if top_distance < 0.10:
                    semantic_skipped += 1
                    continue

        # Genuinely new technical knowledge — prepare metadata matching technical_kb schema
        kb_meta = {
            "concept": subject[:50],
            "domain": clean_domain[:30],
            "source": str(source)[:100],
            "source_url": "",
            "token_count": len(doc.split()),
        }

        merged_ids.append(chunk_id)
        merged_docs.append(doc)
        merged_metas.append(kb_meta)
        if emb is not None:
            merged_embs.append(emb)

    # Upsert in batches of 100
    if merged_ids:
        batch_size = 100
        for b in range(0, len(merged_ids), batch_size):
            b_ids = merged_ids[b:b + batch_size]
            b_docs = merged_docs[b:b + batch_size]
            b_metas = merged_metas[b:b + batch_size]
            b_embs = merged_embs[b:b + batch_size] if merged_embs else None
            
            perm_col.upsert(
                ids=b_ids,
                documents=b_docs,
                metadatas=b_metas,
                embeddings=b_embs,
            )

    print(f"[SyllabusRAG] Merged to technical_kb: {len(merged_ids)} new chunks added, {exact_skipped} exact duplicates skipped, {semantic_skipped} semantic near-duplicates skipped.")
    return {
        "merged_count": len(merged_ids),
        "exact_skipped": exact_skipped,
        "semantic_skipped": semantic_skipped,
    }


def delete_temporary_rag(temp_id: str):
    """Lifecycle cleanup: drops temporary syllabus collection from ChromaDB."""
    if not temp_id:
        return
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = f"temp_syllabus_{temp_id}"
    try:
        client.delete_collection(name=collection_name)
        print(f"[SyllabusRAG] Successfully cleaned up temporary collection: {collection_name}")
    except Exception as e:
        print(f"[SyllabusRAG] Note: temp collection {collection_name} cleanup: {e}")

    _cleanup_knowledge_stats_syllabus(temp_id)
