import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Index
from app.database import Base

class GroundTruthLabel(Base):
    """
    SQLAlchemy model representing ground-truth evidence and label provenance
    associated with a NASA FIRMS thermal observation.
    
    Preserves explicit source lineage, matching metrics, confidence level, and training eligibility.
    """
    __tablename__ = "ground_truth_labels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    observation_id = Column(Integer, ForeignKey("thermal_observations.id"), nullable=False, index=True)
    
    label = Column(String, nullable=False, index=True) # INDUSTRIAL_FIRE, GAS_FLARE, AGRICULTURAL_BURNING, MINING_ACTIVITY, WILDFIRE, UNKNOWN
    label_confidence = Column(String, nullable=False, default="UNKNOWN") # HIGH, MEDIUM, LOW, UNKNOWN
    label_source = Column(String, nullable=False) # e.g. NOAA_VIIRS_NIGHTFIRE, MODIS_MCD64A1, OFFICIAL_INCIDENT_REGISTRY
    label_source_id = Column(String, nullable=True)
    label_method = Column(String, nullable=False, default="EXTERNAL_GROUND_TRUTH_MATCH")
    
    matched_distance_m = Column(Float, nullable=True)
    matched_time_delta_hours = Column(Float, nullable=True)
    training_eligible = Column(Boolean, nullable=False, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_gt_obs_label", "observation_id", "label"),
    )
