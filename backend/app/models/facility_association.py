import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class ThermalFacilityAssociation(Base):
    """
    SQLAlchemy model representing a spatial association between a NASA FIRMS thermal anomaly 
    and an OpenStreetMap industrial facility.
    """
    __tablename__ = "thermal_facility_associations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    observation_id = Column(Integer, ForeignKey("thermal_observations.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("industrial_facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    distance_meters = Column(Float, nullable=False, index=True)
    association_type = Column(String(50), nullable=False, index=True) # DIRECT_MATCH, PROXIMATE_MATCH, VICINITY_MATCH, UNASSOCIATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    observation = relationship("ThermalObservation", backref="facility_associations")
    facility = relationship("IndustrialFacility", backref="thermal_associations")

    __table_args__ = (
        Index("idx_assoc_obs_fac", "observation_id", "facility_id", unique=True),
        Index("idx_assoc_type_dist", "association_type", "distance_meters"),
    )

    def __repr__(self):
        return f"<ThermalFacilityAssociation(obs_id={self.observation_id}, fac_id={self.facility_id}, dist={self.distance_meters}m, type='{self.association_type}')>"
