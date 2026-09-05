# PHASE 4F-20 — CONTROLLED OPERATIONAL VERIFICATION & PRODUCTION READINESS GATE REVIEW

**PROJECT:** AVISHKAR 2.0 — SIH 26162  
**ORGANIZATION:** NTRO / SIH 2024  
**TITLE:** AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources  
**DATE:** 2026-09-04  
**STATUS:** COMPLETE  
**GATE DECISION:** `GATE B — CONDITIONAL PRODUCTION READINESS`  
**AUTHORIZATION:** `PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`  
**MANDATORY STATEMENT:** *Phase 4F-20 does not authorize production deployment.*

---

## 1. Executive Summary

Phase 4F-20 represents the formal, controlled **Production Readiness Gate Review** for the AVISHKAR 2.0 system. Over previous phases (4F-13 through 4F-19), the multi-modal thermal classification engine (`PurePythonGradientBoostingClassifier`, version `4F.13_GB_V1`) has been subjected to rigorous ground-truth independence audits, spatial data leakage tests, multi-region shadow pilots across 4,121 ambient FIRMS observations, perturbation sensitivity analyses, human verification workflow scaffolding, and staging environment verification.

The purpose of Phase 4F-20 is not to retrain models, alter weights, optimize operational thresholds, or fabricate missing evidence, but rather to evaluate whether the system currently possesses sufficient empirical evidence, engineering controls, operational safeguards, and governance to be considered for future production deployment.

Based on a multi-dimensional assessment:
- **Technical & Architecture Readiness:** PASS (Sub-millisecond inference, strict shadow isolation, 100% RiskService invariance, zero secret leakage).
- **Model Integrity & Rollback:** PASS (Pinned SHA-256 fingerprint verified: `f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810`).
- **Controlled Benchmark Accuracy:** PASS (100% macro F1 across 750 curated records over 250 physically isolated clusters).
- **Human Verification & Real-World Calibration:** PARTIAL / CONDITIONAL (Phase 4F-17 review set remains 75% `PENDING_REVIEW` awaiting expert panel adjudication; live continuous satellite ingestion remains unvalidated under production stream conditions).

Therefore, Phase 4F-20 issues a final gate determination of **`GATE B — CONDITIONAL PRODUCTION READINESS`** with **`PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`**.

---

## 2. Objective

The primary objective of Phase 4F-20 is to answer the fundamental question:
> *"Is there sufficient evidence and operational control to consider production deployment, and what conditions remain unresolved?"*

Phase 4F-20 does not automatically deploy the system or activate autonomous ML. It ensures strict scientific reporting, establishes the boundary between controlled benchmark performance and ambient operational behavior, maps architectural failure modes, and outlines the blocking prerequisites for future production consideration.

---

## 3. Scope

### In Scope:
1. End-to-end repository audit covering backend, frontend, database, ingestion pipelines, feature extractors, shadow inference, RiskService, monitoring telemetry, and staging scripts.
2. Cryptographic and structural verification of the approved model artifact (`4F.13_GB_V1`).
3. Synthesis of evidence across Phases 4F-13 through 4F-19 with strict evidence hierarchy preservation.
4. Domain-specific readiness audits for Industrial Fire and Mining classifications.
5. Invariance verification for the authoritative `RiskService`.
6. Construction of a 15-point Failure Modes and Recovery Matrix.
7. Categorical 14-dimension Production Authorization Matrix.
8. Identification and documentation of critical deployment blockers and unresolved limitations.

### Out of Scope:
- Model retraining, re-weighting, or hyperparameter adjustment.
- Post-hoc threshold tuning or operational rule modification.
- Live modification of `RiskService` logic.
- Fabrication or simulation of live satellite streams or human reviewer inputs.
- Activation of production ML autonomous mode.

---

## 4. Current Checkpoint

A complete retrospective of completed validation phases establishes the following baseline:

