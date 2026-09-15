from sqlalchemy import Column, Integer, String, Text, Float, Enum, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, nullable=False)
    skill = Column(String(100), nullable=False)
    question_type = Column(String(50), nullable=False)
    difficulty = Column(Enum("easy", "medium", "hard"), nullable=False)
    question_text = Column(Text, nullable=False)
    rag_context = Column(JSON, nullable=True)
    project_context = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Week 8 — Bloom Taxonomy fields
    bloom_level = Column(String(20), nullable=True)         # e.g. "remember", "apply"
    bloom_level_number = Column(Integer, nullable=True)     # e.g. 1, 3

    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")
    evaluation = relationship("AnswerEvaluation", back_populates="question", uselist=False, cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, unique=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    answer_text = Column(Text)
    submitted_at = Column(DateTime, server_default=func.now())

    question = relationship("InterviewQuestion", back_populates="answer")
    session = relationship("InterviewSession", back_populates="answers")
    evaluation = relationship("AnswerEvaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class AnswerEvaluation(Base):
    """Week 9 — Stores structured evaluation results for each answer."""
    __tablename__ = "answer_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False, unique=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False)

    # Scores (0-100)
    technical_score = Column(Integer, nullable=False, default=0)
    completeness_score = Column(Integer, nullable=False, default=0)
    relevance_score = Column(Integer, nullable=False, default=0)
    semantic_similarity_score = Column(Integer, nullable=False, default=0)
    concept_coverage_score = Column(Integer, nullable=False, default=0)
    overall_score = Column(Integer, nullable=False, default=0)

    # Qualitative feedback
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)        # list of strings
    weaknesses = Column(JSON, nullable=True)       # list of strings
    concepts_expected = Column(JSON, nullable=True) # list of strings
    concepts_found = Column(JSON, nullable=True)    # list of strings

    evaluated_at = Column(DateTime, server_default=func.now())

    answer = relationship("Answer", back_populates="evaluation")
    question = relationship("InterviewQuestion", back_populates="evaluation")
