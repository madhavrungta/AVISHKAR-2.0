import os
import json
import uuid
import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
import httpx
import pandas as pd
from sqlalchemy.orm import Session
from shapely.geometry import Point, Polygon, MultiPolygon, LineString
from shapely.ops import transform
import pyproj

try:
    from geoalchemy2.shape import from_shape
    HAS_GEOALCHEMY_SHAPE = True
except ImportError:
    from_shape = None
    HAS_GEOALCHEMY_SHAPE = False

from app.config import settings
from app.models.industrial_facility import IndustrialFacility
from app.models.healthcare_facility import HealthcareFacility
from app.models.transportation_entity import TransportationEntity
from app.models.thermal_observation import is_sqlite, HAS_GEOALCHEMY2
from app.schemas.industrial_facility import OSMIngestionResponse
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.osm_service")

class OSMIngestionError(Exception):
    """Custom exception for Overpass API ingestion failures."""
    pass

class OSMDataService:
    """
    Service layer for querying OpenStreetMap Overpass API,
    parsing industrial infrastructure geometries, and persisting to PostGIS.
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self):
        self.raw_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
        os.makedirs(self.raw_data_dir, exist_ok=True)

    def build_overpass_query(self, bbox_str: str) -> str:
        """
        Builds Overpass QL query string for industrial facilities.
        Expected bbox_str: 'west,south,east,north'
        Overpass bbox order: (south, west, north, east)
        """
        coords = [float(c.strip()) for c in bbox_str.split(",")]
        if len(coords) != 4:
            raise OSMIngestionError("Invalid bbox format. Expected 'west,south,east,north'.")
        w, s, e, n = coords
        overpass_bbox = f"{s},{w},{n},{e}"

        query = f"""
        [out:json][timeout:60];
        (
          node["landuse"="industrial"]({overpass_bbox});
          way["landuse"="industrial"]({overpass_bbox});
          relation["landuse"="industrial"]({overpass_bbox});
          node["industrial"]({overpass_bbox});
          way["industrial"]({overpass_bbox});
          relation["industrial"]({overpass_bbox});
          node["power"="plant"]({overpass_bbox});
          way["power"="plant"]({overpass_bbox});
          relation["power"="plant"]({overpass_bbox});
          node["power"="substation"]({overpass_bbox});
          way["power"="substation"]({overpass_bbox});
          relation["power"="substation"]({overpass_bbox});
          node["man_made"="works"]({overpass_bbox});
          way["man_made"="works"]({overpass_bbox});
          relation["man_made"="works"]({overpass_bbox});
          node["man_made"="petroleum_refinery"]({overpass_bbox});
          way["man_made"="petroleum_refinery"]({overpass_bbox});
          relation["man_made"="petroleum_refinery"]({overpass_bbox});
          node["amenity"="hospital"]({overpass_bbox});
          way["amenity"="hospital"]({overpass_bbox});
          way["highway"="motorway"]({overpass_bbox});
          way["highway"="trunk"]({overpass_bbox});
          way["highway"="primary"]({overpass_bbox});
          way["railway"="rail"]({overpass_bbox});
        );
        out body;
        >;
        out skel qt;
        """
        return query

    def fetch_overpass_data(self, bbox_str: str) -> Tuple[Dict[str, Any], str]:
        """Fetches raw JSON payload from Overpass API."""
        query = self.build_overpass_query(bbox_str)
        batch_id = f"osm_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        logger.info(f"Querying OpenStreetMap Overpass API for area: {bbox_str}")
        try:
            headers = {"User-Agent": "AVISHKAR-FIRMS-App/2.0 (contact@avishkar.org)"}
            with httpx.Client(timeout=60.0, headers=headers) as client:
                response = client.post(self.OVERPASS_URL, data={"data": query})
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Overpass API returned {len(data.get('elements', []))} elements.")
                return data, batch_id
            else:
                raise OSMIngestionError(f"Overpass API returned status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Error requesting Overpass API: {e}")
            raise OSMIngestionError(f"Overpass API request failed: {e}")

    def save_raw_osm(self, data: Dict[str, Any], batch_id: str) -> str:
        """Saves raw JSON response to preserve data lineage."""
        filename = f"osm_facilities_{batch_id}.json"
        filepath = os.path.join(self.raw_data_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath

    def categorize_facility_type(self, tags: Dict[str, Any]) -> str:
        """Classifies raw OSM tags into standardized industrial & energy categories."""
        man_made = str(tags.get("man_made", "")).lower()
        industrial = str(tags.get("industrial", "")).lower()
        power = str(tags.get("power", "")).lower()
        substation = str(tags.get("substation", "")).lower()

        if "refinery" in man_made or "refinery" in industrial or "oil" in industrial or "petroleum" in man_made:
            return "refinery"
        if "substation" in power or "substation" in industrial or "substation" in tags or substation != "":
            return "substation"
        if "plant" in power or "power" in industrial or "generator" in tags:
            return "power_plant"
        if "steel" in industrial or "metal" in industrial or "works" in man_made:
            return "steel_works"
        if "chemical" in industrial or "pharmaceutical" in industrial:
            return "chemical"
        return "industrial"

    def calculate_polygon_area_sqm(self, geom: Polygon) -> float:
        """Calculates approximate surface area in square meters for WGS84 polygon."""
        try:
            # Planar equal-area projection transform
            proj = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
            projected_geom = transform(proj, geom)
            return abs(float(projected_geom.area))
        except Exception:
            return 0.0

    def parse_osm_elements(self, data: Dict[str, Any], batch_id: str) -> List[Dict[str, Any]]:
        """Parses Overpass nodes & ways into facility dicts with geometries & centroids."""
        elements = data.get("elements", [])
        
        # 1. Map nodes
        nodes = {}
        for elem in elements:
            if elem.get("type") == "node":
                nodes[elem["id"]] = (elem["lat"], elem["lon"])

        facilities = []

        # 2. Parse ways and nodes with tags
        for elem in elements:
            tags = elem.get("tags", {})
            if not tags:
                continue

            elem_type = elem.get("type")
            elem_id = elem.get("id")
            osm_feature_id = f"{elem_type}/{elem_id}"

            name = tags.get("name") or tags.get("name:en") or f"Industrial Site #{elem_id}"
            operator = tags.get("operator")
            fac_type = self.categorize_facility_type(tags)

            geom = None
            lat, lon = None, None
            area_sqm = 0.0

            if elem_type == "node" and "lat" in elem and "lon" in elem:
                lat, lon = elem["lat"], elem["lon"]
                geom = Point(lon, lat)
                area_sqm = 100.0  # Default nominal point area
            elif elem_type == "way" and "nodes" in elem:
                way_nodes = elem["nodes"]
                coord_list = [nodes[nid] for nid in way_nodes if nid in nodes]
                if len(coord_list) >= 3:
                    # Reverse to (lon, lat) for Shapely
                    shapely_coords = [(c[1], c[0]) for c in coord_list]
                    poly = Polygon(shapely_coords)
                    if poly.is_valid and not poly.is_empty:
                        geom = poly
                        centroid = poly.centroid
                        lat, lon = centroid.y, centroid.x
                        area_sqm = self.calculate_polygon_area_sqm(poly)

            if geom is not None and lat is not None and lon is not None:
                facilities.append({
                    "osm_id": osm_feature_id,
                    "name": name,
                    "facility_type": fac_type,
                    "operator": operator,
                    "latitude": lat,
                    "longitude": lon,
                    "geometry": geom,
                    "area_sqm": area_sqm,
                    "raw_tags": json.dumps(tags),
                    "ingestion_batch_id": batch_id
                })

        return facilities

    def ingest_osm_facilities(
        self, 
        db: Session, 
        bbox_str: str = "68.0,6.0,97.0,37.0",
        raw_json_override: Optional[Dict[str, Any]] = None
    ) -> OSMIngestionResponse:
        """Executes full OSM ingestion pipeline."""
        if raw_json_override is not None:
            data = raw_json_override
            batch_id = f"osm_mock_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            raw_path = self.save_raw_osm(data, batch_id)
        else:
            data, batch_id = self.fetch_overpass_data(bbox_str)
            raw_path = self.save_raw_osm(data, batch_id)

        parsed_facilities = self.parse_osm_elements(data, batch_id)

        ingested_count = 0
        type_summary: Dict[str, int] = {}
        now = datetime.datetime.utcnow()

        for fac in parsed_facilities:
            # Check duplicate by osm_id
            existing = db.query(IndustrialFacility).filter(IndustrialFacility.osm_id == fac["osm_id"]).first()
            if existing:
                continue

            geom = fac["geometry"]
            geom_val = None
            if HAS_GEOALCHEMY2 and HAS_GEOALCHEMY_SHAPE and not is_sqlite and from_shape:
                geom_val = from_shape(geom, srid=4326)
            else:
                geom_val = geom.wkt

            db_fac = IndustrialFacility(
                osm_id=fac["osm_id"],
                name=fac["name"],
                facility_type=fac["facility_type"],
                operator=fac["operator"],
                latitude=fac["latitude"],
                longitude=fac["longitude"],
                geometry=geom_val,
                area_sqm=fac["area_sqm"],
                raw_tags=fac["raw_tags"],
                ingestion_batch_id=batch_id,
                created_at=now
            )
            db.add(db_fac)
            ingested_count += 1
            type_summary[fac["facility_type"]] = type_summary.get(fac["facility_type"], 0) + 1

        db.commit()
        logger.info(f"Ingested {ingested_count} OSM industrial facilities into PostGIS DB (Batch ID: {batch_id}).")

        return OSMIngestionResponse(
            status="success",
            batch_id=batch_id,
            facilities_ingested=ingested_count,
            raw_file_path=raw_path,
            types_summary=type_summary
        )

    def ingest_healthcare_facilities(
        self,
        db: Session,
        bbox_str: str = "68.0,6.0,97.0,37.0",
        raw_json_override: Optional[Dict[str, Any]] = None
    ) -> int:
        """Parses and persists healthcare entities (hospitals) into PostGIS DB."""
        if raw_json_override is not None:
            data = raw_json_override
            batch_id = f"osm_hosp_mock_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        else:
            data, batch_id = self.fetch_overpass_data(bbox_str)

        elements = data.get("elements", [])
        nodes = {elem["id"]: (elem["lat"], elem["lon"]) for elem in elements if elem.get("type") == "node"}
        
        ingested_count = 0
        now = datetime.datetime.utcnow()

        for elem in elements:
            tags = elem.get("tags", {})
            amenity = str(tags.get("amenity", "")).lower()
            if amenity != "hospital":
                continue

            elem_type = elem.get("type")
            elem_id = elem.get("id")
            osm_id = f"{elem_type}/{elem_id}"

            # Check duplicate by osm_id
            existing = db.query(HealthcareFacility).filter(HealthcareFacility.osm_id == osm_id).first()
            if existing:
                continue

            name = tags.get("name") or tags.get("name:en") or f"Hospital #{elem_id}"
            operator = tags.get("operator")

            geom = None
            lat, lon = None, None
            area_sqm = 0.0

            if elem_type == "node" and "lat" in elem and "lon" in elem:
                lat, lon = elem["lat"], elem["lon"]
                geom = Point(lon, lat)
                area_sqm = 100.0
            elif elem_type == "way" and "nodes" in elem:
                way_nodes = elem["nodes"]
                coord_list = [nodes[nid] for nid in way_nodes if nid in nodes]
                if len(coord_list) >= 3:
                    shapely_coords = [(c[1], c[0]) for c in coord_list]
                    poly = Polygon(shapely_coords)
                    if poly.is_valid and not poly.is_empty:
                        geom = poly
                        lat, lon = poly.centroid.y, poly.centroid.x
                        area_sqm = self.calculate_polygon_area_sqm(poly)

            if geom is not None and lat is not None and lon is not None:
                geom_val = from_shape(geom, srid=4326) if (HAS_GEOALCHEMY2 and HAS_GEOALCHEMY_SHAPE and not is_sqlite and from_shape) else geom.wkt
                db_hosp = HealthcareFacility(
                    osm_id=osm_id,
                    name=name,
                    entity_type="hospital",
                    operator=operator,
                    latitude=lat,
                    longitude=lon,
                    geometry=geom_val,
                    area_sqm=area_sqm,
                    raw_tags=json.dumps(tags),
                    ingestion_batch_id=batch_id,
                    created_at=now
                )
                db.add(db_hosp)
                ingested_count += 1

        db.commit()
        logger.info(f"Ingested {ingested_count} OSM healthcare facilities (Batch ID: {batch_id}).")
        return ingested_count

    def ingest_transportation_entities(
        self,
        db: Session,
        bbox_str: str = "68.0,6.0,97.0,37.0",
        raw_json_override: Optional[Dict[str, Any]] = None
    ) -> int:
        """Parses and persists transportation corridors (motorway, trunk, primary, railway) into PostGIS DB."""
        if raw_json_override is not None:
            data = raw_json_override
            batch_id = f"osm_trans_mock_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        else:
            data, batch_id = self.fetch_overpass_data(bbox_str)

        elements = data.get("elements", [])
        nodes = {elem["id"]: (elem["lat"], elem["lon"]) for elem in elements if elem.get("type") == "node"}
        
        ingested_count = 0
        now = datetime.datetime.utcnow()

        for elem in elements:
            tags = elem.get("tags", {})
            highway = str(tags.get("highway", "")).lower()
            railway = str(tags.get("railway", "")).lower()

            entity_type = None
            transport_category = None

            if highway in ["motorway", "trunk", "primary"]:
                entity_type = highway
                transport_category = "road"
            elif railway == "rail":
                entity_type = "railway"
                transport_category = "railway"

            if not entity_type or not transport_category:
                continue

            elem_type = elem.get("type")
            elem_id = elem.get("id")
            osm_id = f"{elem_type}/{elem_id}"

            # Check duplicate by osm_id
            existing = db.query(TransportationEntity).filter(TransportationEntity.osm_id == osm_id).first()
            if existing:
                continue

            raw_name = tags.get("name") or tags.get("name:en")
            ref_val = tags.get("ref") or tags.get("ref:old")
            
            from app.services.nominatim_enrichment_service import NominatimEnrichmentService
            disp_label, name_src = NominatimEnrichmentService.build_display_label(raw_name, ref_val, entity_type)

            geom = None
            lat, lon = None, None

            if elem_type == "way" and "nodes" in elem:
                way_nodes = elem["nodes"]
                coord_list = [nodes[nid] for nid in way_nodes if nid in nodes]
                if len(coord_list) >= 2:
                    shapely_coords = [(c[1], c[0]) for c in coord_list]
                    line = LineString(shapely_coords)
                    if line.is_valid and not line.is_empty:
                        geom = line
                        lat, lon = line.centroid.y, line.centroid.x

            if geom is not None and lat is not None and lon is not None:
                geom_val = from_shape(geom, srid=4326) if (HAS_GEOALCHEMY2 and HAS_GEOALCHEMY_SHAPE and not is_sqlite and from_shape) else geom.wkt
                db_trans = TransportationEntity(
                    osm_id=osm_id,
                    name=raw_name,
                    display_label=disp_label,
                    name_source=name_src,
                    entity_type=entity_type,
                    transport_category=transport_category,
                    latitude=lat,
                    longitude=lon,
                    geometry=geom_val,
                    raw_tags=json.dumps(tags),
                    ingestion_batch_id=batch_id,
                    created_at=now
                )
                db.add(db_trans)
                ingested_count += 1

        db.commit()
        logger.info(f"Ingested {ingested_count} OSM transportation corridors (Batch ID: {batch_id}).")
        return ingested_count