| Phase | Description | Key Findings & Evidence | Status |
|---|---|---|---|
| **4F-13** | Gradient Boosting Classifier Implementation | 100 stages, 5 classes, 18 features. 100% accuracy on curated 750-record dataset. | `COMPLETED` |
| **4F-14** | Ground-Truth Independence & Leakage Audit | Spatial cluster disjointness confirmed (200 train / 50 test clusters). 0% data leakage. | `PASS` |
| **4F-15** | Controlled Multi-Region Shadow Pilot | 4,121 ambient FIRMS observations evaluated across 6 macro-regions. 98.69% spatial stability. | `CONDITIONAL ADVANCE` |
| **4F-16** | Calibration, Threshold & Robustness Pilot | Chance-adjusted agreement $\kappa = 0.5482$; 99.42% perturbation invariance; confidence reconciled (0.7924 GT vs 0.4431 ambient). | `GATE A — ROBUST` |
| **4F-17** | Controlled Human Verification Workflow | 100 candidate sample: 25 Level-1 catalog verified, 75 pending expert panel review. | `GATE B — CONDITIONAL ADVANCE` |
| **4F-18** | Operational Shadow Logging & Monitoring | Zero-impact telemetry logging across 4,121 events; 6.05 ms shadow latency; 100% RiskService invariance. | `GATE A — STABLE SHADOW` |
| **4F-19** | Controlled Staging Deployment | 5 API endpoints verified; 0.235 ms model inference; 0% errors across 5 concurrent threads. | `GATE A — STAGING READY` |

---

## 5. Production Readiness Principle

Production readiness is evaluated across 10 distinct, un-collapsed dimensions:
1. **Technical Readiness:** System stability, API integrity, sub-millisecond execution.
2. **Model Readiness:** Fixed architecture, verified weights, immutable schema.
3. **Data Readiness:** Idempotent ingestion, bounding-box filtering, schema validation.
4. **Operational Readiness:** Non-blocking telemetry, staging health verification.
5. **Security Readiness:** Zero hardcoded credentials, isolated environment configs, sanitized error payloads.
6. **Monitoring Readiness:** Comprehensive tracking of latency, drift, candidate classifications, and failures.
7. **Human Oversight Readiness:** Scaffolding for independent expert review and adjudication.
8. **Governance Readiness:** Authoritative priority reserved strictly for deterministic risk rules.
9. **Recovery/Rollback Readiness:** Pinned artifact SHA-256 hashes, graceful fallback modes.
10. **Evidence Readiness:** Explicit separation of controlled benchmark metrics from real-world telemetry.

---

## 6. Model Readiness

The deployed model pipeline is pinned and verified:
- **Model Version:** `4F.13_GB_V1`
- **Architecture:** `PurePythonGradientBoostingClassifier`
- **Boosting Stages:** 100
- **Number of Classes:** 5 (`industrial_fire`, `refinery_flare`, `biomass_agricultural`, `mining_activity`, `urban_static_other`)
- **Feature Vector:** 18 continuous and spatial features (`FEATURE_NAMES_18`)
- **Max Depth:** 4
- **Learning Rate:** 0.05
- **Artifact Path:** `backend/ml_artifacts/phase_4f11a/model_pipeline_weights.json`
- **Cryptographic SHA-256:** `f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810`
- **Model Readiness Status:** `PASS` (Model weights and schema are 100% verified and unchanged).

---

## 7. Model Performance Evidence

| Evidence Stream | Source / Dataset | Metrics & Observed Behavior | Scientific Interpretation |
|---|---|---|---|
| **Controlled Ground-Truth Benchmark** | 750 curated events (250 physical clusters) | Accuracy: 1.0000<br>Macro F1: 1.0000 | Demonstrates complete separation on curated, high-confidence benchmark exemplars. Does not establish unverified ambient accuracy. |
| **Cluster Disjointness Audit** | 200 train / 50 test cluster spatial split | Accuracy: 1.0000<br>Leakage: 0.00% | Proves zero spatial coordinates or facility signatures leaked across train/test partitions. |
| **Multi-Region Shadow Ingestion** | 4,121 ambient FIRMS observations (6 regions) | Spatial stability: 98.69%<br>Top-1 Shift: $< 1.5\%$ | Model exhibits consistent regional class distribution without extreme geographic volatility. |
| **Perturbation Robustness** | $\pm 5\%$ feature jitter across 4,121 events | Invariance: 99.42% | Model predictions are stable against minor measurement noise in FRP and brightness. |
| **Human Expert Verification** | 100 candidate stratified sample | Level-1 Verified: 25<br>Pending Review: 75 | Infrastructure validated; comprehensive operational verification awaits panel review. |
| **Operational Monitoring** | 4,121 real-time telemetry events | Shadow Latency: 6.05 ms<br>Risk Invariance: 100% | Zero interference with production data structures or operational prioritization. |

