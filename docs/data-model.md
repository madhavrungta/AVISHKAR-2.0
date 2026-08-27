# Phase 1 data model

## `thermal_observations`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `observation_key` | text, unique | Deterministic identity for source/time/location/satellite deduplication |
| `observation_timestamp` | timestamptz | UTC timestamp reconstructed from FIRMS acquisition fields |
| `latitude`, `longitude` | float | WGS84 coordinates retained for convenient API use |
| `geometry` | PostGIS geometry(Point, 4326) | Spatially indexed point; longitude then latitude |
| `frp`, `bright_ti4`, `bright_ti5`, `scan`, `track` | float nullable | Observed fields only; never invented |
| `confidence`, `satellite`, `instrument`, `daynight` | text nullable | FIRMS fields may differ by source |
| `source` | text | FIRMS product requested |
| `ingestion_batch_id` | UUID | Links stored records to raw archive metadata |
| `ingestion_timestamp`, `created_at` | timestamptz | System provenance |
| `original_fields` | JSONB | Complete original CSV row preserving unfamiliar future fields |

PostGIS creates a GiST index on `geometry`; indexes also support time, source, and batch queries. Future facility, classification, and event tables are deliberately deferred.

