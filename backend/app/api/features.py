from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.services.feature_engineering_service import FeatureEngineeringService

router = APIRouter(tags=["Multi-Modal Feature Engineering"])
feature_service = FeatureEngineeringService()

@router.get("/features/{event_id}")
def get_engineered_features(
    event_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Constructs a multi-modal engineered feature vector for a thermal observation event.
    Used for Phase 4C feature engineering inspection and future ML dataset assembly.
    """
    try:
        return feature_service.build_feature_vector(db=db, event_id=event_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature engineering service error: {str(e)}")
