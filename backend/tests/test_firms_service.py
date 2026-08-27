from __future__ import annotations

import httpx
import pytest

from app.config import Settings
from app.schemas.firms import FirmsIngestionRequest
from app.services.firms_service import FirmsConfigurationError, FirmsService


def test_archives_exact_response_and_metadata(tmp_path, firms_csv: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/area/csv/test-map-key/VIIRS_SNPP_NRT/" in str(request.url)
        return httpx.Response(200, text=firms_csv, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    service = FirmsService(
        Settings(firms_map_key="test-map-key", raw_data_dir=tmp_path),
        http_client=client,
        sleep=lambda _: None,
    )

    prepared = service.prepare_ingestion(
        FirmsIngestionRequest(source="VIIRS_SNPP_NRT", area="68,6,98,38", days=1)
    )

    csv_path = tmp_path / prepared.result.raw_archive.csv_path.split("\\")[-1]
    if not csv_path.exists():  # Posix paths when tests run in a Linux container.
        csv_path = tmp_path / prepared.result.raw_archive.csv_path.split("/")[-1]
    assert csv_path.read_text(encoding="utf-8") == firms_csv
    metadata = tmp_path / prepared.result.raw_archive.metadata_path.split("\\")[-1]
    if not metadata.exists():
        metadata = tmp_path / prepared.result.raw_archive.metadata_path.split("/")[-1]
    assert '"status": "validated"' in metadata.read_text(encoding="utf-8")
    assert prepared.result.validation_report.valid_records == 1


def test_missing_map_key_has_actionable_error(tmp_path) -> None:
    service = FirmsService(Settings(firms_map_key=None, raw_data_dir=tmp_path))

    with pytest.raises(FirmsConfigurationError, match="FIRMS_MAP_KEY is not configured"):
        service.prepare_ingestion(FirmsIngestionRequest())

