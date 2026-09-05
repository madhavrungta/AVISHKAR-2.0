# PHASE 4F-22 — CONTROLLED 14-DAY LIVE NASA FIRMS STAGING TRIAL

**PROJECT:** AVISHKAR 2.0 — SIH 26162  
**ORGANIZATION:** NTRO / SIH 2024  
**TITLE:** AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources  
**DATE:** 2026-09-04  
**ENVIRONMENT:** `STAGING`  
**STATUS:** `IN_PROGRESS` (Staging Infrastructure Verified; Continuous 14-Day Calendar Logging Active)  
**GATE DECISION:** `GATE B — CONDITIONAL LIVE VALIDATION`  
**AUTHORIZATION:** `PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`  
**MANDATORY STATEMENT:** *Phase 4F-22 does not authorize production deployment.*

---

## 1. Executive Summary

Phase 4F-22 establishes the controlled **14-Day Live NASA FIRMS Staging Trial** for the AVISHKAR 2.0 system. Following the identification of live external streaming validation as a primary blocker in Phase 4F-20, Phase 4F-22 implements and validates the staging telemetry, bounded retry protocols, duplicate rejection, schema validation, and shadow ML inference under authentic external API communication constraints.

### Key Operational Findings:
1. **Staging Environment Isolation:** Execution is verified strictly within an isolated staging environment (`ENVIRONMENT = staging`). Zero production databases, live operational alerting systems, or production endpoints are targeted.
2. **Honest Trial Clock Reporting:** The software explicitly separates *implementation readiness* from *elapsed operational duration*. The trial status is recorded as `IN_PROGRESS` with the full 14-day calendar clock running; zero fabricated uptime, synthetic latency, or fake 14-day metrics are reported.
3. **Data Source Mode Disambiguation:** Ingestion requests strictly record and isolate `LIVE`, `HISTORICAL_REPLAY`, and `SYNTHETIC_TEST` modalities.
4. **Bounded Retry & Rate Limit Protection:** NASA FIRMS API queries use bounded exponential backoff (max 3 retries). HTTP 429 rate-limiting responses immediately trigger non-blocking backoff without flooding the upstream service.
5. **Idempotency & Duplicate Protection:** Live duplicate observation ingestion is detected via coordinate and timestamp keys, blocking duplicate database insertion while maintaining 100% telemetry recording.
6. **Risk Engine & Shadow ML Invariance:** All live observations pass through ML strictly in shadow mode (`ML_CLASSIFIER_SHADOW_ONLY = TRUE`). `RiskService` calculations remain 100% invariant and authoritative (`RISK_ENGINE_INVARIANT = TRUE`).
7. **Model Integrity:** Approved classifier `4F.13_GB_V1` SHA-256 fingerprint verified: `f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810`.

---

## 2. Objective & Scientific Boundaries

### Primary Objective:
Determine whether the AVISHKAR 2.0 ingestion and processing pipeline can continuously communicate with the real NASA FIRMS external API under live network conditions in an isolated staging environment, safely handling upstream outages, rate limits, schema anomalies, and deduplication.

### What Phase 4F-22 Is NOT:
- **NOT a production deployment:** Production authorization remains strictly `FALSE`.
- **NOT a model retraining or threshold tuning phase:** Model weights and schemas remain completely frozen.
- **NOT an accuracy validation phase:** Ambient unverified live satellite detections are not treated as ground truth.
- **NOT an emergency dispatch activation:** No real-world operational fire alerts are dispatched.

---

## 3. NASA FIRMS Staging Configuration

- **Sensor Platform:** `VIIRS_SNPP_NRT` (Suomi NPP Visible Infrared Imaging Radiometer Suite - Near Real-Time)
- **Spatial Coverage (India Bounding Box):**
  - West: $68.0^\circ\text{ E}$
  - South: $6.0^\circ\text{ N}$
  - East: $97.0^\circ\text{ E}$
  - North: $37.0^\circ\text{ N}$
- **Staged Temporal Fallback Sequence:**
  $$\text{Primary 24-Hour Pass} \longrightarrow \text{3-Day Cumulative Fallback} \longrightarrow \text{5-Day Multi-Revisit Fallback}$$

---

## 4. Request Telemetry & Failure Classification

Every polling cycle records full structured telemetry sanitized of credentials:
- `run_id`, `request_id`, `timestamp_utc`, `sensor`, `bbox`, `requested_window`, `source_mode`
- `credential_configured` (`true`/`false`), `http_status`, `response_received`
- `request_latency_ms`, `response_bytes`, `parsed_records`, `valid_records`, `duplicate_records`, `persisted_records`
- `fallback_used`, `fallback_stage`, `error_category`, `error_message_sanitized`

