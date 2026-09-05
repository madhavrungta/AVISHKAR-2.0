import math
import logging
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.thermal_observation import ThermalObservation, is_sqlite, HAS_GEOALCHEMY2
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.persistence_service")

class PersistenceService:
    """
    Service layer providing spatio-temporal persistence feature engineering for thermal observations.
    Calculates objective metrics (recurrence count, unique dates, spatial spread, FRP statistics,
    day/night ratios) over configurable lookback windows and spatial neighborhoods.
    """

    def __init__(self):
        pass

    @staticmethod
    def validate_parameters(lookback_days: int, spatial_radius_m: float) -> None:
        """Validates query parameters."""
        if lookback_days is None or lookback_days <= 0 or lookback_days > 365:
            raise ValueError(f"Invalid lookback_days: {lookback_days}. Must be between 1 and 365 days.")
        if spatial_radius_m is None or spatial_radius_m <= 0.0 or spatial_radius_m > 10000.0:
            raise ValueError(f"Invalid spatial_radius_m: {spatial_radius_m}. Must be between 1 and 10,000 meters.")

    def get_persistence_features(
        self,
        db: Session,
        event_id: int,
        lookback_days: int = 30,
        spatial_radius_m: float = 100.0
    ) -> Dict[str, Any]:
        """
        Calculates objective temporal persistence features around a target thermal observation.
        
        Returns:
            Dict containing calculated features (recurrence_count, unique_detection_dates, 
            spatial location stability metrics, FRP statistics, day/night ratio).
        """
        self.validate_parameters(lookback_days, spatial_radius_m)

        target_obs = db.query(ThermalObservation).filter(ThermalObservation.id == event_id).first()
        if not target_obs:
            raise ValueError(f"Thermal observation with event_id={event_id} not found.")

        target_time = target_obs.observation_timestamp or target_obs.ingestion_timestamp
        start_time = target_time - datetime.timedelta(days=lookback_days)

        # Retrieve candidate historical observations within the time window
        candidates = db.query(ThermalObservation).filter(
            ThermalObservation.observation_timestamp >= start_time,
            ThermalObservation.observation_timestamp <= target_time
        ).all()

        # Spatial neighborhood filtering with distance computation
        nearby_matches: List[Dict[str, Any]] = []

        for obs in candidates:
            dist_m = calculate_geodesic_distance_meters(
                target_obs.latitude, 
                target_obs.longitude, 
                obs.latitude, 
                obs.longitude
            )
            if dist_m <= spatial_radius_m:
                nearby_matches.append({
                    "observation": obs,
                    "distance_m": round(dist_m, 2)
                })

        recurrence_count = len(nearby_matches)

        if recurrence_count == 0:
            return self._empty_features_response(event_id, lookback_days, spatial_radius_m)

        # 1. Temporal & Date Metrics
        dates_set = set()
        passes_set = set()
        satellites_set = set()
        distances: List[float] = []
        frp_values: List[float] = []
        day_count = 0
        night_count = 0
        timestamps: List[datetime.datetime] = []

        for item in nearby_matches:
            obs: ThermalObservation = item["observation"]
            dist_m: float = item["distance_m"]
            distances.append(dist_m)

            if obs.acq_date:
                dates_set.add(obs.acq_date)
            elif obs.observation_timestamp:
                dates_set.add(obs.observation_timestamp.strftime("%Y-%m-%d"))

            if obs.acq_date and obs.acq_time:
                passes_set.add(f"{obs.satellite or 'UNKNOWN'}_{obs.acq_date}_{obs.acq_time}")
            elif obs.observation_timestamp:
                passes_set.add(f"{obs.satellite or 'UNKNOWN'}_{obs.observation_timestamp.isoformat()}")

            if obs.satellite:
                satellites_set.add(obs.satellite)

            if obs.frp is not None and obs.frp > 0.0:
                frp_values.append(float(obs.frp))

            dn = (obs.daynight or "").upper()
            if dn == "N":
                night_count += 1
            elif dn == "D":
                day_count += 1

            if obs.observation_timestamp:
                timestamps.append(obs.observation_timestamp)

        unique_detection_dates = len(dates_set)
        unique_satellite_passes = len(passes_set)
        unique_satellites = len(satellites_set)

        if len(timestamps) >= 2:
            timestamps.sort()
            span_seconds = (timestamps[-1] - timestamps[0]).total_seconds()
            temporal_span_days = round(span_seconds / 86400.0, 2)
        else:
            temporal_span_days = 0.0

        recurrence_frequency = round(unique_detection_dates / float(lookback_days), 4)

        # 2. Location Stability / Spatial Distance Metrics
        mean_dist = round(sum(distances) / float(recurrence_count), 2)
        sorted_dists = sorted(distances)
        median_dist = round(sorted_dists[len(sorted_dists) // 2], 2)
        max_dist = round(max(distances), 2)

        variance_dist = sum((d - mean_dist) ** 2 for d in distances) / float(recurrence_count)
        spatial_stddev_m = round(math.sqrt(variance_dist), 2)

        # 3. FRP Statistics
        if frp_values:
            mean_frp = round(sum(frp_values) / float(len(frp_values)), 2)
            sorted_frps = sorted(frp_values)
            median_frp = round(sorted_frps[len(sorted_frps) // 2], 2)
            max_frp = round(max(frp_values), 2)
            min_frp = round(min(frp_values), 2)
            variance_frp = sum((f - mean_frp) ** 2 for f in frp_values) / float(len(frp_values))
            frp_stddev = round(math.sqrt(variance_frp), 2)
        else:
            mean_frp, median_frp, max_frp, min_frp, frp_stddev = 0.0, 0.0, 0.0, 0.0, 0.0

        # 4. Day / Night Distribution
        nighttime_ratio = round(night_count / float(recurrence_count), 4)

        return {
            "event_id": event_id,
            "lookback_days": lookback_days,
            "spatial_radius_m": spatial_radius_m,
            "recurrence_count": recurrence_count,
            "unique_detection_dates": unique_detection_dates,
            "unique_satellite_passes": unique_satellite_passes,
            "unique_satellites": unique_satellites,
            "temporal_span_days": temporal_span_days,
            "recurrence_frequency": recurrence_frequency,
            "mean_distance_m": mean_dist,
            "median_distance_m": median_dist,
            "max_distance_m": max_dist,
            "spatial_stddev_m": spatial_stddev_m,
            "mean_frp": mean_frp,
            "median_frp": median_frp,
            "max_frp": max_frp,
            "min_frp": min_frp,
            "frp_stddev": frp_stddev,
            "daytime_detections": day_count,
            "nighttime_detections": night_count,
            "nighttime_ratio": nighttime_ratio,
            "calculated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }

    @staticmethod
    def _empty_features_response(
        event_id: int, 
        lookback_days: int, 
        spatial_radius_m: float
    ) -> Dict[str, Any]:
        """Returns default empty features when zero historical matches exist."""
        return {
            "event_id": event_id,
            "lookback_days": lookback_days,
            "spatial_radius_m": spatial_radius_m,
            "recurrence_count": 0,
            "unique_detection_dates": 0,
            "unique_satellite_passes": 0,
            "unique_satellites": 0,
            "temporal_span_days": 0.0,
            "recurrence_frequency": 0.0,
            "mean_distance_m": 0.0,
            "median_distance_m": 0.0,
            "max_distance_m": 0.0,
            "spatial_stddev_m": 0.0,
            "mean_frp": 0.0,
            "median_frp": 0.0,
            "max_frp": 0.0,
            "min_frp": 0.0,
            "frp_stddev": 0.0,
            "daytime_detections": 0,
            "nighttime_detections": 0,
            "nighttime_ratio": 0.0,
            "calculated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
