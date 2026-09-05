import os
import json
import datetime
import logging
from typing import List, Dict, Any
from app.services.ground_truth.base import BaseGroundTruthProvider, GroundTruthEvidence, GroundTruthClass, LabelConfidenceLevel
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.gas_flare_provider")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OFFICIAL_CATALOG_PATH = os.path.join(BASE_DIR, "data", "ground_truth_catalogs", "official", "vnf", "vnf_v30_india_gas_flares.json")
SAMPLE_CATALOG_PATH = os.path.join(BASE_DIR, "data", "ground_truth_catalogs", "vnf_gas_flares.json")

class GasFlareGroundTruthProvider(BaseGroundTruthProvider):
    """
    Authoritative provider for NOAA VIIRS Nightfire (VNF) Version 3.0 Global & India Gas Flaring Dataset.
    """
    def __init__(self, catalog_path: str = None):
        super().__init__("NOAA_VIIRS_NIGHTFIRE_V30_OFFICIAL")
        if catalog_path:
            self.catalog_path = catalog_path
        elif os.path.exists(OFFICIAL_CATALOG_PATH):
            self.catalog_path = OFFICIAL_CATALOG_PATH
        else:
            self.catalog_path = SAMPLE_CATALOG_PATH
            self.provider_name = "NOAA_VIIRS_NIGHTFIRE_SAMPLE_UNVERIFIED"

        self._cached_records: List[Dict[str, Any]] = self._load_catalog()

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.catalog_path):
            logger.warning(f"VNF Gas Flare catalog file not found at {self.catalog_path}")
            return []
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", data) if isinstance(data, dict) else data
                # Semantic filter: Explicitly ensure record category is GAS_FLARE
                return [r for r in records if isinstance(r, dict) and r.get("source_category", "GAS_FLARE") == "GAS_FLARE"]
        except Exception as e:
            logger.error(f"Failed to load VNF Gas Flare catalog: {e}")
            return []

    def fetch_evidence_near(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime.datetime,
        spatial_radius_m: float = 500.0,
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
                    source_type="SATELLITE_NIGHTTIME_PYROMETRY",
                    source_record_id=rec.get("source_record_id") or rec.get("incident_id") or "INC_UNKNOWN",
                    class_label=GroundTruthClass.GAS_FLARE,
                    latitude=rec_lat,
                    longitude=rec_lon,
                    event_start=t_start,
                    event_end=t_end,
                    confidence_level=conf,
                    provenance_url=rec.get("provenance_url"),
                    metadata={
                        "site_name": rec.get("site_name"),
                        "radiant_heat_mw": rec.get("radiant_heat_mw"),
                        "temperature_k": rec.get("temperature_k"),
                        "dataset_version": rec.get("dataset_version", "VNF_V3.0"),
                        "doi": rec.get("doi", "10.3334/ORNLDAAC/1874")
                    }
                )
            )

        return evidence_list
