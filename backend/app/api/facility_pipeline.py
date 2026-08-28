import logging
import datetime
import statistics
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.facility import Facility
from app.models.facility_observation import FacilityObservation
from app.models.thermal_observation import ThermalObservation
from app.models.facility_baseline import FacilityBaseline
from app.services.facility_association_service import FacilityAssociationService

logger = logging.getLogger("firms_app.facility_pipeline")
router = APIRouter(tags=["Step 1 Facility Pipeline"])

# Pydantic response models
class FacilityBase(BaseModel):
    id: int
    osm_id: str
    name: Optional[str]
    facility_type: str
    latitude: float
    longitude: float
    source: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class AssociatedObservationResponse(BaseModel):
    id: int
    observation_time: Optional[datetime.datetime]
    latitude: float
    longitude: float
    frp: Optional[float]
    bright_ti4: Optional[float]
    bright_ti5: Optional[float]
    confidence: Optional[str]
    satellite: Optional[str]
    instrument: Optional[str]
    daynight: Optional[str]
    distance_m: float
    association_method: str

class BaselineResponse(BaseModel):
    facility_id: int
    baseline_start: Optional[datetime.datetime]
    baseline_end: Optional[datetime.datetime]
    observation_count: int
    median_frp: Optional[float]
    p95_frp: Optional[float]
    p99_frp: Optional[float]
    mad_frp: Optional[float]
    median_brightness_ti4: Optional[float]
    median_brightness_ti5: Optional[float]

class TimelinePoint(BaseModel):
    timestamp: datetime.datetime
    frp: float
    observation_id: int

class RunAssociationRequest(BaseModel):
    radius_meters: Optional[float] = None

class AssociationRunSummary(BaseModel):
    status: str
    observations_processed: int
    associations_created: int

class PipelineSummaryResponse(BaseModel):
    total_facilities: int
    total_associations: int
    facilities_with_baseline: int
    avg_associations_per_facility: float

