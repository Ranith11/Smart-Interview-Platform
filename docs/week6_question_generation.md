# Week 6: Resume-Driven Interview Question Generation

## 1. Objective

Week 6 implements a resume-driven, RAG-grounded interview question generation module.
The system parses a candidate's PDF resume, extracts skills and projects, performs semantic
retrieval against the existing ChromaDB knowledge base, and uses Groq LLM to generate
personalized technical interview questions.

## 2. Architecture

```
Resume PDF
    ↓
Resume Parsing (PyMuPDF — local, deterministic)
    ↓
Candidate Profile (skills, projects, experience, education)
    ↓
Resume-driven RAG Queries
    ↓
all-MiniLM-L6-v2 Embedding
    ↓
ChromaDB technical_kb (402 chunks, 8 domains, 50 concepts)
    ↓
Relevant Technical Context (deduplicated chunks)
    ↓
Prompt Engineering (system prompt + candidate + context + difficulty + type)
    ↓
Groq LLM (auto-detected best available model)
    ↓
Personalized Interview Questions
```

The system is NOT: `Resume → LLM → Questions`

It IS: `Resume → Profile → RAG Retrieval → Retrieved Context → LLM → Questions`

## 3. Resume Processing

### Script: `scripts/parse_resume.py`

**Library:** PyMuPDF (`pymupdf`)

**Processing:**
1. Opens PDF, extracts text from all pages
2. Normalizes whitespace
3. Detects sections via keyword pattern matching (Skills, Projects, Experience, Education)
4. Extracts structured data from each section
5. Falls back to keyword scanning if section detection fails

**Output:** Structured candidate profile dictionary:
- `raw_text`: Full extracted text
- `page_count`: Number of pages
- `skills`: List of technical skills
- `projects`: List of {name, description}
- `experience`: List of {role, description}
- `education`: List of education entries

**Standalone usage:**
**Standalone usage:**
```
python scripts\parse_resume.py data\resumes\sample_resume.pdf
```

## 4. RAG Integration

### Reused Infrastructure (Week 5)

| Component | Value |
|---|---|
| Vector database | ChromaDB |
| Collection | `technical_kb` |
| Documents | 402 |
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding dimension | 384 |
| Database path | `chroma_db/` |

### Retrieval Flow

1. **Project-First Retrieval:** Each project name, description, and technologies generate a semantic query:
   `"Technical concepts related to {project}, {description}, and technologies like {techs}"`
2. **Skill-Based Retrieval:** Each candidate skill generates a natural-language query:
   `"Technical interview concepts related to {skill}"`
3. Queries are embedded using the same `all-MiniLM-L6-v2` model
4. ChromaDB is queried with optional domain metadata filtering
5. Top-3 chunks per query are retrieved

### Knowledge Base Coverage

This system distinguishes between the Candidate's Resume Information and the internal Knowledge Base capabilities. For each queried topic (skill or project), a distance threshold determines coverage:
- **COVERED:** Relevant semantic chunks found (Distance < 1.30).
- **PARTIALLY COVERED:** Related but less confident chunks found (Distance < 1.45).
- **NOT COVERED:** No relevant chunks found in the ChromaDB (Distance > 1.45).

### RAG Fallback Rules
- If a topic is **COVERED** or **PARTIALLY COVERED**, the retrieved RAG context is passed to the LLM to ground the question.
- If a topic is **NOT COVERED**, the system **strips out** any loosely retrieved chunks. The LLM is passed an empty RAG context block and told to rely purely on the candidate's resume information and the LLM's general knowledge. This prevents the LLM from fabricating false connections.

## 5. Prompt Engineering

### Prompt Library: `prompts/question_generation.json`

Contains reusable templates for:
- System prompt with interviewer instructions
- Difficulty variations (easy, medium, hard)
- Question type instructions (conceptual, practical, etc.)
- Deduplication instructions for multi-question generation

### Prompt Structure

Each LLM call receives:
1. **System prompt**: Interviewer role, strict length constraints, and the **ONE PRIMARY CONCEPT** generation rule.
2. **Difficulty**: Level + specific word count constraint (e.g., Easy 15-35 words).
3. **Question type**: Type + instruction
4. **Candidate profile**: Skills, projects, experience
5. **Retrieved context**: 2-3 relevant knowledge chunks (or NONE if NOT COVERED)
6. **Knowledge Base Status**: Explicitly tells the LLM if the context is COVERED or NOT COVERED.
7. **Dedup list**: Previously generated questions (for multi-question mode)

