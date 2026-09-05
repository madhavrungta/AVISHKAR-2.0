import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.thermal_observation import ThermalObservation
from app.services.ground_truth.base import (
    GroundTruthEvidence, GroundTruthClass, LabelConfidenceLevel
)
from app.services.ground_truth.matcher import GroundTruthMatcher

client = TestClient(app)

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

    def override_get_db():
        try:
            yield session
        finally:
            pass

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    if previous_override is not None:
        app.dependency_overrides[get_db] = previous_override
    else:
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def gt_test_data(db_session):
    """Creates a sample thermal observation for ground-truth testing."""
    obs = ThermalObservation(
        latitude=12.9750,
        longitude=74.8350,
        frp=140.0,
        acq_date="2026-08-15",
        acq_time="1200",
        satellite="NPP",
        instrument="VIIRS",
        daynight="D",
        observation_timestamp=datetime.datetime(2026, 8, 15, 12, 0, 0),
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_gt_test"
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)
    return obs.id

def test_ground_truth_vocabulary():
    assert GroundTruthClass.INDUSTRIAL_FIRE == "INDUSTRIAL_FIRE"
    assert GroundTruthClass.GAS_FLARE == "GAS_FLARE"
    assert GroundTruthClass.AGRICULTURAL_BURNING == "AGRICULTURAL_BURNING"
    assert GroundTruthClass.MINING_ACTIVITY == "MINING_ACTIVITY"
    assert GroundTruthClass.WILDFIRE == "WILDFIRE"
    assert GroundTruthClass.UNKNOWN == "UNKNOWN"

def test_ground_truth_matcher_unmatched_returns_unknown(db_session, gt_test_data):
    event_id = gt_test_data
    matcher = GroundTruthMatcher()

    res = matcher.evaluate_observation_label(db_session, event_id)

    assert res["event_id"] == event_id
    assert res["label"] == "UNKNOWN"
    assert res["label_confidence"] == "UNKNOWN"
    assert res["training_eligible"] is False
    assert res["evidence_count"] == 0

def test_ground_truth_api_endpoint(db_session, gt_test_data):
    event_id = gt_test_data
    res = client.get(f"/ground-truth/{event_id}")

    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == event_id
    assert data["label"] == "UNKNOWN"
    assert data["training_eligible"] is False

def test_ground_truth_batch_audit_endpoint(db_session, gt_test_data):
    res = client.get("/ground-truth/batch/audit?limit=10")

    assert res.status_code == 200
    data = res.json()
    assert data["total_audited_observations"] >= 1
    assert "class_distribution" in data
    assert "training_eligible_count" in data
    assert data["class_distribution"]["UNKNOWN"] >= 1
