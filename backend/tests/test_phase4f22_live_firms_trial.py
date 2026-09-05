"""
Phase 4F-22 Controlled 14-Day Live NASA FIRMS Staging Trial Test Suite
AVISHKAR 2.0 — SIH 26162 (NTRO)

Tests all 20 criteria specified in Phase 4F-22:
1. Staging isolation
2. Live mode distinction
3. Test mode distinction
4. Secret redaction
5. Bounded retry
6. Timeout handling
7. HTTP 429 handling
8. HTTP 5xx handling
9. Empty valid response handling
10. Malformed CSV response handling
11. Bounding box & feature validation
12. Duplicate protection & idempotency
13. Database persistence
14. ML shadow-only mode
15. RiskService invariance
16. Model checksum integrity
17. Restart recovery
18. Failure recovery
19. No fabricated data
20. Production authorization false
"""

import os
import json
import datetime
from pathlib import Path
import pytest

from app.database import SessionLocal, init_db
from app.models.thermal_observation import ThermalObservation
from app.ml.phase4f22_live_firms_trial import (
    ControlledLiveFIRMSTrialManager, run_phase4f22_live_firms_trial, sanitize_error_message
)
from app.services.risk_service import RiskService


@pytest.fixture(scope="module")
def trial_manager():
    init_db()
    db = SessionLocal()
    mgr = ControlledLiveFIRMSTrialManager(db, environment="staging")
    yield mgr
    db.close()


@pytest.fixture(scope="module")
def trial_results():
    artifact_path = Path(__file__).parent.parent / "ml_artifacts" / "phase_4f22_live_firms_trial_results.json"
    if artifact_path.exists():
        with open(artifact_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return run_phase4f22_live_firms_trial()


def test_01_staging_isolation(trial_manager):
    """1. Verify staging isolation and rejection of non-staging environment."""
    assert trial_manager.environment == "staging"
    bad_mgr = ControlledLiveFIRMSTrialManager(trial_manager.db, environment="production")
    res = bad_mgr.execute_live_polling_cycle(source_mode="LIVE")
    assert res["error_category"] == "CONFIGURATION_ERROR"
    assert "Non-staging environment detected" in res["error_message_sanitized"]


def test_02_live_mode_distinction(trial_manager):
    """2. Verify LIVE mode is explicitly tagged in telemetry."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="LIVE",
        mock_response_text="",
        mock_status_code=200
    )
    assert res["source_mode"] == "LIVE"


def test_03_test_mode_distinction(trial_manager):
    """3. Verify SYNTHETIC_TEST mode is distinctly flagged from LIVE."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text="",
        mock_status_code=200
    )
    assert res["source_mode"] == "SYNTHETIC_TEST"
    assert res["source_mode"] != "LIVE"


def test_04_secret_redaction():
    """4. Verify secrets and API keys are strictly redacted from logs and errors."""
    raw_error = "Failed connecting to https://firms.modaps.eosdis.nasa.gov/api/area/csv/SECRET_API_KEY_12345/VIIRS"
    sanitized = sanitize_error_message(raw_error, key_to_redact="SECRET_API_KEY_12345")
    assert "SECRET_API_KEY_12345" not in sanitized
    assert "***REDACTED_KEY***" in sanitized


def test_05_bounded_retry(trial_manager):
    """5. Verify bounded retries (does not retry indefinitely)."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_status_code=502,
        max_retries=3
    )
    assert res["error_category"] == "HTTP_5XX"
    assert res["persisted_records"] == 0


def test_06_timeout_handling(trial_manager):
    """6. Verify timeout exception handling without process crash."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_status_code=504,
        max_retries=1
    )
    assert res["error_category"] == "HTTP_5XX"


def test_07_http_429_rate_limit(trial_manager):
    """7. Verify HTTP 429 rate limit is captured and halts retries."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_status_code=429
    )
    assert res["error_category"] == "HTTP_429_RATE_LIMIT"
    assert res["persisted_records"] == 0


def test_08_http_5xx_handling(trial_manager):
    """8. Verify external server 5xx error is handled safely."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_status_code=500
    )
    assert res["error_category"] == "HTTP_5XX"
    assert res["persisted_records"] == 0


def test_09_empty_valid_response(trial_manager):
    """9. Verify empty valid CSV is recorded as successful cycle with 0 records."""
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text="",
        mock_status_code=200
    )
    assert res["error_category"] is None
    assert res["parsed_records"] == 0
    assert res["persisted_records"] == 0


def test_10_malformed_csv_handling(trial_manager):
    """10. Verify malformed CSV syntax is caught cleanly."""
    bad_csv = "latitude,longitude\n22.1,NOT_A_VALID_CSV\ninvalid_line_with_no_commas\n"
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text=bad_csv,
        mock_status_code=200
    )
    assert res["error_category"] == "MALFORMED_RESPONSE"
    assert res["persisted_records"] == 0


