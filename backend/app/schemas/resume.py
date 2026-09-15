from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class ResumeResponse(BaseModel):
    id: int
    filename: str
    skills: Optional[List[str]] = None
    projects: Optional[List[Any]] = None
    experience: Optional[List[Any]] = None
    education: Optional[List[str]] = None
    page_count: Optional[int] = None
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
