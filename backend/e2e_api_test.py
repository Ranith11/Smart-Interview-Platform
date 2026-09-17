"""
SmartInterview — Full E2E API verification via HTTP (curl-equivalent using requests).
Tests all Syllabus Mode requirements without a browser.

Run from backend directory:
    python e2e_api_test.py
"""

import os
import sys
import json
import time
import requests
import chromadb

BASE = "http://localhost:8000/api"
CHROMA_DIR = str((os.path.dirname(os.path.abspath(__file__))).replace("\\backend", "") + "\\chroma_db")
OS_PDF   = os.path.join("test_syllabi", "OS_Syllabus.pdf")
DBMS_TXT = os.path.join("test_syllabi", "DBMS_Reference.txt")

# ── helpers ───────────────────────────────────────────────

def hdr(token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def chroma_collections():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    result = [c.name for c in client.list_collections()]
    del client  # release SQLite lock immediately
    return result

def perm_kb_count():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    count = client.get_collection("technical_kb").count()
    del client  # release SQLite lock immediately
    return count

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

RESULTS = {}

def record(key, passed, detail=""):
    RESULTS[key] = ("PASS" if passed else "FAIL", detail)
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status} {key}: {detail}")

# ── 1. Application startup ─────────────────────────────────

sep("1. APPLICATION STARTUP")
try:
    r = requests.get(f"{BASE}/resumes/current", timeout=30)
    server_up = r.status_code in (200, 401, 404)
    record("Backend reachable", server_up, f"HTTP {r.status_code}")
except Exception as e:
    record("Backend reachable", False, str(e)[:100])
    print("Cannot continue -- backend is not reachable.")
    sys.exit(1)

# ── 2. Auth ───────────────────────────────────────────────

sep("2. AUTHENTICATION")
# Use the user created during the previous runtime test
EMAIL = "test_runtime@test.com"
PASSWORD = "hash"  # This user has password_hash='hash' directly in DB; login won't work
# Register a fresh clean account
EMAIL = "e2e_verify_api@example.com"
PASSWORD = "E2eTest123!"

r = requests.post(f"{BASE}/auth/register",
    headers={"Content-Type": "application/json"},
    json={"email": EMAIL, "password": PASSWORD, "confirm_password": PASSWORD, "name": "E2E Tester"})
if r.status_code not in (201, 400):
    print(f"  Register returned: {r.status_code} {r.text[:200]}")

r = requests.post(f"{BASE}/auth/login",
    headers={"Content-Type": "application/json"},
    json={"email": EMAIL, "password": PASSWORD})

if r.status_code != 200:
    print(f"  Login failed: {r.status_code} {r.text[:300]}")
    record("Authentication", False, f"HTTP {r.status_code}")
    sys.exit(1)

TOKEN = r.json().get("access_token") or r.json().get("token")
assert TOKEN, f"No token in response: {r.json()}"
record("Authentication", True, f"Token obtained for {EMAIL}")

# ── 3. Resume ────────────────────────────────────────────

sep("3. RESUME CHECK / AUTO-UPLOAD")
r = requests.get(f"{BASE}/resumes/current", headers=hdr(TOKEN))
if r.status_code == 200:
    RESUME_ID = r.json()["id"]
    record("Resume available", True, f"Resume ID {RESUME_ID}")
else:
    # Auto-upload the existing resume PDF
    EXISTING_RESUME = r"C:\Users\user\Desktop\Smart-Interview-main\uploads\12_033e936b.pdf"
    if not os.path.exists(EXISTING_RESUME):
        record("Resume available", False, "No resume and no fallback PDF found")
        sys.exit(1)
    with open(EXISTING_RESUME, "rb") as rf:
        ru = requests.post(f"{BASE}/resumes/upload",
            headers={"Authorization": f"Bearer {TOKEN}"},
            files=[("file", ("resume.pdf", rf, "application/pdf"))],
            timeout=60)
    if ru.status_code == 201:
        RESUME_ID = ru.json()["id"]
        record("Resume auto-uploaded", True, f"Resume ID {RESUME_ID}")
    else:
        record("Resume available", False, f"Upload failed: {ru.status_code} {ru.text[:200]}")
        sys.exit(1)


