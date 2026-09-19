# SmartInterview: Adaptive Technical Mock Interview Platform
## Academic Project Final Documentation & Technical Reference Report

**Degree / Course**: Bachelor of Technology (B.Tech) in Computer Science & Engineering  
**Project Title**: SmartInterview — Adaptive Technical Mock Interview Platform Grounded in Knowledge-Base Retrieval and Cognitive Taxonomy  
**Source of Truth**: Active Repository Implementation (`Smart-Interview-main`)  
**Evaluation Baseline**: 402 Chunks, 50 Concepts, 8 Domains (ChromaDB `technical_kb`)  
**Authoring Standard**: Academic B.Tech Project Report Format  

---

## 1. Abstract

Technical interview preparation in computer science education has traditionally relied on two extremes: static, non-adaptive problem repositories (e.g., LeetCode, HackerRank, GeeksforGeeks) or resource-intensive human mock interviews that lack scalability and standardized evaluation. Static platforms fail to adapt to a candidate’s immediate cognitive depth, while unconstrained conversational Large Language Model (LLM) interview bots frequently hallucinate technical assertions, lack curricular bounds, and grade candidate responses arbitrarily without a deterministic rubric.

This project presents **SmartInterview**, an intelligent, full-stack, adaptive technical mock interview platform. SmartInterview integrates:
1. **Automated Document Ingestion**: Deterministic PDF parsing using PyMuPDF (`fitz`) to extract verified candidate skills and real personal project descriptions from resumes, cross-referenced against targeted Job Descriptions (JDs) to prioritize role-overlap competencies (Group A) and critical role gaps (Group B).
2. **Domain-Filtered Retrieval-Augmented Generation (RAG)**: A curated, local knowledge base of 402 validated computer science chunks across 50 concepts in 8 technical domains stored in ChromaDB and indexed via SentenceTransformers (`all-MiniLM-L6-v2`, 384 dimensions). This retrieval pipeline achieves **96.97% Hit@1, 100.00% Hit@3, and an MRR of 0.9798** across empirical benchmarks, grounding questions in authoritative literature to reduce the risk of hallucination.
3. **Dynamic Question Generation**: Single-question-at-a-time generation via the Groq Cloud LLM (`openai/gpt-oss-120b`) guided by Bloom’s Revised Taxonomy (Remember, Understand, Apply, Analyze, Evaluate, Create), question difficulty (Easy, Medium, Hard), and previous-question deduplication.
4. **Hybrid Multi-Factor Evaluation**: A 5-dimensional scoring formula:
   $$\text{Overall Score} = 0.30 \times \text{Technical} + 0.20 \times \text{Completeness} + 0.20 \times \text{Relevance} + 0.15 \times \text{Semantic Similarity} + 0.15 \times \text{Concept Coverage}$$
   combining LLM qualitative critique, Sentence-BERT cosine similarity, and algorithmic concept coverage.
5. **Deterministic Adaptive Learning Engine**: Python-governed progression rules ($\text{Score} \ge 80 \implies \text{advance Bloom}$; $\text{Score} < 50 \implies \text{regress Bloom}$) and weakness-biased round-robin skill rotation.
6. **Strict Safeguards & Academic Syllabus Mode**: Strict fundamental-struggle auto-stop ($\ge 5$ questions answered, difficulty Easy, 3 consecutive scores $< 40\%$), hard safety boundaries (max 30 questions), manual termination at any time, and an isolated Coursework Syllabus Mode supporting multi-file ingestion with post-interview deduplicated knowledge base merging.

The system is fully implemented and locally runnable on a zero-budget architecture comprising a React 18 / Vite frontend, FastAPI REST backend, MySQL 8.0 relational database, local ChromaDB vector store, and Groq cloud inference.

---

## 2. Introduction

Technical mock interviews are essential for software engineering candidates transitioning from academic study to professional industry roles. However, effective interview preparation requires active verbal or written retrieval, progressive cognitive challenge, personalized domain alignment, and constructive, actionable feedback.

Standard web-based preparation tools suffer from critical shortcomings:
- **Question Stagnation**: Repetitive, static question lists that do not adjust to what the candidate actually knows.
- **Context Detachment**: Inability to personalize questions around a candidate's actual projects or target job requirements.
- **Uncontrolled Generative AI**: LLM interview bots operating without retrieval grounding produce factually incorrect interview questions and evaluate candidate responses inconsistently.
- **Missing Cognitive Scaffolding**: Lack of pedagogical structure; questions jump randomly between basic syntax recall and complex distributed systems architecture without systematic progression.

SmartInterview addresses these challenges through a modular system design where the generative AI is constrained by local vector retrieval, while interview progression and evaluation scoring are governed by deterministic Python state machines.

---

## 3. Problem Statement

Current technical interview preparation methodologies exhibit four major deficiencies:
1. **Lack of Adaptive Scaffolding**: Static questionnaires do not adjust question complexity based on candidate ability, leading to frustration for struggling learners and boredom for advanced candidates.
2. **Absence of Role Alignment**: General interview preparation does not map a candidate's existing resume profile against specific target Job Description requirements, failing to highlight high-priority competencies or critical knowledge gaps.
3. **Hallucination in Unbounded LLM Generation**: Direct prompting of generative language models without domain-filtered retrieval introduces unsupported technical claims and incorrect architectural premises into generated questions.
4. **Unreliable and Non-Standardized Evaluation**: Qualitative LLM feedback alone lacks deterministic score reproducibility, while keyword matching fails to capture semantic meaning and conceptual depth.

---

## 4. Objectives

The primary engineering and pedagogical objectives of the SmartInterview project are:
1. **Resume & Job Description Analysis**: Implement deterministic, zero-cost PDF parsing using PyMuPDF to extract candidate profiles, technical skills, and project contexts, mapping them into Group A (Role Overlap) and Group B (Role Gaps).
2. **Domain-Filtered Vector Grounding**: Ingest a curated computer science knowledge base (402 chunks, 50 concepts, 8 core domains) into a local ChromaDB vector database, implementing top-3 semantic retrieval via SentenceTransformers (`all-MiniLM-L6-v2`) to ground LLM prompts.
3. **Cognitive Taxonomy Question Generation**: Modulate question formulation dynamically across Bloom's Revised Taxonomy (Levels 1 to 6) and difficulty tiers (Easy, Medium, Hard) using Groq Cloud LLM inference.
4. **Multi-Factor Answer Scoring**: Implement a transparent, deterministic evaluation engine combining LLM technical critique (30%), completeness (20%), relevance (20%), SBERT cosine similarity (15%), and algorithmic concept coverage (15%).
5. **Deterministic Adaptive State Machine**: Regulate interview progression entirely through Python logic (Score $\ge 80 \implies$ advance Bloom; Score $< 50 \implies$ regress Bloom; weakness-biased skill selection).
6. **Academic Syllabus Mode**: Support coursework-specific preparation via isolated temporary vector spaces, single-pass subject/topic inference, and post-interview 2-layer deduplicated knowledge base merging.
7. **Empirical Validation**: Validate all subsystems through reproducible automated tests, measuring retrieval accuracy (Hit@k, MRR), adaptive boundary compliance, and end-to-end transaction integrity.

---

## 5. Existing System Analysis