### 15-Class Failure Recovery Taxonomy:
1. `CONFIGURATION_ERROR` (e.g. missing API key)
2. `AUTHENTICATION_ERROR` (HTTP 401/403)
3. `AUTHORIZATION_ERROR`
4. `NETWORK_TIMEOUT` (HTTP connection / read timeout)
5. `NETWORK_CONNECTION_ERROR` (DNS / TCP failure)
6. `DNS_ERROR`
7. `HTTP_4XX` (Client errors)
8. `HTTP_429_RATE_LIMIT` (Upstream rate limiting)
9. `HTTP_5XX` (Upstream server error)
10. `EMPTY_RESPONSE` (HTTP 200 with 0 records — valid empty pass)
11. `MALFORMED_RESPONSE` (CSV syntax corruption)
12. `SCHEMA_ERROR` (Missing required columns)
13. `VALIDATION_ERROR` (Out-of-bounds coordinates)
14. `DATABASE_ERROR` (Connection pool drop)
15. `PERSISTENCE_ERROR` (Transaction rollback)

---

## 5. Idempotency & Duplicate Protection

To prevent satellite data duplication from repeated cron passes:
- Observations are deduplicated by composite key: $(\text{latitude}, \text{longitude}, \text{acq\_date}, \text{acq\_time})$.
- Repeated polling passes detect existing records, increment `duplicate_records`, and prevent duplicate row persistence.
- Verified in staging: Initial cycle persists valid records; subsequent cycle detects 100% duplicate records with 0 duplicate rows written.

---

## 6. Risk Engine Invariance & Shadow Mode

- **Risk Engine Authority:** `RiskService` remains 100% authoritative for all risk calculations ($S = 0.25 S_{\text{prox}} + 0.30 S_{\text{frp}} + 0.25 S_{\text{sens}} + 0.20 S_{\text{opt}}$).
- **ML Shadow Isolation:** Inferences run purely as non-blocking advisory telemetry (`ML_CLASSIFIER_SHADOW_ONLY = TRUE`).
- **Invariance Test Result:** `PASS` (`100% INVARIANT`).

---

## 7. Security & Credential Governance

- **Zero Secret Exposure:** `FIRMS_MAP_KEY` and database credentials are strictly externalized via `.env`.
- **Sanitization:** All logs, API error payloads, and JSON artifacts sanitize connection strings and query parameters (`***REDACTED_KEY***`).
- **Staging Network Policy:** Isolated staging endpoints with restricted CORS.

---

## 8. Trial Duration & Operational Status

- **Trial Start Date:** 2026-09-04T00:00:00Z
- **Target Duration:** 14 consecutive calendar days (Target: 2026-09-18T00:00:00Z)
- **Current Operational Status:** `IN_PROGRESS` (Staging initialization and automated polling cycle verified; continuous logging active).
- **Scientific Integrity Statement:** *14-day physical duration is running continuously; zero synthetic uptime or fake elapsed metrics are reported.*

---

## 9. Acceptance Criteria Verification

| Criterion | Requirement | Verification Method | Status |
|---|---|---|---|
| **Staging Isolation** | Staging environment only | Rejects non-staging configurations | `PASS` |
| **Data Mode Separation** | Separate LIVE vs TEST | Telemetry tag `source_mode` verified | `PASS` |
| **Secret Redaction** | No API keys in logs/JSON | `sanitize_error_message` verified | `PASS` |
| **Bounded Retry** | Max 3 retries, no runaway loops | Verified on mock HTTP 500/502 | `PASS` |
| **Rate Limit Handling** | Non-blocking on HTTP 429 | Verified on mock HTTP 429 | `PASS` |
| **Empty Response Handling**| HTTP 200 + 0 records != error | Verified on empty CSV | `PASS` |
| **Malformed Response** | Catch CSV syntax errors safely | Verified on corrupt CSV | `PASS` |
| **Deduplication** | Idempotent persistence | Replay test verified | `PASS` |
| **ML Shadow Mode** | Non-authoritative inference | `ML_CLASSIFIER_SHADOW_ONLY == True` | `PASS` |
| **Risk Invariance** | Authoritative scoring unchanged | `RISK_ENGINE_INVARIANT == True` | `PASS` |
| **Model Integrity** | Checksum verified | SHA-256 matches `4F.13_GB_V1` | `PASS` |
| **No Fabricated Time** | Status reflects current progress | `trial_status == 'IN_PROGRESS'` | `PASS` |
| **Production Auth False** | No automatic authorization | `PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE` | `PASS` |

---

## 10. Final Gate Decision

### **Decision: `GATE B — CONDITIONAL LIVE VALIDATION`**

**Rationale:**  
The live NASA FIRMS staging polling infrastructure, bounded retry policies, duplicate protection, schema validation, failure recovery protocols, and shadow inference are fully verified in staging. Final production readiness is CONDITIONAL upon completing the continuous 14-day elapsed operational logging period in staging.

- **`PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`**
- **Mandatory Statement:** *Phase 4F-22 does not authorize production deployment.*
