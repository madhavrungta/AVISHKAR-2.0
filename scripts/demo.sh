#!/usr/bin/env bash
# SIH 26162 — seed demo data and start the FastAPI backend.
# Usage (from repo root):  ./scripts/demo.sh
# Optional:  ./scripts/demo.sh --seed-only

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
SEED_ONLY=0

if [[ "${1:-}" == "--seed-only" ]]; then
  SEED_ONLY=1
fi

echo ""
echo "======================================================="
echo "  SIH 26162 — Phase 8 Judge Demo"
echo "======================================================="
echo ""

cd "$BACKEND"

if [[ ! -x "venv/bin/python" ]]; then
  echo "[1/4] Creating Python venv..."
  python3 -m venv venv
else
  echo "[1/4] Using existing backend/venv"
fi

echo "[2/4] Installing / verifying Python dependencies..."
./venv/bin/pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "[env] Created backend/.env from .env.example (seed works without FIRMS_MAP_KEY)"
  else
    echo "[env] WARNING: backend/.env.example missing"
  fi
else
  echo "[env] Using existing backend/.env"
fi

echo "[3/4] Seeding Indian industrial hubs + running all 8 pipeline phases..."
./venv/bin/python -m app.seed

echo ""
echo "Seed complete. Next: open a second terminal and run:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
echo "Then open http://localhost:5173"
echo "API docs: http://localhost:8000/docs"
echo ""

if [[ "$SEED_ONLY" -eq 1 ]]; then
  echo "[4/4] Seed-only mode — skipping uvicorn."
  exit 0
fi

echo "[4/4] Starting API on http://localhost:8000 ..."
exec ./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
