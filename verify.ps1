# verify.ps1 - TechPulse AI full verification mission (Windows-side runner)
#
# What it does, in order:
#   1. Frontend production build (vite build) - catches type / CSS errors.
#   2. Backend import smoke (python -c "from src.main import app").
#   3. Boots backend on :8000 and frontend on :5173 as background jobs.
#   4. Curls /api/health and /api/news/?page_size=3 to confirm endpoints.
#   5. Installs Playwright chromium browser if missing.
#   6. Runs the full Playwright suite excluding the visual-baseline file
#      (which is expected to diff on every redesign).
#   7. Reports pass / fail count.
#   8. Asks whether you want to regenerate the visual baselines now.
#   9. Cleans up background processes.
#
# Usage:   .\verify.ps1
# Bypass execution policy if needed:
#   powershell -ExecutionPolicy Bypass -File .\verify.ps1

$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

function Section($title) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host (" " + $title) -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Status($ok, $msg) {
    if ($ok) {
        Write-Host "  [ OK ]   $msg" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL]   $msg" -ForegroundColor Red
    }
}

$failures = @()

# --- Phase 1: frontend build -------------------------------------------------
Section "Phase 1 / 5  --  Frontend production build"
Push-Location $frontend
$buildOut = & npm run build 2>&1 | Out-String
$buildOk = $LASTEXITCODE -eq 0
Status $buildOk "vite build"
if (-not $buildOk) {
    Write-Host $buildOut
    $failures += "vite build failed"
}
Pop-Location

# --- Phase 2: backend smoke --------------------------------------------------
Section "Phase 2 / 5  --  Backend import + boot smoke"
Push-Location $backend
$importOut = & python -c "import sys; sys.path.insert(0, '.'); from src.main import app; print(len(app.routes))" 2>&1
$importOk = $LASTEXITCODE -eq 0
Status $importOk "backend imports cleanly ($importOut routes)"
if (-not $importOk) { $failures += "backend import failed" }
Pop-Location

# --- Phase 3: boot both services in background -------------------------------
Section "Phase 3 / 5  --  Booting servers (background)"

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:backend
    python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 2>&1
}
Write-Host "  backend job: $($backendJob.Id)"

$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:frontend
    & "$using:frontend\node_modules\.bin\vite.cmd" --host 127.0.0.1 --port 5173 2>&1
}
Write-Host "  frontend job: $($frontendJob.Id)"

Write-Host "  waiting 10s for both to come up..." -ForegroundColor DarkGray
Start-Sleep -Seconds 10

# Health checks
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 6 -ErrorAction Stop
    Status ($r.StatusCode -eq 200) "GET /api/health -> $($r.StatusCode)"
    if ($r.StatusCode -ne 200) { $failures += "backend health failed" }
} catch {
    Status $false "GET /api/health -> $($_.Exception.Message)"
    $failures += "backend health failed"
}

try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/news/?page_size=3" -UseBasicParsing -TimeoutSec 6 -ErrorAction Stop
    Status ($r.StatusCode -eq 200) "GET /api/news/?page_size=3 -> $($r.StatusCode)"
    if ($r.StatusCode -ne 200) { $failures += "news endpoint failed" }
} catch {
    Status $false "GET /api/news/ -> $($_.Exception.Message)"
    $failures += "news endpoint failed"
}

try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 6 -ErrorAction Stop
    Status ($r.StatusCode -eq 200) "GET http://127.0.0.1:5173/ -> $($r.StatusCode)"
    if ($r.StatusCode -ne 200) { $failures += "frontend serve failed" }
} catch {
    Status $false "GET http://127.0.0.1:5173/ -> $($_.Exception.Message)"
    $failures += "frontend serve failed"
}

# --- Phase 4: Playwright -----------------------------------------------------
Section "Phase 4 / 5  --  Playwright functional suite"

Push-Location $frontend

# Install browsers if needed (idempotent)
Write-Host "  ensuring chromium is installed..." -ForegroundColor DarkGray
& npx --yes playwright install chromium 2>&1 | Out-Null

# Run the functional suite (exclude visual-baselines which always diff)
Write-Host "  running playwright test (excluding m3-visual-baselines)..." -ForegroundColor DarkGray
$pwOut = & npx playwright test --reporter=line --grep-invert "visual.baseline" 2>&1 | Out-String
$pwOk = $LASTEXITCODE -eq 0
Write-Host $pwOut
if ($pwOk) {
    Status $true "playwright suite green"
} else {
    Status $false "playwright suite has failures (see output above)"
    $failures += "playwright failures"
}
Pop-Location

# --- Phase 5: visual baselines (opt-in) --------------------------------------
Section "Phase 5 / 5  --  Visual baselines"
Write-Host "  Visual baselines (m3-visual-baselines.spec.ts) will diff after a redesign."
Write-Host "  Press 'r' to regenerate now, anything else to skip:" -NoNewline
$key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""
if ($key.Character -eq 'r' -or $key.Character -eq 'R') {
    Push-Location $frontend
    Write-Host "  regenerating snapshots..." -ForegroundColor Yellow
    & npx playwright test e2e/m3-visual-baselines.spec.ts --update-snapshots 2>&1 | Out-String | Write-Host
    Pop-Location
    Write-Host "  -> remember to git-commit the new snapshots:" -ForegroundColor DarkGray
    Write-Host "     git add frontend/e2e/m3-visual-baselines.spec.ts-snapshots/" -ForegroundColor DarkGray
    Write-Host "     git commit -m 'test(baselines): regenerate for Broadsheet Terminal'" -ForegroundColor DarkGray
} else {
    Write-Host "  skipped baseline regeneration." -ForegroundColor DarkGray
}

# --- Cleanup -----------------------------------------------------------------
Section "Cleanup"
Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue
# Belt-and-suspenders: kill any orphan node / python listening on our ports
Get-Process | Where-Object { $_.ProcessName -in @("node", "python") } |
    ForEach-Object {
        try {
            $conns = Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue
            if ($conns | Where-Object { $_.LocalPort -in @(8000, 5173) }) {
                Write-Host "  stopping $($_.ProcessName) PID $($_.Id)" -ForegroundColor DarkGray
                Stop-Process -Id $_.Id -Force
            }
        } catch {}
    }
Write-Host "  cleanup complete." -ForegroundColor DarkGray

# --- Final summary -----------------------------------------------------------
Section "Verification result"
if ($failures.Count -eq 0) {
    Write-Host "  All phases passed." -ForegroundColor Green
    Write-Host "  TechPulse AI is fully functional." -ForegroundColor Green
    exit 0
} else {
    Write-Host "  $($failures.Count) failure(s):" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host "    - $f" -ForegroundColor Red }
    exit 1
}
