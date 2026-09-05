import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Index, Text
from app.database import Base
from app.models.thermal_observation import HAS_GEOALCHEMY2, is_sqlite, Geometry

class TransportationEntity(Base):
    """
    SQLAlchemy model representing an OpenStreetMap (OSM) transportation corridor
    (e.g., major roads: motorway, trunk, primary; railways: rail).
    Stores LINESTRING geometries for accurate PostGIS segment distance calculations,
    augmented with Phase 3D display labels, location context, and metadata lineage.
    """
    __tablename__ = "transportation_entities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    osm_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True) # e.g. motorway, trunk, primary, railway
    transport_category = Column(String(50), nullable=False, index=True) # e.g. road, railway

    # Phase 3D Location Enrichment & Display Attributes
    display_label = Column(String(255), nullable=True, index=True)
    location_context = Column(String(255), nullable=True)
    name_source = Column(String(50), nullable=True) # e.g. OSM, OSM_REF, OSM_CLASSIFICATION
    location_source = Column(String(50), nullable=True) # e.g. NOMINATIM_LOOKUP, OSM_TAGS
    enriched_at = Column(DateTime, nullable=True)

    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)

    if HAS_GEOALCHEMY2 and not is_sqlite:
        geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    else:
        geometry = Column(String, nullable=True)

    raw_tags = Column(Text, nullable=True)
    ingestion_batch_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_transport_lat_lon", "latitude", "longitude"),
        Index("idx_transport_type", "entity_type"),
    )

    def __repr__(self):
        return f"<TransportationEntity(id={self.id}, osm_id='{self.osm_id}', label='{self.display_label}', type='{self.entity_type}')>"
