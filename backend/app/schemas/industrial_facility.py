from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IndustrialFacilityBase(BaseModel):
    osm_id: str = Field(..., description="Unique OpenStreetMap element ID (e.g. way/12345)")
    name: Optional[str] = Field(None, description="Facility name")
    facility_type: str = Field(..., description="Categorized industrial type (refinery, power_plant, steel_works, chemical, industrial)")
    operator: Optional[str] = Field(None, description="Facility operator/owner name")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Centroid latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Centroid longitude")
    area_sqm: float = Field(0.0, ge=0.0, description="Calculated surface area in square meters")
    raw_tags: Optional[Dict[str, Any]] = Field(None, description="Key-value dictionary of raw OSM tags")

class IndustrialFacilityCreate(IndustrialFacilityBase):
    ingestion_batch_id: str

class IndustrialFacilityResponse(IndustrialFacilityBase):
    id: int
    ingestion_batch_id: str
    created_at: datetime
    geometry_wkt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class OSMIngestionRequest(BaseModel):
    area: Optional[str] = Field(None, description="Bounding box 'west,south,east,north'")
    facility_type: Optional[str] = Field(None, description="Optional filter by facility type")

class OSMIngestionResponse(BaseModel):
    status: str
    batch_id: str
    facilities_ingested: int
    raw_file_path: Optional[str] = None
    types_summary: Dict[str, int]

class FacilityAnalyticsSummary(BaseModel):
    total_facilities: int
    total_area_sqkm: float
    type_breakdown: Dict[str, int]
    largest_facility: Optional[Dict[str, Any]]
