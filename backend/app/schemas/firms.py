"""Schemas shared by FIRMS ingestion service, CLI, and API."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils import parse_bounding_box


SUPPORTED_FIRMS_SOURCES = frozenset(
    {"VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"}
)


class FirmsIngestionRequest(BaseModel):
    """Safe, constrained parameters for a FIRMS Area API request."""

    model_config = ConfigDict(extra="forbid")

    source: str = "VIIRS_SNPP_NRT"
    area: str = "world"
    days: int = Field(default=1, ge=1, le=5)
    start_date: date | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SUPPORTED_FIRMS_SOURCES:
            supported = ", ".join(sorted(SUPPORTED_FIRMS_SOURCES))
            raise ValueError(f"Unsupported FIRMS source. Use one of: {supported}.")
        return normalized

    @field_validator("area")
    @classmethod
    def validate_area(cls, value: str) -> str:
        return parse_bounding_box(value)


class ValidationReport(BaseModel):
    """Auditable record-level quality summary for one response batch."""

    total_records: int
    valid_records: int
    invalid_records: int
    duplicates: int
    missing_values: dict[str, int]
    rejected_records: list[dict[str, Any]]


class NormalizedObservation(BaseModel):
    """Standard thermal-observation shape while preserving original FIRMS fields."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    observation_key: str
    latitude: float
    longitude: float
    observation_timestamp: datetime
    ingestion_timestamp: datetime
    ingestion_batch_id: uuid.UUID
    source: str
    bright_ti4: float | None = None
    bright_ti5: float | None = None
    frp: float | None = None
    confidence: str | None = None
    satellite: str | None = None
    instrument: str | None = None
    daynight: str | None = None
    scan: float | None = None
    track: float | None = None
    original_fields: dict[str, Any]


class RawPersistenceResult(BaseModel):
    """Local immutable archive locations for one ingestion batch."""

    csv_path: str
    metadata_path: str


class IngestionResult(BaseModel):
    """Outcome shared by the CLI and POST endpoint."""

    ingestion_batch_id: uuid.UUID
    source: str
    area: str
    days: int
    start_date: date | None
    ingestion_timestamp: datetime
    raw_archive: RawPersistenceResult
    validation_report: ValidationReport
    inserted_records: int = 0

