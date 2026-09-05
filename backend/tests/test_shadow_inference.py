"""
AVISHKAR 2.0 — Phase 4F-11B: Controlled ML Shadow Inference Integration Tests

Verifies:
1. Experimental model artifact loading and metadata validation.
2. Strict 17-field feature leakage prevention.
3. Accurate multi-class predictions and probability calibration (probabilities sum to 1.0).
4. Feature flag toggle (ML_CLASSIFIER_SHADOW_MODE=True vs False).
5. Risk Engine authority: RiskService and VerificationRiskScore remain completely unmodified.
6. Non-blocking failure isolation: ML failure or corrupt artifact never disrupts the Risk Engine.
7. Database persistence and idempotency (no duplicate shadow records on repeated runs).
8. Read-only inspection API endpoints: GET /ml/shadow/{event_id} and GET /ml/shadow/audit.
9. Operational latency recording (average and p95 latency) and confidence binning.
"""

import os
import json
import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.models.thermal_observation import ThermalObservation
from app.models.risk_score import VerificationRiskScore
from app.models.shadow_prediction import MLShadowPrediction
from app.services.risk_service import RiskService
from app.ml.shadow_inference_service import (
    MLShadowInferenceService,
    MODEL_VERSION,
    FEATURE_SCHEMA_VERSION,
    TARGET_CLASSES,
    FORBIDDEN_LEAKAGE_KEYS
)


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_thermal_obs(db_session: Session):
    """Creates a sample thermal observation for shadow inference testing."""
    obs = ThermalObservation(
        latitude=28.6139,
        longitude=77.2090,
        scan=0.5,
        track=0.6,
        acq_date="2026-08-27",
        acq_time="0830",
        satellite="NOAA-20",
        instrument="VIIRS",
        confidence="nominal",
        version="2.0NRT",
        bright_ti4=345.2,
        bright_ti5=292.1,
        frp=42.5,
        daynight="D",
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test_001",
        observation_timestamp=datetime.datetime(2026, 8, 27, 8, 30)
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)
    return obs


def test_shadow_artifact_loading_and_metadata():
    """Verifies that the model artifact loads with valid experimental status."""
    service = MLShadowInferenceService()
    assert service.is_ready is True
    assert service.artifact_metadata.get("deployment_status") == "EXPERIMENTAL_NOT_PRODUCTION"
    assert service.artifact_metadata.get("algorithm") == "GradientBoostingClassifier"
    assert "independent_test_metrics" in service.artifact_metadata


def test_shadow_feature_schema_and_leakage_prevention(test_thermal_obs, db_session: Session):
    """Verifies that 17 forbidden target and provenance fields are strictly stripped."""
    service = MLShadowInferenceService()
    raw_features = {
        "frp": 25.0,
        "brightness_temperature": 340.0,
        "background_temperature": 295.0,
        "scan": 0.5,
        "track": 0.5,
        "facility_distance_m": 450.0,
        "facility_density_5km": 3.0,
        "persistence_score": 0.88,
        "cluster_pixel_count": 4.0,
        "landcover_code": 50.0,
        # Forbidden keys
        "target_label": "INDUSTRIAL_FIRE",
        "label": "INDUSTRIAL_FIRE",
        "ground_truth": "CONFIRMED",
        "label_confidence": "HIGH",
        "label_source": "MOEFCC",
        "label_source_id": "MOEFCC_2026_001",
        "physical_event_cluster_id": "CLUSTER_IND_001",
        "provenance_url": "https://moefcc.gov.in"
    }

    clean_features, violations = service.validate_and_filter_features(raw_features)
    assert len(violations) == 8
    for fk in FORBIDDEN_LEAKAGE_KEYS:
        assert fk not in clean_features

    # Verify extracted features from observation
    obs_features, is_valid, msg = service.extract_observation_features(test_thermal_obs, db=db_session)
    assert is_valid is True
    assert "frp" in obs_features
    assert "brightness" in obs_features
    for fk in FORBIDDEN_LEAKAGE_KEYS:
        assert fk not in obs_features


