import sys

# Fix Windows terminal encoding for UTF-8 LLM outputs
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, resumes, interviews, users, job_descriptions

app = FastAPI(
    title="SmartInterview API",
    description="AI-powered Technical Mock Interview Platform",
    version="7.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(job_descriptions.router)
app.include_router(interviews.router)
app.include_router(users.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SmartInterview API"}


@app.get("/api/knowledge-stats")
def get_knowledge_stats():
    import json
    import os
    from app.config import PROJECT_ROOT, CHROMA_DB_DIR
    import chromadb

    stats_path = os.path.join(str(PROJECT_ROOT), "data", "knowledge_stats.json")
    stats = {}
    if os.path.exists(stats_path):
        try:
            with open(stats_path, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except Exception:
            pass

    # Inspect live collections in ChromaDB
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collections = client.list_collections()
        col_stats = {}
        for c in collections:
            col_stats[c.name] = c.count()
        stats["chroma_live_collections"] = col_stats
    except Exception as e:
        stats["chroma_live_error"] = str(e)

    return stats