---

## 8. Accuracy Claim Audit

A rigorous audit of previous accuracy statements establishes:
- **100% Accuracy Claim:** Valid **only** when referring to the curated 750-record ground-truth benchmark dataset across 250 isolated clusters.
- **Ambient Operational Telemetry:** The model predicts plausible distributions across ambient FIRMS observations, but true ambient accuracy **cannot be quantified** without 100% ground-truth labels for diffuse background events.
- **Reporting Standard:** All documentation must refer to Phase 4F-13 performance as *"Controlled Evaluation Performance"* and never as *"Real-World Ambient Accuracy"*.

---

## 9. Human Verification Readiness

The human verification workflow established in Phase 4F-17 was evaluated:
- **Candidate Selection Logic:** Stratified sampling across high-confidence predictions, industrial candidates, and heuristic disagreements.
- **Verification Packet Status:**
  - Total Samples: 100
  - Level-1 Catalog-Linked Verifications: 25 (Refinery flaring and heavy industrial clusters verified via OSM/ISRO industrial boundaries).
  - Pending Expert Adjudication: 75 (`PENDING_REVIEW`).
- **Human Verification Status:** `PARTIAL (Awaiting Expert Panel Adjudication)`.

---

## 10. Industrial Fire Readiness

- **Primary SIH Problem Domain:** AI-based detection and classification of industrial fires.
- **Observed Candidates:** 7 candidate detections identified during operational shadow monitoring.
- **High-Confidence Candidates ($\ge 0.70$):** 1 candidate identified with high thermal intensity and close proximity to known chemical processing assets.
- **Independently Verified Cases:** 1 case verified via Level-1 industrial database linkage.
- **Status:** `PARTIAL_EVIDENCE` (Candidates are logically detected based on spatial and thermal signatures; full operational deployment requires ground validation procedures).

---

## 11. Mining Readiness

- **Historical Benchmark Records:** 150 curated coal/mineral mining records in ground-truth dataset.
- **Ambient Ingestion Observations:**
  - Ambient Top-1 Predictions: 0
  - Ambient Top-2 Predictions: 3 (prob $\le 0.2014$)
  - Independently Verified Ambient Cases: 0
- **Mandatory Statement:** *No Mining top-1 prediction was observed during operational monitoring.*
- **Interpretation:** Mining thermal sources (e.g., overburden fires, smelting) were either absent in the 4,121-event ambient window or did not exceed the classification threshold.

---

## 12. Live Data Readiness

- **FIRMS Configuration:** Schema and ingestion logic are configuration-verified and tested against standard NASA FIRMS CSV structures.
- **Validation Modality:** Multi-region shadow and staging tests utilized **Historical Replay** streams from validated FIRMS archives.
- **Live External Connectivity Validation:** `NOT_ESTABLISHED`. A continuous live operational satellite poll against real-time NASA FIRMS servers under live network constraints has not yet been executed in production.

---

## 13. Data Pipeline Readiness

The end-to-end data pipeline was verified for reliability:
$$\text{FIRMS CSV} \longrightarrow \text{Validation/Pydantic} \longrightarrow \text{PostGIS Storage} \longrightarrow \text{Feature Extraction} \longrightarrow \text{ML Shadow Inference} \longrightarrow \text{Monitoring Telemetry} \longrightarrow \text{API} \longrightarrow \text{Frontend}$$

- **Duplicate Handling:** Idempotent hash and acquisition timestamp checks prevent duplicate observation insertion.
- **Malformed Input Safety:** Invalid coordinates, negative FRP, or corrupt timestamps are rejected cleanly without crashing the pipeline.
- **Fallback Hierarchy:** Staged temporal fallback ($24\text{h} \to 3\text{d} \to 5\text{d}$) ensures data continuity during sparse satellite passes.

---

## 14. RiskService Isolation

