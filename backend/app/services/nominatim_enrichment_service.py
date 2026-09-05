import time
import json
import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.transportation_entity import TransportationEntity

logger = logging.getLogger("firms_app.nominatim_enrichment_service")

class NominatimEnrichmentService:
    """
    Dedicated service for live OpenStreetMap Nominatim location enrichment and 
    deterministic display label generation for transportation corridors.
    Enforces rate limits (1 req/sec), single-threaded requests, and database caching.
    """

    def __init__(self):
        self.base_url = settings.NOMINATIM_BASE_URL.rstrip('/')
        self.user_agent = "AVISHKAR-FIRMS-App/2.0 (contact@avishkar.org)"

    @staticmethod
    def convert_osm_id_to_lookup_id(osm_id: str) -> Optional[str]:
        """
        Converts OSM ID strings ('way/12345', 'node/67890', 'relation/999')
        into Nominatim lookup format ('W12345', 'N67890', 'R999').
        """
        if not osm_id:
            return None
        parts = osm_id.strip().split('/')
        if len(parts) == 2:
            prefix, num = parts[0].lower(), parts[1]
            if prefix == "node":
                return f"N{num}"
            elif prefix == "way":
                return f"W{num}"
            elif prefix == "relation":
                return f"R{num}"
        return None

    @staticmethod
    def build_display_label(
        name: Optional[str], 
        ref: Optional[str], 
        entity_type: str
    ) -> Tuple[str, str]:
        """
        Builds a deterministic, scientifically honest display label and name_source lineage:
        1. Official OSM name -> name_source = "OSM"
        2. OSM ref -> name_source = "OSM_REF" (e.g. "Trunk Road — NH66")
        3. Classification -> name_source = "OSM_CLASSIFICATION" (e.g. "Unnamed Primary Road")
        """
        cleaned_type = (entity_type or "").strip().lower()

        # Sector classification title map
        type_titles = {
            "motorway": "Motorway",
            "trunk": "Trunk Road",
            "primary": "Primary Road",
            "railway": "Railway Corridor",
            "rail": "Railway Corridor"
        }
        title_prefix = type_titles.get(cleaned_type, "Transportation Corridor")

        # Priority 1: Official OSM name
        if name and not name.startswith("Corridor #") and not name.startswith("Unnamed "):
            return (name.strip(), "OSM")

        # Priority 2: OSM ref
        if ref and str(ref).strip():
            return (f"{title_prefix} — {str(ref).strip()}", "OSM_REF")

        # Priority 3: Classification Fallback
        if cleaned_type == "railway" or cleaned_type == "rail":
            return ("Unnamed Railway Corridor", "OSM_CLASSIFICATION")
        elif cleaned_type == "motorway":
            return ("Unnamed Motorway", "OSM_CLASSIFICATION")
        elif cleaned_type == "trunk":
            return ("Unnamed Trunk Road", "OSM_CLASSIFICATION")
        elif cleaned_type == "primary":
            return ("Unnamed Primary Road", "OSM_CLASSIFICATION")
        else:
            return ("Unnamed Transportation Corridor", "OSM_CLASSIFICATION")

    @staticmethod
    def extract_location_context(address: Dict[str, Any]) -> Optional[str]:
        """
        Extracts administrative location context from Nominatim address dictionary
        using a deterministic hierarchy (e.g. "Mangalore, Karnataka").
        """
        if not address:
            return None

        city = (
            address.get("city") 
            or address.get("town") 
            or address.get("municipality") 
            or address.get("suburb") 
            or address.get("district")
            or address.get("county")
        )
        state = address.get("state") or address.get("region")
        country = address.get("country")

        if city and state:
            return f"{city}, {state}"
        elif city and country:
            return f"{city}, {country}"
        elif state and country:
            return f"{state}, {country}"
        elif state:
            return f"{state}"
        elif country:
            return f"{country}"
        return None

    def enrich_transportation_entities(
        self, 
        db: Session, 
        batch_size: int = 40, 
        force: bool = False
    ) -> Dict[str, int]:
        """
        Executes safe, single-threaded Nominatim location enrichment on transportation entities.
        Preserves existing OSM names, caches results in DB, and respects rate limits (1 req/sec).
        """
        # Select candidates
        if force:
            candidates = db.query(TransportationEntity).all()
        else:
            candidates = db.query(TransportationEntity).filter(
                TransportationEntity.location_context == None
            ).all()

        stats = {
            "total_candidates": len(candidates),
            "processed": 0,
            "display_labels_built": 0,
            "locations_enriched": 0,
            "skipped": 0,
            "failed": 0
        }

        if not candidates:
            logger.info("Zero transportation entities require enrichment.")
            return stats

        now = datetime.datetime.utcnow()

        # Step 1: Deterministically update display_label and name_source for all candidates
        lookup_map: Dict[str, TransportationEntity] = {}

        for entity in candidates:
            tags = {}
            if entity.raw_tags:
                try:
                    tags = json.loads(entity.raw_tags)
                except Exception:
                    tags = {}

            name_val = tags.get("name") or tags.get("name:en") or entity.name
            ref_val = tags.get("ref") or tags.get("ref:old")

            disp_label, name_src = self.build_display_label(name_val, ref_val, entity.entity_type)
            entity.display_label = disp_label
            entity.name_source = name_src
            stats["display_labels_built"] += 1

            lookup_id = self.convert_osm_id_to_lookup_id(entity.osm_id)
            if lookup_id and not entity.location_context:
                lookup_map[lookup_id] = entity

        db.commit()

        # Step 2: Batch lookup missing location_context via Nominatim API
        lookup_ids = list(lookup_map.keys())
        if not lookup_ids:
            logger.info(f"All {len(candidates)} entities already have location_context.")
            return stats

        headers = {"User-Agent": self.user_agent}
        chunks = [lookup_ids[i:i + batch_size] for i in range(0, len(lookup_ids), batch_size)]

        with httpx.Client(timeout=15.0, headers=headers) as client:
            for idx, chunk in enumerate(chunks):
                ids_param = ",".join(chunk)
                url = f"{self.base_url}/lookup?osm_ids={ids_param}&format=jsonv2&addressdetails=1"

                try:
                    logger.info(f"Nominatim lookup chunk {idx + 1}/{len(chunks)} ({len(chunk)} IDs)...")
                    response = client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data:
                            osm_type = item.get("osm_type", "").upper()
                            osm_num = item.get("osm_id")
                            item_lookup_id = f"{osm_type[0]}{osm_num}" if (osm_type and osm_num) else None

                            if item_lookup_id in lookup_map:
                                target_entity = lookup_map[item_lookup_id]
                                address = item.get("address", {})
                                loc_ctx = self.extract_location_context(address)

                                if loc_ctx:
                                    target_entity.location_context = loc_ctx
                                    target_entity.location_source = "NOMINATIM_LOOKUP"
                                    target_entity.enriched_at = now
                                    stats["locations_enriched"] += 1

                        stats["processed"] += len(chunk)
                        db.commit()
                    else:
                        logger.warning(f"Nominatim lookup returned status {response.status_code}")
                        stats["failed"] += len(chunk)
                except Exception as e:
                    logger.error(f"Nominatim lookup HTTP request failed: {e}")
                    stats["failed"] += len(chunk)

                # Rate limiting safeguard: 1 req/sec
                if idx < len(chunks) - 1:
                    time.sleep(1.1)

        logger.info(f"Phase 3D Enrichment complete: {stats}")
        return stats
