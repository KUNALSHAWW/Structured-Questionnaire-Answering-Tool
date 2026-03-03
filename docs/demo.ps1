# PowerShell demo script for Windows
# Run from the project root: .\docs\demo.ps1

$BASE = "http://localhost:8000"
$EMAIL = "demo@novatech.test"
$PASSWORD = "demo1234"

Write-Host "=== 1. Register user ===" -ForegroundColor Cyan
$body = @{ email = $EMAIL; password = $PASSWORD } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/api/auth/register" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json

Write-Host "`n=== 2. Login ===" -ForegroundColor Cyan
$loginResp = Invoke-RestMethod -Uri "$BASE/api/auth/login" -Method POST -Body $body -ContentType "application/json"
$TOKEN = $loginResp.access_token
$headers = @{ Authorization = "Bearer $TOKEN" }
Write-Host "Got token: $($TOKEN.Substring(0,20))..."

Write-Host "`n=== 3. Upload questionnaire ===" -ForegroundColor Cyan
$qFile = Get-Item "sample_data\questionnaire.txt"
$form = @{ file = $qFile }
Invoke-RestMethod -Uri "$BASE/api/uploads/questionnaire" -Method POST -Headers $headers -Form $form | ConvertTo-Json

Write-Host "`n=== 4. Upload reference documents ===" -ForegroundColor Cyan
$refs = @("company_overview.txt", "security_policy.txt", "hr_report.txt", "disaster_recovery.txt", "esg_report.txt")
foreach ($r in $refs) {
    Write-Host "  Uploading $r ..."
    $refFile = Get-Item "sample_data\$r"
    $form = @{ file = $refFile }
    Invoke-RestMethod -Uri "$BASE/api/uploads/reference" -Method POST -Headers $headers -Form $form | ConvertTo-Json
}

Write-Host "`n=== 5. Build index ===" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$BASE/api/index/build" -Method POST -Headers $headers -ContentType "application/json" | ConvertTo-Json

Write-Host "`n=== 6. List questionnaires ===" -ForegroundColor Cyan
$qs = Invoke-RestMethod -Uri "$BASE/api/uploads/questionnaires" -Headers $headers
$QID = $qs[0].id
Write-Host "Questionnaire ID: $QID"

Write-Host "`n=== 7. Generate answers ===" -ForegroundColor Cyan
$genBody = @{ questionnaire_id = $QID } | ConvertTo-Json
$runResp = Invoke-RestMethod -Uri "$BASE/api/generate" -Method POST -Headers $headers -Body $genBody -ContentType "application/json"
$runResp | ConvertTo-Json -Depth 5
$RUN_ID = $runResp.run_id
Write-Host "Run ID: $RUN_ID"

Write-Host "`n=== 8. Export XLSX ===" -ForegroundColor Cyan
Invoke-WebRequest -Uri "$BASE/api/export/$RUN_ID`?format=xlsx" -Headers $headers -OutFile "answers_demo.xlsx"
Write-Host "Exported to answers_demo.xlsx"

Write-Host "`n=== 9. Export PDF ===" -ForegroundColor Cyan
Invoke-WebRequest -Uri "$BASE/api/export/$RUN_ID`?format=pdf" -Headers $headers -OutFile "answers_demo.pdf"
Write-Host "Exported to answers_demo.pdf"

Write-Host "`n=== Demo complete! ===" -ForegroundColor Green