Verification of authoritative risk scoring isolation:
- **RiskService Authority:** `AUTHORITATIVE` (Exclusively computes composite risk $S = 0.25 S_{\text{prox}} + 0.30 S_{\text{frp}} + 0.25 S_{\text{sens}} + 0.20 S_{\text{opt}}$).
- **ML Shadow Output:** `NON-AUTHORITATIVE` (Predictions are stored in shadow logs and never modify priority tiers or severity).
- **Invariance Test Result:** `PASS` (100% identical risk scores before and after ML execution).

---

## 15. Monitoring Readiness

The Phase 4F-18 monitoring subsystem was audited:
- **Telemetry Coverage:** Real-time logging of prediction probabilities, class distributions, regional breakdowns, feature drifts, confidence shifts, and inference latencies.
- **Data Quality Invariance:** 0 malformed records allowed; non-blocking background persistence verified.
- **Status:** `READY` for operational observability.

---

## 16. Drift Readiness

- **Telemetry Tracking:** Wasserstein distance and population stability indicators monitor shift in input features (FRP, brightness, distance to industrial assets).
- **Interpretation Constraint:** Feature drift is monitored as a data quality indicator, not as an automatic proxy for model accuracy degradation (which requires verified ground-truth labels).
- **Status:** `READY`.

---

## 17. Alert Governance

Strict operational separation of signals:
1. **`ENGINEERING_MONITORING_SIGNAL`:** Latency spikes, schema anomalies, or drift alerts (sent to system administrators).
2. **`ANALYST_REVIEW_SIGNAL`:** High-confidence ML shadow predictions and ML-vs-Heuristic disagreements (queued for human expert review).
3. **`AUTHORITATIVE_RISK_ALERT`:** Deterministic critical fire and emergency alerts generated solely by `RiskService` (dispatched to operations personnel).

---

## 18. Human Oversight

- **Workflow Review:** Mechanism exists to flag and queue observations for analyst review.
- **Gap Identified:** Formal escalation hierarchy, multi-expert consensus adjudication, and post-review override logging require operational organizational integration.
- **Status:** `HUMAN_OVERSIGHT_GAP` (Adjudication panel not yet integrated into live dispatch workflow).

---

## 19. Security Readiness

- **Credential Storage:** All database credentials, FIRMS API keys, and environment variables are externalized via `.env` and `app/config.py`.
- **Secrets Audit:** Zero secrets or private keys hardcoded in codebase or test fixtures.
- **Error Sanitization:** API routes catch unhandled exceptions and return sanitized JSON responses without exposing internal stack traces or environment variables.
- **Status:** `PASS`.

---

## 20. Database & Data Governance

- **Spatial Schema:** PostGIS spatial indexes on `thermal_observations` and `industrial_facilities` optimize proximity lookups.
- **Model Version Tracking:** Model version `4F.13_GB_V1` and schema version `1.0` are stamped on all telemetry records.
- **Backup & Recovery:** Enterprise backup and point-in-time recovery procedures have not been formally validated on a production database cluster.
- **Status:** `BACKUP_RECOVERY_NOT_VALIDATED`.

---

## 21. Rollback Readiness

- **Rollback Mechanism:** Manual deployment rollback via version-pinned weights JSON file and static configuration rollback.
- **Artifact Fingerprint:** Checksum verification on boot prevents startup with corrupted or modified model weights.
- **Automated Rollback:** Automated blue-green deployment rollback is not currently implemented.
- **Status:** `MANUAL_ROLLBACK_READY`.

---

## 22. Failure Modes & Recovery Matrix

