import os
from groq import Groq

def test_truncation():
    groq_client = Groq()
    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a technical interviewer conducting a realistic mock interview.\n\nGenerate exactly ONE clear, concise interview question about the specified skill.\n\nRules:\n- The question MUST be about the specified skill. Do not switch to an unrelated topic.\n- Ask about ONE primary technical concept.\n- The question should sound natural when spoken by an interviewer.\n- Keep the question concise and appropriate for the requested difficulty.\n- If project context is provided, you may personalize the question using it, but the skill remains the focus.\n- Do not invent candidate experience or technologies not mentioned.\n- Do not ask multi-part questions.\n- Do not provide the answer.\n- Generate ONLY the question text.\n/no_think"},
            {"role": "user", "content": "Difficulty: Hard. Ask a deeper but focused question. Keep it to 20-45 words.\n\nQuestion type: practical\nAsk a practical question about implementing something or solving a specific problem.\n\nSelected Skill: Python\n\nRetrieved Technical Context:\n[dsa/graph]\n..."},
        ],
        temperature=0.7,
        max_tokens=50, 
    )
    
    choice = response.choices[0]
    print(f"Content: {choice.message.content}")
    print(f"Finish Reason: {choice.finish_reason}")
    print(f"Type of Finish Reason: {type(choice.finish_reason)}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_truncation()
