"""
SmartInterview — Job Description Analysis Service

Analyzes a Job Description to extract skill-relevance data that guides
the adaptive engine's skill selection in Job-Specific interviews.

Key principles:
    - Candidate skills and JD skills are kept SEPARATE
    - JD analysis does NOT claim the candidate knows skills from the JD
    - Job relevance influences WHICH skill is selected, not HOW it's tested
    - The output is validated and structured, never raw LLM text
    - Existing skill normalization (SKILL_DOMAIN_MAP) is reused
"""

import json
from typing import Optional
from sentence_transformers import util

# We will import the existing embedding model from question_service
from app.services.question_service import get_embedding_model

VALID_RELEVANCE_LEVELS = {"high", "medium", "low"}

def analyze_job_description(
    jd_text: str,
    candidate_skills: list[str],
    groq_client,
    groq_model: str,
    job_title: str | None = None,
) -> dict:
    if not jd_text or len(jd_text.strip()) < 10:
        raise ValueError("Job description is too short. Please provide a meaningful job description.")
    if not candidate_skills:
        raise ValueError("No candidate skills available. Please upload a resume with technical skills first.")

    candidate_skills_normalized = [s.strip() for s in candidate_skills if s and s.strip()]

    # 1. LLM Extraction (Structure, Context, Required vs Preferred)
    llm_result = _llm_extract_jd_requirements(
        jd_text=jd_text.strip(),
        groq_client=groq_client,
        groq_model=groq_model,
    )

    # 2. Semantic and Exact Matching
    job_relevance_data = _match_and_build_relevance(
        llm_result=llm_result,
        candidate_skills=candidate_skills_normalized,
        job_title=job_title,
    )

    return job_relevance_data


def get_skills_for_interview(
    job_relevance_data: dict,
    candidate_skills: list[str],
) -> list[str]:
    skill_relevance = job_relevance_data.get("skill_relevance", {})
    if not skill_relevance:
        return candidate_skills

    eligible_skills = []
    
    # 1. Matching Resume Skills (exclude "low" relevance completely)
    for skill in candidate_skills:
        relevance = skill_relevance.get(skill, "low")
        if relevance in ("high", "medium"):
            eligible_skills.append(skill)
            
    # 2. JD-Only Skills (requirements in JD but not in resume)
    jd_only = job_relevance_data.get("jd_only_skills", [])
    eligible_skills.extend(jd_only)
    
    # Fallback only if absolutely empty
    if not eligible_skills:
        return candidate_skills

    return eligible_skills


def _llm_extract_jd_requirements(
    jd_text: str,
    groq_client,
    groq_model: str,
) -> dict:
    if groq_client is None or not groq_model:
        return _fallback_extraction()

    system_prompt = """You are an expert technical recruiter and JD parser.

Your task:
1. Analyze the job description structure and identify technical skills, tools, languages, and frameworks.
2. For each identified skill, extract it and determine if it is "required" or "preferred" based on the context.
3. Provide the context quote from the JD where it was found to help with semantic matching later.

Rules:
- Distinguish strictly between "required" (must-have) and "preferred" (nice-to-have).
- If a technology is merely mentioned (e.g. "our stack uses AWS"), classify it as "preferred" unless explicitly required.
- Do NOT invent skills.

Respond ONLY with valid JSON in this exact format:
{
  "requirements": [
    {
      "skill": "Python",
      "type": "required",
      "context": "Experience developing RESTful APIs using Python."
    },
    {
      "skill": "Docker",
      "type": "preferred",
      "context": "Docker preferred"
    }
  ],
  "inferred_title": "Backend Developer"
}"""

    user_prompt = f"""Job Description:
---
{jd_text[:6000]}
---

Extract the requirements as JSON."""

    try:
        response = groq_client.chat.completions.create(
            model=groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )

        text = response.choices[0].message.content
        if not text or not text.strip():
            return _fallback_extraction()

        return _parse_llm_response(text.strip())

    except Exception as e:
        print(f"[JDAnalysisService] LLM extraction error: {e}")
        return _fallback_extraction()


