"""
SmartInterview — Users Router
GET  /api/users/profile
PUT  /api/users/profile
GET  /api/users/stats
GET  /api/users/performance  (Week 10)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.user import UserProfile, UpdateProfileRequest, PerformanceResponse
from app.schemas.resume import ResumeResponse
from app.services.interview_service import get_user_stats, get_user_performance

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/profile")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stats = get_user_stats(db, current_user.id)

    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "created_at": str(current_user.created_at) if current_user.created_at else None,
        },
        "resume": ResumeResponse.model_validate(resume).model_dump() if resume else None,
        "stats": stats,
    }


@router.put("/profile")
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.name:
        current_user.name = req.name

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
    }


@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_stats(db, current_user.id)


@router.get("/performance", response_model=PerformanceResponse)
def get_performance(
    mode: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get aggregated performance data across all evaluated interviews.
    Returns ONLY real data — no fake percentages or placeholders.
    If no evaluated interviews exist, returns has_data=False with empty state.
    """
    return get_user_performance(db, current_user.id, mode)
