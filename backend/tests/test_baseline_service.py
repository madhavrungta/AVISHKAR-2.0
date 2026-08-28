import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.industrial_facility import IndustrialFacility
from app.models.facility_history import FacilityHistoricalBehavior
from app.models.facility_baseline import FacilityNormalBaseline
from app.services.baseline_service import BaselineService, CATEGORY_DEFAULT_BASELINES

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_category_defaults_exist():
    assert "refinery" in CATEGORY_DEFAULT_BASELINES
    assert "power_plant" in CATEGORY_DEFAULT_BASELINES
    assert CATEGORY_DEFAULT_BASELINES["refinery"]["p95"] == 55.0

def test_generate_facility_baselines(db_session):
    # Insert test facility
    fac = IndustrialFacility(
        osm_id="way/22222",
        name="Trombay Power Plant",
        facility_type="power_plant",
        latitude=19.0760,
        longitude=72.8777,
        area_sqm=80000.0,
        ingestion_batch_id="test_batch"
    )
    db_session.add(fac)
    db_session.commit()

    # Insert historical behavior profile
    hist = FacilityHistoricalBehavior(
        facility_id=fac.id,
        total_observations=10,
        observation_days=5,
        median_frp=35.0,
        p95_frp=78.5,
        p99_frp=105.0,
        day_count=8,
        night_count=2,
        activity_tier="MODERATELY_ACTIVE"
    )
    db_session.add(hist)
    db_session.commit()

    service = BaselineService()
    response = service.generate_facility_baselines(db=db_session, recalculate_all=True)

    assert response.status == "success"
    assert response.baselines_generated == 1
    assert response.established_baselines == 1

    b = db_session.query(FacilityNormalBaseline).filter(
        FacilityNormalBaseline.facility_id == fac.id
    ).first()

    assert b is not None
    assert b.baseline_status == "ESTABLISHED"
    assert b.baseline_frp_p95 == 78.5
    assert b.day_night_preference == "DAY_DOMINANT"
