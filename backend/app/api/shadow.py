import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.shadow_prediction import MLShadowPrediction
from app.ml.shadow_inference_service import MLShadowInferenceService, MODEL_VERSION

logger = logging.getLogger("firms_app.api.shadow")

router = APIRouter(prefix="/ml/shadow", tags=["ML Shadow Pilot (Phase 4F-11B)"])
shadow_service = MLShadowInferenceService()


@router.get("/audit", summary="Get ML Shadow Pilot Aggregate Audit & Performance Metrics")
def get_shadow_audit_summary(
    limit: Optional[int] = Query(None, description="Optional limit for batch evaluation sample size"),
    force_run: bool = Query(True, description="Force shadow evaluation even if global flag is off"),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated shadow inference statistics, class distribution, confidence bins,
    ML vs Risk semantic disagreement metrics, and latency performance benchmarks.
    """
    try:
        report = shadow_service.evaluate_shadow_batch(db, limit=limit, force_run=force_run)
        return report
    except Exception as e:
        logger.error(f"Failed to generate shadow audit summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate shadow audit report: {str(e)}")


@router.get("/{event_id}", summary="Get or Run ML Shadow Prediction for Observation")
def get_shadow_prediction_for_event(
    event_id: int,
    force_run: bool = Query(True, description="Force shadow inference on-demand"),
    db: Session = Depends(get_db)
):
    """
    Read-only inspection endpoint returning the ML shadow prediction for a specific thermal observation.
    Maintains zero authority over final risk score or existing Risk Engine decisions.
    """
    # Check existing persisted prediction
    pred = db.query(MLShadowPrediction).filter(
        MLShadowPrediction.event_id == event_id,
        MLShadowPrediction.model_version == MODEL_VERSION
    ).first()

    if pred and not force_run:
        return pred.to_dict()

    # Run / update shadow inference
    res = shadow_service.infer_observation(db, event_id, force_run=force_run)
    if res.get("prediction_status") == "FAILED":
        raise HTTPException(status_code=404, detail=res.get("error", "Shadow inference failed."))

    return res
