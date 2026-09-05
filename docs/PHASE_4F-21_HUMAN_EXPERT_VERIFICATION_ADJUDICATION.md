# PHASE 4F-21 — CONTROLLED HUMAN EXPERT VERIFICATION & ADJUDICATION

**PROJECT:** AVISHKAR 2.0 — SIH 26162  
**ORGANIZATION:** NTRO / SIH 2024  
**TITLE:** AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources  
**DATE:** 2026-09-04  
**STATUS:** COMPLETE  
**GATE DECISION:** `GATE B — CONDITIONAL HUMAN VALIDATION`  
**AUTHORIZATION:** `PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`  
**MANDATORY STATEMENT:** *Phase 4F-21 does not authorize production deployment.*

---

## 1. Executive Summary

Phase 4F-21 implements the formal **Controlled Human Expert Verification and Adjudication Workflow** for AVISHKAR 2.0. In Phase 4F-20 (Production Readiness Gate Review), human verification was identified as the primary operational blocker preventing production authorization, with 75% of the Phase 4F-17 review sample awaiting expert adjudication.

Phase 4F-21 operationalizes a multi-reviewer, double-blinded expert verification lifecycle backed by PostgreSQL audit persistence, automated disagreement detection, formal adjudication workflows, chance-adjusted inter-rater agreement computation (Cohen's Kappa / Fleiss' Kappa), and strict mathematical separation between ML shadow inferences and adjudicated ground truth.

### Key Operational Findings:
1. **Preservation of 100-Case Review Packet:** All 100 stratified observations from Phase 4F-17 (60 priority candidates, 40 diversity/control cases) are preserved without modification.
2. **Strict Invariant on Automated Labels:** 0 human decisions or reviewer comments were auto-generated. 75 unreviewed ambient cases remain strictly `PENDING_REVIEW` until authentic domain expert submission.
3. **Double-Blinded Verification Control:** Reviewers can inspect thermal observations, spatial contexts, land cover, and infrastructure proximities with ML shadow predictions masked (`blinded = true`) to eliminate confirmation bias.
4. **Multi-Reviewer Disagreement & Adjudication:** Independent submissions by multiple reviewers (e.g. `REVIEWER_A`, `REVIEWER_B`) automatically detect semantic classification conflicts, transitioning cases to `NEEDS_ADJUDICATION` for senior panel resolution.
5. **Level-1 Catalog Adjudicated Subset:** 25 cases with official Level-1 ground-truth catalog linkages are adjudicated as `VERIFIED`. ML shadow classification matches 100% of these high-confidence catalog cases.
6. **Risk Engine Invariance:** `RiskService` remains 100% authoritative and invariant (`RISK_ENGINE_INVARIANT = TRUE`).
7. **Model Integrity:** Approved model `4F.13_GB_V1` weights remain frozen and verified via SHA-256 (`f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810`).

---

## 2. Objective & Scientific Invariants

### Primary Objective:
Establish an auditable, scientifically sound workflow that enables independent domain experts to review, classify, and adjudicate satellite thermal observations using explicit ground evidence, allowing rigorous future comparison against ML shadow predictions without biasing reviewers or manufacturing evidence.

### Hard Scientific Invariants Enforced:
1. **Zero Automated Human Labels:** The software never infers, synthesizes, guesses, or auto-approves human labels.
2. **Explicit Uncertainty:** `INSUFFICIENT_EVIDENCE` is explicitly modeled as a distinct outcome and is never conflated with negative rejection (`REJECTED`).
3. **Pending Exclusion:** `PENDING_REVIEW` cases are strictly excluded from accuracy, precision, recall, and F1 calculations.
4. **Non-Authoritative ML:** ML predictions remain strictly shadow-only advisory signals labeled `“ML SHADOW PREDICTION — NOT HUMAN GROUND TRUTH”`.
5. **Zero Model Alteration:** Zero retraining, zero weight tuning, zero threshold modification.
6. **Risk Invariance:** Operational risk scoring and alert generation remain under the exclusive authority of `RiskService`.

---

## 3. Review Taxonomy & Status Lifecycle

### Supported Review Outcomes:
- **`VERIFIED`:** Thermal source is confirmed by explicit physical, spatial, or catalog evidence to belong to a specific modeled category.
- **`REJECTED`:** Evidence explicitly contradicts candidate classification or confirms a sensor artifact / noise event.
- **`UNCERTAIN`:** Evidence provides conflicting or ambiguous indicators across multiple potential source types.
- **`INSUFFICIENT_EVIDENCE`:** Observational data or contextual layers are inadequate (e.g. cloud occlusion, missing imagery) to establish classification.
- **`PENDING_REVIEW`:** Case is queued in review packet awaiting expert inspection.

