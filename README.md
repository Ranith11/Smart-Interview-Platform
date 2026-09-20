# SmartInterview

**AI-Powered Adaptive Technical Mock Interview Platform**

SmartInterview is a full-stack web application that conducts realistic, AI-driven technical mock interviews. It parses candidate resumes, retrieves relevant technical knowledge via RAG (Retrieval-Augmented Generation), generates adaptive interview questions using Bloom's Taxonomy progression, evaluates answers with multi-signal scoring, and provides detailed performance analytics — all designed to prepare candidates for real-world technical interviews.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Interview Modes](#interview-modes)
- [System Architecture](#system-architecture)
- [AI / RAG Architecture](#ai--rag-architecture)
- [Knowledge Base Flow](#knowledge-base-flow)
- [Adaptive Interview Engine](#adaptive-interview-engine)
- [Answer Evaluation](#answer-evaluation)
- [Speech-to-Text](#speech-to-text)
- [Performance Dashboard](#performance-dashboard)
- [End-to-End Flow](#end-to-end-flow)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Security](#security)
- [Testing](#testing)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)

---

## Overview

Technical interviews are high-stakes, and most candidates lack access to structured, personalized practice with real-time feedback. Generic question banks don't adapt to a candidate's skill level, and human mock interviewers are expensive and inconsistent.

SmartInterview solves this by providing:

- **Personalized interviews** derived from the candidate's actual resume (skills, projects, experience)
- **RAG-grounded questions** backed by a curated technical knowledge base, not hallucinated by an LLM
- **Adaptive difficulty** that progresses through Bloom's Taxonomy cognitive levels based on real performance
- **Structured evaluation** with multi-dimensional scoring and actionable feedback
- **Three interview modes** — Normal (resume-based), Job-Specific (resume + JD matching), and Syllabus-Based (academic material)
- **Local Speech-to-Text** for voice-based answering without sending audio to external cloud APIs

---

## Key Features

- **Resume Parsing** — Upload a PDF resume; the system extracts skills, projects, experience, and education using PyMuPDF and structured pattern matching (Groq LLM-assisted)
- **RAG-Based Question Generation** — Questions are grounded in retrieved technical knowledge chunks from ChromaDB, not generated from LLM memory alone
- **Adaptive Learning Engine** — Deterministic progression through Bloom's Taxonomy (Remember → Understand → Apply → Analyze → Evaluate → Create) based on per-skill performance scores
- **Multi-Signal Answer Evaluation** — Combines LLM-based evaluation (technical correctness, completeness, relevance), semantic similarity (Sentence-BERT), and concept coverage into a weighted overall score
- **Three Interview Modes** — Normal, Job-Specific, and Syllabus-Based
- **Job Description Analysis** — SBERT-based semantic matching between resume skills and JD requirements with required/preferred classification
- **Syllabus Material Processing** — Upload PDF/TXT/DOCX academic material; the system chunks, embeds, detects topics, and creates a temporary RAG collection
- **Knowledge Base Enrichment** — Upon syllabus interview completion, genuinely new concepts are merged into the permanent knowledge base with duplicate detection (cosine similarity > 0.85 threshold)
- **Local Speech-to-Text** — Uses `faster-whisper` running locally on CPU; no cloud transcription APIs
- **Performance Dashboard** — Aggregated analytics across all evaluated interviews with skill-wise breakdown, Bloom progression tracking, and AI-generated recommendations
- **Interview History & Results** — Per-session results with question-by-question evaluation, bloom progression charts, and skill performance breakdown
- **JWT Authentication** — Secure user registration/login with bcrypt password hashing

---

## Interview Modes

### Normal Technical Interview

The default mode. The interview scope is defined entirely by the candidate's resume.

```
Resume Upload
  → PDF text extraction (PyMuPDF)
  → Structured parsing (skills, projects, experience, education)
  → Candidate selects skills to focus on
  → Adaptive engine initializes (Bloom Level 1: Remember)
  → For each question:
      Skill → domain mapping → RAG retrieval from technical_kb
        → LLM generates question with Bloom-level guidance
        → Candidate answers (text or voice)
        → Multi-signal evaluation
        → Adaptive engine adjusts: next skill, Bloom level, difficulty
  → Interview completion → results + recommendations
```

Skills are rotated using weakness-biased round-robin: all selected skills get coverage, but weaker skills receive more attention.

### Job-Specific Interview

The interview scope is defined by the intersection of the candidate's resume and a Job Description.

```
Resume + Job Description (paste text or upload PDF/TXT)
  → LLM extracts JD requirements (skill, required/preferred, context)
  → SBERT semantic matching between resume skills and JD requirements
  → Relevance classification per skill:
      - Matching Skills (high/medium relevance) — resume skills that match JD requirements
      - JD-Only Skills — requirements in the JD but not on the resume
      - Non-Matching Resume Skills — resume skills unrelated to this JD (excluded from interview)
  → User reviews match analysis before starting
  → Eligible interview scope = matching skills + JD-only skills
  → Adaptive engine operates within this scope
  → For JD-only skills: questions avoid assuming candidate experience
```

**Key design decisions:**
- Unrelated resume skills are **excluded** from the interview scope. A candidate's Java skills are irrelevant if the JD is for a data science role.
- JD-only skills **can** still be asked about, but the question prompt explicitly instructs the LLM not to assume the candidate has direct experience.
- Job relevance is used as a **tiebreaker** in skill selection, not an override. Weakness priority still dominates — a weak matching skill is selected before a strong one regardless of relevance.
- The analysis result is cached server-side via an `analysis_id` and consumed exactly once when starting the interview.

### Syllabus-Based Interview

Designed for academic preparation. The interview is grounded in uploaded course material rather than the candidate's resume.

```
Upload syllabus files (PDF, TXT, or DOCX)
  → Text extraction → chunking (1000 chars, 200 overlap)
  → LLM infers subject and extracts topic list
  → Embeddings → temporary ChromaDB collection (temp_syllabus_<uuid>)
  → User selects topics and question count
  → Interview starts with deterministic topic rotation
  → Questions are generated from the temporary syllabus RAG
  → Evaluation proceeds normally (LLM + semantic similarity)
  → On completion:
      → Merge genuinely new concepts into permanent technical_kb
         (duplicate detection via cosine similarity > 0.85)
      → Delete temporary collection
```

**Important:** Syllabus Mode uses a **deterministic topic rotation** engine (fixed questions per topic), not the Bloom-based adaptive engine used by Normal and Job-Specific modes. This is by design — syllabus interviews assess topic coverage rather than cognitive progression.

---

## System Architecture

```mermaid
graph TB
    subgraph Frontend["React Frontend (Vite + Tailwind CSS)"]
        Landing[Landing Page]
        Auth[Login / Register]
        Dashboard[Dashboard]
        Resume[Resume Upload]
        Setup[Interview Setup]
        InterviewUI[Interview UI]
        ResultsUI[Results Page]
        HistoryUI[History Page]
        PerfDash[Performance Dashboard]
        Profile[Profile Page]
    end

    subgraph Backend["FastAPI Backend"]
        AuthRouter[Auth Router]
        ResumeRouter[Resume Router]
        InterviewRouter[Interview Router]
        SpeechRouter[Speech Router]
        UserRouter[User Router]
    end

    subgraph Services["Backend Services"]
        AuthService[Auth Service<br/>JWT + bcrypt]
        ResumeService[Resume Service<br/>PyMuPDF Parser]
        InterviewService[Interview Service<br/>Orchestrator]
        QuestionService[Question Service<br/>RAG + LLM]
        EvalService[Evaluation Service<br/>LLM + SBERT]
        AdaptiveEngine[Adaptive Engine<br/>Bloom Taxonomy]
        SyllabusEngine[Syllabus Engine<br/>Topic Rotation]
        JDService[JD Analysis Service<br/>SBERT Matching]
        SpeechService[Speech Service<br/>faster-whisper]
        SyllabusRAG[Syllabus RAG Service<br/>Chunking + Merge]
    end

    subgraph DataStores["Data Stores"]
        MySQL[(MySQL Database)]
        ChromaDB[(ChromaDB<br/>Vector Store)]
    end

    subgraph AI["AI / ML Services"]
        Groq[Groq API<br/>LLM]
        SBERT["Sentence-BERT<br/>(all-MiniLM-L6-v2)"]
        Whisper["faster-whisper<br/>(tiny.en)"]
    end

    Frontend --> Backend
    Backend --> Services
    Services --> DataStores
    Services --> AI
```

---

## AI / RAG Architecture

SmartInterview uses multiple AI components, each with a distinct responsibility:

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| **LLM** | Groq API (configurable model, default: `openai/gpt-oss-120b`) | Question generation, answer evaluation, JD parsing, concept extraction, subject inference |
| **Embedding Model** | Sentence-BERT (`all-MiniLM-L6-v2`) | Encoding text chunks and queries into vector embeddings for RAG retrieval and semantic similarity |
| **Vector Store** | ChromaDB (persistent, local) | Storing and retrieving embedded technical knowledge chunks |
| **Speech Model** | `faster-whisper` (`tiny.en` by default, configurable) | Local audio transcription on CPU |
| **PDF Extraction** | PyMuPDF (`pymupdf`) | Extracting text from PDF resumes and syllabus files |
| **DOCX Extraction** | `python-docx` | Extracting text from Word documents (syllabus uploads) |

### Question Generation Pipeline

```
Skill (from adaptive engine)
  → Resolve skill to knowledge domains (SKILL_DOMAIN_MAP)
  → Build RAG query for the skill
  → Retrieve top-3 relevant chunks from ChromaDB (domain-filtered)
  → Find matching project from candidate's resume (if any)
  → Build prompt: system prompt + skill + RAG context + project context
      + difficulty instruction + question type + dedup list
      + Bloom-level cognitive guidance
      + Job context (if Job-Specific mode)
  → Call Groq LLM → generated question text
```

### Evaluation Pipeline

```
Question + Candidate Answer + RAG Context
  → LLM Evaluation (Groq):
      → technical_score, completeness_score, relevance_score
      → concept_coverage_score
      → feedback, strengths, weaknesses
      → expected_concepts, found_concepts
  → Semantic Similarity (Sentence-BERT):
      → Cosine similarity between answer embedding and reference embedding
      → Nonlinear scaling to 0-100
  → Concept Coverage (hybrid):
      → Average of LLM-assessed coverage and calculated (found/expected) ratio
  → Weighted Overall Score
```

---

## Knowledge Base Flow

### Permanent Knowledge Base (`technical_kb`)

The permanent ChromaDB collection contains pre-ingested technical knowledge organized by domain and concept.

```
Technical source documents
  → Text extraction
  → Chunking (scripts/chunk_text.py)
  → Embedding (all-MiniLM-L6-v2)
  → Stored in ChromaDB collection "technical_kb"
      with metadata: domain, concept, source, source_url
```

The `SKILL_DOMAIN_MAP` in `generate_question.py` maps resume skills (e.g., "Python", "React", "SQL") to relevant knowledge domains (e.g., "dsa", "oop", "dbms"), ensuring RAG retrieval is filtered to the most relevant chunks.

### Temporary Syllabus Collections (`temp_syllabus_<uuid>`)

Syllabus uploads create isolated temporary ChromaDB collections:

```
Syllabus file(s) upload
  → Text extraction (PDF/TXT/DOCX)
  → Chunking (1000 chars, 200 char overlap)
  → LLM concept extraction (batched, 10 chunks at a time)
  → Embedding (all-MiniLM-L6-v2)
  → Stored in "temp_syllabus_<uuid>" collection
```

### Merge on Completion

When a syllabus interview completes (naturally or manually):

```
For each chunk in temp_syllabus_<uuid>:
  → Query permanent technical_kb for nearest neighbor
  → Compute cosine similarity
  → If similarity > 0.85 → IGNORE (duplicate)
  → If similarity ≤ 0.85 → ADD to permanent technical_kb
  → Delete temporary collection
```

This ensures the permanent knowledge base grows with genuinely new material while avoiding redundancy. Merged knowledge is then available for future RAG retrieval in all interview modes.

---

## Adaptive Interview Engine

The adaptive engine is a **deterministic, rule-based system** implemented entirely in Python. The LLM does **not** decide interview progression — it only generates questions within the parameters the engine sets.

### Bloom's Taxonomy Levels

| Order | Level | Description | Preferred Question Type |
|-------|-------|-------------|------------------------|
| 1 | **Remember** | Recall facts, definitions, terminology | conceptual |
| 2 | **Understand** | Explain concepts, summarize, interpret | conceptual |
| 3 | **Apply** | Use knowledge in practical situations | practical |
| 4 | **Analyze** | Compare approaches, break down problems | technical_reasoning |
| 5 | **Evaluate** | Judge solutions, justify decisions | scenario |
| 6 | **Create** | Design new solutions, propose architectures | project |

### Progression Rules

| Score Range | Action |
|------------|--------|
| **≥ 80** | Advance Bloom level (if already at Create, advance difficulty: easy → medium → hard) |
| **50–79** | Maintain current level (no change) |
| **< 50** | Regress Bloom level (if already at Remember, reduce difficulty if possible) |

### Skill Selection Strategy

The engine uses **weakness-biased round-robin**:

1. Find skills with the fewest attempts (ensure coverage)
2. Among equally-attempted skills, prefer the weakest (lowest average score)
3. In Job-Specific mode, an additional tiebreaker favors higher job-relevance, but weakness priority always dominates

### Scope vs. Engine Separation

- **Scope** defines *what* skills are eligible for the interview (set once at creation)
- **Engine** decides *which* skill to ask next and *how* to ask it (runs after each answer)

| Mode | Scope Source |
|------|-------------|
| Normal | Resume skills selected by the candidate |
| Job-Specific | Matching resume skills + JD-only skills (unrelated resume skills excluded) |
| Syllabus | Topics extracted from uploaded material (uses separate deterministic engine) |

---

## Answer Evaluation

Each answer is evaluated using three independent signals combined into a weighted overall score.

### Scoring Formula

```
overall = 0.30 × technical_score
        + 0.20 × completeness_score
        + 0.20 × relevance_score
        + 0.15 × semantic_similarity_score
        + 0.15 × concept_coverage_score
```

All individual scores are 0–100 integers.

### Evaluation Components

| Component | Source | What It Measures |
|-----------|--------|-----------------|
| **Technical Score** | LLM (Groq) | Correctness of the technical content |
| **Completeness Score** | LLM (Groq) | How thoroughly the answer covers the topic |
| **Relevance Score** | LLM (Groq) | How relevant the answer is to the specific question |
| **Semantic Similarity** | Sentence-BERT | Cosine similarity between answer and reference context embeddings |
| **Concept Coverage** | Hybrid (LLM + calculated ratio) | How many expected key concepts are present in the answer |

### Qualitative Feedback

Each evaluation also includes:
- **Feedback** — 2-4 sentences of constructive, question-specific feedback
- **Strengths** — 1-3 specific things the candidate did well
- **Weaknesses** — 1-3 specific areas for improvement
- **Expected Concepts** — Key technical concepts a good answer should mention
- **Found Concepts** — Which expected concepts were actually present

> **Note:** Semantic similarity measures semantic closeness between the candidate's answer and the reference knowledge. It does not by itself establish technical correctness — that primarily comes from the LLM evaluation.

---

## Speech-to-Text

SmartInterview provides local, on-device speech-to-text during interviews.

### Architecture

| Layer | Implementation |
|-------|---------------|
| **Audio Capture** | Browser `MediaRecorder` API with WebM/Opus encoding |
| **Voice Activity Detection** | Client-side frequency analysis (Web Audio API, `AnalyserNode`); 1000ms silence threshold segments speech |
| **Progressive Transcription** | Audio chunks sent to backend every 1000ms for interim display; full segment sent on voice pause for final transcription |
| **Backend Transcription** | `faster-whisper` model running locally on CPU |
| **Model** | Default: `tiny.en` (configurable via `STT_MODEL_SIZE` env var) |

### Flow

```
User clicks microphone → browser requests mic permission
  → MediaRecorder captures audio in WebM format
  → Web Audio API analyser monitors frequency for VAD
  → While speaking: progressive chunks sent for interim transcription
  → On 1000ms silence: segment finalized and sent for final transcription
  → Transcribed text appended to the answer field
  → User can continue speaking (new segment) or stop recording
```

**Key implementation details:**
- Audio is processed entirely locally — no external cloud APIs (e.g., Google Cloud Speech, AWS Transcribe) are used
- VAD with backpressure prevents concurrent interim requests from overwhelming the CPU
- Segment versioning prevents stale out-of-order responses from overwriting newer transcriptions
- Per-question session IDs ensure transcription results are not applied to the wrong question

---

## Performance Dashboard

The performance dashboard aggregates data from all completed, evaluated interviews.

### Metrics Displayed

| Metric | Description |
|--------|-------------|
| **Overall Average Score** | Weighted average across all evaluated answers |
| **Skill-wise Performance** | Per-skill average score and number of questions answered |
| **Highest Bloom Level** | Per-skill maximum Bloom taxonomy level reached |
| **Bloom Progression** | Per-question Bloom level progression across sessions |
| **Bloom Performance** | Average score at each Bloom cognitive level |
| **Strong Skills** | Skills averaging ≥ 75% |
| **Areas to Improve** | Skills averaging < 50% |
| **AI Recommendations** | Personalized per-skill recommendations from completed sessions |
| **Recent Interviews** | List of completed sessions with score, skills, mode, and date |

### Mode Filtering

The dashboard supports mode filtering:
- By default, only Normal and Job-Specific mode interviews are included (Syllabus mode is excluded from Bloom analytics since it uses deterministic topic rotation, not Bloom progression)
- Users can filter to view performance for a specific mode

---

## End-to-End Flow

### Normal Mode

```
Register / Login
  → Upload Resume (PDF)
  → Resume parsed: skills, projects, experience, education extracted
  → Navigate to Interview Setup
  → Select mode: Normal
  → Select skills, difficulty, question type
  → Start Interview
  → Question 1 generated (Bloom: Remember, adaptive engine)
  → Answer via text or voice → Evaluation → Feedback shown
  → Adaptive engine decides next: skill, Bloom level, difficulty
  → Question 2 generated → Answer → Evaluate → Adapt → ...
  → User clicks "End Interview" or safety limit (30 questions) reached
  → Final results: overall score, skill breakdown, Bloom progression, recommendations
  → Results available in History
  → Performance Dashboard updated
```

### Job-Specific Mode

```
Register / Login
  → Upload Resume
  → Navigate to Interview Setup
  → Select mode: Job-Specific
  → Paste/upload Job Description
  → Click "Analyze" → LLM extracts JD requirements → SBERT matches against resume
  → Review: matching skills, JD-only skills, non-matching skills
  → Start Interview (scope = matching + JD-only)
  → Adaptive interview loop (same as Normal, within JD-defined scope)
  → Results + recommendations
```

### Syllabus Mode

```
Register / Login
  → Upload Resume (required for session association)
  → Navigate to Interview Setup
  → Select mode: Syllabus
  → Upload syllabus file(s) (PDF, TXT, DOCX)
  → System infers subject, extracts topics, creates temporary RAG
  → Select topics and question count
  → Start Interview
  → Deterministic topic rotation (N questions per topic)
  → Questions grounded in syllabus RAG → Answer → Evaluate
  → On completion: merge new knowledge into permanent KB → cleanup temp collection
  → Results + recommendations
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | React (via Vite) | Single-page application UI |
| **Styling** | Tailwind CSS v4 | Utility-first responsive styling |
| **Routing** | React Router v7 | Client-side navigation |
| **HTTP Client** | Axios | API communication with JWT interceptor |
| **Icons** | Lucide React | UI iconography |
| **Typography** | Inter (Google Fonts) | Application typeface |
| **Backend Framework** | FastAPI | Async Python API server |
| **ASGI Server** | Uvicorn | Production-grade async server |
| **ORM** | SQLAlchemy 2.0 | Database models and queries |
| **Database** | MySQL (via PyMySQL) | Persistent data storage |
| **Validation** | Pydantic v2 | Request/response schema validation |
| **Authentication** | python-jose (JWT) + passlib/bcrypt | Token-based auth with password hashing |
| **LLM Provider** | Groq API | Question generation, evaluation, JD parsing |
| **Embedding Model** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Text embeddings for RAG and semantic similarity |
| **Vector Database** | ChromaDB | Persistent vector storage and retrieval |
| **PDF Extraction** | PyMuPDF (`pymupdf`) | Resume and syllabus PDF text extraction |
| **DOCX Extraction** | python-docx | Word document text extraction |
| **Speech-to-Text** | faster-whisper (`tiny.en`) | Local audio transcription |
| **Dev Proxy** | Vite proxy (`/api` → `localhost:8000`) | Seamless frontend-backend communication |

---

## Project Structure

```
SmartInterview/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI entry point
│   │   ├── config.py                    # Environment/path configuration
│   │   ├── database.py                  # SQLAlchemy engine and session setup
│   │   ├── dependencies/
│   │   │   └── auth.py                  # JWT authentication dependency
│   │   ├── models/
│   │   │   ├── user.py                  # User model
│   │   │   ├── resume.py                # Resume model
│   │   │   ├── interview.py             # InterviewSession model
│   │   │   └── question.py              # InterviewQuestion, Answer, AnswerEvaluation
│   │   ├── routers/
│   │   │   ├── auth.py                  # /api/auth — register, login, me
│   │   │   ├── resumes.py               # /api/resumes — upload, current, delete
│   │   │   ├── interviews.py            # /api/interviews — start, answer, complete, history, results
│   │   │   ├── users.py                 # /api/users — profile, stats, performance
│   │   │   └── speech.py                # /api/speech — transcribe
│   │   ├── schemas/
│   │   │   ├── auth.py                  # Auth request/response schemas
│   │   │   ├── interview.py             # Interview, evaluation, JD schemas
│   │   │   ├── resume.py                # Resume response schema
│   │   │   └── user.py                  # User profile, performance schemas
│   │   └── services/
│   │       ├── auth_service.py          # Password hashing, JWT, user management
│   │       ├── resume_service.py        # Resume parsing (wraps scripts/parse_resume.py)
│   │       ├── interview_service.py     # Session orchestration, results, performance
│   │       ├── question_service.py      # RAG retrieval + LLM question generation
│   │       ├── evaluation_service.py    # Multi-signal answer evaluation
│   │       ├── adaptive_engine.py       # Bloom-based adaptive progression
│   │       ├── bloom.py                 # Bloom's Taxonomy level definitions
│   │       ├── syllabus_engine.py       # Deterministic syllabus topic rotation
│   │       ├── syllabus_rag_service.py  # Syllabus text processing, temp RAG, merge
│   │       ├── jd_analysis_service.py   # JD parsing + SBERT skill matching
│   │       └── speech_service.py        # faster-whisper transcription
│   ├── setup_database.sql               # Initial MySQL schema (Week 7)
│   ├── setup_database_v2.sql            # Migration: adaptive + evaluation tables
│   ├── setup_database_v3.sql            # Migration: completion_reason column
│   ├── setup_database_v4.sql            # Migration: Job-Specific Mode columns
│   ├── requirements.txt                 # Python dependencies
│   └── e2e_api_test.py                  # End-to-end API test script
├── frontend/
│   ├── index.html                       # HTML entry point
│   ├── package.json                     # Node.js dependencies
│   ├── vite.config.js                   # Vite + Tailwind + proxy configuration
│   └── src/
│       ├── main.jsx                     # React DOM render
│       ├── App.jsx                      # Routes and layout
│       ├── index.css                    # Global styles
│       ├── context/
│       │   └── AuthContext.jsx          # Authentication state provider
│       ├── components/
│       │   ├── Navbar.jsx               # Top navigation bar
│       │   ├── Sidebar.jsx              # Side navigation
│       │   └── ProtectedRoute.jsx       # Auth guard
│       ├── hooks/
│       │   └── useSpeechToText.js       # VAD + MediaRecorder + backend STT hook
│       ├── pages/
│       │   ├── Landing.jsx              # Public landing page
│       │   ├── Login.jsx                # Login form
│       │   ├── Register.jsx             # Registration form
│       │   ├── Dashboard.jsx            # User dashboard
│       │   ├── ResumeUpload.jsx         # Resume upload + parsed data display
│       │   ├── InterviewSetup.jsx       # Mode selection, skill/JD/syllabus config
│       │   ├── Interview.jsx            # Live interview UI (questions, answers, STT)
│       │   ├── Results.jsx              # Per-session results and evaluation
│       │   ├── History.jsx              # Interview history list
│       │   ├── Profile.jsx              # User profile management
│       │   └── PerformanceDashboard.jsx # Aggregated performance analytics
│       └── services/
│           └── api.js                   # Axios instance with JWT interceptor
├── scripts/
│   ├── parse_resume.py                  # Standalone resume parser (Week 6)
│   ├── generate_question.py             # Standalone question generator (Week 6)
│   ├── chunk_text.py                    # Text chunking utility
│   ├── clean_text.py                    # Text cleaning utility
│   ├── extract_text.py                  # PDF text extraction
│   ├── ingest_vector_db.py              # ChromaDB ingestion script
│   ├── validate_chunks.py               # Chunk validation
│   ├── validate_repository.py           # Repository validation
│   ├── evaluate_retrieval.py            # RAG retrieval evaluation
│   └── test_retrieval.py                # Retrieval testing
├── prompts/
│   ├── question_generation.json         # System prompt + question type/difficulty templates
│   └── evaluation_prompts.json          # Evaluation system prompt + user template
├── chroma_db/                           # ChromaDB persistent storage
├── uploads/                             # User-uploaded files (resumes, syllabi)
├── data/                                # Data files (knowledge stats, raw sources)
├── docs/                                # Development documentation
├── .env.example                         # Environment variable template
├── start.bat                            # One-click startup script (Windows)
└── README.md
```

---

## Installation

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 18+ | Frontend build tooling |
| **MySQL** | 8.0+ | Relational database |
| **Git** | Any | Clone the repository |

> **Note:** `faster-whisper` requires C++ build tools on Windows. Install "Desktop development with C++" via Visual Studio Build Tools if you encounter compilation errors during `pip install`.

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/Smart-Interview.git
cd Smart-Interview
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Groq AI — Required for question generation and evaluation
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# MySQL Database
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/smartinterview

# JWT Authentication
JWT_SECRET_KEY=change-this-to-a-random-64-char-hex-string
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | **Yes** | API key from [Groq Console](https://console.groq.com/) |
| `GROQ_MODEL` | No | LLM model to use (default: `openai/gpt-oss-120b`) |
| `DATABASE_URL` | **Yes** | MySQL connection string |
| `JWT_SECRET_KEY` | **Yes** | Secret key for JWT token signing (use a random hex string in production) |
| `JWT_ALGORITHM` | No | JWT algorithm (default: `HS256`) |
| `JWT_EXPIRATION_MINUTES` | No | Token expiration in minutes (default: `1440` = 24 hours) |
| `STT_MODEL_SIZE` | No | faster-whisper model size (default: `tiny.en`). Options: `tiny.en`, `base.en`, `small.en`, etc. |
| `STT_DEVICE` | No | Compute device for STT (default: `cpu`) |
| `STT_COMPUTE_TYPE` | No | Compute type for STT (default: `int8`) |

### 3. Database Setup

Create the MySQL database and apply all migrations in order:

```bash
mysql -u root -p < backend/setup_database.sql
mysql -u root -p < backend/setup_database_v2.sql
mysql -u root -p < backend/setup_database_v3.sql
mysql -u root -p < backend/setup_database_v4.sql
```

### 4. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Project

### Option A: One-Click Start (Windows)

The `start.bat` script handles both backend and frontend:

```bash
start.bat
```

This will:
1. Create/activate a Python virtual environment in `backend/`
2. Install backend dependencies if missing
3. Start the FastAPI backend in a new terminal window
4. Install frontend dependencies if missing
5. Start the Vite dev server in a new terminal window

### Option B: Manual Start

**Terminal 1 — Backend:**

```bash
cd backend
venv\Scripts\activate          # or source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

### Access Points

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/api/health |

> The Vite dev server proxies all `/api` requests to `localhost:8000`, so the frontend communicates with the backend seamlessly.

---

## API Documentation

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/register` | Register a new user | No |
| `POST` | `/api/auth/login` | Login and receive JWT token | No |
| `GET` | `/api/auth/me` | Get current authenticated user | Yes |

### Resumes

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/resumes/upload` | Upload and parse a PDF resume (max 5MB) | Yes |
| `GET` | `/api/resumes/current` | Get the current user's latest resume | Yes |
| `DELETE` | `/api/resumes/{id}` | Delete a resume | Yes |

### Interviews

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/interviews/start` | Start a new adaptive interview (returns first question) | Yes |
| `POST` | `/api/interviews/upload-syllabus` | Upload syllabus files and get topic list | Yes |
| `POST` | `/api/interviews/extract-jd` | Extract text from a JD file (PDF/TXT/MD) | Yes |
| `POST` | `/api/interviews/analyze-jd` | Analyze JD against resume skills | Yes |
| `GET` | `/api/interviews/history` | List all user's interview sessions | Yes |
| `GET` | `/api/interviews/{id}` | Get interview session with questions | Yes |
| `GET` | `/api/interviews/{id}/results` | Get detailed results for a session | Yes |
| `GET` | `/api/interviews/{id}/questions/{num}` | Get a single question (legacy) | Yes |
| `POST` | `/api/interviews/{id}/questions/{question_id}/answer` | Submit answer → evaluate → generate next question | Yes |
| `POST` | `/api/interviews/{id}/complete` | Mark interview as completed | Yes |

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/users/profile` | Get user profile with stats and resume | Yes |
| `PUT` | `/api/users/profile` | Update user name | Yes |
| `GET` | `/api/users/stats` | Get basic interview statistics | Yes |
| `GET` | `/api/users/performance` | Get aggregated performance data (supports `?mode=` filter) | Yes |

### Speech

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/speech/transcribe` | Transcribe an audio file (max 5MB) | Yes |

### Health

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/health` | Service health check | No |

---

## Database Schema

```mermaid
erDiagram
    users ||--o{ resumes : has
    users ||--o{ interview_sessions : has
    resumes ||--o{ interview_sessions : used_in
    interview_sessions ||--o{ interview_questions : contains
    interview_sessions ||--o{ answers : contains
    interview_questions ||--o| answers : has
    interview_questions ||--o| answer_evaluations : has
    answers ||--o| answer_evaluations : has

    users {
        int id PK
        varchar name
        varchar email UK
        varchar password_hash
        datetime created_at
        datetime updated_at
    }

    resumes {
        int id PK
        int user_id FK
        varchar filename
        varchar file_path
        json skills
        json projects
        json experience
        json education
        text raw_text
        int page_count
        datetime uploaded_at
    }

    interview_sessions {
        int id PK
        int user_id FK
        int resume_id FK
        enum difficulty
        varchar question_type
        int question_count
        json selected_skills
        enum status
        boolean is_adaptive
        json adaptive_state
        varchar current_bloom_level
        json final_recommendations
        varchar completion_reason
        varchar mode
        varchar syllabus_id
        json syllabus_state
        text job_description_text
        varchar job_description_title
        json job_relevance_data
        datetime started_at
        datetime completed_at
    }

    interview_questions {
        int id PK
        int session_id FK
        int question_number
        varchar skill
        varchar question_type
        enum difficulty
        text question_text
        json rag_context
        json project_context
        varchar bloom_level
        int bloom_level_number
        datetime created_at
    }

    answers {
        int id PK
        int question_id FK
        int session_id FK
        int user_id FK
        text answer_text
        datetime submitted_at
    }

    answer_evaluations {
        int id PK
        int answer_id FK
        int question_id FK
        int technical_score
        int completeness_score
        int relevance_score
        int semantic_similarity_score
        int concept_coverage_score
        int overall_score
        text feedback
        json strengths
        json weaknesses
        json concepts_expected
        json concepts_found
        datetime evaluated_at
    }
```

---

## Security

The following security measures are implemented in the codebase:

| Measure | Implementation |
|---------|---------------|
| **Password Hashing** | bcrypt via `passlib` (72-byte limit enforced) |
| **Authentication** | JWT Bearer tokens with configurable expiration |
| **Token Storage** | `sessionStorage` (tab-isolated; cleared on browser close) |
| **Authorization** | All data-mutating endpoints verify `user_id` ownership |
| **Resume Ownership** | Resume queries filter by `user_id`; users can only access their own resumes |
| **Session Ownership** | Interview session queries filter by `user_id` |
| **File Upload Validation** | File type checks (PDF only for resumes; PDF/TXT/DOCX for syllabi), size limits (5MB resume, 20MB syllabus) |
| **Path Traversal Prevention** | `os.path.basename()` strips directory components from uploaded filenames |
| **Unique File Names** | Uploaded files are saved with `{user_id}_{uuid_hex}.pdf` to prevent collisions |
| **CORS** | Restricted to `localhost:5173` and `127.0.0.1:5173` (development) |
| **Answer Length** | Limited to 5000 characters via Pydantic schema |
| **401 Handling** | Global Axios interceptor clears tokens and redirects on 401 responses |

---

## Testing

The repository contains the following test files:

| File | Type | Description |
|------|------|-------------|
| `backend/e2e_api_test.py` | E2E API test | Full end-to-end HTTP test covering Syllabus Mode (registration, resume upload, syllabus upload, interview lifecycle, merge verification) |
| `backend/runtime_test.py` | Integration test | Runtime testing of backend services |
| `backend/multi_concept_test.py` | Unit/integration test | Tests for multi-concept question generation |
| `backend/test_optimization.py` | Performance test | Optimization benchmarks |
| `backend/test_perf_db.py` | Performance test | Database performance testing |
| `backend/test_sbert_matching.py` | Unit test | SBERT semantic matching accuracy tests |
| `scripts/test_retrieval.py` | RAG test | RAG retrieval quality testing |
| `scripts/evaluate_retrieval.py` | RAG test | Retrieval evaluation metrics |
| `scripts/validate_chunks.py` | Validation | Chunk quality validation |
| `scripts/validate_repository.py` | Validation | Repository consistency validation |

**Running the E2E test:**

```bash
cd backend
python e2e_api_test.py
```

> Requires the backend server to be running on `localhost:8000`.

---

## Limitations

- **Local model resource usage** — The Sentence-BERT embedding model (`all-MiniLM-L6-v2`) and `faster-whisper` STT model are loaded into memory. On resource-constrained machines, initial load time may be noticeable.
- **Single-worker analysis cache** — The JD analysis cache (`_jd_analysis_cache`) is an in-memory Python dictionary. In a multi-worker deployment (e.g., multiple Uvicorn workers), the analysis result cached in one worker would not be available to another. This is acceptable for single-worker development but would require a shared cache (e.g., Redis) for production multi-worker setups.
- **Browser microphone support** — Speech-to-text relies on the browser's `MediaRecorder` API and `getUserMedia`. Behavior varies across browsers; some may not support WebM/Opus encoding.
- **External API dependency** — Question generation and evaluation depend on the Groq API. Network issues or API key problems will prevent interview functionality.
- **No real-time streaming** — The interview flow uses a synchronous request-response cycle. The LLM generates the next question synchronously after evaluating the previous answer, which takes a few seconds.
- **PDF-only resumes** — Resume upload currently accepts only PDF files.

---

## Future Enhancements

The following features are **not currently implemented** and represent potential future work:

- **Longitudinal adaptive initialization** — Using historical performance data from past interviews to initialize the adaptive engine for new sessions (currently each session starts fresh at Bloom Level 1)
- **Distributed analysis cache** — Replacing the in-memory JD analysis cache with Redis or similar for production multi-worker deployments
- **Docker containerization** — Packaging the full stack (frontend, backend, MySQL, ChromaDB) in Docker Compose for simplified deployment
- **Additional file format support** — Supporting DOCX and other formats for resume upload
- **Real-time LLM streaming** — Streaming question generation and evaluation responses for faster perceived latency
- **Multi-language support** — Expanding beyond English-only interviews and STT

---

## Contributing

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make changes** and write tests where applicable
4. **Ensure the backend starts** without errors: `uvicorn app.main:app --reload`
5. **Ensure the frontend builds**: `npm run build`
6. **Open a Pull Request** with a clear description of changes

Please follow the existing code style and keep commits focused on single concerns.

---

## License

This project was developed as an academic/portfolio project. See the repository for any license information.