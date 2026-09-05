"""
AVISHKAR 2.0 — Phase 4F-17: Automated Test Suite for Human Verification & Expert Evaluation Pilot
"""

import os
import json
import pytest
from app.ml.phase4f17_human_verification import run_phase4f17_human_verification_pilot

ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_artifacts"))
RESULTS_FILE = os.path.join(ARTIFACT_DIR, "phase_4f17_human_verification_results.json")

@pytest.fixture(scope="module")
def phase17_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return run_phase4f17_human_verification_pilot()

def test_hard_scientific_constraint_compliance(phase17_results):
    h = phase17_results.get("hard_scientific_constraint_compliance", {})
    assert h["automation_inferred_decisions"] is False
    assert h["synthetic_demo_data_included_in_metrics"] is False
    assert h["unreviewed_ambient_decision_status"] == "PENDING_REVIEW"

def test_review_sample_size_and_stratification(phase17_results):
    s = phase17_results.get("sample_summary", {})
    assert s["total_sample_size"] == 100
    assert s["priority_review_set_count"] > 0
    assert s["diversity_control_set_count"] > 0
    assert len(s["regions_represented"]) >= 4
    assert len(s["classes_represented"]) >= 3

def test_review_schema_completeness(phase17_results):
    recs = phase17_results.get("review_records", [])
    assert len(recs) == 100
    r0 = recs[0]
    assert "identification" in r0
    assert "ml_evidence" in r0
    assert "thermal_evidence" in r0
    assert "spatial_context" in r0
    assert "comparison" in r0
    assert "expert_review" in r0
    assert r0["expert_review"]["review_mode"] == "MODEL_AWARE"

def test_evidence_hierarchy_levels(phase17_results):
    eb = phase17_results.get("evidence_hierarchy_breakdown", {})
    assert "LEVEL_1_DIRECT_INDEPENDENT_VERIFICATION" in eb
    assert "PENDING_HUMAN_REVIEW" in eb

def test_verification_decision_categories(phase17_results):
    vb = phase17_results.get("verification_breakdown", {})
    assert "verified_count" in vb
    assert "pending_review_count" in vb
    assert vb["plausible_count"] == 0
    assert vb["contradicted_count"] == 0
    assert vb["unverified_count"] == 0
    assert vb["insufficient_evidence_count"] == 0
    total_decisions = vb["verified_count"] + vb["pending_review_count"]
    assert total_decisions == 100

def test_ml_vs_human_performance(phase17_results):
    ml_h = phase17_results.get("ml_vs_human_verified_subset", {})
    assert ml_h["verified_sample_size"] > 0
    assert ml_h["ml_accuracy_pct"] == 100.0

def test_mining_verification_audit(phase17_results):
    m = phase17_results.get("mining_verification_audit", {})
    assert m["mining_candidates_reviewed"] > 0
    assert m["mining_independently_verified_count"] == 0
    assert "No independently verified Mining thermal event was available in the reviewed ambient sample." in m["mandatory_statement"]

def test_industrial_fire_verification_audit(phase17_results):
    ind = phase17_results.get("industrial_fire_verification_audit", {})
    assert ind["industrial_candidates_reviewed"] > 0

def test_inter_rater_status(phase17_results):
    status = phase17_results.get("inter_rater_agreement_status", "")
    assert "Inter-rater agreement could not be established." in status

def test_risk_engine_invariance_and_gate(phase17_results):
    inv = phase17_results.get("risk_engine_invariant", {})
    gate = phase17_results.get("final_gate_decision", {})
    assert inv["risk_service_unaffected"] is True
    assert inv["authoritative_scores_unchanged"] is True
    assert inv["expert_labels_isolated_from_risk_engine"] is True
    assert inv["invariant_percentage"] == 100.0
    assert gate["gate"] == "GATE A — VERIFIED ADVANCE"