| Dimension | Static Platforms (LeetCode, HackerRank) | Human Mock Platforms (Pramp, Interviewing.io) | Generic AI Chatbots (ChatGPT, Claude) |
|---|---|---|---|
| **Adaptability** | None (Static question lists) | High (Human interviewer adjusts) | Uncontrolled (Drifts without pedagogical structure) |
| **Personalization** | None (Same problems for all) | Moderate (Human reads resume) | Low (Requires complex custom prompting) |
| **Cost** | Low / Freemium | High ($50–$200 per session) | Medium (API subscription costs) |
| **Grounding** | Hardcoded problem statements | Human knowledge base | None (Subject to hallucinations) |
| **Scoring Rubric** | Binary unit test pass/fail | Subjective human notes | Opaque LLM output |
| **Availability** | 24/7 self-service | Requires scheduling peer/interviewer | 24/7 self-service |

### Disadvantages of Existing Systems:
- Unit-test-based static platforms test only coding syntax and algorithmic edge cases, neglecting architectural reasoning, design trade-offs, and conceptual explanation.
- Human mock interviews are cost-prohibitive for university students and cannot scale to daily practice.
- Generic LLM chatbots lack state persistence, pedagogical taxonomy, question deduplication, and verifiable grounding in authoritative literature.

---

## 6. Proposed System: SmartInterview

SmartInterview combines the 24/7 availability and low cost of automated software with the contextual adaptation and qualitative feedback of an experienced human interviewer.

### Key Innovations:
1. **Skill-First, Domain-Aware RAG Pipeline**: Rather than performing a global vector search, SmartInterview maps canonical candidate skills to specific technical domains (`dbms`, `oop`, `os`, `cn`, `system-design`, `dsa`, `design-patterns`, `ml-dl`), querying ChromaDB with strict domain metadata filters to guarantee relevant retrieval.
2. **Deterministic Bloom’s Taxonomy Engine**: The LLM generates the text of the question, but deterministic Python code determines the cognitive level (Remember to Create), question type, and difficulty.
3. **Hybrid Evaluation Framework**: Decouples semantic similarity from factual correctness. Sentence-BERT cosine similarity measures vocabulary proximity, while LLM critique and concept coverage math verify factual accuracy.
4. **Stateless Relational State Machine**: Session state, per-skill attempts, and evaluation scores are serialized into JSON columns in MySQL 8.0, ensuring backend worker statelessness.
5. **Safe Academic Syllabus Mode**: Allows university students to upload course syllabi into an isolated temporary vector space, practicing against their own curriculum without corrupting the permanent knowledge base.

---

## 7. System Requirements

### Hardware Requirements (Zero-Budget Local Machine):
- **Processor**: Intel Core i5 / AMD Ryzen 5 or higher (minimum 4 physical cores).
- **RAM**: 8 GB minimum (16 GB recommended for concurrent Vite dev server, Uvicorn, and MySQL).
- **Storage**: 5 GB available disk space for ChromaDB index, PyTorch models, and MySQL database.
- **Network**: Internet connectivity required exclusively for cloud Groq LLM API calls; vector retrieval, embeddings, and database run 100% locally.

### Software & Environment:
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Version 3.10 to 3.12.
- **Node.js**: Version 18.x or 20.x LTS.
- **Database Server**: MySQL 8.0 Server running on `localhost:3306`.
- **Package Managers**: `pip` (Python), `npm` (Node).

### Key Python Dependencies:
- `fastapi >= 0.115.0`, `uvicorn >= 0.30.0` (REST API layer)
- `sqlalchemy >= 2.0.0`, `pymysql >= 1.1.0`, `cryptography` (Database ORM)
- `chromadb == 0.6.0` (Persistent local vector database)
- `sentence-transformers >= 3.0.0`, `torch` (Local dense embeddings)
- `pymupdf >= 1.24.0` (PDF document extraction)
- `python-docx >= 1.1.0` (DOCX extraction and documentation compilation)
- `python-jose[cryptography]`, `bcrypt` (JWT and password security)
- `groq >= 0.11.0` (Cloud LLM client)

### Key Frontend Dependencies:
- `react ^18.3.1`, `react-dom ^18.3.1` (UI library)
- `vite ^6.0.0` (Build tool and development server)
- `react-router-dom ^7.0.0` (Client-side routing)
- `axios ^1.7.0` (HTTP client with JWT interceptors)
- `tailwindcss ^4.0.0`, `@tailwindcss/vite` (Styling)
- `lucide-react ^0.460.0` (Iconography)

---

## 8. System Architecture

SmartInterview enforces a strict separation between **Local Infrastructure** and **Cloud Services**:
- **LOCAL**: MySQL 8.0, ChromaDB vector storage, SentenceTransformer embeddings (`all-MiniLM-L6-v2`), PyMuPDF parsing, and FastAPI business logic.
- **CLOUD**: Groq API inference for high-speed LLM generation (`openai/gpt-oss-120b`).

```
+---------------------------------------------------------------------------------------------------+
|                                     REACT FRONTEND (Vite / Port 5174)                             |
|  Landing -> Login/Register -> Dashboard -> Resume/JD Upload -> Setup -> Interview -> Results/Hist  |
+---------------------------------------------------------------------------------------------------+
                                                |  HTTP / REST (Axios with Bearer JWT)
                                                v
+---------------------------------------------------------------------------------------------------+
|                                    FASTAPI BACKEND (Uvicorn / Port 8000)                          |
|  Routers: /api/auth | /api/resumes | /api/job-descriptions | /api/interviews | /api/users          |
+---------------------------------------------------------------------------------------------------+
      |                          |                             |                        |
      | Password / Token         | PDF Extraction              | Question Loop          | Persistence
      v                          v                             v                        v
+--------------+      +---------------------+      +----------------------+   +---------------------+
| Auth Service |      | Resume & JD Service |      |  Interview Service   |   |   MySQL 8 Database  |
| - bcrypt hash|      | - PyMuPDF (fitz)    |      |  - submit_and_eval() |   | - users             |
| - JWT HS256  |      | - Section Regex     |      |  - Bloom Progression |   | - resumes           |
+--------------+      | - Skill Taxonomy    |      |  - Skill Selection   |   | - job_descriptions  |
                      +---------------------+      +----------------------+   | - interview_sessions|
                                 |                             |              | - interview_questions
                                 v (Matched Skills)            |              | - answers           |
                      +----------------------------------------+              | - answer_evaluations|
                      |                                                       +---------------------+
                      v
+---------------------------------------------------------------------------------------------------+
|                                     QUESTION GENERATION PIPELINE                                  |
| 1. SkillDomainMap: Canonical Skill -> Relevant KB Domain (e.g. 'sql' -> 'dbms')                    |
| 2. DomainQueryTemplate: Construct domain-aware query string                                       |
| 3. ChromaDB Query: SentenceTransformer all-MiniLM-L6-v2 -> retrieve top-3 chunks filtered by domain |
| 4. Prompt Assembly: System prompt + Bloom instruction + RAG chunks + Project context + Dedup     |
| 5. Groq LLM Inference: openai/gpt-oss-120b call with retry/backoff -> Single Clean Question Text  |
+---------------------------------------------------------------------------------------------------+
                                                |
                                                v (Candidate Submits Text Answer)
+---------------------------------------------------------------------------------------------------+
|                                      ANSWER EVALUATION PIPELINE                                   |
| 1. Groq LLM Critique: Technical (30%), Completeness (20%), Relevance (20%), Feedback, Strengths   |
| 2. SentenceTransformer: Cosine similarity between candidate answer and (Question + Reference RAG) |
| 3. Concept Coverage Math: Average of LLM score and len(found_concepts) / len(expected_concepts)  |
| 4. Weighted Overall Score Calculation (Clamped 0-100) -> Persist AnswerEvaluation in MySQL        |
| 5. Adaptive Decision: Score updates SkillPerformance -> Decide next Bloom level & next skill      |
+---------------------------------------------------------------------------------------------------+
```

