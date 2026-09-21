# Software Requirements Specification (SRS) - Source of Truth
**Project:** SmartInterview — AI-Powered Technical Mock Interview Platform

## 1. Introduction
### 1.1 Purpose
This document specifies the software requirements for SmartInterview, an adaptive mock interview system designed to dynamically scale interview difficulty based on candidate performance using Bloom's Taxonomy.

### 1.2 Scope
SmartInterview targets software engineers and tech professionals. It integrates real-time RAG (Retrieval-Augmented Generation), an advanced multi-signal evaluation framework, and Microsoft Neural TTS.

## 2. Overall Description
### 2.1 System Architecture
The application follows a standard client-server architecture with external API integrations:
- **Client (Frontend)**: React 18, Vite, Tailwind CSS v4, React Router v7.
- **Server (Backend)**: FastAPI running on Uvicorn.
- **Database**: MySQL 8.0 for relational data (users, session history).
- **Vector DB**: ChromaDB for RAG contexts (persisted locally).
- **External AI Services**: Groq API (`openai/gpt-oss-120b`) for LLM inference, Microsoft `edge-tts` for Voice synthesis, Groq Whisper for Speech-to-Text.

### 2.2 User Classes
- **Candidate/User**: Uploads resumes/JDs, conducts mock interviews, reviews performance.
- **System Administrator (Implicit)**: Manages vector DB updates.

## 3. Specific Requirements
### 3.1 Functional Requirements
**FR1: Authentication and Profiles**
- System must allow users to register with email/password.
- System must hash passwords using `bcrypt` and issue 24-hour JWTs.
- System must maintain a user performance dashboard tracking metrics across sessions.

**FR2: Document Processing & RAG Pipeline**
- System must accept PDF uploads (Resume and JD) up to 5MB.
- System must extract technical skills using `PyMuPDF`.
- System must map and intersect Resume and JD skills for targeted questions.
- System must construct localized vector collections (Syllabus mode) for academic study.

**FR3: Adaptive Interview Engine**
- System must implement Bloom's Taxonomy (Levels 1-6).
- System must scale question difficulty deterministically:
  - Advance level if score >= 80%.
  - Maintain level if 50% <= score < 80%.
  - Regress level if score < 50%.
- System must implement a safety cap of 30 questions for open-ended interviews.

**FR4: Answer Evaluation System**
- System must evaluate answers using a multi-signal approach, computing an average overall score from:
  1. Technical Accuracy & Completeness (LLM rated)
  2. Concept Coverage (LLM extracted boolean flags)
  3. Semantic Similarity (SentenceTransformers `all-MiniLM-L6-v2` embeddings compared against expected concepts).

**FR5: Voice Capabilities**
- System must synthesize AI questions into natural speech using Microsoft `edge-tts`.
- System must transcribe user audio using Groq Whisper.

### 3.2 Non-Functional Requirements
**NFR1: Performance**
- System must utilize Groq's LPU architecture for <2s LLM generation latency.
- RAG queries must execute in <500ms using local ChromaDB.
- Voice synthesis (TTS) must stream audio directly to memory avoiding disk I/O.

**NFR2: Security**
- System must not log sensitive `.env` keys.
- JWT secrets must be cryptographically secure in production.
- User files must be isolated using user ID prefixes.

**NFR3: Reliability**
- System must degrade gracefully (fallback LLM models, safe zero-score defaults on generation/evaluation failure).