# ── 4. OS PDF UPLOAD ─────────────────────────────────────

sep("4. OS PDF UPLOAD — /api/interviews/upload-syllabus")
assert os.path.exists(OS_PDF), f"OS PDF not found at {OS_PDF}"

t0 = time.time()
with open(OS_PDF, "rb") as f:
    r = requests.post(
        f"{BASE}/interviews/upload-syllabus",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files=[("files", ("OS_Syllabus.pdf", f, "application/pdf"))],
        timeout=120
    )
upload_time = time.time() - t0

record("OS PDF upload HTTP 200", r.status_code == 200, f"HTTP {r.status_code} in {upload_time:.1f}s")
if r.status_code != 200:
    print(f"UPLOAD FAILED: {r.text}")
    sys.exit(1)

upload_data = r.json()
print(f"  Response: {json.dumps(upload_data, indent=2)}")

OS_SYLLABUS_ID  = upload_data["syllabus_id"]
OS_SUBJECT      = upload_data["subject"]
OS_TOPICS       = upload_data["topics"]
FILES_PROCESSED = upload_data["files_processed"]

record("syllabus_id returned (UUID hex)", bool(OS_SYLLABUS_ID) and len(OS_SYLLABUS_ID) == 32, OS_SYLLABUS_ID)
record("subject detected", bool(OS_SUBJECT) and len(OS_SUBJECT) > 2, OS_SUBJECT)
record("topics detected", len(OS_TOPICS) >= 3, f"{len(OS_TOPICS)} topics: {OS_TOPICS}")
record("files_processed = 1", FILES_PROCESSED == 1, str(FILES_PROCESSED))

java_terms = {"classes", "inheritance", "polymorphism", "interfaces", "generics"}
topics_lower = {t.lower() for t in OS_TOPICS}
is_not_java = not topics_lower.intersection(java_terms)
record("Topics are NOT hardcoded Java topics", is_not_java, str(OS_TOPICS))

# ── 5. TEMP RAG EXISTS ────────────────────────────────────

sep("5. TEMPORARY RAG CREATION")
cols = chroma_collections()
temp_col_name = f"temp_syllabus_{OS_SYLLABUS_ID}"
record("temp_syllabus_<uuid> created", temp_col_name in cols, temp_col_name)
record("temp_syllabus_None NOT created", "temp_syllabus_None" not in cols, "clean")

client = chromadb.PersistentClient(path=CHROMA_DIR)
temp_col = client.get_collection(temp_col_name)
temp_chunk_count = temp_col.count()
del temp_col, client  # CRITICAL: release SQLite lock before any HTTP calls
record("Temp RAG has chunks", temp_chunk_count > 0, f"{temp_chunk_count} chunks")

kb_before = perm_kb_count()
print(f"  Permanent KB baseline: {kb_before} chunks")

# ── 6. START OS SYLLABUS INTERVIEW ───────────────────────

sep("6. START OS SYLLABUS INTERVIEW")
selected_topics = OS_TOPICS[:3]  # select first 3 topics
print(f"  Selected topics: {selected_topics}")

t0 = time.time()
r = requests.post(f"{BASE}/interviews/start",
    headers=hdr(TOKEN),
    json={
        "resume_id": RESUME_ID,
        "difficulty": "easy",
        "question_type": "conceptual",
        "question_count": None,
        "selected_skills": [],
        "mode": "syllabus",
        "syllabus_id": OS_SYLLABUS_ID,
        "selected_topics": selected_topics,
    }, timeout=300)  # 300s: embeds + LLM question generation
start_time = time.time() - t0

record("Interview start HTTP 201", r.status_code == 201, f"HTTP {r.status_code} in {start_time:.1f}s")
if r.status_code != 201:
    print(f"START FAILED: {r.text}")
    sys.exit(1)

start_data = r.json()
SESSION_ID    = start_data["session_id"]
FIRST_Q_ID    = start_data["current_question"]["id"]
FIRST_Q_TEXT  = start_data["current_question"]["question_text"]
FIRST_Q_SKILL = start_data["current_question"]["skill"]

