import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.human_review import HumanReviewCase, HumanReviewDecision, HumanAdjudicationRecord
from app.ml.phase4f21_human_verification import HumanExpertVerificationManager

logger = logging.getLogger("firms_app.api.human_review")

router = APIRouter(prefix="/ml/human-review", tags=["Human Expert Verification & Adjudication (Phase 4F-21)"])


class ReviewSubmissionSchema(BaseModel):
    reviewer_id: str
    review_status: str  # VERIFIED, REJECTED, UNCERTAIN, INSUFFICIENT_EVIDENCE
    observed_class: Optional[str] = None
    evidence_strength: str = "MODERATE"
    confidence_level: str = "MEDIUM"
    evidence_sources: List[str] = []
    reviewer_comment: Optional[str] = None
    reviewer_flags: List[str] = []
    reviewer_role: str = "DOMAIN_EXPERT"
    is_blinded: bool = True


class AdjudicationSubmissionSchema(BaseModel):
    adjudicator_id: str
    final_decision: str  # VERIFIED, REJECTED, UNCERTAIN, INSUFFICIENT_EVIDENCE
    final_class: Optional[str] = None
    adjudication_reason: str
    evidence_used: List[str] = []


@router.get("/cases", summary="List Human Review Cases")
def list_review_cases(
    status: Optional[str] = Query(None, description="Filter by status (e.g. PENDING_REVIEW, ADJUDICATED, NEEDS_ADJUDICATION)"),
    set_type: Optional[str] = Query(None, description="Filter by set type (PRIORITY_SET, DIVERSITY_CONTROL_SET)"),
    blinded: bool = Query(True, description="Whether to mask ML shadow prediction to prevent cognitive bias"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lists human review cases with optional filtering and blinding control."""
    manager = HumanExpertVerificationManager(db)
    manager.initialize_from_phase4f17_packet()
    
    query = db.query(HumanReviewCase)
    if status:
        query = query.filter(HumanReviewCase.status == status)
    if set_type:
        query = query.filter(HumanReviewCase.set_type == set_type)
        
    total = query.count()
    cases = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "count": len(cases),
        "blinded": blinded,
        "cases": [c.to_dict(include_ml=not blinded) for c in cases]
    }


@router.get("/cases/{case_id}", summary="Get Specific Review Case Details")
def get_review_case(
    case_id: str,
    blinded: bool = Query(True, description="Whether to mask ML shadow prediction"),
    db: Session = Depends(get_db)
):
    """Returns complete structured evidence for a single review case."""
    manager = HumanExpertVerificationManager(db)
    manager.initialize_from_phase4f17_packet()
    
    case_obj = db.query(HumanReviewCase).filter(HumanReviewCase.case_id == case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail=f"Review case {case_id} not found.")
        
    return case_obj.to_dict(include_ml=not blinded)


@router.post("/cases/{case_id}/review", summary="Submit Independent Reviewer Decision")
def submit_review(
    case_id: str,
    payload: ReviewSubmissionSchema,
    db: Session = Depends(get_db)
):
    """Submits an independent human review decision."""
    manager = HumanExpertVerificationManager(db)
    manager.initialize_from_phase4f17_packet()
    
    try:
        res = manager.submit_reviewer_decision(
            case_id=case_id,
            reviewer_id=payload.reviewer_id,
            review_status=payload.review_status,
            observed_class=payload.observed_class,
            evidence_strength=payload.evidence_strength,
            confidence_level=payload.confidence_level,
            evidence_sources=payload.evidence_sources,
            reviewer_comment=payload.reviewer_comment,
            reviewer_flags=payload.reviewer_flags,
            reviewer_role=payload.reviewer_role,
            is_blinded=payload.is_blinded
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cases/{case_id}/reviews", summary="Get All Review Decisions for Case")
def get_case_reviews(
    case_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves all independent reviewer decisions submitted for a specific case."""
    case_obj = db.query(HumanReviewCase).filter(HumanReviewCase.case_id == case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail=f"Review case {case_id} not found.")
        
    decisions = db.query(HumanReviewDecision).filter(
        HumanReviewDecision.review_case_id == case_obj.id
    ).all()
    
    adjudications = db.query(HumanAdjudicationRecord).filter(
        HumanAdjudicationRecord.review_case_id == case_obj.id
    ).all()
    
    return {
        "case_id": case_id,
        "status": case_obj.status,
        "decisions": [d.to_dict() for d in decisions],
        "adjudications": [a.to_dict() for a in adjudications]
    }


@router.post("/cases/{case_id}/adjudicate", summary="Adjudicate Review Case")
def adjudicate_case_endpoint(
    case_id: str,
    payload: AdjudicationSubmissionSchema,
    db: Session = Depends(get_db)
):
    """Adjudicates a review case resolving disagreements or finalizing classification."""
    manager = HumanExpertVerificationManager(db)
    manager.initialize_from_phase4f17_packet()
    
    try:
        res = manager.adjudicate_case(
            case_id=case_id,
            adjudicator_id=payload.adjudicator_id,
            final_decision=payload.final_decision,
            final_class=payload.final_class,
            adjudication_reason=payload.adjudication_reason,
            evidence_used=payload.evidence_used
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adjudicating case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", summary="Get Human Verification & Adjudication Summary")
def get_verification_summary(
    db: Session = Depends(get_db)
):
    """Returns aggregated human verification progress, inter-rater agreement, and ML comparison metrics."""
    manager = HumanExpertVerificationManager(db)
    manager.initialize_from_phase4f17_packet()
    
    cases = db.query(HumanReviewCase).all()
    status_counts = {}
    for c in cases:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1
        
    inter_rater = manager.evaluate_inter_rater_agreement()
    ml_vs_human = manager.evaluate_ml_vs_human_metrics()
    
    return {
        "total_cases": len(cases),
        "status_distribution": status_counts,
        "inter_rater_agreement": inter_rater,
        "ml_vs_human_metrics": ml_vs_human,
        "risk_engine_invariance": "100% INVARIANT",
        "ml_shadow_only": True
    }
