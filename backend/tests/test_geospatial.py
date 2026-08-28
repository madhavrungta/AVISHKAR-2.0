import pytest
import geopandas as gpd
from shapely.geometry import Point
from app.geospatial.utils import (
    create_point_geometry,
    convert_records_to_geodataframe,
    calculate_geodesic_distance_meters
)

def test_create_point_geometry():
    pt = create_point_geometry(77.2090, 28.6139)
    assert isinstance(pt, Point)
    assert pt.x == 77.2090
    assert pt.y == 28.6139

def test_convert_records_to_geodataframe():
    records = [
        {"latitude": 28.6139, "longitude": 77.2090, "frp": 15.2},
        {"latitude": 19.0760, "longitude": 72.8777, "frp": 8.4}
    ]
    gdf = convert_records_to_geodataframe(records)
    
    assert len(gdf) == 2
    assert "geometry" in gdf.columns
    assert isinstance(gdf["geometry"].iloc[0], Point)

def test_calculate_geodesic_distance_meters():
    # Distance between New Delhi (28.6139, 77.2090) and Mumbai (19.0760, 72.8777) ~1148 km
    dist_m = calculate_geodesic_distance_meters(28.6139, 77.2090, 19.0760, 72.8777)
    dist_km = dist_m / 1000.0
    
    assert 1100.0 <= dist_km <= 1200.0
