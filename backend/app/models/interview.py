from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    difficulty = Column(Enum("easy", "medium", "hard"), nullable=False, default="medium")
    question_type = Column(String(50), nullable=False, default="mixed")
    question_count = Column(Integer, nullable=False, default=5)
    selected_skills = Column(JSON)
    status = Column(Enum("in_progress", "completed", "abandoned"), default="in_progress")
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Week 8 — Adaptive learning fields
    is_adaptive = Column(Boolean, nullable=True, default=True)
    adaptive_state = Column(JSON, nullable=True)           # serialized AdaptiveState
    current_bloom_level = Column(String(20), nullable=True) # current Bloom level id
    final_recommendations = Column(JSON, nullable=True)     # generated at completion
    completion_reason = Column(String(50), nullable=True)   # manual, assessment_complete, max_questions_safety_limit
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", back_populates="sessions")
    resume = relationship("Resume", back_populates="sessions")
    job_description = relationship("JobDescription", back_populates="sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")
