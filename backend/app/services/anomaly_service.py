import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.facility_association import ThermalFacilityAssociation
from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.facility_baseline import FacilityNormalBaseline
from app.models.abnormal_event import AbnormalThermalEvent
from app.schemas.abnormal_event import DetectAnomalyResponse, AnomalySummary

logger = logging.getLogger("firms_app.anomaly_service")

MANDATORY_CAUTION_LABEL = "Abnormal Thermal Output Candidate - Requires Multi-Pass / High-Res Optical Verification"

class AnomalyService:
    """
    Service layer evaluating thermal observations against facility normal baselines (P95 FRP upper bound)
    and flagging abnormal thermal output candidates.
    """

    @staticmethod
    def classify_severity(ratio: float) -> str:
        """Classifies anomaly severity based on FRP / P95 multiplier ratio."""
        if ratio > 2.5:
            return "CRITICAL_INDUSTRIAL_ANOMALY"
        elif ratio > 1.5:
            return "HIGH_ABNORMAL_SPIKE"
        else:
            return "MODERATE_ABNORMAL_SPIKE"

    def detect_abnormal_events(
        self, 
        db: Session, 
        recalculate_all: bool = False
    ) -> DetectAnomalyResponse:
        """Evaluates all associated thermal observations for abnormal FRP spikes exceeding P95 baselines."""
        if recalculate_all:
            db.query(AbnormalThermalEvent).delete()
            db.commit()

        associations = db.query(ThermalFacilityAssociation).all()
        total_assocs = len(associations)

        detected_cnt = 0
        mod_cnt = 0
        high_cnt = 0
        crit_cnt = 0

        now = datetime.datetime.utcnow()

        for assoc in associations:
            obs = db.query(ThermalObservation).filter(
                ThermalObservation.id == assoc.observation_id
            ).first()
            
            if not obs or obs.frp is None:
                continue

            baseline = db.query(FacilityNormalBaseline).filter(
                FacilityNormalBaseline.facility_id == assoc.facility_id
            ).first()

            p95_threshold = baseline.baseline_frp_p95 if baseline else 45.0
            obs_frp = float(obs.frp)

            if obs_frp > p95_threshold:
                ratio = round(obs_frp / p95_threshold, 2)
                severity = self.classify_severity(ratio)

                existing = db.query(AbnormalThermalEvent).filter(
                    AbnormalThermalEvent.observation_id == obs.id
                ).first()

                fac_name = assoc.facility.name if assoc.facility else "Industrial Facility"
                explanation = (
                    f"Observed FRP ({obs_frp} MW) at {fac_name} exceeds normal P95 baseline threshold ({p95_threshold} MW) "
                    f"by {ratio}x multiplier. Classified as {severity.replace('_', ' ')}. "
                    f"Scientific Caution: Persistent Industrial Heat != Confirmed Fire. Multi-pass optical verification mandatory."
                )

                if existing:
                    existing.facility_id = assoc.facility_id
                    existing.observed_frp = obs_frp
                    existing.baseline_p95_frp = p95_threshold
                    existing.frp_multiplier_ratio = ratio
                    existing.anomaly_severity = severity
                    existing.scientific_caution_label = MANDATORY_CAUTION_LABEL
                    existing.explanation_reason = explanation
                    existing.detected_at = now
                else:
                    event = AbnormalThermalEvent(
                        observation_id=obs.id,
                        facility_id=assoc.facility_id,
                        observed_frp=obs_frp,
                        baseline_p95_frp=p95_threshold,
                        frp_multiplier_ratio=ratio,
                        anomaly_severity=severity,
                        scientific_caution_label=MANDATORY_CAUTION_LABEL,
                        explanation_reason=explanation,
                        detected_at=now
                    )
                    db.add(event)

                detected_cnt += 1
                if severity == "CRITICAL_INDUSTRIAL_ANOMALY": crit_cnt += 1
                elif severity == "HIGH_ABNORMAL_SPIKE": high_cnt += 1
                else: mod_cnt += 1

        db.commit()
        logger.info(f"Abnormal event detection pipeline completed: {detected_cnt} anomalies flagged from {total_assocs} associations.")

        return DetectAnomalyResponse(
            status="success",
            total_evaluated=total_assocs,
            anomalies_detected=detected_cnt,
            moderate_spikes=mod_cnt,
            high_spikes=high_cnt,
            critical_anomalies=crit_cnt
        )
