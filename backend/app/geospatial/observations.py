"""Geospatial representation of normalized thermal observations."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point

from app.schemas.firms import NormalizedObservation


def observations_to_geodataframe(
    observations: list[NormalizedObservation],
) -> gpd.GeoDataFrame:
    """Create WGS84 points in longitude/latitude order for spatial processing.

    This function intentionally does not calculate metre distances. Future proximity
    work must reproject or use geodesic/PostGIS distance operations.
    """

    rows = [observation.model_dump(mode="json") for observation in observations]
    geometry = [Point(item.longitude, item.latitude) for item in observations]
    return gpd.GeoDataFrame(rows, geometry=geometry, crs="EPSG:4326")

