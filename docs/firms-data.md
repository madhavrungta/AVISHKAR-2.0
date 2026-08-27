# NASA FIRMS data use in Phase 1

## Official API

The ingestion service uses the official FIRMS Area API CSV route:

```text
https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA}/{DAY_RANGE}[/{DATE}]
```

- `AREA` is either `world` or a comma-separated `west,south,east,north` bounding box.
- `DAY_RANGE` is 1 through 5.
- When `DATE` is absent, FIRMS returns the most recent observations; when present (`YYYY-MM-DD`), the window starts on that date.
- Phase 1 accepts `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, and `VIIRS_NOAA21_NRT`.

Consult the current [FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/) and [Area API documentation](https://firms.modaps.eosdis.nasa.gov/api/area/) before changing the service. API behavior and products can change.

## Terminology

FIRMS supplies satellite active-fire / thermal-anomaly detections. One detection does **not** independently establish the cause or nature of heat at a location. Phase 1 therefore calls every map point a **NASA FIRMS thermal anomaly**. It makes no assertion that the point is a confirmed fire, industrial source, leak, or emergency.

## Received fields and preservation

FIRMS products commonly include `latitude`, `longitude`, `bright_ti4`, `bright_ti5`, `scan`, `track`, `acq_date`, `acq_time`, `satellite`, `instrument`, `confidence`, `version`, `frp`, and `daynight`. Some products or future versions may omit or add fields. The parser requires only coordinates and acquisition date/time; it records all raw headers and preserves every original row field in `original_fields`.

Derived metadata is never substituted for original FIRMS fields:

- `observation_timestamp` — normalized UTC timestamp from acquisition date/time
- `ingestion_timestamp` — UTC time this system processed the batch
- `source` — requested FIRMS source
- `ingestion_batch_id` — UUID for the archive and database batch

## Quality policy

- Out-of-range or non-numeric coordinates and malformed timestamps are rejected.
- Negative or non-numeric supplied physical numeric values are rejected.
- Optional absent values are counted, not fabricated.
- Exact source/time/location duplicates are reported and not inserted.
- The raw source response and validation metadata provide an audit trail for all outcomes.

