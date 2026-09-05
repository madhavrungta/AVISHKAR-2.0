from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ImpactEntity(BaseModel):
    """
    Represents a single nearby entity (industrial facility, power plant, substation, 
    healthcare facility, or transportation corridor) identified within the configured 
    impact assessment radius, augmented with Phase 3D display labels and location context.
    """
    entity_category: str = Field(default="INDUSTRIAL", description="High-level category: INDUSTRIAL, ENERGY, HEALTHCARE, TRANSPORTATION")
    entity_type: str = Field(default="industrial_facility", description="Specific entity type: refinery, power_plant, substation, hospital, motorway, trunk, primary, railway")
    facility_id: int = Field(description="Unique primary key ID of the entity")
    entity_id: Optional[int] = Field(default=None, description="Unique primary key ID of the entity")
    osm_id: Optional[str] = Field(default=None, description="OSM feature ID: e.g. node/123, way/456")
    name: Optional[str] = Field(default=None, description="Official name of the entity/facility from OSM source")
    
    # Phase 3D Display Label, Location Context, and Lineage Metadata
    display_label: Optional[str] = Field(default=None, description="Human-readable data-driven display label")
    location_context: Optional[str] = Field(default=None, description="Administrative location context (e.g. Mangalore, Karnataka)")
    name_source: Optional[str] = Field(default=None, description="Lineage source for display label: OSM, OSM_REF, OSM_CLASSIFICATION")
    location_source: Optional[str] = Field(default=None, description="Lineage source for location context: NOMINATIM_LOOKUP, OSM_TAGS")
    enriched_at: Optional[datetime] = Field(default=None, description="Timestamp when location context was enriched")

    facility_type: Optional[str] = Field(default=None, description="Industrial sector / infrastructure classification")
    geometry_type: str = Field(default="POINT", description="Geometry type: POINT, LINESTRING, POLYGON, MULTIPOLYGON")
    distance_meters: float = Field(description="Physical distance from thermal event to entity in meters")
    distance_km: float = Field(description="Physical distance from thermal event to entity in kilometers")
    sensitivity_tier: Optional[str] = Field(default="MODERATE", description="Entity intrinsic sensitivity tier: CRITICAL, HIGH, MODERATE, or None")
    footprint_scale: Optional[str] = Field(default="STANDARD_FACILITY", description="Physical footprint scale class: MEGA_FACILITY, LARGE_FACILITY, STANDARD_FACILITY, or None")
    latitude: float = Field(description="Entity centroid latitude")
    longitude: float = Field(description="Entity centroid longitude")

class ImpactAssessmentResponse(BaseModel):
    """
    Response schema for GET /impact/{event_id} assessment queries.
    """
    event_id: int = Field(description="Thermal observation event ID")
    event_latitude: float = Field(description="Thermal observation latitude")
    event_longitude: float = Field(description="Thermal observation longitude")
    assessment_radius_km: float = Field(description="Configured assessment search radius in kilometers")
    total_entities_found: int = Field(description="Total count of nearby entities within assessment radius")
    entities: List[ImpactEntity] = Field(default_factory=list, description="List of nearby exposed entities ordered by distance ascending")
    scientific_disclaimer: str = Field(
        default=(
            "Potentially exposed entities are identified from spatial proximity within the configured assessment radius. "
            "Spatial proximity indicates potential exposure context and does not establish fire causality, confirmed damage, or actual fire impact."
        ),
        description="Scientific disclaimer clarifying potential exposure context vs fire causality"
    )
