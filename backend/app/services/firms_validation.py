"""Runtime schema checks and quality reporting for FIRMS CSV responses."""

from __future__ import annotations

import hashlib
import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Any

import pandas as pd

from app.schemas.firms import NormalizedObservation, ValidationReport


REQUIRED_COLUMNS = frozenset({"latitude", "longitude", "acq_date", "acq_time"})
OPTIONAL_NUMERIC_COLUMNS = ("bright_ti4", "bright_ti5", "frp", "scan", "track")
CANONICAL_COLUMNS = (
    "latitude",
    "longitude",
    "bright_ti4",
    "bright_ti5",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "frp",
    "daynight",
)


class FirmsSchemaError(ValueError):
    """Raised when a received FIRMS response cannot be treated as a data CSV."""


@dataclass(frozen=True)
class ValidationOutcome:
    """Normalized valid records plus their complete validation report."""

    observations: list[NormalizedObservation]
    report: ValidationReport


def parse_firms_csv(csv_text: str) -> pd.DataFrame:
    """Parse CSV and validate required source headers at runtime."""

    try:
        frame = pd.read_csv(pd.io.common.StringIO(csv_text), dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError as error:
        raise FirmsSchemaError("FIRMS response did not contain a CSV header.") from error

    normalized_headers = {str(column).strip().lower(): str(column) for column in frame.columns}
    missing_required = REQUIRED_COLUMNS.difference(normalized_headers)
    if missing_required:
        missing = ", ".join(sorted(missing_required))
        raise FirmsSchemaError(
            f"FIRMS response schema is missing required column(s): {missing}. "
            "The raw response was archived for review."
        )
    # Normalize only column names internally. Values and unrecognized columns remain untouched.
    return frame.rename(columns={actual: canonical for canonical, actual in normalized_headers.items()})


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or pd.isna(value)


def _as_original_value(value: Any) -> Any:
    """Convert pandas scalar values into JSON-compatible original-field values."""

    if _is_missing(value):
        return None
    if hasattr(value, "item"):
        try:
            value = value.item()
        except ValueError:
            pass
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    return value


def _optional_text(value: Any) -> str | None:
    if _is_missing(value):
        return None
    return str(value).strip()


def _parse_number(value: Any, field: str, *, non_negative: bool = True) -> float | None:
    if _is_missing(value):
        return None
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} is not numeric") from error
    if not math.isfinite(number):
        raise ValueError(f"{field} is not finite")
    if non_negative and number < 0:
        raise ValueError(f"{field} cannot be negative")
    return number


def _parse_timestamp(acq_date: Any, acq_time: Any) -> datetime:
    if _is_missing(acq_date) or _is_missing(acq_time):
        raise ValueError("acq_date and acq_time are required")
    try:
        parsed_date = datetime.strptime(str(acq_date).strip(), "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("acq_date must use YYYY-MM-DD") from error

    raw_time = str(acq_time).strip()
    if raw_time.endswith(".0"):
        raw_time = raw_time[:-2]
    if not raw_time.isdigit():
        raise ValueError("acq_time must be an HHMM value")
    parsed_time = raw_time.zfill(4)
    hours, minutes = int(parsed_time[:2]), int(parsed_time[2:])
    if hours > 23 or minutes > 59:
        raise ValueError("acq_time is outside 0000–2359")
    return datetime.combine(parsed_date, time(hours, minutes), tzinfo=UTC)


def _observation_key(
    source: str,
    latitude: float,
    longitude: float,
    observation_timestamp: datetime,
    satellite: str | None,
) -> str:
    """Build a stable dedupe key without relying on non-guaranteed FIRMS IDs."""

    identity = "|".join(
        (
            source,
            f"{latitude:.6f}",
            f"{longitude:.6f}",
            observation_timestamp.isoformat(),
            satellite or "",
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def validate_and_normalize(
    frame: pd.DataFrame,
    *,
    source: str,
    ingestion_timestamp: datetime,
    ingestion_batch_id: uuid.UUID,
) -> ValidationOutcome:
    """Validate rows explicitly and return distinct normalized observations.

    A duplicate is valid syntactically but excluded from the output to avoid duplicate
    database rows. Invalid and duplicate rows are always recorded in the report.
    """

    if ingestion_timestamp.tzinfo is None:
        raise ValueError("ingestion_timestamp must be timezone-aware")

    missing_values: dict[str, int] = {}
    for column in CANONICAL_COLUMNS:
        if column not in frame.columns:
            missing_values[column] = len(frame)
        else:
            missing_values[column] = sum(_is_missing(value) for value in frame[column])

    observations: list[NormalizedObservation] = []
    rejected_records: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    duplicates = 0

    for index, row in frame.iterrows():
        original_fields = {str(column): _as_original_value(value) for column, value in row.items()}
        try:
            latitude = _parse_number(row["latitude"], "latitude", non_negative=False)
            longitude = _parse_number(row["longitude"], "longitude", non_negative=False)
            if latitude is None or longitude is None:
                raise ValueError("latitude and longitude are required")
            if not -90 <= latitude <= 90:
                raise ValueError("latitude is outside -90 to 90")
            if not -180 <= longitude <= 180:
                raise ValueError("longitude is outside -180 to 180")

            observation_timestamp = _parse_timestamp(row["acq_date"], row["acq_time"])
            numeric_values = {
                field: _parse_number(row.get(field), field) for field in OPTIONAL_NUMERIC_COLUMNS
            }
            satellite = _optional_text(row.get("satellite"))
            key = _observation_key(source, latitude, longitude, observation_timestamp, satellite)
        except ValueError as error:
            rejected_records.append(
                {"row_number": int(index) + 2, "reason": str(error), "original_fields": original_fields}
            )
            continue

        if key in seen_keys:
            duplicates += 1
            rejected_records.append(
                {
                    "row_number": int(index) + 2,
                    "reason": "duplicate source/time/location/satellite observation",
                    "original_fields": original_fields,
                }
            )
            continue
        seen_keys.add(key)

        observations.append(
            NormalizedObservation(
                observation_key=key,
                latitude=latitude,
                longitude=longitude,
                observation_timestamp=observation_timestamp,
                ingestion_timestamp=ingestion_timestamp,
                ingestion_batch_id=ingestion_batch_id,
                source=source,
                bright_ti4=numeric_values["bright_ti4"],
                bright_ti5=numeric_values["bright_ti5"],
                frp=numeric_values["frp"],
                confidence=_optional_text(row.get("confidence")),
                satellite=satellite,
                instrument=_optional_text(row.get("instrument")),
                daynight=_optional_text(row.get("daynight")),
                scan=numeric_values["scan"],
                track=numeric_values["track"],
                original_fields=original_fields,
            )
        )

    report = ValidationReport(
        total_records=len(frame),
        valid_records=len(observations),
        invalid_records=len(rejected_records) - duplicates,
        duplicates=duplicates,
        missing_values=missing_values,
        rejected_records=rejected_records,
    )
    return ValidationOutcome(observations=observations, report=report)

