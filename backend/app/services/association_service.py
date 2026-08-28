import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.facility_association import ThermalFacilityAssociation
from app.schemas.facility_association import RunAssociationResponse, AssociationSummary
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.association_service")

class AssociationService:
    """
    Service layer for matching thermal anomaly observations to nearby industrial facilities.
    """

    @staticmethod
    def classify_association(distance_meters: float) -> str:
        """Classifies spatial association into standardized confidence tiers."""
        if distance_meters <= 100.0:
            return "DIRECT_MATCH"
        elif distance_meters <= 1000.0:
            return "PROXIMATE_MATCH"
        elif distance_meters <= 3000.0:
            return "VICINITY_MATCH"
        else:
            return "UNASSOCIATED"

    def run_association_pipeline(
        self, 
        db: Session, 
        max_distance_meters: float = 3000.0,
        recalculate_all: bool = False
    ) -> RunAssociationResponse:
        """
        Executes spatial proximity matching between all thermal observations and industrial facilities.
        """
        if recalculate_all:
            db.query(ThermalFacilityAssociation).delete()
            db.commit()

        observations = db.query(ThermalObservation).all()
        facilities = db.query(IndustrialFacility).all()

        total_obs = len(observations)
        associations_created = 0
        direct_cnt = 0
        proximate_cnt = 0
        vicinity_cnt = 0
        unassociated_cnt = 0

        if not observations or not facilities:
            return RunAssociationResponse(
                status="success",
                total_observations_processed=total_obs,
                associations_created=0,
                direct_matches=0,
                proximate_matches=0,
                vicinity_matches=0,
                unassociated=total_obs
            )

        now = datetime.datetime.utcnow()

        for obs in observations:
            # Check existing association
            existing = db.query(ThermalFacilityAssociation).filter(
                ThermalFacilityAssociation.observation_id == obs.id
            ).first()

            if existing and not recalculate_all:
                if existing.association_type == "DIRECT_MATCH": direct_cnt += 1
                elif existing.association_type == "PROXIMATE_MATCH": proximate_cnt += 1
                elif existing.association_type == "VICINITY_MATCH": vicinity_cnt += 1
                else: unassociated_cnt += 1
                continue

            # Find nearest facility
            best_facility = None
            min_dist = float("inf")

            for fac in facilities:
                dist = calculate_geodesic_distance_meters(
                    obs.latitude, obs.longitude, fac.latitude, fac.longitude
                )
                if dist < min_dist:
                    min_dist = dist
                    best_facility = fac

            if best_facility and min_dist <= max_distance_meters:
                assoc_type = self.classify_association(min_dist)

                if existing:
                    existing.facility_id = best_facility.id
                    existing.distance_meters = round(min_dist, 2)
                    existing.association_type = assoc_type
                else:
                    assoc = ThermalFacilityAssociation(
                        observation_id=obs.id,
                        facility_id=best_facility.id,
                        distance_meters=round(min_dist, 2),
                        association_type=assoc_type,
                        created_at=now
                    )
                    db.add(assoc)

                associations_created += 1

                if assoc_type == "DIRECT_MATCH": direct_cnt += 1
                elif assoc_type == "PROXIMATE_MATCH": proximate_cnt += 1
                elif assoc_type == "VICINITY_MATCH": vicinity_cnt += 1
            else:
                unassociated_cnt += 1

        db.commit()
        logger.info(f"Association job completed: {associations_created} created/updated for {total_obs} observations.")

        return RunAssociationResponse(
            status="success",
            total_observations_processed=total_obs,
            associations_created=associations_created,
            direct_matches=direct_cnt,
            proximate_matches=proximate_cnt,
            vicinity_matches=vicinity_cnt,
            unassociated=unassociated_cnt
        )
