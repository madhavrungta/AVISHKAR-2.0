# OpenStreetMap (OSM) Industrial Facility Integration

## Overview

Phase 2 introduces OpenStreetMap industrial land-use boundaries and infrastructure nodes to enable downstream spatial association between satellite thermal anomalies and industrial sites.

---

## Overpass API Query Filter Tags

The system queries the Overpass API (`https://overpass-api.de/api/interpreter`) using the following tags:

- `landuse=industrial`
- `industrial=*`
- `power=plant`
- `man_made=works`
- `man_made=petroleum_refinery`
- `building=industrial`

---

## Industrial Classification Rules

| Tag Pattern | Standardized Category |
| :--- | :--- |
| `man_made=petroleum_refinery` or `industrial=refinery/oil` | `refinery` |
| `power=plant` or `industrial=power` | `power_plant` |
| `industrial=steel` or `industrial=metal` or `man_made=works` | `steel_works` |
| `industrial=chemical` or `industrial=pharmaceutical` | `chemical` |
| Other industrial tags | `industrial` |

---

## PostGIS Schema: `industrial_facilities`

```sql
CREATE TABLE industrial_facilities (
    id SERIAL PRIMARY KEY,
    osm_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    facility_type VARCHAR(100) NOT NULL,
    operator VARCHAR(255),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Geometry, 4326),
    area_sqm DOUBLE PRECISION DEFAULT 0.0,
    raw_tags TEXT,
    ingestion_batch_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_facility_lat_lon ON industrial_facilities (latitude, longitude);
CREATE INDEX idx_facility_type_area ON industrial_facilities (facility_type, area_sqm);
CREATE INDEX idx_facility_geom ON industrial_facilities USING GIST (geometry);
```
