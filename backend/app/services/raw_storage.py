"""Immutable local persistence for original FIRMS responses and metadata."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.schemas.firms import RawPersistenceResult


def _safe_source_name(source: str) -> str:
    """Create a predictable filename component without accepting path content."""

    return re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")


class RawFirmsStorage:
    """Stores a never-overwritten CSV and its JSON ingestion metadata."""

    def __init__(self, raw_data_dir: Path) -> None:
        self.raw_data_dir = raw_data_dir

    def reserve_archive(self, source: str, timestamp: datetime) -> RawPersistenceResult:
        """Write location paths using a collision-resistant UTC timestamp suffix."""

        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        stamp = timestamp.strftime("%Y%m%d_%H%M%S_%f")
        base_name = f"firms_{_safe_source_name(source)}_{stamp}"
        return RawPersistenceResult(
            csv_path=str(self.raw_data_dir / f"{base_name}.csv"),
            metadata_path=str(self.raw_data_dir / f"{base_name}.metadata.json"),
        )

    def write_csv(self, archive: RawPersistenceResult, csv_text: str) -> None:
        """Persist the exact response body without modifying it."""

        csv_path = Path(archive.csv_path)
        if csv_path.exists():
            raise FileExistsError(f"Refusing to overwrite raw FIRMS archive: {csv_path.name}")
        csv_path.write_text(csv_text, encoding="utf-8", newline="")

    def write_metadata(self, archive: RawPersistenceResult, metadata: dict[str, Any]) -> None:
        """Persist provenance and quality metadata adjacent to the raw response."""

        metadata_path = Path(archive.metadata_path)
        if metadata_path.exists():
            raise FileExistsError(f"Refusing to overwrite FIRMS metadata: {metadata_path.name}")
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

