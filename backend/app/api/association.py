from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.facility_association import ThermalFacilityAssociation
from app.models.industrial_facility import IndustrialFacility
from app.models.thermal_observation import ThermalObservation
from app.schemas.facility_association import (
    AssociationResponse,
    RunAssociationRequest,
    RunAssociationResponse,
    AssociationSummary
)
from app.services.association_service import AssociationService

router = APIRouter(tags=["Facility Associations"])

@router.post("/associations/run", response_model=RunAssociationResponse, summary="Run Thermal -> Facility Spatial Association Engine")
def run_association_job(
    payload: RunAssociationRequest = RunAssociationRequest(),
    db: Session = Depends(get_db)
):
    """Triggers spatial association job matching thermal anomalies to nearby industrial facilities."""
    service = AssociationService()
    max_dist = payload.max_distance_meters or 3000.0
    recalc = payload.recalculate_all or False

    response = service.run_association_pipeline(
        db=db,
        max_distance_meters=max_dist,
        recalculate_all=recalc
    )
    return response

@router.get("/associations", response_model=List[AssociationResponse], summary="Retrieve Thermal -> Facility Associations")
def list_associations(
    facility_id: Optional[int] = Query(None, description="Filter by industrial facility ID"),
    observation_id: Optional[int] = Query(None, description="Filter by thermal observation ID"),
    association_type: Optional[str] = Query(None, description="Filter by tier (DIRECT_MATCH, PROXIMATE_MATCH, VICINITY_MATCH)"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in meters"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists thermal observation to facility associations with spatial distance and type filters."""
    query = db.query(ThermalFacilityAssociation)

    if facility_id:
        query = query.filter(ThermalFacilityAssociation.facility_id == facility_id)
    if observation_id:
        query = query.filter(ThermalFacilityAssociation.observation_id == observation_id)
    if association_type:
        query = query.filter(ThermalFacilityAssociation.association_type == association_type)
    if max_distance is not None:
        query = query.filter(ThermalFacilityAssociation.distance_meters <= max_distance)

    assocs = query.order_by(ThermalFacilityAssociation.distance_meters.asc()).offset(offset).limit(limit).all()

    results = []
    for a in assocs:
        fac = a.facility
        res_dict = {
            "id": a.id,
            "observation_id": a.observation_id,
            "facility_id": a.facility_id,
            "distance_meters": a.distance_meters,
            "association_type": a.association_type,
            "created_at": a.created_at,
            "facility_name": fac.name if fac else None,
            "facility_type": fac.facility_type if fac else None,
            "facility_latitude": fac.latitude if fac else None,
            "facility_longitude": fac.longitude if fac else None
        }
        results.append(AssociationResponse(**res_dict))

    return results

@router.get("/associations/thermal/{obs_id}", response_model=Optional[AssociationResponse], summary="Get Association Detail for Observation")
def get_thermal_association(obs_id: int, db: Session = Depends(get_db)):
    """Retrieves facility association details for a specific thermal observation."""
    assoc = db.query(ThermalFacilityAssociation).filter(
        ThermalFacilityAssociation.observation_id == obs_id
    ).first()

    if not assoc:
        return None

    fac = assoc.facility
    res_dict = {
        "id": assoc.id,
        "observation_id": assoc.observation_id,
        "facility_id": assoc.facility_id,
        "distance_meters": assoc.distance_meters,
        "association_type": assoc.association_type,
        "created_at": assoc.created_at,
        "facility_name": fac.name if fac else None,
        "facility_type": fac.facility_type if fac else None,
        "facility_latitude": fac.latitude if fac else None,
        "facility_longitude": fac.longitude if fac else None
    }
    return AssociationResponse(**res_dict)

@router.get("/associations/facility/{fac_id}", response_model=List[AssociationResponse], summary="Get All Thermal Anomalies for Facility")
def get_facility_associations(fac_id: int, db: Session = Depends(get_db)):
    """Retrieves all thermal anomaly observations associated with a specific facility."""
    assocs = db.query(ThermalFacilityAssociation).filter(
        ThermalFacilityAssociation.facility_id == fac_id
    ).order_by(ThermalFacilityAssociation.distance_meters.asc()).all()

    results = []
    for a in assocs:
        fac = a.facility
        res_dict = {
            "id": a.id,
            "observation_id": a.observation_id,
            "facility_id": a.facility_id,
            "distance_meters": a.distance_meters,
            "association_type": a.association_type,
            "created_at": a.created_at,
            "facility_name": fac.name if fac else None,
            "facility_type": fac.facility_type if fac else None,
            "facility_latitude": fac.latitude if fac else None,
            "facility_longitude": fac.longitude if fac else None
        }
        results.append(AssociationResponse(**res_dict))

    return results
