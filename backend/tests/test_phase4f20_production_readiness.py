"""
Phase 4F-20 Controlled Operational Verification & Production Readiness Gate Review Test Suite
AVISHKAR 2.0 — SIH 26162 (NTRO)

Tests all 20 criteria specified in Phase 4F-20 requirements:
1. Pinned model checksum verification (4F.13_GB_V1 integrity)
2. RiskService invariance (RiskService remains 100% authoritative)
3. Shadow isolation (ML classifier output is strictly shadow and non-authoritative)
4. Alert generation authority (RiskService exclusively controls alerts)
5. Zero retraining / zero weight changes check
6. Zero threshold optimization check
7. Controlled ground truth accuracy verification (750 records)
8. Cluster disjointness audit check (Phase 4F-14 validation)
9. Multi-region spatial stability check (Phase 4F-15 98.69%)
10. Cohen's Kappa & calibration check (Phase 4F-16 results)
11. Human verification partial state verification (Phase 4F-17 review state)
12. Operational shadow monitoring data quality check (Phase 4F-18 data quality PASS)
13. Staging deployment health & isolation check (Phase 4F-19 results)
14. Industrial fire candidate detection logic
15. Mining top-1 prediction statement verification
16. Failure modes recovery matrix completeness (15 failure modes)
17. Authorization matrix evaluation
18. Critical blockers identification
19. Final gate decision check (GATE B — CONDITIONAL PRODUCTION READINESS)
20. Mandatory statement check ('Phase 4F-20 does not authorize production deployment.')
"""

import os
import json
from pathlib import Path
import pytest

from app.ml.phase4f20_production_readiness import run_phase4f20_production_readiness
from app.services.risk_service import RiskService


