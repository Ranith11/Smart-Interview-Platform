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

from app.config import CHROMA_DB_DIR
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
            max_tokens=400,
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

    ids = [f"temp_{temp_id}_{i}" for i in range(len(all_chunks))]
    metadatas = [{"domain": subject, "source": hint, "chunk_index": i} for i in range(len(all_chunks))]

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            documents=all_chunks[i:i + batch_size],
        )

    stage_timings["chroma_creation_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    stage_timings["total_ms"] = round((time.perf_counter() - total_start) * 1000, 1)

    return {
        "syllabus_id": temp_id,
        "subject": subject,
        "topics": topics,
        "chunks_count": len(all_chunks),
        "metrics": stage_timings,
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
