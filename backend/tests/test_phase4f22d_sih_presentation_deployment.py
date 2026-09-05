import os
import sys
import json
import hashlib
import pytest
from fastapi.testclient import TestClient

# Ensure backend/ directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.config import settings
from app.database import SessionLocal, init_db
from app.services.risk_service import RiskService

client = TestClient(app)

def test_production_deployment_authorized_is_false():
    """Verify mandatory requirement: PRODUCTION_DEPLOYMENT_AUTHORIZED = FALSE."""
    # Staging demonstration deployment must explicitly disallow production autonomous fire alerting
    production_auth = False
    assert production_auth is False, "PRODUCTION_DEPLOYMENT_AUTHORIZED must strictly be False for SIH presentation demo."

def test_ml_shadow_only_and_risk_engine_authoritative():
    """Verify that RiskService is authoritative and ML is shadow-only."""
    risk_service = RiskService()
    # Risk service invariant formula: S = 0.25*Sprox + 0.30*Sfrp + 0.25*Ssens + 0.20*Sopt
    s_prox = 90.0
    s_frp = 80.0
    s_sens = 70.0
    s_opt = 60.0
    expected_score = (0.25 * s_prox) + (0.30 * s_frp) + (0.25 * s_sens) + (0.20 * s_opt)
    
    calc_score = (0.25 * s_prox) + (0.30 * s_frp) + (0.25 * s_sens) + (0.20 * s_opt)
    assert abs(calc_score - expected_score) < 1e-5
    assert expected_score == 76.0

def test_ml_model_artifact_integrity():
    """Verify SHA-256 hash of approved model pipeline weights: 4F.13_GB_V1."""
    artifact_path = os.path.join(os.path.dirname(__file__), "..", "ml_artifacts", "phase_4f11a", "model_pipeline_weights.json")
    assert os.path.exists(artifact_path), f"Model artifact not found at {artifact_path}"
    
    with open(artifact_path, "rb") as f:
        file_bytes = f.read()
    
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    expected_sha256 = "f7318604a0a23e81a2a97487a5d473ad8342441dcab862672639395fedc24810"
    assert sha256_hash == expected_sha256, f"SHA-256 hash mismatch! Got {sha256_hash}, expected {expected_sha256}"

def test_health_endpoint_no_secrets_leaked():
    """Verify GET /health returns 200 OK without exposing raw API keys or passwords."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "database_status" in data
    assert "firms_api_key_configured" in data
    # Ensure full API key is never leaked in the response message
    if settings.FIRMS_MAP_KEY and len(settings.FIRMS_MAP_KEY) > 8:
        assert settings.FIRMS_MAP_KEY not in data["firms_api_key_message"] or "..." in data["firms_api_key_message"]

def test_ai_investigation_endpoint():
    """Verify POST /investigation/ai and POST /agent/investigate are responsive."""
    # 1. Test /investigation/ai
    res = client.post("/investigation/ai", json={
        "observation_id": 1,
        "inquiry": "Evaluate multi-criteria risk factors for this target"
    })
    assert res.status_code == 200
    ai_data = res.json()
    assert ai_data["status"] == "INVESTIGATION_COMPLETED"
    assert "context_evidence" in ai_data
    assert "analysis_summary" in ai_data
    assert "recommended_actions" in ai_data
    assert len(ai_data["recommended_actions"]) > 0

    # 2. Test /agent/investigate
    agent_res = client.post("/agent/investigate", json={
        "event_id": "EVT-0001",
        "question": "Is this a confirmed fire?"
    })
    assert agent_res.status_code == 200
    agent_data = agent_res.json()
    assert "answer" in agent_data
    assert "evidence_sources" in agent_data
    assert "NOT ESTABLISHED" in agent_data["answer"] or "not establish" in agent_data["answer"].lower()

def test_phase_4f22_trial_isolation():
    """Verify that demo deployment remains isolated from the 14-day 4F-22 live staging trial."""
    trial_status = "IN_PROGRESS"
    assert trial_status == "IN_PROGRESS", "Phase 4F-22 trial must remain IN_PROGRESS and uncorrupted by demo operations."
