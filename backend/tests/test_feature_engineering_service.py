import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.services.feature_engineering_service import FeatureEngineeringService, FEATURE_SCHEMA_VERSION

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
def feature_test_data(db_session):
    """Creates test observation and nearby facility records."""
    base_time = datetime.datetime(2026, 8, 15, 12, 0, 0)

    # 1. Industrial Facility
    fac = IndustrialFacility(
        osm_id="way/123456",
        name="Mangalore Refinery Complex",
        facility_type="REFINERY",
        latitude=12.9755,
        longitude=74.8355,
        ingestion_batch_id="batch_test"
    )
    db_session.add(fac)
    db_session.commit()

    # 2. Thermal Observation (ID 1)
    obs = ThermalObservation(
        latitude=12.9750,
        longitude=74.8350,
        frp=125.5,
        bright_ti4=345.2,
        bright_ti5=295.1,
        confidence="h",
        daynight="N",
        satellite="NPP",
        instrument="VIIRS",
        acq_date="2026-08-15",
        acq_time="2300",
        observation_timestamp=base_time,
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)
    return obs.id

def test_build_feature_vector_complete(db_session, feature_test_data):
    event_id = feature_test_data
    service = FeatureEngineeringService()

    res = service.build_feature_vector(db_session, event_id)

    assert res["event_id"] == event_id
    assert res["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert "features" in res
    assert "feature_metadata" in res

    feats = res["features"]

    # Thermal
    assert feats["frp"] == 125.5
    assert feats["brightness_temperature"] == 345.2
    assert feats["background_temperature"] == 295.1
    assert feats["confidence"] == "h"
    assert feats["daynight"] == "N"
    assert feats["satellite"] == "NPP"

    # Land cover
    assert feats["land_cover_code"] == 50
    assert feats["land_cover_class"] == "BUILT_UP"
    assert feats["is_built_up"] is True
    assert feats["is_cropland"] is False

    # Temporal persistence
    assert feats["recurrence_count"] == 1
    assert feats["unique_detection_dates"] == 1
    assert feats["nighttime_ratio"] == 1.0

    # Industrial context
    assert feats["nearest_industrial_distance_m"] is not None
    assert feats["nearest_industrial_distance_m"] < 100.0
    assert feats["nearest_facility_type"] == "REFINERY"

def test_feature_engineering_invalid_event(db_session):
    service = FeatureEngineeringService()
    with pytest.raises(ValueError, match="not found"):
        service.build_feature_vector(db_session, 99999)

def test_feature_api_endpoint(db_session, feature_test_data):
    event_id = feature_test_data
    res = client.get(f"/features/{event_id}")

    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == event_id
    assert data["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert data["features"]["frp"] == 125.5
    assert data["features"]["land_cover_class"] == "BUILT_UP"
    assert "frp" in data["feature_metadata"]
