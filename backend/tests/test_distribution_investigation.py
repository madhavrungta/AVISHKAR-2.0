"""
Unit tests for Phase 4F-12: Shadow Prediction Distribution & Calibration Investigation.
Tests feature extraction across 18 features, distribution shift calculation,
confusion matrix evaluation, calibration metrics, bias & saturation verification,
data duplication audit, and strict feature leakage filtering.
"""

import os
import json
import pytest
import numpy as np
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models.thermal_observation import ThermalObservation
from app.models.shadow_prediction import MLShadowPrediction
from app.ml.shadow_inference_service import (
    MLShadowInferenceService, TARGET_CLASSES, FORBIDDEN_LEAKAGE_KEYS,
    MODEL_VERSION, FEATURE_SCHEMA_VERSION
)
from app.ml.phase4f12_investigation import run_fast_investigation

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="module")
def investigation_results():
    results = run_fast_investigation()
    return results

def test_feature_extraction_and_names(investigation_results):
    """Test that all 18 required features are present and analyzed."""
    expected_18_features = [
        "p50_ratio", "p95_ratio", "p99_ratio", "frp_zscore", "bright_ti4_zscore",
        "worldcover_class", "persistence_3d_count", "dist_to_industrial_m",
        "dist_to_energy_m", "dist_to_healthcare_m", "dist_to_transport_m",
        "dist_to_railway_m", "dist_to_highway_m", "dist_to_airport_m",
        "dist_to_port_m", "frp", "brightness", "scan"
    ]
    dist_comp = investigation_results["distribution_comparison"]
    for fn in expected_18_features:
        assert fn in dist_comp, f"Feature {fn} missing from distribution comparison."
        t_stats = dist_comp[fn]["training_stats"]
        s_stats = dist_comp[fn]["shadow_stats"]
        assert t_stats["count"] == 750
        assert s_stats["count"] >= 0
        assert t_stats["missing_pct"] == 0.0
        assert s_stats["missing_pct"] == 0.0

def test_class_wise_distribution_stats(investigation_results):
    """Test class-wise feature distributions across all 5 target classes."""
    cw_stats = investigation_results["class_wise_stats"]
    for cls_name in TARGET_CLASSES:
        assert cls_name in cw_stats, f"Class {cls_name} missing from class-wise stats."
        assert cw_stats[cls_name]["sample_count"] == 150
        feat_stats = cw_stats[cls_name]["feature_stats"]
        assert "frp" in feat_stats
        assert "dist_to_industrial_m" in feat_stats
        assert "persistence_3d_count" in feat_stats

def test_verified_ground_truth_evaluation(investigation_results):
    """Test ground-truth evaluation metrics, confusion matrix, and class metrics."""
    gt_eval = investigation_results["verified_ground_truth_evaluation"]
    assert "accuracy" in gt_eval
    assert "balanced_accuracy" in gt_eval
    assert "macro_f1" in gt_eval
    assert "confusion_matrix" in gt_eval
    
    cm = gt_eval["confusion_matrix"]
    assert len(cm) == 5
    assert len(cm[0]) == 5
    
    # 750 total support
    total_support = sum(sum(row) for row in cm)
    assert total_support == 750

def test_confidence_and_probability_saturation(investigation_results):
    """Test confidence analysis and verification of continuous probabilistic confidence."""
    conf = investigation_results["confidence_analysis"]
    assert conf["average_top1_confidence"] > 0.50
    assert conf["confidence_bins"]["0.70-0.85"] > 0 or conf["confidence_bins"][">0.95"] > 0
    assert conf["average_margin"] > 0.50

def test_calibration_metrics(investigation_results):
    """Test calibration audit metrics: Brier score, log loss, ECE."""
    calib = investigation_results["calibration_audit"]
    assert "brier_score" in calib
    assert "log_loss" in calib
    assert "expected_calibration_error" in calib
    assert calib["sample_size"] == 750
    assert calib["brier_score"] >= 0.0

def test_data_duplication_audit(investigation_results):
    """Test data duplication audit on clusters, feature vectors, and shadow predictions."""
    dup = investigation_results["duplication_audit"]
    assert dup["total_candidates"] == 750
    assert dup["unique_physical_event_clusters"] == 250
    assert dup["total_shadow_predictions"] >= 3251

def test_leakage_safeguard_strict():
    """Verify strict 17-field leakage filtering in MLShadowInferenceService."""
    service = MLShadowInferenceService()
    leaky_input = {
        "frp": 15.0,
        "brightness_temperature": 330.0,
        "facility_distance_m": 1200.0,
        "target_label": "INDUSTRIAL_FIRE",
        "ground_truth": "OFFICIAL_REGISTRY",
        "label_confidence": "HIGH",
        "confidence": "HIGH",
        "physical_event_cluster_id": "CLUSTER_123",
        "acq_date": "2026-02-15",
        "provenance_url": "https://data.gov.in"
    }
    clean_features, violations = service.validate_and_filter_features(leaky_input)
    assert len(violations) == 7
    for vk in ["target_label", "ground_truth", "label_confidence", "confidence", "physical_event_cluster_id", "acq_date", "provenance_url"]:
        assert vk in violations
        assert vk not in clean_features

def test_model_artifact_json_file_exists():
    """Verify that the Phase 4F-12 investigation result JSON file exists and is valid."""
    artifact_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "ml_artifacts", "phase_4f12_investigation_results.json")
    )
    assert os.path.exists(artifact_path)
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "dataset_baseline" in data
    assert "distribution_comparison" in data
    assert "verified_ground_truth_evaluation" in data
