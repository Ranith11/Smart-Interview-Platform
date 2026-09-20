import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.services.interview_service import select_skill_with_relevance

def run_adaptive_engine_tests():
    print("--- Running Adaptive Engine Tests ---")
    results = []

    try:
        job_relevance_data = {
            "skill_relevance": {
                "Python": "high",
                "SQL": "high",
                "Docker": "medium",
                "React": "low"
            },
            "job_skills": ["Python", "SQL", "Docker", "AWS"],
            "candidate_skills": ["Python", "SQL", "Docker", "React"]
        }

        candidate_skills = ["Python", "SQL", "Docker", "React"]
        
        from app.services.adaptive_engine import initialize_state
        state = initialize_state(candidate_skills, "medium", "mixed", 10)
        
        # Simulate weakness on React (low avg score), and strong performance on others
        p_react = state.get_skill_performance("React")
        p_react.record_score(20)
        state.update_skill_performance(p_react)
        
        p_py = state.get_skill_performance("Python")
        p_py.record_score(100)
        state.update_skill_performance(p_py)
        
        p_sql = state.get_skill_performance("SQL")
        p_sql.record_score(100)
        state.update_skill_performance(p_sql)
        
        p_docker = state.get_skill_performance("Docker")
        p_docker.record_score(100)
        state.update_skill_performance(p_docker)
        
        # Now call the actual function
        selected_skill = select_skill_with_relevance(state, job_relevance_data)
        
        # The algorithm chooses least-attempted first. Since all have 1 attempt, it picks the lowest average score.
        # So React (score 20) is picked over Python (100).
        # Wait, if all have 1 attempt, it picks React because it's weakest. Job relevance is only a tie-breaker.
        if selected_skill == "React":
            results.append(("Adaptive Bias (Job-Specific Mode)", "PASS", f"Selected weak skill {selected_skill} despite low relevance (Weakness takes priority)"))
        else:
            results.append(("Adaptive Bias (Job-Specific Mode)", "FAIL", f"Expected React (weakest), got {selected_skill}"))
    except Exception as e:
        import traceback
        results.append(("Adaptive Bias (Job-Specific Mode)", "FAIL", traceback.format_exc()))

    return results

if __name__ == "__main__":
    res = run_adaptive_engine_tests()
    for r in res:
        print(f"[{r[1]}] {r[0]}: {r[2]}")
