"""
AVISHKAR 2.0 — Phase 4F-13: Continuous Probabilistic ML Shadow Inference Service

Responsibilities:
1. Loads and validates experimental Gradient Boosting Pipeline artifact from Phase 4F-11A/4F-13.
2. Respects feature flag ML_CLASSIFIER_SHADOW_MODE (default: False).
3. Executes strictly in non-blocking shadow mode (zero authority over Risk Engine or final risk scores).
4. Enforces strict 17-field feature leakage prevention and 18-feature schema validation.
5. Emits continuous calibrated class probabilities via model.predict_proba() for the 5 target classes:
   - AGRICULTURAL_BURNING
   - GAS_FLARE
   - INDUSTRIAL_FIRE
   - MINING_ACTIVITY
   - WILDFIRE
6. Stores shadow predictions idempotently in MLShadowPrediction database table.
7. Computes operational performance metrics: average & p95 latency, continuous confidence distributions,
   and semantic ML vs Risk comparison.
"""

import os
import time
import json
import logging
import datetime
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.models.thermal_observation import ThermalObservation
from app.models.risk_score import VerificationRiskScore
from app.models.facility_association import ThermalFacilityAssociation
from app.models.industrial_facility import IndustrialFacility
from app.models.shadow_prediction import MLShadowPrediction
from app.services.landcover_service import LandCoverService
from app.geospatial.utils import calculate_geodesic_distance_meters
from app.ml.gradient_boosting import (
    PurePythonMLPipeline, PurePythonStandardScaler,
    PurePythonGradientBoostingClassifier, FEATURE_NAMES_18, TARGET_CLASSES
)

logger = logging.getLogger("firms_app.ml.shadow_inference")

MODEL_VERSION = "4F.13_GB_V1"
FEATURE_SCHEMA_VERSION = "4F.13"
DEFAULT_ARTIFACT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ml_artifacts", "phase_4f11a", "model_artifact_phase4f11a.json")
)
DEFAULT_WEIGHTS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ml_artifacts", "phase_4f11a", "model_pipeline_weights.json")
)

FORBIDDEN_LEAKAGE_KEYS = {
    "target_label", "label", "ground_truth", "label_confidence", "confidence",
    "label_source", "label_source_id", "training_eligible", "matched_distance_m",
    "matched_time_delta_hours", "physical_event_cluster_id", "provenance_url",
    "acq_date", "acq_time", "satellite", "instrument", "source"
}


