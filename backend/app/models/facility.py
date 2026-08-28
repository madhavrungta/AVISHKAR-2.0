import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from app.database import Base, engine

try:
    from geoalchemy2 import Geometry
    HAS_GEOALCHEMY2 = True
except ImportError:
    Geometry = None
    HAS_GEOALCHEMY2 = False

is_sqlite = engine.url.drivername.startswith("sqlite")

class Facility(Base):
    """
    SQLAlchemy model representing an OpenStreetMap industrial facility / plant.
    """
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    osm_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    facility_type = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    if HAS_GEOALCHEMY2 and not is_sqlite:
        geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    else:
        geometry = Column(String, nullable=True)
        
    source = Column(String(100), default="OSM Overpass API", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Facility(id={self.id}, name='{self.name}', type='{self.facility_type}', lat={self.latitude}, lon={self.longitude})>"
