import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base

class FacilityBaseline(Base):
    """
    SQLAlchemy model representing computed historical statistical baseline metrics for a facility.
    """
    __tablename__ = "facility_baselines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    baseline_start = Column(DateTime, nullable=False)
    baseline_end = Column(DateTime, nullable=False)
    observation_count = Column(Integer, nullable=False, default=0)
    
    # Statistical measures
    median_frp = Column(Float, nullable=True)
    p95_frp = Column(Float, nullable=True)
    p99_frp = Column(Float, nullable=True)
    mad_frp = Column(Float, nullable=True)
    
    median_brightness_ti4 = Column(Float, nullable=True)
    median_brightness_ti5 = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationship
    facility = relationship("Facility", backref="baseline", uselist=False)

    def __repr__(self):
        return f"<FacilityBaseline(facility={self.facility_id}, count={self.observation_count}, p95_frp={self.p95_frp})>"


class FacilityNormalBaseline(Base):
    """
    SQLAlchemy model representing computed normal historical operational parameters for an industrial facility.
    """
    __tablename__ = "facility_normal_baselines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    facility_id = Column(Integer, ForeignKey("industrial_facilities.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # FRP Baselines
    baseline_frp_p50 = Column(Float, nullable=False) # Median FRP
    baseline_frp_p95 = Column(Float, nullable=False) # 95th Percentile FRP
    baseline_frp_p99 = Column(Float, nullable=False) # 99th Percentile FRP
    
    # Frequency Baselines
    monthly_frequency = Column(Float, nullable=True) # Average detections per month
    day_night_preference = Column(String(10), nullable=True) # 'DAY', 'NIGHT', or 'MIXED'
    
    # Metadata
    baseline_status = Column(String(50), nullable=False) # 'ACTIVE', 'INSUFFICIENT_DATA', 'STALE'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    facility = relationship("IndustrialFacility", backref="normal_baseline", uselist=False)

    def __repr__(self):
        return f"<FacilityNormalBaseline(facility_id={self.facility_id}, p50={self.baseline_frp_p50}MW, p95={self.baseline_frp_p95}MW, status='{self.baseline_status}')>"
