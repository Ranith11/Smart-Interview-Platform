# Week 9 — Answer Evaluation Engine

## Overview

Week 9 adds automated answer evaluation using LLM-based analysis and semantic similarity. Each candidate answer is evaluated across five dimensions and produces actionable feedback.

## Architecture

File: `backend/app/services/evaluation_service.py`

### Evaluation Pipeline

```
Question + RAG Context
       ↓
Expected Concepts / Reference Representation
       ↓
Candidate Answer
       ↓
┌─────────────────────┐   ┌──────────────────────┐
│  LLM Evaluation     │   │  Semantic Similarity  │
│  (Groq)             │   │  (SentenceTransformer)│
│  - Technical score   │   │  - Cosine similarity  │
│  - Completeness     │   │  - Reference vs answer│
│  - Relevance        │   │                      │
│  - Concept coverage │   │                      │
│  - Feedback         │   │                      │
│  - Strengths/Weakn. │   │                      │
│  - Expected/Found   │   │                      │
└─────────────────────┘   └──────────────────────┘
       ↓                         ↓
       └──────────┬──────────────┘
                  ↓
         Weighted Overall Score
```

## Scoring Formula

```
overall = 0.30 × technical
        + 0.20 × completeness
        + 0.20 × relevance
        + 0.15 × semantic_similarity
        + 0.15 × concept_coverage
```

All individual scores are clamped to **0–100**.

This formula is the project's defined scoring framework. It is NOT claimed to be scientifically validated.

### Score Dimensions

| Dimension | Weight | Source | Description |
|-----------|--------|--------|-------------|
| Technical Correctness | 30% | LLM | Is the answer technically correct? |
| Completeness | 20% | LLM | How thoroughly does it cover the topic? |
| Relevance | 20% | LLM | How relevant is it to the specific question? |
| Semantic Similarity | 15% | SBERT | Semantic closeness to reference information |
| Concept Coverage | 15% | LLM + calculation | How many expected concepts are present? |

## Semantic Similarity

**Semantic similarity measures semantic closeness between the candidate response and the reference information. It does NOT by itself establish technical correctness.**

Technical correctness primarily comes from the LLM evaluation and concept coverage signals.

Implementation:
- Reference = question text + RAG knowledge chunks (up to 1500 chars)
- Candidate answer is encoded separately
- Cosine similarity between embeddings
- Nonlinear scaling: similarity range [0.1, 0.7] → score range [0, 100]
- Reuses the existing `SentenceTransformer` (`all-MiniLM-L6-v2`) singleton

## Concept Extraction

Expected concepts are extracted by the **LLM** as part of the structured evaluation response.

Requirements for concept extraction:
- Concepts represent meaningful technical ideas required to answer the question
- Generic or obvious words are not concepts
- LLM returns structured JSON with `expected_concepts` and `found_concepts` arrays
- Results are validated (deduplicated, cleaned, truncated)
- If parsing fails, safe defaults are used

Example for "What is database normalization and why is it useful?":
- Expected: `["normalization", "data redundancy", "update anomalies", "decomposition", "normal forms"]`
- Found (from answer): `["normalization", "data redundancy", "normal forms"]`
- Coverage: 3/5 = 60%

Concept coverage score is averaged between LLM-reported score and the calculated ratio for robustness.

## LLM Evaluation

- Uses existing Groq client singleton
- Temperature: 0.3 (lower than generation for consistency)
- Max tokens: 1024
- Prompt requires JSON-only output with exact field names
- Response parsing handles:
  - Markdown code blocks around JSON
  - JSON extraction from mixed text
  - Field validation and clamping
  - Safe defaults on any parsing failure
- **Never crashes FastAPI** — all failures return safe default scores

## Prompt Templates

File: `prompts/evaluation_prompts.json`

Contains:
- `evaluation_system_prompt` — instructs LLM to return exact JSON schema
- `evaluation_user_template` — template with placeholders for question, answer, difficulty, bloom level, reference context

## Data Storage

Table: `answer_evaluations`

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Auto-increment |
| answer_id | INT FK UNIQUE | Links to answers.id |
| question_id | INT FK | Links to interview_questions.id |
| technical_score | INT | 0-100 |
| completeness_score | INT | 0-100 |
| relevance_score | INT | 0-100 |
| semantic_similarity_score | INT | 0-100 |
| concept_coverage_score | INT | 0-100 |
| overall_score | INT | 0-100 |
| feedback | TEXT | Constructive feedback |
| strengths | JSON | List of strength strings |
| weaknesses | JSON | List of weakness strings |
| concepts_expected | JSON | Expected concept list |
| concepts_found | JSON | Found concept list |
| evaluated_at | DATETIME | Timestamp |

One answer can have at most one evaluation (UNIQUE constraint on `answer_id`).

## Limitations

- Semantic similarity is a heuristic signal, not a measure of technical correctness
- LLM evaluation quality depends on the Groq model and prompt design
- Concept extraction is LLM-dependent and may miss subtle concepts
- Scores may vary slightly between identical evaluations due to LLM temperature > 0
- No human calibration or validation of score thresholds

## Voice/STT Status

**Voice-based interview and Speech-to-Text integration are deferred to Week 11.**