# GET /facilities
@router.get("/facilities", response_model=List[FacilityBase], summary="List all facilities")
def list_facilities(
    facility_type: Optional[str] = Query(None, description="Filter by facility type"),
    name: Optional[str] = Query(None, description="Filter by name (case-insensitive substring)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Facility)
    if facility_type:
        query = query.filter(Facility.facility_type == facility_type)
    if name:
        query = query.filter(Facility.name.ilike(f"%{name}%"))
    return query.offset(offset).limit(limit).all()

# GET /facilities/{facility_id}
@router.get("/facilities/{facility_id}", response_model=FacilityBase, summary="Get facility details")
def get_facility(facility_id: int, db: Session = Depends(get_db)):
    fac = db.query(Facility).filter(Facility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail=f"Facility #{facility_id} not found")
    return fac

# GET /facilities/{facility_id}/observations
@router.get("/facilities/{facility_id}/observations", response_model=List[AssociatedObservationResponse], summary="Get associated observations")
def get_facility_observations(
    facility_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    # Verify facility exists
    fac = db.query(Facility).filter(Facility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail=f"Facility #{facility_id} not found")

    query = db.query(ThermalObservation, FacilityObservation.distance_m, FacilityObservation.association_method) \
              .join(FacilityObservation, FacilityObservation.observation_id == ThermalObservation.id) \
              .filter(FacilityObservation.facility_id == facility_id)

    if start_date:
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ThermalObservation.observation_timestamp >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

    if end_date:
        try:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            # End of day filter
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(ThermalObservation.observation_timestamp <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

    # Order by observation timestamp
    results = query.order_by(ThermalObservation.observation_timestamp.asc()).limit(limit).all()

    response = []
    for obs, dist, method in results:
        response.append(
            AssociatedObservationResponse(
                id=obs.id,
                observation_time=obs.observation_time or obs.observation_timestamp,
                latitude=obs.latitude,
                longitude=obs.longitude,
                frp=obs.frp,
                bright_ti4=obs.bright_ti4,
                bright_ti5=obs.bright_ti5,
                confidence=obs.confidence,
                satellite=obs.satellite,
                instrument=obs.instrument,
                daynight=obs.daynight,
                distance_m=dist,
                association_method=method
            )
        )
    return response

# GET /facilities/{facility_id}/baseline
@router.get("/facilities/{facility_id}/baseline", response_model=BaselineResponse, summary="Get facility statistical baseline")
def get_facility_baseline(facility_id: int, db: Session = Depends(get_db)):
    fac = db.query(Facility).filter(Facility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail=f"Facility #{facility_id} not found")

    # Fetch all associated observations
    assoc_obs = db.query(ThermalObservation) \
                  .join(FacilityObservation, FacilityObservation.observation_id == ThermalObservation.id) \
                  .filter(FacilityObservation.facility_id == facility_id) \
                  .all()

    count = len(assoc_obs)
    if count == 0:
        return BaselineResponse(
            facility_id=facility_id,
            baseline_start=None,
            baseline_end=None,
            observation_count=0,
            median_frp=None,
            p95_frp=None,
            p99_frp=None,
            mad_frp=None,
            median_brightness_ti4=None,
            median_brightness_ti5=None
        )

    frp_vals = [o.frp for o in assoc_obs if o.frp is not None]
    ti4_vals = [o.bright_ti4 for o in assoc_obs if o.bright_ti4 is not None]
    ti5_vals = [o.bright_ti5 for o in assoc_obs if o.bright_ti5 is not None]
    timestamps = [o.observation_timestamp for o in assoc_obs if o.observation_timestamp]

    # Calculate statistics
    med_frp = statistics.median(frp_vals) if frp_vals else None
    
    # Custom percentiles calculation (handles missing or single values)
    p95 = None
    p99 = None
    if frp_vals:
        frp_sorted = sorted(frp_vals)
        n = len(frp_sorted)
        p95 = frp_sorted[max(0, min(n - 1, int(n * 0.95)))]
        p99 = frp_sorted[max(0, min(n - 1, int(n * 0.99)))]

    # MAD (Median Absolute Deviation)
    mad = None
    if frp_vals and med_frp is not None:
        abs_deviations = [abs(x - med_frp) for x in frp_vals]
        mad = statistics.median(abs_deviations)

    med_ti4 = statistics.median(ti4_vals) if ti4_vals else None
    med_ti5 = statistics.median(ti5_vals) if ti5_vals else None
    start_time = min(timestamps) if timestamps else None
    end_time = max(timestamps) if timestamps else None

    # Sync with facility_baselines table
    baseline = db.query(FacilityBaseline).filter(FacilityBaseline.facility_id == facility_id).first()
    if not baseline:
        baseline = FacilityBaseline(
            facility_id=facility_id,
            baseline_start=start_time or datetime.datetime.utcnow(),
            baseline_end=end_time or datetime.datetime.utcnow(),
            observation_count=count,
            median_frp=med_frp,
            p95_frp=p95,
            p99_frp=p99,
            mad_frp=mad,
            median_brightness_ti4=med_ti4,
            median_brightness_ti5=med_ti5
        )
        db.add(baseline)
    else:
        baseline.baseline_start = start_time or baseline.baseline_start
        baseline.baseline_end = end_time or baseline.baseline_end
        baseline.observation_count = count
        baseline.median_frp = med_frp
        baseline.p95_frp = p95
        baseline.p99_frp = p99
        baseline.mad_frp = mad
        baseline.median_brightness_ti4 = med_ti4
        baseline.median_brightness_ti5 = med_ti5
        baseline.updated_at = datetime.datetime.utcnow()
    db.commit()

    return BaselineResponse(
        facility_id=facility_id,
        baseline_start=start_time,
        baseline_end=end_time,
        observation_count=count,
        median_frp=med_frp,
        p95_frp=p95,
        p99_frp=p99,
        mad_frp=mad,
        median_brightness_ti4=med_ti4,
        median_brightness_ti5=med_ti5
    )

# GET /facilities/{facility_id}/timeline
@router.get("/facilities/{facility_id}/timeline", response_model=List[TimelinePoint], summary="Get facility thermal timeline")
def get_facility_timeline(facility_id: int, db: Session = Depends(get_db)):
    fac = db.query(Facility).filter(Facility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail=f"Facility #{facility_id} not found")

    results = db.query(ThermalObservation) \
                .join(FacilityObservation, FacilityObservation.observation_id == ThermalObservation.id) \
                .filter(FacilityObservation.facility_id == facility_id) \
                .order_by(ThermalObservation.observation_timestamp.asc()) \
                .all()

    return [
        TimelinePoint(
            timestamp=o.observation_time or o.observation_timestamp,
            frp=o.frp or 0.0,
            observation_id=o.id
        ) for o in results
    ]

# POST /analytics/facility-association
@router.post("/analytics/facility-association", response_model=AssociationRunSummary, summary="Trigger association job")
def run_facility_association(payload: RunAssociationRequest = RunAssociationRequest(), db: Session = Depends(get_db)):
    service = FacilityAssociationService(radius_meters=payload.radius_meters)
    
    # Process observations that have not been processed for the new "facility_observations" table
    observations = db.query(ThermalObservation).all()
    
    associations_created = 0
    for obs in observations:
        matches = service.associate_observation(db, obs)
        associations_created += len(matches)
        
    return AssociationRunSummary(
        status="success",
        observations_processed=len(observations),
        associations_created=associations_created
    )

# GET /analytics/facilities/summary
@router.get("/analytics/facilities/summary", response_model=PipelineSummaryResponse, summary="Get summary analytics")
def get_pipeline_summary(db: Session = Depends(get_db)):
    total_facs = db.query(func.count(Facility.id)).scalar() or 0
    total_assocs = db.query(func.count(FacilityObservation.id)).scalar() or 0
    facs_with_baseline = db.query(func.count(FacilityBaseline.id)).scalar() or 0
    
    avg_assocs = 0.0
    if total_facs > 0:
        avg_assocs = round(total_assocs / total_facs, 2)
        
    return PipelineSummaryResponse(
        total_facilities=total_facs,
        total_associations=total_assocs,
        facilities_with_baseline=facs_with_baseline,
        avg_associations_per_facility=avg_assocs
    )
