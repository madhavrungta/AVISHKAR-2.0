# Facility Normal Baseline Engine

## Overview

Phase 6 establishes the normal operating thermal envelope ($P_{50}$ median, $P_{95}$ upper bound, $P_{99}$ peak bound) for every monitored industrial facility.

---

## Category-Level Default Baselines

For new facilities or facilities with $< 3$ historical observations, the baseline engine initializes preliminary default upper bounds based on facility type:

| Facility Category | $P_{50}$ Median FRP | $P_{95}$ Upper Operating Bound | $P_{99}$ Peak Bound |
| :--- | :--- | :--- | :--- |
| `refinery` | $25.0\,\text{MW}$ | $55.0\,\text{MW}$ | $85.0\,\text{MW}$ |
| `power_plant` | $35.0\,\text{MW}$ | $75.0\,\text{MW}$ | $110.0\,\text{MW}$ |
| `steel_works` | $30.0\,\text{MW}$ | $65.0\,\text{MW}$ | $95.0\,\text{MW}$ |
| `chemical` | $15.0\,\text{MW}$ | $35.0\,\text{MW}$ | $50.0\,\text{MW}$ |
| `industrial` | $10.0\,\text{MW}$ | $25.0\,\text{MW}$ | $40.0\,\text{MW}$ |

---

## PostGIS Schema: `facility_baselines`

```sql
CREATE TABLE facility_baselines (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER UNIQUE NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
    baseline_frp_p50 DOUBLE PRECISION DEFAULT 15.0 NOT NULL,
    baseline_frp_p95 DOUBLE PRECISION DEFAULT 45.0 NOT NULL,
    baseline_frp_p99 DOUBLE PRECISION DEFAULT 75.0 NOT NULL,
    monthly_frequency DOUBLE PRECISION DEFAULT 1.0 NOT NULL,
    day_night_preference VARCHAR(50) DEFAULT 'BALANCED' NOT NULL,
    baseline_status VARCHAR(50) DEFAULT 'PRELIMINARY_DEFAULT' NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_baseline_status_p95 ON facility_baselines (baseline_status, baseline_frp_p95);
```
