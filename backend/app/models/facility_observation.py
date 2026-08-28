import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class FacilityObservation(Base):
    """
    SQLAlchemy model representing spatial associations between thermal observations and facilities.
    """
    __tablename__ = "facility_observations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id = Column(Integer, ForeignKey("thermal_observations.id", ondelete="CASCADE"), nullable=False, index=True)
    distance_m = Column(Float, nullable=False, index=True)
    association_method = Column(String(50), nullable=False, index=True) # e.g. "Direct Point Match", "Proximity Query"
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    facility = relationship("Facility", backref="facility_observations")
    observation = relationship("ThermalObservation", backref="associated_facilities")

    __table_args__ = (
        Index("idx_fac_obs_uniq", "facility_id", "observation_id", unique=True),
    )

    def __repr__(self):
        return f"<FacilityObservation(id={self.id}, facility={self.facility_id}, observation={self.observation_id}, dist={self.distance_m}m)>"