---

## 9. Module Architecture

The backend application is structured into modular layers adhering to separation of concerns:

```
backend/app/
├── main.py                  # App entrypoint, CORS setup, router mounting
├── config.py                # Environment configuration and path constants
├── database.py              # SQLAlchemy engine, SessionLocal, get_db dependency
├── dependencies/
│   └── auth.py              # HTTPBearer token extraction & User resolution
├── models/                  # SQLAlchemy ORM models (7 tables)
│   ├── user.py              # User account entity
│   ├── resume.py            # Uploaded resume metadata & parsed JSON profile
│   ├── job_description.py   # Job description metadata & extracted skills JSON
│   ├── interview.py         # InterviewSession & serialized AdaptiveState JSON
│   └── question.py          # InterviewQuestion, Answer, and AnswerEvaluation
├── schemas/                 # Pydantic validation models (Requests & Responses)
├── routers/                 # REST API route controllers
│   ├── auth.py              # POST /register, POST /login, GET /me
│   ├── resumes.py           # POST /upload, GET /current, DELETE /{id}
│   ├── job_descriptions.py  # POST /upload, GET /current, GET /mapping
│   ├── interviews.py        # POST /start, POST /answer, POST /complete, GET /results
│   └── users.py             # GET /profile, PUT /profile, GET /performance
└── services/                # Business logic and external service integrations
    ├── auth_service.py      # bcrypt password verification & JWT encoding
    ├── resume_service.py    # Service wrapper for PyMuPDF extraction
    ├── jd_service.py        # Technical section filter & Group A/B mapping
    ├── question_service.py  # Singleton manager for ChromaDB, SBERT, and Groq
    ├── bloom.py             # Bloom's Revised Taxonomy levels & helpers
    ├── adaptive_engine.py   # Deterministic progression rules & skill selection
    ├── evaluation_service.py# 5-factor scoring engine & Groq evaluator
    ├── interview_service.py # Full session lifecycle coordinator
    ├── syllabus_rag_service.py # Temporary ChromaDB RAG & deduplicated merge
    └── syllabus_engine.py   # Syllabus topic selection with coverage constraints
```

---

## 10. Database Design

The relational database is implemented in **MySQL 8.0** with InnoDB storage, utf8mb4 character encoding, and foreign key constraints enforcing cascade deletion.

### Entity-Relationship (ER) Overview:
- `users` (1) $\rightarrow$ (N) `resumes`
- `users` (1) $\rightarrow$ (N) `job_descriptions`
- `users` (1) $\rightarrow$ (N) `interview_sessions`
- `interview_sessions` (1) $\rightarrow$ (N) `interview_questions`
- `interview_questions` (1) $\rightarrow$ (1) `answers`
- `answers` (1) $\rightarrow$ (1) `answer_evaluations`
- `interview_questions` (1) $\rightarrow$ (1) `answer_evaluations`

### Table Specifications:

#### 1. `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique user ID |
| `name` | VARCHAR(100) | NOT NULL | User's full name |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | User email address (login credential) |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt password hash |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |

#### 2. `resumes`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique resume ID |
| `user_id` | INT | NOT NULL, FK $\rightarrow$ users(id) ON DELETE CASCADE | Owner user ID |
| `filename` | VARCHAR(255) | NOT NULL | Original uploaded PDF filename |
| `name` | VARCHAR(255) | NULL | Candidate name extracted from resume |
| `file_path` | VARCHAR(500) | NOT NULL | Path to saved PDF on disk |
| `skills` | JSON | NULL | List of extracted canonical skills |
| `projects` | JSON | NULL | List of extracted candidate projects |
| `experience` | JSON | NULL | Extracted work experience blocks |
| `education` | JSON | NULL | Extracted education blocks |
| `raw_text` | MEDIUMTEXT | NULL | Cleaned text extracted from PDF |
| `page_count` | INT | NULL | Number of pages in PDF |
| `uploaded_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Upload timestamp |

#### 3. `job_descriptions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique JD ID |
| `user_id` | INT | NOT NULL, FK $\rightarrow$ users(id) ON DELETE CASCADE | Owner user ID |
| `filename` | VARCHAR(255) | NOT NULL | Original uploaded JD PDF filename |
| `file_path` | VARCHAR(500) | NOT NULL | Path to saved JD file on disk |
| `skills` | JSON | NULL | List of extracted technical skills |
| `raw_text` | MEDIUMTEXT | NULL | Cleaned technical text from JD |
| `uploaded_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Upload timestamp |

#### 4. `interview_sessions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique session ID |
| `user_id` | INT | NOT NULL, FK $\rightarrow$ users(id) ON DELETE CASCADE | Candidate user ID |
| `resume_id` | INT | NULL, FK $\rightarrow$ resumes(id) ON DELETE CASCADE | Associated resume ID |
| `difficulty` | ENUM('easy','medium','hard') | NOT NULL, DEFAULT 'medium' | Initial/current difficulty |
| `question_type` | VARCHAR(50) | NOT NULL, DEFAULT 'mixed' | Starting question type preference |
| `question_count` | INT | NOT NULL, DEFAULT 5 | Target question count |
| `selected_skills` | JSON | NULL | List of target skills chosen for session |
| `status` | ENUM('in_progress','completed','abandoned') | DEFAULT 'in_progress' | Lifecycle state |
| `started_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Session start timestamp |
| `completed_at` | DATETIME | NULL | Session completion timestamp |
| `is_adaptive` | TINYINT(1) | DEFAULT 1 | Boolean indicating adaptive session |
| `adaptive_state` | JSON | NULL | Serialized AdaptiveState (scores, attempts, Bloom) |
| `current_bloom_level`| VARCHAR(20) | NULL | Active Bloom level ID (e.g., 'remember') |
| `final_recommendations`| JSON | NULL | Post-interview generated improvement tips |
| `completion_reason`| VARCHAR(50) | NULL | 'manual', 'auto_stop_fundamental_struggle', 'max_questions_safety_limit' |
| `job_description_id`| INT | NULL, FK $\rightarrow$ job_descriptions(id) | Associated target JD |
| `mode` | VARCHAR(50) | NOT NULL, DEFAULT 'normal' | 'normal' or 'syllabus' |
| `syllabus_id` | VARCHAR(100) | NULL | Associated syllabus identifier |
| `syllabus_state` | JSON | NULL | Serialized SyllabusState (topic coverage) |

#### 5. `interview_questions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique question ID |
| `session_id` | INT | NOT NULL, FK $\rightarrow$ interview_sessions(id) ON DELETE CASCADE | Parent interview session |
| `question_number` | INT | NOT NULL | Sequential question number (1, 2, 3...) |
| `skill` | VARCHAR(100) | NOT NULL | Tested technical skill |
| `question_type` | VARCHAR(50) | NOT NULL | Type: conceptual, practical, scenario, etc. |
| `difficulty` | ENUM('easy','medium','hard') | NOT NULL | Difficulty tier of this question |
| `question_text` | TEXT | NOT NULL | Question text presented to candidate |
| `rag_context` | JSON | NULL | Top-3 RAG chunks supplied in prompt |
| `project_context` | JSON | NULL | Candidate project details passed in prompt |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Generation timestamp |
| `bloom_level` | VARCHAR(20) | NULL | Bloom level ID ('remember' to 'create') |
| `bloom_level_number`| INT | NULL | Bloom numeric order (1 to 6) |

