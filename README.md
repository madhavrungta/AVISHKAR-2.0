# AI-Based Detection & Classification of Industrial Fires and Persistent Thermal Sources

**Problem Statement ID:** 26162  
**Organization:** National Technical Research Organisation (NTRO)  
**Category:** Software  
**Status:** Phase 8 — Multi-Modal Verification & Risk Scoring (demo-ready)

---

## 1. Project Overview

Geospatial surveillance platform that ingests NASA FIRMS thermal anomalies, links them to industrial facilities (OpenStreetMap), builds facility baselines, flags abnormal heat, and scores investigative risk.

> [!IMPORTANT]
> A NASA FIRMS detection is a **thermal anomaly**, not a confirmed fire. Industrial sites routinely emit high mid-IR energy (kilns, flaring, furnaces). This system uses scientific wording and does not claim “confirmed fires” without multi-source verification.

---

## 2. 8-Phase Pipeline

| Phase | Capability |
|------:|------------|
| 1 | NASA FIRMS ingestion + raw CSV archive + PostGIS/SQLite persistence |
| 2 | OSM industrial facility ingest |
| 3 | Spatial association (thermal point ↔ facility) |
| 4 | Candidate source classification (industrial / natural / agricultural / other) |
| 5 | Historical facility thermal behavior |
| 6 | Normal operating baselines (e.g. P95) |
| 7 | Abnormal event detection (FRP above baseline) |
| 8 | Multi-criteria risk score (0–100) + optical confidence **proxy** |

Details: [`docs/architecture.md`](docs/architecture.md) and the other phase docs under `docs/`.

---

## 3. Quick Judge Demo (recommended)

Fastest path to a full map with Indian industrial hubs, associations, anomalies, and risk tiers — **no live FIRMS key required**.

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Docker Desktop for PostGIS

### One-command seed + backend

**Windows (PowerShell)** from the repo root:

```powershell
.\scripts\demo.ps1
```

**macOS / Linux:**

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

What it does:
1. Creates `backend/venv` and installs Python deps if needed  
2. Ensures `backend/.env` exists (copies from example)  
3. Seeds demo data and runs all 8 pipeline phases  
4. Starts the API on [http://localhost:8000](http://localhost:8000)  

Then in a **second terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Demo talk track
1. Map: FIRMS points + industrial facilities (Jamnagar, Trombay, Tata Steel, Vizag, …)  
2. Associations / classifications in the stats panel  
3. Abnormal spikes vs facility baselines  
4. Risk tiers (`CRITICAL_VERIFIED_RISK` → `LOW_RISK`)  
5. Optional: header **risk evaluate** button; overlay **FIRMS ingest** if a real `FIRMS_MAP_KEY` is set  

API docs while backend is up: [http://localhost:8000/docs](http://localhost:8000/docs).

### Seed only (no server)

```bash
cd backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
python -m app.seed
# or: python -m app.cli seed
```

---

## 4. Environment Configuration

1. Copy examples (demo script does this for `backend/.env` if missing):

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

2. For **live** FIRMS pulls, set a key from [NASA FIRMS map key](https://firms.modaps.eosdis.nasa.gov/api/map_key):

```ini
FIRMS_MAP_KEY=your_actual_map_key_here
FIRMS_SOURCE=VIIRS_SNPP_NRT
FIRMS_AREA=68.0,6.0,97.0,37.0
FIRMS_DAYS=1
```

Without a key, use the **seeded demo** above. Default bbox is India.

---

## 5. Run Backend Manually

### Option A: Local Python

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Docker Compose (PostGIS + backend)

```bash
docker-compose up --build
```

Backend: `:8000` · Postgres/PostGIS: `:5432`  
Frontend is **not** in Compose — run it separately (§3).

---

## 6. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` → `http://localhost:8000`.

---

## 7. Live Ingestion & Pipeline CLI

```bash
cd backend
python -m app.cli status
python -m app.cli seed
python -m app.cli ingest-firms --source VIIRS_SNPP_NRT --days 1
python -m app.cli ingest-osm
python -m app.cli run-associations --recalculate
python -m app.cli run-classification --recalculate
python -m app.cli run-history --recalculate
python -m app.cli generate-baselines --recalculate
python -m app.cli detect-anomalies --recalculate
python -m app.cli evaluate-risk --recalculate
```

UI alternatives: **Execute FIRMS API Ingestion** on the map overlay, or `POST` jobs via `/docs`.

---

## 8. Tests

```bash
cd backend
pytest -v
```

---

## 9. Data & API Surface

- **Raw FIRMS CSV:** `backend/data/raw/firms_<source>_<timestamp>_<batch_id>.csv`
- **DB:** PostgreSQL + PostGIS when `DATABASE_URL` is Postgres; otherwise local SQLite (`thermal_observations.db`)
- **Geometry:** `POINT` in EPSG:4326

| Area | Examples |
|------|----------|
| Health | `GET /health` |
| Thermal | `GET /thermal-observations`, `GET /analytics/summary` |
| Ingest | `POST /ingestion/firms`, `POST /ingestion/osm` |
| Facilities | `GET /industrial-facilities` |
| Pipeline jobs | `POST /associations/run`, `/classification/run`, `/history/aggregate`, `/baselines/generate`, `/anomalies/detect`, `/risk/evaluate` |
| Risk | `GET /risk`, `GET /analytics/risk-summary` |

---

## 10. Scientific Limitations

- Classification is **rule/heuristic**, not a trained deep model.
- “Optical verification” in Phase 8 is a **confidence proxy** (not live Sentinel-2 / Landsat APIs).
- Suitable for SIH demonstration and investigator triage UX; not production ops hardening.
