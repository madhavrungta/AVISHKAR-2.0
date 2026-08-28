from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RiskScoreResponse(BaseModel):
    id: int
    observation_id: int
    facility_id: Optional[int] = None
    composite_risk_score: float
    risk_level: str
    spatial_proximity_score: float
    frp_multiplier_score: float
    facility_sensitivity_score: float
    optical_verification_confidence: float
    verification_source: str
    risk_breakdown_json: Optional[Dict[str, Any]] = None
    evaluated_at: datetime

    # Facility & observation details
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class EvaluateRiskRequest(BaseModel):
    recalculate_all: Optional[bool] = Field(False, description="Whether to re-evaluate risk scores for all observations")

class EvaluateRiskResponse(BaseModel):
    status: str
    total_evaluated: int
    critical_verified: int
    high_risk: int
    medium_risk: int
    low_risk: int

class RiskSummary(BaseModel):
    total_evaluations: int
    tier_breakdown: Dict[str, int]
    avg_composite_score: float
    highest_risk_observation: Optional[Dict[str, Any]]
