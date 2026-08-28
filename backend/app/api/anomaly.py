from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.abnormal_event import AbnormalThermalEvent
from app.models.industrial_facility import IndustrialFacility
from app.models.thermal_observation import ThermalObservation
from app.schemas.abnormal_event import (
    AbnormalEventResponse,
    DetectAnomalyRequest,
    DetectAnomalyResponse,
    AnomalySummary
)
from app.services.anomaly_service import AnomalyService

router = APIRouter(tags=["Abnormal Thermal Events"])

@router.post("/anomalies/detect", response_model=DetectAnomalyResponse, summary="Detect Abnormal Thermal Events Exceeding Baseline P95")
def detect_anomalies(
    payload: DetectAnomalyRequest = DetectAnomalyRequest(),
    db: Session = Depends(get_db)
):
    """Triggers batch anomaly detection evaluating observed FRP values against facility P95 baseline thresholds."""
    service = AnomalyService()
    recalc = payload.recalculate_all or False
    response = service.detect_abnormal_events(db=db, recalculate_all=recalc)
    return response

@router.get("/anomalies", response_model=List[AbnormalEventResponse], summary="Retrieve Detected Abnormal Thermal Events")
def list_anomalies(
    facility_id: Optional[int] = Query(None, description="Filter by industrial facility ID"),
    anomaly_severity: Optional[str] = Query(None, description="Filter by severity (MODERATE_ABNORMAL_SPIKE, HIGH_ABNORMAL_SPIKE, CRITICAL_INDUSTRIAL_ANOMALY)"),
    min_multiplier: Optional[float] = Query(None, ge=1.0, description="Minimum FRP multiplier ratio over P95 baseline"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists flagged abnormal thermal events with severity tiers, FRP multiplier ratios, and mandatory scientific caution labels."""
    query = db.query(AbnormalThermalEvent)

    if facility_id:
        query = query.filter(AbnormalThermalEvent.facility_id == facility_id)
    if anomaly_severity:
        query = query.filter(AbnormalThermalEvent.anomaly_severity == anomaly_severity)
    if min_multiplier is not None:
        query = query.filter(AbnormalThermalEvent.frp_multiplier_ratio >= min_multiplier)

    events = query.order_by(AbnormalThermalEvent.frp_multiplier_ratio.desc()).offset(offset).limit(limit).all()

    results = []
    for e in events:
        fac = e.facility
        obs = e.observation
        res_dict = {
            "id": e.id,
            "observation_id": e.observation_id,
            "facility_id": e.facility_id,
            "observed_frp": e.observed_frp,
            "baseline_p95_frp": e.baseline_p95_frp,
            "frp_multiplier_ratio": e.frp_multiplier_ratio,
            "anomaly_severity": e.anomaly_severity,
            "scientific_caution_label": e.scientific_caution_label,
            "explanation_reason": e.explanation_reason,
            "detected_at": e.detected_at,
            "facility_name": fac.name if fac else None,
            "facility_type": fac.facility_type if fac else None,
            "latitude": obs.latitude if obs else None,
            "longitude": obs.longitude if obs else None
        }
        results.append(AbnormalEventResponse(**res_dict))

    return results

@router.get("/anomalies/observation/{obs_id}", response_model=Optional[AbnormalEventResponse], summary="Get Abnormal Event Detail for Observation")
def get_observation_anomaly(obs_id: int, db: Session = Depends(get_db)):
    """Retrieves abnormal event details for a single thermal observation ID if flagged."""
    e = db.query(AbnormalThermalEvent).filter(
        AbnormalThermalEvent.observation_id == obs_id
    ).first()

    if not e:
        return None

    fac = e.facility
    obs = e.observation
    res_dict = {
        "id": e.id,
        "observation_id": e.observation_id,
        "facility_id": e.facility_id,
        "observed_frp": e.observed_frp,
        "baseline_p95_frp": e.baseline_p95_frp,
        "frp_multiplier_ratio": e.frp_multiplier_ratio,
        "anomaly_severity": e.anomaly_severity,
        "scientific_caution_label": e.scientific_caution_label,
        "explanation_reason": e.explanation_reason,
        "detected_at": e.detected_at,
        "facility_name": fac.name if fac else None,
        "facility_type": fac.facility_type if fac else None,
        "latitude": obs.latitude if obs else None,
        "longitude": obs.longitude if obs else None
    }
    return AbnormalEventResponse(**res_dict)

@router.get("/analytics/anomalies-summary", response_model=AnomalySummary, summary="Get Aggregate Abnormal Event Metrics")
def get_anomalies_summary(db: Session = Depends(get_db)):
    """Computes summary metrics for flagged abnormal thermal events."""
    total = db.query(func.count(AbnormalThermalEvent.id)).scalar() or 0
    if total == 0:
        return AnomalySummary(
            total_anomalies=0,
            severity_breakdown={},
            max_multiplier_ratio=0.0,
            highest_anomaly=None
        )

    max_ratio = db.query(func.max(AbnormalThermalEvent.frp_multiplier_ratio)).scalar() or 0.0

    counts = db.query(
        AbnormalThermalEvent.anomaly_severity, func.count(AbnormalThermalEvent.id)
    ).group_by(AbnormalThermalEvent.anomaly_severity).all()
    severity_breakdown = {str(sev): count for sev, count in counts if sev}

    highest = db.query(AbnormalThermalEvent).order_by(
        AbnormalThermalEvent.frp_multiplier_ratio.desc()
    ).first()

    highest_dict = None
    if highest and highest.facility:
        highest_dict = {
            "observation_id": highest.observation_id,
            "facility_name": highest.facility.name,
            "facility_type": highest.facility.facility_type,
            "multiplier_ratio": highest.frp_multiplier_ratio,
            "severity": highest.anomaly_severity
        }

    return AnomalySummary(
        total_anomalies=total,
        severity_breakdown=severity_breakdown,
        max_multiplier_ratio=round(float(max_ratio), 2),
        highest_anomaly=highest_dict
    )
