"""API-safe thermal observation response models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ThermalObservationRead(BaseModel):
    """Read model that never infers a classification from a FIRMS record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    observation_timestamp: datetime
    ingestion_timestamp: datetime
    ingestion_batch_id: uuid.UUID
    latitude: float
    longitude: float
    frp: float | None
    bright_ti4: float | None
    bright_ti5: float | None
    confidence: str | None
    satellite: str | None
    instrument: str | None
    daynight: str | None
    scan: float | None
    track: float | None
    source: str


class ThermalObservationDetail(ThermalObservationRead):
    """Single-observation detail including preserved original FIRMS columns."""

    original_fields: dict[str, Any]


class ThermalObservationPage(BaseModel):
    """Page of observations ordered by latest acquisition time."""

    items: list[ThermalObservationRead]
    limit: int
    offset: int
    total: int


class AnalyticsSummary(BaseModel):
    """Phase 1 storage summary, not an incident count."""

    total_observations: int
    source_counts: dict[str, int]
    earliest_observation: datetime | None
    latest_observation: datetime | None

