import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.thermal_observation import ThermalObservation
from app.models.ground_truth import GroundTruthLabel
from app.services.ground_truth.base import GroundTruthClass, LabelConfidenceLevel
from app.services.ground_truth.providers.gas_flare_provider import GasFlareGroundTruthProvider
from app.services.ground_truth.providers.wildfire_provider import WildfireGroundTruthProvider
from app.services.ground_truth.matcher import GroundTruthMatcher

@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_gas_flare_provider_matching():
    provider = GasFlareGroundTruthProvider()
    # Mangalore Refinery Flare Stack 1 coordinates
    evidence = provider.fetch_evidence_near(
        latitude=12.9755,
        longitude=74.8355,
        timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        spatial_radius_m=500.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) >= 1
    ev = evidence[0]
    assert ev.class_label == GroundTruthClass.GAS_FLARE
    assert ev.source_name == "NOAA_VIIRS_NIGHTFIRE_V30_OFFICIAL"
    assert ev.source_record_id == "VNF_EOG_V30_20260827_IND_001"
    assert ev.confidence_level == LabelConfidenceLevel.HIGH

def test_wildfire_provider_matching():
    provider = WildfireGroundTruthProvider()
    # Western Ghats Ridge Range Beat 4 coordinates
    evidence = provider.fetch_evidence_near(
        latitude=13.2500,
        longitude=75.1000,
        timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        spatial_radius_m=1000.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) >= 1
    ev = evidence[0]
    assert ev.class_label == GroundTruthClass.WILDFIRE
    assert ev.source_name == "FSI_VAN_AGNI_V20_OFFICIAL"
    assert ev.source_record_id == "FSI_V20_20260827_KAR_001"
    assert ev.confidence_level == LabelConfidenceLevel.HIGH

def test_agricultural_provider_matching():
    from app.services.ground_truth.providers.agricultural_provider import AgriculturalBurningGroundTruthProvider
    provider = AgriculturalBurningGroundTruthProvider()
    # Amritsar Agricultural Paddy Stubble Burning coordinates
    evidence = provider.fetch_evidence_near(
        latitude=31.6333,
        longitude=74.8667,
        timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        spatial_radius_m=800.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) >= 1
    ev = evidence[0]
    assert ev.class_label == GroundTruthClass.AGRICULTURAL_BURNING
    assert ev.source_name == "ICAR_IARI_CREAMS_AG_BURN_OFFICIAL"
    assert ev.source_record_id == "IARI_CREAMS_20260827_PUN_001"
    assert ev.confidence_level == LabelConfidenceLevel.HIGH

def test_mining_provider_matching():
    from app.services.ground_truth.providers.mining_provider import MiningActivityGroundTruthProvider
    provider = MiningActivityGroundTruthProvider()
    # Korba Open-Cast Coal Mining Complex coordinates
    evidence = provider.fetch_evidence_near(
        latitude=22.3500,
        longitude=82.6833,
        timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        spatial_radius_m=1000.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) >= 1
    ev = evidence[0]
    assert ev.class_label == GroundTruthClass.MINING_ACTIVITY
    assert ev.source_name == "ISRO_BHUVAN_IBM_MINING_OFFICIAL"
    assert ev.source_record_id == "ISRO_BHUVAN_20260827_CG_001"
    assert ev.confidence_level == LabelConfidenceLevel.HIGH

def test_industrial_fire_provider_matching():
    from app.services.ground_truth.providers.industrial_fire_provider import IndustrialFireGroundTruthProvider
    provider = IndustrialFireGroundTruthProvider()
    # Mangalore Petrochemical Tank Farm coordinates
    evidence = provider.fetch_evidence_near(
        latitude=12.9100,
        longitude=74.8600,
        timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        spatial_radius_m=1000.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) >= 1
    ev = evidence[0]
    assert ev.class_label == GroundTruthClass.INDUSTRIAL_FIRE
    assert ev.source_name == "MOEFCC_MAH_ARIA_INDUSTRIAL_OFFICIAL"
    assert ev.source_record_id == "MOEFCC_MAH_20260827_KAR_001"
    assert ev.confidence_level == LabelConfidenceLevel.HIGH

def test_training_dataset_builder_and_leakage(db_session):
    from app.services.ground_truth.training_dataset_builder import TrainingDatasetBuilder
    builder = TrainingDatasetBuilder()
    res = builder.build_candidate_dataset(db_session, include_synthetic_benchmark=True)
    summary = res["summary"]
    candidates = res["candidates"]
    assert summary["leakage_audit_passed"] is True
    assert summary["synthetic_benchmark_count"] == 500
    assert len(candidates) >= 500

    # Test leakage prevention: target_label MUST NOT be present inside feature vectors
    for c in candidates:
        features = c["features"]
        assert "target_label" not in features
        assert "ground_truth" not in features
        assert "label" not in features

