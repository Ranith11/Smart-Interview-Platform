from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    name = Column(String(255), nullable=True)
    skills = Column(JSON)
    projects = Column(JSON)
    experience = Column(JSON)
    education = Column(JSON)
    raw_text = Column(Text)
    page_count = Column(Integer)
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="resumes")
    sessions = relationship("InterviewSession", back_populates="resume", cascade="all, delete-orphan")
