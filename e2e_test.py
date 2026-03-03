"""End-to-end smoke test script."""
import httpx
import json
import sys

BASE = "http://localhost:8000"
c = httpx.Client(base_url=BASE, timeout=120)

# 1. Register
print("=== REGISTER ===")
r = c.post("/api/auth/register", json={"email": "demo@test.com", "password": "test1234"})
print(r.status_code, r.json())

# 2. Login
print("\n=== LOGIN ===")
r = c.post("/api/auth/login", json={"email": "demo@test.com", "password": "test1234"})
token = r.json()["access_token"]
print("Token:", token[:30], "...")
headers = {"Authorization": f"Bearer {token}"}

# 3. Upload questionnaire
print("\n=== UPLOAD QUESTIONNAIRE ===")
with open("sample_data/questionnaire.txt", "rb") as f:
    r = c.post("/api/uploads/questionnaire", files={"file": ("questionnaire.txt", f)}, headers=headers)
qdata = r.json()
print(json.dumps(qdata, indent=2))
qid = qdata["questionnaire_id"]

# 4. Upload references
print("\n=== UPLOAD REFERENCES ===")
for fname in ["company_overview.txt", "security_policy.txt", "hr_report.txt", "disaster_recovery.txt", "esg_report.txt"]:
    with open(f"sample_data/{fname}", "rb") as f:
        r = c.post("/api/uploads/reference", files={"file": (fname, f)}, headers=headers)
    resp = r.json()
    print(f"  {fname}: {resp['text_length']} chars")

# 5. Build index
print("\n=== BUILD INDEX ===")
r = c.post("/api/index/build", headers=headers)
print(json.dumps(r.json(), indent=2))

# 6. Generate answers
print("\n=== GENERATE ANSWERS ===")
r = c.post("/api/generate", json={"questionnaire_id": qid}, headers=headers)
gen = r.json()
run_id = gen["run_id"]
print(f"Run ID: {run_id}")
print(f"Number of answers: {gen['num_answers']}")

for ans in gen["answers"]:
    print(f"\n--- Q{ans['question_index']}: {ans['question_text'][:60]}...")
    print(f"    Answer: {ans['answer_text'][:120]}...")
    print(f"    Citations: {ans['citations']}")
    print(f"    Confidence: {ans['confidence_score']}%")

# 7. Export XLSX
print("\n=== EXPORT XLSX ===")
r = c.get(f"/api/export/{run_id}?format=xlsx", headers=headers)
with open("test_export.xlsx", "wb") as f:
    f.write(r.content)
print(f"Exported XLSX: {len(r.content)} bytes -> test_export.xlsx")

# 8. Export PDF
print("\n=== EXPORT PDF ===")
r = c.get(f"/api/export/{run_id}?format=pdf", headers=headers)
with open("test_export.pdf", "wb") as f:
    f.write(r.content)
print(f"Exported PDF: {len(r.content)} bytes -> test_export.pdf")

print("\n=== ALL STEPS PASSED ===")