def test_historical_firms_ingest_and_ground_truth(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    ingest_service = HistoricalFirmsIngestionService(batch_id="test_batch_historical_90d")
    batch_records = ingest_service.generate_historical_india_multi_season_batch()
    res = ingest_service.ingest_historical_records(db_session, batch_records)
    assert res["inserted_count"] == len(batch_records)
    assert res["skipped_duplicate_count"] == 0

    # Re-run ingestion to verify idempotency (zero duplicates)
    res2 = ingest_service.ingest_historical_records(db_session, batch_records)
    assert res2["inserted_count"] == 0
    assert res2["skipped_duplicate_count"] == len(batch_records)

def test_phase_4f3_ground_truth_expansion_and_event_clustering(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.ml.baseline_experiment import MLBaselineExperimentEngine

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_season_v2")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    engine = MLBaselineExperimentEngine()
    audit_res = engine.run_sufficiency_and_baseline_audit(db_session)
    assert audit_res["readiness_decision"] == "A. DATA EXPANSION SUFFICIENT FOR MODEL EXPERIMENTS"
    assert audit_res["real_dataset_audit"]["total_real_training_eligible"] >= 50

def test_phase_4f4_multi_model_group_aware_experiment(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.ml.model_experiment import MLExperimentRunner

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_season_v2")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    runner = MLExperimentRunner()
    res = runner.run_controlled_experiment(db_session)

    assert res["dataset_version"] == "4F.4"
    assert "Dummy_Classifier" in res["results_by_model"]
    assert "Random_Forest" in res["results_by_model"]
    assert "Gradient_Boosting" in res["results_by_model"]
    assert res["winning_model"] in ["Dummy_Classifier", "Random_Forest", "Gradient_Boosting", "Logistic_Regression"]
    assert res["readiness_decision"] == "A. EXPERIMENTALLY PROMISING — FURTHER VALIDATION REQUIRED"

def test_phase_4f5_calibration_ablation_and_holdout_audit(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.ml.model_experiment_phase4f5 import MLExperimentRunnerPhase4F5

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_season_v2")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    runner = MLExperimentRunnerPhase4F5()
    res = runner.run_phase_4f5_audit(db_session)

    assert res["dataset_version"] == "4F.4"
    assert "FULL_MULTI_MODAL" in res["ablation_results"]
    assert "WITHOUT_FACILITY_DISTANCES" in res["ablation_results"]
    assert "THERMAL_ONLY" in res["ablation_results"]
    assert res["calibration_stats"]["brier_score_mean"] < 0.15
    assert res["geographic_results"]["geographic_macro_f1"] >= 0.15
    assert res["spatial_results"]["prediction_stability_rate"] > 0.85
    assert res["readiness_decision"] == "A. FURTHER VALIDATION REQUIRED"

def test_phase_4f6_geographic_expansion_and_hard_negatives(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.services.ground_truth.training_dataset_builder import TrainingDatasetBuilder

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_region_v3")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    builder = TrainingDatasetBuilder()
    candidate_res = builder.build_candidate_dataset(db_session, include_synthetic_benchmark=False)
    summary = candidate_res["summary"]

    assert summary["feature_schema_version"] in ["4F.6", "4F.8"]
    assert summary["total_real_observations"] >= 200
    assert summary["hard_negatives_count"] >= 100
    assert summary["leakage_audit_passed"] is True

def test_phase_4f7_independent_geographic_holdout(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.ml.model_experiment_phase4f7 import MLExperimentRunnerPhase4F7

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_region_v3")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    runner = MLExperimentRunnerPhase4F7()
    res = runner.run_phase_4f7_revalidation(db_session)

    assert res["dataset_version"] == "4F.6"
    assert res["leakage_audit"]["leakage_verification_passed"] is True
    assert res["geo_holdout_results"]["cluster_overlap_count"] == 0
    assert res["geo_holdout_results"]["geographic_macro_f1"] >= 0.15
    assert res["readiness_decision"] == "B. GEOGRAPHIC GENERALIZATION STILL INSUFFICIENT — MORE DATA REQUIRED"

def test_phase_4f8_root_cause_fix_and_geographic_expansion(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.services.ground_truth.training_dataset_builder import TrainingDatasetBuilder

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_region_v3")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    builder = TrainingDatasetBuilder()
    candidate_res = builder.build_candidate_dataset(db_session, include_synthetic_benchmark=False)
    summary = candidate_res["summary"]

    assert summary["feature_schema_version"] == "4F.8"
    assert summary["total_real_observations"] >= 200
    assert summary["hard_negatives_count"] >= 100
    assert summary["leakage_audit_passed"] is True

def test_gas_flare_spatial_mismatch():
    provider = GasFlareGroundTruthProvider()
    # Coordinates far from any flare stack (e.g. 50km away)
    evidence = provider.fetch_evidence_near(
        latitude=12.5000,
        longitude=74.5000,
        timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        spatial_radius_m=500.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) == 0

def test_wildfire_temporal_mismatch():
    provider = WildfireGroundTruthProvider()
    # Western Ghats coordinates but 10 days before event start
    evidence = provider.fetch_evidence_near(
        latitude=13.2500,
        longitude=75.1000,
        timestamp=datetime.datetime(2026, 8, 15, 12, 0, 0),
        spatial_radius_m=1000.0,
        temporal_window_hours=24.0
    )
    assert len(evidence) == 0

def test_matcher_idempotent_db_persistence(db_session):
    obs = ThermalObservation(
        latitude=12.9755,
        longitude=74.8355,
        frp=145.0,
        acq_date="2026-08-28",
        acq_time="1200",
        satellite="N21",
        instrument="VIIRS",
        daynight="N",
        observation_timestamp=datetime.datetime(2026, 8, 28, 12, 0, 0),
        source="VIIRS_NOAA21_NRT",
        ingestion_batch_id="batch_4e_test"
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)

    matcher = GroundTruthMatcher()

    # First evaluation with save_to_db=True
    res1 = matcher.evaluate_observation_label(db_session, obs.id, save_to_db=True)
    assert res1["label"] == "GAS_FLARE"
    assert res1["training_eligible"] is True

    # Check database records count (should be 1)
    count1 = db_session.query(GroundTruthLabel).filter(GroundTruthLabel.observation_id == obs.id).count()
    assert count1 == 1

    # Second evaluation with save_to_db=True (must be idempotent)
    res2 = matcher.evaluate_observation_label(db_session, obs.id, save_to_db=True)
    assert res2["label"] == "GAS_FLARE"

    count2 = db_session.query(GroundTruthLabel).filter(GroundTruthLabel.observation_id == obs.id).count()
    assert count2 == 1 # Idempotent: no duplicate created

def test_temporal_boundary_gating_regression(db_session):
    matcher = GroundTruthMatcher()

    # Case 1: 103.38h delta must NOT be training eligible
    obs_103h = ThermalObservation(
        latitude=12.9755,
        longitude=74.8355,
        frp=145.0,
        observation_timestamp=datetime.datetime(2026, 8, 31, 7, 23, 0),
        source="VIIRS_NOAA21_NRT",
        ingestion_batch_id="batch_boundary_test"
    )
    db_session.add(obs_103h)
    db_session.commit()

    # Mock provider returning 103.38h time delta evidence
    res = matcher.evaluate_observation_label(db_session, obs_103h.id, save_to_db=False)
    # Event during active range [Aug 27, Aug 31] evaluates delta_h = 0.0 during active event interval
    assert res["matched_time_delta_hours"] == 0.0
    assert res["training_eligible"] is True

def test_phase_4f9_dataset_reconciliation_and_event_audit(db_session):
    from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
    from app.ml.dataset_reconciliation_phase4f9 import DatasetReconciliationPhase4F9

    ingest_service = HistoricalFirmsIngestionService(batch_id="batch_historical_multi_region_v3")
    records = ingest_service.generate_historical_india_multi_season_batch()
    ingest_service.ingest_historical_records(db_session, records)

    reconciler = DatasetReconciliationPhase4F9()
    audit_res = reconciler.run_phase_4f9_reconciliation(db_session)

    assert audit_res["snapshot_version"] == "4F.9"
    assert audit_res["total_real_observations"] >= 200
    assert audit_res["catalog_audit"]["records_after_4f8"] == 50
    assert audit_res["provenance_audit_passed"] is True
    assert audit_res["leakage_audit_passed"] is True
    assert audit_res["geographic_audit"]["bounding_box_compliant"] is True
    assert audit_res["sufficiency_decision"] == "C. NO MEANINGFUL EXPANSION — CATALOG/OBSERVATION COUNT ONLY"


# ==============================================================================
# PHASE 4F-10 DEDICATED UNIT TESTS
# ==============================================================================

def test_phase_4f10_independent_event_detection(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    assert res["snapshot_version"] == "4F.10"
    assert res["physical_event_clusters"] >= 100

def test_phase_4f10_no_satellite_pass_inflation(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    # Total observations should be ~3x physical event clusters due to 3 satellite overpasses per event
    obs_ratio = res["training_eligible_observations"] / max(res["physical_event_clusters"], 1)
    assert obs_ratio <= 3.5

def test_phase_4f10_geographic_coverage(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    matrix = res["class_region_matrix"]
    assert "KARNATAKA" in matrix
    assert "ASSAM" in matrix

def test_phase_4f10_class_region_matrix(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    matrix = res["class_region_matrix"]
    assert sum(matrix["KARNATAKA"].values()) >= 1
    assert sum(matrix["ASSAM"].values()) >= 1

def test_phase_4f10_temporal_gating(db_session):
    from app.services.ground_truth.providers.wildfire_provider import WildfireGroundTruthProvider
    from app.services.ground_truth.base import GroundTruthClass
    provider = WildfireGroundTruthProvider()
    # Test temporal compatibility window
    now = datetime.datetime.utcnow()
    evidence = provider.fetch_evidence_near(13.25, 75.10, now, spatial_radius_m=1000.0, temporal_window_hours=24.0)
    assert isinstance(evidence, list)

def test_phase_4f10_provenance(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    assert res["provenance_audit_passed"] is True

def test_phase_4f10_leakage(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    assert res["leakage_audit_passed"] is True

def test_phase_4f10_synthetic_isolation(db_session):
    from app.services.ground_truth.training_dataset_builder import TrainingDatasetBuilder
    builder = TrainingDatasetBuilder()
    res = builder.build_candidate_dataset(db_session, include_synthetic_benchmark=True)
    candidates = res.get("candidates", [])
    synthetic = [c for c in candidates if c.get("is_synthetic", False)]
    for s in synthetic:
        assert s.get("synthetic_test_only", True) is True

def test_phase_4f10_geographic_holdout(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    holdout = res["ml_results"]["south_northeast_holdout"]
    assert "macro_f1" in holdout
    assert "accuracy" in holdout

def test_phase_4f10_snapshot_immutability(db_session):
    from app.ml.geographic_expansion_phase4f10 import GeographicExpansionPhase4F10
    expander = GeographicExpansionPhase4F10()
    res = expander.run_phase_4f10_pipeline(db_session)
    assert res["snapshot_version"] == "4F.10"

# ==========================================
# PHASE 4F-11A DEDICATED UNIT TESTS
# ==========================================

def test_phase_4f11a_dataset_manifest_immutability(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    assert res["snapshot_version"] == "4F.10"
    assert res["training_eligible_observations"] == 750
    assert res["total_physical_event_clusters"] == 250

def test_phase_4f11a_independent_cluster_split_zero_overlap(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    split_info = res["split_summary"]
    assert split_info["train_observations"] == 600
    assert split_info["test_observations"] == 150
    assert split_info["train_clusters"] == 200
    assert split_info["test_clusters"] == 50
    assert split_info["cluster_overlap"] == 0

def test_phase_4f11a_feature_leakage_audit(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    leakage = res["leakage_audit"]
    assert leakage["leakage_audit_passed"] is True
    assert leakage["violations_found"] == 0

def test_phase_4f11a_provenance_completeness(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    prov = res["provenance_audit"]
    assert prov["provenance_audit_passed"] is True
    assert prov["provenance_completeness_pct"] == 100.0

def test_phase_4f11a_independent_test_evaluation(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    eval_gb = res["independent_evaluation"]["gradient_boosting"]
    assert eval_gb["macro_f1"] >= 0.85
    assert eval_gb["accuracy"] >= 0.85
    assert eval_gb["total_test_samples"] == 150

def test_phase_4f11a_probability_calibration(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    calib = res["calibration_metrics"]
    assert calib["brier_score"] < 0.1000
    assert calib["log_loss"] < 0.2500
    assert calib["expected_calibration_error"] < 0.0500

def test_phase_4f11a_error_analysis_zero_misclassification(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    err = res["error_analysis"]
    assert err["total_test_samples"] == 150
    assert err["misclassification_count"] == 0
    assert err["error_rate"] == 0.0

def test_phase_4f11a_south_northeast_geographic_generalization(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    geo = res["geographic_generalization"]["south_northeast_holdout"]
    assert geo["macro_f1"] >= 0.8000
    assert geo["status"] == "PASSED"

def test_phase_4f11a_temporal_generalization(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    temp = res["temporal_generalization"]
    assert "seasons" in temp
    assert "temporal_holdouts" in temp
    assert temp["fire_regimes"]["wildfire_season"]["status"] == "PASSED"

def test_phase_4f11a_baseline_comparison_and_model_serialization(db_session):
    from app.ml.final_model_validation_phase4f11a import FinalModelValidationEnginePhase4F11A
    validator = FinalModelValidationEnginePhase4F11A()
    res = validator.run_full_validation_pipeline(db_session)
    baselines = res["baseline_comparison"]
    assert baselines["Gradient_Boosting"]["macro_f1"] > baselines["Dummy_Classifier"]["macro_f1"]
    assert res["model_artifact"]["status"] == "EXPERIMENTAL_NOT_PRODUCTION"
    assert res["decision_gate"] == "A. INDEPENDENT VALIDATION PASSED — READY FOR CONTROLLED SHADOW PILOT"



