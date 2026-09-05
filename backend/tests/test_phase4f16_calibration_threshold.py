"""
AVISHKAR 2.0 — Phase 4F-16: Automated Test Suite for Calibration, Threshold Selection & Regional Robustness
"""

import os
import json
import pytest
from app.ml.phase4f16_calibration_threshold import run_phase4f16_calibration_threshold_pilot

ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_artifacts"))
RESULTS_FILE = os.path.join(ARTIFACT_DIR, "phase_4f16_calibration_threshold_results.json")

@pytest.fixture(scope="module")
def phase16_results():
    if not os.path.exists(RESULTS_FILE):
        return run_phase4f16_calibration_threshold_pilot()
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def test_confidence_discrepancy_reconciliation(phase16_results):
    recon = phase16_results.get("confidence_reconciliation", {})
    assert "reconciliation_table" in recon
    tbl = recon["reconciliation_table"]
    assert len(tbl) == 4
    assert tbl[0]["mean_top1_confidence"] == 0.7924  # Test set
    assert tbl[1]["mean_top1_confidence"] == 0.9831  # Train set
    assert tbl[3]["mean_top1_confidence"] == 0.4431  # Ambient DB

def test_spatial_stability_reproduction(phase16_results):
    stab = phase16_results.get("spatial_stability_audit", {})
    assert stab["reproduced_spatial_stability_pct"] == 98.69
    assert stab["total_candidate_pairs_checked"] == 2824
    assert stab["stable_class_pairs"] == 2787
    assert stab["unstable_class_flips"] == 37

def test_cohens_kappa_agreement(phase16_results):
    ag = phase16_results.get("cohens_kappa_agreement_analysis", {})
    assert ag["raw_agreement_pct"] > 80.0
    assert ag["cohens_kappa_overall"] >= 0.50
    assert "confusion_matrix_ml_rows_heuristic_cols" in ag
    assert len(ag["regional_agreement_and_kappa"]) >= 5

def test_regional_and_temporal_robustness(phase16_results):
    reg = phase16_results.get("regional_robustness", {})
    temp = phase16_results.get("temporal_robustness", {})
    assert reg["regions_evaluated"] == 6
    assert len(temp["temporal_windows"]) == 3

def test_sensitivity_analysis(phase16_results):
    sens = phase16_results.get("sensitivity_analysis", {})
    inv = sens["distance_perturbation_plus_20_pct"]["prediction_invariance_pct"]
    assert inv >= 99.0

def test_mining_generalization_and_candidates(phase16_results):
    m_data = phase16_results.get("mining_analysis", {})
    assert m_data["mining_top1_predictions_count"] == 0
    assert len(m_data["top_20_mining_candidates"]) == 20
    assert "No ambient observation in the evaluated dataset strongly matched the learned Mining signature." in m_data["mandatory_language_finding"]

def test_calibration_vs_confidence_distinction(phase16_results):
    cal = phase16_results.get("calibration_vs_confidence", {})
    assert cal["verified_ground_truth_metrics"]["brier_score"] == 0.0385
    assert cal["verified_ground_truth_metrics"]["ece_expected_calibration_error"] == 0.0210
    assert cal["mandatory_disclaimer"] == "Ambient confidence is not equivalent to verified calibration."

def test_offline_threshold_matrix(phase16_results):
    th = phase16_results.get("threshold_analysis", {})
    assert len(th["evaluated_thresholds"]) == 8
    assert len(th["ambient_observations_threshold_matrix"]) == 8
    assert th["recommended_prioritization_thresholds"]["high_priority_candidate_cutoff"] == 0.85

def test_risk_engine_invariance(phase16_results):
    inv = phase16_results.get("risk_engine_invariant", {})
    assert inv["risk_service_unaffected"] is True
    assert inv["authoritative_scores_unchanged"] is True
    assert inv["shadow_mode_isolation_verified"] is True
    assert inv["invariant_percentage"] == 100.0

def test_gate_decision(phase16_results):
    gate = phase16_results.get("final_gate_decision", {})
    assert gate["gate"] == "GATE A — ADVANCE TO CONTROLLED HUMAN VERIFICATION"
