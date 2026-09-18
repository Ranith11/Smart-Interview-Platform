import os
import uuid
import numpy as np

from app.config import CHROMA_DB_DIR
from app.services.question_service import get_embedding_model, get_chroma_collection, get_groq_client, get_groq_model_name, normalize_domain


def extract_text_from_file(file_path: str) -> str:
    """Extract text from a PDF or TXT file."""
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
    """Extract all text from a PDF using PyMuPDF."""
    import pymupdf  # type: ignore
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")
    text = ""
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text


def _extract_txt(txt_path: str) -> str:
    """Read a plain text file."""
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"File not found: {txt_path}")
    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _extract_docx(docx_path: str) -> str:
    """Read a Microsoft Word (.docx) file."""
    import docx
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"File not found: {docx_path}")
    doc = docx.Document(docx_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


# Keep for backward-compatibility
def extract_text_from_pdf(pdf_path: str) -> str:
    return _extract_pdf(pdf_path)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """A basic text chunker."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        break_point = text.rfind("\n", start, end)
        if break_point == -1 or break_point <= start + chunk_size // 2:
            break_point = text.rfind(". ", start, end)
        if break_point == -1 or break_point <= start + chunk_size // 2:
            break_point = end
        chunks.append(text[start:break_point].strip())
        start = break_point - overlap
        if start <= 0 or start == break_point:
            start = break_point
    return [c for c in chunks if len(c) > 50]


def extract_concepts_batched(chunks: list[str], syllabus_subject: str) -> list[str]:
    """Use LLM to briefly identify the core concept/topic for a batch of chunks."""
    if not chunks:
        return []

    try:
        client = get_groq_client()
        model = get_groq_model_name()

        batch_size = 10
        all_concepts = []

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            prompt_text = "\n\n".join(
                [f"Snippet {j + 1}:\n{c[:300]}..." for j, c in enumerate(batch_chunks)]
            )

            system_prompt = (
                "You are a technical concept extractor. For each snippet provided, "
                "reply with exactly ONE line containing a 1-3 word technical concept "
                "representing its core topic. Output exactly as many lines as there are snippets."
            )
            user_prompt = (
                f"Syllabus Subject: {syllabus_subject}\n\nSnippets:\n{prompt_text}\n\nConcepts:"
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
            )

            lines = response.choices[0].message.content.strip().split("\n")
            lines = [
                line.strip().lstrip("0123456789.- ").title()
                for line in lines
                if line.strip()
            ]

            while len(lines) < len(batch_chunks):
                lines.append(syllabus_subject)
            lines = lines[: len(batch_chunks)]
            all_concepts.extend(lines)

        return all_concepts
    except Exception as e:
        print(f"Batch concept extraction failed: {e}")
        return [syllabus_subject] * len(chunks)


def extract_topics_from_chunks(chunks: list[str], subject: str) -> list[str]:
    """
    Ask the LLM to identify the high-level unique topics present in the material.
    Returns a deduplicated list of topic names suitable for user selection.
    """
    if not chunks:
        return []

    try:
        client = get_groq_client()
        model = get_groq_model_name()

        # Combine representative snippets (first 300 chars of every chunk, up to 40 chunks)
        sample_count = min(40, len(chunks))
        sample_text = "\n---\n".join(c[:300] for c in chunks[:sample_count])

        system_prompt = (
            "You are a curriculum analyst. Given excerpts from a technical syllabus or reference material, "
            "identify and list the distinct high-level topics covered. "
            "Return ONLY a plain list, one topic per line, no bullets, no numbering, no extra text. "
            "Each topic should be 2-5 words. Return between 4 and 16 topics."
        )
        user_prompt = f"Subject hint: {subject}\n\nExcerpts:\n{sample_text}\n\nTopics:"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )

        lines = response.choices[0].message.content.strip().split("\n")
        topics = []
        seen = set()
        for line in lines:
            t = line.strip().lstrip("0123456789.-) ").strip()
            if t and t.lower() not in seen:
                seen.add(t.lower())
                topics.append(t)

        return topics if topics else [subject]
    except Exception as e:
        print(f"Topic extraction failed: {e}")
        return [subject]


def infer_subject_from_text(text: str, filename_hint: str = "") -> str:
    """
    Ask the LLM to infer the overall subject/discipline from the content.
    Falls back to a cleaned-up version of the filename hint.
    """
    try:
        client = get_groq_client()
        model = get_groq_model_name()

        sample = text[:2000]
        prompt = (
            f"What is the primary academic or technical subject of this document? "
            f"Reply with only 1-4 words (e.g. 'Operating Systems', 'Database Management', 'Machine Learning'). "
            f"Filename hint: {filename_hint}\n\nContent:\n{sample}"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=20,
        )
        return response.choices[0].message.content.strip().strip('"').strip("'")
    except Exception:
        # Fall back to filename without extension
        name = os.path.splitext(filename_hint)[0]
        return name.replace("_", " ").replace("-", " ").title() or "Technical Material"


def create_temporary_rag_from_chunks(temp_id: str, all_chunks: list[str], source_labels: list[str], subject: str) -> str:
    """
    Given a list of chunks and their source labels, embed them and store them in a 
    temporary ChromaDB collection named temp_syllabus_<temp_id>.
    """
    import chromadb

    if not all_chunks:
        raise ValueError("No text provided to create temporary RAG.")

    embedding_model = get_embedding_model()
    embeddings = embedding_model.encode(all_chunks, convert_to_numpy=True).tolist()

    concepts = extract_concepts_batched(all_chunks, subject)

    metadatas = []
    ids = []
    documents = []

    normalized_domain = normalize_domain(subject)

    for i, chunk in enumerate(all_chunks):
        concept = concepts[i] if i < len(concepts) else subject
        metadatas.append({
            "domain": normalized_domain,
            "concept": concept,
            "source": source_labels[i],
            "source_url": source_labels[i],
        })
        ids.append(f"temp_{temp_id}_{i}")
        documents.append(chunk)

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = f"temp_syllabus_{temp_id}"

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.create_collection(name=collection_name)

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            documents=documents[i:i + batch_size],
        )

    return collection_name


def create_temporary_rag_from_files(temp_id: str, file_paths: list[str], subject: str) -> str:
    """
    Legacy compatible: Given a list of file paths (PDF, TXT, DOCX), extract text, chunk, 
    and store in a temporary ChromaDB collection.
    """
    all_chunks: list[str] = []
    source_labels: list[str] = []

    for fp in file_paths:
        try:
            text = extract_text_from_file(fp)
            file_chunks = chunk_text(text)
            all_chunks.extend(file_chunks)
            source_labels.extend([os.path.basename(fp)] * len(file_chunks))
        except Exception as e:
            print(f"[SyllabusRAG] Failed to extract {fp}: {e}")

    if not all_chunks:
        raise ValueError("No text could be extracted from the uploaded files.")

    return create_temporary_rag_from_chunks(temp_id, all_chunks, source_labels, subject)


# Legacy: kept so existing test scripts don't break.
def create_temporary_rag(session_id: int, syllabus_id: str):
    """
    LEGACY — reads the old syllabi.json catalog.
    New code should use create_temporary_rag_from_files().
    """
    import json

    syllabi_file = os.path.join("data", "syllabi.json")
    if not os.path.exists(syllabi_file):
        raise ValueError("syllabi.json not found")

    with open(syllabi_file, "r") as f:
        syllabi = json.load(f)

    syllabus = next((s for s in syllabi if s["id"] == syllabus_id), None)
    if not syllabus:
        raise ValueError(f"Syllabus {syllabus_id} not found in catalog")

    pdf_path = os.path.abspath(syllabus["pdf_path"])
    subject = syllabus["subject"]

    return create_temporary_rag_from_files(
        temp_id=str(session_id),
        file_paths=[pdf_path],
        subject=subject,
    )


def delete_temporary_rag(temp_id: str):
    """Delete the temporary ChromaDB collection for a given temp_id (str)."""
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = f"temp_syllabus_{temp_id}"
    try:
        client.delete_collection(name=collection_name)
        print(f"Deleted temporary collection: {collection_name}")
    except Exception as e:
        print(f"Failed to delete temp collection {collection_name}: {e}")


def cosine_similarity(v1, v2):
    """Compute cosine similarity between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def merge_temporary_to_permanent(temp_id: str):
    """
    Compare temporary syllabus concepts against permanent technical_kb.
    Add only genuinely new concepts. temp_id is a string (UUID or legacy int).
    """
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = f"temp_syllabus_{temp_id}"

    try:
        temp_collection = client.get_collection(name=collection_name)
    except Exception:
        print("Temporary collection not found for merge.")
        return

    perm_collection = get_chroma_collection()

    temp_data = temp_collection.get(include=["embeddings", "metadatas", "documents"])
    if not temp_data or not temp_data["ids"]:
        return

    added_count = 0
    ignored_count = 0

    for i, temp_id_item in enumerate(temp_data["ids"]):
        emb = temp_data["embeddings"][i]
        meta = temp_data["metadatas"][i]
        doc = temp_data["documents"][i]
        concept = meta.get("concept", "")

        results = perm_collection.query(
            query_embeddings=[emb],
            n_results=1,
            include=["embeddings", "distances", "metadatas"],
        )

        is_duplicate = False

        if (
            results
            and results["distances"]
            and len(results["distances"]) > 0
            and len(results["distances"][0]) > 0
        ):
            perm_emb = results["embeddings"][0][0]
            sim = cosine_similarity(emb, perm_emb)

            if sim > 0.85:
                is_duplicate = True
                print(
                    f"IGNORE Concept '{concept}': Match found in permanent KB (sim: {sim:.3f})"
                )

        if not is_duplicate:
            perm_id = str(uuid.uuid4())
            perm_collection.upsert(
                ids=[perm_id],
                embeddings=[emb],
                metadatas=[meta],
                documents=[doc],
            )
            added_count += 1
            print(f"ADD Concept '{concept}': Genuinely new concept added to permanent KB.")
        else:
            ignored_count += 1

    print(
        f"Merge Complete: Added {added_count} new concepts, Ignored {ignored_count} existing concepts."
    )
