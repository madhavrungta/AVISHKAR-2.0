import datetime
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.thermal_observation import ThermalObservation
from app.models.ground_truth import GroundTruthLabel
from app.services.ground_truth.base import (
    GroundTruthEvidence, GroundTruthClass, LabelConfidenceLevel, BaseGroundTruthProvider
)
from app.services.ground_truth.providers import (
    WildfireGroundTruthProvider,
    GasFlareGroundTruthProvider,
    AgriculturalBurningGroundTruthProvider,
    MiningActivityGroundTruthProvider,
    IndustrialFireGroundTruthProvider
)
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.ground_truth_matcher")

class GroundTruthMatcher:
    """
    Deterministic spatial-temporal matching engine that queries external ground-truth dataset providers,
    evaluates spatial and temporal tolerances, resolves multi-source evidence conflicts, and assesses
    training eligibility for supervised ML training.
    """

    def __init__(self):
        self.providers: List[BaseGroundTruthProvider] = [
            WildfireGroundTruthProvider(),
            GasFlareGroundTruthProvider(),
            AgriculturalBurningGroundTruthProvider(),
            MiningActivityGroundTruthProvider(),
            IndustrialFireGroundTruthProvider()
        ]

    def evaluate_observation_label(
        self,
        db: Session,
        event_id: int,
        save_to_db: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates an observation against independent external ground-truth evidence sources.
        """
        obs = db.query(ThermalObservation).filter(ThermalObservation.id == event_id).first()
        if not obs:
            raise ValueError(f"Thermal observation with event_id={event_id} not found.")

        obs_time = obs.observation_timestamp or datetime.datetime.utcnow()

        collected_evidence: List[Dict[str, Any]] = []

        for provider in self.providers:
            try:
                ev_list = provider.fetch_evidence_near(
                    latitude=obs.latitude,
                    longitude=obs.longitude,
                    timestamp=obs_time
                )
                for ev in ev_list:
                    dist_m = round(calculate_geodesic_distance_meters(
                        obs.latitude, obs.longitude, ev.latitude, ev.longitude
                    ), 2)
                    # Calculate accurate temporal delta to the active event interval
                    if ev.event_end and (ev.event_start <= obs_time <= ev.event_end):
                        delta_h = 0.0
                    elif ev.event_end and obs_time > ev.event_end:
                        delta_h = round((obs_time - ev.event_end).total_seconds() / 3600.0, 2)
                    elif obs_time < ev.event_start:
                        delta_h = round((ev.event_start - obs_time).total_seconds() / 3600.0, 2)
                    else:
                        delta_h = round(abs((obs_time - ev.event_start).total_seconds()) / 3600.0, 2)

                    collected_evidence.append({
                        "evidence": ev,
                        "distance_m": dist_m,
                        "time_delta_h": delta_h
                    })
            except Exception as e:
                logger.error(f"Provider {provider.provider_name} failed: {e}")

        # Check existing persisted ground truth label in DB
        existing_rec = db.query(GroundTruthLabel).filter(GroundTruthLabel.observation_id == obs.id).first()
        if existing_rec and not save_to_db:
            return {
                "event_id": obs.id,
                "label": existing_rec.label,
                "label_confidence": existing_rec.label_confidence,
                "label_source": existing_rec.label_source,
                "label_source_id": existing_rec.label_source_id,
                "label_method": existing_rec.label_method,
                "matched_distance_m": existing_rec.matched_distance_m,
                "matched_time_delta_hours": existing_rec.matched_time_delta_hours,
                "training_eligible": existing_rec.training_eligible,
                "evidence_count": len(collected_evidence),
                "evidence": [self._format_evidence(item) for item in collected_evidence],
                "evaluated_at": datetime.datetime.utcnow().isoformat() + "Z"
            }

        # Conflict resolution logic
        if len(collected_evidence) == 0:
            final_label = GroundTruthClass.UNKNOWN.value
            confidence = LabelConfidenceLevel.UNKNOWN.value
            source_name = "NONE"
            source_id = None
            dist_m = None
            delta_h = None
            training_eligible = False
        else:
            # Check for multi-class conflicting evidence
            unique_classes = set(item["evidence"].class_label for item in collected_evidence)
            if len(unique_classes) > 1:
                logger.warning(f"Conflicting ground-truth evidence for event #{obs.id}: {unique_classes}")
                final_label = GroundTruthClass.UNKNOWN.value
                confidence = LabelConfidenceLevel.UNKNOWN.value
                source_name = "CONFLICTING_SOURCES"
                source_id = None
                dist_m = None
                delta_h = None
                training_eligible = False
            else:
                top_match = sorted(collected_evidence, key=lambda x: (x["distance_m"], x["time_delta_h"]))[0]
                ev: GroundTruthEvidence = top_match["evidence"]
                final_label = ev.class_label.value
                confidence = ev.confidence_level.value
                source_name = ev.source_name
                source_id = ev.source_record_id
                dist_m = top_match["distance_m"]
                delta_h = top_match["time_delta_h"]
                
                # Strict training eligibility:
                # 1. High or Medium independent evidence confidence
                # 2. Strict temporal delta <= 24.0 hours
                training_eligible = (
                    confidence in [LabelConfidenceLevel.HIGH.value, LabelConfidenceLevel.MEDIUM.value]
                    and (delta_h is not None and delta_h <= 24.0)
                )

        if save_to_db:
            if existing_rec:
                existing_rec.label = final_label
                existing_rec.label_confidence = confidence
                existing_rec.label_source = source_name
                existing_rec.label_source_id = source_id
                existing_rec.matched_distance_m = dist_m
                existing_rec.matched_time_delta_hours = delta_h
                existing_rec.training_eligible = training_eligible
            else:
                gt_rec = GroundTruthLabel(
                    observation_id=obs.id,
                    label=final_label,
                    label_confidence=confidence,
                    label_source=source_name,
                    label_source_id=source_id,
                    label_method="EXTERNAL_GROUND_TRUTH_MATCH",
                    matched_distance_m=dist_m,
                    matched_time_delta_hours=delta_h,
                    training_eligible=training_eligible
                )
                db.add(gt_rec)
            db.commit()

        return {
            "event_id": obs.id,
            "label": final_label,
            "label_confidence": confidence,
            "label_source": source_name,
            "label_source_id": source_id,
            "label_method": "EXTERNAL_GROUND_TRUTH_MATCH",
            "matched_distance_m": dist_m,
            "matched_time_delta_hours": delta_h,
            "training_eligible": training_eligible,
            "evidence_count": len(collected_evidence),
            "evidence": [self._format_evidence(item) for item in collected_evidence],
            "evaluated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }

    @staticmethod
    def _format_evidence(item: Dict[str, Any]) -> Dict[str, Any]:
        ev: GroundTruthEvidence = item["evidence"]
        return {
            "source_name": ev.source_name,
            "source_record_id": ev.source_record_id,
            "class_label": ev.class_label.value,
            "confidence_level": ev.confidence_level.value,
            "matched_distance_m": item["distance_m"],
            "matched_time_delta_hours": item["time_delta_h"],
            "provenance_url": ev.provenance_url
        }
