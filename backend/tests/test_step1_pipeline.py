import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base
from app.models.facility import Facility
from app.models.thermal_observation import ThermalObservation
from app.models.facility_observation import FacilityObservation
from app.models.facility_baseline import FacilityBaseline
from app.models.ingestion_batch import IngestionBatch
from app.services.facility_association_service import FacilityAssociationService
from app.services.firms_service import FIRMSDataService
from app.main import app

from sqlalchemy.pool import StaticPool

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db_dependency] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# Help dependency resolution
from app.database import get_db
get_db_dependency = get_db

def test_coordinate_validation_and_batch_ingestion(db_session):
    """Verify raw FIRMS coordinates cleaning, rejection of bad values, and batch metrics."""
    service = FIRMSDataService()

    # Create dummy data: 1 valid, 1 bad latitude, 1 bad longitude, 1 duplicate
    raw_csv = (
        "latitude,longitude,bright_ti4,bright_ti5,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,frp,daynight\n"
        "28.61,77.20,320.1,295.4,0.37,0.38,2026-08-28,1200,N,VIIRS,n,1.0HS,15.2,D\n"  # Valid
        "120.5,77.20,320.1,295.4,0.37,0.38,2026-08-28,1200,N,VIIRS,n,1.0HS,15.2,D\n" # Invalid Lat
        "28.61,-250.0,320.1,295.4,0.37,0.38,2026-08-28,1200,N,VIIRS,n,1.0HS,15.2,D\n" # Invalid Lon
        "28.61,77.20,320.1,295.4,0.37,0.38,2026-08-28,1200,N,VIIRS,n,1.0HS,15.2,D\n"  # Duplicate
    )

    res = service.ingest_firms_data(db=db_session, source="VIIRS_SNPP_NRT", raw_csv_override=raw_csv)
    
    assert res.status == "success"
    assert res.records_ingested == 1
    assert res.validation_report.total_records == 4
    assert res.validation_report.valid_records == 1
    assert res.validation_report.invalid_records == 3
    assert res.validation_report.duplicates == 1

    # Verify IngestionBatch model fields
    batch = db_session.query(IngestionBatch).filter(IngestionBatch.id == res.batch_id).first()
    assert batch is not None
    assert batch.records_received == 4
    assert batch.records_valid == 1
    assert batch.records_rejected == 3
    assert batch.status == "completed"


def test_spatial_association_and_distance(db_session):
    """Verify distance calculations and radius filter configurations."""
    # Seed 1 facility at New Delhi
    fac = Facility(
        osm_id="way_1",
        name="Delhi Industrial Plant",
        facility_type="refinery",
        latitude=28.6139,
        longitude=77.2090,
        geometry="POINT(77.2090 28.6139)"
    )
    db_session.add(fac)
    db_session.commit()

    # Observation 1: Very close (~150m)
    obs_close = ThermalObservation(
        latitude=28.6130,
        longitude=77.2100,
        observation_timestamp=datetime.datetime.utcnow(),
        source="TEST",
        ingestion_batch_id="test_batch"
    )
    # Observation 2: Far (~5km)
    obs_far = ThermalObservation(
        latitude=28.6500,
        longitude=77.2500,
        observation_timestamp=datetime.datetime.utcnow(),
        source="TEST",
        ingestion_batch_id="test_batch"
    )
    db_session.add_all([obs_close, obs_far])
    db_session.commit()

    # Match with default 3000m radius
    service = FacilityAssociationService(radius_meters=3000.0)
    matches_close = service.associate_observation(db_session, obs_close)
    matches_far = service.associate_observation(db_session, obs_far)

    assert len(matches_close) == 1
    assert matches_close[0][0].id == fac.id
    assert matches_close[0][1] < 500.0 # distance in meters
    assert len(matches_far) == 0

    # Verify relationship persistence in facility_observations table
    assoc = db_session.query(FacilityObservation).filter(FacilityObservation.observation_id == obs_close.id).first()
    assert assoc is not None
    assert assoc.facility_id == fac.id
    assert assoc.distance_m < 500.0
    assert "Proximity" in assoc.association_method