4. `qwen/qwen3.6-27b`
5. `openai/gpt-oss-120b`
6. `openai/gpt-oss-20b`

**API Key:** Loaded from `.env` via `python-dotenv`.
Never hardcoded, never printed, never committed.

**Error handling:**
- Missing API key → clear setup instructions
- Authentication failure → error message
- Rate limit → 10-second backoff + retry
- Empty/failed response → graceful handling

## 7. Multiple Question Generation

### `--count N` (default: 1, max: 10)

**Diversity strategy:**
- Questions rotate through different retrieval sources (skill groups)
- Each question gets focused context from a different skill area
- Mixed mode rotates through 5 question types
- Previously generated questions are included in each subsequent prompt to prevent duplication

### Example flow for `--count 5`:

| Slot | Source | Type |
|---|---|---|
| Q1 | skill:Java | conceptual |
| Q2 | skill:Python | practical |
| Q3 | skill:C++ | technical_reasoning |
| Q4 | skill:SQL | scenario |
| Q5 | skill:JavaScript | project |

## 8. CLI Usage

```
python scripts\generate_question.py --resume <PATH> [options]

Required:
  --resume PATH       Path to candidate resume PDF

Optional:
  --count N           Number of questions (1-10, default: 1)
  --difficulty LEVEL  easy | medium | hard (default: medium)
  --type TYPE         conceptual | technical_reasoning | practical |
                      scenario | project | mixed (default: mixed)
  --verbose           Show detailed pipeline output
```

### Examples

```bash
# Single question with defaults
python scripts\generate_question.py --resume data\resumes\sample_resume.pdf

# 5 mixed medium questions
python scripts\generate_question.py --resume data\resumes\sample_resume.pdf --count 5

# 3 hard scenario questions with verbose output
python scripts\generate_question.py --resume data\resumes\sample_resume.pdf --count 3 --difficulty hard --type scenario --verbose
```

## 9. Environment Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. Get a free Groq API key at: https://console.groq.com

## 10. Difficulty Levels

Controlled entirely via prompt engineering:

| Level | Description |
|---|---|
| easy | Foundational concepts, definitions, simple use cases |
| medium | Application, reasoning, comparisons, trade-offs |
| hard | Complex scenarios, debugging, edge cases, architectural decisions |

## 11. Question Types

| Type | Description |
|---|---|
| conceptual | Theory, definitions, foundational principles |
| technical_reasoning | Trade-offs, comparisons, complexity analysis |
| practical | Application-oriented, implementation questions |
| scenario | Realistic problem diagnosis/debugging |
| project | Direct reference to candidate's specific projects |
| mixed | Rotates through all 5 types (default) |

## 12. Limitations

- Resume parsing is keyword-based, not LLM-based. Unusual formats may miss sections.
- Skills not in the domain hint dictionary still use unfiltered semantic search.
- Question quality depends on the Groq model available in the user's account.
- No adaptive difficulty or cross-session learning (planned for later weeks).
- No answer evaluation or scoring.

## 13. What Belongs to Later Weeks

- FastAPI backend
- Frontend UI
- Authentication
- Voice interview (Whisper)
- Answer evaluation / scoring
- Adaptive learning engine
- Cross-session tracking
- Full Bloom's Taxonomy adaptation
- Recommendation engine

## 14. Test Results

Week 6 was validated using a comprehensive audit and 3 distinct test resumes:
- **Resume A (Backend):** Successfully identified Java/SQL as COVERED, Spring Boot/Redis as NOT COVERED. RAG fallback worked perfectly.
- **Resume B (Machine Learning):** Successfully identified Python as COVERED, PyTorch/Scikit-Learn as NOT COVERED. Questions generated correctly despite being out-of-bounds for the current Technical KB.
- **Resume C (Frontend):** Successfully identified React, JS, HTML as COVERED, and correctly retrieved load-balancing context for the React Dashboard project.

All difficulties and question types were validated, adhering strictly to the ONE PRIMARY CONCEPT rule and length bounds. Week 5 regression tests passed with 402 chunks maintained intact.
