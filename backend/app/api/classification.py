import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.thermal_classification import ThermalClassification
from app.schemas.thermal_classification import (
    ClassificationResponse,
    RunClassificationRequest,
    RunClassificationResponse,
    ClassificationSummary
)
from app.services.classification_service import ClassificationService

router = APIRouter(tags=["Source Classification"])

@router.post("/classification/run", response_model=RunClassificationResponse, summary="Run Candidate Source Classification Engine")
def run_classification_job(
    payload: RunClassificationRequest = RunClassificationRequest(),
    db: Session = Depends(get_db)
):
    """Triggers candidate source classification engine over thermal observations."""
    service = ClassificationService()
    recalc = payload.recalculate_all or False
    response = service.run_classification_pipeline(db=db, recalculate_all=recalc)
    return response

@router.get("/classification", response_model=List[ClassificationResponse], summary="Retrieve Thermal Source Classifications")
def list_classifications(
    predicted_class: Optional[str] = Query(None, description="Filter by class (INDUSTRIAL_CANDIDATE, NATURAL_FOREST_CANDIDATE, AGRICULTURAL_CANDIDATE, OTHER_UNKNOWN)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score threshold"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists thermal anomaly source classification predictions."""
    query = db.query(ThermalClassification)

    if predicted_class:
        query = query.filter(ThermalClassification.predicted_class == predicted_class)
    if min_confidence is not None:
        query = query.filter(ThermalClassification.confidence_score >= min_confidence)

    classifications = query.order_by(ThermalClassification.confidence_score.desc()).offset(offset).limit(limit).all()

    results = []
    for c in classifications:
        features_dict = None
        if c.feature_vector_json:
            try:
                features_dict = json.loads(c.feature_vector_json)
            except Exception:
                pass

        res_dict = {
            "id": c.id,
            "observation_id": c.observation_id,
            "predicted_class": c.predicted_class,
            "confidence_score": c.confidence_score,
            "classification_reason": c.classification_reason,
            "feature_vector": features_dict,
            "created_at": c.created_at
        }
        results.append(ClassificationResponse(**res_dict))

    return results

@router.get("/classification/observation/{obs_id}", response_model=Optional[ClassificationResponse], summary="Get Classification for Single Thermal Anomaly")
def get_observation_classification(obs_id: int, db: Session = Depends(get_db)):
    """Retrieves candidate classification result for a single observation."""
    c = db.query(ThermalClassification).filter(
        ThermalClassification.observation_id == obs_id
    ).first()

    if not c:
        return None

    features_dict = None
    if c.feature_vector_json:
        try:
            features_dict = json.loads(c.feature_vector_json)
        except Exception:
            pass

    res_dict = {
        "id": c.id,
        "observation_id": c.observation_id,
        "predicted_class": c.predicted_class,
        "confidence_score": c.confidence_score,
        "classification_reason": c.classification_reason,
        "feature_vector": features_dict,
        "created_at": c.created_at
    }
    return ClassificationResponse(**res_dict)

@router.get("/analytics/classification-summary", response_model=ClassificationSummary, summary="Get Aggregate Classification Metrics")
def get_classification_summary(db: Session = Depends(get_db)):
    """Computes summary metrics for candidate source classifications."""
    total = db.query(func.count(ThermalClassification.id)).scalar() or 0
    if total == 0:
        return ClassificationSummary(
            total_classifications=0,
            class_breakdown={},
            avg_confidence=0.0
        )

    avg_conf = db.query(func.avg(ThermalClassification.confidence_score)).scalar() or 0.0

    counts = db.query(
        ThermalClassification.predicted_class, func.count(ThermalClassification.id)
    ).group_by(ThermalClassification.predicted_class).all()
    class_breakdown = {str(c): count for c, count in counts if c}

    return ClassificationSummary(
        total_classifications=total,
        class_breakdown=class_breakdown,
        avg_confidence=round(float(avg_conf), 2)
    )
