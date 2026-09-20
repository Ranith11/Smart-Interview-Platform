import sys
import os
import asyncio
import io

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.routers.interviews import extract_jd_file
from app.services.jd_analysis_service import analyze_job_description
from app.services.question_service import get_groq_client, get_groq_model_name
from app.services.adaptive_engine import initialize_state, select_skill_with_relevance
from fastapi import UploadFile
from starlette.datastructures import Headers

async def run_e2e():
    print("========================================")
    print("E2E JOB-SPECIFIC VERIFICATION (REAL PDF)")
    print("========================================")
    
    pdf_path = r"c:\Users\user\Desktop\Smart-Interview-main\Software_Engineer_Job_Description.pdf"
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    # 1. Extraction
    print("\n--- 1. JD Extraction ---")
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    upload_file = UploadFile(
        filename="Software_Engineer_Job_Description.pdf",
        file=io.BytesIO(content),
        headers=Headers({"content-type": "application/pdf"})
    )
    
    res = await extract_jd_file(upload_file, current_user=None)
    jd_text = res["extracted_text"]
    print("Extracted Text Preview:")
    print(jd_text[:300] + "...\n")

    # 2. Structure & Relevance (SBERT + LLM)
    print("\n--- 2. Structure & Relevance Analysis ---")
    candidate_skills = ["Python", "FastAPI", "React", "Docker", "AWS", "SQL", "Git", "REST APIs", "Node.js", "Java", "Flask"]
    print(f"Candidate Skills: {candidate_skills}\n")
    
    relevance_data = analyze_job_description(
        jd_text=jd_text,
        candidate_skills=candidate_skills,
        groq_client=get_groq_client(),
        groq_model=get_groq_model_name(),
        job_title="Software Engineer"
    )
    
    print("SBERT Similarity Matches (Job Skills):")
    for skill, rel in relevance_data["skill_relevance"].items():
        print(f" - {skill}: {rel}")
        
    print("\nJD Only Requirements (Missing in Resume):")
    print(relevance_data.get("jd_only_skills", []))
    
    print("\nInferred Job Title:", relevance_data.get("inferred_title"))
    
    # 3. Adaptive Bias Engine
    print("\n--- 3. Adaptive Selection ---")
    state = initialize_state(candidate_skills, "medium", "mixed", 10)
    
    # Scenario A: All skills equally attempt/score -> Should pick weakest (all same) -> Should pick highest relevance
    print("Scenario A: Equal Performance")
    selected_A = select_skill_with_relevance(state, relevance_data)
    print(f"Selected Skill (Equal Perf): {selected_A} (Expected a High Relevance skill)")
    
    # Scenario B: High relevance skill is strong (100), Low relevance skill is weak (20)
    print("\nScenario B: Strong High-Rel, Weak Low-Rel")
    for s in candidate_skills:
        perf = state.get_skill_performance(s)
        if relevance_data["skill_relevance"].get(s) == "high":
            perf.record_score(100)
        else:
            perf.record_score(20)
        state.update_skill_performance(perf)
        
    selected_B = select_skill_with_relevance(state, relevance_data)
    print(f"Selected Skill (Weak Low-Rel): {selected_B} (Expected a Low/Medium relevance skill because it is weak)")
    
    # Scenario C: Multiple weak skills -> Should pick the one with highest JD relevance
    print("\nScenario C: Tie-break on Weak Skills")
    # Reset state
    state2 = initialize_state(candidate_skills, "medium", "mixed", 10)
    for s in candidate_skills:
        perf = state2.get_skill_performance(s)
        perf.record_score(30) # All are weak
        state2.update_skill_performance(perf)
        
    selected_C = select_skill_with_relevance(state2, relevance_data)
    print(f"Selected Skill (Multiple Weak): {selected_C} (Expected a High Relevance skill among the weak ones)")

if __name__ == "__main__":
    asyncio.run(run_e2e())
