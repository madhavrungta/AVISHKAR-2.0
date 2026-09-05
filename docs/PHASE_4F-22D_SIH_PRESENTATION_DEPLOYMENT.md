# PHASE 4F-22D — SIH PRESENTATION DEMO DEPLOYMENT SPECIFICATION

**PROJECT**: AVISHKAR 2.0 (SIH 26162 — NTRO)  
**TITLE**: AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources  
**DEPLOYMENT STAGE**: SIH Presentation / Controlled Demonstration Deployment  
**TARGET PLATFORM**: Railway  
**MANDATORY FRONTEND**: `frontend-v2/`  

---

## 1. MANDATORY OPERATIONAL CONSTRAINTS

* `PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`
* `ML_CLASSIFIER_SHADOW_ONLY = TRUE` (Model: `4F.13_GB_V1`, pure Python gradient boosting classifier)
* `RISK_SERVICE_AUTHORITATIVE = TRUE` (Authoritative scoring invariant: $S = 0.25 S_{\text{prox}} + 0.30 S_{\text{frp}} + 0.25 S_{\text{sens}} + 0.20 S_{\text{opt}}$)
* `PHASE_4F-22_TRIAL_STATUS = IN_PROGRESS` (Strictly isolated demo environment & demo database)

---

## 2. REPOSITORY AUDIT & ARCHITECTURE

### A. Frontend Entry Point & Build
* **Path**: `frontend-v2/` (Vite + React 18 + TypeScript + TailwindCSS + Leaflet + Framer Motion)
* **Build Verification**: `npm run build` $\rightarrow$ **PASS (0 TypeScript errors)**.
* **API Routing**: Uses centralized `getApiUrl()` from `src/services/api.ts` which respects `VITE_API_BASE_URL` for Railway while proxying `/api/*` for local and containerized environments.
* **Map Engine**: Leaflet with dark Stadia Alidade tiles, coordinate tracker reticle, dynamic camera fly-to, and ResizeObserver container invalidation.

### B. Backend Entry Point & Engine
* **Path**: `backend/` (FastAPI + Uvicorn + SQLAlchemy + PostGIS / SQLite)
* **Entry Point**: `app.main:app` binding to `0.0.0.0` and dynamic `$PORT`.
* **CORS**: Configured with strict origin list and regex matching `https://.*\.railway\.app` / `https://.*\.up\.railway\.app`.
* **Health Check**: `GET /health` returns `200 OK` with database status, FIRMS key masking (no raw secret leakage), and ML shadow status.

### C. Database & Seeding Strategy
* **Schema**: Supports PostgreSQL + PostGIS (via `CREATE EXTENSION IF NOT EXISTS postgis`) with SQLite fallback.
* **Seed Data**: Pre-loaded with authentic Indian industrial complexes (Reliance Jamnagar, Trombay Power, Tata Steel Jamshedpur, Vizag Petrochemical, Mangalore MRPL, Mundra UMPP), forest reserves (Western Ghats, Simlipal), and agricultural zones (Punjab, Haryana).
* **Isolation**: Demo database is completely isolated from the ongoing Phase 4F-22 14-day live trial database.

### D. Model Artifact Integrity
* **Approved Version**: `4F.13_GB_V1`
* **Artifact Path**: `backend/ml_artifacts/phase_4f11a/model_pipeline_weights.json`
* **Verified SHA-256 Checksum**: `f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810` (**PASS**).

---

## 3. RAILWAY SERVICE DEPLOYMENT GUIDE

Railway project configuration:

```
RAILWAY PROJECT: AVISHKAR-2.0
├── SERVICE 1: backend (FastAPI Web Service)
│   ├── Source: /backend (Dockerfile or GitHub Repo)
│   ├── Build: Dockerfile
│   ├── Port: $PORT (8000)
│   ├── Environment Variables:
│   │   ├── FIRMS_MAP_KEY=fd1aa1c498b6ba1e4ed04024872d1b60
│   │   ├── DATABASE_URL=${{Postgres.DATABASE_URL}}
│   │   ├── CORS_ORIGINS=https://${{frontend-v2.RAILWAY_PUBLIC_DOMAIN}}
│   │   └── ENVIRONMENT=staging_demo
│   └── Healthcheck: /health
│
├── SERVICE 2: frontend-v2 (React Web Service / Static Site)
│   ├── Source: /frontend-v2 (Dockerfile or Nixpacks)
│   ├── Build: npm run build
│   └── Environment Variables:
│       └── VITE_API_BASE_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}
│
└── SERVICE 3: Postgres (Managed Database)
    └── Extension: PostGIS
```

---

## 4. SCIENTIFIC & EVIDENCE DISCLAIMERS

1. **NASA FIRMS Telemetry**: Thermal anomaly points represent active radiative heat emissions, not structural damage or confirmed fire incidents.
2. **AI Investigation Agent**: Uses grounded database tools with zero hallucination. Unavailable sources (optical high-res passes, localized weather) are explicitly labeled as `Unavailable`.
3. **ML Shadow Mode**: Operates in non-authoritative shadow advisory mode. Risk alerts are governed strictly by the 4-Factor multi-criteria RiskService.

---

## 5. GATE EVALUATION

* **Status**: **`GATE A — PRESENTATION DEPLOYMENT READY`**
* **Production Authorization**: `PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`
