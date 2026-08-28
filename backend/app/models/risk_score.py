import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class VerificationRiskScore(Base):
    """
    SQLAlchemy model representing the 4-factor Multi-Criteria Risk Score (0-100) 
    and Sentinel-2 / Landsat-8 optical verification confidence metrics for a thermal observation.
    """
    __tablename__ = "verification_risk_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    observation_id = Column(Integer, ForeignKey("thermal_observations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    facility_id = Column(Integer, ForeignKey("industrial_facilities.id", ondelete="CASCADE"), nullable=True, index=True)
    
    composite_risk_score = Column(Float, nullable=False, index=True) # 0.0 - 100.0
    risk_level = Column(String(50), nullable=False, index=True)      # LOW_RISK, MEDIUM_RISK, HIGH_RISK, CRITICAL_VERIFIED_RISK
    
    spatial_proximity_score = Column(Float, default=10.0, nullable=False)
    frp_multiplier_score = Column(Float, default=30.0, nullable=False)
    facility_sensitivity_score = Column(Float, default=20.0, nullable=False)
    optical_verification_confidence = Column(Float, default=0.50, nullable=False) # 0.0 - 1.0 confidence proxy
    
    verification_source = Column(String(100), default="Sentinel-2 MSI / Landsat-8 OLI Optical Proxy", nullable=False)
    risk_breakdown_json = Column(Text, nullable=True)
    
    evaluated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    observation = relationship("ThermalObservation", backref="risk_score", uselist=False)
    facility = relationship("IndustrialFacility", backref="risk_scores")

    __table_args__ = (
        Index("idx_risk_level_score", "risk_level", "composite_risk_score"),
    )

    def __repr__(self):
        return f"<VerificationRiskScore(obs={self.observation_id}, score={self.composite_risk_score}, level='{self.risk_level}')>"
