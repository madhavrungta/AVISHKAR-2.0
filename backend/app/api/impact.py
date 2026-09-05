from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.impact import ImpactAssessmentResponse
from app.services.impact_service import ImpactAssessmentService

router = APIRouter(tags=["Impact Assessment"])

@router.get(
    "/impact/{event_id}",
    response_model=ImpactAssessmentResponse,
    summary="Assess Nearby Industrial Entities Exposed to Thermal Event"
)
def get_event_impact_assessment(
    event_id: int,
    assessment_radius_km: float = Query(
        5.0, 
        ge=0.1, 
        le=50.0, 
        description="Spatial assessment search radius in kilometers (min: 0.1 km, max: 50.0 km)"
    ),
    db: Session = Depends(get_db)
):
    """
    Identifies all industrial facilities located within the specified assessment radius
    of a thermal anomaly event.
    
    Returns entities sorted nearest to farthest. Proximity indicates potential exposure 
    context and does not establish fire causality.
    """
    service = ImpactAssessmentService()
    result = service.assess_impact(
        db=db,
        event_id=event_id,
        assessment_radius_km=assessment_radius_km
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal observation event #{event_id} not found."
        )

    return result
