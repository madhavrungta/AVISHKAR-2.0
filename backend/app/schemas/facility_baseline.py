from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class FacilityBaselineResponse(BaseModel):
    id: int
    facility_id: int
    baseline_frp_p50: float
    baseline_frp_p95: float
    baseline_frp_p99: float
    monthly_frequency: float
    day_night_preference: str
    baseline_status: str
    updated_at: datetime

    # Facility details
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GenerateBaselineRequest(BaseModel):
    recalculate_all: Optional[bool] = Field(False, description="Whether to recompute baselines for all facilities")

class GenerateBaselineResponse(BaseModel):
    status: str
    baselines_generated: int
    established_baselines: int
    preliminary_defaults: int

class BaselineSummary(BaseModel):
    total_baselines: int
    established_count: int
    preliminary_count: int
    avg_p95_frp_overall: float
