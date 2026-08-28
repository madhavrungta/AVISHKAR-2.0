import json
import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.thermal_observation import ThermalObservation
from app.models.facility_association import ThermalFacilityAssociation
from app.models.industrial_facility import IndustrialFacility
from app.models.abnormal_event import AbnormalThermalEvent
from app.models.risk_score import VerificationRiskScore
from app.schemas.risk_score import EvaluateRiskResponse, RiskSummary

logger = logging.getLogger("firms_app.risk_service")

FACILITY_SENSITIVITY_SCORES = {
    "refinery": 95.0,
    "chemical": 90.0,
    "power_plant": 80.0,
    "steel_works": 75.0,
    "industrial": 50.0,
    "none": 20.0
}

class RiskService:
    """
    Service layer computing 4-factor Multi-Criteria Risk Scores (0-100) 
    and integrating Sentinel-2 / Landsat-8 optical verification confidence proxies.
    """

    @staticmethod
    def classify_risk_tier(score: float) -> str:
        """Classifies risk level based on composite score (0-100)."""
        if score > 85.0:
            return "CRITICAL_VERIFIED_RISK"
        elif score > 60.0:
            return "HIGH_RISK"
        elif score > 30.0:
            return "MEDIUM_RISK"
        else:
            return "LOW_RISK"

    def evaluate_risk_scores(
        self, 
        db: Session, 
        recalculate_all: bool = False
    ) -> EvaluateRiskResponse:
        """Evaluates multi-modal risk scores for all thermal observations."""
        if recalculate_all:
            db.query(VerificationRiskScore).delete()
            db.commit()

        observations = db.query(ThermalObservation).all()
        total_obs = len(observations)

        crit_cnt = 0
        high_cnt = 0
        med_cnt = 0
        low_cnt = 0
        evaluated_cnt = 0

        now = datetime.datetime.utcnow()

        for obs in observations:
            existing = db.query(VerificationRiskScore).filter(
                VerificationRiskScore.observation_id == obs.id
            ).first()

            if existing and not recalculate_all:
                if existing.risk_level == "CRITICAL_VERIFIED_RISK": crit_cnt += 1
                elif existing.risk_level == "HIGH_RISK": high_cnt += 1
                elif existing.risk_level == "MEDIUM_RISK": med_cnt += 1
                else: low_cnt += 1
                continue

            # Fetch spatial association
            assoc = db.query(ThermalFacilityAssociation).filter(
                ThermalFacilityAssociation.observation_id == obs.id
            ).first()

            # 1. Spatial Proximity Score (S_prox)
            if assoc:
                if assoc.association_type == "DIRECT_MATCH": s_prox = 100.0
                elif assoc.association_type == "PROXIMATE_MATCH": s_prox = 75.0
                elif assoc.association_type == "VICINITY_MATCH": s_prox = 50.0
                else: s_prox = 20.0
            else:
                s_prox = 10.0

            # 2. FRP Anomaly Multiplier Score (S_frp)
            anom = db.query(AbnormalThermalEvent).filter(
                AbnormalThermalEvent.observation_id == obs.id
            ).first()

            if anom:
                s_frp = min(100.0, round(40.0 * anom.frp_multiplier_ratio, 2))
            else:
                obs_frp = float(obs.frp) if obs.frp is not None else 10.0
                s_frp = min(100.0, round(2.0 * obs_frp, 2))

            # 3. Facility Sensitivity Score (S_sens)
            fac_type = assoc.facility.facility_type.lower() if assoc and assoc.facility else "none"
            s_sens = FACILITY_SENSITIVITY_SCORES.get(fac_type, FACILITY_SENSITIVITY_SCORES["industrial"])

            # 4. Optical Verification Proxy Confidence (S_opt)
            obs_frp = float(obs.frp) if obs.frp is not None else 10.0
            if obs_frp >= 50.0 and fac_type in ["refinery", "power_plant", "chemical"]:
                s_opt = 0.85
            elif obs_frp >= 20.0:
                s_opt = 0.65
            else:
                s_opt = 0.45

            # Composite Risk Score Calculation
            composite = round(0.25 * s_prox + 0.30 * s_frp + 0.25 * s_sens + 0.20 * (s_opt * 100.0), 2)
            risk_level = self.classify_risk_tier(composite)

            breakdown = {
                "spatial_proximity_score": s_prox,
                "frp_multiplier_score": s_frp,
                "facility_sensitivity_score": s_sens,
                "optical_confidence_proxy": s_opt,
                "weights": {"proximity": 0.25, "frp": 0.30, "sensitivity": 0.25, "optical": 0.20}
            }

            fac_id = assoc.facility_id if assoc else None

            if existing:
                existing.facility_id = fac_id
                existing.composite_risk_score = composite
                existing.risk_level = risk_level
                existing.spatial_proximity_score = s_prox
                existing.frp_multiplier_score = s_frp
                existing.facility_sensitivity_score = s_sens
                existing.optical_verification_confidence = s_opt
                existing.risk_breakdown_json = json.dumps(breakdown)
                existing.evaluated_at = now
            else:
                risk_rec = VerificationRiskScore(
                    observation_id=obs.id,
                    facility_id=fac_id,
                    composite_risk_score=composite,
                    risk_level=risk_level,
                    spatial_proximity_score=s_prox,
                    frp_multiplier_score=s_frp,
                    facility_sensitivity_score=s_sens,
                    optical_verification_confidence=s_opt,
                    verification_source="Sentinel-2 MSI / Landsat-8 OLI Optical Proxy",
                    risk_breakdown_json=json.dumps(breakdown),
                    evaluated_at=now
                )
                db.add(risk_rec)

            evaluated_cnt += 1
            if risk_level == "CRITICAL_VERIFIED_RISK": crit_cnt += 1
            elif risk_level == "HIGH_RISK": high_cnt += 1
            elif risk_level == "MEDIUM_RISK": med_cnt += 1
            else: low_cnt += 1

        db.commit()
        logger.info(f"Multi-modal risk evaluation completed: {evaluated_cnt} risk scores evaluated.")

        return EvaluateRiskResponse(
            status="success",
            total_evaluated=evaluated_cnt,
            critical_verified=crit_cnt,
            high_risk=high_cnt,
            medium_risk=med_cnt,
            low_risk=low_cnt
        )