### Supported Target Classes:
- `INDUSTRIAL_FIRE`
- `GAS_FLARE`
- `AGRICULTURAL_BURNING`
- `MINING_ACTIVITY`
- `WILDFIRE`
- `UNKNOWN / OTHER`

### Review Lifecycle Workflow:
```
[ PENDING_REVIEW ]
        │
        ▼
   [ ASSIGNED ]
        │
        ▼
  [ IN_REVIEW ] (Blinded: ml_visible = False)
        │
        ▼
[ REVIEW_SUBMITTED ]
        │
        ├─────────────────────────────────────────┐
        │                                         │
 (Unanimous Agreement)                     (Disagreement)
        │                                         │
        ▼                                         ▼
  [ ADJUDICATED ]                       [ NEEDS_ADJUDICATION ]
                                                  │
                                                  ▼
                                       [ EXPERT ADJUDICATION ]
                                                  │
                                                  ▼
                                            [ ADJUDICATED ]
```

---

## 4. Evidence Panel Structure

Every review case provides a comprehensive 7-layer evidence packet:
1. **FIRMS Observation:** Latitude, longitude, acquisition date/time, satellite platform (MODIS / VIIRS), instrument, Fire Radiative Power (FRP), brightness temperature, scan angle, track.
2. **ML Shadow Prediction:** Predicted class, full probability distribution, top-1/top-2 margin, anomaly score (masked during blinded review).
3. **Temporal Context:** 3-day / 30-day persistence count, baseline historical distribution ($P_{50}, P_{95}, P_{99}$), FRP $z$-score, brightness $z$-score.
4. **Spatial Context:** Geodesic distances to industrial facilities, energy assets, transportation hubs, railways, highways, ports, airports, and healthcare centers.
5. **Land-Cover Context:** ESA WorldCover classification (cropland, forest, urban, wetland, bare ground) and local vegetation index.
6. **External Evidence:** Level-1 catalog linkage, official registry IDs, industrial boundary polygons.
7. **Optical Evidence:** Sentinel-2 / Landsat-8 optical verification status (explicitly flagged as `OPTICAL_EVIDENCE = NOT_AVAILABLE` when absent).

---

## 5. Reviewer Audit Schema & Database Architecture

Three dedicated, relational tables maintain complete data provenance:
- **`human_review_cases`:** Stores the 100 review packets, sampling rationales, evidence snapshots, and lifecycle state (`PENDING_REVIEW`, `ADJUDICATED`, `NEEDS_ADJUDICATION`).
- **`human_review_decisions`:** Records immutable individual reviewer submissions, including `reviewer_id`, `review_status`, `observed_class`, `evidence_strength` (`STRONG`, `MODERATE`, `WEAK`, `INSUFFICIENT`), `confidence_level` (`HIGH`, `MEDIUM`, `LOW`), `evidence_sources`, `reviewer_comment`, and `is_blinded` flags.
- **`human_adjudications`:** Logs formal panel adjudications, documenting `adjudicator_id`, timestamp, `adjudication_reason`, `evidence_used`, and `final_decision`.

---

## 6. Multi-Reviewer Agreement & Adjudication Metrics

### Mathematical Formulations:
1. **Cohen's Kappa ($\kappa$) for 2 Raters:**
   $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   where $P_o$ is observed fractional agreement and $P_e$ is chance-expected agreement.
2. **Fleiss' Kappa for $k \ge 3$ Raters:**
   $$\kappa = \frac{\bar{P} - \bar{P}_e}{1 - \bar{P}_e}$$

### Operational Inter-Rater Status:
- **Current Metric Status:** `NOT_ESTABLISHED` (evaluated across single-reviewer catalog initialization; requires multi-expert panel overlap across common cases before generating statistical coefficients).

---

## 7. ML vs. Human Ground-Truth Performance

Evaluating ML shadow inferences strictly against the 25 independently adjudicated Level-1 catalog ground-truth cases:

| Metric | Measured Value | Sample Basis |
|---|---|---|
| **Adjudicated Sample Size** | 25 records | Level-1 Official Catalog Records |
| **Pending Review Excluded** | 75 records | Excluded from calculation |
| **Accuracy on Adjudicated Set** | **100.0%** ($25/25$) | Verified catalog subset |
| **Macro F1 Score** | **1.0000** | Balanced across verified classes |
| **Agricultural Burning F1** | **1.0000** ($14/14$) | Support: 14 |
| **Gas Flaring F1** | **1.0000** ($11/11$) | Support: 11 |

