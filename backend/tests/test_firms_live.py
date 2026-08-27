from __future__ import annotations

import os

import pytest

from app.config import Settings
from app.schemas.firms import FirmsIngestionRequest
from app.services.firms_service import FirmsService


pytestmark = pytest.mark.live


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_FIRMS_TESTS") != "1" or not os.getenv("FIRMS_MAP_KEY"),
    reason="Set RUN_LIVE_FIRMS_TESTS=1 and FIRMS_MAP_KEY to call the live NASA API.",
)
def test_live_firms_area_request_archives_and_validates(tmp_path) -> None:
    service = FirmsService(
        Settings(firms_map_key=os.environ["FIRMS_MAP_KEY"], raw_data_dir=tmp_path)
    )
    result = service.prepare_ingestion(
        FirmsIngestionRequest(source="VIIRS_NOAA20_NRT", area="77,28,78,29", days=1)
    )

    assert result.result.raw_archive.csv_path.endswith(".csv")
    assert result.result.validation_report.total_records >= 0

