from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class FacilityHistoryResponse(BaseModel):
    id: int
    facility_id: int
    total_observations: int
    observation_days: int
    min_frp: float
    max_frp: float
    mean_frp: float
    median_frp: float
    p95_frp: float
    p99_frp: float
    day_count: int
    night_count: int
    day_night_ratio: float
    activity_tier: str
    first_observed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    updated_at: datetime

    # Facility detail fields
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RunHistoryRequest(BaseModel):
    recalculate_all: Optional[bool] = Field(False, description="Whether to recompute historical profiles for all facilities")

class RunHistoryResponse(BaseModel):
    status: str
    facilities_profiled: int
    highly_persistent: int
    moderately_active: int
    sporadic: int
    no_historical_anomalies: int

class HistorySummary(BaseModel):
    total_monitored_facilities: int
    tier_breakdown: Dict[str, int]
    max_p95_frp_overall: float
    highest_activity_facility: Optional[Dict[str, Any]]
