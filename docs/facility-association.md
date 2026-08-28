# Thermal Anomaly $\rightarrow$ Facility Association Engine

## Overview

Phase 3 introduces spatial proximity matching and geodesic distance analysis to connect NASA FIRMS thermal anomaly observations with OpenStreetMap industrial facilities.

---

## Association Classification Tiers

| Association Type | Distance Threshold | Interpretation |
| :--- | :--- | :--- |
| `DIRECT_MATCH` | $\le 100\,\text{m}$ | Thermal observation is inside or directly adjacent to facility boundary |
| `PROXIMATE_MATCH` | $100\,\text{m} - 1000\,\text{m}$ | Thermal observation is in immediate facility operational vicinity |
| `VICINITY_MATCH` | $1000\,\text{m} - 3000\,\text{m}$ | Thermal observation is in regional industrial zone |
| `UNASSOCIATED` | $> 3000\,\text{m}$ | Isolated thermal observation (likely natural/agricultural/unknown) |

---

## PostGIS Schema: `thermal_facility_associations`

```sql
CREATE TABLE thermal_facility_associations (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER NOT NULL REFERENCES thermal_observations(id) ON DELETE CASCADE,
    facility_id INTEGER NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
    distance_meters DOUBLE PRECISION NOT NULL,
    association_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT idx_assoc_obs_fac UNIQUE (observation_id, facility_id)
);

CREATE INDEX idx_assoc_type_dist ON thermal_facility_associations (association_type, distance_meters);
```

---

## Scientific Distinction Rule

> [!IMPORTANT]
> **Facility Association $\ne$ Confirmed Industrial Fire**
> Spatial association with an industrial facility establishes that a thermal anomaly occurred near industrial infrastructure. At refineries, power plants, and steel mills, high thermal radiative power is routine. Historical baselining (Phase 4 & 5) is required to determine whether current thermal intensity exceeds normal facility baseline behavior.
