"""
SmartInterview — Interview Router (Weeks 7-10)

Endpoints:
    POST /api/interviews/start              — Create adaptive session + first question
    GET  /api/interviews/history            — List all user interviews
    GET  /api/interviews/{id}               — Get interview session state
    GET  /api/interviews/{id}/results       — Get rich results for a session
    GET  /api/interviews/{id}/questions/{num} — Get single question (legacy)
    POST /api/interviews/{id}/questions/{question_id}/answer — Submit answer (adaptive)
    POST /api/interviews/{id}/complete      — Mark interview complete

CORRECTION 1: Uses question_id (database ID) consistently in the adaptive answer endpoint.
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import SYLLABUS_UPLOAD_DIR
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.interview import InterviewSession
from app.models.question import InterviewQuestion, Answer, AnswerEvaluation
from app.schemas.interview import (
    StartInterviewRequest,
    SessionResponse,
    QuestionResponse,
    AnswerRequest,
    HistoryItem,
    AdaptiveStartResponse,
    AdaptiveAnswerResponse,
    EvaluationResponse,
    SessionResultsResponse,
)
from app.services.interview_service import (
    create_interview_session,
    submit_and_evaluate,
    submit_answer,
    complete_interview,
    get_session_results,
)

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


ALLOWED_SYLLABUS_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_SYLLABUS_FILE_SIZE = 20 * 1024 * 1024  # 20 MB per file


@router.post("/upload-syllabus", status_code=status.HTTP_200_OK)
async def upload_syllabus(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload one or more syllabus / reference files (PDF or TXT).
    Extracts content, creates a temporary RAG, detects topics,
    and returns a unique syllabus_id + topic list for the frontend.
    """
    from app.services.syllabus_rag_service import (
        create_temporary_rag_from_files,
        extract_topics_from_chunks,
        infer_subject_from_text,
        extract_text_from_file,
        chunk_text,
    )

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    saved_paths: list[str] = []
    all_text_sample = ""
    filename_hints: list[str] = []

    for upload in files:
        # Validate extension
        _, ext = os.path.splitext(upload.filename or "")
        if ext.lower() not in ALLOWED_SYLLABUS_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Allowed: PDF, TXT",
            )

        # Prevent path traversal — strip any directory components
        safe_name = os.path.basename(upload.filename or "file")
        if not safe_name or safe_name in (".", ".."):
            safe_name = "upload"

        content = await upload.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"File '{safe_name}' is empty")
        if len(content) > MAX_SYLLABUS_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File '{safe_name}' exceeds 20 MB limit",
            )

        # Save with a unique prefix to avoid collisions
        unique_name = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{safe_name}"
        file_path = os.path.join(str(SYLLABUS_UPLOAD_DIR), unique_name)
        with open(file_path, "wb") as f:
            f.write(content)

        saved_paths.append(file_path)
        filename_hints.append(safe_name)

    # Generate a unique temp_id for this upload session
    temp_id = uuid.uuid4().hex

    # Infer subject from combined content
    try:
        first_text = extract_text_from_file(saved_paths[0])
        all_text_sample = first_text[:3000]
        subject = infer_subject_from_text(all_text_sample, filename_hints[0])
    except Exception:
        subject = os.path.splitext(filename_hints[0])[0].replace("_", " ").title()

    # Build temp RAG
    try:
        create_temporary_rag_from_files(
            temp_id=temp_id,
            file_paths=saved_paths,
            subject=subject,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded material: {e}")

    # Dynamically detect topics from the chunks
    try:
        all_chunks: list[str] = []
        for fp in saved_paths:
            raw = extract_text_from_file(fp)
            all_chunks.extend(chunk_text(raw))
        topics = extract_topics_from_chunks(all_chunks, subject)
    except Exception as e:
        topics = [subject]

    return {
        "syllabus_id": temp_id,
        "subject": subject,
        "topics": topics,
        "files_processed": len(saved_paths),
    }

@router.post("/start", status_code=status.HTTP_201_CREATED)
def start_interview(
    req: StartInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new adaptive interview. Returns session + first question only."""
    try:
        result = create_interview_session(
            db=db,
            user_id=current_user.id,
            resume_id=req.resume_id,
            difficulty=req.difficulty,
            question_type=req.question_type,
            question_count=req.question_count,
            selected_skills=req.selected_skills,
            mode=req.mode,
            syllabus_id=req.syllabus_id,
            selected_topics=req.selected_topics,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

    session = result["session"]
    question = result["current_question"]

    return {
        "session_id": session.id,
        "difficulty": session.difficulty,
        "question_type": session.question_type,
        "question_count": session.question_count,
        "selected_skills": session.selected_skills,
        "status": session.status,
        "is_adaptive": session.is_adaptive,
        "mode": session.mode,
        "syllabus_id": session.syllabus_id,
        "current_bloom_level": session.current_bloom_level,
        "current_question": {
            "id": question.id,
            "question_number": question.question_number,
            "skill": question.skill,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "question_text": question.question_text,
            "bloom_level": question.bloom_level,
            "bloom_level_number": question.bloom_level_number,
        },
    }


@router.get("/history", response_model=list[HistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.started_at.desc())
        .all()
    )

    result = []
    for s in sessions:
        answered = db.query(Answer).filter(Answer.session_id == s.id).count()

        # Calculate average score from evaluations (real data only)
        avg_score = None
        if s.is_adaptive:
            from sqlalchemy import func as sql_func
            avg_result = (
                db.query(sql_func.avg(AnswerEvaluation.overall_score))
                .join(Answer, AnswerEvaluation.answer_id == Answer.id)
                .filter(Answer.session_id == s.id)
                .scalar()
            )
            if avg_result is not None:
                avg_score = round(float(avg_result), 1)

        result.append(HistoryItem(
            id=s.id,
            difficulty=s.difficulty,
            question_type=s.question_type,
            question_count=s.question_count,
            status=s.status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            completion_reason=s.completion_reason,
            questions_answered=answered,
            selected_skills=s.selected_skills,
            is_adaptive=s.is_adaptive,
            average_score=avg_score,
        ))
    return result


@router.get("/{session_id}")
def get_interview(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get interview session with all questions generated so far."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    return _build_session_response(db, session)


@router.get("/{session_id}/results")
def get_results(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get rich results for a completed interview (evaluation data, skill breakdown, recommendations)."""
    try:
        results = get_session_results(db, current_user.id, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return results


@router.get("/{session_id}/questions/{question_num}", response_model=QuestionResponse)
def get_question(
    session_id: int,
    question_num: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single question by question number (legacy endpoint)."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id,
        InterviewQuestion.question_number == question_num,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = db.query(Answer).filter(Answer.question_id == question.id).first()
    evaluation = db.query(AnswerEvaluation).filter(
        AnswerEvaluation.question_id == question.id
    ).first()

    eval_data = None
    if evaluation:
        eval_data = EvaluationResponse(
            technical_score=evaluation.technical_score,
            completeness_score=evaluation.completeness_score,
            relevance_score=evaluation.relevance_score,
            semantic_similarity_score=evaluation.semantic_similarity_score,
            concept_coverage_score=evaluation.concept_coverage_score,
            overall_score=evaluation.overall_score,
            feedback=evaluation.feedback or "",
            strengths=evaluation.strengths or [],
            weaknesses=evaluation.weaknesses or [],
            concepts_expected=evaluation.concepts_expected or [],
            concepts_found=evaluation.concepts_found or [],
        )

    return QuestionResponse(
        id=question.id,
        question_number=question.question_number,
        skill=question.skill,
        question_type=question.question_type,
        difficulty=question.difficulty,
        question_text=question.question_text,
        answer_text=answer.answer_text if answer else None,
        bloom_level=question.bloom_level,
        bloom_level_number=question.bloom_level_number,
        evaluation=eval_data,
    )


@router.post("/{session_id}/questions/{question_id}/answer", status_code=status.HTTP_200_OK)
def answer_question(
    session_id: int,
    question_id: int,
    req: AnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit answer for an adaptive interview question.

    Uses question_id (database ID), NOT question_number.

    Flow: save answer → evaluate → update adaptive state → generate next question
    Returns: evaluation + next question (or completion signal)
    """
    # Check if this is an adaptive session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    if session.is_adaptive or session.mode == "syllabus":
        # Adaptive flow: evaluate + generate next
        try:
            result = submit_and_evaluate(
                db=db,
                user_id=current_user.id,
                session_id=session_id,
                question_id=question_id,
                answer_text=req.answer_text,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")

        # Build response
        next_q = None
        if result.get("next_question"):
            nq = result["next_question"]
            next_q = {
                "id": nq.id,
                "question_number": nq.question_number,
                "skill": nq.skill,
                "question_type": nq.question_type,
                "difficulty": nq.difficulty,
                "question_text": nq.question_text,
                "bloom_level": nq.bloom_level,
                "bloom_level_number": nq.bloom_level_number,
            }

        return {
            "evaluation": result["evaluation"],
            "next_question": next_q,
            "is_complete": result["is_complete"],
            "questions_answered": result["questions_answered"],
            "questions_remaining": result["questions_remaining"],
            "current_bloom_level": result.get("current_bloom_level"),
            "current_difficulty": result.get("current_difficulty"),
        }
    else:
        # Legacy flow: just save the answer
        # For legacy sessions, question_id might actually be question_number
        # Try to find by ID first, then fall back to question_number
        question = db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id,
            InterviewQuestion.session_id == session_id,
        ).first()

        if not question:
            # Fall back to question_number for backward compat
            question = db.query(InterviewQuestion).filter(
                InterviewQuestion.session_id == session_id,
                InterviewQuestion.question_number == question_id,
            ).first()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        try:
            answer = submit_answer(
                db=db,
                user_id=current_user.id,
                session_id=session_id,
                question_number=question.question_number,
                answer_text=req.answer_text,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return {"message": "Answer submitted", "answer_id": answer.id}


@router.post("/{session_id}/complete")
def complete(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark interview as completed and return results."""
    try:
        session = complete_interview(db, current_user.id, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return rich results if adaptive
    if session.is_adaptive:
        try:
            return get_session_results(db, current_user.id, session_id)
        except Exception:
            pass

    return _build_session_response(db, session)


def _build_session_response(db: Session, session: InterviewSession) -> dict:
    """Build a full session response with questions and their answers/evaluations."""
    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session.id)
        .order_by(InterviewQuestion.question_number)
        .all()
    )

    q_responses = []
    for q in questions:
        answer = db.query(Answer).filter(Answer.question_id == q.id).first()
        evaluation = db.query(AnswerEvaluation).filter(
            AnswerEvaluation.question_id == q.id
        ).first()

        eval_data = None
        if evaluation:
            eval_data = {
                "technical_score": evaluation.technical_score,
                "completeness_score": evaluation.completeness_score,
                "relevance_score": evaluation.relevance_score,
                "semantic_similarity_score": evaluation.semantic_similarity_score,
                "concept_coverage_score": evaluation.concept_coverage_score,
                "overall_score": evaluation.overall_score,
                "feedback": evaluation.feedback or "",
                "strengths": evaluation.strengths or [],
                "weaknesses": evaluation.weaknesses or [],
            }

        q_responses.append({
            "id": q.id,
            "question_number": q.question_number,
            "skill": q.skill,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "answer_text": answer.answer_text if answer else None,
            "bloom_level": q.bloom_level,
            "bloom_level_number": q.bloom_level_number,
            "evaluation": eval_data,
        })

    return {
        "id": session.id,
        "difficulty": session.difficulty,
        "question_type": session.question_type,
        "question_count": session.question_count,
        "selected_skills": session.selected_skills,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "completion_reason": session.completion_reason,
        "is_adaptive": session.is_adaptive,
        "mode": session.mode,
        "syllabus_id": session.syllabus_id,
        "syllabus_state": session.syllabus_state,
        "current_bloom_level": session.current_bloom_level,
        "questions": q_responses,
    }
