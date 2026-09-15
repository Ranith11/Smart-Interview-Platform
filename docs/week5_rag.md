# Week 5: Retrieval-Augmented Generation (RAG)

## 1. Objective
Implement the foundational RAG vector database and retrieval pipeline. This involves converting the 402 validated knowledge chunks from Week 4 into dense semantic embeddings and storing them in a persistent ChromaDB instance for later semantic search and question generation.

## 2. Input Data
- **Source**: `data/processed/`
- **Scope**: 8 domains (DSA, DBMS, OS, OOP, CN, System Design, Design Patterns, ML-DL)
- **Total Chunks**: 402

## 3. Embedding Model
- **Model Name**: `all-MiniLM-L6-v2` (via `sentence-transformers`)
- **Dimensions**: 384
- **Why selected**: `all-MiniLM-L6-v2` offers an excellent balance between embedding quality and performance. It is extremely fast on CPU-only environments (ideal for local development or student laptops) while still capturing highly accurate semantic meaning for technical concepts.

## 4. Vector Database
- **Database**: ChromaDB
- **Storage**: Persistent storage at `chroma_db/`
- **Collection Name**: `technical_kb`
- **Document ID Strategy**: Using the pre-generated, globally unique `chunk_id` (e.g., `dsa_array_001`). This ensures idempotency; running the ingestion script multiple times updates existing entries rather than duplicating them.

## 5. Metadata Schema
Each stored vector carries the following metadata directly ingested from the Week 4 JSON structure:
- `domain`: Broad subject area (e.g., `dbms`)
- `concept`: Specific topic (e.g., `indexing`)
- `source`: Origin site (e.g., `geeksforgeeks`)
- `source_url`: Link to original content
- `token_count`: Length of the chunk

This allows the retrieval engine to execute highly efficient metadata-filtered queries (e.g., `domain="dsa"`).

## 6. Ingestion Process
The `scripts/ingest_vector_db.py` script:
1. Recursively loads all `*_chunks.json` files.
2. Validates metadata requirements.
3. Generates 384-dimensional embeddings for all valid texts.
4. Uses ChromaDB's `upsert` functionality to insert/update the collection.

## 7. Retrieval Process
The `scripts/test_retrieval.py` script allows natural language querying. It encodes the user's query using the exact same `all-MiniLM-L6-v2` model and calculates similarity distances across the `technical_kb` collection, returning the top-k most relevant chunks.

## 8. Evaluation
A manually curated evaluation dataset (`data/evaluation/retrieval_queries.json`) containing 33 technical queries covering all 8 domains was created.

The `scripts/evaluate_retrieval.py` script tests the vector database against these queries.

### Evaluation Metrics
- **Total Queries**: 33
- **Hit@1**: 96.97%
- **Hit@3**: 100.00%
- **Hit@5 (Recall@5)**: 100.00%
- **MRR**: 0.9798

## 9. Next Step: Week 6
With the RAG pipeline functional, the next phase will introduce Large Language Models (LLMs) to generate dynamic interview questions based on the retrieved context, applying Bloom's Taxonomy for varying difficulty levels.
