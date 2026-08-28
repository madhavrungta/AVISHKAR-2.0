from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.schemas.thermal_observation import FIRMSIngestionRequest, FIRMSIngestionResponse
from app.services.firms_service import FIRMSDataService, FIRMSIngestionError

router = APIRouter(tags=["Data Ingestion"])

@router.post("/ingestion/firms", response_model=FIRMSIngestionResponse, summary="Trigger NASA FIRMS API Data Ingestion")
def trigger_firms_ingestion(
    payload: FIRMSIngestionRequest = FIRMSIngestionRequest(),
    db: Session = Depends(get_db)
):
    """
    Triggers on-demand ingestion from NASA FIRMS API into raw storage and PostGIS DB.
    
    Required Environment Variable:
    - FIRMS_MAP_KEY (Set inside backend/.env)
    """
    if not settings.is_firms_key_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FIRMS_MAP_KEY is not configured. Add it to backend/.env."
        )

    service = FIRMSDataService()

    source = payload.source or settings.FIRMS_SOURCE
    area = payload.area or settings.FIRMS_AREA
    days = payload.days or settings.FIRMS_DAYS
    date = payload.date

    try:
        response = service.ingest_firms_data(
            db=db,
            source=source,
            area=area,
            days=days,
            date=date
        )
        return response
    except FIRMSIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during ingestion: {str(exc)}"
        )
