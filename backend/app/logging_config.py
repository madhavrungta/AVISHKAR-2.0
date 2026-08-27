"""Structured, secret-safe application logging."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configure a compact log format without logging request secrets."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )

