import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.database import get_db
from app.models.thermal_observation import ThermalObservation
from app.models.ground_truth import GroundTruthLabel
from app.services.ground_truth.matcher import GroundTruthMatcher

router = APIRouter(tags=["Ground-Truth Acquisition & Provenance"])
matcher = GroundTruthMatcher()

@router.get("/ground-truth/{event_id}")
def get_ground_truth_label(
    event_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieves independent ground-truth evidence, label provenance, and training eligibility
    for a given thermal observation event.
    """
    try:
        return matcher.evaluate_observation_label(db=db, event_id=event_id, save_to_db=False)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ground-truth service error: {str(e)}")

@router.get("/ground-truth/batch/audit")
def audit_ground_truth_batch(
    limit: int = Query(default=100, ge=1, le=500, description="Max observations to audit"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Audits ground-truth label status and class distribution across active thermal observations.
    """
    observations = db.query(ThermalObservation).limit(limit).all()
    total = len(observations)

    class_counts = {
        "INDUSTRIAL_FIRE": 0,
        "GAS_FLARE": 0,
        "AGRICULTURAL_BURNING": 0,
        "MINING_ACTIVITY": 0,
        "WILDFIRE": 0,
        "UNKNOWN": 0
    }

    confidence_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "UNKNOWN": 0
    }

    training_eligible_count = 0
    conflicting_count = 0

    for obs in observations:
        eval_res = matcher.evaluate_observation_label(db=db, event_id=obs.id, save_to_db=False)
        lbl = eval_res.get("label", "UNKNOWN")
        conf = eval_res.get("label_confidence", "UNKNOWN")

        if lbl in class_counts:
            class_counts[lbl] += 1
        else:
            class_counts["UNKNOWN"] += 1

        if conf in confidence_counts:
            confidence_counts[conf] += 1

        if eval_res.get("training_eligible"):
            training_eligible_count += 1

        if eval_res.get("label_source") == "CONFLICTING_SOURCES":
            conflicting_count += 1

    return {
        "total_audited_observations": total,
        "class_distribution": class_counts,
        "confidence_distribution": confidence_counts,
        "training_eligible_count": training_eligible_count,
        "conflicting_evidence_count": conflicting_count,
        "audited_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
