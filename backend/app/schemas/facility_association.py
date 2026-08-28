from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AssociationResponse(BaseModel):
    id: int
    observation_id: int
    facility_id: int
    distance_meters: float
    association_type: str
    created_at: datetime
    
    # Nested detail fields
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    facility_latitude: Optional[float] = None
    facility_longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class RunAssociationRequest(BaseModel):
    max_distance_meters: Optional[float] = Field(3000.0, ge=100.0, le=50000.0, description="Maximum radius threshold in meters")
    recalculate_all: Optional[bool] = Field(False, description="Whether to recompute existing associations")

class RunAssociationResponse(BaseModel):
    status: str
    total_observations_processed: int
    associations_created: int
    direct_matches: int
    proximate_matches: int
    vicinity_matches: int
    unassociated: int

class AssociationSummary(BaseModel):
    total_associations: int
    direct_matches_count: int
    proximate_matches_count: int
    vicinity_matches_count: int
    type_breakdown: Dict[str, int]