#### 6. `answers`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique answer ID |
| `question_id` | INT | NOT NULL, UNIQUE, FK $\rightarrow$ interview_questions(id) ON DELETE CASCADE | Associated question |
| `session_id` | INT | NOT NULL, FK $\rightarrow$ interview_sessions(id) ON DELETE CASCADE | Associated session |
| `user_id` | INT | NOT NULL, FK $\rightarrow$ users(id) ON DELETE CASCADE | Candidate user ID |
| `answer_text` | TEXT | NULL | Candidate's submitted text response |
| `submitted_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Submission timestamp |

#### 7. `answer_evaluations`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique evaluation ID |
| `answer_id` | INT | NOT NULL, UNIQUE, FK $\rightarrow$ answers(id) ON DELETE CASCADE | Associated answer |
| `question_id` | INT | NOT NULL, FK $\rightarrow$ interview_questions(id) ON DELETE CASCADE | Associated question |
| `technical_score` | INT | NOT NULL, DEFAULT 0 | LLM technical score (0-100) |
| `completeness_score`| INT | NOT NULL, DEFAULT 0 | LLM completeness score (0-100) |
| `relevance_score` | INT | NOT NULL, DEFAULT 0 | LLM relevance score (0-100) |
| `semantic_similarity_score`| INT | NOT NULL, DEFAULT 0 | SBERT cosine similarity score (0-100) |
| `concept_coverage_score` | INT | NOT NULL, DEFAULT 0 | Algorithmic concept coverage (0-100) |
| `overall_score` | INT | NOT NULL, DEFAULT 0 | Weighted overall score (0-100) |
| `feedback` | TEXT | NULL | Qualitative explanation and coaching feedback |
| `strengths` | JSON | NULL | List of positive points identified |
| `weaknesses` | JSON | NULL | List of deficiencies identified |
| `concepts_expected`| JSON | NULL | List of concepts expected in a complete answer |
| `concepts_found` | JSON | NULL | List of expected concepts identified in answer |
| `evaluated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Evaluation timestamp |

---

## 11. Knowledge Base and RAG

### Ground-Truth Knowledge Base Baseline:
The curated knowledge base stored in `data/processed/` and indexed in ChromaDB collection `technical_kb` consists of exactly **402 chunks, 50 concepts, and 8 domains**.

| Domain Code | Domain Name | Concepts | Chunks | Key Concepts Covered |
|---|---|---|---|---|
| `cn` | Computer Networks | 5 | 33 | dns (8), http-vs-https (5), ipv4-vs-ipv6 (5), osi-model (13), tcp-vs-udp (2) |
| `dbms` | Database Management Systems | 6 | 45 | acid-properties (8), indexing (9), keys (10), normalization (7), sql-joins (6), transactions (5) |
| `design-patterns`| Software Design Patterns | 4 | 105 | factory (10), observer (34), singleton (26), strategy (35) |
| `dsa` | Data Structures & Algorithms | 15 | 63 | array (9), graph (8), linked-list (7), string (6), tree (6), matrix (4), recursion (4), hash-table (3), trie (2), stack (2) |
| `ml-dl` | Machine Learning & Deep Learning | 5 | 35 | decision-trees (11), neural-networks (9), bias-variance (5), linear-vs-logistic (5), overfitting (5) |
| `oop` | Object-Oriented Programming | 5 | 33 | polymorphism (10), composition-inheritance (7), abstraction (6), interfaces (6), encapsulation (4) |
| `os` | Operating Systems | 5 | 35 | scheduling-algorithms (10), virtual-memory (10), mutex-vs-semaphore (8), process-vs-thread (4), deadlock (3) |
| `system-design` | Distributed System Design | 5 | 53 | consistent-hashing (16), load-balancing (13), caching (11), cap-theorem (9), microservices (4) |
| **TOTAL** | **8 Core Domains** | **50** | **402** | **100% Quality Audit (`data/knowledge_stats.json`)** |

### Chunk Schema & Boundary Constraints:
Every chunk stored in `data/processed/` satisfies:
- Token count bounded between 50 and 400 tokens (average: 195.47 tokens).
- Bounded token distribution prevents context starvation (too short) or context dilution (too long).
- Globally unique ID pattern: `<domain>_<concept>_<index:03d>` (e.g., `dbms_acid-properties_001`).
- Fields: `chunk_id`, `domain`, `concept`, `source`, `source_url`, `text`, `token_count`.

### Retrieval Evaluation Benchmark:
Retrieved using SentenceTransformer `all-MiniLM-L6-v2` with top-k=5 against `data/evaluation/retrieval_queries.json` (33 technical queries across all 8 domains):
- **Total Test Queries**: 33
- **Hit@1**: 96.97%
- **Hit@3**: 100.00%
- **Hit@5 (Recall@5)**: 100.00%
- **Mean Reciprocal Rank (MRR)**: 0.9798
- **Failed Queries**: 0 (all queries retrieved their expected concept within the top 5 chunks).

---

## 12. Resume Processing

Implemented in `scripts/parse_resume.py` and wrapped by `backend/app/services/resume_service.py`:
1. **Text Extraction**: Uses PyMuPDF (`fitz`) to extract raw text blocks with bounding-box ordering.
2. **Generic Header/Footer Cleaning**: `clean_document_pages()` detects repeated header/footer lines across pages, pagination markers (`Page 1 of 2`, `- 2 -`), and removes them without LLM costs.
3. **Candidate Name Extraction**: Scans top 10 lines of the document, filtering out contact lines (containing `@`, `http`, phone numbers) and resume title keywords (`Resume`, `Curriculum Vitae`), matching against a strict Title-Case name regex. Verified on `scratch/alex_chen_resume.pdf` $\rightarrow$ "Alex Chen".
4. **Section Boundary Detection**: Employs regex patterns for standard headings (`Skills`, `Technical Skills`, `Experience`, `Projects`, `Education`, `Certifications`) to partition raw text into distinct semantic sections.
5. **Canonical Skill Matching**: Matches candidate text against the project's central canonical skill taxonomy (`CANONICAL_SKILL_NAMES` and `SKILL_ALIASES`). Matches longest phrases first with regex word boundaries to prevent false substring matches (e.g., ensuring "Java" does not match inside "JavaScript").

---

## 13. Job Description Processing

Implemented in `backend/app/services/jd_service.py`:
1. **Document Ingestion**: Extracts raw text from uploaded JD PDFs up to 5 MB using PyMuPDF.
2. **Non-Technical Section Filtering**: Real-world job descriptions contain large non-technical sections (company perks, EEO disclosures, salary ranges, benefits). `_find_technical_sections()` identifies headings and excludes non-technical blocks matching `benefits`, `equal opportunity`, `compensation`, and `about us`.
3. **Technical Skill Extraction**: Scans the filtered technical requirements using `match_skills_in_text()` to extract validated canonical skills. Verified on `scratch/senior_backend_jd.pdf` $\rightarrow$ 14 skills extracted (Python, FastAPI, AsyncIO, Go, PostgreSQL, Redis, Docker, Kubernetes, CI/CD, REST API, Kafka, Prometheus, OpenTelemetry, Grafana).

---

## 14. Skill Mapping

Implemented in `map_skills()` in `backend/app/services/jd_service.py`:
When both a candidate resume and a target job description are present, the system prioritizes skills into two groups:

1. **Group A (Role Overlap / Matched Skills)**: Skills required by the JD that the candidate explicitly claims on their resume ($JD \cap Resume$).
   - *Interview Purpose*: Verify that the candidate actually possesses the depth of experience claimed on their resume.
   - *Example (`alex_chen_resume.pdf` vs `senior_backend_jd.pdf`)*: 11 skills (Python, FastAPI, AsyncIO, Go, PostgreSQL, Redis, Docker, Kubernetes, CI/CD, REST API, Kafka).
