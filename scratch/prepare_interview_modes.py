import requests

BASE_URL = "http://127.0.0.1:8000/api"

# Login as uitester_1
r_login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "uitester_1@example.com",
    "password": "Password123!"
})
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. Normal mode interview
resume_id = requests.get(f"{BASE_URL}/resumes/current", headers=headers).json()["id"]

r_start_normal = requests.post(f"{BASE_URL}/interviews/start", json={
    "resume_id": resume_id,
    "mode": "normal",
    "difficulty": "medium",
    "question_type": "mixed",
    "selected_skills": ["Python", "FastAPI"]
}, headers=headers)
normal_id = r_start_normal.json()["session_id"]
print("Normal Session ID:", normal_id)

# 2. Syllabus mode interview
with open("scratch/cs450_distributed_systems_syllabus.pdf", "rb") as f:
    r_syl_up = requests.post(f"{BASE_URL}/interviews/upload-syllabus", files={"files": ("cs450_distributed_systems_syllabus.pdf", f, "application/pdf")}, headers=headers)
syl_data = r_syl_up.json()
syl_id = syl_data["syllabus_id"]
topics = syl_data["topics"]

r_start_syl = requests.post(f"{BASE_URL}/interviews/start", json={
    "mode": "syllabus",
    "syllabus_id": syl_id,
    "difficulty": "medium",
    "selected_topics": topics[:2]
}, headers=headers)
syllabus_session_id = r_start_syl.json()["session_id"]
print("Syllabus Session ID:", syllabus_session_id)
