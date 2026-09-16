import os
import sys
import json
import requests
import docx

BASE = "http://localhost:8000/api"

# Create a docx file
docx_path = "test_syllabi/Network_Security.docx"
os.makedirs("test_syllabi", exist_ok=True)
doc = docx.Document()
doc.add_paragraph("Network security is critical. It involves encryption, firewalls, and intrusion detection systems.")
doc.save(docx_path)

pdf_path = "test_syllabi/OS_Syllabus.pdf"
txt_path = "test_syllabi/DBMS_Reference.txt"

if not os.path.exists(pdf_path) or not os.path.exists(txt_path):
    print("Cannot find existing PDF or TXT files. Exiting.")
    sys.exit(1)

# Register user to get token
EMAIL = "optimization_test@example.com"
PASSWORD = "Password123!"

r = requests.post(f"{BASE}/auth/register", json={"email": EMAIL, "password": PASSWORD, "confirm_password": PASSWORD, "name": "Test User"})
r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
TOKEN = r.json().get("access_token")

# Helper function
def test_upload(name, files, expect_code=200):
    print(f"\n--- Testing {name} ---")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    files_data = []
    file_handles = []
    
    for f in files:
        fh = open(f, "rb")
        file_handles.append(fh)
        ext = os.path.splitext(f)[1].lower()
        if ext == '.pdf':
            mime = 'application/pdf'
        elif ext == '.txt':
            mime = 'text/plain'
        else:
            mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        files_data.append(("files", (os.path.basename(f), fh, mime)))
        
    r = requests.post(f"{BASE}/interviews/upload-syllabus", headers=headers, files=files_data)
    
    for fh in file_handles:
        fh.close()
        
    if r.status_code == expect_code:
        print(f"{name} Passed! HTTP {r.status_code}")
        try:
            print("Response:", r.json())
        except:
            pass
    else:
        print(f"{name} Failed! HTTP {r.status_code}")
        print(r.text)

test_upload("Single PDF", [pdf_path])
test_upload("Single TXT", [txt_path])
test_upload("Single DOCX", [docx_path])
test_upload("Mixed Files", [pdf_path, txt_path, docx_path])