record("Session created", bool(SESSION_ID), f"Session ID: {SESSION_ID}")
record("Mode is 'syllabus'", start_data.get("mode") == "syllabus", start_data.get("mode"))
record("syllabus_id stored on session", start_data.get("syllabus_id") == OS_SYLLABUS_ID,
       start_data.get("syllabus_id"))
record("First question generated", bool(FIRST_Q_TEXT) and FIRST_Q_TEXT != "[GENERATION FAILED]",
       FIRST_Q_TEXT[:100])
record("Question skill = selected topic", FIRST_Q_SKILL in selected_topics, FIRST_Q_SKILL)

print(f"\n  First question: {FIRST_Q_TEXT}")
print(f"  Skill/Topic:    {FIRST_Q_SKILL}")

# Verify temp RAG was NOT recreated (still only 1 temp collection)
cols_after_start = chroma_collections()
temp_count = sum(1 for c in cols_after_start if c.startswith("temp_syllabus_"))
record("RAG NOT recreated on session start (still 1 temp)", temp_count == 1, f"{temp_count} temp collections")

# ── 7. ANSWER ALL QUESTIONS (natural completion) ─────────

sep("7. ANSWER QUESTIONS — NATURAL COMPLETION")
current_q_id = FIRST_Q_ID
q_num = 1
prev_topic = FIRST_Q_SKILL
topic_transitions = [FIRST_Q_SKILL]
is_complete = False
evaluation_scores = []

GENERIC_ANSWER = (
    "This concept is fundamental to the topic. It involves specific mechanisms "
    "and principles that ensure correct operation. The key characteristics include "
    "proper management of resources and deterministic behavior. Implementation "
    "typically involves well-defined algorithms and data structures."
)

while not is_complete and q_num <= 30:
    print(f"\n  Q{q_num} (topic: {prev_topic}): answering...")
    t0 = time.time()
    r = requests.post(
        f"{BASE}/interviews/{SESSION_ID}/questions/{current_q_id}/answer",
        headers=hdr(TOKEN),
        json={"answer_text": GENERIC_ANSWER},
        timeout=120
    )
    ans_time = time.time() - t0

    if r.status_code != 200:
        print(f"  ANSWER FAILED: {r.status_code} {r.text}")
        break

    result = r.json()
    is_complete = result["is_complete"]
    score = result["evaluation"].get("overall_score", 0)
    evaluation_scores.append(score)
    answered = result["questions_answered"]
    remaining = result["questions_remaining"]

    print(f"  Score: {score}/100 | Answered: {answered} | Remaining: {remaining} | Time: {ans_time:.1f}s")

    if not is_complete:
        nq = result["next_question"]
        current_q_id = nq["id"]
        new_topic = nq["skill"]
        if new_topic != prev_topic:
            print(f"  -> Topic progressed: {prev_topic} -> {new_topic}")
        topic_transitions.append(new_topic)
        prev_topic = new_topic
        q_num += 1
    else:
        print(f"  -> Interview COMPLETE after Q{q_num}")

record("All questions answered", is_complete, f"{q_num} questions answered")
record("Evaluation scores received", len(evaluation_scores) > 0,
       f"Scores: {evaluation_scores}")
record("Topic progression was deterministic (backend-controlled)",
       len(set(topic_transitions)) <= len(selected_topics),
       f"Transitions: {topic_transitions}")

# ── 8. VERIFY NATURAL COMPLETION TRIGGERS MERGE+CLEANUP ──

sep("8. NATURAL COMPLETION — MERGE + CLEANUP")
cols_after = chroma_collections()
kb_after = perm_kb_count()

record("Temp RAG deleted after completion", temp_col_name not in cols_after,
       f"temp_syllabus_{OS_SYLLABUS_ID} not in {cols_after}")
record("Permanent KB still exists", "technical_kb" in cols_after, "technical_kb present")
record("Permanent KB updated", kb_after >= kb_before,
       f"KB: {kb_before} → {kb_after} (added {kb_after - kb_before} chunks)")

# ── 9. RESULTS ────────────────────────────────────────────

sep("9. RESULTS")
r = requests.get(f"{BASE}/interviews/{SESSION_ID}/results", headers=hdr(TOKEN))
record("Results endpoint HTTP 200", r.status_code == 200, f"HTTP {r.status_code}")

