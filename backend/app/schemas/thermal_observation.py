from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ThermalObservationBase(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in EPSG:4326")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in EPSG:4326")
    bright_ti4: Optional[float] = Field(None, description="VIIRS I-4 brightness temperature (Kelvin)")
    bright_ti5: Optional[float] = Field(None, description="VIIRS I-5 brightness temperature (Kelvin)")
    scan: Optional[float] = Field(None, description="Pixel scan size (km)")
    track: Optional[float] = Field(None, description="Pixel track size (km)")
    acq_date: Optional[str] = Field(None, description="Acquisition date YYYY-MM-DD")
    acq_time: Optional[str] = Field(None, description="Acquisition time HHMM UTC")
    satellite: Optional[str] = Field(None, description="Satellite identifier")
    instrument: Optional[str] = Field(None, description="Instrument name")
    confidence: Optional[str] = Field(None, description="Detection confidence value or level")
    version: Optional[str] = Field(None, description="FIRMS processing algorithm version")
    frp: Optional[float] = Field(None, ge=0.0, description="Fire Radiative Power (MW)")
    daynight: Optional[str] = Field(None, description="Day (D) or Night (N) detection")

class ThermalObservationCreate(ThermalObservationBase):
    observation_timestamp: datetime
    source: str
    ingestion_batch_id: str

class ThermalObservationResponse(ThermalObservationBase):
    id: int
    observation_timestamp: datetime
    ingestion_timestamp: datetime
    source: str
    ingestion_batch_id: str
    geometry_wkt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ValidationReport(BaseModel):
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicates: int = 0
    missing_values: int = 0
    rejected_records: List[Dict[str, Any]] = []

class FIRMSIngestionRequest(BaseModel):
    source: Optional[str] = Field(None, description="FIRMS source e.g. VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT")
    area: Optional[str] = Field(None, description="Bounding box west,south,east,north or 'world'")
    days: Optional[int] = Field(None, ge=1, le=10, description="Day range to fetch (1 to 5 for NRT)")
    date: Optional[str] = Field(None, description="Optional start date YYYY-MM-DD")

class FIRMSIngestionResponse(BaseModel):
    status: str
    batch_id: str
    source: str
    records_ingested: int
    raw_file_path: Optional[str] = None
    validation_report: ValidationReport
    safety_message: str

class AnalyticsSummary(BaseModel):
    total_observations: int
    max_frp: Optional[float]
    min_frp: Optional[float]
    avg_frp: Optional[float]
    latest_observation: Optional[datetime]
    satellites_breakdown: Dict[str, int]
    sources_breakdown: Dict[str, int]
