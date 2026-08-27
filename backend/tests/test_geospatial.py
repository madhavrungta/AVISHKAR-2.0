from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.geospatial.observations import observations_to_geodataframe
from app.services.firms_validation import parse_firms_csv, validate_and_normalize


def test_observations_use_wgs84_points(firms_csv: str) -> None:
    outcome = validate_and_normalize(
        parse_firms_csv(firms_csv),
        source="VIIRS_SNPP_NRT",
        ingestion_timestamp=datetime(2026, 8, 20, 12, tzinfo=UTC),
        ingestion_batch_id=uuid.uuid4(),
    )
    frame = observations_to_geodataframe(outcome.observations)

    assert frame.crs.to_epsg() == 4326
    assert frame.geometry.iloc[0].x == 88.3639
    assert frame.geometry.iloc[0].y == 22.5726

