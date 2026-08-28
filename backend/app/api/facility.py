import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.industrial_facility import IndustrialFacility
from app.schemas.industrial_facility import (
    IndustrialFacilityResponse, 
    OSMIngestionRequest, 
    OSMIngestionResponse, 
    FacilityAnalyticsSummary
)
from app.services.osm_service import OSMDataService, OSMIngestionError

router = APIRouter(tags=["Industrial Facilities"])

@router.get("/industrial-facilities", response_model=List[IndustrialFacilityResponse], summary="Retrieve OSM Industrial Facilities")
def list_industrial_facilities(
    bbox: Optional[str] = Query(None, description="Bounding box 'west,south,east,north'"),
    facility_type: Optional[str] = Query(None, description="Filter by category (refinery, power_plant, steel_works, chemical, industrial)"),
    min_area: Optional[float] = Query(None, ge=0.0, description="Minimum surface area in m²"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """Returns a list of OpenStreetMap industrial facilities and infrastructure boundaries."""
    query = db.query(IndustrialFacility)

    if facility_type:
        query = query.filter(IndustrialFacility.facility_type == facility_type)
    if min_area is not None:
        query = query.filter(IndustrialFacility.area_sqm >= min_area)

    if bbox:
        try:
            coords = [float(c.strip()) for c in bbox.split(",")]
            if len(coords) == 4:
                w, s, e, n = coords
                query = query.filter(
                    IndustrialFacility.longitude >= w,
                    IndustrialFacility.longitude <= e,
                    IndustrialFacility.latitude >= s,
                    IndustrialFacility.latitude <= n
                )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid bbox format. Use 'west,south,east,north'.")

    facilities = query.order_by(IndustrialFacility.area_sqm.desc()).offset(offset).limit(limit).all()

    results = []
    for fac in facilities:
        geom_wkt = f"POINT({fac.longitude} {fac.latitude})"
        raw_tags_dict = None
        if fac.raw_tags:
            try:
                raw_tags_dict = json.loads(fac.raw_tags)
            except Exception:
                pass

        res_dict = {
            "id": fac.id,
            "osm_id": fac.osm_id,
            "name": fac.name,
            "facility_type": fac.facility_type,
            "operator": fac.operator,
            "latitude": fac.latitude,
            "longitude": fac.longitude,
            "area_sqm": fac.area_sqm,
            "raw_tags": raw_tags_dict,
            "ingestion_batch_id": fac.ingestion_batch_id,
            "created_at": fac.created_at,
            "geometry_wkt": geom_wkt
        }
        results.append(IndustrialFacilityResponse(**res_dict))

    return results

@router.get("/industrial-facilities/{fac_id}", response_model=IndustrialFacilityResponse, summary="Get Industrial Facility Detail")
def get_industrial_facility(fac_id: int, db: Session = Depends(get_db)):
    """Retrieves single facility detail by ID."""
    fac = db.query(IndustrialFacility).filter(IndustrialFacility.id == fac_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail=f"Industrial facility #{fac_id} not found.")

    geom_wkt = f"POINT({fac.longitude} {fac.latitude})"
    raw_tags_dict = None
    if fac.raw_tags:
        try:
            raw_tags_dict = json.loads(fac.raw_tags)
        except Exception:
            pass

    res_dict = {
        "id": fac.id,
        "osm_id": fac.osm_id,
        "name": fac.name,
        "facility_type": fac.facility_type,
        "operator": fac.operator,
        "latitude": fac.latitude,
        "longitude": fac.longitude,
        "area_sqm": fac.area_sqm,
        "raw_tags": raw_tags_dict,
        "ingestion_batch_id": fac.ingestion_batch_id,
        "created_at": fac.created_at,
        "geometry_wkt": geom_wkt
    }
    return IndustrialFacilityResponse(**res_dict)

@router.post("/ingestion/osm", response_model=OSMIngestionResponse, summary="Trigger OSM Industrial Ingestion")
def trigger_osm_ingestion(
    payload: OSMIngestionRequest = OSMIngestionRequest(),
    db: Session = Depends(get_db)
):
    """Triggers OpenStreetMap Overpass API query for industrial infrastructure."""
    service = OSMDataService()
    bbox_str = payload.area or "68.0,6.0,97.0,37.0"

    try:
        response = service.ingest_osm_facilities(db=db, bbox_str=bbox_str)
        return response
    except OSMIngestionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(exc)}")

@router.get("/analytics/facilities-summary", response_model=FacilityAnalyticsSummary, summary="Get Industrial Facility Analytics")
def get_facilities_summary(db: Session = Depends(get_db)):
    """Computes summary metrics for ingested industrial facilities."""
    total = db.query(func.count(IndustrialFacility.id)).scalar() or 0
    if total == 0:
        return FacilityAnalyticsSummary(
            total_facilities=0,
            total_area_sqkm=0.0,
            type_breakdown={},
            largest_facility=None
        )

    sum_area_sqm = db.query(func.sum(IndustrialFacility.area_sqm)).scalar() or 0.0
    total_area_sqkm = round(float(sum_area_sqm) / 1_000_000.0, 2)

    type_counts = db.query(
        IndustrialFacility.facility_type, func.count(IndustrialFacility.id)
    ).group_by(IndustrialFacility.facility_type).all()
    type_breakdown = {str(ftype): count for ftype, count in type_counts if ftype}

    largest = db.query(IndustrialFacility).order_by(IndustrialFacility.area_sqm.desc()).first()
    largest_dict = None
    if largest:
        largest_dict = {
            "id": largest.id,
            "name": largest.name,
            "facility_type": largest.facility_type,
            "area_sqm": largest.area_sqm,
            "latitude": largest.latitude,
            "longitude": largest.longitude
        }

    return FacilityAnalyticsSummary(
        total_facilities=total,
        total_area_sqkm=total_area_sqkm,
        type_breakdown=type_breakdown,
        largest_facility=largest_dict
    )
