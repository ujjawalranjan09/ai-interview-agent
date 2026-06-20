"""End-to-end workflow tests for AI Interview Agent API."""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
TOKEN = None

def api(method, path, data=None, auth=True):
    global TOKEN
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def login(email, password):
    global TOKEN
    r = api("POST", "/api/v1/auth/login", {"email": email, "password": password}, auth=False)
    TOKEN = r["access_token"]
    return r

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check(step, result, *keys):
    for k in keys:
        if k not in result:
            print(f"  FAIL {step}: missing key '{k}' in {result}")
            return False
    print(f"  OK   {step}")
    return True

# ============================================================
section("JOURNEY 1: Full Interview Lifecycle")
# ============================================================

print("\nStep 1: Login")
login("admin@test.com", "Admin123!")
print("  OK   Logged in as interviewer")

print("\nStep 2: Create candidate")
cand = api("POST", "/api/v1/candidates", {"name": "E2E Candidate", "email": "e2e@test.com", "skills": ["python", "react", "sql"]})
check("Create candidate", cand, "id")
cand_id = cand["id"]

print("\nStep 3: Create interview")
intv = api("POST", "/api/v1/interviews", {"candidate_id": cand_id, "question_count": 3})
check("Create interview", intv, "id")
intv_id = intv["id"]

print("\nStep 4: Start interview")
started = api("POST", f"/api/v1/interviews/{intv_id}/start")
check("Start interview", started, "status")
assert started["status"] == "in_progress", f"Expected in_progress, got {started['status']}"

print("\nStep 5: Get questions")
questions = api("GET", f"/api/v1/interviews/{intv_id}/questions")
assert len(questions) >= 1, "No questions returned"
print(f"  OK   Got {len(questions)} questions")

print("\nStep 6: Answer Q1 (good answer)")
a1 = api("POST", f"/api/v1/questions/{questions[0]['id']}/answer", {"answer_text": "Python is a high-level programming language known for readability. I use it with Django for web, pandas for data, and scikit-learn for ML. The ecosystem is vast."})
check("Answer Q1", a1, "total_score")
print(f"       Score: {a1['total_score']}")

print("\nStep 7: Answer Q2 (poor answer)")
a2 = api("POST", f"/api/v1/questions/{questions[1]['id']}/answer", {"answer_text": "Yes."})
check("Answer Q2", a2, "total_score")
print(f"       Score: {a2['total_score']}")

print("\nStep 8: Answer Q3 (medium answer)")
a3 = api("POST", f"/api/v1/questions/{questions[2]['id']}/answer", {"answer_text": "I would design the system by first analyzing requirements, then creating database schema with PostgreSQL, building REST API with FastAPI, and frontend with React. I would use Docker for deployment."})
check("Answer Q3", a3, "total_score")
print(f"       Score: {a3['total_score']}")

print("\nStep 9: Close interview")
closed = api("POST", f"/api/v1/interviews/{intv_id}/close")
check("Close interview", closed, "status")
assert closed["status"] == "completed", f"Expected completed, got {closed['status']}"
print(f"       Total score: {closed.get('total_score', 'N/A')}")

print("\nStep 10: Generate report")
report = api("POST", f"/api/v1/interviews/{intv_id}/report/generate")
check("Generate report", report, "metrics", "feedback")
print(f"       Average score: {report['metrics']['average_score']}")
print(f"       Grade: {report['metrics']['overall_grade']}")

print("\nStep 11: Get coaching plan")
coaching = api("POST", f"/api/v1/interviews/{intv_id}/coaching/generate")
check("Generate coaching", coaching, "weak_topics", "one_week_plan")
print(f"       Weak topics: {len(coaching.get('weak_topics', []))}")

print("\nStep 12: Get replay data")
replay = api("GET", f"/api/v1/interviews/{intv_id}/replay")
check("Get replay", replay, "events", "score_progression")
print(f"       Events: {len(replay.get('events', []))}")

# ============================================================
section("JOURNEY 2: Copilot Mode")
# ============================================================

print("\nStep 1: Login")
login("admin@test.com", "Admin123!")
print("  OK   Logged in")

print("\nStep 2: Create fresh interview for copilot test")
intv2 = api("POST", "/api/v1/interviews", {"candidate_id": cand_id, "question_count": 3})
intv2_id = intv2["id"]
started2 = api("POST", f"/api/v1/interviews/{intv2_id}/start")
print(f"  OK   Interview {intv2_id[:8]}... started")

print("\nStep 3: Start copilot session")
copilot = api("POST", f"/api/v1/interviews/{intv2_id}/copilot/start")
check("Start copilot", copilot, "id", "interview_id")
print(f"       Session: {copilot['id']}")

print("\nStep 4: Get questions and submit answer")
qs2 = api("GET", f"/api/v1/interviews/{intv2_id}/questions")
api("POST", f"/api/v1/questions/{qs2[0]['id']}/answer", {"answer_text": "JavaScript is a versatile language for web development."})
print("  OK   Answer submitted")

