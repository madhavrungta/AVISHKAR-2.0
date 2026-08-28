import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.industrial_facility import IndustrialFacility
from app.models.thermal_observation import ThermalObservation
from app.models.facility_association import ThermalFacilityAssociation
from app.models.facility_history import FacilityHistoricalBehavior
from app.services.history_service import HistoryService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_classify_activity_tier():
    service = HistoryService()
    assert service.classify_activity_tier(20) == "HIGHLY_PERSISTENT"
    assert service.classify_activity_tier(8) == "MODERATELY_ACTIVE"
    assert service.classify_activity_tier(2) == "SPORADIC"
    assert service.classify_activity_tier(0) == "NO_HISTORICAL_ANOMALIES"

def test_run_historical_aggregation_pipeline(db_session):
    # Insert facility: Reliance Jamnagar Refinery
    fac = IndustrialFacility(
        osm_id="way/11111",
        name="Reliance Jamnagar Refinery",
        facility_type="refinery",
        latitude=28.6140,
        longitude=77.2090,
        area_sqm=100000.0,
        ingestion_batch_id="test_batch"
    )
    db_session.add(fac)
    db_session.commit()

    now = datetime.datetime.utcnow()

    # Insert 6 thermal observations with varying FRPs (10, 20, 30, 40, 50, 100)
    frps = [10.0, 20.0, 30.0, 40.0, 50.0, 100.0]
    for idx, f in enumerate(frps):
        obs = ThermalObservation(
            latitude=28.6141,
            longitude=77.2091,
            frp=f,
            acq_date="2026-08-26",
            acq_time=f"0{idx}00",
            daynight="D" if idx % 2 == 0 else "N",
            observation_timestamp=now,
            source="VIIRS_SNPP_NRT",
            ingestion_batch_id="test_batch"
        )
        db_session.add(obs)
        db_session.commit()

        assoc = ThermalFacilityAssociation(
            observation_id=obs.id,
            facility_id=fac.id,
            distance_meters=50.0,
            association_type="DIRECT_MATCH"
        )
        db_session.add(assoc)
    
    db_session.commit()

    service = HistoryService()
    response = service.run_historical_aggregation_pipeline(db=db_session, recalculate_all=True)

    assert response.status == "success"
    assert response.facilities_profiled == 1
    assert response.moderately_active == 1

    profile = db_session.query(FacilityHistoricalBehavior).filter(
        FacilityHistoricalBehavior.facility_id == fac.id
    ).first()

    assert profile is not None
    assert profile.total_observations == 6
    assert profile.min_frp == 10.0
    assert profile.max_frp == 100.0
    assert profile.p95_frp > 50.0
    assert profile.activity_tier == "MODERATELY_ACTIVE"
