from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.services.persistence_service import PersistenceService

router = APIRouter(tags=["Temporal Persistence"])
persistence_service = PersistenceService()

@router.get("/persistence/{event_id}")
def get_temporal_persistence(
    event_id: int,
    lookback_days: int = Query(default=30, ge=1, le=365, description="Lookback window in calendar days"),
    spatial_radius_m: float = Query(default=100.0, ge=1.0, le=10000.0, description="Geospatial neighborhood radius in meters"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculates spatio-temporal persistence metrics around a thermal observation event.
    Used for Phase 4B temporal feature engineering.
    """
    try:
        return persistence_service.get_persistence_features(
            db=db,
            event_id=event_id,
            lookback_days=lookback_days,
            spatial_radius_m=spatial_radius_m
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persistence service error: {str(e)}")