class MLShadowInferenceService:
    """
    Continuous Probabilistic Shadow Inference Engine for supervised thermal source classification.
    Executes actual frozen GradientBoostingClassifier via predict_proba() without heuristic routing.
    Runs strictly in shadow mode, guaranteeing zero interference with the authoritative Risk Engine.
    """

    def __init__(
        self,
        artifact_path: str = DEFAULT_ARTIFACT_PATH,
        weights_path: str = DEFAULT_WEIGHTS_PATH
    ):
        self.artifact_path = artifact_path
        self.weights_path = weights_path
        self.artifact_metadata: Dict[str, Any] = {}
        self.pipeline: Optional[PurePythonMLPipeline] = None
        self.landcover_service = LandCoverService()
        self.is_ready = False
        self._load_pipeline()

    def _load_pipeline(self) -> bool:
        """
        Loads and validates the experimental Gradient Boosting pipeline artifact.
        """
        try:
            if not os.path.exists(self.artifact_path):
                logger.warning(f"Shadow ML metadata artifact not found at {self.artifact_path}. Shadow inference disabled.")
                self.is_ready = False
                return False

            with open(self.artifact_path, "r", encoding="utf-8") as f:
                self.artifact_metadata = json.load(f)

            if not os.path.exists(self.weights_path):
                logger.warning(f"Pipeline weights not found at {self.weights_path}. Shadow inference disabled.")
                self.is_ready = False
                return False

            self.pipeline = PurePythonMLPipeline.load(self.weights_path)
            self.is_ready = True
            logger.info(
                f"Loaded Shadow ML Pipeline: {len(self.pipeline.classes_)} classes, "
                f"{len(self.pipeline.feature_names_in_)} features (v{MODEL_VERSION})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load shadow model pipeline: {e}")
            self.is_ready = False
            return False

    def validate_and_filter_features(self, raw_features: Dict[str, Any]) -> Tuple[Dict[str, float], List[str]]:
        """
        Validates the input feature schema and strictly strips any forbidden target or provenance keys.
        """
        violations = []
        filtered_features = {}

        for k, v in raw_features.items():
            if k in FORBIDDEN_LEAKAGE_KEYS:
                violations.append(k)
                continue
            if isinstance(v, (int, float, bool)):
                filtered_features[k] = float(v)

        return filtered_features, violations

    def extract_observation_features(self, obs: ThermalObservation, db: Optional[Session] = None) -> Tuple[Dict[str, float], bool, str]:
        """
        Extracts clean numeric 18-feature vector from a ThermalObservation instance.
        Validates 18-feature count, schema ordering, and zero NaN/Inf/leakage.
        """
        dist_ind_m = 99999.0
        dist_energy_m = 99999.0

        if db:
            facilities = db.query(IndustrialFacility).all()
            for f in facilities:
                if f.latitude and f.longitude:
                    d = calculate_geodesic_distance_meters(obs.latitude, obs.longitude, f.latitude, f.longitude)
                    ftype = (f.facility_type or "").upper()
                    if ftype in ["POWER_PLANT", "SUBSTATION", "ENERGY"]:
                        if d < dist_energy_m:
                            dist_energy_m = d
                    else:
                        if d < dist_ind_m:
                            dist_ind_m = d

        frp = float(obs.frp) if obs.frp is not None else 10.0
        ti4 = float(obs.bright_ti4) if obs.bright_ti4 is not None else 320.0
        scan = float(obs.scan) if obs.scan is not None else 0.5

        lc_info = self.landcover_service.get_land_cover(obs.latitude, obs.longitude)
        lc_code = float(lc_info.get("class_code", 10))

        persistence = 1.0 if dist_ind_m > 3000.0 else 6.0

        raw_dict = {
            "p50_ratio": 1.0,
            "p95_ratio": 1.0,
            "p99_ratio": 1.0,
            "frp_zscore": round((frp - 20.0) / 15.0, 4),
            "bright_ti4_zscore": round((ti4 - 325.0) / 18.0, 4),
            "worldcover_class": lc_code,
            "persistence_3d_count": persistence,
            "dist_to_industrial_m": round(dist_ind_m, 2),
            "dist_to_energy_m": round(dist_energy_m, 2),
            "dist_to_healthcare_m": 99999.0,
            "dist_to_transport_m": 99999.0,
            "dist_to_railway_m": 99999.0,
            "dist_to_highway_m": 99999.0,
            "dist_to_airport_m": 99999.0,
            "dist_to_port_m": 99999.0,
            "frp": frp,
            "brightness": ti4,
            "scan": scan
        }

        clean_features, violations = self.validate_and_filter_features(raw_dict)
        if violations:
            return {}, False, f"Leakage violation: {violations}"

        if len(clean_features) != 18:
            return {}, False, f"Invalid feature count: expected 18, got {len(clean_features)}"

        for fn in FEATURE_NAMES_18:
            if fn not in clean_features:
                return {}, False, f"Missing required feature: {fn}"
            val = clean_features[fn]
            if np.isnan(val) or np.isinf(val):
                return {}, False, f"Invalid numeric value in feature {fn}: {val}"

        return clean_features, True, "OK"

    def predict_probabilities(self, features: Dict[str, float]) -> Tuple[str, Dict[str, float], float]:
        """
        Continuous probabilistic inference using frozen Gradient Boosting Pipeline.
        Obtains class ordering dynamically from pipeline.classes_.
        Probabilities strictly sum to 1.0 via continuous softmax.
        Predicted class is argmax(probs), confidence is max(probs).
        """
        if not self.is_ready or self.pipeline is None:
            raise RuntimeError("ML Shadow Inference Pipeline is not initialized.")

        ordered_vector = [features[fn] for fn in self.pipeline.feature_names_in_]
        probs_arr = self.pipeline.predict_proba([ordered_vector])[0]
        
        class_names = self.pipeline.classes_
        probs = {}
        for cls_name, p_val in zip(class_names, probs_arr):
            probs[cls_name] = round(float(p_val), 4)

        total_p = sum(probs.values())
        if total_p > 0 and abs(total_p - 1.0) > 1e-6:
            probs = {k: round(v / total_p, 4) for k, v in probs.items()}
            diff = round(1.0 - sum(probs.values()), 4)
            best_k = max(probs, key=probs.get)
            probs[best_k] = round(probs[best_k] + diff, 4)

        pred_class = max(probs, key=probs.get)
        max_p = probs[pred_class]

        return pred_class, probs, max_p

    def infer_observation(
        self,
        db: Session,
        event_id: int,
        force_run: bool = False,
        commit: bool = True
    ) -> Dict[str, Any]:
        """
        Executes non-blocking shadow inference on a single thermal observation.
        Persists results idempotently to MLShadowPrediction.
        """
        start_time = time.perf_counter()

        # Check feature flag (Safe Default = False)
        is_enabled = settings.ML_CLASSIFIER_SHADOW_MODE or force_run
        if not is_enabled:
            return {
                "event_id": event_id,
                "model_version": MODEL_VERSION,
                "predicted_class": "SHADOW_DISABLED",
                "probabilities": {cls: 0.0 for cls in TARGET_CLASSES},
                "max_probability": 0.0,
                "existing_risk_level": None,
                "existing_risk_score": None,
                "prediction_status": "SKIPPED_DISABLED",
                "inference_latency_ms": 0.0,
                "feature_schema_version": FEATURE_SCHEMA_VERSION,
                "inference_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "message": "ML_CLASSIFIER_SHADOW_MODE is disabled."
            }

        try:
            obs = db.query(ThermalObservation).filter(ThermalObservation.id == event_id).first()
            if not obs:
                return {
                    "event_id": event_id,
                    "model_version": MODEL_VERSION,
                    "predicted_class": "UNKNOWN",
                    "probabilities": {cls: 0.0 for cls in TARGET_CLASSES},
                    "max_probability": 0.0,
                    "prediction_status": "FAILED",
                    "error": f"Thermal observation with event_id={event_id} not found."
                }

            # Fetch existing authoritative risk score for comparison (Read-Only)
            risk_rec = db.query(VerificationRiskScore).filter(
                VerificationRiskScore.observation_id == event_id
            ).first()
            existing_risk_level = risk_rec.risk_level if risk_rec else "UNASSESSED"
            existing_risk_score = risk_rec.composite_risk_score if risk_rec else None

            # Extract clean 18 features with schema validation
            clean_features, is_valid, err_msg = self.extract_observation_features(obs, db=db)
            if not is_valid:
                return {
                    "event_id": event_id,
                    "model_version": MODEL_VERSION,
                    "predicted_class": "ERROR",
                    "probabilities": {cls: 0.0 for cls in TARGET_CLASSES},
                    "max_probability": 0.0,
                    "prediction_status": "FAILED",
                    "error": f"Schema validation failed: {err_msg}",
                    "inference_latency_ms": round((time.perf_counter() - start_time) * 1000.0, 3)
                }

            # Predict
            pred_class, probs, max_p = self.predict_probabilities(clean_features)
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

            now = datetime.datetime.utcnow()

            # Idempotent database persistence
            existing_pred = db.query(MLShadowPrediction).filter(
                MLShadowPrediction.event_id == event_id,
                MLShadowPrediction.model_version == MODEL_VERSION
            ).first()

            if existing_pred:
                existing_pred.predicted_class = pred_class
                existing_pred.probability_industrial_fire = probs["INDUSTRIAL_FIRE"]
                existing_pred.probability_gas_flare = probs["GAS_FLARE"]
                existing_pred.probability_agricultural_burning = probs["AGRICULTURAL_BURNING"]
                existing_pred.probability_mining_activity = probs["MINING_ACTIVITY"]
                existing_pred.probability_wildfire = probs["WILDFIRE"]
                existing_pred.max_probability = max_p
                existing_pred.existing_risk_level = existing_risk_level
                existing_pred.existing_risk_score = existing_risk_score
                existing_pred.inference_latency_ms = latency_ms
                existing_pred.inference_timestamp = now
                existing_pred.prediction_status = "SUCCESS"
            else:
                new_pred = MLShadowPrediction(
                    event_id=event_id,
                    model_version=MODEL_VERSION,
                    predicted_class=pred_class,
                    probability_industrial_fire=probs["INDUSTRIAL_FIRE"],
                    probability_gas_flare=probs["GAS_FLARE"],
                    probability_agricultural_burning=probs["AGRICULTURAL_BURNING"],
                    probability_mining_activity=probs["MINING_ACTIVITY"],
                    probability_wildfire=probs["WILDFIRE"],
                    max_probability=max_p,
                    existing_risk_level=existing_risk_level,
                    existing_risk_score=existing_risk_score,
                    inference_latency_ms=latency_ms,
                    inference_timestamp=now,
                    feature_schema_version=FEATURE_SCHEMA_VERSION,
                    prediction_status="SUCCESS"
                )
                db.add(new_pred)

            if commit:
                db.commit()

            return {
                "event_id": event_id,
                "model_version": MODEL_VERSION,
                "predicted_class": pred_class,
                "probabilities": probs,
                "max_probability": max_p,
                "existing_risk_level": existing_risk_level,
                "existing_risk_score": existing_risk_score,
                "prediction_status": "SUCCESS",
                "inference_latency_ms": latency_ms,
                "feature_schema_version": FEATURE_SCHEMA_VERSION,
                "inference_timestamp": now.isoformat() + "Z"
            }

        except Exception as e:
            logger.error(f"Shadow inference failed safely for event_id={event_id}: {e}")
            if commit:
                db.rollback()
            return {
                "event_id": event_id,
                "model_version": MODEL_VERSION,
                "predicted_class": "ERROR",
                "probabilities": {cls: 0.0 for cls in TARGET_CLASSES},
                "max_probability": 0.0,
                "prediction_status": "FAILED",
                "error": str(e),
                "inference_latency_ms": round((time.perf_counter() - start_time) * 1000.0, 3)
            }

    def evaluate_shadow_batch(
        self,
        db: Session,
        limit: Optional[int] = None,
        force_run: bool = True
    ) -> Dict[str, Any]:
        """
        Executes shadow inference over a batch of real observations and computes comprehensive
        operational monitoring metrics, latency benchmarks, and semantic disagreement statistics.
        """
        query = db.query(ThermalObservation)
        if limit:
            query = query.limit(limit)
        observations = query.all()

        total_obs = len(observations)
        if total_obs == 0:
            return {
                "total_shadow_predictions": 0,
                "message": "No thermal observations available for shadow evaluation."
            }

        class_counts = {cls: 0 for cls in TARGET_CLASSES}
        conf_bins = {
            "<0.50": 0,
            "0.50-0.70": 0,
            "0.70-0.85": 0,
            "0.85-0.95": 0,
            ">0.95": 0
        }
        latencies = []
        confidences = []
        success_count = 0
        failure_count = 0
        disagreement_count = 0

        for obs in observations:
            res = self.infer_observation(db, obs.id, force_run=force_run, commit=False)
            if res.get("prediction_status") == "SUCCESS":
                success_count += 1
                cls = res.get("predicted_class")
                if cls in class_counts:
                    class_counts[cls] += 1

                p = res.get("max_probability", 0.0)
                confidences.append(p)
                latencies.append(res.get("inference_latency_ms", 0.0))

                # Bin confidence
                if p < 0.50:
                    conf_bins["<0.50"] += 1
                elif p < 0.70:
                    conf_bins["0.50-0.70"] += 1
                elif p < 0.85:
                    conf_bins["0.70-0.85"] += 1
                elif p <= 0.95:
                    conf_bins["0.85-0.95"] += 1
                else:
                    conf_bins[">0.95"] += 1

                # Disagreement analysis:
                r_level = res.get("existing_risk_level")
                if (r_level == "CRITICAL_VERIFIED_RISK" and cls == "WILDFIRE") or \
                   (r_level == "LOW_RISK" and cls == "INDUSTRIAL_FIRE"):
                    disagreement_count += 1
            else:
                failure_count += 1

        try:
            db.commit()
        except Exception as e:
            logger.error(f"Failed to commit batch shadow predictions: {e}")
            db.rollback()

        avg_lat = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
        sorted_lat = sorted(latencies)
        p95_idx = int(0.95 * len(sorted_lat)) if sorted_lat else 0
        p95_lat = sorted_lat[min(p95_idx, len(sorted_lat) - 1)] if sorted_lat else 0.0

        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

        return {
            "total_shadow_predictions": total_obs,
            "successful_predictions": success_count,
            "failed_predictions": failure_count,
            "prediction_success_rate": round(success_count / total_obs, 4) if total_obs > 0 else 0.0,
            "inference_failure_rate": round(failure_count / total_obs, 4) if total_obs > 0 else 0.0,
            "class_distribution": class_counts,
            "confidence_distribution": conf_bins,
            "average_confidence": avg_conf,
            "low_confidence_count": conf_bins["<0.50"] + conf_bins["0.50-0.70"],
            "disagreement_analysis": {
                "disagreement_count": disagreement_count,
                "disagreement_percentage": round((disagreement_count / success_count) * 100.0, 2) if success_count > 0 else 0.0,
                "semantic_note": (
                    "Risk Level (consequence/severity score) and Event Class (physical thermal mechanism) "
                    "are distinct semantic concepts and evaluate complementary axes of information."
                )
            },
            "performance_metrics": {
                "average_latency_ms": avg_lat,
                "p95_latency_ms": p95_lat,
                "total_observations_measured": len(latencies)
            },
            "model_version": MODEL_VERSION,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "shadow_mode_enabled": settings.ML_CLASSIFIER_SHADOW_MODE or force_run,
            "latest_inference_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
