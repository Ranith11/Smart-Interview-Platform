"""
SmartInterview — Question Generation Service
Wraps the EXISTING Week 6 generate_question.py functions.

This service imports the standalone functions directly from generate_question.py
WITHOUT modifying that file. Both the CLI and the API use the same engine.

Week 8 additions:
    - generate_single_question(): generates ONE question with Bloom-level guidance
    - Safe Groq model verification (no sys.exit)
    - Exposes singletons for use by evaluation_service.py
"""

import sys
import os
import importlib.util
import json
import time
import threading

from app.config import SCRIPTS_DIR, CHROMA_DB_DIR, PROMPTS_FILE

# ── Import existing Week 6 functions ──────────────────────
_gen_path = os.path.join(SCRIPTS_DIR, "generate_question.py")
_spec = importlib.util.spec_from_file_location("generate_question_mod", _gen_path)
_gen_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen_mod)

# All functions from Week 6, unchanged
load_prompts = _gen_mod.load_prompts
find_project_for_skill = _gen_mod.find_project_for_skill
resolve_skill_domains = _gen_mod.resolve_skill_domains
build_rag_query = _gen_mod.build_rag_query
retrieve_rag_context = _gen_mod.retrieve_rag_context
build_prompt = _gen_mod.build_prompt
call_groq = _gen_mod.call_groq
QUESTION_TYPES = _gen_mod.QUESTION_TYPES
SKILL_DOMAIN_MAP = _gen_mod.SKILL_DOMAIN_MAP

# ── Lazy-initialized singletons ──────────────────────────
_lock = threading.Lock()
_embedding_model = None
_chroma_collection = None
_groq_client = None
_groq_model = None
_prompts = None


def _init_rag():
    """Initialize SentenceTransformer + ChromaDB (once, thread-safe)."""
    global _embedding_model, _chroma_collection
    if _embedding_model is not None:
        return
    with _lock:
        if _embedding_model is not None:
            return
        from sentence_transformers import SentenceTransformer
        import chromadb
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        _chroma_collection = client.get_collection(name="technical_kb")


def _init_groq():
    """Initialize Groq client (once, thread-safe). Safe — no sys.exit."""
    global _groq_client, _groq_model
    if _groq_client is not None:
        return
    with _lock:
        if _groq_client is not None:
            return
        from groq import Groq
        _groq_client = Groq()
        # Safe model verification — wraps sys.exit risk
        try:
            _groq_model = _gen_mod.get_groq_model(_groq_client)
        except SystemExit:
            # get_groq_model calls sys.exit(1) on failure — catch it
            # Fall back to configured model
            _groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            print(f"[QuestionService] WARNING: Model verification failed, using fallback: {_groq_model}")
        except Exception as e:
            _groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            print(f"[QuestionService] WARNING: Model verification error: {e}, using fallback: {_groq_model}")


def _get_prompts():
    """Load prompts once."""
    global _prompts
    if _prompts is None:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            _prompts = json.load(f)
    return _prompts


# ── Singleton Accessors (for evaluation_service) ─────────

def get_embedding_model():
    """Get the lazy-initialized embedding model singleton."""
    _init_rag()
    return _embedding_model


def get_groq_client():
    """Get the lazy-initialized Groq client singleton."""
    _init_groq()
    return _groq_client


def get_groq_model_name():
    """Get the verified Groq model name."""
    _init_groq()
    return _groq_model


def get_chroma_collection():
    """Get the ChromaDB collection singleton."""
    _init_rag()
    return _chroma_collection


# ── Single Question Generation (Week 8 — Adaptive) ──────

