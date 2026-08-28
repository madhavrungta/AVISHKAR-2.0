import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
from shapely.geometry import Point
from shapely.ops import transform
import pyproj

try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    gpd = None
    HAS_GEOPANDAS = False

logger = logging.getLogger("firms_app.geospatial")


def create_point_geometry(lon: float, lat: float) -> Point:
    """Create a Shapely Point geometry from longitude and latitude in EPSG:4326."""
    return Point(float(lon), float(lat))

def convert_records_to_geodataframe(
    records: List[Dict[str, Any]], 
    lon_col: str = "longitude", 
    lat_col: str = "latitude",
    crs: str = "EPSG:4326"
) -> gpd.GeoDataFrame:
    """
    Converts a list of dictionary observations into a GeoPandas GeoDataFrame.
    
    Args:
        records: List of dictionaries containing observation data.
        lon_col: Column name for longitude.
        lat_col: Column name for latitude.
        crs: Coordinate Reference System (default: EPSG:4326).
        
    Returns:
        GeoPandas GeoDataFrame with Shapely Point geometries.
    """
    if not records:
        df = pd.DataFrame(columns=[lon_col, lat_col, "geometry"])
        if HAS_GEOPANDAS and gpd:
            return gpd.GeoDataFrame(df, geometry="geometry", crs=crs)
        return df

    df = pd.DataFrame(records)
    
    # Generate Shapely Point geometries
    geometry = [
        create_point_geometry(row[lon_col], row[lat_col]) 
        if pd.notnull(row[lon_col]) and pd.notnull(row[lat_col]) else None 
        for _, row in df.iterrows()
    ]
    
    if HAS_GEOPANDAS and gpd:
        return gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
    
    df["geometry"] = geometry
    return df

def calculate_geodesic_distance_meters(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculates accurate physical distance between two WGS84 points in meters 
    using geodesic transformation (WGS84 ellipsoid).
    
    NEVER uses raw lat/lon Euclidean distance.
    """
    geod = pyproj.Geod(ellps="WGS84")
    _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
    return abs(distance)
