from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ClassificationResponse(BaseModel):
    id: int
    observation_id: int
    predicted_class: str
    confidence_score: float
    classification_reason: str
    feature_vector: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RunClassificationRequest(BaseModel):
    recalculate_all: Optional[bool] = Field(False, description="Whether to reclassify existing observations")

class RunClassificationResponse(BaseModel):
    status: str
    total_processed: int
    classifications_created: int
    industrial_candidates: int
    natural_forest_candidates: int
    agricultural_candidates: int
    other_unknown: int

class ClassificationSummary(BaseModel):
    total_classifications: int
    class_breakdown: Dict[str, int]
    avg_confidence: float