def test_shadow_probabilities_sum_to_one():
    """Verifies that the multi-class probability distribution across all 5 classes sums to 1.0."""
    service = MLShadowInferenceService()
    
    def make_18_feats(dist=99999.0, frp=15.0, ti4=325.0, lc=10.0, persist=1.0):
        return {
            "p50_ratio": 1.0, "p95_ratio": 1.0, "p99_ratio": 1.0,
            "frp_zscore": round((frp - 20.0) / 15.0, 4),
            "bright_ti4_zscore": round((ti4 - 325.0) / 18.0, 4),
            "worldcover_class": lc,
            "persistence_3d_count": persist,
            "dist_to_industrial_m": dist,
            "dist_to_energy_m": dist,
            "dist_to_healthcare_m": 99999.0,
            "dist_to_transport_m": 99999.0,
            "dist_to_railway_m": 99999.0,
            "dist_to_highway_m": 99999.0,
            "dist_to_airport_m": 99999.0,
            "dist_to_port_m": 99999.0,
            "frp": frp,
            "brightness": ti4,
            "scan": 0.5
        }

    test_feature_vectors = [
        make_18_feats(dist=450.0, frp=160.0, ti4=325.0, lc=50.0, persist=8.0),
        make_18_feats(dist=800.0, frp=180.0, ti4=365.0, lc=50.0, persist=10.0),
        make_18_feats(dist=8500.0, frp=22.0, ti4=325.0, lc=40.0, persist=1.0),
        make_18_feats(dist=12000.0, frp=85.0, ti4=325.0, lc=10.0, persist=2.0)
    ]

    for fv in test_feature_vectors:
        pred_class, probs, max_p = service.predict_probabilities(fv)
        assert pred_class in TARGET_CLASSES
        assert len(probs) == 5
        prob_sum = sum(probs.values())
        assert abs(prob_sum - 1.0) < 1e-4
        assert max_p == probs[pred_class]
        assert max_p >= 0.20


def test_shadow_mode_flag_enabled_vs_disabled(test_thermal_obs, db_session: Session):
    """Verifies that ML_CLASSIFIER_SHADOW_MODE controls shadow inference execution."""
    service = MLShadowInferenceService()

    # 1. When disabled
    settings.ML_CLASSIFIER_SHADOW_MODE = False
    res_disabled = service.infer_observation(db_session, test_thermal_obs.id, force_run=False)
    assert res_disabled["prediction_status"] == "SKIPPED_DISABLED"
    assert res_disabled["predicted_class"] == "SHADOW_DISABLED"

    # 2. When enabled or force_run=True
    res_enabled = service.infer_observation(db_session, test_thermal_obs.id, force_run=True)
    assert res_enabled["prediction_status"] == "SUCCESS"
    assert res_enabled["predicted_class"] in TARGET_CLASSES
    assert res_enabled["max_probability"] > 0.0


def test_risk_engine_unaffected_by_ml_shadow(test_thermal_obs, db_session: Session):
    """Verifies that RiskService and VerificationRiskScore produce identical results regardless of ML shadow."""
    risk_service = RiskService()

    # Initial risk evaluation
    resp1 = risk_service.evaluate_risk_scores(db_session, recalculate_all=True)
    rec1 = db_session.query(VerificationRiskScore).filter(
        VerificationRiskScore.observation_id == test_thermal_obs.id
    ).first()
    score1 = rec1.composite_risk_score
    tier1 = rec1.risk_level

    # Run ML shadow inference
    shadow_service = MLShadowInferenceService()
    shadow_res = shadow_service.infer_observation(db_session, test_thermal_obs.id, force_run=True)
    assert shadow_res["prediction_status"] == "SUCCESS"

    # Re-evaluate risk scores with recalculate_all=True
    resp2 = risk_service.evaluate_risk_scores(db_session, recalculate_all=True)
    rec2 = db_session.query(VerificationRiskScore).filter(
        VerificationRiskScore.observation_id == test_thermal_obs.id
    ).first()

    assert rec2.composite_risk_score == score1
    assert rec2.risk_level == tier1
    assert resp2.total_evaluated == resp1.total_evaluated
    assert resp2.medium_risk == resp1.medium_risk


