import pytest
from app.ml.classifier import SourceClassifier

def test_industrial_candidate_classification():
    classifier = SourceClassifier()
    vector = {
        "distance_meters": 150.0,
        "facility_type": "refinery",
        "frp": 25.0,
        "bright_ti4": 330.0,
        "bright_ti5": 295.0,
        "daynight": "D"
    }
    pred, conf, reason = classifier.predict(vector)
    assert pred == "INDUSTRIAL_CANDIDATE"
    assert conf >= 0.85
    assert "refinery" in reason.lower() or "industrial" in reason.lower()

def test_natural_forest_candidate_classification():
    classifier = SourceClassifier()
    vector = {
        "distance_meters": 5000.0,
        "facility_type": "none",
        "frp": 45.0,
        "daynight": "N"
    }
    pred, conf, reason = classifier.predict(vector)
    assert pred == "NATURAL_FOREST_CANDIDATE"
    assert conf == 0.85
    assert "natural" in reason.lower() or "forest" in reason.lower()

def test_agricultural_candidate_classification():
    classifier = SourceClassifier()
    vector = {
        "distance_meters": 3500.0,
        "facility_type": "none",
        "frp": 12.0,
        "daynight": "D"
    }
    pred, conf, reason = classifier.predict(vector)
    assert pred == "AGRICULTURAL_CANDIDATE"
    assert conf == 0.75

def test_other_unknown_classification():
    classifier = SourceClassifier()
    vector = {
        "distance_meters": 2500.0,
        "facility_type": "none",
        "frp": 25.0,
        "daynight": "N"
    }
    pred, conf, reason = classifier.predict(vector)
    assert pred == "OTHER_UNKNOWN"
    assert conf == 0.50
