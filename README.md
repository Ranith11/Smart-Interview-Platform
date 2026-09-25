<div align="center">
  <img src="frontend/public/logo.png" alt="SmartInterview Logo" width="120" />
  <h1>SmartInterview</h1>
  <p><strong>Next-Generation AI-Powered Adaptive Mock Interview Platform</strong></p>
  <p>
    <img src="https://img.shields.io/badge/FastAPI-0.115.0-009688.svg?style=flat&logo=FastAPI&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-18.3.1-61DAFB.svg?style=flat&logo=React&logoColor=black" alt="React" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white" alt="Tailwind" />
    <img src="https://img.shields.io/badge/ChromaDB-0.6.3-FF6F00.svg?style=flat" alt="ChromaDB" />
    <img src="https://img.shields.io/badge/Groq_Cloud-openai%2Fgpt--oss--120b-F55036.svg?style=flat" alt="Groq" />
    <img src="https://img.shields.io/badge/Local_Ollama-Llama_3.1-000000.svg?style=flat" alt="Ollama" />
    <img src="https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-7952B3.svg?style=flat" alt="SBERT" />
    <img src="https://img.shields.io/badge/Database-MySQL_8.0-4479A1.svg?style=flat&logo=mysql&logoColor=white" alt="MySQL" />
  </p>
</div>

---

## 📖 Executive Summary

**SmartInterview** is an open-ended, adaptive technical interview simulation platform. While traditional technical interview platforms rely on static multiple-choice questions or rigid coding problems (like LeetCode), SmartInterview acts as an empathetic, pedagogical interviewer that conducts real-time, conversational technical interviews.

