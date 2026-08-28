import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Index, Text
from app.database import Base, engine
from app.models.thermal_observation import HAS_GEOALCHEMY2, is_sqlite, Geometry

class IndustrialFacility(Base):
    """
    SQLAlchemy model representing an OpenStreetMap (OSM) industrial facility, 
    infrastructure node, or industrial land-use boundary.
    """
    __tablename__ = "industrial_facilities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    osm_id = Column(String(100), unique=True, index=True, nullable=False) # e.g. way/123456, node/7890
    name = Column(String(255), nullable=True, index=True)
    facility_type = Column(String(100), nullable=False, index=True)      # e.g. refinery, power_plant, steel_works, chemical, industrial
    operator = Column(String(255), nullable=True)
    
    # Centroid coordinates
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    # Geometry: Polygon/MultiPolygon or Point
    if HAS_GEOALCHEMY2 and not is_sqlite:
        geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    else:
        geometry = Column(String, nullable=True)

    area_sqm = Column(Float, default=0.0, index=True)                    # Surface area in m²
    raw_tags = Column(Text, nullable=True)                               # Serialized JSON of OSM tags
    ingestion_batch_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_facility_lat_lon", "latitude", "longitude"),
        Index("idx_facility_type_area", "facility_type", "area_sqm"),
    )

    def __repr__(self):
        return f"<IndustrialFacility(id={self.id}, osm_id='{self.osm_id}', name='{self.name}', type='{self.facility_type}', area_sqm={self.area_sqm})>"
