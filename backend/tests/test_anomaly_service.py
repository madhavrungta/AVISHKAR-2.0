import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.industrial_facility import IndustrialFacility
from app.models.thermal_observation import ThermalObservation
from app.models.facility_association import ThermalFacilityAssociation
from app.models.facility_baseline import FacilityNormalBaseline
from app.models.abnormal_event import AbnormalThermalEvent
from app.services.anomaly_service import AnomalyService, MANDATORY_CAUTION_LABEL

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_classify_severity():
    service = AnomalyService()
    assert service.classify_severity(1.2) == "MODERATE_ABNORMAL_SPIKE"
    assert service.classify_severity(2.0) == "HIGH_ABNORMAL_SPIKE"
    assert service.classify_severity(3.5) == "CRITICAL_INDUSTRIAL_ANOMALY"

def test_detect_abnormal_events(db_session):
    # Insert test facility
    fac = IndustrialFacility(
        osm_id="way/33333",
        name="Mangalore Chemical Refinery",
        facility_type="refinery",
        latitude=12.9141,
        longitude=74.8560,
        area_sqm=60000.0,
        ingestion_batch_id="test_batch"
    )
    db_session.add(fac)
    db_session.commit()

    # Insert baseline P95 = 50.0 MW
    baseline = FacilityNormalBaseline(
        facility_id=fac.id,
        baseline_frp_p50=20.0,
        baseline_frp_p95=50.0,
        baseline_frp_p99=80.0,
        baseline_status="ESTABLISHED"
    )
    db_session.add(baseline)
    db_session.commit()

    now = datetime.datetime.utcnow()

    # Observation with FRP = 125.0 MW (2.5x multiplier)
    obs = ThermalObservation(
        latitude=12.9142,
        longitude=74.8561,
        frp=125.0,
        acq_date="2026-08-26",
        acq_time="1200",
        daynight="D",
        observation_timestamp=now,
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="test_batch"
    )
    db_session.add(obs)
    db_session.commit()

    assoc = ThermalFacilityAssociation(
        observation_id=obs.id,
        facility_id=fac.id,
        distance_meters=40.0,
        association_type="DIRECT_MATCH"
    )
    db_session.add(assoc)
    db_session.commit()

    service = AnomalyService()
    response = service.detect_abnormal_events(db=db_session, recalculate_all=True)

    assert response.status == "success"
    assert response.anomalies_detected == 1
    assert response.high_spikes == 1

    event = db_session.query(AbnormalThermalEvent).filter(
        AbnormalThermalEvent.observation_id == obs.id
    ).first()

    assert event is not None
    assert event.frp_multiplier_ratio == 2.5
    assert event.anomaly_severity == "HIGH_ABNORMAL_SPIKE"
    assert event.scientific_caution_label == MANDATORY_CAUTION_LABEL
    assert "Persistent Industrial Heat != Confirmed Fire" in event.explanation_reason
