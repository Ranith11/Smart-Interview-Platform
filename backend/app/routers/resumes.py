"""
SmartInterview — Resume Router
POST /api/resumes/upload
GET  /api/resumes/current
DELETE /api/resumes/{id}
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse
from app.services.resume_service import parse_resume_file

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Save file with unique name
    safe_name = f"{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(str(UPLOAD_DIR), safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse resume using existing Week 6 parser
    try:
        profile = parse_resume_file(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

    skills = profile.get("skills", [])
    if not skills:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail="No technical skills found in the resume")

    # Delete old resumes for this user (keep only latest)
    old_resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    for old in old_resumes:
        if os.path.exists(old.file_path):
            try:
                os.remove(old.file_path)
            except OSError:
                pass
        db.delete(old)

    # Save new resume record
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        skills=skills,
        projects=profile.get("projects", []),
        experience=profile.get("experience", []),
        education=profile.get("education", []),
        raw_text=profile.get("raw_text", ""),
        page_count=profile.get("page_count", 0),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeResponse.model_validate(resume)


@router.get("/current", response_model=ResumeResponse)
def get_current_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    return ResumeResponse.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except OSError:
            pass

    db.delete(resume)
    db.commit()
