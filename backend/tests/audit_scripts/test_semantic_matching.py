import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.services.jd_analysis_service import _match_and_build_relevance

def run_semantic_matching_tests():
    print("--- Running SBERT Semantic Matching Tests ---")
    results = []
    
    # We will mock the LLM output
    llm_mock_result = {
        "requirements": [
            {"skill": "Python", "type": "required", "context": "Experience developing RESTful APIs using Python."},
            {"skill": "Docker", "type": "preferred", "context": "Docker preferred for deployment."},
            {"skill": "FastAPI", "type": "required", "context": "Must have experience with FastAPI."},
            {"skill": "AWS", "type": "preferred", "context": "Cloud deployment experience, preferably AWS."}
        ],
        "inferred_title": "Backend Developer"
    }

    # 1. Exact Match Test
    candidate_skills_exact = ["Docker"]
    res_exact = _match_and_build_relevance(llm_mock_result, candidate_skills_exact)
    if res_exact["skill_relevance"].get("Docker") == "medium":
        results.append(("Exact Match (Preferred -> Medium)", "PASS", ""))
    else:
        results.append(("Exact Match (Preferred -> Medium)", "FAIL", f"Got {res_exact['skill_relevance'].get('Docker')}"))

    # 2. Semantic Match Test
    candidate_skills_semantic = ["Built backend APIs using FastAPI and Python."]
    # Wait, the candidate skills are usually just short strings like "Python", "React", "FastAPI" 
    # but the semantic matching should still handle "Built backend APIs using FastAPI and Python." 
    # if the resume parser extracted it that way (sometimes it does for projects).
    res_semantic = _match_and_build_relevance(llm_mock_result, candidate_skills_semantic)
    # The requirement is "Python" (required). It should match this with high relevance.
    if res_semantic["skill_relevance"].get(candidate_skills_semantic[0]) == "high":
         results.append(("Semantic Match (Required -> High)", "PASS", ""))
    else:
         results.append(("Semantic Match (Required -> High)", "FAIL", f"Got {res_semantic['skill_relevance'].get(candidate_skills_semantic[0])}"))
         
    # 3. Missing Test
    candidate_skills_missing = ["React"]
    res_missing = _match_and_build_relevance(llm_mock_result, candidate_skills_missing)
    if res_missing["skill_relevance"].get("React") == "low":
         results.append(("Missing Skill (React vs Backend JD -> Low)", "PASS", ""))
    else:
         results.append(("Missing Skill (React vs Backend JD -> Low)", "FAIL", f"Got {res_missing['skill_relevance'].get('React')}"))

    # 4. Related but not same (Flask vs FastAPI)
    candidate_skills_related = ["Flask"]
    res_related = _match_and_build_relevance(llm_mock_result, candidate_skills_related)
    # FastAPI and Flask have a similarity of ~0.23 which is below 0.45. It should be "low".
    if res_related["skill_relevance"].get("Flask") == "low":
         results.append(("Related Skill Threshold (Flask vs FastAPI -> Low)", "PASS", ""))
    else:
         results.append(("Related Skill Threshold (Flask vs FastAPI -> Low)", "FAIL", f"Got {res_related['skill_relevance'].get('Flask')}"))

    return results

if __name__ == "__main__":
    res = run_semantic_matching_tests()
    for r in res:
        print(f"[{r[1]}] {r[0]}: {r[2]}")