def generate_single_question(
    skill: str,
    difficulty: str,
    question_type: str,
    bloom_level=None,
    projects: list[dict] | None = None,
    previous_questions: list[str] | None = None,
) -> dict:
    """
    Generate ONE interview question with optional Bloom-level guidance.

    This reuses the existing Week 6 pipeline:
        resolve_skill_domains → retrieve_rag_context → build_prompt → call_groq

    Args:
        skill: The technical skill to ask about
        difficulty: easy / medium / hard
        question_type: conceptual / practical / technical_reasoning / scenario / project
        bloom_level: Optional BloomLevel object for cognitive-level guidance
        projects: Candidate's projects for personalization
        previous_questions: Previously asked questions for deduplication

    Returns:
        Dict with: skill, question_type, difficulty, question_text,
                    bloom_level, bloom_level_number, rag_context, project_context
    """
    _init_rag()
    _init_groq()
    prompts = _get_prompts()

    projects = projects or []
    previous_questions = previous_questions or []

    # Resolve skill → knowledge-base domains
    skill_domains = resolve_skill_domains(skill)

    # RAG retrieval (domain-filtered) — uses existing function
    rag_chunks, rag_query = retrieve_rag_context(
        skill, _embedding_model, _chroma_collection, domains=skill_domains
    )

    # Optional project context — uses existing function
    project_ctx = find_project_for_skill(skill, projects)

    # Build prompt — uses existing function with Bloom augmentation
    system_prompt, user_prompt = build_prompt(
        skill=skill,
        rag_chunks=rag_chunks,
        project_context=project_ctx,
        difficulty=difficulty,
        question_type=question_type,
        previous_questions=previous_questions,
        prompts=prompts,
    )

    # Add Bloom-level guidance to the user prompt
    if bloom_level is not None:
        bloom_instruction = (
            f"\n\nCognitive Level: {bloom_level.name}\n"
            f"{bloom_level.question_guidance}\n"
            f"The question MUST target the '{bloom_level.name}' cognitive level."
        )
        user_prompt += bloom_instruction

    # Call Groq — uses existing function with retry/backoff
    question_text = call_groq(system_prompt, user_prompt, _groq_client, _groq_model)

    # Serialize RAG chunk metadata (not full text, to keep DB clean)
    rag_meta = None
    rag_context_full = None  # Full context for evaluation later
    if rag_chunks:
        rag_meta = [
            {"chunk_id": c["chunk_id"], "domain": c["domain"], "concept": c["concept"]}
            for c in rag_chunks[:3]
        ]
        rag_context_full = [
            {"chunk_id": c["chunk_id"], "domain": c["domain"], "concept": c["concept"], "text": c.get("text", "")}
            for c in rag_chunks[:3]
        ]

    proj_meta = None
    if project_ctx:
        proj_meta = {
            "name": project_ctx.get("name", ""),
            "technologies": project_ctx.get("technologies", []),
        }

    result = {
        "skill": skill,
        "question_type": question_type,
        "difficulty": difficulty,
        "question_text": question_text or "[GENERATION FAILED]",
        "rag_context": rag_meta,
        "rag_context_full": rag_context_full,  # kept for evaluation, NOT stored in DB
        "project_context": proj_meta,
        "bloom_level": bloom_level.id if bloom_level else None,
        "bloom_level_number": bloom_level.order if bloom_level else None,
    }

    return result


# ── Batch Question Generation (Week 7 — Legacy) ─────────

def generate_questions(
    skills: list[str],
    projects: list[dict],
    difficulty: str,
    question_type: str,
    count: int,
    selected_skills: list[str] | None = None,
) -> list[dict]:
    """
    Generate interview questions using the existing Week 6 engine.
    PRESERVED for backward compatibility with legacy (non-adaptive) sessions.

    Args:
        skills: All skills extracted from resume
        projects: All projects extracted from resume
        difficulty: easy / medium / hard
        question_type: conceptual / practical / technical_reasoning / scenario / project / mixed
        count: Number of questions (1-10)
        selected_skills: Optional subset of skills to use. If None, uses all skills.

    Returns:
        List of dicts: [{skill, question_type, difficulty, question_text, rag_context, project_context}, ...]
    """
    _init_rag()
    _init_groq()
    prompts = _get_prompts()

    # Use selected skills if provided, otherwise use all
    use_skills = selected_skills if selected_skills else skills
    if not use_skills:
        use_skills = skills

    # Deterministic rotation (same as Week 6 main())
    skill_rotation = [use_skills[i % len(use_skills)] for i in range(count)]

    # Question type rotation (same as Week 6 main())
    if question_type == "mixed":
        slot_types = [QUESTION_TYPES[i % len(QUESTION_TYPES)] for i in range(count)]
    else:
        slot_types = [question_type] * count

    generated = []
    previous_questions = []

    for i in range(count):
        skill = skill_rotation[i]
        q_type = slot_types[i]

        # Resolve skill → knowledge-base domains
        skill_domains = resolve_skill_domains(skill)

        # RAG retrieval (domain-filtered) — uses existing function
        rag_chunks, rag_query = retrieve_rag_context(
            skill, _embedding_model, _chroma_collection, domains=skill_domains
        )

        # Optional project context — uses existing function
        project_ctx = find_project_for_skill(skill, projects)

        # Build prompt — uses existing function
        system_prompt, user_prompt = build_prompt(
            skill=skill,
            rag_chunks=rag_chunks,
            project_context=project_ctx,
            difficulty=difficulty,
            question_type=q_type,
            previous_questions=previous_questions,
            prompts=prompts,
        )

        # Call Groq — uses existing function with retry/backoff
        question_text = call_groq(system_prompt, user_prompt, _groq_client, _groq_model)

        if question_text:
            previous_questions.append(question_text)

            # Serialize RAG chunk metadata (not full text, to keep DB clean)
            rag_meta = None
            if rag_chunks:
                rag_meta = [
                    {"chunk_id": c["chunk_id"], "domain": c["domain"], "concept": c["concept"]}
                    for c in rag_chunks[:3]
                ]

            proj_meta = None
            if project_ctx:
                proj_meta = {
                    "name": project_ctx.get("name", ""),
                    "technologies": project_ctx.get("technologies", []),
                }

            generated.append({
                "question_number": i + 1,
                "skill": skill,
                "question_type": q_type,
                "difficulty": difficulty,
                "question_text": question_text,
                "rag_context": rag_meta,
                "project_context": proj_meta,
            })
        else:
            generated.append({
                "question_number": i + 1,
                "skill": skill,
                "question_type": q_type,
                "difficulty": difficulty,
                "question_text": "[GENERATION FAILED]",
                "rag_context": None,
                "project_context": None,
            })

        # Rate limit spacing between questions
        if i < count - 1:
            time.sleep(1)

    return generated
