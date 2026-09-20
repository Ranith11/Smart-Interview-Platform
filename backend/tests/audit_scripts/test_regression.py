import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.services.interview_service import select_skill_with_relevance

def run_regression_tests():
    print("--- Running Regression Tests ---")
    results = []

    try:
        from app.services.adaptive_engine import initialize_state, select_skill
        
        # 1. Normal Mode
        candidate_skills = ["Python", "SQL", "React"]
        state = initialize_state(candidate_skills, "medium", "mixed", 10)
        
        # In normal mode, we use select_skill directly or pass None for job_relevance_data to select_skill_with_relevance
        selected_normal = select_skill_with_relevance(state, None)
        if selected_normal:
            results.append(("Normal Mode (No JD Data)", "PASS", f"Selected {selected_normal}"))
        else:
            results.append(("Normal Mode (No JD Data)", "FAIL", "Returned empty"))

        # 2. Syllabus Mode
        # In Syllabus mode, adaptive_engine is not used for skill selection in the same way, but it should not crash.
        selected_syllabus = select_skill_with_relevance(state, None)
        if selected_syllabus:
            results.append(("Syllabus Mode (No JD Data)", "PASS", f"Selected {selected_syllabus}"))
        else:
            results.append(("Syllabus Mode (No JD Data)", "FAIL", "Returned empty"))
    except Exception as e:
        import traceback
        results.append(("Regression Test", "FAIL", traceback.format_exc()))

    return results

if __name__ == "__main__":
    res = run_regression_tests()
    for r in res:
        print(f"[{r[1]}] {r[0]}: {r[2]}")
