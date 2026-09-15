from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class JobDescriptionResponse(BaseModel):
    id: int
    filename: str
    skills: Optional[List[str]] = []
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SkillMappingResponse(BaseModel):
    matched_skills: List[str] = []   # Group A: JD ∩ Resume
    gap_skills: List[str] = []       # Group B: JD - Resume
    resume_only: List[str] = []      # Resume - JD (not in interview plan)
    interview_skills: List[str] = [] # Ordered: Group A + Group B
