import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../../.."))

from app.database import SessionLocal
from app.models.user import User
from app.models.interview import InterviewSession
from app.models.question import InterviewQuestion, AnswerEvaluation
from app.services.interview_service import get_user_performance
import json

db = SessionLocal()

def verify():
    # Find a user with both normal and syllabus sessions
    users = db.query(User).all()
    target_user = None
    
    for u in users:
        sessions = db.query(InterviewSession).filter(InterviewSession.user_id == u.id, InterviewSession.status == "completed").all()
        modes = [s.mode for s in sessions]
        if "normal" in modes and "syllabus" in modes:
            target_user = u
            break
            
    if not target_user:
        # If we can't find one, just pick a user with normal completed, and we'll manually create a completed syllabus session for them
        target_user = db.query(User).first()
        if not target_user:
            print("No users in DB.")
            return

        # Let's forcefully create a normal and a syllabus session for target_user
        print(f"Creating mock sessions for User {target_user.id}...")
        
        # 1. Normal session completed
        s_normal = InterviewSession(user_id=target_user.id, resume_id=1, mode="normal", status="completed")
        db.add(s_normal)
        db.commit()
        
        q_norm = InterviewQuestion(session_id=s_normal.id, question_number=1, skill="Python", bloom_level="apply", bloom_level_number=3)
        db.add(q_norm)
        db.commit()
        
        ev_norm = AnswerEvaluation(question_id=q_norm.id, overall_score=85)
        db.add(ev_norm)
        db.commit()

        # 2. Syllabus session completed
        s_syll = InterviewSession(user_id=target_user.id, resume_id=1, mode="syllabus", status="completed")
        db.add(s_syll)
        db.commit()

        q_syll = InterviewQuestion(session_id=s_syll.id, question_number=1, skill="React", bloom_level="create", bloom_level_number=6)
        db.add(q_syll)
        db.commit()

        ev_syll = AnswerEvaluation(question_id=q_syll.id, overall_score=40)
        db.add(ev_syll)
        db.commit()

        # 3. Normal session incomplete
        s_inc = InterviewSession(user_id=target_user.id, resume_id=1, mode="normal", status="in_progress")
        db.add(s_inc)
        db.commit()
        print("Mock data created.")
    else:
        print(f"Found User {target_user.id} with both normal and syllabus completed sessions.")

    # Get performance
    perf = get_user_performance(db, target_user.id)
    
    print("\n" + "="*50)
    print("PERFORMANCE API DATA")
    print("="*50)
    
    print(f"Total Interviews Count (in data): {len(perf['recent_interviews'])}")
    
    modes_returned = [r.get("mode") for r in perf['recent_interviews']]
    print(f"Modes in recent_interviews: {modes_returned}")
    
    print(f"Overall Average Score: {perf['overall_average']}")
    
    skills = list(perf['skill_performance'].keys())
    print(f"Skills Evaluated: {skills}")
    
    blooms = list(perf['bloom_performance'].keys())
    print(f"Bloom Levels Present: {blooms}")
    
    print("\n" + "="*50)
    print("VERIFICATION CHECKLIST")
    print("="*50)
    
    # Check 1: No syllabus mode
    pass_no_syllabus = "syllabus" not in modes_returned
    print(f"1. No syllabus mode sessions returned: {'PASS' if pass_no_syllabus else 'FAIL'}")
    
    # Check 2: Total count matches normal mode completed count
    db_normal_completed = db.query(InterviewSession).filter(
        InterviewSession.user_id == target_user.id, 
        InterviewSession.mode == "normal", 
        InterviewSession.status == "completed"
    ).count()
    pass_count = (len(perf['recent_interviews']) == db_normal_completed)
    print(f"2. Total count ({len(perf['recent_interviews'])}) matches DB completed normal ({db_normal_completed}): {'PASS' if pass_count else 'FAIL'}")

    # Check 3: Check skills don't include Syllabus mode skills (if we created mock data, "React" was syllabus)
    pass_skills = "React" not in skills
    print(f"3. Skills do NOT include syllabus-only topics: {'PASS' if pass_skills else 'FAIL'}")

if __name__ == "__main__":
    verify()
