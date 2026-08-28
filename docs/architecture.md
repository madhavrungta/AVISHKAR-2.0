# Phase 8 System Architecture: Multi-Modal Verification & Risk Scoring Pipeline

## SIH Problem Statement ID: 26162 (NTRO)
**Title:** AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources Using NASA FIRMS, OSM & Satellite Data

---

## Architectural Data Flow (Phase 1 to Phase 8)

```
 ┌─────────────────────────┐             ┌─────────────────────────┐
 │ NASA FIRMS Official API │             │ OpenStreetMap Overpass  │
 └────────────┬────────────┘             └────────────┬────────────┘
              │                                       │
              ▼                                       ▼
 ┌─────────────────────────┐             ┌─────────────────────────┐
 │ PostGIS Table:          │             │ PostGIS Table:          │
 │ `thermal_observations`  │             │ `industrial_facilities` │
 └────────────┬────────────┘             └────────────┬────────────┘
              │                                       │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │  Association Service    │
                     └────────────┬────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Source Engine│          │History Engine│          │Baseline Engine│
└───────┬──────┘          └───────┬──────┘          └───────┬──────┘
        │                         │                         │
        │                         └───────────┬─────────────┘
        │                                     │
        ▼                                     ▼
┌──────────────┐                      ┌──────────────┐
│Classifications│                      │Anomaly Engine│ (FRP > P95)
└───────┬──────┘                      └───────┬──────┘
        │                                     │
        └───────────────────┬─────────────────┘
                            │
                            ▼
               ┌─────────────────────────┐
               │ Multi-Modal Risk Engine │ (Sentinel-2 / Landsat-8 Optical Proxy)
               └────────────┬────────────┘
                            │
                            ▼
               ┌─────────────────────────┐
               │ PostGIS Table:          │
               │ `verification_risk_     │
               │  scores`                │
               └────────────┬────────────┘
                            │
                            ▼
               ┌─────────────────────────┐
               │ React Leaflet GIS Map   │
               │  - Composite Risk Gauge │
               │  - Risk Tier Badges     │
               │  - Optical Confidence % │
               └─────────────────────────┘
```