### Confusion Matrix (Adjudicated Set Only):
```
Actual \ Predicted       AGRICULTURAL_BURNING    GAS_FLARE
AGRICULTURAL_BURNING              14                 0
GAS_FLARE                          0                11
```

*Note: Performance on the 25 adjudicated Level-1 cases does not imply 100% accuracy on the remaining 75 unreviewed ambient cases.*

---

## 8. Domain-Specific Verification Audits

### Industrial Fire Verification:
- **Candidate Cases in Review Packet:** 15 candidates identified via high thermal intensity and industrial proximity.
- **Adjudicated Verified Cases:** 0 confirmed industrial fires (11 refinery gas flaring events verified in industrial zones).
- **Pending Review Cases:** 15 candidates remain in `PENDING_REVIEW` awaiting field / fire department incident record correlation.
- **Status:** `PARTIAL_EVIDENCE` (Proximity to industrial assets alone does not constitute confirmed fire damage).

### Mining Activity Verification:
- **Candidate Cases in Review Packet:** 0 top-1 ambient mining detections in review sample.
- **Adjudicated Verified Cases:** 0.
- **Mandatory Statement:** *No independently verified Mining thermal event was available in the evaluated review sample.*
- **Status:** `NOT_ESTABLISHED_IN_REVIEW_SAMPLE`.

---

## 9. RiskService Invariance Audit

Verification of operational risk calculation isolation:
- **Before Human Verification Implementation:** $S = 0.25 S_{\text{prox}} + 0.30 S_{\text{frp}} + 0.25 S_{\text{sens}} + 0.20 S_{\text{opt}}$
- **After Human Verification Implementation:** Identical ($100\%$ numerical invariance).
- **Risk Engine Invariance Status:** `PASS` (`RISK_ENGINE_INVARIANT = TRUE`).

---

## 10. REST API Endpoints

The following REST API endpoints are active in `backend/app/api/human_review.py`:
- `GET /ml/human-review/cases` — List review cases with status filters and `blinded=true/false` controls.
- `GET /ml/human-review/cases/{case_id}` — Get complete evidence packet for a specific case.
- `POST /ml/human-review/cases/{case_id}/review` — Submit independent reviewer decision.
- `GET /ml/human-review/cases/{case_id}/reviews` — Retrieve all reviewer decisions and adjudication history.
- `POST /ml/human-review/cases/{case_id}/adjudicate` — Manually adjudicate disagreements or finalize cases.
- `GET /ml/human-review/summary` — Aggregate progress, inter-rater status, and ML comparison metrics.

---

## 11. Acceptance Criteria Verification

| Acceptance Criterion | Verification Method | Status |
|---|---|---|
| **100-Case Packet Preserved** | `HumanReviewCase.count() == 100` | `PASS` |
| **75 Pending Cases Preserved** | `status == 'PENDING_REVIEW'` count verified | `PASS` |
| **Zero Automated Human Labels** | Audit query for un-submitted decisions | `PASS` |
| **Zero Automatic Adjudications** | Adjudication requires explicit `adjudicator_id` | `PASS` |
| **Insufficient Evidence Distinct** | Explicitly modeled as separate status | `PASS` |
| **Blinded Review Supported** | `blinded=True` suppresses ML predictions | `PASS` |
| **Disagreement Detection** | Divergent votes trigger `NEEDS_ADJUDICATION` | `PASS` |
| **Duplicate Submission Block** | Same reviewer cannot submit twice for same case | `PASS` |
| **RiskService Invariance** | Deterministic 4-factor scoring unchanged | `PASS` |
| **ML Shadow-Only Isolation** | Model remains non-authoritative advisory | `PASS` |
| **Model Weights Untouched** | Pinned SHA-256 matches `4F.13_GB_V1` | `PASS` |
| **Mining Statement Exact** | Mandatory statement verified in artifact | `PASS` |
| **Automated Tests** | 20/20 unit tests passed | `PASS` |
| **Frontend Build** | `npm run build` succeeds (0 errors) | `PASS` |

---

## 12. Final Gate Decision

### **Decision: `GATE B — CONDITIONAL HUMAN VALIDATION`**

**Rationale:**  
The human expert verification and adjudication framework is fully implemented with double-blinded controls, audit logs, multi-reviewer lifecycle support, and disagreement handling. 25 cases have Level-1 catalog ground-truth adjudication, while 75 cases remain `PENDING_REVIEW` awaiting independent domain-expert panel completion.

- **`PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE`**
- **Mandatory Statement:** *Phase 4F-21 does not authorize production deployment.*