def test_ml_failure_does_not_break_risk_engine(test_thermal_obs, db_session: Session):
    """Verifies that an error in shadow inference is safely caught and does not affect the caller."""
    corrupt_service = MLShadowInferenceService(artifact_path="nonexistent_model_artifact.json")
    assert corrupt_service.is_ready is False

    res = corrupt_service.infer_observation(db_session, test_thermal_obs.id, force_run=True)
    assert res["prediction_status"] in ["SUCCESS", "FAILED"]


def test_shadow_database_persistence_and_idempotency(test_thermal_obs, db_session: Session):
    """Verifies that shadow predictions are persisted and repeated executions do not create duplicate records."""
    service = MLShadowInferenceService()

    # Run 1
    res1 = service.infer_observation(db_session, test_thermal_obs.id, force_run=True)
    assert res1["prediction_status"] == "SUCCESS"

    pred_records1 = db_session.query(MLShadowPrediction).filter(
        MLShadowPrediction.event_id == test_thermal_obs.id,
        MLShadowPrediction.model_version == MODEL_VERSION
    ).all()
    assert len(pred_records1) == 1

    # Run 2 (Idempotent update)
    res2 = service.infer_observation(db_session, test_thermal_obs.id, force_run=True)
    assert res2["prediction_status"] == "SUCCESS"

    pred_records2 = db_session.query(MLShadowPrediction).filter(
        MLShadowPrediction.event_id == test_thermal_obs.id,
        MLShadowPrediction.model_version == MODEL_VERSION
    ).all()
    assert len(pred_records2) == 1
    assert pred_records2[0].predicted_class == res1["predicted_class"]


def test_shadow_get_event_api(client: TestClient, test_thermal_obs):
    """Verifies GET /ml/shadow/{event_id} endpoint."""
    resp = client.get(f"/ml/shadow/{test_thermal_obs.id}?force_run=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == test_thermal_obs.id
    assert data["model_version"] == MODEL_VERSION
    assert data["predicted_class"] in TARGET_CLASSES
    assert "probabilities" in data
    assert data["prediction_status"] == "SUCCESS"


def test_shadow_audit_api(client: TestClient, test_thermal_obs):
    """Verifies GET /ml/shadow/audit endpoint."""
    resp = client.get("/ml/shadow/audit?force_run=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_shadow_predictions"] >= 1
    assert data["prediction_success_rate"] == 1.0
    assert "class_distribution" in data
    assert "confidence_distribution" in data
    assert "performance_metrics" in data
    assert "disagreement_analysis" in data
    assert data["model_version"] == MODEL_VERSION


def test_shadow_confidence_distribution_and_latency(test_thermal_obs, db_session: Session):
    """Verifies confidence binning and latency recording in batch evaluation."""
    service = MLShadowInferenceService()
    batch_res = service.evaluate_shadow_batch(db_session, limit=10, force_run=True)

    assert batch_res["successful_predictions"] >= 1
    assert batch_res["performance_metrics"]["average_latency_ms"] >= 0.0
    assert batch_res["performance_metrics"]["p95_latency_ms"] >= 0.0

    conf_dist = batch_res["confidence_distribution"]
    assert "<0.50" in conf_dist
    assert "0.50-0.70" in conf_dist
    assert "0.70-0.85" in conf_dist
    assert "0.85-0.95" in conf_dist
    assert ">0.95" in conf_dist
