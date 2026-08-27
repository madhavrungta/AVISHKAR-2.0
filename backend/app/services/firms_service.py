"""Official NASA FIRMS Area API ingestion service."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote

import httpx

from app.config import Settings
from app.schemas.firms import FirmsIngestionRequest, IngestionResult
from app.services.firms_validation import (
    FirmsSchemaError,
    ValidationOutcome,
    parse_firms_csv,
    validate_and_normalize,
)
from app.services.raw_storage import RawFirmsStorage


LOGGER = logging.getLogger(__name__)
FIRMS_AREA_API_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


class FirmsConfigurationError(RuntimeError):
    """Raised when a required operator-side FIRMS setting is absent."""


class FirmsApiError(RuntimeError):
    """Raised when FIRMS cannot provide a usable API response."""


@dataclass(frozen=True)
class PreparedFirmsIngestion:
    """A raw archived and validated batch awaiting optional database insertion."""

    result: IngestionResult
    validation: ValidationOutcome


class FirmsService:
    """Fetches the documented FIRMS Area CSV API without logging the MAP_KEY."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self._http_client = http_client
        self._sleep = sleep
        self._storage = RawFirmsStorage(settings.raw_data_dir)

    def _build_url(self, request: FirmsIngestionRequest) -> str:
        """Build the current documented Area API URL.

        This URL contains a credential and must never be put in a log message or
        returned from the API.
        """

        if not self.settings.has_firms_map_key:
            raise FirmsConfigurationError(
                "FIRMS_MAP_KEY is not configured. Add it to backend/.env."
            )
        parts = [
            FIRMS_AREA_API_BASE_URL,
            quote(self.settings.firms_map_key or "", safe=""),
            quote(request.source, safe=""),
            quote(request.area, safe=","),
            str(request.days),
        ]
        if request.start_date is not None:
            parts.append(request.start_date.isoformat())
        return "/".join(parts)

    def _get_csv(self, request: FirmsIngestionRequest) -> str:
        """Retrieve CSV with bounded retries for transport and transient HTTP errors."""

        url = self._build_url(request)
        owns_client = self._http_client is None
        client = self._http_client or httpx.Client(
            timeout=httpx.Timeout(self.settings.firms_timeout_seconds),
            follow_redirects=True,
        )
        try:
            for attempt in range(self.settings.firms_max_retries + 1):
                try:
                    response = client.get(url)
                except httpx.RequestError as error:
                    if attempt == self.settings.firms_max_retries:
                        raise FirmsApiError(
                            "Unable to reach the NASA FIRMS API after retrying. "
                            "Check network connectivity and try again."
                        ) from error
                    self._wait_before_retry(attempt, "network error")
                    continue

                if response.status_code == 200:
                    return response.text
                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt == self.settings.firms_max_retries:
                        raise FirmsApiError(
                            "NASA FIRMS API returned a transient error after retrying "
                            f"(HTTP {response.status_code}). Try again later."
                        )
                    self._wait_before_retry(attempt, f"HTTP {response.status_code}")
                    continue
                raise FirmsApiError(
                    "NASA FIRMS API rejected the request "
                    f"(HTTP {response.status_code}). Check source, area, date, and MAP_KEY."
                )
            raise AssertionError("Retry loop should return or raise.")
        finally:
            if owns_client:
                client.close()

    def _wait_before_retry(self, attempt: int, reason: str) -> None:
        seconds = 0.5 * (2**attempt)
        LOGGER.warning("Retrying FIRMS request after %s; attempt=%s", reason, attempt + 1)
        self._sleep(seconds)

    def prepare_ingestion(self, request: FirmsIngestionRequest) -> PreparedFirmsIngestion:
        """Fetch, archive, validate, and normalize one FIRMS response batch."""

        ingestion_timestamp = datetime.now(UTC)
        ingestion_batch_id = uuid.uuid4()
        LOGGER.info(
            "Starting FIRMS ingestion batch=%s source=%s area=%s days=%s",
            ingestion_batch_id,
            request.source,
            request.area,
            request.days,
        )
        csv_text = self._get_csv(request)
        archive = self._storage.reserve_archive(request.source, ingestion_timestamp)
        self._storage.write_csv(archive, csv_text)

        metadata = {
            "ingestion_batch_id": str(ingestion_batch_id),
            "ingestion_timestamp": ingestion_timestamp.isoformat(),
            "source": request.source,
            "area": request.area,
            "days": request.days,
            "start_date": request.start_date.isoformat() if request.start_date else None,
            "api_endpoint_template": (
                "/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA_COORDINATES}/{DAY_RANGE}[/{DATE}]"
            ),
        }
        try:
            frame = parse_firms_csv(csv_text)
            validation = validate_and_normalize(
                frame,
                source=request.source,
                ingestion_timestamp=ingestion_timestamp,
                ingestion_batch_id=ingestion_batch_id,
            )
        except FirmsSchemaError as error:
            metadata.update({"status": "schema_error", "error": str(error)})
            self._storage.write_metadata(archive, metadata)
            raise

        metadata.update(
            {
                "status": "validated",
                "received_columns": [str(column) for column in frame.columns],
                "validation_report": validation.report.model_dump(mode="json"),
            }
        )
        self._storage.write_metadata(archive, metadata)
        result = IngestionResult(
            ingestion_batch_id=ingestion_batch_id,
            source=request.source,
            area=request.area,
            days=request.days,
            start_date=request.start_date,
            ingestion_timestamp=ingestion_timestamp,
            raw_archive=archive,
            validation_report=validation.report,
        )
        LOGGER.info(
            "Validated FIRMS batch=%s valid=%s invalid=%s duplicates=%s",
            ingestion_batch_id,
            validation.report.valid_records,
            validation.report.invalid_records,
            validation.report.duplicates,
        )
        return PreparedFirmsIngestion(result=result, validation=validation)