SmartInterview incorporates three foundational engineering innovations:
1. **Pedagogical Cognitive Engine (Bloom's Taxonomy):** Dynamically scales interview questions across 6 cognitive tiers (from Level 1 *Remember* to Level 6 *Create*) based on deterministic candidate proficiency scoring.
2. **Strictly Grounded RAG Knowledge Base:** Employs ChromaDB vector storage (402 verified chunks across 8 core Computer Science domains) and `all-MiniLM-L6-v2` dense embeddings to eliminate LLM hallucinations.
3. **Dual-Engine Resilient LLM Architecture:** Operates with ultra-low latency (~0.69s) via **Cloud Groq (`openai/gpt-oss-120b`)** while supporting a 100% offline, air-gapped mode via **Local Ollama (`llama3.1`)** with automatic live failover.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Frontend [React 18 + Vite — Port 5174]
        UI[Candidate Dashboard]
        Upload[Resume / JD / Syllabus Ingestion]
        LiveAudio[Mic Audio Capture & TTS Player]
    end

    subgraph Backend [FastAPI — Port 8000]
        Router[REST API Routers: Auth, Resumes, Interviews, Syllabus]
        Extractor[PyMuPDF Text & Skill Parser]
        AdaptiveEngine[Bloom's Taxonomy Adaptive State Machine]
        EvalService[5-Factor Multi-Signal Answer Evaluator]
        LLMHub[Resilient LLM Client Provider]
    end

    subgraph Storage [Databases & Vectors]
        MySQL[(MySQL 8: Users, Sessions, Evaluations)]
        Chroma[(ChromaDB: 402 Core CS Chunks + Dynamic Syllabi)]
    end

    subgraph AI_Inference [AI Providers]
        Groq[Cloud Groq API: openai/gpt-oss-120b ~0.69s]
        Ollama[Local Ollama: llama3.1 100% Offline ~6.0s]
    end

    UI -->|JWT Authenticated REST| Router
    Upload -->|PDF/DOCX/TXT| Extractor
    Extractor -->|Skills & Concepts| AdaptiveEngine
    AdaptiveEngine -->|Cosine Vector Query| Chroma
    Chroma -->|Retrieved Grounding Chunks| LLMHub
    LLMHub -->|Cloud Primary| Groq
    LLMHub -.->|Automatic Offline Failover| Ollama
    Groq -->|Generated Question| LiveAudio
    Ollama -->|Generated Question| LiveAudio
    LiveAudio -->|Candidate Answer| EvalService
    EvalService -->|Accuracy, Completeness, SBERT Score| AdaptiveEngine
    AdaptiveEngine -->|Persist Metrics| MySQL
```

---

## ✨ Key Features & Capabilities

### 1. Dual-Engine LLM with Zero-Downtime Fallback
* **Cloud Mode (Groq):** Powered by `openai/gpt-oss-120b`, delivering sub-second response times (~0.69s) for fluid conversational dialogue.
* **Local Mode (Ollama):** Powered by local `llama3.1` (8B), enabling 100% offline, air-gapped interview execution with zero external data egress.
* **Automatic Failover:** If internet connectivity drops mid-interview, the system seamlessly rescues the active session by routing prompts to your local Ollama instance.

### 2. Pedagogical Question Generation via Bloom's Taxonomy
Questions are never selected at random. An adaptive state machine modulates cognitive difficulty in real time:
* **Level 1 (Remember):** Definitions, keyword recall, syntax facts.
* **Level 2 (Understand):** Explaining mechanisms and architectural principles.
* **Level 3 (Apply):** Code implementation and practical endpoint configuration.
* **Level 4 (Analyze):** Debugging bottlenecks, diagnosing concurrency deadlocks.
* **Level 5 (Evaluate):** Assessing trade-offs, justifying database architectures (ACID vs. BASE).
* **Level 6 (Create):** Designing end-to-end distributed system architectures.

### 3. Source-Grounded Vector RAG Knowledge Base
* **Core Dataset (`technical_kb`):** 402 pre-indexed, quality-audited chunks across 8 core domains (`cn`, `dbms`, `design-patterns`, `dsa`, `ml-dl`, `oop`, `os`, `system-design`).
* **Syllabus Mode:** Ingests academic course documents (PDF/DOCX/TXT), extracts syllabus modules, creates isolated temporary collections (`temp_syllabus_{id}`), and dynamically tracks live chunk metrics.

### 4. 5-Factor Candidate Answer Evaluation
Candidate answers are scored on a deterministic 100-point scale across 5 distinct dimensions:
1. **Technical Accuracy (30%):** Factual correctness against verified RAG grounding.
2. **Completeness (25%):** Depth of coverage addressing all parts of the question.
3. **Relevance (15%):** Direct alignment with the technical topic without filler fluff.
4. **Semantic Similarity (15%):** SBERT dense embedding distance to model reference answers.
5. **Concept Keyword Coverage (15%):** Domain-specific lexical entity density.

### 5. Neural Voice Interface & Performance Reporting
* **Text-to-Speech (TTS):** Microsoft Neural voice synthesis (`edge-tts`).
* **Speech-to-Text (STT):** Groq Whisper audio transcription.
* **Automated PDF Reports:** Detailed downloadable interview scorecards compiled via `reportlab`.

---

## ⚡ Live Empirical Benchmarks

Tested on standard development hardware (Windows 11, Intel Core i5 / AMD Ryzen, 16 GB RAM):

| Performance Dimension | ⚡ Cloud Groq (`openai/gpt-oss-120b`) | 🦙 Local Ollama (`llama3.1`) |
| :--- | :--- | :--- |
| **Average Generation Latency** | **0.69 seconds** *(~13x faster)* | **8.88 seconds** |
| **Level 1 (Remember) Latency** | **0.66 seconds** | 13.39 seconds *(with warm-up)* |
| **Level 3 (Apply) Latency** | **0.47 seconds** | 5.98 seconds |
| **Level 5 (Evaluate) Latency** | **0.94 seconds** | 7.27 seconds |
| **Evaluation Latency** | **1.14 seconds** | 10.41 seconds |
| **Internet Requirement** | Active Connection | **0% (100% Offline)** |
| **Privacy / Data Egress** | Encrypted HTTPS | **100% On-Device** |
| **Schema Stability** | 80% *(requires padding)* | **100% Valid JSON** |

---

## 🚀 Quickstart Guide

### Prerequisites
* **Python 3.10+**
* **Node.js 18+**
* **MySQL Server 8.0+**
* *(Optional for Offline Mode)*: **[Ollama](https://ollama.com/)** with `llama3.1` pulled (`ollama pull llama3.1`)

---

### Step 1: Clone & Configure Credentials

```bash
git clone https://github.com/konduriabhiram29-ai/SmartInterview-main.git
cd SmartInterview-main
```

Copy the example environment configuration:
```bash
cp .env.example .env
```

Open `.env` and set your credentials:
```env
# ── AI Provider Configuration ──
# Set to "groq" for Cloud (sub-second) or "ollama" for 100% Offline
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=openai/gpt-oss-20b

# Local Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ── Relational Database ──
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/smartinterview

# ── Security & Authentication ──
JWT_SECRET_KEY=your_secure_random_64_char_hex_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

---

### Step 2: Database Initialization

Initialize the database schema:
```bash
mysql -u root -p < backend/setup_database.sql
```

---

### Step 3: Start the Backend (FastAPI)

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```
* Backend API: `http://localhost:8000`
* Swagger Interactive Docs: `http://localhost:8000/docs`

---

### Step 4: Start the Frontend (React + Vite)

In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
* Frontend Web App: `http://localhost:5174` (or `http://localhost:5173`)

---

## 📴 Running 100% Offline (Air-Gapped Mode)

To run the complete platform without any internet connection:
1. Ensure Ollama is running: `ollama run llama3.1`
2. In your `.env` file, set:
   ```env
   LLM_PROVIDER=ollama
   ```
3. Disconnect Wi-Fi. The entire application (FastAPI, React, MySQL, ChromaDB vector search, Llama 3.1 question generation, and answer scoring) will run completely offline on your local machine!

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new candidate account |
| `POST` | `/api/auth/login` | Authenticate user & return JWT token |
| `GET` | `/api/auth/me` | Fetch active user profile |
| `POST` | `/api/resumes/upload` | Upload & parse candidate resume (PDF) |
| `POST` | `/api/job-descriptions/upload` | Upload & parse target Job Description (PDF) |
| `POST` | `/api/syllabus/upload` | Upload academic syllabus (PDF/DOCX/TXT) for Syllabus Mode |
| `POST` | `/api/interviews/sessions` | Create a new adaptive mock interview session |
| `GET` | `/api/interviews/sessions/{id}/question` | Generate next adaptive question via RAG & Bloom's Taxonomy |
| `POST` | `/api/interviews/sessions/{id}/answer` | Submit candidate answer & compute 5-factor evaluation score |
| `GET` | `/api/interviews/sessions/{id}/report` | Generate downloadable PDF performance scorecard |
| `GET` | `/api/knowledge-stats` | Live inspection of ChromaDB collections and chunk counts |
| `GET` | `/api/health` | Service health status check |

---

## 📂 Project Directory Structure

```text
SmartInterview-main/
├── backend/
│   ├── app/
│   │   ├── dependencies/       # JWT auth & DB session injection
│   │   ├── models/             # SQLAlchemy ORM schemas (Users, Sessions, Questions)
│   │   ├── routers/            # FastAPI endpoints (auth, resumes, interviews, etc.)
│   │   ├── schemas/            # Pydantic request/response validation
│   │   ├── services/           # Core business logic:
│   │   │   ├── bloom.py        # Bloom's Taxonomy state definitions
│   │   │   ├── llm_client.py   # Resilient Unified LLM Provider (Groq + Ollama)
│   │   │   ├── question_service.py # Adaptive question synthesis
│   │   │   ├── evaluation_service.py # 5-factor answer scoring
│   │   │   ├── syllabus_rag_service.py # Syllabus chunking & dynamic RAG
│   │   │   └── voice_service.py # edge-tts & Whisper transcription
│   │   ├── config.py           # Application environment loader
│   │   └── main.py             # FastAPI entrypoint & middleware
│   ├── requirements.txt        # Python backend dependencies
│   └── setup_database.sql      # MySQL schema creation script
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI Lego blocks (Sidebar, Header, Cards)
│   │   ├── context/            # React AuthContext & Global state
│   │   ├── pages/              # View pages (Login, Dashboard, Interview, Reports)
│   │   └── App.jsx             # Main routing component
│   ├── package.json            # Node.js dependencies
│   └── vite.config.js          # Vite configuration with /api reverse proxy
├── chroma_db/                  # Local persistent vector database (402 CS chunks)
├── data/
│   ├── processed/              # Curated 50 concepts across 8 domains
│   └── knowledge_stats.json    # Canonical knowledge base statistics
├── scripts/
│   ├── generate_question.py    # Standalone CLI interview runner
│   ├── ingest_vector_db.py     # Vector database ingestion tool
│   └── verify_deliverables_sync.py # Deliverables synchronization auditor
├── SmartInterview_Deliverables/ # Frozen baseline academic deliverables
├── SmartInterview_Progressive_Updates/ # Active synchronized project documents
├── .env.example                # Configuration template
├── .gitignore                  # Git exclusion rules (protects secrets)
└── README.md                   # Project documentation
```

---

## 👥 Contributors & Academic Defense

* **Lead Developer:** Abhiram Konduri ([@konduriabhiram29-ai](https://github.com/konduriabhiram29-ai))
* **Project Review & Readiness:** Verified for Project Readiness Review (PRR) and Final Academic Defense.
* **Synchronized Documentation:** All academic deliverables (SRS, Research Paper, Master Encyclopedia, and Presentation Slides) are maintained under `SmartInterview_Progressive_Updates/`.

---

<div align="center">
  <sub>Built with ❤️ using FastAPI, React, ChromaDB, Groq, and Ollama.</sub>
</div>