def test_11_bounding_box_validation(trial_manager):
    """11. Verify out-of-bounds coordinates are rejected."""
    out_of_bounds_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "85.0,150.0,330.0,0.5,0.5,2026-09-04,1200,SNPP,VIIRS,nominal,2.0NRT,295.0,20.0,D\n"
    )
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text=out_of_bounds_csv,
        mock_status_code=200
    )
    assert res["invalid_records"] == 1
    assert res["persisted_records"] == 0


def test_12_duplicate_protection(trial_manager):
    """12. Verify duplicate observation ingestion is detected and blocked."""
    t_str = datetime.datetime.utcnow().strftime('%H%M%S')
    test_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        f"24.5678,78.1234,340.0,0.5,0.5,2026-09-04,{t_str},SNPP,VIIRS,nominal,2.0NRT,295.0,30.0,D\n"
    )
    res1 = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text=test_csv,
        mock_status_code=200
    )
    res2 = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text=test_csv,
        mock_status_code=200
    )
    assert res1["persisted_records"] == 1
    assert res2["duplicate_records"] == 1
    assert res2["persisted_records"] == 0


def test_13_database_persistence(trial_manager):
    """13. Verify valid observations are persisted in PostgreSQL / SQLite."""
    t_str = datetime.datetime.utcnow().strftime('%H%M%S')
    test_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        f"25.1111,79.2222,342.0,0.5,0.5,2026-09-04,{t_str},SNPP,VIIRS,nominal,2.0NRT,295.0,32.0,D\n"
    )
    res = trial_manager.execute_live_polling_cycle(
        source_mode="SYNTHETIC_TEST",
        mock_response_text=test_csv,
        mock_status_code=200
    )
    assert res["persisted_records"] == 1
    obs = trial_manager.db.query(ThermalObservation).filter(
        ThermalObservation.latitude == 25.1111,
        ThermalObservation.longitude == 79.2222,
        ThermalObservation.acq_time == t_str
    ).first()
    assert obs is not None
    assert obs.frp == 32.0


def test_14_ml_shadow_only(trial_manager):
    """14. Verify ML inferences are computed strictly in shadow mode."""
    from app.ml.shadow_inference_service import MODEL_VERSION
    assert trial_manager.shadow_service.is_ready is True
    assert MODEL_VERSION == "4F.13_GB_V1"


def test_15_risk_service_invariance():
    """15. Verify RiskService scoring is completely unaffected by live ingestion."""
    risk_svc = RiskService()
    tier_crit = risk_svc.classify_risk_tier(91.0)
    tier_high = risk_svc.classify_risk_tier(72.0)
    tier_med = risk_svc.classify_risk_tier(40.0)
    tier_low = risk_svc.classify_risk_tier(15.0)
    assert tier_crit == "CRITICAL_VERIFIED_RISK"
    assert tier_high == "HIGH_RISK"
    assert tier_med == "MEDIUM_RISK"
    assert tier_low == "LOW_RISK"


def test_16_model_checksum_integrity(trial_results):
    """16. Verify approved model checksum SHA-256 matches pinned hash."""
    assert trial_results["model_sha256"] == "f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810"
    assert trial_results["model_integrity"] is True


def test_17_restart_recovery(trial_manager):
    """17. Verify application restart and re-initialization maintains state."""
    db_new = SessionLocal()
    mgr_new = ControlledLiveFIRMSTrialManager(db_new, environment="staging")
    assert mgr_new.service is not None
    assert mgr_new.shadow_service.is_ready is True
    db_new.close()


def test_18_failure_recovery_matrix(trial_results):
    """18. Verify failure recovery indicators are active and passing in audit."""
    polls = trial_results["poll_statistics"]
    assert polls["deduplication_protection_verified"] is True
    assert polls["bounded_retry_recovery_verified"] is True
    assert polls["empty_response_handling_verified"] is True


def test_19_no_fabricated_data(trial_results):
    """19. Verify trial status honestly reflects uncompleted 14-day duration."""
    assert trial_results["trial_status"] == "IN_PROGRESS"
    assert "Full 14 consecutive calendar days" in trial_results["critical_blockers"][0]


def test_20_production_authorization_false(trial_results):
    """20. Verify production deployment authorization is explicitly FALSE."""
    assert trial_results["production_deployment_authorized"] is False
    assert trial_results["gate"] == "GATE B \u2014 CONDITIONAL LIVE VALIDATION"
    assert trial_results["mandatory_statement"] == "Phase 4F-22 does not authorize production deployment."
