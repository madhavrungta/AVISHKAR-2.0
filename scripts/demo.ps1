# SIH 26162 - seed demo data and start the FastAPI backend (Windows).
# Usage (from repo root):  .\scripts\demo.ps1
# Optional:  .\scripts\demo.ps1 -SeedOnly

param(
    [switch]$SeedOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$VenvPython = Join-Path $Backend "venv\Scripts\python.exe"
$VenvPip = Join-Path $Backend "venv\Scripts\pip.exe"
$EnvFile = Join-Path $Backend ".env"
$EnvExample = Join-Path $Backend ".env.example"

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  SIH 26162 - Phase 8 Judge Demo" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $Backend

if (-not (Test-Path $VenvPython)) {
    Write-Host 'Step 1/4: Creating Python venv...' -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host 'Step 1/4: Using existing backend\venv' -ForegroundColor Green
}

Write-Host 'Step 2/4: Installing / verifying Python dependencies...' -ForegroundColor Yellow
& $VenvPip install -q -r requirements.txt

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host 'Env: Created backend\.env from .env.example (seed works without FIRMS_MAP_KEY)' -ForegroundColor Green
    } else {
        Write-Host 'Env: WARNING - backend\.env.example missing' -ForegroundColor Yellow
    }
} else {
    Write-Host 'Env: Using existing backend\.env' -ForegroundColor Green
}

Write-Host 'Step 3/4: Seeding Indian industrial hubs + running all 8 pipeline phases...' -ForegroundColor Yellow
& $VenvPython -m app.seed
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: Seed failed.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host 'Seed complete. Next: open a second terminal and run:' -ForegroundColor Green
Write-Host '  cd frontend' -ForegroundColor White
Write-Host '  npm install' -ForegroundColor White
Write-Host '  npm run dev' -ForegroundColor White
Write-Host 'Then open http://localhost:5173' -ForegroundColor White
Write-Host 'API docs: http://localhost:8000/docs' -ForegroundColor White
Write-Host ""

if ($SeedOnly) {
    Write-Host 'Step 4/4: Seed-only mode - skipping uvicorn.' -ForegroundColor Yellow
    exit 0
}

Write-Host 'Step 4/4: Starting API on http://localhost:8000 ...' -ForegroundColor Yellow
& $VenvPython -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
