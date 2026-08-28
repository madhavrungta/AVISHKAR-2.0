import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.industrial_facility import IndustrialFacility
from app.models.thermal_observation import ThermalObservation
from app.models.facility_association import ThermalFacilityAssociation
from app.models.abnormal_event import AbnormalThermalEvent
from app.models.risk_score import VerificationRiskScore
from app.services.risk_service import RiskService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_classify_risk_tier():
    service = RiskService()
    assert service.classify_risk_tier(90.0) == "CRITICAL_VERIFIED_RISK"
    assert service.classify_risk_tier(72.5) == "HIGH_RISK"
    assert service.classify_risk_tier(45.0) == "MEDIUM_RISK"
    assert service.classify_risk_tier(15.0) == "LOW_RISK"

def test_evaluate_risk_scores(db_session):
    # Insert high-sensitivity facility: Refinery
    fac = IndustrialFacility(
        osm_id="way/44444",
        name="IOCL Koyali Refinery",
        facility_type="refinery",
        latitude=22.3650,
        longitude=73.1810,
        area_sqm=120000.0,
        ingestion_batch_id="test_batch"
    )
    db_session.add(fac)
    db_session.commit()

    now = datetime.datetime.utcnow()

    # Observation with FRP = 85.0 MW
    obs = ThermalObservation(
        latitude=22.3651,
        longitude=73.1811,
        frp=85.0,
        acq_date="2026-08-26",
        acq_time="1400",
        daynight="D",
        observation_timestamp=now,
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="test_batch"
    )
    db_session.add(obs)
    db_session.commit()

    # Direct match association
    assoc = ThermalFacilityAssociation(
        observation_id=obs.id,
        facility_id=fac.id,
        distance_meters=35.0,
        association_type="DIRECT_MATCH"
    )
    db_session.add(assoc)

    # Abnormal event multiplier = 2.2x
    anom = AbnormalThermalEvent(
        observation_id=obs.id,
        facility_id=fac.id,
        observed_frp=85.0,
        baseline_p95_frp=38.6,
        frp_multiplier_ratio=2.2,
        anomaly_severity="HIGH_ABNORMAL_SPIKE",
        explanation_reason="High spike"
    )
    db_session.add(anom)
    db_session.commit()

    service = RiskService()
    response = service.evaluate_risk_scores(db=db_session, recalculate_all=True)

    assert response.status == "success"
    assert response.total_evaluated == 1

    risk = db_session.query(VerificationRiskScore).filter(
        VerificationRiskScore.observation_id == obs.id
    ).first()

    assert risk is not None
    assert risk.composite_risk_score > 80.0
    assert risk.spatial_proximity_score == 100.0
    assert risk.facility_sensitivity_score == 95.0
    assert risk.optical_verification_confidence == 0.85