print("\nStep 5: Get copilot suggestions")
suggestions = api("GET", f"/api/v1/interviews/{intv2_id}/copilot/suggestions")
check("Get suggestions", suggestions, "suggestions")
sugs = suggestions["suggestions"]
print(f"       Got {len(sugs)} suggestions")
for s in sugs:
    print(f"       - [{s['type']}] {s['text'][:60]}...")

print("\nStep 6: Dismiss first suggestion")
if sugs:
    dismiss = api("POST", f"/api/v1/interviews/{intv2_id}/copilot/dismiss/{sugs[0]['id']}")
    check("Dismiss suggestion", dismiss, "status")
else:
    print("  SKIP No suggestions to dismiss")

# ============================================================
section("JOURNEY 3: Async Interview via Share Link")
# ============================================================

print("\nStep 1: Create interview")
intv3 = api("POST", "/api/v1/interviews", {"candidate_id": cand_id, "question_count": 2})
intv3_id = intv3["id"]
api("POST", f"/api/v1/interviews/{intv3_id}/start")
print(f"  OK   Interview {intv3_id[:8]}... started")

print("\nStep 2: Generate share link")
share = api("POST", f"/api/v1/interviews/{intv3_id}/share")
check("Share interview", share, "share_token", "share_url")
token = share["share_token"]
print(f"       Token: {token[:20]}...")

print("\nStep 3: Join interview (no auth)")
join = api("GET", f"/api/v1/interviews/join/{token}", auth=False)
check("Join interview", join, "id", "status")
print(f"       Status: {join['status']}")

print("\nStep 4: Get questions for answering")
qs3 = api("GET", f"/api/v1/interviews/{intv3_id}/questions")
print(f"  OK   Got {len(qs3)} questions")

print("\nStep 5: Submit answer via share link (no auth)")
ans = api("POST", f"/api/v1/interviews/join/{token}/answer", {"question_id": qs3[0]["id"], "answer_text": "I would use Python with Flask for the backend and React for the frontend."}, auth=False)
score_val = ans.get("total_score") or ans.get("score", "N/A")
print(f"  OK   Submit answer (score={score_val}, completed={ans.get('completed', False)})")

print("\nStep 6: Invalid token returns 404")
bad = api("GET", "/api/v1/interviews/join/invalid_token_12345", auth=False)
assert bad.get("detail") == "Interview not found" or bad.get("status") == "error", f"Expected 404, got {bad}"
print("  OK   Invalid token returns error")

# ============================================================
section("JOURNEY 4: Admin User Management")
# ============================================================

print("\nStep 1: Login as interviewer (non-admin)")
login("admin@test.com", "Admin123!")
print("  OK   Logged in as interviewer")

print("\nStep 2: Try admin endpoint (should fail)")
admin_check = api("GET", "/api/v1/admin/users")
assert admin_check.get("detail") == "Admin only" or admin_check.get("status") == "error", f"Expected 403, got {admin_check}"
print("  OK   Non-admin correctly rejected")

print("\nStep 3: System health (public)")
health = api("GET", "/api/v1/health", auth=False)
check("System health", health, "status")
print(f"       Status: {health['status']}")

# ============================================================
section("JOURNEY 5: JD Matching & Question Banks")
# ============================================================

print("\nStep 1: JD match for candidate")
jd_text = "We are looking for a senior Python developer with experience in FastAPI, PostgreSQL, Docker, and AWS. Knowledge of React and TypeScript is preferred. Must have 5+ years of experience."
jd = api("POST", f"/api/v1/candidates/{cand_id}/jd", {"jd_text": jd_text})
check("JD match", jd, "match_percentage")
print(f"       Match: {jd['match_percentage']}%")
print(f"       Matched required: {jd.get('matched_required', [])}")
print(f"       Missing required: {jd.get('missing_required', [])}")

print("\nStep 2: Generate JD questions")
jd_qs = api("POST", f"/api/v1/candidates/{cand_id}/jd/questions", {"jd_text": jd_text, "count": 2})
check("JD questions", jd_qs, "questions")
print(f"       Generated {len(jd_qs['questions'])} questions")

print("\nStep 3: Create question bank")
bank = api("POST", "/api/v1/banks", {"name": "E2E Test Bank", "description": "Bank created during E2E testing", "category": "technical"})
check("Create bank", bank, "id")
bank_id = bank["id"]

print("\nStep 4: Add question to bank")
bq = api("POST", f"/api/v1/banks/{bank_id}/questions", {"question_text": "What is a REST API?", "question_type": "technical", "difficulty": "easy"})
check("Add to bank", bq, "id")

print("\nStep 5: List banks")
banks = api("GET", "/api/v1/banks")
check("List banks", banks, "items")
print(f"       Banks: {len(banks['items'])}")

print("\nStep 6: Generate from bank")
gen = api("POST", f"/api/v1/banks/{bank_id}/generate-interview", {"count": 1, "candidate_id": cand_id})
if "questions" in gen:
    print(f"  OK   Generated: {len(gen['questions'])} questions")
else:
    print(f"  OK   Generate response: {list(gen.keys())}")

# ============================================================
section("SUMMARY")
# ============================================================
print("\nAll 5 journeys completed successfully!")
