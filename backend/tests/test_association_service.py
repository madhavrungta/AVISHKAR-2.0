import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.facility_association import ThermalFacilityAssociation
from app.services.association_service import AssociationService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_classify_association():
    service = AssociationService()
    assert service.classify_association(50.0) == "DIRECT_MATCH"
    assert service.classify_association(500.0) == "PROXIMATE_MATCH"
    assert service.classify_association(2000.0) == "VICINITY_MATCH"
    assert service.classify_association(5000.0) == "UNASSOCIATED"

def test_run_association_pipeline(db_session):
    # Insert test facility: Jamnagar Refinery (28.6140, 77.2090)
    fac = IndustrialFacility(
        osm_id="way/9999",
        name="Jamnagar Refinery",
        facility_type="refinery",
        latitude=28.6140,
        longitude=77.2090,
        area_sqm=50000.0,
        ingestion_batch_id="test_batch"
    )
    db_session.add(fac)

    # Insert test thermal observation #1 (very close to facility ~50m)
    obs1 = ThermalObservation(
        latitude=28.6143,
        longitude=77.2092,
        frp=15.0,
        observation_timestamp=pytest.importorskip("datetime").datetime.utcnow(),
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="test_batch"
    )
    # Insert test thermal observation #2 (far away in Mumbai ~1150km)
    obs2 = ThermalObservation(
        latitude=19.0760,
        longitude=72.8777,
        frp=8.0,
        observation_timestamp=pytest.importorskip("datetime").datetime.utcnow(),
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="test_batch"
    )
    db_session.add_all([obs1, obs2])
    db_session.commit()

    service = AssociationService()
    response = service.run_association_pipeline(db=db_session, max_distance_meters=3000.0)

    assert response.status == "success"
    assert response.total_observations_processed == 2
    assert response.associations_created == 1
    assert response.direct_matches == 1
    assert response.unassociated == 1

    assocs = db_session.query(ThermalFacilityAssociation).all()
    assert len(assocs) == 1
    assert assocs[0].observation_id == obs1.id
    assert assocs[0].facility_id == fac.id
    assert assocs[0].association_type == "DIRECT_MATCH"
