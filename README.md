

Phase 1 establishes a reproducible pipeline for NASA FIRMS VIIRS thermal-anomaly observations. It fetches the official FIRMS Area API CSV, preserves each original response, validates and normalizes observations, stores valid records in PostGIS, and exposes a deliberately small GIS map for inspection.

> **Scientific scope:** a FIRMS record is a satellite thermal anomaly / active-fire detection. It is not proof of a confirmed fire, an industrial incident, or an industrial source. This phase does not perform facility association or classification.

## Architecture

```text
NASA FIRMS Area CSV API
          |
          v
HTTP retrieval + raw CSV/metadata archive
          |
          v
schema and quality validation
          |
          +--> validation report
          v
normalized thermal observations (EPSG:4326)
          |
          v
PostgreSQL + PostGIS --> FastAPI --> MapLibre validation map
```

The detailed design is in [docs/architecture.md](docs/architecture.md), [docs/firms-data.md](docs/firms-data.md), and [docs/data-model.md](docs/data-model.md).

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- Docker Desktop (recommended for PostgreSQL/PostGIS)
- A free NASA FIRMS `MAP_KEY`. Request one at the [official FIRMS API page](https://firms.modaps.eosdis.nasa.gov/api/map_key/).

## Configure credentials

Copy the root example to `backend/.env`, then replace the placeholder value:

```powershell
Copy-Item .env.example backend/.env
```

`FIRMS_MAP_KEY` is used only by the backend. Do not add it to frontend environment files, source code, screenshots, or logs. Change `FIRMS_AREA` to a bounding box (`west,south,east,north`) for focused, low-volume queries; for example `68,6,98,38`. The default `world` avoids assuming a country but can return many observations.

## Run with Docker Compose

```powershell
docker compose up --build
```

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Map: `http://localhost:5173`

## Run locally

Start PostGIS first:

```powershell
docker compose up -d db
```

Create and activate a virtual environment, then install backend packages:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Start the API from `backend`:

```powershell
uvicorn app.main:app --reload
```

Start the map in a second terminal:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run dev
```

## Ingest FIRMS observations

The CLI reads `backend/.env`:

```powershell
Set-Location backend
python -m app.cli firms-ingest --source VIIRS_SNPP_NRT --area "68,6,98,38" --days 1
```

Or request ingestion through the prototype API:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/ingestion/firms -ContentType application/json -Body '{"source":"VIIRS_SNPP_NRT","area":"68,6,98,38","days":1}'
```

The endpoint has no authentication in this prototype. It must be protected before deployment, because it initiates an external data fetch.

Every call first saves the unaltered CSV and a metadata/validation JSON file beneath `backend/data/raw/`. These local archives are intentionally ignored by Git. Valid observations are inserted into `thermal_observations`; invalid records remain documented in their raw-ingestion metadata and are never silently discarded.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | API and database readiness |
| GET | `/thermal-observations` | Latest validated observations as a paginated list |
| GET | `/thermal-observations/{id}` | One observation and preserved original fields |
| POST | `/ingestion/firms` | Fetch, archive, validate, and store an official FIRMS CSV |
| GET | `/analytics/summary` | Counts, sources, and time range |

## Tests

Tests are deterministic and use `httpx` mock transports; they never require NASA availability.

```powershell
Set-Location backend
pytest
```

Database integration tests are opt-in after PostGIS is running:

```powershell
$env:RUN_DATABASE_TESTS = "1"
pytest -m integration
```

An optional live FIRMS smoke test is also opt-in and uses the configured key:

```powershell
$env:RUN_LIVE_FIRMS_TESTS = "1"
pytest -m live
```

## Limitations in Phase 1

- No OSM facilities, land cover, satellite-image analysis, weather, ML, event engine, or prioritization exists yet.
- FIRMS source fields can vary by product/version; the pipeline validates the received CSV rather than assuming every optional field exists.
- NRT observations can be revised or replaced by later processing. The raw response and request metadata are retained for reproducibility.
- Map points are thermal anomalies only. They are not labelled as industrial fires or confirmed events.

## Next phase

Phase 2 will ingest and normalize OSM industrial-facility features, with source provenance and spatial indexes. It will not classify observations yet; facility association belongs to Phase 3.

