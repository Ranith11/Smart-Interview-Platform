import sys
import json
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path("c:/Users/user/Desktop/Smart-Interview-main/backend").resolve()))

from app.services.jd_analysis_service import analyze_job_description
from app.services.question_service import get_embedding_model

class MockGroqMessage:
    def __init__(self, content):
        self.content = content

class MockGroqChoice:
    def __init__(self, content):
        self.message = MockGroqMessage(content)

class MockGroqResponse:
    def __init__(self, content):
        self.choices = [MockGroqChoice(content)]

class MockGroqChatCompletions:
    def create(self, **kwargs):
        # We will mock the LLM response to see how the system handles it, or use real if available
        pass

class MockGroqChat:
    def __init__(self):
        self.completions = MockGroqChatCompletions()

class MockGroqClient:
    def __init__(self):
        self.chat = MockGroqChat()

async def test_jd_analysis():
    print("Testing JD Analysis...")
    # Real test requires a real groq client or we just test the SBERT part
    model = get_embedding_model()
    
    # Test semantic similarity between JD requirement and candidate skill
    jd_reqs = [
        "Experience developing RESTful APIs using Python.",
        "Docker preferred",
        "FastAPI",
        "AWS"
    ]
    candidate_skills = [
        "Built backend APIs using FastAPI and Python.",
        "Docker",
        "Flask",
        "React"
    ]
    
    from sentence_transformers import util
    
    print("\n--- Semantic Similarity Tests ---")
    for req in jd_reqs:
        req_emb = model.encode(req)
        print(f"JD Requirement: '{req}'")
        for skill in candidate_skills:
            skill_emb = model.encode(skill)
            sim = util.cos_sim(req_emb, skill_emb).item()
            print(f"  vs '{skill}': {sim:.3f}")

if __name__ == "__main__":
    asyncio.run(test_jd_analysis())