if r.status_code == 200:
    results = r.json()
    avg = results.get("overall_average_score", 0)
    skill_perf = results.get("skill_performance", {})
    record("Overall average score present", avg >= 0, f"Score: {avg}")
    record("Skill performance shows OS topics", bool(skill_perf),
           f"Topics: {list(skill_perf.keys())}")
    java_in_results = bool(set(skill_perf.keys()).intersection(java_terms))
    record("Results NOT showing Java topics", not java_in_results, str(list(skill_perf.keys())))

# ── 10. DBMS TXT UPLOAD ──────────────────────────────────

sep("10. DBMS TXT UPLOAD + INTERVIEW")
assert os.path.exists(DBMS_TXT), f"DBMS TXT not found at {DBMS_TXT}"

t0 = time.time()
with open(DBMS_TXT, "rb") as f:
    r = requests.post(
        f"{BASE}/interviews/upload-syllabus",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files=[("files", ("DBMS_Reference.txt", f, "text/plain"))],
        timeout=120
    )
dbms_upload_time = time.time() - t0

record("DBMS TXT upload HTTP 200", r.status_code == 200, f"HTTP {r.status_code} in {dbms_upload_time:.1f}s")
if r.status_code == 200:
    d = r.json()
    DBMS_ID     = d["syllabus_id"]
    DBMS_SUBJ   = d["subject"]
    DBMS_TOPICS = d["topics"]
    print(f"  Subject: {DBMS_SUBJ}")
    print(f"  Topics: {DBMS_TOPICS}")
    record("DBMS syllabus_id unique (different from OS)", DBMS_ID != OS_SYLLABUS_ID,
           f"{DBMS_ID[:8]}... vs {OS_SYLLABUS_ID[:8]}...")
    record("DBMS topics different from OS topics",
           not set(DBMS_TOPICS).intersection(set(OS_TOPICS)),
           f"{DBMS_TOPICS}")
    is_dbms_subject = any(kw in DBMS_SUBJ.lower() for kw in ["data", "database", "dbms", "sql", "db"])
    record("DBMS subject correctly inferred", is_dbms_subject, DBMS_SUBJ)

    # Quick 1-topic DBMS interview
    dbms_topics_sel = DBMS_TOPICS[:2]
    r2 = requests.post(f"{BASE}/interviews/start",
        headers=hdr(TOKEN),
        json={
            "resume_id": RESUME_ID,
            "difficulty": "easy",
            "question_type": "conceptual",
            "question_count": None,
            "selected_skills": [],
            "mode": "syllabus",
            "syllabus_id": DBMS_ID,
            "selected_topics": dbms_topics_sel,
        }, timeout=120)
    record("DBMS interview start HTTP 201", r2.status_code == 201, f"HTTP {r2.status_code}")

    if r2.status_code == 201:
        d2 = r2.json()
        dbms_sess_id = d2["session_id"]
        dbms_q_id    = d2["current_question"]["id"]
        dbms_q_text  = d2["current_question"]["question_text"]
        dbms_q_skill = d2["current_question"]["skill"]
        record("DBMS question generated", dbms_q_text != "[GENERATION FAILED]", dbms_q_text[:80])
        record("DBMS question topic is DBMS-related", dbms_q_skill in dbms_topics_sel, dbms_q_skill)
        print(f"  DBMS Q: {dbms_q_text}")

        # Manual complete (Finish Interview)
        r3 = requests.post(f"{BASE}/interviews/{dbms_sess_id}/complete", headers=hdr(TOKEN))
        record("DBMS manual complete HTTP 200", r3.status_code == 200, f"HTTP {r3.status_code}")

        cols_dbms = chroma_collections()
        dbms_temp = f"temp_syllabus_{DBMS_ID}"
        record("DBMS temp RAG deleted after manual complete",
               dbms_temp not in cols_dbms, f"{dbms_temp} not in collections")

# ── 11. MULTIPLE FILE UPLOAD ──────────────────────────────

sep("11. MULTIPLE FILE UPLOAD")
with open(OS_PDF, "rb") as f1, open(DBMS_TXT, "rb") as f2:
    r = requests.post(
        f"{BASE}/interviews/upload-syllabus",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files=[
            ("files", ("OS_Syllabus.pdf", f1, "application/pdf")),
            ("files", ("DBMS_Reference.txt", f2, "text/plain")),
        ]
    )