| Failure Mode | Detection Mechanism | System Impact | Safe Behavior | Recovery Procedure | Readiness Status |
|---|---|---|---|---|---|
| **1. FIRMS API Unavailable** | HTTP Timeout / 503 | Ingestion delayed | Fallback to cached observations | Retry on scheduled cron interval | `PASS` |
| **2. Database Unavailable** | `SessionLocal` Connection Exception | Telemetry/API failure | Return HTTP 503, log critical error | Automatic reconnection pool | `PASS` |
| **3. Malformed FIRMS Data** | Pydantic validation error | Corrupt row ingestion | Drop invalid row, log schema error | Continue parsing valid rows | `PASS` |
| **4. Model Artifact Missing** | `FileNotFoundError` on startup | ML inference disabled | Bypass ML shadow, keep RiskService intact | Deploy pinned artifact | `PASS` |
| **5. Model Checksum Mismatch** | SHA-256 hash check fails | Unverified model weights | Abort model load, log critical security alert | Restore certified model artifact | `PASS` |
| **6. Feature Extraction Failure** | Missing column / math error | ML feature incomplete | Set status `FAILED`, fallback imputation | Log feature extraction exception | `PASS` |
| **7. ML Inference Exception** | Exception inside `predict_proba` | Shadow prediction lost | Catch exception, record telemetry error | Isolate shadow worker | `PASS` |
| **8. RiskService Failure** | Math/logic exception in scoring | Risk tier calculation error | Assign baseline conservative risk tier | Maintain deterministic rules | `PASS` |
| **9. Monitoring Failure** | Telemetry write exception | Observability lost | Non-blocking background worker drop | Resume logging on next event | `PASS` |
| **10. Frontend UI Failure** | Client JavaScript exception | Dashboard render error | React ErrorBoundary catches component crash | Reload client state | `PASS` |
| **11. External OSM Timeout** | Overpass API timeout | Enriched distance missing | Default to conservative max distance ($99\text{ km}$) | Non-blocking spatial fallback | `PASS` |
| **12. API Route Exception** | Unhandled route error | HTTP 500 error | Return sanitized error payload without secrets | Uvicorn worker process recycling | `PASS` |
| **13. Resource Exhaustion (OOM)** | Memory threshold breach | Latency spike / crash | Graceful process termination | Container auto-restart via orchestrator | `PASS` |
| **14. Stale Thermal Data** | `acq_date` > 48h from ingest | Inaccurate real-time picture | Tag telemetry as `HISTORICAL_REPLAY` | Await fresh satellite pass | `PASS` |
| **15. Unexpected Model Version** | Version tag mismatch | Incompatible schema | Block shadow inference, log mismatch | Pin approved model version | `PASS` |

---

## 23. Observability

- **Operational Logging:** Structured logging enabled across ingestion, feature extraction, ML shadow inference, and RiskService execution.
- **Traceability:** Every prediction record includes `observation_id`, `model_version`, `timestamp`, `probabilities`, and `execution_latency_ms`.
- **Sanitization:** All logs are verified free of credentials, tokens, or PII.

---

## 24. Performance Readiness

- **Model-Only Inference Latency:** $0.235\text{ ms}$ per observation (evaluated in Phase 4F-19).
- **Shadow Pipeline Latency:** $6.05\text{ ms}$ average end-to-end (feature extraction, inference, telemetry logging in Phase 4F-18).
- **End-to-End Ingestion Latency:** `NOT_ESTABLISHED` under live external production stream conditions.

---

## 25. Load Readiness

- **Staging Concurrency:** Tested at 5 concurrent worker threads with 0% errors (Phase 4F-19).
- **Production Load Capacity:** `NOT_ESTABLISHED`. Distributed high-throughput load testing (e.g., $> 1,000\text{ req/sec}$) has not been conducted.
- **Assessment:** Limited controlled concurrency testing completed; production-scale capacity requires cluster load benchmarking.

---

## 26. Frontend Readiness

- **Production Build:** `npm run build` completes cleanly with 0 TypeScript/compilation errors.
- **User Interface Components:** Map layer, hotspot inspection panel, risk distribution breakdown, and telemetry monitoring dashboards render cleanly.
- **Isolation:** Frontend displays authoritative RiskEngine scores as primary, with ML shadow predictions clearly marked as experimental advisory signals.

---

## 27. Dependency Readiness

- **Core Dependencies:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, PostGIS, GeoPandas, Shapely, NumPy, React, Vite, Leaflet.
- **Vulnerability Audit:** No deprecated or vulnerable packages identified in core pipeline path.
- **External Dependencies:** NASA FIRMS API, OpenStreetMap Overpass API (all isolated with non-blocking fallbacks).

---

## 28. External Service Failure Handling

When external third-party services fail:
- NASA FIRMS downtime $\to$ System uses staged historical cache; no crash.
- OpenStreetMap downtime $\to$ Facility association defaults to conservative distances; no crash.
- No external service failure ever causes the system to fabricate observations or fake fire confirmations.

---

## 29. Production Authorization Matrix

