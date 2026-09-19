import requests

BASE_URL = "http://127.0.0.1:8000/api"

# Login as uitester_1
r_login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "uitester_1@example.com",
    "password": "Password123!"
})
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload resume
with open("scratch/alex_chen_resume.pdf", "rb") as f:
    r_res = requests.post(f"{BASE_URL}/resumes/upload", files={"file": f}, headers=headers)
print("Resume Upload:", r_res.status_code, r_res.json().get("name"))

# Upload JD
with open("scratch/senior_backend_jd.pdf", "rb") as f:
    r_jd = requests.post(f"{BASE_URL}/job-descriptions/upload", files={"file": f}, headers=headers)
print("JD Upload:", r_jd.status_code, len(r_jd.json().get("skills", [])))

# Verify mapping
r_map = requests.get(f"{BASE_URL}/job-descriptions/mapping", headers=headers)
print("Mapping:", r_map.status_code, "Matched:", len(r_map.json().get("matched_skills", [])), "Gaps:", len(r_map.json().get("gap_skills", [])))
