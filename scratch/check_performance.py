import requests

BASE_URL = "http://127.0.0.1:8000"

# Login with user 3 or user from test
s = requests.Session()
login_res = s.post(f"{BASE_URL}/api/auth/login", json={
    "email": "alex_e2e_1789544525@example.com",
    "password": "Password123!",
})

if login_res.status_code != 200:
    print(f"Login failed: {login_res.status_code}")
else:
    token = login_res.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})
    
    perf = s.get(f"{BASE_URL}/api/users/performance")
    print(f"Performance status: {perf.status_code}")
    print(f"Performance data: {perf.json()}")