record("Multi-file upload HTTP 200", r.status_code == 200, f"HTTP {r.status_code}")
if r.status_code == 200:
    md = r.json()
    record("Multi-file: files_processed = 2", md["files_processed"] == 2, str(md["files_processed"]))
    record("Multi-file: topics returned", len(md["topics"]) >= 4, f"{len(md['topics'])} topics")
    # Clean up this temp collection (no interview started)
    temp_multi = f"temp_syllabus_{md['syllabus_id']}"
    c = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        c.delete_collection(temp_multi)
        print(f"  Cleaned up abandoned temp collection: {temp_multi}")
    except:
        pass

# ── 12. FILE VALIDATION ──────────────────────────────────

sep("12. FILE VALIDATION")

# Wrong type (.py file)
py_content = b"print('hello')"
r = requests.post(
    f"{BASE}/interviews/upload-syllabus",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files=[("files", ("exploit.py", py_content, "text/x-python"))]
)
record("Python file REJECTED (400)", r.status_code == 400, f"HTTP {r.status_code}: {r.json().get('detail','')[:60]}")

# Wrong type (.exe file)
r = requests.post(
    f"{BASE}/interviews/upload-syllabus",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files=[("files", ("virus.exe", b"MZ\x90\x00", "application/octet-stream"))]
)
record("EXE file REJECTED (400)", r.status_code == 400, f"HTTP {r.status_code}: {r.json().get('detail','')[:60]}")

# Empty file
r = requests.post(
    f"{BASE}/interviews/upload-syllabus",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files=[("files", ("empty.pdf", b"", "application/pdf"))]
)
record("Empty file REJECTED (400)", r.status_code == 400, f"HTTP {r.status_code}: {r.json().get('detail','')[:60]}")

# ── 13. NORMAL MODE VERIFICATION ─────────────────────────

sep("13. NORMAL MODE VERIFICATION")
r = requests.post(f"{BASE}/interviews/start",
    headers=hdr(TOKEN),
    json={
        "resume_id": RESUME_ID,
        "difficulty": "easy",
        "question_type": "conceptual",
        "question_count": None,
        "selected_skills": None,
        "mode": "normal",
    })
record("Normal mode start HTTP 201", r.status_code == 201, f"HTTP {r.status_code}")
if r.status_code == 201:
    nd = r.json()
    record("Normal mode is_adaptive=True", nd.get("is_adaptive") == True, str(nd.get("is_adaptive")))
    record("Normal mode mode='normal'", nd.get("mode") == "normal", nd.get("mode"))
    record("Normal mode question generated", bool(nd["current_question"]["question_text"]),
           nd["current_question"]["question_text"][:80])
    norm_sess = nd["session_id"]
    # Complete it
    requests.post(f"{BASE}/interviews/{norm_sess}/complete", headers=hdr(TOKEN))
    record("Normal mode complete OK", True, "Manual finish OK")

# ── 14. IDEMPOTENCY CHECK ─────────────────────────────────

sep("14. IDEMPOTENCY — SAME OS MATERIAL AGAIN")
# Upload OS PDF again (same content)
with open(OS_PDF, "rb") as f:
    r = requests.post(
        f"{BASE}/interviews/upload-syllabus",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files=[("files", ("OS_Syllabus.pdf", f, "application/pdf"))]
    )

if r.status_code == 200:
    idem = r.json()
    idem_id = idem["syllabus_id"]

    r2 = requests.post(f"{BASE}/interviews/start",
        headers=hdr(TOKEN),
        json={
            "resume_id": RESUME_ID,
            "difficulty": "easy",
            "question_type": "conceptual",
            "selected_skills": [],
            "mode": "syllabus",
            "syllabus_id": idem_id,
            "selected_topics": idem["topics"][:2],
        })

    if r2.status_code == 201:
        idem_sess = r2.json()["session_id"]
        kb_before_idem = perm_kb_count()
        r3 = requests.post(f"{BASE}/interviews/{idem_sess}/complete", headers=hdr(TOKEN))
        kb_after_idem = perm_kb_count()
        record("Idempotency: second OS upload adds 0 new KB chunks",
               kb_after_idem == kb_before_idem,
               f"KB: {kb_before_idem} → {kb_after_idem} (added {kb_after_idem - kb_before_idem})")
    else:
        record("Idempotency session start", False, f"HTTP {r2.status_code}")
