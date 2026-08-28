import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.thermal_observation import ThermalObservation
from app.models.facility import Facility
from app.models.facility_observation import FacilityObservation
from app.models.facility_baseline import FacilityBaseline
from app.models.abnormal_event import AbnormalThermalEvent
from app.models.risk_score import VerificationRiskScore
from app.models.ingestion_batch import IngestionBatch

from agent.tools import (
    get_event,
    get_thermal_observations,
    get_facility,
    get_facility_baseline,
    get_event_timeline,
    get_context
)

# Test engine sharing connection
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    # Overwrite the global SessionLocal inside agent.tools to use our test session
    monkeypatch.setattr("agent.tools.SessionLocal", TestingSessionLocal)
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed ingestion batch
        batch = IngestionBatch(
            id="batch_mock_123",
            source="VIIRS_SNPP_NRT",
            status="completed",
            started_at=datetime.datetime.utcnow(),
            completed_at=datetime.datetime.utcnow()
        )
        db.add(batch)
        db.commit()

        # Seed test data
        obs = ThermalObservation(
            id=1,
            latitude=28.61,
            longitude=77.20,
            frp=150.5,
            bright_ti4=340.2,
            bright_ti5=295.1,
            confidence="nominal",
            satellite="VIIRS NPP",
            instrument="VIIRS",
            daynight="D",
            source="VIIRS_SNPP_NRT",
            ingestion_batch_id="batch_mock_123",
            observation_timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
            observation_time=datetime.datetime(2026, 8, 28, 12, 0, 0)
        )
        db.add(obs)
        
        fac = Facility(
            id=101,
            osm_id="way/12345",
            name="Test Refinery",
            facility_type="refinery",
            latitude=28.61,
            longitude=77.20,
            source="OSM Overpass API",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        db.add(fac)
        db.commit()

        # Seed association
        assoc = FacilityObservation(
            facility_id=101,
            observation_id=1,
            distance_m=120.0,
            association_method="spatial_proximity"
        )
        db.add(assoc)

        # Seed abnormal event
        ab = AbnormalThermalEvent(
            observation_id=1,
            facility_id=101,
            observed_frp=150.5,
            baseline_p95_frp=50.0,
            frp_multiplier_ratio=3.01,
            anomaly_severity="HIGH_ABNORMAL_SPIKE",
            explanation_reason="Thermal spike 3x above baseline"
        )
        db.add(ab)

        # Seed risk score
        risk = VerificationRiskScore(
            observation_id=1,
            composite_risk_score=85.0,
            risk_level="HIGH_RISK",
            spatial_proximity_score=20.0,
            frp_multiplier_score=40.0
        )
        db.add(risk)

        # Seed baseline
        base = FacilityBaseline(
            facility_id=101,
            observation_count=5,
            median_frp=20.0,
            p95_frp=50.0,
            p99_frp=90.0,
            mad_frp=2.5,
            baseline_start=datetime.datetime(2026, 5, 1),
            baseline_end=datetime.datetime(2026, 8, 1)
        )
        db.add(base)
        
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_tool_get_event():
    # Test numeric and EVT formats
    res1 = get_event("1")
    assert res1["event_id"] == "EVT-0001"
    assert "HIGH_RISK" in res1["priority"]
    assert res1["facility_id"] == 101
    assert res1["anomaly_score"] == 85.0

    res2 = get_event("EVT-0001")
    assert res2["event_id"] == "EVT-0001"

    # Test not found
    res3 = get_event("999")
    assert "not found" in res3["error"]

def test_tool_get_thermal_observations():
    res = get_thermal_observations("1")
    assert res["FRP"] == 150.5
    assert res["satellite"] == "VIIRS NPP"
    assert res["latitude"] == 28.61

def test_tool_get_facility():
    res = get_facility(101)
    assert res["name"] == "Test Refinery"
    assert res["facility_type"] == "refinery"

def test_tool_get_facility_baseline():
    res = get_facility_baseline(101)
    assert res["median_frp"] == 20.0
    assert res["p95_frp"] == 50.0
    assert res["observation_count"] == 5

    # Test baseline not found
    res_none = get_facility_baseline(999)
    assert res_none["status"] == "baseline unavailable"

def test_tool_get_event_timeline():
    res = get_event_timeline("1")
    assert res["observation_count"] == 1
    assert len(res["timeline"]) == 1
    assert res["timeline"][0]["FRP"] == 150.5

def test_tool_get_context():
    res = get_context("1")
    assert res == "contextual evidence unavailable"
