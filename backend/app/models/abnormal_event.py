import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class AbnormalThermalEvent(Base):
    """
    SQLAlchemy model representing an abnormal thermal spike event detected at an industrial facility 
    where observed FRP exceeds historical P95 baseline threshold.
    """
    __tablename__ = "abnormal_thermal_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    observation_id = Column(Integer, ForeignKey("thermal_observations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    facility_id = Column(Integer, ForeignKey("industrial_facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    observed_frp = Column(Float, nullable=False)
    baseline_p95_frp = Column(Float, nullable=False)
    frp_multiplier_ratio = Column(Float, nullable=False, index=True) # FRP / P95 ratio
    
    anomaly_severity = Column(String(50), nullable=False, index=True) # MODERATE_ABNORMAL_SPIKE, HIGH_ABNORMAL_SPIKE, CRITICAL_INDUSTRIAL_ANOMALY
    scientific_caution_label = Column(String(255), default="Abnormal Thermal Output Candidate - Requires Multi-Pass / High-Res Optical Verification", nullable=False)
    explanation_reason = Column(Text, nullable=False)
    
    detected_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    observation = relationship("ThermalObservation", backref="abnormal_event", uselist=False)
    facility = relationship("IndustrialFacility", backref="abnormal_events")

    __table_args__ = (
        Index("idx_anomaly_sev_ratio", "anomaly_severity", "frp_multiplier_ratio"),
    )

    def __repr__(self):
        return f"<AbnormalThermalEvent(obs={self.observation_id}, fac={self.facility_id}, multiplier={self.frp_multiplier_ratio}x, severity='{self.anomaly_severity}')>"
