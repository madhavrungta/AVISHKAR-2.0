# Historical Facility Behavior Engine

## Overview

Phase 5 establishes the historical thermal behavior baseline per industrial facility, tracking observation frequency, $P_{95}$ / $P_{99}$ FRP percentiles, day/night orbit pass ratios, and persistence tiers.

---

## Facility Activity Persistence Tiers

| Activity Tier | Observation Count Criteria | Description |
| :--- | :--- | :--- |
| `HIGHLY_PERSISTENT` | $\ge 15$ detections | Facility exhibits continuous background thermal output (flares, kilns, furnaces) |
| `MODERATELY_ACTIVE` | $5 - 14$ detections | Facility exhibits regular periodic thermal emissions |
| `SPORADIC` | $1 - 4$ detections | Facility exhibits occasional thermal emissions |
| `NO_HISTORICAL_ANOMALIES` | $0$ detections | Facility has no historical satellite thermal detections |

---

## PostGIS Schema: `facility_historical_behaviors`

```sql
CREATE TABLE facility_historical_behaviors (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER UNIQUE NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
    total_observations INTEGER DEFAULT 0 NOT NULL,
    observation_days INTEGER DEFAULT 0 NOT NULL,
    min_frp DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    max_frp DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    mean_frp DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    median_frp DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    p95_frp DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    p99_frp DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    day_count INTEGER DEFAULT 0 NOT NULL,
    night_count INTEGER DEFAULT 0 NOT NULL,
    day_night_ratio DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    activity_tier VARCHAR(50) DEFAULT 'NO_HISTORICAL_ANOMALIES' NOT NULL,
    first_observed TIMESTAMP WITH TIME ZONE,
    last_observed TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_history_tier_p95 ON facility_historical_behaviors (activity_tier, p95_frp);
```
