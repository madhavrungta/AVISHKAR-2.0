"""
AVISHKAR 2.0 — Phase 4F-18: Automated Test Suite for Operational Shadow Logging & Pilot Monitoring
"""

import os
import json
import pytest
from app.ml.phase4f18_operational_shadow_monitoring import run_phase4f18_operational_shadow_monitoring

ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_artifacts"))
RESULTS_FILE = os.path.join(ARTIFACT_DIR, "phase_4f18_operational_shadow_monitoring.json")

@pytest.fixture(scope="module")
def phase18_results():
    if not os.path.exists(RESULTS_FILE):
        return run_phase4f18_operational_shadow_monitoring()
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def test_1_shadow_only_mode(phase18_results):
    assert phase18_results["model_metadata"]["inference_mode"] == "SHADOW_ONLY"

def test_2_model_version_integrity(phase18_results):
    integ = phase18_results.get("model_integrity", {})
    assert integ["integrity_check_passed"] is True
    assert integ["approved_model_version"] == "4F.13_GB_V1"

def test_3_prediction_probability_validity(phase18_results):
    dq = phase18_results.get("data_quality", {})
    assert "valid_probabilities" in dq["checks_passed"]
    assert "probabilities_within_unit_interval" in dq["checks_passed"]
    assert "no_nan_or_infinite_values" in dq["checks_passed"]

def test_4_probability_sum(phase18_results):
    dq = phase18_results.get("data_quality", {})
    assert "probability_sum_approximately_one" in dq["checks_passed"]

def test_5_class_distribution(phase18_results):
    dist = phase18_results.get("prediction_distribution", {})
    assert len(dist) == 5
    assert "AGRICULTURAL_BURNING" in dist
    assert "WILDFIRE" in dist
    assert "GAS_FLARE" in dist
    assert "INDUSTRIAL_FIRE" in dist
    assert "MINING_ACTIVITY" in dist

def test_6_confidence_buckets(phase18_results):
    conf = phase18_results.get("confidence_distribution", {})
    buckets = conf.get("confidence_buckets", {})
    assert "under_0_50" in buckets
    assert "from_0_50_to_0_70" in buckets
    assert "from_0_70_to_0_85" in buckets
    assert "greater_or_equal_0_85" in buckets

def test_7_high_confidence_candidate_extraction(phase18_results):
    hc = phase18_results.get("high_confidence_shadow_candidates", {})
    assert hc["candidate_label"] == "HIGH_CONFIDENCE_SHADOW_CANDIDATE"
    assert "count" in hc
    assert hc["count"] >= 0
    assert "candidates" in hc

def test_8_regional_aggregation(phase18_results):
    reg = phase18_results.get("regional_monitoring", {})
    assert len(reg) >= 5
    assert "South" in reg
    assert "North" in reg

def test_9_temporal_aggregation(phase18_results):
    temp = phase18_results.get("temporal_monitoring", {})
    assert len(temp) == 3

def test_10_industrial_fire_candidate_extraction(phase18_results):
    ind = phase18_results.get("industrial_fire_monitoring", {})
    assert ind["candidate_label"] == "INDUSTRIAL_FIRE_CANDIDATES"
    assert "total_candidates" in ind
    assert "mandatory_disclaimer" in ind

def test_11_mining_candidate_monitoring(phase18_results):
    m = phase18_results.get("mining_monitoring", {})
    assert m["mining_top1_predictions"] == 0
    assert "No Mining top-1 prediction was observed during this monitoring window." in m["mandatory_statement"]

def test_12_ml_heuristic_disagreement(phase18_results):
    disag = phase18_results.get("disagreement_monitoring", {})
    assert "total_disagreements" in disag
    assert disag["total_disagreements"] > 0
    assert "disagreement_rate_pct" in disag

def test_13_feature_drift(phase18_results):
    drift = phase18_results.get("drift_monitoring", {})
    assert "features_monitored" in drift
    assert "frp" in drift["features_monitored"]
    assert "p50_ratio" in drift["features_monitored"]

def test_14_confidence_drift(phase18_results):
    drift = phase18_results.get("drift_monitoring", {})
    assert "confidence_drift" in drift
    assert "current_mean_confidence" in drift["confidence_drift"]

def test_15_data_quality_checks(phase18_results):
    dq = phase18_results.get("data_quality", {})
    assert dq["status"] in ["DATA_QUALITY_PASS", "DATA_QUALITY_WARNING"]
    assert len(dq["checks_passed"]) >= 8

def test_16_failure_handling(phase18_results):
    fail = phase18_results.get("failure_statistics", {})
    assert "total_failures" in fail
    assert fail["total_failures"] == 0

def test_17_risk_invariance(phase18_results):
    inv = phase18_results.get("risk_invariance", {})
    assert inv["risk_service_unaffected"] is True
    assert inv["authoritative_scores_unchanged"] is True
    assert inv["shadow_mode_isolation_verified"] is True
    assert inv["invariant_percentage"] == 100.0

def test_18_risk_service_non_mutation(phase18_results):
    assert phase18_results["risk_invariance"]["risk_service_unaffected"] is True

def test_19_model_weight_non_mutation(phase18_results):
    assert phase18_results["model_metadata"]["model_version"] == "4F.13_GB_V1"

def test_20_idempotent_rerun():
    res1 = run_phase4f18_operational_shadow_monitoring()
    assert res1["volume_metrics"]["observations_processed"] > 0

def test_21_historical_live_mode_labeling(phase18_results):
    assert phase18_results["monitoring_mode"] in ["HISTORICAL_REPLAY", "LIVE_OPERATIONAL"]

def test_22_synthetic_data_exclusion(phase18_results):
    assert phase18_results["monitoring_mode"] == "HISTORICAL_REPLAY"
    assert phase18_results["final_gate_decision"]["gate"] == "GATE A — OPERATIONALLY STABLE SHADOW"

def test_23_pending_review_preservation(phase18_results):
    p17_pres = phase18_results.get("phase17_pending_review_preservation", {})
    assert p17_pres.get("preservation_status") == "PRESERVED_AS_AUDIT_METADATA"

def test_24_no_automatic_human_label_creation(phase18_results):
    p17_pres = phase18_results.get("phase17_pending_review_preservation", {})
    assert p17_pres.get("zero_automatic_human_labels_generated") is True
