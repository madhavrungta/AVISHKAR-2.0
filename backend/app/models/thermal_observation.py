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


class ThermalObservation(Base):
    """
    SQLAlchemy model representing a NASA FIRMS thermal anomaly / active-fire observation.
    
    Preserves all original NASA FIRMS fields while injecting system metadata:
    - observation_timestamp
    - ingestion_timestamp
    - source
    - ingestion_batch_id
    - geometry (EPSG:4326 WGS84 Point)
    """
    __tablename__ = "thermal_observations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Coordinates & Spatial Geometry
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    # Use PostGIS Geometry when PostgreSQL/GeoAlchemy2 is configured; fallback to String WKT on SQLite
    if HAS_GEOALCHEMY2 and not is_sqlite:
        geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    else:
        geometry = Column(String, nullable=True)

    # NASA FIRMS Thermal Measurements
    bright_ti4 = Column(Float, nullable=True)
    bright_ti5 = Column(Float, nullable=True)
    scan = Column(Float, nullable=True)
    track = Column(Float, nullable=True)
    acq_date = Column(String(10), nullable=True, index=True)  # YYYY-MM-DD
    acq_time = Column(String(4), nullable=True)               # HHMM
    satellite = Column(String(20), nullable=True, index=True) # e.g. N (NPP), N20 (NOAA-20), N21 (NOAA-21)
    instrument = Column(String(20), nullable=True)            # e.g. VIIRS
    confidence = Column(String(10), nullable=True)            # e.g. n, l, h or numeric %
    version = Column(String(20), nullable=True)
    frp = Column(Float, nullable=True, index=True)            # Fire Radiative Power (MW)
    daynight = Column(String(1), nullable=True)               # D / N

    # System Ingestion Metadata
    observation_timestamp = Column(DateTime, nullable=False, index=True)
    observation_time = Column(DateTime, nullable=True, index=True)
    ingestion_timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    source = Column(String(50), nullable=False, index=True)    # e.g. VIIRS_SNPP_NRT
    ingestion_batch_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_thermal_lat_lon", "latitude", "longitude"),
        Index("idx_thermal_source_date", "source", "acq_date"),
    )

    def __repr__(self):
        return f"<ThermalObservation(id={self.id}, lat={self.latitude}, lon={self.longitude}, FRP={self.frp}, sat={self.satellite}, timestamp={self.observation_timestamp})>"
