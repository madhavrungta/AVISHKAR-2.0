# Abnormal Thermal Event Detection Engine

## Overview

Phase 7 evaluates associated satellite thermal anomaly observations against facility normal baselines ($P_{95}$ FRP upper bound) to detect abnormal thermal output candidates, compute intensity multiplier ratios ($\text{Ratio} = \frac{FRP}{P_{95}}$), and enforce strict NTRO scientific caution labeling.

---

## Anomaly Severity Classification Tiers

| Severity Code | FRP Multiplier Ratio Criteria | Operational Description |
| :--- | :--- | :--- |
| `MODERATE_ABNORMAL_SPIKE` | $1.0 < \text{Ratio} \le 1.5$ | Thermal output moderately exceeds upper baseline threshold |
| `HIGH_ABNORMAL_SPIKE` | $1.5 < \text{Ratio} \le 2.5$ | Thermal output significantly exceeds normal flare/kiln operations |
| `CRITICAL_INDUSTRIAL_ANOMALY` | $\text{Ratio} > 2.5$ | Severe thermal output spike requiring immediate investigation |

---

## Mandatory NTRO Scientific Label

> `"Abnormal Thermal Output Candidate - Requires Multi-Pass / High-Res Optical Verification"`

> **Strict Warning Mandate**: *"Persistent Industrial Heat != Confirmed Fire. FRP > P95 != Confirmed Industrial Disaster."*

---

## PostGIS Schema: `abnormal_thermal_events`

```sql
CREATE TABLE abnormal_thermal_events (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER UNIQUE NOT NULL REFERENCES thermal_observations(id) ON DELETE CASCADE,
    facility_id INTEGER NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
    observed_frp DOUBLE PRECISION NOT NULL,
    baseline_p95_frp DOUBLE PRECISION NOT NULL,
    frp_multiplier_ratio DOUBLE PRECISION NOT NULL,
    anomaly_severity VARCHAR(50) NOT NULL,
    scientific_caution_label VARCHAR(255) DEFAULT 'Abnormal Thermal Output Candidate - Requires Multi-Pass / High-Res Optical Verification' NOT NULL,
    explanation_reason TEXT NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_anomaly_sev_ratio ON abnormal_thermal_events (anomaly_severity, frp_multiplier_ratio);
```
