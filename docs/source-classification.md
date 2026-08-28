# Industrial vs Natural/Other Source Classification Engine

## Overview

Phase 4 implements the candidate source classifier to evaluate thermal anomaly observations into operational category candidates.

---

## Candidate Source Classes

| Class Code | Description | Decision Criteria |
| :--- | :--- | :--- |
| `INDUSTRIAL_CANDIDATE` | Heat source associated with industrial facility | Distance $\le 500\,\text{m}$ or $\le 1500\,\text{m}$ near refinery/power/steel/chemical facility |
| `NATURAL_FOREST_CANDIDATE` | Forest or wildland fire candidate | Distance $> 3000\,\text{m}$ from industrial footprint and $FRP \ge 20\,\text{MW}$ |
| `AGRICULTURAL_CANDIDATE` | Open crop burning candidate | Distance $> 2000\,\text{m}$ from industrial footprint, daytime pass, and $FRP < 20\,\text{MW}$ |
| `OTHER_UNKNOWN` | Insufficient spatial/temporal signature | General unassociated thermal point requiring multi-pass baselining |

---

## PostGIS Schema: `thermal_classifications`

```sql
CREATE TABLE thermal_classifications (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER UNIQUE NOT NULL REFERENCES thermal_observations(id) ON DELETE CASCADE,
    predicted_class VARCHAR(50) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    classification_reason TEXT NOT NULL,
    feature_vector_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_class_score ON thermal_classifications (predicted_class, confidence_score);
```