2. **Group B (Role Gaps / Untested Requirements)**: Skills required by the JD that do NOT appear on the candidate's resume ($JD - Resume$).
   - *Interview Purpose*: Test whether the candidate can reason about critical role requirements they have not formally documented.
   - *Example*: 3 skills (Prometheus, OpenTelemetry, Grafana).
3. **Resume-Only Skills**: Skills on the candidate's resume not mentioned in the JD ($Resume - JD$, e.g., Django, SQL). These are excluded from the primary interview plan.
4. **Ordered Interview Pool**: Concatenates Group A first, followed by Group B, ensuring claimed competencies are verified before exploring gap areas.

---

## 15. Question Generation Pipeline

Question generation runs dynamically one question at a time via `generate_single_question()` in `backend/app/services/question_service.py`:

```
Selected Skill (e.g. 'PostgreSQL')
       ↓
SKILL_DOMAIN_MAP Lookup → domain: 'dbms'
       ↓
DOMAIN_QUERY_TEMPLATES Format → 'SQL database PostgreSQL concepts: indexing, joins, normalization...'
       ↓
SentenceTransformer ('all-MiniLM-L6-v2') → 384-d Embedding
       ↓
ChromaDB 'technical_kb' Query (n_results=3, where={'domain': 'dbms'})
       ↓
Retrieved Top-3 Grounding Chunks
       ↓
Prompt Assembly:
- System Prompt (technical interviewer persona)
- Bloom Cognitive Instruction (e.g., 'Apply' guidance)
- Difficulty Instruction ('easy', 'medium', 'hard')
- Retrieved RAG Context (top-3 vetted chunks)
- Optional Project Context (from candidate's resume)
- Previous Questions List (deduplication constraint)
       ↓
Groq Cloud LLM Call (openai/gpt-oss-120b, temp=0.7, max_tokens=1500)
       ↓
Clean, Single Question Text Returned to Frontend
```

---

## 16. Answer Evaluation Engine

Implemented in `backend/app/services/evaluation_service.py`:
Candidate answers are evaluated across five dimensions, each addressing a distinct aspect of response quality:

$$\text{Overall Score} = 0.30 \times \text{Technical} + 0.20 \times \text{Completeness} + 0.20 \times \text{Relevance} + 0.15 \times \text{Semantic Similarity} + 0.15 \times \text{Concept Coverage}$$

1. **Technical Correctness ($30\%$)**: Assessed by Groq LLM (temperature 0.3) against reference RAG context to verify factual accuracy and algorithmic correctness.
2. **Completeness ($20\%$)**: Assessed by LLM to verify whether all parts of the multi-part question were addressed.
3. **Relevance ($20\%$)**: Assessed by LLM to penalize tangential or evasive answers.
4. **Semantic Similarity ($15\%$)**: Computed via SentenceTransformer cosine similarity between candidate text and reference text ($\text{Question} + \text{RAG chunks}$), scaled non-linearly:
   $$\text{Score} = \max\left(0, \min\left(100, \frac{\text{cosine} - 0.10}{0.60} \times 100\right)\right)$$
   *Note*: Semantic similarity measures vocabulary and topic closeness; it is an auxiliary signal and does NOT prove factual correctness.
5. **Concept Coverage ($15\%$)**: Average of LLM-extracted concept coverage and programmatic verification:
   $$\text{Coverage} = \frac{|\text{found\_concepts}|}{|\text{expected\_concepts}|} \times 100$$
6. **Qualitative Feedback**: Generates constructive feedback text, actionable strengths, and specific weaknesses. All scores are clamped to $[0, 100]$.

---

## 17. Adaptive Interview Engine

The adaptive learning engine (`backend/app/services/adaptive_engine.py`) operates deterministically. **The LLM does NOT decide interview flow, difficulty, or pass/fail transitions.**

### Deterministic Progression Rules:
- **Score $\ge 80\%$ (Mastery)**: Advance Bloom level ($+1$). If already at maximum Bloom level (*Create*), advance difficulty tier ($\text{easy} \rightarrow \text{medium} \rightarrow \text{hard}$).
- **Score $50\% - 79\%$ (Proficiency)**: Maintain current Bloom level and current difficulty tier.
- **Score $< 50\%$ (Struggle)**: Regress Bloom level ($-1$). If already at minimum Bloom level (*Remember*), decrease difficulty tier ($\text{hard} \rightarrow \text{medium} \rightarrow \text{easy}$).

### Weakness-Biased Round-Robin Skill Selection:
`select_skill()` ensures comprehensive coverage while focusing on candidate weaknesses:
1. Calculates attempts and average scores across all selected skills in `AdaptiveState`.
2. Identifies the minimum number of attempts across all candidate skills.
3. Filters candidates to only those skills with minimum attempts (ensuring all skills are tested).
4. If multiple skills tie for minimum attempts, selects the skill with the **lowest average score** (reinforcing weaknesses).

### Termination Safeguards:
1. **Manual Finish**: Candidate can click "Finish Interview" at any time. `complete_interview()` sets `completion_reason = "manual"` and generates final recommendations.
2. **Strict Fundamental-Struggle Auto-Stop**: Automatically halts interview early ONLY when ALL 4 conditions are met:
   - At least 5 questions have been answered.
   - Current difficulty has dropped to `easy`.
   - The last 3 consecutive answers all scored below $40\%$.
   - Objective evidence demonstrates the candidate cannot handle fundamental concepts.
   - Sets `completion_reason = "auto_stop_fundamental_struggle"`.
3. **Safety Upper Bound**: Maximum limit of `MAX_ADAPTIVE_QUESTIONS = 30` to prevent runaway server loops. Sets `completion_reason = "max_questions_safety_limit"`.

---

## 18. Bloom’s Taxonomy Representation

SmartInterview models Bloom's Revised Taxonomy across six immutable cognitive levels defined in `backend/app/services/bloom.py`:

| Order | Level | Description | Action Verbs | Preferred Question Types |
|---|---|---|---|---|
| 1 | **Remember** | Recall facts, definitions, terminology | Define, list, name, identify, state | Conceptual, Practical |
| 2 | **Understand** | Explain concepts, summarize, interpret meaning | Explain, describe, summarize, illustrate | Conceptual, Technical Reasoning |
| 3 | **Apply** | Use knowledge to solve concrete practical problems | Implement, use, solve, demonstrate | Practical, Scenario |
| 4 | **Analyze** | Compare approaches, break down trade-offs | Compare, contrast, differentiate, examine | Technical Reasoning, Practical |
| 5 | **Evaluate** | Judge solutions, justify architectural decisions | Evaluate, justify, argue, critique | Scenario, Project |
| 6 | **Create** | Architect new systems, synthesize solutions | Design, propose, formulate, construct | Project, Scenario |

Cognitive boundaries are strictly enforced: order is clamped to $[1, 6]$.

---

## 19. Syllabus Mode

Syllabus Mode enables coursework-specific interview preparation:
1. **Multi-File Ingestion**: Accepts PDF, TXT, and DOCX course materials via `POST /api/interviews/upload-syllabus`.
2. **Single-Pass Inference**: `infer_subject_and_topics()` executes a single unified LLM prompt over document excerpts, extracting the overall subject title and 4–14 distinct curriculum topics.
3. **Isolated Temporary Vector Space**: Chunks and embeds syllabus text into an isolated ChromaDB collection named `temp_syllabus_{temp_id}`. Questions during the interview are retrieved strictly from this temporary collection, preventing cross-contamination.
4. **Adaptive Topic Selection**: `SyllabusState` selects topics using a three-tier constraint algorithm:
   - *Breadth-First*: Topics with 0 attempts are asked first.
   - *Weakness Reinforcement*: Topics with an average score $< 60\%$ are prioritized for follow-up.
   - *Depth Balancing*: Topics with the fewest total questions asked are selected next.
