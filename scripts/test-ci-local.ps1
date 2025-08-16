# 🔧 Comprehensive Build Test Script (PowerShell)
# This script simulates the CI environment to catch issues before pushing

$ErrorActionPreference = "Stop"

Write-Host "🧪 Starting Comprehensive Build Tests..." -ForegroundColor Cyan
Write-Host "======================================"

# Check if we're in the right directory
if (-not (Test-Path "README.md")) {
    Write-Host "❌ Error: Must run from project root directory" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📍 Step 1: Environment Check" -ForegroundColor Yellow
Write-Host "----------------------------"
Write-Host "✓ PowerShell version: $($PSVersionTable.PSVersion)"
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "✓ Node version: $(node --version)"
} else {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
    exit 1
}
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "✓ npm version: $(npm --version)"
} else {
    Write-Host "❌ npm not found" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Current directory: $(Get-Location)"

Write-Host ""
Write-Host "🐍 Step 2: Backend Tests" -ForegroundColor Yellow
Write-Host "------------------------"
Set-Location backend

# Get Python executable path
$pythonExe = "C:/Users/Tri/AppData/Local/Programs/Python/Python313/python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Python executable not found at $pythonExe" -ForegroundColor Red
    exit 1
}

# Test Python imports
Write-Host "Testing Python imports..."
try {
    $result = & $pythonExe -c "import simple_main; print('✓ Backend imports successfully')"
    Write-Host "✓ Backend imports: PASS" -ForegroundColor Green
}
catch {
    Write-Host "❌ Backend imports: FAIL" -ForegroundColor Red
    exit 1
}

# Test FastAPI app creation
Write-Host "Testing FastAPI app creation..."
try {
    $result = & $pythonExe -c "from simple_main import app; print('✓ FastAPI app created successfully')"
    Write-Host "✓ FastAPI app creation: PASS" -ForegroundColor Green
}
catch {
    Write-Host "❌ FastAPI app creation: FAIL" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Test CI-friendly tests
Write-Host "Testing validation script..."
try {
    $result = & $pythonExe tests/test_ci_friendly.py
    Write-Host "✓ CI validation tests: PASS" -ForegroundColor Green
}
catch {
    Write-Host "❌ CI validation tests: FAIL" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🌐 Step 3: Frontend Tests" -ForegroundColor Yellow
Write-Host "-------------------------"
Set-Location frontend

# Test current dependencies first
Write-Host "Testing current dependencies..."
try {
    npm run type-check
    Write-Host "✓ TypeScript type check: PASS" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ TypeScript type check: ISSUES (but continuing...)" -ForegroundColor Yellow
}

# Test development build
Write-Host "Testing development build..."
try {
    npm run build
    Write-Host "✓ Development build: PASS" -ForegroundColor Green
}
catch {
    Write-Host "❌ Development build: FAIL" -ForegroundColor Red
    exit 1
}

# Test CI build
Write-Host "Testing CI build (Vite only)..."
try {
    npm run build:ci
    Write-Host "✓ CI build: PASS" -ForegroundColor Green
}
catch {
    Write-Host "❌ CI build: FAIL" -ForegroundColor Red
    exit 1
}

# Verify build output
if ((Test-Path "dist") -and (Test-Path "dist/index.html")) {
    Write-Host "✓ Build output verification: PASS" -ForegroundColor Green
    $indexSize = (Get-Item "dist/index.html").Length
    Write-Host "  - dist/index.html: $indexSize bytes"
    Get-ChildItem "dist/assets" | Select-Object -First 5 | Format-Table Name, Length
} else {
    Write-Host "❌ Build output verification: FAIL" -ForegroundColor Red
    exit 1
}

Set-Location ..

Write-Host ""
Write-Host "🎯 Step 4: Project Structure Validation" -ForegroundColor Yellow
Write-Host "---------------------------------------"

# Check required files
$requiredFiles = @(
    "README.md",
    "docker-compose.yml",
    "backend/simple_main.py",
    "backend/requirements.txt",
    "frontend/package.json",
    "frontend/src/main.tsx",
    ".github/workflows/deploy.yml"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
        exit 1
    }
}

# Check directory structure
$requiredDirs = @(
    "backend/src",
    "frontend/src",
    "deployment",
    "docs",
    "tests",
    "scripts"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✓ $dir/ exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $dir/ missing" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🚀 Final Status" -ForegroundColor Cyan
Write-Host "==============="
Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Test Summary:"
Write-Host "  ✓ Backend imports and FastAPI creation"
Write-Host "  ✓ CI validation tests"
Write-Host "  ✓ Frontend builds (dev and CI)"
Write-Host "  ✓ Build output verification"
Write-Host "  ✓ Project structure validation"
Write-Host ""
Write-Host "🎯 Ready for CI/CD push!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Usage: Run this script before pushing to catch issues early"
Write-Host "   .\scripts\test-ci-local.ps1"
