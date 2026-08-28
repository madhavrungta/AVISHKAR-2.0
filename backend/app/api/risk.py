import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.risk_score import VerificationRiskScore
from app.models.industrial_facility import IndustrialFacility
from app.models.thermal_observation import ThermalObservation
from app.schemas.risk_score import (
    RiskScoreResponse,
    EvaluateRiskRequest,
    EvaluateRiskResponse,
    RiskSummary
)
from app.services.risk_service import RiskService

router = APIRouter(tags=["Multi-Modal Risk Scoring"])

@router.post("/risk/evaluate", response_model=EvaluateRiskResponse, summary="Evaluate Multi-Modal Risk Scores")
def evaluate_risk(
    payload: EvaluateRiskRequest = EvaluateRiskRequest(),
    db: Session = Depends(get_db)
):
    """Triggers batch 4-factor multi-criteria risk score (0-100) evaluation and optical verification proxy integration."""
    service = RiskService()
    recalc = payload.recalculate_all or False
    response = service.evaluate_risk_scores(db=db, recalculate_all=recalc)
    return response

@router.get("/risk", response_model=List[RiskScoreResponse], summary="Retrieve Multi-Modal Risk Scores")
def list_risk_scores(
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (LOW_RISK, MEDIUM_RISK, HIGH_RISK, CRITICAL_VERIFIED_RISK)"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum composite risk score (0-100)"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists evaluated thermal anomaly risk scores with sub-component breakdowns and optical verification confidence."""
    query = db.query(VerificationRiskScore)

    if risk_level:
        query = query.filter(VerificationRiskScore.risk_level == risk_level)
    if min_score is not None:
        query = query.filter(VerificationRiskScore.composite_risk_score >= min_score)

    scores = query.order_by(VerificationRiskScore.composite_risk_score.desc()).offset(offset).limit(limit).all()

    results = []
    for r in scores:
        fac = r.facility
        obs = r.observation
        breakdown_dict = None
        if r.risk_breakdown_json:
            try:
                breakdown_dict = json.loads(r.risk_breakdown_json)
            except Exception:
                pass

        res_dict = {
            "id": r.id,
            "observation_id": r.observation_id,
            "facility_id": r.facility_id,
            "composite_risk_score": r.composite_risk_score,
            "risk_level": r.risk_level,
            "spatial_proximity_score": r.spatial_proximity_score,
            "frp_multiplier_score": r.frp_multiplier_score,
            "facility_sensitivity_score": r.facility_sensitivity_score,
            "optical_verification_confidence": r.optical_verification_confidence,
            "verification_source": r.verification_source,
            "risk_breakdown_json": breakdown_dict,
            "evaluated_at": r.evaluated_at,
            "facility_name": fac.name if fac else None,
            "facility_type": fac.facility_type if fac else None,
            "latitude": obs.latitude if obs else None,
            "longitude": obs.longitude if obs else None
        }
        results.append(RiskScoreResponse(**res_dict))

    return results

@router.get("/risk/observation/{obs_id}", response_model=Optional[RiskScoreResponse], summary="Get Risk Profile for Single Observation")
def get_observation_risk(obs_id: int, db: Session = Depends(get_db)):
    """Retrieves composite risk score and optical verification metrics for a single thermal observation ID."""
    r = db.query(VerificationRiskScore).filter(
        VerificationRiskScore.observation_id == obs_id
    ).first()

    if not r:
        return None

    fac = r.facility
    obs = r.observation
    breakdown_dict = None
    if r.risk_breakdown_json:
        try:
            breakdown_dict = json.loads(r.risk_breakdown_json)
        except Exception:
            pass

    res_dict = {
        "id": r.id,
        "observation_id": r.observation_id,
        "facility_id": r.facility_id,
        "composite_risk_score": r.composite_risk_score,
        "risk_level": r.risk_level,
        "spatial_proximity_score": r.spatial_proximity_score,
        "frp_multiplier_score": r.frp_multiplier_score,
        "facility_sensitivity_score": r.facility_sensitivity_score,
        "optical_verification_confidence": r.optical_verification_confidence,
        "verification_source": r.verification_source,
        "risk_breakdown_json": breakdown_dict,
        "evaluated_at": r.evaluated_at,
        "facility_name": fac.name if fac else None,
        "facility_type": fac.facility_type if fac else None,
        "latitude": obs.latitude if obs else None,
        "longitude": obs.longitude if obs else None
    }
    return RiskScoreResponse(**res_dict)

@router.get("/analytics/risk-summary", response_model=RiskSummary, summary="Get Aggregate Risk Metrics")
def get_risk_summary(db: Session = Depends(get_db)):
    """Computes summary metrics for evaluated multi-modal risk scores."""
    total = db.query(func.count(VerificationRiskScore.id)).scalar() or 0
    if total == 0:
        return RiskSummary(
            total_evaluations=0,
            tier_breakdown={},
            avg_composite_score=0.0,
            highest_risk_observation=None
        )

    avg_score = db.query(func.avg(VerificationRiskScore.composite_risk_score)).scalar() or 0.0

    counts = db.query(
        VerificationRiskScore.risk_level, func.count(VerificationRiskScore.id)
    ).group_by(VerificationRiskScore.risk_level).all()
    tier_breakdown = {str(tier): count for tier, count in counts if tier}

    highest = db.query(VerificationRiskScore).order_by(
        VerificationRiskScore.composite_risk_score.desc()
    ).first()

    highest_dict = None
    if highest:
        fac = highest.facility
        highest_dict = {
            "observation_id": highest.observation_id,
            "facility_name": fac.name if fac else "Unassociated",
            "facility_type": fac.facility_type if fac else "none",
            "composite_risk_score": highest.composite_risk_score,
            "risk_level": highest.risk_level,
            "optical_confidence": highest.optical_verification_confidence
        }

    return RiskSummary(
        total_evaluations=total,
        tier_breakdown=tier_breakdown,
        avg_composite_score=round(float(avg_score), 2),
        highest_risk_observation=highest_dict
    )