5. **Post-Interview 2-Layer Deduplicated Merge**: Upon interview completion, `merge_temporary_to_permanent_kb()` inspects all temporary chunks:
   - *Layer 1 (Exact Content-Hash Deduplication)*: Computes SHA-256 hash of normalized text; skips if chunk ID exists.
   - *Layer 2 (Semantic Near-Duplicate Filtering)*: Queries `technical_kb` with the chunk embedding; skips if top cosine distance $< 0.10$ ($> 95\%$ semantic similarity).
   - Genuinely novel technical chunks are upserted into `technical_kb`.
6. **Lifecycle Cleanup**: `delete_temporary_rag()` drops `temp_syllabus_{temp_id}` from ChromaDB, reclaiming disk space.

---

## 20. Authentication and Security

### Security Architecture:
- **Password Hashing**: Salted bcrypt hashing via `passlib` / `bcrypt`, safely truncated to 72 bytes.
- **Stateless JWT Tokens**: HMAC-SHA256 (`HS256`) signed tokens with 24-hour expiration (`1440` minutes).
- **Protected Endpoints**: Verified through FastAPI `Depends(get_current_user)` reading `Authorization: Bearer <token>`.
- **SQL Injection Prevention**: 100% of relational queries use SQLAlchemy ORM parameterized statements; raw SQL string concatenation is prohibited.
- **File Upload Protection**: Enforces 5 MB file size limits (20 MB for syllabi), PDF/TXT/DOCX extension validation, and unique UUID filenames outside web root.
- **CORS Configuration**: Restricts access to frontend origins (`localhost:5173`, `localhost:5174`).

### Academic / Demonstration vs. Production Security Disclosure:
- **Academic Implementation**: JWT secret key has a development fallback in `config.py`; tokens stored in browser `localStorage` are accessible to JavaScript (vulnerable to hypothetical XSS); no refresh token rotation or multi-tab user isolation is implemented.
- **Production Requirements**: A production release would require storing JWTs in `HttpOnly`, `Secure`, `SameSite=Strict` cookies, implementing CSRF tokens, rotating refresh tokens in Redis, and integrating rate limiting (e.g., `slowapi`).

---

## 21. API Specification

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Status & Key Fields |
|---|---|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Register new candidate account | `{ name, email, password, confirm_password }` | `201 Created`: `{ access_token, user }` |
| `POST` | `/api/auth/login` | Public | Authenticate candidate & issue JWT | `{ email, password }` | `200 OK`: `{ access_token, user }` |
| `GET` | `/api/auth/me` | Bearer | Verify token & return current user | None | `200 OK`: `{ id, name, email, created_at }` |
| `POST` | `/api/resumes/upload` | Bearer | Upload & parse candidate PDF resume | `multipart/form-data` (`file`) | `201 Created`: `ResumeResponse` (name, skills, projects) |
| `GET` | `/api/resumes/current` | Bearer | Get active resume metadata & skills | None | `200 OK`: `ResumeResponse` |
| `DELETE` | `/api/resumes/{id}` | Bearer | Delete uploaded resume and file | Path param: `id` | `204 No Content` |
| `POST` | `/api/job-descriptions/upload` | Bearer | Upload & parse target JD PDF | `multipart/form-data` (`file`) | `201 Created`: `JobDescriptionResponse` (skills) |
| `GET` | `/api/job-descriptions/current`| Bearer | Get active JD metadata & skills | None | `200 OK`: `JobDescriptionResponse` |
| `GET` | `/api/job-descriptions/mapping`| Bearer | Get Resume vs JD skill mapping | None | `200 OK`: `{ matched_skills, gap_skills, interview_skills }` |
| `POST` | `/api/interviews/start` | Bearer | Initialize session & generate Q1 | `{ resume_id, difficulty, question_type, selected_skills, mode }` | `201 Created`: `{ session_id, current_question, current_bloom_level }` |
| `POST` | `/api/interviews/{id}/questions/{qid}/answer` | Bearer | Submit answer & receive evaluation | `{ answer_text }` | `200 OK`: `{ evaluation, next_question, is_complete }` |
| `POST` | `/api/interviews/{id}/complete` | Bearer | Complete interview manually | Path param: `id` | `200 OK`: `SessionResultsResponse` |
| `GET` | `/api/interviews/{id}/results` | Bearer | Get post-interview score breakdown | Path param: `id` | `200 OK`: `{ overall_average_score, skill_breakdown, recommendations }` |
| `GET` | `/api/interviews/history` | Bearer | List past interview sessions | None | `200 OK`: `List[HistoryItem]` |
| `POST` | `/api/interviews/upload-syllabus`| Bearer | Ingest course files into temp RAG | `multipart/form-data` (`files`) | `200 OK`: `{ syllabus_id, subject, topics, chunks_count }` |
| `GET` | `/api/users/profile` | Bearer | Get user profile and stats | None | `200 OK`: `{ user, resume, stats }` |
| `PUT` | `/api/users/profile` | Bearer | Update user account name | `{ name }` | `200 OK`: `{ id, name, email }` |
| `GET` | `/api/users/performance` | Bearer | Longitudinal cross-interview analytics | None | `200 OK`: `PerformanceResponse` (has_data, overall_average) |
| `GET` | `/api/health` | Public | System health check | None | `200 OK`: `{ status: "ok", service: "SmartInterview API" }` |

---

## 22. User Workflow (Illustrative Example: Alex Chen)

To illustrate the complete operational lifecycle, consider **Alex Chen**, an illustrative candidate preparing for a Senior Backend Engineer role:

```
[Candidate Alex Chen] -> Register / Login at http://localhost:5174
       ↓
[Resume Upload] -> Uploads 'alex_chen_resume.pdf'
       ↓ (PyMuPDF extracts: Name='Alex Chen', 19 skills: Python, FastAPI, Go, PostgreSQL, Docker...)
[JD Upload] -> Uploads 'senior_backend_jd.pdf'
       ↓ (Extracts 14 skills; System computes: Group A Overlap=11, Group B Gaps=3)
[Interview Setup] -> Selects skills ['Python', 'FastAPI', 'PostgreSQL', 'Docker'], clicks Start
       ↓
[Question 1] -> Python / Remember: "What is the Global Interpreter Lock (GIL) in CPython, and why does it exist for threading?"
       ↓
[Answer 1] -> Alex explains async/await instead of GIL -> Evaluator scores 16% (Irrelevant answer detected)
       ↓
[Adaptive Decision] -> Score < 50% & at Remember (min Bloom): Maintains Remember; rotates to 'FastAPI'
       ↓
[Question 2] -> FastAPI / Remember: "Define a FastAPI dependency, and explain the syntax used to declare it in a path operation function."
       ↓
[Answer 2] -> Alex provides thorough explanation with Depends() -> Evaluator scores 88%
       ↓
[Adaptive Decision] -> Score >= 80%: Advances Bloom to 'Understand' (Level 2); rotates to 'PostgreSQL'
       ↓
[Manual Finish] -> Alex clicks "Finish Interview" -> Session marked completed with completion_reason='manual'
       ↓
[Results Dashboard] -> Displays average score, per-skill progress bars, cognitive milestones, and recommendations
```

---

## 23. Implementation Details