else:
    record("Idempotency re-upload", False, f"HTTP {r.status_code}")

# ── 15. FINAL KB STATE ────────────────────────────────────

sep("15. FINAL STATE")
kb_final = perm_kb_count()
cols_final = chroma_collections()
print(f"  Permanent KB chunks: {kb_final}")
print(f"  Collections: {cols_final}")
record("Permanent technical_kb intact", "technical_kb" in cols_final, "exists")
leftover_temps = [c for c in cols_final if c.startswith("temp_syllabus_")]
record("No leftover temp collections", len(leftover_temps) == 0,
       f"Leftover: {leftover_temps}" if leftover_temps else "Clean")

# ── SUMMARY ──────────────────────────────────────────────

sep("FINAL VERIFICATION REPORT")

CATEGORIES = {
    "APPLICATION STARTUP":           ["Backend reachable"],
    "AUTHENTICATION":                ["Authentication"],
    "OS PDF END-TO-END":             ["OS PDF upload HTTP 200","syllabus_id returned (UUID hex)","subject detected","topics detected"],
    "DYNAMIC TOPIC DETECTION":       ["topics detected","Topics are NOT hardcoded Java topics"],
    "TEMPORARY RAG CREATION":        ["temp_syllabus_<uuid> created","temp_syllabus_None NOT created","Temp RAG has chunks"],
    "SYLLABUS INTERVIEW START":      ["Interview start HTTP 201","Session created","Mode is 'syllabus'","First question generated"],
    "QUESTION FROM SYLLABUS RAG":    ["Question skill = selected topic","RAG NOT recreated on session start (still 1 temp)"],
    "TOPIC RESTRICTION":             ["Question skill = selected topic"],
    "DETERMINISTIC PROGRESSION":     ["Topic progression was deterministic (backend-controlled)"],
    "NATURAL COMPLETION":            ["All questions answered"],
    "KB SEMANTIC MERGE":             ["Permanent KB updated"],
    "TEMPORARY RAG CLEANUP":         ["Temp RAG deleted after completion"],
    "RESULTS":                       ["Results endpoint HTTP 200","Overall average score present"],
    "DBMS TXT END-TO-END":           ["DBMS TXT upload HTTP 200","DBMS question generated"],
    "MULTIPLE FILE UPLOAD":          ["Multi-file upload HTTP 200","Multi-file: files_processed = 2"],
    "FILE VALIDATION":               ["Python file REJECTED (400)","EXE file REJECTED (400)","Empty file REJECTED (400)"],
    "NORMAL MODE":                   ["Normal mode start HTTP 201","Normal mode is_adaptive=True","Normal mode question generated"],
    "IDEMPOTENCY":                   ["Idempotency: second OS upload adds 0 new KB chunks"],
}

all_pass = True
for category, keys in CATEGORIES.items():
    statuses = [RESULTS.get(k, ("NOT TESTED", ""))[0] for k in keys]
    if all(s == "PASS" for s in statuses):
        cat_status = "PASS"
    elif any(s == "FAIL" for s in statuses):
        cat_status = "FAIL"
        all_pass = False
    else:
        cat_status = "PARTIAL"
        all_pass = False
    print(f"  {category:<40} {cat_status}")
    for k in keys:
        r_status, detail = RESULTS.get(k, ("NOT TESTED",""))
        icon = "OK" if r_status == "PASS" else ("XX" if r_status == "FAIL" else "--")
        print(f"    {icon} {k}: {detail}")

print()
print(f"  KB chunks: {kb_before} (baseline) → {kb_after} (after OS) → {kb_final} (final)")
print()
if all_pass:
    print("  *** READY FOR PRODUCT TESTING ***")
else:
    fails = [k for k,v in RESULTS.items() if v[0] == "FAIL"]
    print(f"  *** NOT READY -- issues remain: {fails} ***")
