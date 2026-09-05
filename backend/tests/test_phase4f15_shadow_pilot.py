import os
import json
import pytest
from app.ml.shadow_inference_service import TARGET_CLASSES
from app.ml.gradient_boosting import FEATURE_NAMES_18

PILOT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml_artifacts', 'phase_4f15_shadow_pilot_results.json'))

@pytest.fixture(scope='module')
def pilot_data():
    assert os.path.exists(PILOT_JSON), f'Phase 4F-15 pilot artifact not found: {PILOT_JSON}'
    with open(PILOT_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_multi_region_coverage(pilot_data):
    reg_summary = pilot_data['regional_summary']
    expected_regions = ['North', 'South', 'West', 'East', 'Central', 'Northeast']
    for reg in expected_regions:
        assert reg in reg_summary, f'Region {reg} missing from regional summary'
        assert reg_summary[reg]['observation_count'] > 0
        assert len(reg_summary[reg]['states_represented']) > 0

def test_temporal_partitions(pilot_data):
    temp_summary = pilot_data['temporal_summary']
    expected_windows = [
        'Window_1_Early (2025-10 to 2026-01)',
        'Window_2_Mid (2026-02 to 2026-05)',
        'Window_3_Late (2026-06 to 2026-08)'
    ]
    for tw in expected_windows:
        assert tw in temp_summary
        assert temp_summary[tw]['observation_count'] > 0

def test_overall_prediction_distribution(pilot_data):
    overall = pilot_data['overall_shadow_distribution']
    counts = overall['prediction_counts']
    for c in TARGET_CLASSES:
        assert c in counts
    total = sum(counts.values())
    assert total == 4121
    assert counts['AGRICULTURAL_BURNING'] > 3000
    assert counts['WILDFIRE'] > 500

def test_spatial_stability(pilot_data):
    stability = pilot_data['spatial_temporal_stability']
    assert stability['spatial_pairs_checked'] > 1000
    assert stability['spatial_stability_rate'] >= 0.95

def test_latency_and_performance(pilot_data):
    perf = pilot_data['performance_benchmarks']
    assert perf['total_inferences'] == 4121
    assert perf['failure_count'] == 0
    assert perf['average_latency_ms'] < 25.0
    assert perf['p95_latency_ms'] < 50.0

def test_risk_engine_invariance(pilot_data):
    risk_inv = pilot_data['risk_engine_invariance']
    assert risk_inv['risk_service_unaffected'] is True
    assert risk_inv['authoritative_scores_unchanged'] is True
    assert risk_inv['shadow_mode_isolation_verified'] is True

def test_human_review_candidates(pilot_data):
    candidates = pilot_data['human_review_candidates']
    assert len(candidates) >= 10
    categories = set(c['category'] for c in candidates)
    assert 'HIGH_CONFIDENCE_INDUSTRIAL_OR_FLARE' in categories
    assert 'TOP_MINING_PROBABILITY_CANDIDATE' in categories

def test_gate_decision(pilot_data):
    gate = pilot_data['final_gate_recommendation']
    assert 'GATE A' in gate['gate']
