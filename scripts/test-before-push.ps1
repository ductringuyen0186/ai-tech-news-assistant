# 🔧 Simple Build Test Script (PowerShell)
# This script tests the build before pushing to catch CI issues

param([switch]$SkipFrontend)

Write-Host "🧪 Testing Build Before Push..." -ForegroundColor Cyan
Write-Host "================================"

# Check environment
Write-Host ""
Write-Host "📍 Environment Check" -ForegroundColor Yellow
if (-not (Test-Path "README.md")) {
    Write-Host "❌ Must run from project root" -ForegroundColor Red
    exit 1
}
Write-Host "✓ In project root"
Write-Host "✓ Node: $(node --version)"
Write-Host "✓ npm: $(npm --version)"

# Test backend
Write-Host ""
Write-Host "🐍 Backend Tests" -ForegroundColor Yellow
Set-Location backend

$pythonExe = "C:/Users/Tri/AppData/Local/Programs/Python/Python313/python.exe"
Write-Host "Testing backend imports..."
$importResult = & $pythonExe -c "import simple_main; print('Backend imports OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Backend imports: PASS" -ForegroundColor Green
} else {
    Write-Host "❌ Backend imports: FAIL" -ForegroundColor Red
    Write-Host $importResult
    exit 1
}

Set-Location ..

Write-Host "Testing validation script..."
$testResult = & $pythonExe tests/test_ci_friendly.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Validation tests: PASS" -ForegroundColor Green
} else {
    Write-Host "❌ Validation tests: FAIL" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}

# Test frontend
if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "🌐 Frontend Tests" -ForegroundColor Yellow
    Set-Location frontend

    Write-Host "Testing development build..."
    $buildResult = npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Development build: PASS" -ForegroundColor Green
    } else {
        Write-Host "❌ Development build: FAIL" -ForegroundColor Red
        Write-Host $buildResult
        exit 1
    }

    Write-Host "Testing CI build..."
    $ciBuildResult = npm run build:ci 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ CI build: PASS" -ForegroundColor Green
    } else {
        Write-Host "❌ CI build: FAIL" -ForegroundColor Red
        Write-Host $ciBuildResult
        exit 1
    }

    Set-Location ..
}

Write-Host ""
Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
Write-Host "🎯 Ready to push to GitHub!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage examples:"
Write-Host "  .\scripts\test-before-push.ps1          # Test everything"
Write-Host "  .\scripts\test-before-push.ps1 -SkipFrontend  # Skip frontend tests"
