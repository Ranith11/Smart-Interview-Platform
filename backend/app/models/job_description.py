from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    skills = Column(JSON)
    raw_text = Column(Text)
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="job_descriptions")
    sessions = relationship("InterviewSession", back_populates="job_description")
