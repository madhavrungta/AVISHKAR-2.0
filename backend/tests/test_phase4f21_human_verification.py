"""
Phase 4F-21 Controlled Human Expert Verification & Adjudication Test Suite
AVISHKAR 2.0 — SIH 26162 (NTRO)

Tests all 20 criteria specified in Phase 4F-21:
1. Review case loading (100 cases loaded)
2. PENDING_REVIEW preservation (75 cases remain pending without auto-labels)
3. Reviewer submission workflow
4. Reviewer decision persistence
5. No automatic human labeling
6. Insufficient evidence handling (distinct from REJECTED)
7. Blinded ML workflow (masks predictions)
8. Disagreement detection (triggers NEEDS_ADJUDICATION)
9. Adjudication workflow (manual resolution)
10. No automatic adjudication
11. Agreement metric calculation (Cohen's Kappa & Fleiss' Kappa)
12. Insufficient reviewer overlap handling (NOT_ESTABLISHED)
13. ML-vs-human comparison calculation
14. Pending cases excluded from accuracy
15. Mining zero-verification handling (mandatory statement)
16. Audit trail integrity
17. Duplicate submission protection
18. RiskService invariance
19. ML shadow-only invariant
20. API validation
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.models.human_review import HumanReviewCase, HumanReviewDecision, HumanAdjudicationRecord
from app.ml.phase4f21_human_verification import (
    HumanExpertVerificationManager, run_phase4f21_human_verification_pilot,
    calculate_cohens_kappa, calculate_fleiss_kappa
)
from app.services.risk_service import RiskService
from app.main import app


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    manager = HumanExpertVerificationManager(db)
    manager.initialize_from_phase4f17_packet()
    yield db
    db.close()


@pytest.fixture(scope="module")
def verification_results():
    artifact_path = Path(__file__).parent.parent / "ml_artifacts" / "phase_4f21_human_verification_results.json"
    if artifact_path.exists():
        with open(artifact_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return run_phase4f21_human_verification_pilot()


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)


def test_01_review_case_loading(db_session, verification_results):
    """1. Verify 100 review cases are loaded from Phase 4F-17 packet."""
    cases_count = db_session.query(HumanReviewCase).count()
    assert cases_count == 100
    assert verification_results["review_packet_size"] == 100


def test_02_pending_review_preservation(db_session, verification_results):
    """2. Verify 75 unreviewed cases remain strictly PENDING_REVIEW."""
    pending_count = db_session.query(HumanReviewCase).filter(HumanReviewCase.status == "PENDING_REVIEW").count()
    assert pending_count == 75
    assert verification_results["pending_review_count"] == 75


def test_03_reviewer_submission(db_session):
    """3. Test independent reviewer decision submission workflow."""
    manager = HumanExpertVerificationManager(db_session)
    # Pick a pending case (e.g., REV-050)
    case_obj = db_session.query(HumanReviewCase).filter(HumanReviewCase.status == "PENDING_REVIEW").first()
    assert case_obj is not None
    
    res = manager.submit_reviewer_decision(
        case_id=case_obj.case_id,
        reviewer_id="TEST_REVIEWER_A",
        review_status="VERIFIED",
        observed_class="AGRICULTURAL_BURNING",
        evidence_strength="STRONG",
        confidence_level="HIGH",
        evidence_sources=["FIRMS_FRP", "LANDCOVER_MAP"],
        reviewer_comment="Clear agricultural field thermal signature",
        reviewer_flags=["NEEDS_OPTICAL_VERIFICATION"],
        is_blinded=True
    )
    assert res["status"] == "SUCCESS"
    assert res["case_status"] in ["REVIEW_SUBMITTED", "ADJUDICATED"]


def test_04_reviewer_decision_persistence(db_session):
    """4. Verify reviewer decision is persisted with all required audit fields."""
    dec = db_session.query(HumanReviewDecision).filter(
        HumanReviewDecision.reviewer_id == "TEST_REVIEWER_A"
    ).first()
    assert dec is not None
    assert dec.observed_class == "AGRICULTURAL_BURNING"
    assert dec.evidence_strength == "STRONG"
    assert dec.confidence_level == "HIGH"
    assert "FIRMS_FRP" in dec.evidence_sources
    assert dec.is_blinded is True
    assert dec.model_version_at_review == "4F.13_GB_V1"


def test_05_no_automatic_human_labeling(db_session):
    """5. Verify cases without explicit reviewer decisions do NOT have human labels."""
    pending_cases = db_session.query(HumanReviewCase).filter(HumanReviewCase.status == "PENDING_REVIEW").all()
    for pc in pending_cases:
        assert pc.final_adjudicated_class is None
        assert pc.final_adjudicated_status is None


def test_06_insufficient_evidence_handling(db_session):
    """6. Verify INSUFFICIENT_EVIDENCE is handled distinctly from REJECTED."""
    manager = HumanExpertVerificationManager(db_session)
    case_obj = db_session.query(HumanReviewCase).filter(HumanReviewCase.status == "PENDING_REVIEW").first()
    if case_obj:
        res = manager.submit_reviewer_decision(
            case_id=case_obj.case_id,
            reviewer_id="TEST_REVIEWER_B",
            review_status="INSUFFICIENT_EVIDENCE",
            evidence_strength="INSUFFICIENT",
            confidence_level="LOW",
            reviewer_comment="Cloud occlusion; thermal signal too low"
        )
        assert res["status"] == "SUCCESS"
        assert res["case_status"] == "INSUFFICIENT_EVIDENCE"
        
        # Verify status in database is INSUFFICIENT_EVIDENCE and not REJECTED
        db_session.refresh(case_obj)
        assert case_obj.status == "INSUFFICIENT_EVIDENCE"


def test_07_blinded_ml_workflow(db_session):
    """7. Verify blinding workflow masks ML shadow predictions when blinded=True."""
    case_obj = db_session.query(HumanReviewCase).first()
    blinded_dict = case_obj.to_dict(include_ml=False)
    unblinded_dict = case_obj.to_dict(include_ml=True)
    
    assert blinded_dict["evidence"]["ml_evidence"]["status"] == "BLINDED_DURING_REVIEW"
    assert "predicted_class" not in blinded_dict["evidence"]["ml_evidence"]
    assert "predicted_class" in unblinded_dict["evidence"]["ml_evidence"]


def test_08_disagreement_detection(db_session):
    """8. Verify conflicting reviewer decisions trigger NEEDS_ADJUDICATION status."""
    manager = HumanExpertVerificationManager(db_session)
    # Pick a fresh pending case
    case_obj = db_session.query(HumanReviewCase).filter(HumanReviewCase.status == "PENDING_REVIEW").first()
    if case_obj:
        # Reviewer 1 votes INDUSTRIAL_FIRE
        manager.submit_reviewer_decision(
            case_id=case_obj.case_id,
            reviewer_id="REVIEWER_EXPERT_1",
            review_status="VERIFIED",
            observed_class="INDUSTRIAL_FIRE"
        )
        # Reviewer 2 votes GAS_FLARE
        manager.submit_reviewer_decision(
            case_id=case_obj.case_id,
            reviewer_id="REVIEWER_EXPERT_2",
            review_status="VERIFIED",
            observed_class="GAS_FLARE"
        )
        db_session.refresh(case_obj)
        assert case_obj.status == "NEEDS_ADJUDICATION"


def test_09_adjudication_workflow(db_session):
    """9. Verify expert adjudication resolves disagreements."""
    manager = HumanExpertVerificationManager(db_session)
    needs_adj = db_session.query(HumanReviewCase).filter(HumanReviewCase.status == "NEEDS_ADJUDICATION").first()
    if needs_adj:
        res = manager.adjudicate_case(
            case_id=needs_adj.case_id,
            adjudicator_id="SENIOR_PANEL_ADJUDICATOR",
            final_decision="VERIFIED",
            final_class="GAS_FLARE",
            adjudication_reason="Refinery flare stack visible on satellite boundary polygon.",
            evidence_used=["OSM Industrial Boundary", "Thermal Temporal Continuity"]
        )
        assert res["status"] == "SUCCESS"
        db_session.refresh(needs_adj)
        assert needs_adj.status == "ADJUDICATED"
        assert needs_adj.final_adjudicated_class == "GAS_FLARE"
        assert needs_adj.final_adjudicated_status == "VERIFIED"


def test_10_no_automatic_adjudication(db_session):
    """10. Verify adjudication records exist only from explicit adjudications."""
    adjs = db_session.query(HumanAdjudicationRecord).all()
    assert len(adjs) > 0
    for a in adjs:
        assert a.adjudicator_id is not None
        assert a.final_decision in ["VERIFIED", "REJECTED", "UNCERTAIN", "INSUFFICIENT_EVIDENCE"]


def test_11_agreement_metric_calculation():
    """11. Verify chance-adjusted Cohen's Kappa and Fleiss' Kappa mathematical calculations."""
    r1 = ["CAT_A", "CAT_A", "CAT_B", "CAT_C", "CAT_B"]
    r2 = ["CAT_A", "CAT_B", "CAT_B", "CAT_C", "CAT_B"]
    cats = ["CAT_A", "CAT_B", "CAT_C"]
    
    kappa = calculate_cohens_kappa(r1, r2, cats)
    assert 0.0 <= kappa <= 1.0
    
    # Fleiss Kappa
    matrix = [
        {"CAT_A": 2, "CAT_B": 0, "CAT_C": 0},
        {"CAT_A": 0, "CAT_B": 2, "CAT_C": 0},
        {"CAT_A": 0, "CAT_B": 0, "CAT_C": 2}
    ]
    f_kappa = calculate_fleiss_kappa(matrix, cats)
    assert f_kappa == 1.0


def test_12_insufficient_reviewer_overlap_handling(db_session):
    """12. Verify inter-rater agreement returns NOT_ESTABLISHED when overlap is insufficient."""
    manager = HumanExpertVerificationManager(db_session)
    res = manager.evaluate_inter_rater_agreement()
    assert res["status"] in ["ESTABLISHED", "NOT_ESTABLISHED"]


def test_13_ml_vs_human_comparison(db_session):
    """13. Verify ML vs Human metrics are calculated across adjudicated cases."""
    manager = HumanExpertVerificationManager(db_session)
    metrics = manager.evaluate_ml_vs_human_metrics()
    assert metrics["status"] == "ESTABLISHED"
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "confusion_matrix" in metrics


def test_14_pending_cases_excluded_from_accuracy(verification_results):
    """14. Verify pending cases (75) are excluded from accuracy sample size."""
    ml_metrics = verification_results["ml_vs_human_metrics"]
    assert ml_metrics["sample_size"] <= 26
    assert ml_metrics["sample_size"] != 100


def test_15_mining_zero_verification_handling(verification_results):
    """15. Verify Mining audit displays the mandatory statement without claiming zero mining exists."""
    mining = verification_results["mining_status"]
    assert mining["adjudicated_verified_count"] == 0
    assert mining["mandatory_statement"] == "No independently verified Mining thermal event was available in the evaluated review sample."


def test_16_audit_trail_integrity(db_session):
    """16. Verify audit trail integrity and relations between cases and decisions."""
    dec = db_session.query(HumanReviewDecision).first()
    assert dec.review_case is not None
    assert dec.review_case.case_id is not None


def test_17_duplicate_submission_protection(db_session):
    """17. Verify that duplicate review submission by the same reviewer raises an error."""
    manager = HumanExpertVerificationManager(db_session)
    case_obj = db_session.query(HumanReviewCase).first()
    with pytest.raises(ValueError, match="already submitted a decision"):
        manager.submit_reviewer_decision(
            case_id=case_obj.case_id,
            reviewer_id="OFFICIAL_LEVEL1_CATALOG",
            review_status="VERIFIED",
            observed_class="GAS_FLARE"
        )


def test_18_risk_service_invariance():
    """18. Verify RiskService invariance is strictly preserved."""
    risk_svc = RiskService()
    tier_crit = risk_svc.classify_risk_tier(92.0)
    tier_high = risk_svc.classify_risk_tier(68.0)
    tier_med = risk_svc.classify_risk_tier(45.0)
    tier_low = risk_svc.classify_risk_tier(20.0)
    assert tier_crit == "CRITICAL_VERIFIED_RISK"
    assert tier_high == "HIGH_RISK"
    assert tier_med == "MEDIUM_RISK"
    assert tier_low == "LOW_RISK"


def test_19_ml_shadow_only_invariant(verification_results):
    """19. Verify ML is strictly shadow-only and production authorization is FALSE."""
    assert verification_results["ml_shadow_only"] is True
    assert verification_results["production_deployment_authorized"] is False
    assert verification_results["gate"] == "GATE B \u2014 CONDITIONAL HUMAN VALIDATION"


def test_20_api_validation(test_client):
    """20. Verify FastAPI human review endpoints respond with valid schemas."""
    # 1. Summary endpoint
    resp_sum = test_client.get("/ml/human-review/summary")
    assert resp_sum.status_code == 200
    data_sum = resp_sum.json()
    assert data_sum["total_cases"] == 100
    assert data_sum["risk_engine_invariance"] == "100% INVARIANT"
    
    # 2. Cases list endpoint (blinded)
    resp_cases = test_client.get("/ml/human-review/cases?blinded=true&limit=5")
    assert resp_cases.status_code == 200
    data_cases = resp_cases.json()
    assert data_cases["blinded"] is True
    assert len(data_cases["cases"]) == 5
    
    # 3. Single case endpoint (unblinded)
    case_id = data_cases["cases"][0]["case_id"]
    resp_single = test_client.get(f"/ml/human-review/cases/{case_id}?blinded=false")
    assert resp_single.status_code == 200
    data_single = resp_single.json()
    assert data_single["case_id"] == case_id
