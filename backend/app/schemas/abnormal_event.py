from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AbnormalEventResponse(BaseModel):
    id: int
    observation_id: int
    facility_id: int
    observed_frp: float
    baseline_p95_frp: float
    frp_multiplier_ratio: float
    anomaly_severity: str
    scientific_caution_label: str
    explanation_reason: str
    detected_at: datetime

    # Facility & observation details
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class DetectAnomalyRequest(BaseModel):
    recalculate_all: Optional[bool] = Field(False, description="Whether to re-evaluate all observations for abnormal events")

class DetectAnomalyResponse(BaseModel):
    status: str
    total_evaluated: int
    anomalies_detected: int
    moderate_spikes: int
    high_spikes: int
    critical_anomalies: int

class AnomalySummary(BaseModel):
    total_anomalies: int
    severity_breakdown: Dict[str, int]
    max_multiplier_ratio: float
    highest_anomaly: Optional[Dict[str, Any]]
