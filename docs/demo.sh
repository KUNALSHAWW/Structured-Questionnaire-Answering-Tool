#!/usr/bin/env bash
# demo.sh — End-to-end demo of the Questionnaire Answering Tool
# Run from the project root: bash docs/demo.sh

set -euo pipefail

BASE="http://localhost:8000"
EMAIL="demo@novatech.test"
PASSWORD="demo1234"

echo "=== 1. Register user ==="
curl -s -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" | python -m json.tool

echo ""
echo "=== 2. Login ==="
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Got token: ${TOKEN:0:20}..."

AUTH="Authorization: Bearer $TOKEN"

echo ""
echo "=== 3. Upload questionnaire ==="
curl -s -X POST "$BASE/api/uploads/questionnaire" \
  -H "$AUTH" \
  -F "file=@sample_data/questionnaire.txt" | python -m json.tool

echo ""
echo "=== 4. Upload reference documents ==="
for f in sample_data/company_overview.txt sample_data/security_policy.txt sample_data/hr_report.txt sample_data/disaster_recovery.txt sample_data/esg_report.txt; do
  echo "  Uploading $f ..."
  curl -s -X POST "$BASE/api/uploads/reference" \
    -H "$AUTH" \
    -F "file=@$f" | python -m json.tool
done

echo ""
echo "=== 5. Build index ==="
curl -s -X POST "$BASE/api/index/build" \
  -H "$AUTH" \
  -H "Content-Type: application/json" | python -m json.tool

echo ""
echo "=== 6. List questionnaires (get ID) ==="
QID=$(curl -s "$BASE/api/uploads/questionnaires" -H "$AUTH" | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
echo "Questionnaire ID: $QID"

echo ""
echo "=== 7. Generate answers ==="
RUN_RESPONSE=$(curl -s -X POST "$BASE/api/generate" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"questionnaire_id\": \"$QID\"}")
echo "$RUN_RESPONSE" | python -m json.tool

RUN_ID=$(echo "$RUN_RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['run_id'])")
echo "Run ID: $RUN_ID"

echo ""
echo "=== 8. Export XLSX ==="
curl -s -o "answers_demo.xlsx" "$BASE/api/export/$RUN_ID?format=xlsx" -H "$AUTH"
echo "Exported to answers_demo.xlsx"

echo ""
echo "=== 9. Export PDF ==="
curl -s -o "answers_demo.pdf" "$BASE/api/export/$RUN_ID?format=pdf" -H "$AUTH"
echo "Exported to answers_demo.pdf"

echo ""
echo "=== Demo complete! ==="
