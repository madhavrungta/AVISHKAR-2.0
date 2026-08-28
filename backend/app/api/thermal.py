from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.thermal_observation import ThermalObservation
from app.schemas.thermal_observation import ThermalObservationResponse, AnalyticsSummary

router = APIRouter(tags=["Thermal Observations"])

@router.get("/thermal-observations", response_model=List[ThermalObservationResponse], summary="Retrieve Thermal Anomalies")
def list_thermal_observations(
    bbox: Optional[str] = Query(None, description="Bounding box in format 'west,south,east,north'"),
    satellite: Optional[str] = Query(None, description="Filter by satellite (e.g. N, N20, N21)"),
    source: Optional[str] = Query(None, description="Filter by FIRMS source (e.g. VIIRS_SNPP_NRT)"),
    min_frp: Optional[float] = Query(None, ge=0.0, description="Minimum Fire Radiative Power (MW)"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset pagination"),
    db: Session = Depends(get_db)
):
    """
    Returns a list of NASA FIRMS thermal anomaly observations based on spatial,
    temporal, or sensor filters.
    
    IMPORTANT: Every point represents a THERMAL ANOMALY, NOT a confirmed fire.
    """
    query = db.query(ThermalObservation)

    if satellite:
        query = query.filter(ThermalObservation.satellite == satellite)
    if source:
        query = query.filter(ThermalObservation.source == source)
    if min_frp is not None:
        query = query.filter(ThermalObservation.frp >= min_frp)

    if bbox:
        try:
            coords = [float(c.strip()) for c in bbox.split(",")]
            if len(coords) == 4:
                w, s, e, n = coords
                query = query.filter(
                    ThermalObservation.longitude >= w,
                    ThermalObservation.longitude <= e,
                    ThermalObservation.latitude >= s,
                    ThermalObservation.latitude <= n
                )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid bbox format. Use 'west,south,east,north'.")

    observations = query.order_by(ThermalObservation.observation_timestamp.desc()).offset(offset).limit(limit).all()

    # Format geometry WKT for response payload
    results = []
    for obs in observations:
        geom_wkt = f"POINT({obs.longitude} {obs.latitude})"
        obs_dict = {
            "id": obs.id,
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "bright_ti4": obs.bright_ti4,
            "bright_ti5": obs.bright_ti5,
            "scan": obs.scan,
            "track": obs.track,
            "acq_date": obs.acq_date,
            "acq_time": obs.acq_time,
            "satellite": obs.satellite,
            "instrument": obs.instrument,
            "confidence": obs.confidence,
            "version": obs.version,
            "frp": obs.frp,
            "daynight": obs.daynight,
            "observation_timestamp": obs.observation_timestamp,
            "ingestion_timestamp": obs.ingestion_timestamp,
            "source": obs.source,
            "ingestion_batch_id": obs.ingestion_batch_id,
            "geometry_wkt": geom_wkt
        }
        results.append(ThermalObservationResponse(**obs_dict))

    return results

@router.get("/thermal-observations/{obs_id}", response_model=ThermalObservationResponse, summary="Get Single Thermal Anomaly Detail")
def get_thermal_observation(obs_id: int, db: Session = Depends(get_db)):
    """Retrieves single thermal anomaly detail by ID."""
    obs = db.query(ThermalObservation).filter(ThermalObservation.id == obs_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail=f"Thermal observation #{obs_id} not found.")

    geom_wkt = f"POINT({obs.longitude} {obs.latitude})"
    obs_dict = {
        "id": obs.id,
        "latitude": obs.latitude,
        "longitude": obs.longitude,
        "bright_ti4": obs.bright_ti4,
        "bright_ti5": obs.bright_ti5,
        "scan": obs.scan,
        "track": obs.track,
        "acq_date": obs.acq_date,
        "acq_time": obs.acq_time,
        "satellite": obs.satellite,
        "instrument": obs.instrument,
        "confidence": obs.confidence,
        "version": obs.version,
        "frp": obs.frp,
        "daynight": obs.daynight,
        "observation_timestamp": obs.observation_timestamp,
        "ingestion_timestamp": obs.ingestion_timestamp,
        "source": obs.source,
        "ingestion_batch_id": obs.ingestion_batch_id,
        "geometry_wkt": geom_wkt
    }
    return ThermalObservationResponse(**obs_dict)

@router.get("/analytics/summary", response_model=AnalyticsSummary, summary="Get Aggregated Thermal Analytics")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Computes summary stats of ingested thermal anomaly observations."""
    total = db.query(func.count(ThermalObservation.id)).scalar() or 0
    if total == 0:
        return AnalyticsSummary(
            total_observations=0,
            max_frp=None,
            min_frp=None,
            avg_frp=None,
            latest_observation=None,
            satellites_breakdown={},
            sources_breakdown={}
        )

    stats = db.query(
        func.max(ThermalObservation.frp),
        func.min(ThermalObservation.frp),
        func.avg(ThermalObservation.frp),
        func.max(ThermalObservation.observation_timestamp)
    ).first()

    sat_counts = db.query(
        ThermalObservation.satellite, func.count(ThermalObservation.id)
    ).group_by(ThermalObservation.satellite).all()
    sat_breakdown = {str(sat): count for sat, count in sat_counts if sat}

    src_counts = db.query(
        ThermalObservation.source, func.count(ThermalObservation.id)
    ).group_by(ThermalObservation.source).all()
    src_breakdown = {str(src): count for src, count in src_counts if src}

    return AnalyticsSummary(
        total_observations=total,
        max_frp=round(float(stats[0]), 2) if stats[0] is not None else None,
        min_frp=round(float(stats[1]), 2) if stats[1] is not None else None,
        avg_frp=round(float(stats[2]), 2) if stats[2] is not None else None,
        latest_observation=stats[3],
        satellites_breakdown=sat_breakdown,
        sources_breakdown=src_breakdown
    )
