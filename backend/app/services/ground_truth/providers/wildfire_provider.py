import os
import json
import datetime
import logging
from typing import List, Dict, Any
from app.services.ground_truth.base import BaseGroundTruthProvider, GroundTruthEvidence, GroundTruthClass, LabelConfidenceLevel
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.wildfire_provider")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OFFICIAL_CATALOG_PATH = os.path.join(BASE_DIR, "data", "ground_truth_catalogs", "official", "wildfire", "fsi_v20_india_wildfires.json")
SAMPLE_CATALOG_PATH = os.path.join(BASE_DIR, "data", "ground_truth_catalogs", "fsi_wildfires.json")

class WildfireGroundTruthProvider(BaseGroundTruthProvider):
    """
    Authoritative provider for Forest Survey of India (FSI Van Agni V2.0) & NASA MCD64A1 forest fire dataset.
    """
    def __init__(self, catalog_path: str = None):
        super().__init__("FSI_VAN_AGNI_V20_OFFICIAL")
        if catalog_path:
            self.catalog_path = catalog_path
        elif os.path.exists(OFFICIAL_CATALOG_PATH):
            self.catalog_path = OFFICIAL_CATALOG_PATH
        else:
            self.catalog_path = SAMPLE_CATALOG_PATH
            self.provider_name = "FSI_VAN_AGNI_SAMPLE_UNVERIFIED"

        self._cached_records: List[Dict[str, Any]] = self._load_catalog()

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.catalog_path):
            logger.warning(f"FSI Wildfire catalog file not found at {self.catalog_path}")
            return []
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", data) if isinstance(data, dict) else data
                # Semantic filter: Explicitly ensure record category is WILDFIRE
                return [r for r in records if isinstance(r, dict) and r.get("source_category", "WILDFIRE") == "WILDFIRE"]
        except Exception as e:
            logger.error(f"Failed to load FSI Wildfire catalog: {e}")
            return []

    def fetch_evidence_near(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime.datetime,
        spatial_radius_m: float = 1000.0,
        temporal_window_hours: float = 24.0
    ) -> List[GroundTruthEvidence]:
        evidence_list: List[GroundTruthEvidence] = []

        for rec in self._cached_records:
            rec_lat = float(rec["latitude"])
            rec_lon = float(rec["longitude"])
            dist_m = calculate_geodesic_distance_meters(latitude, longitude, rec_lat, rec_lon)

            if dist_m > spatial_radius_m:
                continue

            # Temporal Window Evaluation
            t_start_str = rec.get("event_start") or rec.get("event_timestamp") or "2026-01-01T00:00:00Z"
            t_start = datetime.datetime.fromisoformat(t_start_str.replace("Z", "+00:00")).replace(tzinfo=None)
            t_end = datetime.datetime.fromisoformat(rec["event_end"].replace("Z", "+00:00")).replace(tzinfo=None) if rec.get("event_end") else None

            is_temporally_compatible = False
            if t_end:
                is_temporally_compatible = (t_start <= timestamp <= t_end)
            else:
                delta_h = abs((timestamp - t_start).total_seconds()) / 3600.0
                is_temporally_compatible = (delta_h <= temporal_window_hours)

            if not is_temporally_compatible:
                continue

            conf = LabelConfidenceLevel.HIGH if rec.get("confidence") == "HIGH" else LabelConfidenceLevel.MEDIUM

            evidence_list.append(
                GroundTruthEvidence(
                    source_name=self.provider_name,
                    source_type="FOREST_BEAT_ALERT_CATALOG",
                    source_record_id=rec.get("source_record_id") or rec.get("incident_id") or "INC_UNKNOWN",
                    class_label=GroundTruthClass.WILDFIRE,
                    latitude=rec_lat,
                    longitude=rec_lon,
                    event_start=t_start,
                    event_end=t_end,
                    confidence_level=conf,
                    provenance_url=rec.get("provenance_url"),
                    metadata={
                        "forest_beat": rec.get("forest_beat"),
                        "burned_area_ha": rec.get("burned_area_ha"),
                        "dataset_version": rec.get("dataset_version", "FSI_VAN_AGNI_V2.0"),
                        "doi": rec.get("doi", "10.5067/MODIS/MCD64A1.061")
                    }
                )
            )

        return evidence_list
