"""PostGIS model for validated Phase 1 FIRMS observations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.database import Base


class ThermalObservation(Base):
    """A validated thermal anomaly observation, not a confirmed fire."""

    __tablename__ = "thermal_observations"
    __table_args__ = (
        UniqueConstraint("observation_key", name="uq_thermal_observations_observation_key"),
        Index("ix_thermal_observations_source_timestamp", "source", "observation_timestamp"),
        Index("ix_thermal_observations_ingestion_batch", "ingestion_batch_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    observation_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    observation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingestion_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingestion_batch_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    frp: Mapped[float | None] = mapped_column(Float, nullable=True)
    bright_ti4: Mapped[float | None] = mapped_column(Float, nullable=True)
    bright_ti5: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    satellite: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instrument: Mapped[str | None] = mapped_column(String(64), nullable=True)
    daynight: Mapped[str | None] = mapped_column(String(8), nullable=True)
    scan: Mapped[float | None] = mapped_column(Float, nullable=True)
    track: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    original_fields: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

