# SmartInterview — Final Release Audit Report (Phase 26 Checkpoint)

> **AUDIT STATUS**: Phases 0–24 complete. Awaiting PROCEED command before any code changes.
> **Environment Tested**: Windows 11, Python venv, MySQL, ChromaDB, Groq API
> **Audit Date**: 2026-09-21
> **Backend**: http://localhost:8000 RUNNING
> **Frontend**: http://localhost:5174 RUNNING

---

## PHASE 0 — BASELINE SUMMARY

| Item | Value |
|------|-------|
| Git Branch | `main` |
| Git Status | 3 modified files (chroma_db/chroma.sqlite3, start_backend.ps1, start_frontend.ps1); 2 untracked dirs |
| Recent Commits | 5 commits; latest: `9fdebf1` "redesign Performance Dashboard" |
| Backend Version | `app.version = "7.0.0"` (FastAPI) |
| Frontend Stack | React + Vite v8.2.2 + Tailwind CSS v4 + react-router-dom v7 |
| Backend Stack | FastAPI 0.115.0 + SQLAlchemy 2.0.35 + PyMySQL + ChromaDB 0.6.3 + SentenceTransformers 3.4.1 + Groq |
| Database | MySQL (`smartinterview` schema, `root@localhost:3306`) |
| ChromaDB | Persistent, `chroma_db/` directory, collection `technical_kb` (109 files tracked in git) |
| LLM Provider | Groq — model `openai/gpt-oss-120b`, fallback `openai/gpt-oss-20b` |
| Embedding Model | `all-MiniLM-L6-v2` (SentenceTransformers, 384 dimensions) |
| JWT Expiry | 1440 minutes (24 hours) |
| README | **1 LINE ONLY** — completely empty |

### Environment Variables

| Variable | Present | Notes |
|----------|---------|-------|
| `GROQ_API_KEY` | YES | Real key in .env — NOT git tracked (safe), but should be rotated |
| `GROQ_MODEL` | YES | `openai/gpt-oss-120b` |
| `GROQ_FALLBACK_MODEL` | YES in .env only | **NOT loaded in config.py — dead variable** |
| `DATABASE_URL` | YES | MySQL with encoded password |
| `JWT_SECRET_KEY` | YES | Weak predictable value — must be changed |
| `JWT_ALGORITHM` | YES | HS256 |
| `JWT_EXPIRATION_MINUTES` | YES | 1440 |

---

## PHASE 1 — APPLICATION STARTUP VERIFIED

| Service | Status | Port | Notes |
|---------|--------|------|-------|
| Backend (FastAPI/Uvicorn) | RUNNING | 8000 | No import errors |
| Frontend (Vite) | RUNNING | 5174 | Started on 5174 (not 5173); both in CORS allow-list |
| `/api/health` | RESPONDS | — | `{"status":"ok","service":"SmartInterview API"}` |
| MySQL | CONNECTED | 3306 | Backend started without DB errors |
| ChromaDB | AVAILABLE | — | Persistent client, 109 binary files tracked |
| All Python imports | PASS | — | fastapi, sqlalchemy, groq, chromadb, sentence_transformers, pymysql — all OK |

---

## PHASE 2 — COMPLETE APPLICATION INVENTORY

### Frontend Routes (from App.jsx)
| Route | Page Component | Protected | Notes |
|-------|---------------|-----------|-------|
| `/` | Landing | No | Public |
| `/login` | Login | No | Public |
| `/register` | Register | No | Public |
| `/dashboard` | Dashboard | Yes | With Sidebar |
| `/resume` | ResumeUpload | Yes | With Sidebar |
| `/syllabus` | SyllabusUpload | Yes | With Sidebar |
| `/setup` | InterviewSetup | Yes | With Sidebar |
| `/interview/:id` | Interview | Yes | No Sidebar (full-screen) |
| `/results/:id` | Results | Yes | With Sidebar |
| `/history` | History | Yes | With Sidebar |
| `/profile` | Profile | Yes | With Sidebar |
| `/performance` | PerformanceDashboard | Yes | With Sidebar |

**Total pages**: 12 — **Missing 404 route**: No catch-all `*` route defined.

### Backend API Endpoints (~20 total)
| Router Prefix | Key Endpoints |
|--------------|---------------|
| `/api/auth` | POST /register, POST /login, GET /me |
| `/api/resumes` | POST /upload, GET /current, DELETE /{id} |
| `/api/job-descriptions` | POST /upload, GET /current, GET /mapping, DELETE /{id} |
| `/api/interviews` | POST /start, GET /history, GET /{id}, GET /{id}/results, GET /{id}/report/pdf, POST /{id}/questions/{qid}/answer, POST /{id}/complete, POST /upload-syllabus, POST /voice/tts, POST /voice/transcribe, GET /voice/status |
| `/api/users` | GET /profile, PUT /profile, GET /stats, GET /performance |
| `/api/health` | GET |

