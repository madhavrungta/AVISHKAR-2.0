import json
import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.thermal_observation import ThermalObservation
from app.models.facility_association import ThermalFacilityAssociation
from app.models.thermal_classification import ThermalClassification
from app.schemas.thermal_classification import RunClassificationResponse, ClassificationSummary
from app.ml.classifier import SourceClassifier

logger = logging.getLogger("firms_app.classification_service")

class ClassificationService:
    """
    Service layer executing source classification pipeline over thermal observations.
    """

    def __init__(self):
        self.classifier = SourceClassifier()

    def run_classification_pipeline(
        self, 
        db: Session, 
        recalculate_all: bool = False
    ) -> RunClassificationResponse:
        """Runs candidate source classification engine for all thermal observations."""
        if recalculate_all:
            db.query(ThermalClassification).delete()
            db.commit()

        observations = db.query(ThermalObservation).all()
        total_obs = len(observations)
        
        created_cnt = 0
        ind_cnt = 0
        nat_cnt = 0
        agr_cnt = 0
        unk_cnt = 0

        if not observations:
            return RunClassificationResponse(
                status="success",
                total_processed=0,
                classifications_created=0,
                industrial_candidates=0,
                natural_forest_candidates=0,
                agricultural_candidates=0,
                other_unknown=0
            )

        now = datetime.datetime.utcnow()

        for obs in observations:
            existing = db.query(ThermalClassification).filter(
                ThermalClassification.observation_id == obs.id
            ).first()

            if existing and not recalculate_all:
                if existing.predicted_class == "INDUSTRIAL_CANDIDATE": ind_cnt += 1
                elif existing.predicted_class == "NATURAL_FOREST_CANDIDATE": nat_cnt += 1
                elif existing.predicted_class == "AGRICULTURAL_CANDIDATE": agr_cnt += 1
                else: unk_cnt += 1
                continue

            # Fetch spatial association if available
            assoc = db.query(ThermalFacilityAssociation).filter(
                ThermalFacilityAssociation.observation_id == obs.id
            ).first()

            dist = assoc.distance_meters if assoc else 99999.0
            fac_type = assoc.facility.facility_type if assoc and assoc.facility else "none"

            feature_vector = {
                "distance_meters": dist,
                "facility_type": fac_type,
                "frp": obs.frp or 0.0,
                "bright_ti4": obs.bright_ti4,
                "bright_ti5": obs.bright_ti5,
                "daynight": obs.daynight or "D",
                "scan": obs.scan or 0.4
            }

            pred_class, conf, reason = self.classifier.predict(feature_vector)

            if existing:
                existing.predicted_class = pred_class
                existing.confidence_score = conf
                existing.classification_reason = reason
                existing.feature_vector_json = json.dumps(feature_vector)
            else:
                clf = ThermalClassification(
                    observation_id=obs.id,
                    predicted_class=pred_class,
                    confidence_score=conf,
                    classification_reason=reason,
                    feature_vector_json=json.dumps(feature_vector),
                    created_at=now
                )
                db.add(clf)

            created_cnt += 1
            if pred_class == "INDUSTRIAL_CANDIDATE": ind_cnt += 1
            elif pred_class == "NATURAL_FOREST_CANDIDATE": nat_cnt += 1
            elif pred_class == "AGRICULTURAL_CANDIDATE": agr_cnt += 1
            else: unk_cnt += 1

        db.commit()
        logger.info(f"Classification pipeline completed: {created_cnt} records classified for {total_obs} observations.")

        return RunClassificationResponse(
            status="success",
            total_processed=total_obs,
            classifications_created=created_cnt,
            industrial_candidates=ind_cnt,
            natural_forest_candidates=nat_cnt,
            agricultural_candidates=agr_cnt,
            other_unknown=unk_cnt
        )
