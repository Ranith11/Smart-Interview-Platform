import requests

BASE_URL = "http://127.0.0.1:8000/api"

# Register or login candidate
email = "candidate_voice@smartinterview.com"
password = "Password123!"

r_auth = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
if r_auth.status_code != 200:
    r_reg = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Alex Chen",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    token = r_reg.json()["access_token"]
else:
    token = r_auth.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Check or upload resume
r_cur = requests.get(f"{BASE_URL}/resumes/current", headers=headers)
if r_cur.status_code != 200 or not r_cur.json().get("id"):
    with open("scratch/alex_chen_resume.pdf", "rb") as f:
        r_up = requests.post(f"{BASE_URL}/resumes/upload", files={"file": ("alex_chen_resume.pdf", f, "application/pdf")}, headers=headers)
    resume_id = r_up.json()["id"]
else:
    resume_id = r_cur.json()["id"]

# Upload JD if needed
with open("scratch/senior_backend_jd.pdf", "rb") as f:
    requests.post(f"{BASE_URL}/job-descriptions/upload", files={"file": ("senior_backend_jd.pdf", f, "application/pdf")}, headers=headers)

# Create adaptive interview session
r_session = requests.post(f"{BASE_URL}/interviews/start", json={
    "resume_id": resume_id,
    "difficulty": "medium",
    "question_type": "conceptual",
    "question_count": 5,
    "selected_skills": ["Python", "FastAPI", "PostgreSQL"]
}, headers=headers)

data = r_session.json()
session_id = data["session_id"]
question = data["current_question"]

print(f"TOKEN={token}")
print(f"SESSION_ID={session_id}")
print(f"QUESTION_ID={question['id']}")
print(f"QUESTION_TEXT={question['question_text']}")
