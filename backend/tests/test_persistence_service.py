import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.thermal_observation import ThermalObservation
from app.services.persistence_service import PersistenceService

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
def persistence_test_data(db_session):
    """Creates a controlled set of historical thermal observations for persistence testing."""
    base_time = datetime.datetime(2026, 8, 15, 12, 0, 0)
    
    # Target Observation (ID 1)
    target = ThermalObservation(
        latitude=12.9750,
        longitude=74.8350,
        frp=100.0,
        acq_date="2026-08-15",
        acq_time="1200",
        satellite="NPP",
        instrument="VIIRS",
        daynight="D",
        observation_timestamp=base_time,
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)

    # 1. Same location 5 days ago (Nighttime, NOAA-20)
    obs_5d = ThermalObservation(
        latitude=12.9751, # ~11m distance
        longitude=74.8351,
        frp=120.0,
        acq_date="2026-08-10",
        acq_time="2200",
        satellite="N20",
        instrument="VIIRS",
        daynight="N",
        observation_timestamp=base_time - datetime.timedelta(days=5),
        source="VIIRS_N20_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(obs_5d)

    # 2. Same location 15 days ago (Nighttime, NPP)
    obs_15d = ThermalObservation(
        latitude=12.9749, # ~11m distance
        longitude=74.8349,
        frp=80.0,
        acq_date="2026-08-01",
        acq_time="2300",
        satellite="NPP",
        instrument="VIIRS",
        daynight="N",
        observation_timestamp=base_time - datetime.timedelta(days=14),
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(obs_15d)

    # 3. Same location 20 days ago, same date second pass
    obs_20d = ThermalObservation(
        latitude=12.9752, # ~22m distance
        longitude=74.8352,
        frp=150.0,
        acq_date="2026-07-26",
        acq_time="0300",
        satellite="N21",
        instrument="VIIRS",
        daynight="N",
        observation_timestamp=base_time - datetime.timedelta(days=20),
        source="VIIRS_N21_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(obs_20d)

    # 4. Spatially separated observation (2 km away, should be excluded by 100m radius)
    obs_far = ThermalObservation(
        latitude=12.9900, # ~2 km distance
        longitude=74.8350,
        frp=200.0,
        acq_date="2026-08-12",
        acq_time="1200",
        satellite="NPP",
        instrument="VIIRS",
        daynight="D",
        observation_timestamp=base_time - datetime.timedelta(days=3),
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(obs_far)

    # 5. Old observation (45 days ago, should be excluded by 30-day lookback)
    obs_old = ThermalObservation(
        latitude=12.9750,
        longitude=74.8350,
        frp=90.0,
        acq_date="2026-06-30",
        acq_time="1200",
        satellite="NPP",
        instrument="VIIRS",
        daynight="D",
        observation_timestamp=base_time - datetime.timedelta(days=46),
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test"
    )
    db_session.add(obs_old)

    db_session.commit()
    return target.id

def test_persistence_service_30d(db_session, persistence_test_data):
    target_id = persistence_test_data
    service = PersistenceService()
    
    res = service.get_persistence_features(db_session, target_id, lookback_days=30, spatial_radius_m=100.0)
    
    assert res["event_id"] == target_id
    assert res["lookback_days"] == 30
    assert res["spatial_radius_m"] == 100.0
    assert res["recurrence_count"] == 4 # Target + obs_5d + obs_15d + obs_20d
    assert res["unique_detection_dates"] == 4 # Aug 15, Aug 10, Aug 1, Jul 26
    assert res["unique_satellites"] == 3 # NPP, N20, N21
    assert res["daytime_detections"] == 1
    assert res["nighttime_detections"] == 3
    assert res["nighttime_ratio"] == 0.75
    assert res["mean_frp"] == round((100 + 120 + 80 + 150) / 4.0, 2) # 112.5
    assert res["max_frp"] == 150.0
    assert res["min_frp"] == 80.0
    assert res["mean_distance_m"] < 50.0

def test_persistence_service_7d_window(db_session, persistence_test_data):
    target_id = persistence_test_data
    service = PersistenceService()
    
    # 7-day lookback window should only include Target + obs_5d
    res = service.get_persistence_features(db_session, target_id, lookback_days=7, spatial_radius_m=100.0)
    
    assert res["recurrence_count"] == 2
    assert res["unique_detection_dates"] == 2

def test_persistence_service_parameter_validation(db_session, persistence_test_data):
    target_id = persistence_test_data
    service = PersistenceService()
    
    with pytest.raises(ValueError, match="Invalid lookback_days"):
        service.get_persistence_features(db_session, target_id, lookback_days=0)

    with pytest.raises(ValueError, match="Invalid spatial_radius_m"):
        service.get_persistence_features(db_session, target_id, spatial_radius_m=-10.0)

def test_persistence_api_endpoint(db_session, persistence_test_data):
    target_id = persistence_test_data
    res = client.get(f"/persistence/{target_id}?lookback_days=30&spatial_radius_m=100")
    
    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == target_id
    assert data["recurrence_count"] == 4
    assert data["nighttime_ratio"] == 0.75
    assert "mean_distance_m" in data
    assert "frp_stddev" in data
