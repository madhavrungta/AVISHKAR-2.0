from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
from app.services.landcover_service import LandCoverService

router = APIRouter(tags=["Land Cover"])
landcover_service = LandCoverService()

@router.get("/landcover")
def get_landcover(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="WGS84 latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="WGS84 longitude coordinate")
) -> Dict[str, Any]:
    """
    Retrieves ESA WorldCover 10m land-cover classification for a given coordinate.
    Used for Phase 4A Land-Cover feature extraction.
    """
    try:
        return landcover_service.get_land_cover(latitude, longitude)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Land-cover service error: {str(e)}")
