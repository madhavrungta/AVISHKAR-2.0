import os
import json
import pytest
from app.ml.shadow_inference_service import MLShadowInferenceService, TARGET_CLASSES, FORBIDDEN_LEAKAGE_KEYS
from app.ml.gradient_boosting import PurePythonMLPipeline, FEATURE_NAMES_18

ARTIFACT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml_artifacts', 'phase_4f14_audit_results.json'))

@pytest.fixture(scope='module')
def audit_data():
    assert os.path.exists(ARTIFACT_JSON), f'Phase 4F-14 audit artifact not found: {ARTIFACT_JSON}'
    with open(ARTIFACT_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_ground_truth_lineage_counts(audit_data):
    gt = audit_data['ground_truth_lineage']
    assert gt['total_ground_truth_records'] == 750
    assert gt['total_physical_clusters'] == 250
    assert gt['records_per_class'] == 150
    assert gt['clusters_per_class'] == 50
    assert len(gt['source_catalogs']) == 5

def test_leakage_audit_isolation(audit_data):
    leakage = audit_data['leakage_audit']
    assert leakage['train_records'] == 600
    assert leakage['test_records'] == 150
    assert leakage['train_unique_clusters'] == 200
    assert leakage['test_unique_clusters'] == 50
    assert leakage['cluster_overlap_count'] == 0
    assert leakage['exact_coord_overlap_count'] == 0
    assert leakage['test_records_within_threshold_of_train'] == 0
    assert leakage['min_distance_to_train_km']['min'] >= 1.0
    assert leakage['cluster_isolation_status'] == 'STRICTLY_DISJOINT_CLUSTERS'

def test_independent_test_evaluation(audit_data):
    test_eval = audit_data['evaluation_recalculations']['independent_test_partition_150']
    assert test_eval['sample_count'] == 150
    assert test_eval['accuracy'] == 1.0
    assert test_eval['macro_f1'] == 1.0
    assert test_eval['brier_score'] <= 0.05
    assert test_eval['log_loss'] <= 0.35

def test_ambient_mining_distribution_explained(audit_data):
    amb = audit_data['ambient_generalization_audit']
    assert amb['total_ambient_evaluated'] == 4121
    mining_analysis = amb['mining_prediction_analysis']
    assert mining_analysis['mining_predicted_count'] == 0
    assert mining_analysis['mining_max_probability'] <= 0.30
    assert mining_analysis['mining_mean_probability'] <= 0.05
    assert len(mining_analysis['root_cause_of_mining_zero']) > 0

def test_18_feature_shifts_present(audit_data):
    shifts = audit_data['feature_distribution_shifts']
    for fn in FEATURE_NAMES_18:
        assert fn in shifts
        assert 'cohen_d_shift' in shifts[fn]
        assert 'training_mining_stats' in shifts[fn]
        assert 'ambient_stats' in shifts[fn]

def test_inference_consistency_and_safeguards(audit_data):
    consistency = audit_data['inference_pipeline_consistency']
    assert consistency['feature_ordering_identical'] is True
    assert consistency['scaler_mean_std_frozen'] is True
    assert consistency['leakage_keys_filtered'] == 17
    assert consistency['status'] == 'CONSISTENT_VERIFIED'

def test_gate_decision_recorded(audit_data):
    gate = audit_data['gate_recommendation']
    assert 'GATE A' in gate['gate']
    assert len(gate['rationale']) > 0
