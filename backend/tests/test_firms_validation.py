from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.services.firms_validation import FirmsSchemaError, parse_firms_csv, validate_and_normalize


def test_normalizes_timestamp_and_preserves_original_fields(firms_csv: str) -> None:
    outcome = validate_and_normalize(
        parse_firms_csv(firms_csv),
        source="VIIRS_SNPP_NRT",
        ingestion_timestamp=datetime(2026, 8, 20, 12, tzinfo=UTC),
        ingestion_batch_id=uuid.uuid4(),
    )

    assert outcome.report.total_records == 1
    assert outcome.report.valid_records == 1
    observation = outcome.observations[0]
    assert observation.observation_timestamp == datetime(2026, 8, 20, 5, 30, tzinfo=UTC)
    assert observation.original_fields["version"] == "2.0NRT"
    assert observation.frp == 12.5


def test_reports_invalid_coordinates_negative_frp_and_duplicates(firms_csv: str) -> None:
    invalid_and_duplicate_csv = "\n".join(
        [
            firms_csv,
            "22.5726,88.3639,330.1,0.4,0.5,2026-08-20,530,NPP,VIIRS,n,2.0NRT,290.2,12.5,D",
            "91,88.3639,330.1,0.4,0.5,2026-08-20,530,NPP,VIIRS,n,2.0NRT,290.2,12.5,D",
            "22.6,88.4,330.1,0.4,0.5,2026-08-20,600,NPP,VIIRS,n,2.0NRT,290.2,-1,D",
        ]
    )
    outcome = validate_and_normalize(
        parse_firms_csv(invalid_and_duplicate_csv),
        source="VIIRS_SNPP_NRT",
        ingestion_timestamp=datetime(2026, 8, 20, 12, tzinfo=UTC),
        ingestion_batch_id=uuid.uuid4(),
    )

    assert outcome.report.total_records == 4
    assert outcome.report.valid_records == 1
    assert outcome.report.invalid_records == 2
    assert outcome.report.duplicates == 1
    assert len(outcome.report.rejected_records) == 3


def test_rejects_missing_required_source_headers() -> None:
    with pytest.raises(FirmsSchemaError, match="longitude"):
        parse_firms_csv("latitude,acq_date,acq_time\n22.5,2026-08-20,530\n")


def test_rejects_malformed_acquisition_time() -> None:
    csv = "latitude,longitude,acq_date,acq_time\n22.5,88.3,2026-08-20,2460\n"
    outcome = validate_and_normalize(
        parse_firms_csv(csv),
        source="VIIRS_SNPP_NRT",
        ingestion_timestamp=datetime(2026, 8, 20, 12, tzinfo=UTC),
        ingestion_batch_id=uuid.uuid4(),
    )

    assert outcome.report.invalid_records == 1
    assert "acq_time" in outcome.report.rejected_records[0]["reason"]

