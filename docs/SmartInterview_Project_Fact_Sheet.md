# SmartInterview: Project Fact Sheet

## 1. Core Purpose
SmartInterview is an AI-powered technical mock interview platform that simulates rigorous, open-ended technical interviews. It evaluates candidates dynamically by adjusting question difficulty and cognitive depth based on real-time performance.

## 2. Technical Stack
- **Frontend**: React 18, Vite, Tailwind CSS v4, React Router v7
- **Backend**: FastAPI 0.115, Python 3.10+
- **Database**: MySQL 8.0, SQLAlchemy 2.0 ORM, PyMySQL
- **Vector Database**: ChromaDB (local persistent SQLite/Parquet)
- **AI/LLM Provider**: Groq (`openai/gpt-oss-120b`)
- **Embedding Model**: SentenceTransformers (`all-MiniLM-L6-v2`)
- **Voice Stack**: `edge-tts` (Microsoft Neural TTS), Groq Whisper (STT)

## 3. Key Differentiators
1. **Dynamic JD & Resume Mapping**: Unlike generic platforms, SmartInterview uses PyMuPDF to extract and intersect skills from both a candidate's resume and a target Job Description, ensuring hyper-relevant questions.
2. **Deterministic Adaptive Engine**: Avoids unpredictable LLM behavior by using strict deterministic rules based on Bloom's Taxonomy. The system strictly promotes or demotes difficulty (Remember → Create) based on the calculated score of previous answers.
3. **Multi-Signal Evaluation**: Does not rely on a single LLM prompt for a score. Instead, it aggregates:
   - Technical accuracy & completeness (LLM)
   - Concept coverage (LLM classification)
   - Semantic similarity (SentenceTransformer embeddings against expected concepts)
4. **Offline-Capable TTS**: Uses `edge-tts` directly in Python memory instead of relying on expensive third-party paid voice APIs.

## 4. Subsystems
- **RAG Knowledge Base**: A pre-computed vector database (`chroma_db/`) containing verified technical documentation ensuring the LLM is grounded in real engineering truths.
- **Syllabus Mode**: Allows users to upload custom study materials (PDF/TXT/DOCX). The backend dynamically chunks and embeds this data into a temporary vector collection, restricting the interview scope purely to the uploaded context.

## 5. System Status (Final Audit)
- **Status**: Production-ready for local evaluation.
- **Security**: JWT authentication (24h expiry) and hashed passwords (bcrypt).
- **Quality**: Verified zero console errors in frontend navigation. Full interview loop tested and functional.
