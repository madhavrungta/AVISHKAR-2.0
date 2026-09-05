"""
AVISHKAR 2.0 — Phase 4F-19: Automated Test Suite for Staging Deployment & Operational Readiness
"""

import os
import json
import pytest
from app.ml.phase4f19_staging_readiness import run_phase4f19_staging_readiness

ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_artifacts"))
RESULTS_FILE = os.path.join(ARTIFACT_DIR, "phase_4f19_staging_readiness_results.json")

@pytest.fixture(scope="module")
def staging_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return run_phase4f19_staging_readiness()

def test_1_staging_environment_detection(staging_results):
    env_info = staging_results.get("environment_separation", {})
    assert env_info.get("staging_isolation_status") == "STAGING-VERIFIED"
    assert env_info.get("database_url_safe") is True

def test_2_health_readiness(staging_results):
    api = staging_results.get("api_readiness", {})
    assert "/health" in api.get("endpoints_tested", [])
    assert api["details"]["/health"]["passed"] is True

def test_3_database_connectivity(staging_results):
    db_info = staging_results.get("database_readiness", {})
    assert db_info.get("connected") is True
    assert db_info.get("status") == "DATABASE_READY"

def test_4_schema_readiness(staging_results):
    db_info = staging_results.get("database_readiness", {})
    assert db_info.get("schema_initialized") is True
    assert len(db_info.get("tables_verified", [])) >= 3

def test_5_model_artifact_existence(staging_results):
    m = staging_results.get("model_integrity", {})
    assert m.get("file_exists") is True
    assert os.path.exists(m.get("artifact_path", ""))

def test_6_model_version_integrity(staging_results):
    m = staging_results.get("model_integrity", {})
    assert m.get("model_version") == "4F.13_GB_V1"
    assert m.get("approved_version") == "4F.13_GB_V1"
    assert m.get("status") == "MODEL_INTEGRITY_PASS"

def test_7_model_checksum(staging_results):
    m = staging_results.get("model_integrity", {})
    sha = m.get("sha256_checksum", "")
    assert len(sha) == 64
    assert sha != "FILE_NOT_FOUND"

def test_8_shadow_only_mode(staging_results):
    shadow = staging_results.get("shadow_mode_isolation", {})
    assert shadow.get("shadow_mode_flag") == "SHADOW_ONLY"

def test_9_probability_validity(staging_results):
    perf = staging_results.get("performance_metrics", {})
    assert perf.get("status") == "PERFORMANCE_PASS"

def test_10_firms_configuration(staging_results):
    firms = staging_results.get("firms_readiness", {})
    assert firms.get("configuration_status") == "CONFIGURATION-VERIFIED"
    assert firms.get("fallback_logic_present") is True

def test_11_api_readiness(staging_results):
    api = staging_results.get("api_readiness", {})
    assert api.get("status") == "API_READY"
    assert api.get("endpoints_passed_count") == api.get("total_endpoints_tested")

def test_12_risk_service_invariance(staging_results):
    shadow = staging_results.get("shadow_mode_isolation", {})
    assert shadow.get("risk_invariance_passed") is True
    assert shadow.get("status") == "RISK_INVARIANCE_PASS"

def test_13_monitoring_initialization(staging_results):
    assert staging_results.get("observability_status") == "PHASE_4F18_MONITORING_INTEGRATED"

def test_14_configuration_safety(staging_results):
    sec = staging_results.get("security_audit", {})
    assert sec.get("status") == "SECURITY_CONFIG_PASS"
    assert sec.get("secrets_in_code") == "NONE_DETECTED"

def test_15_no_synthetic_operational_data(staging_results):
    ds = staging_results.get("data_safety", {})
    assert ds.get("synthetic_operational_data") is False
    assert ds.get("authoritative_data_intact") is True

def test_16_pending_human_review_preservation(staging_results):
    ds = staging_results.get("data_safety", {})
    assert ds.get("pending_review_preservation") is True

def test_17_safe_failure_behavior(staging_results):
    api = staging_results.get("api_readiness", {})
    assert api.get("error_handling_safe") is True

def test_18_restart_recovery_assumptions(staging_results):
    rec = staging_results.get("rollback_and_recovery", {})
    assert rec.get("status") == "ROLLBACK_READY"
    assert rec.get("rollback_procedure") == "MANUAL_ROLLBACK_PROCEDURE_DOCUMENTED"

def test_19_frontend_backend_compatibility(staging_results):
    env_info = staging_results.get("environment_separation", {})
    assert len(env_info.get("cors_origins_configured", [])) > 0

def test_20_staging_isolation(staging_results):
    prod_auth = staging_results.get("production_authorization", {})
    assert prod_auth.get("status") == "NOT_AUTHORIZED_BY_PHASE_4F_19"
    assert staging_results.get("final_gate_decision", {}).get("gate") == "GATE A — STAGING READY"
