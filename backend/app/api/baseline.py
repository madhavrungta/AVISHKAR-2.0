from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.facility_baseline import FacilityNormalBaseline
from app.models.industrial_facility import IndustrialFacility
from app.schemas.facility_baseline import (
    FacilityBaselineResponse,
    GenerateBaselineRequest,
    GenerateBaselineResponse,
    BaselineSummary
)
from app.services.baseline_service import BaselineService

router = APIRouter(tags=["Facility Normal Baselines"])

@router.post("/baselines/generate", response_model=GenerateBaselineResponse, summary="Generate Facility Normal Thermal Baselines")
def generate_baselines(
    payload: GenerateBaselineRequest = GenerateBaselineRequest(),
    db: Session = Depends(get_db)
):
    """Triggers batch generation of expected normal operating thermal envelope (P50, P95, P99 bounds) per facility."""
    service = BaselineService()
    recalc = payload.recalculate_all or False
    response = service.generate_facility_baselines(db=db, recalculate_all=recalc)
    return response

@router.get("/baselines", response_model=List[FacilityBaselineResponse], summary="Retrieve Facility Normal Baselines")
def list_baselines(
    baseline_status: Optional[str] = Query(None, description="Filter by status (ESTABLISHED, PRELIMINARY_DEFAULT)"),
    min_p95_frp: Optional[float] = Query(None, ge=0.0, description="Minimum P95 upper operating bound (MW)"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists facility normal thermal baselines and upper operating envelope bounds."""
    query = db.query(FacilityNormalBaseline)

    if baseline_status:
        query = query.filter(FacilityNormalBaseline.baseline_status == baseline_status)
    if min_p95_frp is not None:
        query = query.filter(FacilityNormalBaseline.baseline_frp_p95 >= min_p95_frp)

    baselines = query.order_by(FacilityNormalBaseline.baseline_frp_p95.desc()).offset(offset).limit(limit).all()

    results = []
    for b in baselines:
        fac = b.facility
        res_dict = {
            "id": b.id,
            "facility_id": b.facility_id,
            "baseline_frp_p50": b.baseline_frp_p50,
            "baseline_frp_p95": b.baseline_frp_p95,
            "baseline_frp_p99": b.baseline_frp_p99,
            "monthly_frequency": b.monthly_frequency,
            "day_night_preference": b.day_night_preference,
            "baseline_status": b.baseline_status,
            "updated_at": b.updated_at,
            "facility_name": fac.name if fac else None,
            "facility_type": fac.facility_type if fac else None
        }
        results.append(FacilityBaselineResponse(**res_dict))

    return results

@router.get("/baselines/facility/{fac_id}", response_model=Optional[FacilityBaselineResponse], summary="Get Baseline for Single Facility")
def get_facility_baseline(fac_id: int, db: Session = Depends(get_db)):
    """Retrieves normal thermal operating baseline profile for a single facility."""
    b = db.query(FacilityNormalBaseline).filter(
        FacilityNormalBaseline.facility_id == fac_id
    ).first()

    if not b:
        return None

    fac = b.facility
    res_dict = {
        "id": b.id,
        "facility_id": b.facility_id,
        "baseline_frp_p50": b.baseline_frp_p50,
        "baseline_frp_p95": b.baseline_frp_p95,
        "baseline_frp_p99": b.baseline_frp_p99,
        "monthly_frequency": b.monthly_frequency,
        "day_night_preference": b.day_night_preference,
        "baseline_status": b.baseline_status,
        "updated_at": b.updated_at,
        "facility_name": fac.name if fac else None,
        "facility_type": fac.facility_type if fac else None
    }
    return FacilityBaselineResponse(**res_dict)

@router.get("/analytics/baselines-summary", response_model=BaselineSummary, summary="Get Aggregate Facility Baseline Metrics")
def get_baselines_summary(db: Session = Depends(get_db)):
    """Computes summary stats across established facility normal operating baselines."""
    total = db.query(func.count(FacilityNormalBaseline.id)).scalar() or 0
    if total == 0:
        return BaselineSummary(
            total_baselines=0,
            established_count=0,
            preliminary_count=0,
            avg_p95_frp_overall=0.0
        )

    established = db.query(func.count(FacilityNormalBaseline.id)).filter(
        FacilityNormalBaseline.baseline_status == "ESTABLISHED"
    ).scalar() or 0

    preliminary = db.query(func.count(FacilityNormalBaseline.id)).filter(
        FacilityNormalBaseline.baseline_status == "PRELIMINARY_DEFAULT"
    ).scalar() or 0

    avg_p95 = db.query(func.avg(FacilityNormalBaseline.baseline_frp_p95)).scalar() or 0.0

    return BaselineSummary(
        total_baselines=total,
        established_count=established,
        preliminary_count=preliminary,
        avg_p95_frp_overall=round(float(avg_p95), 2)
    )