def _parse_llm_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        json_lines = []
        inside = False
        for line in lines:
            if line.strip().startswith("```") and not inside:
                inside = True
                continue
            elif line.strip() == "```" and inside:
                break
            elif inside:
                json_lines.append(line)
        cleaned = "\n".join(json_lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return _fallback_extraction()
        else:
            return _fallback_extraction()

    reqs = data.get("requirements", [])
    valid_reqs = []
    if isinstance(reqs, list):
        for r in reqs:
            if isinstance(r, dict) and "skill" in r:
                valid_reqs.append({
                    "skill": str(r.get("skill", "")).strip(),
                    "type": str(r.get("type", "required")).strip().lower(),
                    "context": str(r.get("context", "")).strip()
                })

    return {
        "requirements": valid_reqs,
        "inferred_title": str(data.get("inferred_title", "")).strip()[:200],
    }


def _fallback_extraction() -> dict:
    return {
        "requirements": [],
        "inferred_title": "",
    }


def _match_and_build_relevance(
    llm_result: dict,
    candidate_skills: list[str],
    job_title: str | None = None,
) -> dict:
    requirements = llm_result.get("requirements", [])
    inferred_title = llm_result.get("inferred_title", "")
    
    # Extract just the skill names from the JD for the final output
    job_skills = [r["skill"] for r in requirements if r["skill"]]
    
    skill_relevance = {}
    
    if not requirements:
        # Fallback if extraction failed
        skill_relevance = {s: "medium" for s in candidate_skills}
    else:
        # Load SBERT model
        model = get_embedding_model()
        
        # Precompute embeddings for requirements
        req_embeddings = []
        for req in requirements:
            # We embed both the explicit skill name and its surrounding context
            text_to_embed = f"{req['skill']} {req['context']}"
            req_embeddings.append({
                "req": req,
                "emb": model.encode(text_to_embed)
            })

        for c_skill in candidate_skills:
            c_emb = model.encode(c_skill)
            
            best_relevance = "low"
            best_score = 0.0
            
            for r_data in req_embeddings:
                req = r_data["req"]
                req_skill = req["skill"].lower()
                c_skill_lower = c_skill.lower()
                
                # 1. Exact Match Check (including aliases/substrings like 'react' in 'react.js')
                is_exact = False
                if req_skill == c_skill_lower or req_skill in c_skill_lower or c_skill_lower in req_skill:
                    is_exact = True
                    
                # 2. Semantic Match Check
                sim = util.cos_sim(c_emb, r_data["emb"]).item()
                
                # SBERT threshold logic based on testing:
                # > 0.45 is a strong semantic match
                is_semantic = sim > 0.45
                
                if is_exact or is_semantic:
                    # Determine relevance based on JD requirement type
                    if req["type"] == "required":
                        potential_relevance = "high"
                    else:
                        potential_relevance = "medium"
                        
                    # Keep the highest relevance found for this candidate skill
                    if best_relevance == "low" or (best_relevance == "medium" and potential_relevance == "high"):
                        best_relevance = potential_relevance
                        
                if sim > best_score:
                    best_score = sim
            
            skill_relevance[c_skill] = best_relevance

    # Determine JD-only skills
    candidate_set = {s.lower() for s in candidate_skills}
    jd_only = [s for s in job_skills if s.lower() not in candidate_set]

    # Determine Candidate-only skills
    jd_set = {s.lower() for s in job_skills}
    candidate_only = [s for s in candidate_skills if s.lower() not in jd_set]

    display_title = job_title.strip() if job_title and job_title.strip() else inferred_title

    return {
        "job_title": display_title[:500] if display_title else "",
        "job_skills": job_skills,
        "candidate_skills": candidate_skills,
        "skill_relevance": skill_relevance,
        "jd_only_skills": jd_only,
        "candidate_only_skills": candidate_only,
    }

