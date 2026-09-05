import logging
import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.facility_baseline import FacilityNormalBaseline
from app.models.abnormal_event import AbnormalThermalEvent
from app.models.facility_association import ThermalFacilityAssociation
from app.services.landcover_service import LandCoverService
from app.services.persistence_service import PersistenceService
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.feature_engineering_service")

FEATURE_SCHEMA_VERSION = "4C.1"

class FeatureEngineeringService:
    """
    Service layer providing multi-modal feature engineering for thermal observations.
    Combines satellite thermal measurements, facility baseline anomalies, land-cover context,
    temporal persistence metrics, and spatial infrastructure proximity into a structured,
    ML-ready feature vector with explicit data lineage and schema versioning.
    """

    def __init__(self):
        self.landcover_service = LandCoverService()
        self.persistence_service = PersistenceService()

    def build_feature_vector(self, db: Session, event_id: int) -> Dict[str, Any]:
        """
        Constructs a complete multi-modal feature vector for a given thermal observation event.
        
        Returns:
            Dict containing event_id, feature_schema_version, features, feature_metadata, engineered_at.
        """
        obs = db.query(ThermalObservation).filter(ThermalObservation.id == event_id).first()
        if not obs:
            raise ValueError(f"Thermal observation with event_id={event_id} not found.")

        # --- Group A: Thermal Features ---
        frp_val = float(obs.frp) if obs.frp is not None else None
        bright_ti4_val = float(obs.bright_ti4) if obs.bright_ti4 is not None else None
        bright_ti5_val = float(obs.bright_ti5) if obs.bright_ti5 is not None else None
        scan_val = float(obs.scan) if obs.scan is not None else None
        track_val = float(obs.track) if obs.track is not None else None

        thermal_features = {
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "frp": frp_val,
            "brightness_temperature": bright_ti4_val,
            "background_temperature": bright_ti5_val,
            "confidence": obs.confidence or "UNKNOWN",
            "daynight": (obs.daynight or "UNKNOWN").upper(),
            "satellite": obs.satellite or "UNKNOWN",
            "instrument": obs.instrument or "UNKNOWN",
            "scan": scan_val,
            "track": track_val,
        }

        # --- Group B: Baseline & Anomaly Features ---
        assoc = db.query(ThermalFacilityAssociation).filter(
            ThermalFacilityAssociation.observation_id == obs.id
        ).first()

        baseline_p50 = None
        baseline_p95 = None
        baseline_p99 = None
        if assoc and assoc.facility_id:
            base_rec = db.query(FacilityNormalBaseline).filter(
                FacilityNormalBaseline.facility_id == assoc.facility_id
            ).first()
            if base_rec:
                baseline_p50 = float(base_rec.baseline_frp_p50)
                baseline_p95 = float(base_rec.baseline_frp_p95)
                baseline_p99 = float(base_rec.baseline_frp_p99)

        anom = db.query(AbnormalThermalEvent).filter(
            AbnormalThermalEvent.observation_id == obs.id
        ).first()

        frp_multiplier_ratio = float(anom.frp_multiplier_ratio) if anom else (round(frp_val / baseline_p95, 2) if (frp_val and baseline_p95) else 1.0)
        is_anomaly_candidate = bool(anom is not None or (frp_val and baseline_p95 and frp_val > baseline_p95))

        baseline_features = {
            "baseline_frp_p50": baseline_p50,
            "baseline_frp_p95": baseline_p95,
            "baseline_frp_p99": baseline_p99,
            "frp_multiplier_ratio": frp_multiplier_ratio,
            "is_anomaly_candidate": is_anomaly_candidate,
        }

        # --- Group C: Land Cover Features ---
        lc_info = self.landcover_service.get_land_cover(obs.latitude, obs.longitude)
        lc_code = lc_info.get("class_code")
        lc_class = lc_info.get("class_name", "UNKNOWN")

        landcover_features = {
            "land_cover_code": lc_code,
            "land_cover_class": lc_class,
            "is_built_up": bool(lc_code == 50),
            "is_cropland": bool(lc_code == 40),
            "is_tree_cover": bool(lc_code == 10),
            "is_grassland": bool(lc_code == 30),
            "is_shrubland": bool(lc_code == 20),
            "is_water": bool(lc_code == 80),
            "is_bare_land": bool(lc_code == 60),
        }

        # --- Group D: Temporal Persistence Features ---
        persist_info = self.persistence_service.get_persistence_features(
            db=db, event_id=obs.id, lookback_days=30, spatial_radius_m=100.0
        )

        persistence_features = {
            "recurrence_count": persist_info["recurrence_count"],
            "unique_detection_dates": persist_info["unique_detection_dates"],
            "unique_satellite_passes": persist_info["unique_satellite_passes"],
            "unique_satellites": persist_info["unique_satellites"],
            "temporal_span_days": persist_info["temporal_span_days"],
            "recurrence_frequency": persist_info["recurrence_frequency"],
            "mean_distance_m": persist_info["mean_distance_m"],
            "spatial_stddev_m": persist_info["spatial_stddev_m"],
            "mean_frp": persist_info["mean_frp"],
            "nighttime_ratio": persist_info["nighttime_ratio"],
        }

        # --- Group E: Industrial & Infrastructure Spatial Context ---
        facilities = db.query(IndustrialFacility).all()
        ind_facilities = [f for f in facilities if f.facility_type and f.facility_type.upper() not in ["POWER_PLANT", "SUBSTATION"]]
        energy_facilities = [f for f in facilities if f.facility_type and f.facility_type.upper() in ["POWER_PLANT", "SUBSTATION"]]

        # Industrial distances
        ind_distances = []
        nearest_ind_dist_m = None
        nearest_ind_type = "NONE"

        for f in ind_facilities:
            d_m = calculate_geodesic_distance_meters(obs.latitude, obs.longitude, f.latitude, f.longitude)
            ind_distances.append((d_m, f))

        if ind_distances:
            ind_distances.sort(key=lambda x: x[0])
            nearest_ind_dist_m = round(ind_distances[0][0], 2)
            nearest_ind_type = ind_distances[0][1].facility_type or "INDUSTRIAL"

        count_ind_1km = sum(1 for d, _ in ind_distances if d <= 1000.0)
        count_ind_5km = sum(1 for d, _ in ind_distances if d <= 5000.0)

        industrial_features = {
            "nearest_industrial_distance_m": nearest_ind_dist_m,
            "nearest_facility_type": nearest_ind_type,
            "count_industrial_facilities_1km": count_ind_1km,
            "count_industrial_facilities_5km": count_ind_5km,
        }

        # --- Group F: Energy Context Features ---
        energy_distances = []
        nearest_energy_dist_m = None

        for f in energy_facilities:
            d_m = calculate_geodesic_distance_meters(obs.latitude, obs.longitude, f.latitude, f.longitude)
            energy_distances.append((d_m, f))

        if energy_distances:
            energy_distances.sort(key=lambda x: x[0])
            nearest_energy_dist_m = round(energy_distances[0][0], 2)

        count_energy_1km = sum(1 for d, _ in energy_distances if d <= 1000.0)
        count_energy_5km = sum(1 for d, _ in energy_distances if d <= 5000.0)

        energy_features = {
            "nearest_energy_distance_m": nearest_energy_dist_m,
            "count_energy_entities_1km": count_energy_1km,
            "count_energy_entities_5km": count_energy_5km,
        }

        # Combine all features
        all_features = {}
        all_features.update(thermal_features)
        all_features.update(baseline_features)
        all_features.update(landcover_features)
        all_features.update(persistence_features)
        all_features.update(industrial_features)
        all_features.update(energy_features)

        # Feature Metadata & Lineage
        feature_metadata = {
            "frp": {"type": "NUMERIC", "source": "NASA_FIRMS", "missing_policy": "NULL"},
            "brightness_temperature": {"type": "NUMERIC", "source": "NASA_FIRMS_VIIRS_I4", "missing_policy": "NULL"},
            "confidence": {"type": "CATEGORICAL", "source": "NASA_FIRMS", "missing_policy": "UNKNOWN"},
            "daynight": {"type": "CATEGORICAL", "source": "NASA_FIRMS", "missing_policy": "UNKNOWN"},
            "land_cover_class": {"type": "CATEGORICAL", "source": "ESA_WORLDCOVER_10M", "missing_policy": "UNKNOWN"},
            "recurrence_count": {"type": "NUMERIC", "source": "PersistenceService_30d", "missing_policy": "0"},
            "nighttime_ratio": {"type": "NUMERIC", "source": "PersistenceService_30d", "missing_policy": "0.0"},
            "nearest_industrial_distance_m": {"type": "NUMERIC", "source": "PostGIS_IndustrialFacility", "missing_policy": "NULL"},
            "nearest_energy_distance_m": {"type": "NUMERIC", "source": "PostGIS_EnergyFacility", "missing_policy": "NULL"},
        }

        return {
            "event_id": event_id,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "features": all_features,
            "feature_metadata": feature_metadata,
            "engineered_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