| Dimension / Capability | Status | Justification / Evidence |
|---|---|---|
| **ML Shadow Inference** | `PASS` | Verified sub-millisecond execution with complete isolation. |
| **Production ML Autonomous Mode** | `BLOCKED` | ML is strictly non-authoritative; no autonomous trigger allowed. |
| **Authoritative RiskService Engine** | `AUTHORITATIVE` | 100% invariant, deterministic operational risk scoring. |
| **Human Verification Panel** | `PARTIAL` | 25/100 cases catalog-verified; 75/100 pending expert review. |
| **Live FIRMS External Validation** | `NOT_ESTABLISHED` | Ingestion tested via Historical Replay; live continuous poll unvalidated. |
| **Operational Monitoring Telemetry** | `PASS` | Comprehensive zero-impact telemetry and drift tracking active. |
| **Security & Secrets Isolation** | `PASS` | Zero hardcoded secrets, sanitized API responses, clean environment separation. |
| **Rollback & Pinned Checksums** | `PASS` | Pinned SHA-256 fingerprint verified against `4F.13_GB_V1`. |
| **Backup & Disaster Recovery** | `NOT_VALIDATED` | Production cluster backup/restore procedures unverified. |
| **Production-Scale Load Capacity** | `NOT_ESTABLISHED` | High-throughput distributed stress testing not performed. |
| **Controlled Benchmark Accuracy** | `PASS` | 100% macro F1 across 750 curated records in 250 clusters. |
| **Real-World Ambient Accuracy** | `NOT_ESTABLISHED` | Unlabeled background ambient accuracy cannot be quantified without field truth. |
| **Geographic Robustness** | `PASS` | 98.69% spatial stability across 6 diverse Indian macro-regions. |
| **Operational Alert Governance** | `PASS` | Three-tier separation: Engineering, Review, Authoritative Risk. |

---

## 30. Engineering Readiness Assessment

Overall technical architecture, software stability, security controls, and shadow observability are fully mature and staging-ready. However, operational deployment readiness cannot be granted until human verification is completed by an independent expert panel and live satellite ingestion is proven under continuous operation.

---

## 31. Critical Blockers

Before any future production deployment may be authorized, the following 4 critical blockers must be resolved:
1. **Phase 4F-17 Human Verification Completion:** The remaining 75% of the human verification review packet must undergo formal review by an expert adjudication panel.
2. **Live External Satellite Ingest Validation:** Live operational ingest connectivity to NASA FIRMS must be validated under continuous production network conditions.
3. **Empirical Real-World Ambient Accuracy:** Establish ground-truth verification for diffuse ambient thermal events via field reports or high-resolution optical imagery (Sentinel-2 / Landsat-8).
4. **Production-Scale Load & Disaster Recovery Validation:** Complete distributed load stress testing and validate database disaster recovery failover on target production infrastructure.

---

## 32. Limitations

- Model inference probabilities on diffuse, small-scale agricultural burns reflect ambient class prevalence and should not be interpreted as definitive physical ground truth without optical verification.
- Zero Mining top-1 predictions were observed in the ambient test sample, reflecting sample rarity rather than absence of regional mining activity.
- The system relies on NASA FIRMS satellite revisit cycles (MODIS/VIIRS), which introduce physical temporal latency between fire ignition and satellite detection.

---

## 33. Recommendations

1. Convene an independent domain expert review panel to complete the Phase 4F-17 review packet.
2. Execute a 14-day continuous live NASA FIRMS connectivity trial in a dedicated staging environment.
3. Integrate automated Sentinel-2 / Landsat-8 optical tile fetching to provide high-resolution visual evidence for queued candidate reviews.
4. Maintain ML classification strictly in shadow advisory mode until all 4 critical blockers are resolved.

---

## 34. Final Gate Decision

### **Decision: `GATE B — CONDITIONAL PRODUCTION READINESS`**

**Rationale:**  
The AVISHKAR 2.0 system is technically mature, architecturally robust, and operationally stable in staging with verified sub-millisecond inference, 100% Risk Engine invariance, and strict shadow isolation. However, production deployment remains CONDITIONAL upon completing human expert panel adjudication, validating live satellite connectivity, and establishing empirical real-world accuracy on ambient detections.

- **`PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`**
- **Mandatory Statement:** *Phase 4F-20 does not authorize production deployment.*
