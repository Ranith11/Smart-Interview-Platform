"""
SmartInterview — Application Configuration
Loads all settings from the project-root .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level above backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── Database ──────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/smartinterview"
)

# ── JWT ───────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

# ── Groq / AI ────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# ── Paths ─────────────────────────────────────────────────
UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

CHROMA_DB_DIR = str(PROJECT_ROOT / "chroma_db")
PROMPTS_FILE = str(PROJECT_ROOT / "prompts" / "question_generation.json")
SCRIPTS_DIR = str(PROJECT_ROOT / "scripts")
