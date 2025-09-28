# Build Test Script
Write-Host "Testing builds..." -ForegroundColor Green

# Test backend
Write-Host "Backend test..."
Set-Location backend
$result = C:/Users/Tri/AppData/Local/Programs/Python/Python313/python.exe -c "import production_main; print('OK')"
if ($LASTEXITCODE -eq 0) { Write-Host "Backend: PASS" -ForegroundColor Green } else { exit 1 }
Set-Location ..

# Test validation
Write-Host "Validation test..."
$result = C:/Users/Tri/AppData/Local/Programs/Python/Python313/python.exe tests/test_ci_simple.py
if ($LASTEXITCODE -eq 0) { Write-Host "Validation: PASS" -ForegroundColor Green } else { exit 1 }

# Test frontend
Write-Host "Frontend test..."
Set-Location frontend
npm run build:ci
if ($LASTEXITCODE -eq 0) { Write-Host "Frontend: PASS" -ForegroundColor Green } else { exit 1 }
Set-Location ..

Write-Host "ALL TESTS PASSED!" -ForegroundColor Green
