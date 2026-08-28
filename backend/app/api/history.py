from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.facility_history import FacilityHistoricalBehavior
from app.models.industrial_facility import IndustrialFacility
from app.schemas.facility_history import (
    FacilityHistoryResponse,
    RunHistoryRequest,
    RunHistoryResponse,
    HistorySummary
)
from app.services.history_service import HistoryService

router = APIRouter(tags=["Historical Facility Behavior"])

@router.post("/history/aggregate", response_model=RunHistoryResponse, summary="Run Historical Facility Behavior Aggregation Pipeline")
def run_history_aggregation(
    payload: RunHistoryRequest = RunHistoryRequest(),
    db: Session = Depends(get_db)
):
    """Triggers batch historical aggregation calculating P95/P99 FRP distributions and activity tiers for all facilities."""
    service = HistoryService()
    recalc = payload.recalculate_all or False
    response = service.run_historical_aggregation_pipeline(db=db, recalculate_all=recalc)
    return response

@router.get("/history", response_model=List[FacilityHistoryResponse], summary="Retrieve Facility Historical Baseline Profiles")
def list_facility_histories(
    activity_tier: Optional[str] = Query(None, description="Filter by tier (HIGHLY_PERSISTENT, MODERATELY_ACTIVE, SPORADIC, NO_HISTORICAL_ANOMALIES)"),
    min_observations: Optional[int] = Query(None, ge=0, description="Minimum historical observation count"),
    min_p95_frp: Optional[float] = Query(None, ge=0.0, description="Minimum P95 FRP in MW"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists historical facility behavior profiles with FRP percentile distribution metrics."""
    query = db.query(FacilityHistoricalBehavior)

    if activity_tier:
        query = query.filter(FacilityHistoricalBehavior.activity_tier == activity_tier)
    if min_observations is not None:
        query = query.filter(FacilityHistoricalBehavior.total_observations >= min_observations)
    if min_p95_frp is not None:
        query = query.filter(FacilityHistoricalBehavior.p95_frp >= min_p95_frp)

    profiles = query.order_by(FacilityHistoricalBehavior.p95_frp.desc()).offset(offset).limit(limit).all()

    results = []
    for p in profiles:
        fac = p.facility
        res_dict = {
            "id": p.id,
            "facility_id": p.facility_id,
            "total_observations": p.total_observations,
            "observation_days": p.observation_days,
            "min_frp": p.min_frp,
            "max_frp": p.max_frp,
            "mean_frp": p.mean_frp,
            "median_frp": p.median_frp,
            "p95_frp": p.p95_frp,
            "p99_frp": p.p99_frp,
            "day_count": p.day_count,
            "night_count": p.night_count,
            "day_night_ratio": p.day_night_ratio,
            "activity_tier": p.activity_tier,
            "first_observed": p.first_observed,
            "last_observed": p.last_observed,
            "updated_at": p.updated_at,
            "facility_name": fac.name if fac else None,
            "facility_type": fac.facility_type if fac else None
        }
        results.append(FacilityHistoryResponse(**res_dict))

    return results

@router.get("/history/facility/{fac_id}", response_model=Optional[FacilityHistoryResponse], summary="Get Historical Profile for Single Facility")
def get_facility_history_profile(fac_id: int, db: Session = Depends(get_db)):
    """Retrieves historical thermal behavior profile for a specific facility."""
    p = db.query(FacilityHistoricalBehavior).filter(
        FacilityHistoricalBehavior.facility_id == fac_id
    ).first()

    if not p:
        return None

    fac = p.facility
    res_dict = {
        "id": p.id,
        "facility_id": p.facility_id,
        "total_observations": p.total_observations,
        "observation_days": p.observation_days,
        "min_frp": p.min_frp,
        "max_frp": p.max_frp,
        "mean_frp": p.mean_frp,
        "median_frp": p.median_frp,
        "p95_frp": p.p95_frp,
        "p99_frp": p.p99_frp,
        "day_count": p.day_count,
        "night_count": p.night_count,
        "day_night_ratio": p.day_night_ratio,
        "activity_tier": p.activity_tier,
        "first_observed": p.first_observed,
        "last_observed": p.last_observed,
        "updated_at": p.updated_at,
        "facility_name": fac.name if fac else None,
        "facility_type": fac.facility_type if fac else None
    }
    return FacilityHistoryResponse(**res_dict)

@router.get("/analytics/historical-summary", response_model=HistorySummary, summary="Get Monitored Facilities Historical Analytics")
def get_history_summary(db: Session = Depends(get_db)):
    """Computes summary metrics for historical facility baselines."""
    total = db.query(func.count(FacilityHistoricalBehavior.id)).scalar() or 0
    if total == 0:
        return HistorySummary(
            total_monitored_facilities=0,
            tier_breakdown={},
            max_p95_frp_overall=0.0,
            highest_activity_facility=None
        )

    max_p95 = db.query(func.max(FacilityHistoricalBehavior.p95_frp)).scalar() or 0.0

    tier_counts = db.query(
        FacilityHistoricalBehavior.activity_tier, func.count(FacilityHistoricalBehavior.id)
    ).group_by(FacilityHistoricalBehavior.activity_tier).all()
    tier_breakdown = {str(tier): count for tier, count in tier_counts if tier}

    highest_fac = db.query(FacilityHistoricalBehavior).order_by(
        FacilityHistoricalBehavior.total_observations.desc()
    ).first()

    highest_dict = None
    if highest_fac and highest_fac.facility:
        highest_dict = {
            "facility_id": highest_fac.facility_id,
            "name": highest_fac.facility.name,
            "facility_type": highest_fac.facility.facility_type,
            "total_observations": highest_fac.total_observations,
            "p95_frp": highest_fac.p95_frp
        }

    return HistorySummary(
        total_monitored_facilities=total,
        tier_breakdown=tier_breakdown,
        max_p95_frp_overall=round(float(max_p95), 2),
        highest_activity_facility=highest_dict
    )
