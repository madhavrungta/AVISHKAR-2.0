import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class HumanReviewCase(Base):
    __tablename__ = "human_review_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(32), unique=True, index=True, nullable=False)  # e.g., "REV-001"
    event_id = Column(Integer, ForeignKey("thermal_observations.id"), nullable=True, index=True)
    set_type = Column(String(64), nullable=False, default="PRIORITY_SET")  # PRIORITY_SET, DIVERSITY_CONTROL_SET
    sampling_rationale = Column(String(256), nullable=True)
    
    # Snapshot of context for reproducible audit
    evidence_data = Column(JSON, nullable=False, default=dict)
    
    # Workflow status: PENDING_REVIEW, ASSIGNED, IN_REVIEW, REVIEW_SUBMITTED, NEEDS_ADJUDICATION, ADJUDICATED, INSUFFICIENT_EVIDENCE
    status = Column(String(64), nullable=False, default="PENDING_REVIEW", index=True)
    
    # Final Adjudicated outcome (if adjudicated)
    final_adjudicated_class = Column(String(64), nullable=True)  # INDUSTRIAL_FIRE, GAS_FLARE, AGRICULTURAL_BURNING, MINING_ACTIVITY, WILDFIRE, UNKNOWN_OTHER
    final_adjudicated_status = Column(String(64), nullable=True)  # VERIFIED, REJECTED, UNCERTAIN, INSUFFICIENT_EVIDENCE
    
    model_version_at_creation = Column(String(64), nullable=False, default="4F.13_GB_V1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    decisions = relationship("HumanReviewDecision", back_populates="review_case", cascade="all, delete-orphan")
    adjudications = relationship("HumanAdjudicationRecord", back_populates="review_case", cascade="all, delete-orphan")

    def to_dict(self, include_ml: bool = True):
        data = {
            "id": self.id,
            "case_id": self.case_id,
            "event_id": self.event_id,
            "set_type": self.set_type,
            "sampling_rationale": self.sampling_rationale,
            "status": self.status,
            "final_adjudicated_class": self.final_adjudicated_class,
            "final_adjudicated_status": self.final_adjudicated_status,
            "model_version_at_creation": self.model_version_at_creation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "evidence": dict(self.evidence_data) if self.evidence_data else {}
        }
        if not include_ml and "ml_evidence" in data["evidence"]:
            data["evidence"]["ml_evidence"] = {
                "status": "BLINDED_DURING_REVIEW",
                "notice": "ML Shadow prediction is hidden to prevent reviewer cognitive bias."
            }
        return data


class HumanReviewDecision(Base):
    __tablename__ = "human_review_decisions"

    id = Column(Integer, primary_key=True, index=True)
    review_case_id = Column(Integer, ForeignKey("human_review_cases.id"), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=False, index=True)  # REVIEWER_A, REVIEWER_B, etc.
    reviewer_role = Column(String(64), nullable=False, default="DOMAIN_EXPERT")
    review_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Reviewer decision: VERIFIED, REJECTED, UNCERTAIN, INSUFFICIENT_EVIDENCE
    review_status = Column(String(64), nullable=False)
    
    # Selected class: INDUSTRIAL_FIRE, GAS_FLARE, AGRICULTURAL_BURNING, MINING_ACTIVITY, WILDFIRE, UNKNOWN_OTHER
    observed_class = Column(String(64), nullable=True)
    
    # Evidence Strength: STRONG, MODERATE, WEAK, INSUFFICIENT
    evidence_strength = Column(String(32), nullable=False, default="MODERATE")
    
    # Confidence Level: HIGH, MEDIUM, LOW
    confidence_level = Column(String(32), nullable=False, default="MEDIUM")
    
    # Sources used (e.g. ["FIRMS_THERMAL", "OSM_INDUSTRIAL_BOUNDARY", "LANDCOVER_MAP"])
    evidence_sources = Column(JSON, nullable=False, default=list)
    
    reviewer_comment = Column(Text, nullable=True)
    reviewer_flags = Column(JSON, nullable=False, default=list)
    
    is_blinded = Column(Boolean, default=True)
    model_version_at_review = Column(String(64), nullable=False, default="4F.13_GB_V1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review_case = relationship("HumanReviewCase", back_populates="decisions")

    def to_dict(self):
        return {
            "id": self.id,
            "review_case_id": self.review_case_id,
            "reviewer_id": self.reviewer_id,
            "reviewer_role": self.reviewer_role,
            "review_timestamp": self.review_timestamp.isoformat() if self.review_timestamp else None,
            "review_status": self.review_status,
            "observed_class": self.observed_class,
            "evidence_strength": self.evidence_strength,
            "confidence_level": self.confidence_level,
            "evidence_sources": self.evidence_sources,
            "reviewer_comment": self.reviewer_comment,
            "reviewer_flags": self.reviewer_flags,
            "is_blinded": self.is_blinded,
            "model_version_at_review": self.model_version_at_review
        }


class HumanAdjudicationRecord(Base):
    __tablename__ = "human_adjudications"

    id = Column(Integer, primary_key=True, index=True)
    review_case_id = Column(Integer, ForeignKey("human_review_cases.id"), nullable=False, index=True)
    adjudicator_id = Column(String(64), nullable=False, index=True)
    adjudication_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    adjudication_reason = Column(Text, nullable=False)
    evidence_used = Column(JSON, nullable=False, default=list)
    
    # Final Decision: VERIFIED, REJECTED, UNCERTAIN, INSUFFICIENT_EVIDENCE
    final_decision = Column(String(64), nullable=False)
    final_class = Column(String(64), nullable=True)
    
    model_version_at_adjudication = Column(String(64), nullable=False, default="4F.13_GB_V1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review_case = relationship("HumanReviewCase", back_populates="adjudications")

    def to_dict(self):
        return {
            "id": self.id,
            "review_case_id": self.review_case_id,
            "adjudicator_id": self.adjudicator_id,
            "adjudication_timestamp": self.adjudication_timestamp.isoformat() if self.adjudication_timestamp else None,
            "adjudication_reason": self.adjudication_reason,
            "evidence_used": self.evidence_used,
            "final_decision": self.final_decision,
            "final_class": self.final_class,
            "model_version_at_adjudication": self.model_version_at_adjudication
        }
