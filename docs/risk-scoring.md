# Multi-Modal Satellite Verification & Risk Scoring Pipeline

## Overview

Phase 8 evaluates satellite thermal anomaly observations using a 4-factor Multi-Criteria Risk Scoring model ($0 - 100$) integrated with Sentinel-2 / Landsat-8 optical verification confidence proxies.

---

## Composite Multi-Criteria Risk Formula

$$\text{RiskScore} = 0.25 \times S_{\text{prox}} + 0.30 \times S_{\text{frp}} + 0.25 \times S_{\text{sens}} + 0.20 \times (S_{\text{opt}} \times 100)$$

### Sub-Component Score Definitions:

| Factor | Description | Weight | Range |
| :--- | :--- | :--- | :--- |
| $S_{\text{prox}}$ | Spatial Proximity Score | $25\%$ | $10 - 100$ ($100$ if $\le 100\,\text{m}$, $75$ if $\le 1000\,\text{m}$, $50$ if $\le 3000\,\text{m}$, $10$ unassociated) |
| $S_{\text{frp}}$ | FRP Anomaly Multiplier Score | $30\%$ | $0 - 100$ ($\min(100, 40 \times \text{multiplier})$ if abnormal) |
| $S_{\text{sens}}$ | Facility Operational Sensitivity | $25\%$ | $20 - 95$ (`refinery`: $95$, `chemical`: $90$, `power_plant`: $80$, `steel_works`: $75$, `industrial`: $50$) |
| $S_{\text{opt}}$ | Optical Verification Confidence | $20\%$ | $0.0 - 1.0$ (Sentinel-2 MSI / Landsat-8 OLI cloud-free optical verification proxy score) |

---

## Risk Tier Classification

| Risk Level | Score Range | Description |
| :--- | :--- | :--- |
| `CRITICAL_VERIFIED_RISK` | $> 85.0$ | High FRP anomaly combined with high optical verification confidence |
| `HIGH_RISK` | $61.0 - 85.0$ | Significant thermal output near sensitive industrial infrastructure |
| `MEDIUM_RISK` | $31.0 - 60.0$ | Moderate thermal anomaly requiring routine monitoring |
| `LOW_RISK` | $0.0 - 30.0$ | Background heat or unassociated low FRP detection |

---

## PostGIS Schema: `verification_risk_scores`

```sql
CREATE TABLE verification_risk_scores (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER UNIQUE NOT NULL REFERENCES thermal_observations(id) ON DELETE CASCADE,
    facility_id INTEGER REFERENCES industrial_facilities(id) ON DELETE CASCADE,
    composite_risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    spatial_proximity_score DOUBLE PRECISION DEFAULT 10.0 NOT NULL,
    frp_multiplier_score DOUBLE PRECISION DEFAULT 30.0 NOT NULL,
    facility_sensitivity_score DOUBLE PRECISION DEFAULT 20.0 NOT NULL,
    optical_verification_confidence DOUBLE PRECISION DEFAULT 0.50 NOT NULL,
    verification_source VARCHAR(100) DEFAULT 'Sentinel-2 MSI / Landsat-8 OLI Optical Proxy' NOT NULL,
    risk_breakdown_json TEXT,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_risk_level_score ON verification_risk_scores (risk_level, composite_risk_score);
```