### Configuration Management (`backend/app/config.py`):
- `DATABASE_URL`: MySQL connection URI (`mysql+pymysql://root:***@localhost:3306/smartinterview`) with connection pooling (`pool_pre_ping=True`, `pool_recycle=3600`).
- `GROQ_API_KEY`, `GROQ_MODEL`: Cloud inference credentials (`openai/gpt-oss-120b`).
- `CHROMA_DB_DIR`: Persistent path `chroma_db/`.
- `UPLOAD_DIR`, `SYLLABUS_UPLOAD_DIR`: Local directories for document storage.

### Singleton Management (`backend/app/services/question_service.py`):
Thread-safe, lazy-initialized singletons prevent re-loading heavy machine learning models on every HTTP request:
- `_embedding_model`: Initialized once (`SentenceTransformer("all-MiniLM-L6-v2")`).
- `_chroma_collection`: Persistent connection to `technical_kb`.
- `_groq_client`: Initialized Groq API client with model fallback handling.

---

## 24. Testing and Validation

A dedicated test suite was executed across all platform layers. All tests below were genuinely executed against the active codebase:

### 1. Authentication Test Cases
- **Valid Registration**: `POST /api/auth/register` $\rightarrow$ Status `201 Created`, valid JWT returned. [VERIFIED]
- **Duplicate Registration**: Re-registering existing email $\rightarrow$ Status `400 Bad Request` ("Email already registered"). [VERIFIED]
- **Valid Login**: `POST /api/auth/login` with correct password $\rightarrow$ Status `200 OK`, valid JWT returned. [VERIFIED]
- **Invalid Password**: `POST /api/auth/login` with bad password $\rightarrow$ Status `401 Unauthorized`. [VERIFIED]
- **Protected Endpoint Access**: `GET /api/auth/me` without token $\rightarrow$ Status `403 Forbidden` / `401 Unauthorized`. [VERIFIED]
- **Identity Resolution**: `GET /api/auth/me` with Bearer token $\rightarrow$ Correct candidate user object returned. [VERIFIED]

### 2. Resume & JD Parsing Test Cases
- **Resume Parsing**: Tested on `scratch/alex_chen_resume.pdf` $\rightarrow$ Extracted Name: "Alex Chen", 19 skills, 2 projects. [VERIFIED]
- **Header/Footer Cleaning**: Multi-page pagination lines stripped cleanly. [VERIFIED]
- **JD Upload & Skill Filtering**: Tested on `scratch/senior_backend_jd.pdf` $\rightarrow$ Extracted 14 technical skills, non-technical sections filtered. [VERIFIED]
- **Skill Mapping**: Verified Group A (11 matched skills) and Group B (3 gap skills: Prometheus, OpenTelemetry, Grafana). [VERIFIED]

### 3. Adaptive Engine Boundary Test Cases
- **Boundary 79 vs 80**: Score 79 maintains level; Score 80 advances Bloom level. [VERIFIED]
- **Boundary 50 vs 49**: Score 50 maintains level; Score 49 regresses Bloom level. [VERIFIED]
- **Minimum Bloom Limit**: Score 20 at Remember maintains Remember; lowers difficulty to `easy`. [VERIFIED]
- **Minimum Difficulty Limit**: Score 20 at Easy remains `easy` (cannot drop below Easy). [VERIFIED]
- **Maximum Bloom Limit**: Score 90 at Create maintains Create; advances difficulty to `hard`. [VERIFIED]
- **Maximum Difficulty Limit**: Score 95 at Hard remains `hard` (cannot advance above Hard). [VERIFIED]
- **Weakness-Biased Skill Selection**: Among equally attempted skills, skill with lowest average score is selected. [VERIFIED]

### 4. Auto-Stop & Safety Limit Test Cases
- **Insufficient Question Count**: 4 questions answered with 3 consecutive fails $< 40\%$ at Easy $\rightarrow$ Auto-stop does NOT trigger (requires $\ge 5$). [VERIFIED]
- **Non-Easy Difficulty**: 5 questions answered with 3 consecutive fails at Medium $\rightarrow$ Auto-stop does NOT trigger (requires difficulty Easy). [VERIFIED]
- **Fundamental Struggle Trigger**: 5 questions answered, difficulty Easy, last 3 scores $< 40\%$ $\rightarrow$ Auto-stop triggers; `completion_reason = "auto_stop_fundamental_struggle"`. [VERIFIED]
- **Safety Boundary**: `MAX_ADAPTIVE_QUESTIONS = 30` halts infinite interview loops; `completion_reason = "max_questions_safety_limit"`. [VERIFIED]
- **Manual Completion**: Clicking Finish marks session completed with `completion_reason = "manual"`. [VERIFIED]

### 5. Answer Evaluation Test Cases
- **Irrelevant Answer**: Tested GIL question with async/await answer $\rightarrow$ Awarded 16/100; weaknesses correctly flagged irrelevance. [VERIFIED]
- **High-Quality Answer**: Tested question with technically complete answer $\rightarrow$ Evaluator awarded high technical and semantic similarity scores. [VERIFIED]
- **Formula Verification**: Programmatic calculation confirmed: $0.30 \times \text{Tech} + 0.20 \times \text{Comp} + 0.20 \times \text{Rel} + 0.15 \times \text{SemSim} + 0.15 \times \text{ConceptCov}$ matches reported overall score. [VERIFIED]

### 6. Syllabus Mode Test Cases
- **Multi-File Ingestion**: Ingested sample text $\rightarrow$ Inferred subject and curriculum topics. [VERIFIED]
- **Temporary Isolation**: Chunks stored in isolated collection `temp_syllabus_{id}`; verified count. [VERIFIED]
- **Topic Selection**: Verified breadth-first selection followed by uncovered topics. [VERIFIED]
- **Lifecycle Cleanup**: `delete_temporary_rag()` dropped temporary collection from ChromaDB without residual artifacts. [VERIFIED]

---

## 25. Experimental Results

The following metrics represent actual empirical measurements obtained during platform execution:

### 1. Knowledge Base Quality Audit (`scripts/validate_repository.py`)
- **Total Processed Files**: 50 JSON files
- **Total Knowledge Base Domains**: 8 domains
- **Total Canonical Concepts**: 50 concepts
- **Total Chunks**: 402 chunks
- **Unique Chunk IDs**: 402 (0 duplicate IDs)
- **Token Bounds**: Minimum 50 tokens, Maximum 385 tokens, Mean 195.47 tokens

### 2. Information Retrieval Accuracy (`scripts/evaluate_retrieval.py`)
Evaluated across 33 domain queries from `data/evaluation/retrieval_queries.json`:
- **Hit@1**: 96.97% (32 of 33 queries returned expected concept at rank 1)
- **Hit@3**: 100.00% (33 of 33 queries returned expected concept within top 3)
- **Hit@5 (Recall@5)**: 100.00%
- **Mean Reciprocal Rank (MRR)**: 0.9798
- **Failed Queries**: 0

### 3. Execution Latency Profile (Observed During E2E Run)
- **Resume & JD PDF Ingestion**: $\approx 0.8 - 1.5$ seconds (PyMuPDF local CPU processing)
- **ChromaDB Vector Retrieval**: $\approx 15 - 45$ ms (top-3 semantic search with domain metadata filtering)
- **Groq LLM Question Generation**: $\approx 2.5 - 4.5$ seconds (cloud API inference, model `openai/gpt-oss-120b`)
- **Answer Evaluation (Groq LLM + SBERT Cosine)**: $\approx 3.5 - 6.0$ seconds (includes LLM JSON critique + PyTorch cosine embedding calculation)