### Key Backend Services
| Service | Lines | Purpose |
|---------|-------|---------|
| interview_service.py | 967 | Core session orchestration |
| report_service.py | ~700 | PDF report generation |
| question_service.py | 512 | RAG + LLM question generation |
| evaluation_service.py | 419 | Multi-signal answer scoring |
| adaptive_engine.py | 494 | Deterministic Bloom progression |
| syllabus_rag_service.py | ~400 | Syllabus-mode RAG |
| voice_service.py | 271 | TTS (edge-tts) + STT (Groq Whisper) |
| bloom.py | ~200 | Bloom taxonomy definitions |

### Identified Inventory Issues
- `GROQ_FALLBACK_MODEL`: In `.env` but **never read in `config.py`** — dead env var
- `_active_user_syllabus` dict in `interviews.py`: In-memory only — **lost on server restart**
- 5 `setup_database*.sql` files: No clear indication of which is current
- `scratch/` directories: Dev scripts that should not be in production
- `e2e_full_audit_*.webp`: Previous audit screenshot committed to repo root
- Zero automated tests anywhere in the project

---

## PHASE 3 — FRONTEND QA RESULTS (VERIFIED LIVE IN BROWSER)

| Route | Loads | Console Errors | Issues Found |
|-------|-------|----------------|--------------|
| `/` Landing | YES | NONE | None |
| `/login` | YES | NONE | None |
| `/register` | YES | NONE | None |
| `/dashboard` | YES | NONE | **ISSUE: "86% response" badge shown for 0-interview user — hardcoded** |
| `/resume` | YES | NONE | None |
| `/setup` | YES | NONE | Shows "No Resume Uploaded" guard correctly |
| `/history` | YES | NONE | "No interviews yet" empty state |
| `/performance` | YES | NONE | "No Completed Interviews Yet" empty state |
| `/profile` | YES | NONE | User info displayed correctly |
| `/syllabus` | YES | NONE | File upload UI correct |
| `/interview/:id` | NOT TESTED | — | Requires resume+JD upload (test PDF not provided) |
| `/results/:id` | NOT TESTED | — | Requires completed interview |

### Auth Flow (Live Tested)
- Registration creates real user in MySQL: YES
- Auto-login after registration: YES
- JWT stored in localStorage: YES
- Logout clears storage, redirects to /login: YES
- Protected routes redirect to /login when unauthenticated: YES
- `/api/auth/me` token verification on app load: YES

---

## PHASE 4 — AUTHENTICATION AUDIT

| Check | Status | Notes |
|-------|--------|-------|
| Registration | WORKS | Creates user, returns JWT |
| Login | WORKS | bcrypt password verification |
| JWT on every request | YES | `Authorization: Bearer <token>` header via axios interceptor |
| Token verification on load | YES | AuthContext calls `/api/auth/me` |
| 401 global handler | YES | Clears token, redirects to /login |
| Logout | WORKS | Clears localStorage |
| Protected routes | WORKS | ProtectedRoute component |
| Token expiry | 24h | 1440 minutes |
| No token refresh | MISSING | No refresh token mechanism |
| Password hashing | bcrypt | Correct implementation |
| JWT secret strength | WEAK | `my-super-secret-random-key-1234567890` — must be changed |

---

## PHASE 5 — INTERVIEW WORKFLOW (CODE TRACE)

> Normal mode requires BOTH resume AND job description. Backend returns error if JD is missing. Frontend only warns about missing resume — **does NOT warn about missing JD**.

| Step | Status |
|------|--------|
| Resume upload + PyMuPDF parsing | IMPLEMENTED |
| JD upload + skill extraction | IMPLEMENTED |
| Skill mapping (Group A: JD∩Resume, Group B: JD-only) | IMPLEMENTED |
| Interview session creation | IMPLEMENTED |
| First question: RAG retrieval + Groq LLM generation | IMPLEMENTED |
| Adaptive state init (serialized to MySQL JSON) | IMPLEMENTED |
| Answer submission | IMPLEMENTED |
| Evaluation: LLM + semantic similarity + concept coverage | IMPLEMENTED |
| Adaptive decision: `decide_next()` Bloom progression | IMPLEMENTED |
| Next question generation | IMPLEMENTED |
| Session completion + recommendations | IMPLEMENTED |
| Results: per-question breakdown | IMPLEMENTED |
| PDF report (reportlab) | IMPLEMENTED |
| History persistence | IMPLEMENTED |
| Performance analytics (real DB data) | IMPLEMENTED |

