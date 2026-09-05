import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Index, Text
from app.database import Base
from app.models.thermal_observation import HAS_GEOALCHEMY2, is_sqlite, Geometry

class HealthcareFacility(Base):
    """
    SQLAlchemy model representing an OpenStreetMap (OSM) healthcare facility
    (e.g., hospital campus, medical center).
    """
    __tablename__ = "healthcare_facilities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    osm_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True, index=True)
    entity_type = Column(String(100), default="hospital", nullable=False, index=True)
    operator = Column(String(255), nullable=True)

    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)

    if HAS_GEOALCHEMY2 and not is_sqlite:
        geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    else:
        geometry = Column(String, nullable=True)

    area_sqm = Column(Float, default=0.0, index=True)
    raw_tags = Column(Text, nullable=True)
    ingestion_batch_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_healthcare_lat_lon", "latitude", "longitude"),
    )

    def __repr__(self):
        return f"<HealthcareFacility(id={self.id}, osm_id='{self.osm_id}', name='{self.name}', type='{self.entity_type}')>"