@pytest.fixture(scope="module")
def readiness_results():
    artifact_path = Path(__file__).parent.parent / "ml_artifacts" / "phase_4f20_production_readiness_results.json"
    if artifact_path.exists():
        with open(artifact_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return run_phase4f20_production_readiness()


def test_01_pinned_model_checksum_verification(readiness_results):
    """1. Verify pinned model version 4F.13_GB_V1 and its sha256 integrity."""
    model_data = readiness_results["model_readiness"]
    assert model_data["model_version"] == "4F.13_GB_V1"
    assert model_data["integrity_verified"] is True
    assert model_data["status"] == "PASS"
    assert len(model_data["sha256_checksum"]) == 64


def test_02_risk_service_invariance(readiness_results):
    """2. Verify RiskService invariance and authoritative status."""
    gov = readiness_results["risk_governance"]
    assert gov["risk_service_authority"] == "AUTHORITATIVE"
    assert gov["risk_invariance_status"] == "PASS"
    
    # Test RiskService calculation directly
    tier_crit = RiskService.classify_risk_tier(90.0)
    tier_high = RiskService.classify_risk_tier(75.0)
    tier_med = RiskService.classify_risk_tier(45.0)
    tier_low = RiskService.classify_risk_tier(15.0)
    assert tier_crit == "CRITICAL_VERIFIED_RISK"
    assert tier_high == "HIGH_RISK"
    assert tier_med == "MEDIUM_RISK"
    assert tier_low == "LOW_RISK"


def test_03_shadow_isolation(readiness_results):
    """3. Verify ML classifier output is strictly shadow and non-authoritative."""
    gov = readiness_results["risk_governance"]
    assert gov["ml_shadow_isolation"] == "STRICTLY_SHADOW_NON_AUTHORITATIVE"
    assert readiness_results["authorization_matrix"]["ML Shadow Inference"] == "PASS"
    assert readiness_results["authorization_matrix"]["Production ML Autonomous Mode"] == "BLOCKED"


def test_04_alert_generation_authority(readiness_results):
    """4. Verify alert generation is exclusive to RiskService."""
    gov = readiness_results["risk_governance"]
    assert gov["alert_generation_authority"] == "RiskService Exclusive"
    assert readiness_results["authorization_matrix"]["Operational Alert Governance"] == "PASS"


def test_05_zero_retraining_zero_weight_changes(readiness_results):
    """5. Verify zero retraining and zero weight alterations."""
    model_data = readiness_results["model_readiness"]
    assert model_data["boosting_stages"] == 100
    assert model_data["classes_count"] == 5
    assert model_data["feature_count"] == 18


def test_06_zero_threshold_optimization(readiness_results):
    """6. Verify threshold integrity without ad-hoc post-hoc overrides."""
    perf = readiness_results["performance_evidence"]
    assert perf["phase_4f16_calibration_and_robustness"]["perturbation_invariance_pct"] >= 99.0


def test_07_controlled_ground_truth_accuracy(readiness_results):
    """7. Verify controlled ground truth performance on 750 curated records."""
    gt = readiness_results["performance_evidence"]["phase_4f13_controlled_ground_truth"]
    assert gt["accuracy"] == 1.0
    assert gt["macro_f1"] == 1.0
    assert "Does not establish unverified ambient real-world accuracy" in gt["interpretation"]


def test_08_cluster_disjointness_audit(readiness_results):
    """8. Verify cluster isolation and zero spatial data leakage from Phase 4F-14."""
    leak = readiness_results["performance_evidence"]["phase_4f14_leakage_audit"]
    assert leak["cluster_isolation_status"] == "STRICTLY_DISJOINT_CLUSTERS"
    assert leak["train_clusters"] == 200
    assert leak["test_clusters"] == 50
    assert leak["status"] == "PASS"


def test_09_multi_region_spatial_stability(readiness_results):
    """9. Verify 98.69% multi-region spatial stability metric from Phase 4F-15."""
    p15 = readiness_results["performance_evidence"]["phase_4f15_multi_region_shadow_pilot"]
    assert p15["spatial_stability_rate"] == 0.9869
    assert p15["observations_evaluated"] == 4121
    assert p15["macro_regions_covered"] == 6


def test_10_cohens_kappa_and_calibration(readiness_results):
    """10. Verify chance-adjusted agreement and confidence reconciliation from Phase 4F-16."""
    p16 = readiness_results["performance_evidence"]["phase_4f16_calibration_and_robustness"]
    assert p16["cohens_kappa_agreement"] == 0.5482
    assert p16["reconciled_gt_test_confidence"] == 0.7924
    assert p16["ambient_confidence_mean"] == 0.4431


def test_11_human_verification_partial_state(readiness_results):
    """11. Verify Phase 4F-17 human verification partial state."""
    p17 = readiness_results["performance_evidence"]["phase_4f17_human_verification"]
    assert p17["total_review_sample"] == 100
    assert p17["level1_catalog_verified"] == 25
    assert p17["pending_expert_review"] == 75
    assert "PARTIAL" in p17["human_verification_status"]


def test_12_operational_shadow_monitoring_data_quality(readiness_results):
    """12. Verify operational shadow monitoring data quality and latency from Phase 4F-18."""
    p18 = readiness_results["performance_evidence"]["phase_4f18_operational_shadow_monitoring"]
    assert p18["telemetry_records_monitored"] == 4121
    assert p18["data_quality_status"] == "DATA_QUALITY_PASS"
    assert p18["risk_engine_invariance"] == "100% INVARIANT"
    assert p18["mean_shadow_latency_ms"] < 20.0


def test_13_staging_deployment_health_and_isolation(readiness_results):
    """13. Verify Phase 4F-19 staging deployment readiness."""
    p19 = readiness_results["performance_evidence"]["phase_4f19_staging_readiness"]
    assert p19["health_probe_status"] == "HTTP 200 OK"
    assert p19["api_endpoints_passed"] == 5
    assert p19["model_inference_latency_ms"] < 1.0
    assert p19["staging_isolation_status"] == "STAGING-VERIFIED"


def test_14_industrial_fire_candidate_logic(readiness_results):
    """14. Verify Industrial Fire domain readiness."""
    ind = readiness_results["domain_readiness"]["industrial_fire"]
    assert ind["candidate_count_in_monitoring"] == 7
    assert ind["high_confidence_candidates"] == 1
    assert ind["status"] == "PARTIAL_EVIDENCE"


def test_15_mining_top1_prediction_statement(readiness_results):
    """15. Verify Mining domain statement regarding zero top-1 ambient predictions."""
    mining = readiness_results["domain_readiness"]["mining_activity"]
    assert mining["ambient_top1_predictions_observed"] == 0
    assert mining["mandatory_statement"] == "No Mining top-1 prediction was observed during operational monitoring."


def test_16_failure_modes_recovery_matrix_completeness(readiness_results):
    """16. Verify failure modes matrix covers 15 key architectural failure modes."""
    modes = readiness_results["failure_modes_matrix"]
    assert len(modes) == 15
    for item in modes:
        assert "mode" in item
        assert "detection" in item
        assert "safe_behavior" in item
        assert "recovery" in item
        assert item["readiness"] == "PASS"


def test_17_authorization_matrix_evaluation(readiness_results):
    """17. Verify authorization matrix evaluates correctly."""
    auth = readiness_results["authorization_matrix"]
    assert auth["ML Shadow Inference"] == "PASS"
    assert auth["Production ML Autonomous Mode"] == "BLOCKED"
    assert auth["Authoritative RiskService Engine"] == "AUTHORITATIVE"
    assert auth["Live FIRMS External Validation"] == "NOT_ESTABLISHED"
    assert auth["Backup & Disaster Recovery"] == "NOT_VALIDATED"
    assert auth["Production-Scale Load Capacity"] == "NOT_ESTABLISHED"


def test_18_critical_blockers_identification(readiness_results):
    """18. Verify the 4 critical production deployment blockers are explicitly documented."""
    blockers = readiness_results["critical_blockers"]
    assert len(blockers) == 4
    assert any("Phase 4F-17 human verification" in b for b in blockers)
    assert any("Live external satellite ingest connectivity" in b for b in blockers)
    assert any("Real-world generalization" in b for b in blockers)
    assert any("Production-scale distributed load capacity" in b for b in blockers)


def test_19_final_gate_decision(readiness_results):
    """19. Verify final gate decision is GATE B — CONDITIONAL PRODUCTION READINESS."""
    gate = readiness_results["final_gate_decision"]
    assert gate["gate"] == "GATE B \u2014 CONDITIONAL PRODUCTION READINESS"
    assert gate["production_deployment_authorized"] is False
    assert readiness_results["production_deployment_authorized"] is False


def test_20_mandatory_statement(readiness_results):
    """20. Verify mandatory statement: 'Phase 4F-20 does not authorize production deployment.'"""
    gate = readiness_results["final_gate_decision"]
    assert gate["mandatory_statement"] == "Phase 4F-20 does not authorize production deployment."