---

## PHASE 6 — ADAPTIVE ENGINE VERIFICATION

Rules in `adaptive_engine.py` (deterministic Python, NOT LLM-driven):

| Score | Action |
|-------|--------|
| >= 80 | Advance Bloom level; if at Create (max), advance difficulty |
| 50-79 | Maintain current level |
| < 50 | Regress Bloom level; if at Remember (min), lower difficulty |

- **Bloom levels**: Remember (1) → Understand (2) → Apply (3) → Analyze (4) → Evaluate (5) → Create (6)
- **Skill selection**: Weakness-biased round-robin (least-attempted first, then lowest avg score)
- **Safety limit**: MAX_ADAPTIVE_QUESTIONS = 30 (prevents infinite sessions)
- **Open-ended mode**: question_count=0 → only safety limit stops interview
- **Documentation vs Code**: MATCH — code matches `docs/week8_adaptive_learning.md`

---

## PHASE 7 — RAG / CHROMADB VERIFICATION

| Item | Value |
|------|-------|
| ChromaDB path | `{project_root}/chroma_db/` |
| Collection name | `technical_kb` |
| Embedding model | `all-MiniLM-L6-v2` (384 dims) |
| ChromaDB version | 0.6.3 |
| Files in git | 109 binary segment files + chroma.sqlite3 (~14MB) |
| Collections present | 27+ UUID subdirectories (includes old syllabus temp collections) |

- ChromaDB binary files ARE intentionally committed (pre-built knowledge base)
- `chroma.sqlite3` is listed as "modified" (populated during prior sessions)
- 27 UUID directories include stale temporary syllabus collections from prior runs
- RAG is NOT "guaranteed grounded" — context used as LLM input, LLM can still deviate
- RAG context re-retrieved by chunk_id at evaluation time (not fake)

---

## PHASE 8 — LLM / API VERIFICATION

| Item | Status |
|------|--------|
| Provider | Groq |
| Model | `openai/gpt-oss-120b` |
| Fallback model | In `.env` but NOT in `config.py` — not active |
| Empty response handling | YES — `_safe_defaults()` returns zero scores |
| Malformed JSON parsing | YES — handles markdown code blocks, fallback extraction |
| Missing API key | Handled — returns zero scores with feedback message |
| Rate-limit handling | UNKNOWN — not tested live |
| Groq Whisper STT | `whisper-large-v3` via in-memory transcription |
| TTS | Microsoft Neural TTS (edge-tts, offline-capable) — `en-US-ChristopherNeural` |

---

## PHASE 9 — DATABASE SCHEMA VERIFICATION

**Tables confirmed (from SQLAlchemy models)**:
- `users` — id, name, email, password_hash, created_at
- `resumes` — user_id (FK), skills/projects/education (JSON), raw_text, page_count
- `job_descriptions` — user_id (FK), skills (JSON), raw_text
- `interview_sessions` — complex JSON columns for adaptive_state, syllabus_state, selected_skills, final_recommendations
- `interview_questions` — bloom_level, bloom_level_number, rag_context (JSON)
- `answers` — question_id (unique FK)
- `answer_evaluations` — 5 individual score columns + JSON arrays for concepts

**Issues**:
- 5 SQL setup files (v1 through v5) — no canonical version labeled

---

## PHASE 10 — PERFORMANCE DASHBOARD AUDIT

- `/api/users/performance` returns ONLY real data — verified in code
- Empty state (`has_data: false`) returns correctly when no completed interviews
- `bloom_performance` keyed by Bloom level name (real)
- `skill_performance` from real `answer_evaluations` records
- **ISSUE**: Dashboard KPI subtitle labels ("86% response", "AI Evaluated", "Algorithmic & System Design") are **hardcoded** in JSX regardless of actual data

---

## PHASE 11 — UPLOAD / FILE HANDLING AUDIT

| Check | Status |
|-------|--------|
| Resume: PDF-only validation | YES |
| Resume: 5MB limit | YES |
| Resume: empty file | HANDLED |
| Resume: no skills found → 422 | YES |
| Resume: cleanup on error | YES (os.remove) |
| JD: PDF-only, 5MB | YES |
| Syllabus: PDF/TXT/DOCX, 20MB | YES |
| User isolation (user_id prefix) | YES |
| File path traversal | PARTIAL — os.path.basename() used but upload filename not fully sanitized |
| Syllabus file cleanup | UNKNOWN — stored permanently in uploads/syllabi/ |

