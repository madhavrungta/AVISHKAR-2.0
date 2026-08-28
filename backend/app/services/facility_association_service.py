import logging
import math
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import settings
from app.models.facility import Facility
from app.models.facility_observation import FacilityObservation
from app.models.thermal_observation import ThermalObservation

logger = logging.getLogger("firms_app.facility_association_service")

class FacilityAssociationService:
    """
    Geospatial matching service associating thermal observations to industrial facilities.
    """
    def __init__(self, radius_meters: float = None):
        self.radius = radius_meters or settings.ASSOCIATION_RADIUS_METERS

    def associate_observation(self, db: Session, obs: ThermalObservation) -> List[Tuple[Facility, float, str]]:
        """
        Finds and associates facilities within the configured radius of a thermal observation.
        Uses PostGIS if using PostgreSQL; falls back to geodesic Haversine distance in Python on SQLite.
        
        Returns:
            List of tuples: (Facility, distance_meters, association_method)
        """
        results = []
        is_postgres = db.bind.dialect.name == "postgresql"
        
        if is_postgres:
            try:
                obs_point = func.ST_SetSRID(func.ST_MakePoint(obs.longitude, obs.latitude), 4326)
                
                query = db.query(
                    Facility, 
                    func.ST_Distance(Facility.geometry.cast(func.geography), obs_point.cast(func.geography)).label("dist")
                ).filter(
                    func.ST_DWithin(Facility.geometry.cast(func.geography), obs_point.cast(func.geography), self.radius)
                ).order_by("dist")
                          
                candidates = query.all()
                for fac, dist in candidates:
                    results.append((fac, dist, "PostGIS ST_DWithin Proximity Query"))
            except Exception as e:
                logger.error(f"PostGIS association query failed, falling back to python math: {e}")
                is_postgres = False

        if not is_postgres:
            # SQLite / Python math fallback
            # Bounding box filter to optimize search (1 deg lat = ~111,111m)
            lat_delta = self.radius / 111111.0
            cos_lat = math.cos(math.radians(obs.latitude))
            lon_delta = self.radius / (111111.0 * cos_lat) if cos_lat != 0 else lat_delta
            
            bbox_query = db.query(Facility).filter(
                Facility.latitude >= obs.latitude - lat_delta,
                Facility.latitude <= obs.latitude + lat_delta,
                Facility.longitude >= obs.longitude - lon_delta,
                Facility.longitude <= obs.longitude + lon_delta
            )
            
            facilities = bbox_query.all()
            for fac in facilities:
                dist = self._haversine_distance(obs.latitude, obs.longitude, fac.latitude, fac.longitude)
                if dist <= self.radius:
                    results.append((fac, dist, "Python Geodesic Proximity Filter"))
            
            # Sort by distance
            results.sort(key=lambda x: x[1])

        # Write associations to database, preventing duplicates
        for fac, dist, method in results:
            existing = db.query(FacilityObservation).filter(
                FacilityObservation.facility_id == fac.id,
                FacilityObservation.observation_id == obs.id
            ).first()
            
            if not existing:
                assoc = FacilityObservation(
                    facility_id=fac.id,
                    observation_id=obs.id,
                    distance_m=round(dist, 2),
                    association_method=method
                )
                db.add(assoc)
                
        db.commit()
        return results

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula to compute distance in meters between two coordinates."""
        R = 6371000.0 # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(d_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c
