from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    total_interviews: int = 0
    total_questions: int = 0
    total_answered: int = 0

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


class PerformanceResponse(BaseModel):
    """Aggregated performance data from actual evaluated interviews."""
    has_data: bool = False
    overall_average: Optional[float] = None
    skill_performance: Dict[str, Any] = {}
    bloom_progression: List[Dict[str, Any]] = []
    strengths: List[str] = []
    weak_areas: List[str] = []
    recommendations: List[Dict[str, Any]] = []
    recent_interviews: List[Dict[str, Any]] = []