---

## PHASE 12 — VOICE / STT AUDIT

| Feature | Status |
|---------|--------|
| TTS (edge-tts) | IMPLEMENTED — in-memory MP3 bytes, SHA-256 LRU cache |
| STT (Groq Whisper) | IMPLEMENTED — in-memory processing, no audio saved to disk |
| Technical vocab prompting | YES — custom 896-char Whisper prompt |
| Audio not persisted | YES — privacy preserved |
| No auth on `/voice/tts` | MEDIUM ISSUE — endpoint is publicly accessible |

---

## PHASE 13 — SECURITY AUDIT

| Issue | Severity | Detail |
|-------|----------|--------|
| Real Groq API key in .env | CRITICAL | Key present; .env not git-tracked (good); key should be rotated after demo |
| Weak JWT secret | HIGH | `my-super-secret-random-key-1234567890` — predictable, low entropy |
| No auth on `/voice/tts` | MEDIUM | Public access to TTS synthesis |
| Database password in env file | MEDIUM | Visible in `.env` (not git tracked) |
| CORS: localhost only | LOW | Dev-mode only, acceptable |
| JWT in localStorage | LOW | Standard SPA pattern; acceptable for academic project |
| traceback.print_exc() | LOW | Console only, not user-facing |
| No rate limiting | LOW | Acceptable for academic demo |
| chroma_db/ in git | MEDIUM | 14MB+ binary data committed; contains stale session data |

---

## PHASE 14 — CODE QUALITY

### Must Fix Before Review

| ID | Location | Issue |
|----|----------|-------|
| CQ-1 | `interviews.py:62` | `_active_user_syllabus` in-memory dict — lost on server restart |
| CQ-2 | `config.py` | `GROQ_FALLBACK_MODEL` not loaded — dead env var |
| CQ-3 | `InterviewSetup.jsx` | No JD missing warning — interview will fail silently |
| CQ-4 | `question_service.py` | `get_groq_model()` calls `sys.exit(1)` — SystemExit wrapper mitigates but risky |

### Optional Improvements

| ID | Location | Issue |
|----|----------|-------|
| CQ-5 | Multiple locations | Dev artifacts (scratch/, generate_pdf.py, get_samples.py) in backend |
| CQ-6 | `setup_database*.sql` | 5 schema versions — no canonical one |
| CQ-7 | `App.jsx` | No 404 route — unknown URLs render blank |
| CQ-8 | `Dashboard.jsx` | Hardcoded badge labels |
| CQ-10 | Entire project | Zero automated tests |

---

## PHASE 15-16 — PERFORMANCE & BUILD

| Check | Status |
|-------|--------|
| Python imports | PASS |
| Backend startup | PASS |
| Frontend dev server | PASS (6575ms) |
| npm run build | NOT RUN |
| Python tests | NONE — zero test files |
| Jest/frontend tests | NONE |
| SentenceTransformer lazy load | May cause slow first question (expected) |

---

## PHASE 17 — GIT / REPOSITORY AUDIT

| Item | Tracked? | Should Be? |
|------|----------|-----------|
| `.env` | NO | NO (correct) |
| `venv/` | NO | NO (correct) |
| `frontend/dist/` | NO | NO (correct) |
| `chroma_db/` binary files | YES | OPTIONAL — intentional for demo |
| `e2e_full_audit_*.webp` | YES | NO — should be gitignored |
| `scratch/` directories | YES (partially) | NO |

### Missing .gitignore Entries
- `*.webp` (audit screenshots)
- `scratch/`
- `backend/scratch/`

---

## COMPLETE BUG LIST

### BLOCKERS
None — basic functionality is operational.

### CRITICAL
| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| BUG-01 | `interviews.py:62` | Syllabus state lost on server restart (in-memory dict) | Use DB-stored `syllabus_state` or accept limitation |
| BUG-02 | `InterviewSetup.jsx` | No JD upload warning — interview start fails without JD | Add JD status check |

### HIGH
| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| BUG-03 | `config.py` | `GROQ_FALLBACK_MODEL` not loaded | Add to config.py |
| BUG-04 | `interviews.py:547` | `/voice/tts` has no authentication | Add `Depends(get_current_user)` |
| BUG-05 | `App.jsx` | No 404 route — unknown URLs render blank | Add catch-all `<Route path="*">` |

### MEDIUM
| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| BUG-06 | `Dashboard.jsx` | Hardcoded badge labels for new users | Remove or make dynamic |
| BUG-07 | `.env` | Weak JWT secret | Generate 64-char hex secret |
| BUG-08 | `backend/` | 5 SQL setup files | Identify and keep only canonical one |

