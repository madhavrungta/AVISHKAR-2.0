from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select

from app.database import get_session_factory, initialize_database
from app.models.thermal_observation import ThermalObservation
from app.services.firms_validation import parse_firms_csv, validate_and_normalize
from app.services.thermal_observation_repository import insert_observations


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="Set RUN_DATABASE_TESTS=1 with PostGIS running to execute database integration tests.",
)
def test_inserts_geometry_into_postgis(firms_csv: str) -> None:
    source = f"TEST_{uuid.uuid4().hex}"
    outcome = validate_and_normalize(
        parse_firms_csv(firms_csv),
        source=source,
        ingestion_timestamp=datetime(2026, 8, 20, 12, tzinfo=UTC),
        ingestion_batch_id=uuid.uuid4(),
    )
    initialize_database()
    with get_session_factory()() as session:
        try:
            assert insert_observations(session, outcome.observations) == 1
            stored = session.scalar(
                select(ThermalObservation).where(ThermalObservation.source == source)
            )
            assert stored is not None
            assert stored.latitude == 22.5726
            assert stored.geometry is not None
        finally:
            session.execute(delete(ThermalObservation).where(ThermalObservation.source == source))
            session.commit()

