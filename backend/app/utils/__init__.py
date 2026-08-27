"""Shared geospatial validation helpers."""

from __future__ import annotations


def parse_bounding_box(value: str) -> str:
    """Validate and normalize a bounding box string.

    Accepts 'world' or 'west,south,east,north' with proper range checks.
    Returns the normalized string.
    """

    area = value.strip()
    if area.lower() == "world":
        return "world"
    parts = area.split(",")
    if len(parts) != 4:
        raise ValueError("Area must be 'world' or west,south,east,north.")
    try:
        west, south, east, north = (float(item.strip()) for item in parts)
    except ValueError as error:
        raise ValueError("Area coordinates must be numeric.") from error
    if not (-180 <= west <= 180 and -180 <= east <= 180):
        raise ValueError("Area longitude values must be between -180 and 180.")
    if not (-90 <= south < north <= 90):
        raise ValueError("Area must have -90 <= south < north <= 90.")
    return ",".join(str(item) for item in (west, south, east, north))