### LOW
| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| BUG-09 | `.gitignore` | Missing entries for *.webp, scratch/ | Add entries |
| BUG-10 | Root dir | `e2e_full_audit_*.webp` committed | Remove from git |
| BUG-11 | `README.md` | 1-line README | Write full README |

---

## FEATURE STATUS MATRIX

| Feature | Status | Notes |
|---------|--------|-------|
| User registration & login | IMPLEMENTED AND VERIFIED | bcrypt + JWT, tested live |
| Resume upload + parsing | IMPLEMENTED AND VERIFIED | PyMuPDF, skills/projects extracted |
| Job Description upload | IMPLEMENTED | Not browser-tested in this audit |
| Skill mapping (Resume + JD) | IMPLEMENTED | Group A + B priority model |
| Interview setup | IMPLEMENTED AND VERIFIED | Guards for missing resume |
| Adaptive interview engine | IMPLEMENTED | Bloom + difficulty progression |
| RAG question generation | IMPLEMENTED | ChromaDB + MiniLM + Groq |
| Answer evaluation (multi-signal) | IMPLEMENTED | LLM + embeddings + concept coverage |
| Bloom's Taxonomy progression | IMPLEMENTED | 6 levels, deterministic |
| Interview results | IMPLEMENTED | Per-Q scores, feedback |
| PDF report | IMPLEMENTED | reportlab |
| Interview history | IMPLEMENTED AND VERIFIED | Empty state correct |
| Performance analytics | IMPLEMENTED AND VERIFIED | Real data, empty state correct |
| Voice TTS | IMPLEMENTED | edge-tts (offline) |
| Voice STT | IMPLEMENTED | Groq Whisper |
| Syllabus mode | IMPLEMENTED | Separate RAG pipeline |
| 404 route | NOT IMPLEMENTED | Blank page on unknown URL |
| Automated tests | NOT IMPLEMENTED | Zero tests |
| Token refresh | NOT IMPLEMENTED | 24h single JWT |
| Syllabus state persistence | PARTIAL | In-memory only |
| GROQ_FALLBACK_MODEL | PARTIAL | In .env but not read by config.py |

---

## REVIEWER READINESS

### Will Impress
- Full-stack application actually runs without errors
- Real MySQL database with well-structured schema
- Real RAG pipeline (ChromaDB + SentenceTransformers)
- Real deterministic adaptive engine (not LLM-driven — a strength)
- Real multi-signal evaluation (LLM + semantic similarity + concept coverage)
- Real voice TTS (offline-capable) + STT (Groq Whisper)
- Professional, polished UI with empty state handling
- JD-driven skill mapping (novel feature not commonly seen)
- Syllabus mode (second distinct interview mode)
- PDF report generation

### Could Concern Reviewers
- Empty README (critical gap)
- No automated tests
- Static badge labels in dashboard may appear as fake data
- Multiple setup_database SQL files — no clear canonical schema
- Interview setup doesn't warn about missing JD

### Will NOT Work If Groq API Fails
- Question generation → `[GENERATION FAILED]` stored in DB
- Answer evaluation → zero scores returned (safe defaults active)
- Voice STT → fails
- TTS: edge-tts is offline — this WILL still work

---

## RECOMMENDED FIX ORDER (After PROCEED)

### Priority 1 — Before Demo (Critical)
1. BUG-02: Add JD check to InterviewSetup.jsx
2. BUG-06: Fix hardcoded dashboard badge labels
3. BUG-11: Write complete README.md

### Priority 2 — Before Demo (High)
4. BUG-03: Add GROQ_FALLBACK_MODEL to config.py
5. BUG-04: Add auth to /voice/tts endpoint
6. BUG-05: Add 404 catch-all route to App.jsx

### Priority 3 — Before Final Submission (Medium)
7. BUG-07: Replace JWT secret with secure value
8. BUG-08: Consolidate SQL setup files

### Priority 4 — Documentation
9. Create docs/SmartInterview_Final_Audit_Report.md
10. Create docs/SmartInterview_SRS_Source_of_Truth.md
11. Create docs/SmartInterview_Research_Paper_Source_of_Truth.md
12. Create docs/SmartInterview_Project_Fact_Sheet.md
13. Update .gitignore

---

## STOP — AWAITING "PROCEED" COMMAND

No application code changes have been made during this audit.
The application is running (backend :8000, frontend :5174).
Say **PROCEED** to begin implementing fixes in priority order.
