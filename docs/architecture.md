# Phase 1 architecture

## Scope

This phase creates the trusted data foundation for SIH 26162. A separate later layer will use OSM facilities, land cover, imagery, weather, and ML. None of those are present here.

## Components

| Component | Responsibility |
| --- | --- |
| `app/config.py` | Validated environment configuration; no credentials in code |
| `FirmsService` | Official FIRMS Area API retrieval, retries, CSV parsing, normalization, and archive orchestration |
| `validation.py` | Explicit coordinate, timestamp, numeric, missing-value, and duplicate reporting |
| `raw_storage.py` | Immutable timestamped raw CSV + ingestion metadata persistence |
| `geospatial/observations.py` | EPSG:4326 GeoDataFrame conversion |
| `models/thermal_observation.py` | PostGIS `POINT` model and indexes |
| FastAPI routes | Inspection, prototype ingestion trigger, and summary endpoints |
| MapLibre frontend | Read-only visual validation of stored thermal anomaly points |

## Data flow

1. An operator supplies a source, an area (`world` or `west,south,east,north`), and 1–5 days.
2. The backend builds the documented FIRMS Area CSV URL without logging its key.
3. The exact response CSV is archived with an immutable batch ID and UTC timestamp.
4. The received headers are checked before processing. Required source fields must be present; optional FIRMS columns remain optional.
5. Records receive a UTC observation timestamp from `acq_date` + `acq_time`, ingestion timestamp, source, batch ID, deterministic observation key, and an `original_fields` JSON object.
6. Invalid and duplicate records are counted and explained. Only valid, non-duplicate records reach PostGIS.
7. The database creates `geometry(Point, 4326)` and spatial/GiST indexes. The public map consumes only normalized backend responses.

## Boundary for future phases

The `NormalizedObservation` schema and GeoDataFrame helper are intentionally independent of FIRMS retrieval. OSM, land-cover, and satellite-imagery adapters can add contextual evidence later without rewriting Phase 1 ingestion.

## Operational safety

- The app starts if PostGIS is unavailable, but database-backed endpoints return `503` and `/health` reports the state.
- A missing `FIRMS_MAP_KEY` produces a specific actionable configuration error.
- Raw files are ignored from version control and never overwritten.
- An ingestion API call should be placed behind authentication and rate limits for production.