*Human Correlation Validation Note*: Direct statistical correlation (Pearson/Spearman $r$) between automated scores and human expert interviewers has not been measured under controlled double-blind conditions and remains future work.

---

## 26. Performance Analysis

1. **Inference Latency Breakdown**:
   - The primary latency component during the interview loop is cloud LLM generation via Groq ($\approx 70\%$ of total step time).
   - Local operations (MySQL queries, SBERT vector embeddings, ChromaDB search) execute in under 100 ms combined, confirming the viability of a zero-budget architecture on student hardware.
2. **Stateless Backend Throughput**:
   - Because `AdaptiveState` is fully serialized into MySQL JSON columns on each turn, FastAPI server instances maintain no in-memory session state between turns. Any worker thread can process any turn for any user.
3. **Storage Scalability**:
   - 402 chunks in ChromaDB consume under 15 MB on disk.
   - User interview sessions (including questions, answers, and evaluations) require an average of 4 KB of MySQL storage per turn.

---

## 27. Limitations and Technical Debt

1. **Cloud LLM Dependency**: Relies on the external Groq API (`openai/gpt-oss-120b`). API rate limits, network outages, or model deprecations can affect availability. Mitigated by exponential retry backoff.
2. **Heuristic Document Parsing**: PyMuPDF and regex parsing rely on standard resume layouts. Highly stylized, multi-column, or graphic-heavy resumes can occasionally misclassify section boundaries.
3. **Browser `localStorage` Token Storage**: Storing JWT access tokens in browser `localStorage` simplifies development but is vulnerable to hypothetical Cross-Site Scripting (XSS).
4. **No Multi-Tab Session Isolation**: `localStorage` is scoped per origin; logging in as a different user in a second browser tab overwrites the active session token for the first tab.
5. **Absence of Audio / Vision Processing**: Spoken voice interaction (STT/TTS) and video facial analysis are not implemented in the current codebase.

---

## 28. Future Enhancements

1. **Speech-to-Text (STT) and Text-to-Speech (TTS)**: Integration of lightweight local speech models (e.g., Whisper.cpp) and browser-native SpeechSynthesis to support voice-based mock interviews.
2. **Real-Time Question Timer**: Configurable countdown timers per question (e.g., 2 minutes for conceptual, 5 minutes for scenario) with auto-submission upon timeout.
3. **Secure Cookie Authentication**: Transition from `localStorage` to `HttpOnly`, `SameSite=Strict` cookies with CSRF protection and Redis-backed refresh token rotation.
4. **Semantic Response Caching**: Use Redis or a vector cache to cache evaluations of recurring standard answers across users, reducing LLM API calls.
5. **Double-Blind Human Validation**: Conduct a formal academic study comparing automated scores against senior engineering interviewers across a benchmark cohort of candidates.

---

## 29. Conclusion

SmartInterview demonstrates that an effective, adaptive, and grounded technical interview platform can be engineered without expensive enterprise infrastructure or proprietary API costs. By grounding generative language models in a domain-filtered vector database (ChromaDB) and governing interview flow through deterministic Python state machines (Bloom's Taxonomy and weakness-biased round-robin), the system eliminates arbitrary grading and reduces the risk of technical hallucination.

The platform successfully satisfies all academic and technical objectives, providing candidates with a personalized, scaffolded, and measurable mock interview experience.

---

## 30. References

1. **Anderson, L. W., & Krathwohl, D. R.** (2001). *A taxonomy for learning, teaching, and assessing: A revision of Bloom's taxonomy of educational objectives*. Longman.
2. **Reimers, N., & Gurevych, I.** (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP).
3. **Lewis, P., et al.** (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. Advances in Neural Information Processing Systems (NeurIPS), 33, 9459-9474.
4. **ChromaDB Development Team**. (2024). *Chroma: The AI-native open-source embedding database*. https://docs.trychroma.com/
5. **Tiangolo, S.** (2024). *FastAPI: High performance, easy to learn, fast to code, ready for production*. https://fastapi.tiangolo.com/
6. **McKerns, M., et al.** (2024). *PyMuPDF: High-performance PDF parsing and rendering*. https://pymupdf.readthedocs.io/
7. **Groq Inc.** (2024). *LPU Inference Engine and API Reference*. https://groq.com/
8. **MySQL AB & Oracle Corporation**. (2024). *MySQL 8.0 Reference Manual: JSON Data Type and InnoDB Storage Engine*. Oracle.

---

## 31. Appendix

### Appendix A: Reproducibility & Setup Instructions

#### 1. Prerequisites
- Python 3.10+ installed and added to PATH.
- Node.js 18+ and npm installed.
- MySQL 8.0 Server running on `localhost:3306` with database `smartinterview`.

#### 2. Environment Configuration (`.env`)
Create `.env` in the repository root:
```ini
# Groq Cloud API
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Local MySQL Database
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/smartinterview

# JWT Security
JWT_SECRET_KEY=your-secure-random-secret-key-for-development
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

#### 3. Database Initialization
```bash
# Execute schema migration scripts
mysql -u root -p smartinterview < backend/setup_database.sql
mysql -u root -p smartinterview < backend/setup_database_v2.sql
mysql -u root -p smartinterview < backend/setup_database_v3.sql
mysql -u root -p smartinterview < backend/setup_database_v4.sql
mysql -u root -p smartinterview < backend/setup_database_v5.sql
```

#### 4. Vector Database Ingestion (402 Baseline Chunks)
```bash
python scripts/ingest_vector_db.py
python scripts/validate_repository.py
python scripts/evaluate_retrieval.py
```

#### 5. Running the Backend
```bash
# From repository root
.\start_backend.ps1
# Or directly via uvicorn:
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation available at: `http://localhost:8000/docs`

#### 6. Running the Frontend
```bash
# From repository root
.\start_frontend.ps1
# Or directly via npm:
cd frontend
npm install
npm run dev
```
Application accessible in browser at: `http://localhost:5174`

---

### Appendix B: Verification Checklist & Screenshots Guide

The following screenshots correspond to pages and interfaces verified in the active codebase:
1. **Landing Page (`/`)**: Public overview, platform features, and navigation bar.
2. **Registration Page (`/register`)**: Account creation form with name, email, password, and confirm password fields.
3. **Login Page (`/login`)**: Authentication form with credential validation.
4. **Dashboard Page (`/dashboard`)**: Candidate greeting, preparation summary stats, and quick-action navigation cards.
5. **Resume & JD Upload Page (`/resume`)**: Dual upload dropzones for PDF resume and target Job Description.
6. **Skill Mapping View (`/resume`)**: Categorized visualization of Group A (Overlap) and Group B (Gaps).
7. **Interview Setup Page (`/setup`)**: Interactive skill selection checkboxes and difficulty selector.
8. **Interview Active Screen (`/interview/:id`)**: Real-time interface showing question text, Bloom cognitive level badge, difficulty badge, and answer textarea.
9. **Answer Evaluation Modal (`/interview/:id`)**: Real-time evaluation breakdown displaying 5 sub-scores, feedback, strengths, and weaknesses.
10. **Results Page (`/results/:id`)**: Comprehensive post-interview report with overall percentage, per-skill mastery bars, cognitive milestones, and recommendations.
11. **History Page (`/history`)**: Chronological table of past interviews with status, dates, scores, and review links.
12. **Performance Analytics Dashboard (`/performance`)**: Longitudinal multi-interview metrics, strengths, and weak areas.
13. **Syllabus Upload Page (`/syllabus`)**: Coursework material ingestion view with detected topics and stage timing metrics.

---
*Report compiled directly against active repository code: `Smart-Interview-main`.*