def test_duplicate_association_protection(db_session):
    """Verify that multiple association calls do not create duplicate facility_observations records."""
    fac = Facility(
        osm_id="way_1",
        name="Delhi Plant",
        facility_type="refinery",
        latitude=28.61,
        longitude=77.20,
        geometry="POINT(77.20 28.61)"
    )
    obs = ThermalObservation(
        latitude=28.611,
        longitude=77.201,
        observation_timestamp=datetime.datetime.utcnow(),
        source="TEST",
        ingestion_batch_id="test_batch"
    )
    db_session.add_all([fac, obs])
    db_session.commit()

    service = FacilityAssociationService(radius_meters=3000.0)
    service.associate_observation(db_session, obs)
    
    # Try creating duplicate
    service.associate_observation(db_session, obs)

    # Total counts in table must be exactly 1
    count = db_session.query(FacilityObservation).filter(
        FacilityObservation.facility_id == fac.id,
        FacilityObservation.observation_id == obs.id
    ).count()
    assert count == 1


def test_baseline_statistics_math(db_session):
    """Verify baseline median, p95, p99, and MAD calculations including missing values."""
    fac = Facility(
        osm_id="way_1",
        name="Base Test Plant",
        facility_type="refinery",
        latitude=28.61,
        longitude=77.20,
        geometry="POINT(77.20 28.61)"
    )
    db_session.add(fac)
    db_session.commit()

    # Generate observations with specific FRP: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 MW
    obs_list = []
    now = datetime.datetime.utcnow()
    for frp in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]:
        o = ThermalObservation(
            latitude=28.61,
            longitude=77.20,
            frp=frp,
            bright_ti4=300.0,
            bright_ti5=290.0,
            observation_timestamp=now - datetime.timedelta(days=frp),
            source="TEST",
            ingestion_batch_id="test_batch"
        )
        obs_list.append(o)
    
    # Add one with missing FRP to test handling of nulls (should not break stats)
    obs_list.append(
        ThermalObservation(
            latitude=28.61,
            longitude=77.20,
            frp=None,
            observation_timestamp=now,
            source="TEST",
            ingestion_batch_id="test_batch"
        )
    )

    db_session.add_all(obs_list)
    db_session.commit()

    # Associate them all
    for o in obs_list:
        assoc = FacilityObservation(
            facility_id=fac.id,
            observation_id=o.id,
            distance_m=10.0,
            association_method="Mock"
        )
        db_session.add(assoc)
    db_session.commit()

    # Fetch baseline stats via service logic (embedded in route / GET implementation)
    # FRP list: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
    # Median should be 55.0
    # Absolute deviations from 55: 45, 35, 25, 15, 5, 5, 15, 25, 35, 45 -> sorted: 5, 5, 15, 15, 25, 25, 35, 35, 45, 45 -> Median deviation (MAD) is 25.0
    
    from app.api.facility_pipeline import get_facility_baseline
    res = get_facility_baseline(facility_id=fac.id, db=db_session)

    assert res.observation_count == 11 # 10 valid + 1 null
    assert res.median_frp == 55.0
    assert res.mad_frp == 25.0
    assert res.p95_frp == 100.0
    assert res.p99_frp == 100.0


def test_api_endpoints(client, db_session):
    """Verify facility pipeline GET & POST endpoints."""
    # Seed 1 facility
    fac = Facility(
        osm_id="way_1",
        name="API Delhi Plant",
        facility_type="refinery",
        latitude=28.61,
        longitude=77.20,
        geometry="POINT(77.20 28.61)"
    )
    db_session.add(fac)
    db_session.commit()

    # GET /facilities
    response = client.get("/facilities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "API Delhi Plant"

    # GET /facilities/{id}
    response = client.get(f"/facilities/{fac.id}")
    assert response.status_code == 200
    assert response.json()["osm_id"] == "way_1"

    # GET /facilities/{id}/baseline (empty)
    response = client.get(f"/facilities/{fac.id}/baseline")
    assert response.status_code == 200
    assert response.json()["observation_count"] == 0

    # GET /analytics/facilities/summary
    response = client.get("/analytics/facilities/summary")
    assert response.status_code == 200
    assert response.json()["total_facilities"] == 1
