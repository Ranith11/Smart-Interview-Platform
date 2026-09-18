"""
SmartInterview — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, resumes, interviews, users, speech

app = FastAPI(
    title="SmartInterview API",
    description="AI-powered Technical Mock Interview Platform",
    version="7.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(interviews.router)
app.include_router(users.router)
app.include_router(speech.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SmartInterview API"}
