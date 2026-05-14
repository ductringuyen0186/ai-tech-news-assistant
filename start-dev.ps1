# start-dev.ps1 - TechPulse AI dev stack launcher
#
# Boots backend (FastAPI :8000) + frontend (Vite :3000) in two new
# PowerShell windows. Before launching, runs preflight checks:
#   1. Backend venv exists + has langchain-core / deepagents.
#   2. Backend news.db has populated article_embeddings (RAG fuel).
#   3. Frontend node_modules is installed.
# If any of those are missing, the script auto-fixes before launching.
#
# Usage:   .\start-dev.ps1
# Bypass exec policy:  powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPy = Join-Path $backend "venv\Scripts\python.exe"

function Info($m) { Write-Host "  $m" -ForegroundColor DarkCyan }
function Ok($m)   { Write-Host "  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "  $m" -ForegroundColor Red }
function Section($t) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host (" " + $t) -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

Section "TechPulse AI - starting dev stack"
Info "root:     $root"
Info "backend:  $backend  (FastAPI on :8000)"
Info "frontend: $frontend (Vite on :3000)"

# ============ Preflight ============
Section "Preflight"

# 1. Backend venv
if (-not (Test-Path $venvPy)) {
    Warn "Backend venv missing - creating..."
    & py -m venv (Join-Path $backend "venv")
    if (-not (Test-Path $venvPy)) { Fail "Could not create venv. Install Python 3.13+ first."; exit 1 }
    Ok "venv created"
}

# 2. Backend deps - quick import probe; if it fails, run pip install -r requirements.txt
$probe = & $venvPy -c "import langchain_core, langchain_ollama, deepagents, fastapi; print('OK')" 2>&1
if ($probe -notmatch "OK") {
    Warn "Backend deps incomplete (missing langchain-core / deepagents / etc.)"
    Info "Running: pip install -r requirements.txt (this may take a few minutes)"
    Push-Location $backend
    & $venvPy -m pip install -r requirements.txt
    Pop-Location
    # Re-probe
    $probe2 = & $venvPy -c "import langchain_core, langchain_ollama, deepagents, fastapi; print('OK')" 2>&1
    if ($probe2 -notmatch "OK") {
        Fail "Backend deps still missing after pip install. Aborting."
        Fail "Probe output: $probe2"
        exit 1
    }
    Ok "Backend deps installed"
} else {
    Ok "Backend deps OK (langchain-core, langchain-ollama, deepagents, fastapi)"
}

# 3. Article embeddings populated
$dbCheck = & $venvPy -c "import sqlite3, os; os.chdir(r'$backend'); c=sqlite3.connect('news.db'); n=c.execute('SELECT COUNT(*) FROM article_embeddings').fetchone()[0]; print(n)" 2>&1
if ($dbCheck -match "^\d+$" -and [int]$dbCheck -gt 0) {
    Ok "Article embeddings populated ($dbCheck rows)"
} else {
    Warn "Article embeddings empty or missing - agentic research will say 'Could not find data'"
    Info "Running: python scripts/backfill_embeddings.py (one-time, ~2s for 80 articles)"
    Push-Location $backend
    & $venvPy scripts/backfill_embeddings.py
    Pop-Location
    Ok "Embeddings backfilled"
}

# 4. Frontend node_modules
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Warn "Frontend node_modules missing - running npm install (one-time, 1-3 minutes)"
    Push-Location $frontend
    & npm install
    Pop-Location
    Ok "node_modules installed"
} else {
    Ok "Frontend node_modules OK"
}

# ============ Launch ============
Section "Launching services"

# Backend: must run from backend/ cwd so settings.database_path resolves to news.db
$backendCmd = "Set-Location '$backend'; Write-Host 'Backend (FastAPI) - http://localhost:8000' -ForegroundColor Green; & '$venvPy' -m uvicorn src.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Info "Backend window opened"

Start-Sleep -Seconds 2

# Frontend: dev server on :3000 (matches playwright.config.ts baseURL)
$frontendCmd = "Set-Location '$frontend'; Write-Host 'Frontend (Vite) - http://localhost:3000' -ForegroundColor Green; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
Info "Frontend window opened"

Section "Ready"
Info "Open in browser:"
Write-Host "  http://localhost:3000/" -ForegroundColor White -NoNewline; Write-Host "          (Welcome)" -ForegroundColor DarkGray
Write-Host "  http://localhost:3000/feed" -ForegroundColor White -NoNewline;     Write-Host "       (News Feed)" -ForegroundColor DarkGray
Write-Host "  http://localhost:3000/research" -ForegroundColor White -NoNewline; Write-Host "   (Agentic Research)" -ForegroundColor DarkGray
Write-Host "  http://localhost:3000/knowledge" -ForegroundColor White -NoNewline;Write-Host "  (Knowledge Graph)" -ForegroundColor DarkGray
Write-Host "  http://localhost:3000/digest" -ForegroundColor White -NoNewline;   Write-Host "     (Daily Digest)" -ForegroundColor DarkGray
Write-Host "  http://localhost:3000/saved" -ForegroundColor White -NoNewline;    Write-Host "      (Saved Research)" -ForegroundColor DarkGray
Write-Host "  http://localhost:3000/settings" -ForegroundColor White -NoNewline; Write-Host "   (Settings)" -ForegroundColor DarkGray
Write-Host ""
Info "Close either service window to stop it. Ctrl+C inside a window also works."
