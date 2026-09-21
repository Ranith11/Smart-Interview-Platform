<div align="center">
  <img src="frontend/public/logo.png" alt="SmartInterview Logo" width="120" />
  <h1>SmartInterview</h1>
  <p><strong>AI-Powered Adaptive Mock Interview Platform</strong></p>
</div>

---

## 📖 Project Overview

SmartInterview is an advanced, full-stack application designed to simulate open-ended, technical mock interviews. Unlike rigid Q&A platforms, SmartInterview uses an adaptive learning engine based on **Bloom’s Taxonomy** to dynamically adjust the difficulty, depth, and cognitive level of questions based on real-time candidate performance.

It leverages Retrieval-Augmented Generation (RAG) through a persistent ChromaDB vector knowledge base, powered by Groq's high-speed LLM inference, to generate highly contextual, technically accurate questions tailored to both the candidate's resume and the target job description.

## ✨ Core Features

*   **Resume & JD Skill Mapping**: Extracts and maps overlapping skills from uploaded Resumes and Job Descriptions (PDF) using PyMuPDF to drive targeted interview sessions.
*   **Deterministic Adaptive Engine**: Modulates question difficulty and cognitive complexity across 6 levels of Bloom's Taxonomy based on a multi-signal scoring evaluation (not just LLM subjective scores).
*   **Vector RAG Knowledge Base**: Uses ChromaDB and `all-MiniLM-L6-v2` embeddings to retrieve verified technical concepts, ensuring the LLM asks grounded questions.
*   **Syllabus Mode**: A secondary mode that dynamically creates isolated, temporary vector collections from uploaded course material (PDF/DOCX/TXT) for academic study sessions.
*   **Multi-Signal Answer Evaluation**: Evaluates candidate responses using 5 distinct metrics (Technical Accuracy, Completeness, Relevance, Semantic Similarity, and Concept Coverage).
*   **Integrated Voice Synthesis (TTS & STT)**: High-quality offline-capable Microsoft Neural text-to-speech (`edge-tts`) and Groq Whisper audio transcription.
*   **Performance Analytics & Reporting**: Real-time KPI dashboards tracking historical performance and automatic PDF report generation (`reportlab`).

---

## 🏗️ Architecture Stack

### Frontend (User Interface)
*   **Framework**: React 18 + Vite (Runs on port 5174)
*   **Styling**: Tailwind CSS v4 + Lucide React (Icons)
*   **Routing**: React Router DOM v7
*   **State & Auth**: React Context API, JWT stored securely in standard SPA pattern.

### Backend (API & Engine)
*   **Framework**: FastAPI (Runs on port 8000)
*   **Database**: MySQL (PyMySQL + SQLAlchemy 2.0 ORM)
*   **Vector Database**: ChromaDB (Persistent local SQLite/Parquet)
*   **LLM Provider**: Groq API (`openai/gpt-oss-120b` with fallback)
*   **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`)
*   **Voice/Audio**: `edge-tts` (TTS), Groq Whisper (STT)

---

## 🚀 Local Setup & Installation

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   MySQL Server 8.0+
*   Git

### 1. Database Initialization
Create the database and required tables using the canonical setup script:
```bash
mysql -u root -p < backend/setup_database.sql
```
*(Ensure your MySQL credentials match the `.env` configuration).*

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the **project root** (same level as the `backend` and `frontend` folders) based on `.env.example`:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=openai/gpt-oss-20b
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/smartinterview
JWT_SECRET_KEY=generate_a_secure_random_64_char_hex_string
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

Start the backend server:
```bash
# Windows
.\start_backend.ps1
# Or manually:
cd backend && python -m uvicorn app.main:app --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Start the frontend development server:
```bash
# Windows
.\start_frontend.ps1
# Or manually:
cd frontend && npm run dev
```

The application will be available at `http://localhost:5174`.

---

## 🔒 Security Notes
*   **API Keys**: Never commit your `GROQ_API_KEY` to version control. The `.env` file is excluded via `.gitignore`.
*   **JWT Secret**: Ensure `JWT_SECRET_KEY` is a cryptographically secure random string in production environments.
*   **Vector DB**: The `chroma_db/` directory contains pre-computed embeddings and is intentionally tracked in Git to provide a ready-to-use technical knowledge base.

---

## 📝 License
This is an academic project developed as a final software engineering capstone. All rights reserved by the original authors.