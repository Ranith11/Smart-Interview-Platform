from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class StartInterviewRequest(BaseModel):
    resume_id: Optional[int] = None
    difficulty: Optional[str] = Field(default="medium", pattern="^(easy|medium|hard)$")
    question_type: Optional[str] = Field(default="mixed")
    question_count: Optional[int] = Field(default=None)  # Ignored for adaptive, kept for legacy
    selected_skills: Optional[List[str]] = None
    mode: Optional[str] = "normal"  # "normal" or "syllabus"
    syllabus_id: Optional[str] = None
    selected_topics: Optional[List[str]] = None


# ── Evaluation (Week 9) ──────────────────────────────────

class EvaluationResponse(BaseModel):
    technical_score: int = 0
    completeness_score: int = 0
    relevance_score: int = 0
    semantic_similarity_score: int = 0
    concept_coverage_score: int = 0
    overall_score: int = 0
    feedback: str = ""
    strengths: List[str] = []
    weaknesses: List[str] = []
    concepts_expected: List[str] = []
    concepts_found: List[str] = []


# ── Question Response ─────────────────────────────────────

class QuestionResponse(BaseModel):
    id: int
    question_number: int
    skill: str
    question_type: str
    difficulty: str
    question_text: str
    answer_text: Optional[str] = None
    bloom_level: Optional[str] = None
    bloom_level_number: Optional[int] = None
    evaluation: Optional[EvaluationResponse] = None

    class Config:
        from_attributes = True


# ── Adaptive Answer Response (Week 8-9) ───────────────────

class AdaptiveAnswerResponse(BaseModel):
    """Returned after submitting an answer in adaptive mode."""
    evaluation: EvaluationResponse
    next_question: Optional[QuestionResponse] = None
    is_complete: bool = False
    questions_answered: int = 0
    questions_remaining: int = 0
    current_bloom_level: Optional[str] = None
    current_difficulty: Optional[str] = None


# ── Session Response ──────────────────────────────────────

class SessionResponse(BaseModel):
    id: int
    difficulty: str
    question_type: str
    question_count: int
    selected_skills: Optional[List[str]] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_reason: Optional[str] = None
    is_adaptive: Optional[bool] = None
    current_bloom_level: Optional[str] = None
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True


# ── Adaptive Session Start Response ───────────────────────

class AdaptiveStartResponse(BaseModel):
    """Response for starting a new adaptive interview."""
    session_id: int
    difficulty: str
    question_type: str
    question_count: int
    selected_skills: List[str]
    status: str
    completion_reason: Optional[str] = None
    is_adaptive: bool = True
    current_bloom_level: Optional[str] = None
    current_question: QuestionResponse


# ── Answer Request ────────────────────────────────────────

class AnswerRequest(BaseModel):
    answer_text: str = Field(default="", max_length=5000)


# ── History ───────────────────────────────────────────────

class HistoryItem(BaseModel):
    id: int
    difficulty: str
    question_type: str
    question_count: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_reason: Optional[str] = None
    questions_answered: int = 0
    selected_skills: Optional[List[str]] = None
    is_adaptive: Optional[bool] = None
    average_score: Optional[float] = None

    class Config:
        from_attributes = True


# ── Results ───────────────────────────────────────────────

class SkillPerformanceItem(BaseModel):
    average_score: float
    questions: int

class SessionResultsResponse(BaseModel):
    session: Dict[str, Any]
    overall_average_score: float = 0
    skill_performance: Dict[str, SkillPerformanceItem] = {}
    bloom_progression: List[Dict[str, Any]] = []
    questions: List[QuestionResponse] = []
    recommendations: List[Dict[str, Any]] = []


# ── Legacy (kept for backward compat) ─────────────────────

class ResultResponse(BaseModel):
    session: SessionResponse
    questions: List[QuestionResponse] = []
    total_questions: int = 0
    total_answered: int = 0
    skills_evaluated: List[str] = []
