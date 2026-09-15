"""
SmartInterview — Job Description Router

POST   /api/job-descriptions/upload    — Upload and parse a JD PDF
GET    /api/job-descriptions/current   — Get current user's JD
DELETE /api/job-descriptions/{id}      — Delete a JD
GET    /api/job-descriptions/mapping   — Get Resume + JD skill mapping
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.schemas.job_description import JobDescriptionResponse, SkillMappingResponse
from app.services.jd_service import parse_jd_file, map_skills

router = APIRouter(prefix="/api/job-descriptions", tags=["job-descriptions"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB — same as resume upload


@router.post("/upload", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def upload_job_description(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Save file with unique name in the shared uploads dir
    safe_name = f"jd_{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(str(UPLOAD_DIR), safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse using deterministic JD service
    try:
        profile = parse_jd_file(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"Failed to parse job description: {str(e)}")

    # Delete old JDs for this user (keep only latest, same pattern as Resume)
    old_jds = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).all()
    for old in old_jds:
        if os.path.exists(old.file_path):
            try:
                os.remove(old.file_path)
            except OSError:
                pass
        db.delete(old)

    # Persist new JD record
    jd = JobDescription(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        skills=profile.get("skills", []),
        raw_text=profile.get("raw_text", ""),
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)

    return JobDescriptionResponse.model_validate(jd)


@router.get("/current", response_model=JobDescriptionResponse)
def get_current_jd(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.uploaded_at.desc())
        .first()
    )
    if not jd:
        raise HTTPException(status_code=404, detail="No job description uploaded yet")
    return JobDescriptionResponse.model_validate(jd)


@router.get("/mapping", response_model=SkillMappingResponse)
def get_skill_mapping(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.uploaded_at.desc())
        .first()
    )

    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    if not jd:
        raise HTTPException(status_code=404, detail="No job description uploaded yet")

    result = map_skills(resume.skills or [], jd.skills or [])
    return SkillMappingResponse(**result)


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_description(
    jd_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    if os.path.exists(jd.file_path):
        try:
            os.remove(jd.file_path)
        except OSError:
            pass

    db.delete(jd)
    db.commit()
