import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class FacilityHistoricalBehavior(Base):
    """
    SQLAlchemy model representing the historical thermal behavior, 
    FRP percentile distribution, and observation frequency of an industrial facility.
    """
    __tablename__ = "facility_historical_behaviors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    facility_id = Column(Integer, ForeignKey("industrial_facilities.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    total_observations = Column(Integer, default=0, nullable=False, index=True)
    observation_days = Column(Integer, default=0, nullable=False)
    
    min_frp = Column(Float, default=0.0, nullable=False)
    max_frp = Column(Float, default=0.0, nullable=False, index=True)
    mean_frp = Column(Float, default=0.0, nullable=False)
    median_frp = Column(Float, default=0.0, nullable=False)
    p95_frp = Column(Float, default=0.0, nullable=False, index=True)      # 95th Percentile FRP (MW)
    p99_frp = Column(Float, default=0.0, nullable=False)                  # 99th Percentile FRP (MW)
    
    day_count = Column(Integer, default=0, nullable=False)
    night_count = Column(Integer, default=0, nullable=False)
    day_night_ratio = Column(Float, default=0.0, nullable=False)
    
    activity_tier = Column(String(50), default="NO_HISTORICAL_ANOMALIES", nullable=False, index=True) # HIGHLY_PERSISTENT, MODERATELY_ACTIVE, SPORADIC, NO_HISTORICAL_ANOMALIES
    
    first_observed = Column(DateTime, nullable=True)
    last_observed = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationship
    facility = relationship("IndustrialFacility", backref="historical_behavior", uselist=False)

    __table_args__ = (
        Index("idx_history_tier_p95", "activity_tier", "p95_frp"),
    )

    def __repr__(self):
        return f"<FacilityHistoricalBehavior(fac_id={self.facility_id}, obs={self.total_observations}, P95_FRP={self.p95_frp}MW, tier='{self.activity_tier}')>"
