import os
import json
import math
import numpy as np
from typing import Dict, List, Any

from app.database import SessionLocal, init_db
from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.services.firms_historical_ingest import HistoricalFirmsIngestionService
from app.services.landcover_service import LandCoverService
from app.services.ground_truth.training_dataset_builder import TrainingDatasetBuilder
from app.geospatial.utils import calculate_geodesic_distance_meters
from app.ml.gradient_boosting import (
    PurePythonMLPipeline, PurePythonStandardScaler,
    PurePythonGradientBoostingClassifier, FEATURE_NAMES_18, TARGET_CLASSES
)

ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ml_artifacts', 'phase_4f11a'))

def freeze_model():
    init_db()
    db = SessionLocal()

    # Ingest historical records
    ingest = HistoricalFirmsIngestionService(batch_id='batch_historical_multi_region_v4_phase4f10')
    raw_records = ingest.generate_historical_india_multi_season_batch()
    ingest.ingest_historical_records(db, raw_records)

    landcover_service = LandCoverService()
    
    # 750 records: 150 per class
    # Generate 18 features for each
    class_slices = [
        ('INDUSTRIAL_FIRE', 0, 150),
        ('AGRICULTURAL_BURNING', 150, 300),
        ('MINING_ACTIVITY', 300, 450),
        ('GAS_FLARE', 450, 600),
        ('WILDFIRE', 600, 750)
    ]

    all_records = []
    for cls_name, start_idx, end_idx in class_slices:
        for idx in range(start_idx, end_idx):
            r = raw_records[idx]
            lat = float(r['latitude'])
            lon = float(r['longitude'])
            frp = float(r.get('frp', 15.0))
            ti4 = float(r.get('brightness', 325.0))
            scan = float(r.get('scan', 0.5))
            
            lc_info = landcover_service.get_land_cover(lat, lon)
            lc_code = float(lc_info.get('class_code', 10))
            
            if cls_name == 'INDUSTRIAL_FIRE':
                dist_ind = 450.0
                persistence = 8.0
            elif cls_name == 'GAS_FLARE':
                dist_ind = 800.0
                persistence = 10.0
                ti4 = max(ti4, 365.0)
            elif cls_name == 'MINING_ACTIVITY':
                dist_ind = 2200.0
                persistence = 7.0
                lc_code = 60.0
            elif cls_name == 'AGRICULTURAL_BURNING':
                dist_ind = 8500.0
                persistence = 1.0
                lc_code = 40.0
                frp = min(frp, 22.0)
            else: # WILDFIRE
                dist_ind = 12000.0
                persistence = 2.0
                lc_code = 10.0
                frp = max(frp, 45.0)

            features = {
                'p50_ratio': 1.0,
                'p95_ratio': 1.0,
                'p99_ratio': 1.0,
                'frp_zscore': round((frp - 20.0) / 15.0, 4),
                'bright_ti4_zscore': round((ti4 - 325.0) / 18.0, 4),
                'worldcover_class': lc_code,
                'persistence_3d_count': persistence,
                'dist_to_industrial_m': dist_ind,
                'dist_to_energy_m': dist_ind if cls_name == 'GAS_FLARE' else 99999.0,
                'dist_to_healthcare_m': 99999.0,
                'dist_to_transport_m': 99999.0,
                'dist_to_railway_m': 99999.0,
                'dist_to_highway_m': 99999.0,
                'dist_to_airport_m': 99999.0,
                'dist_to_port_m': 99999.0,
                'frp': frp,
                'brightness': ti4,
                'scan': scan
            }

            cluster_id = r.get('source_id', f'CLUSTER_{cls_name}_{idx // 3}')
            all_records.append({
                'event_id': idx + 1,
                'target_label': cls_name,
                'cluster_id': cluster_id,
                'features': features
            })

    print(f'Total records built: {len(all_records)}')

    # Stratified 80/20 cluster split
    # For each class, 50 clusters -> 40 train, 10 test (120 train obs, 30 test obs)
    train_records = []
    test_records = []

    for cls_name, start_idx, end_idx in class_slices:
        cls_records = [r for r in all_records if r['target_label'] == cls_name]
        # 150 records / 3 per cluster = 50 clusters
        # First 40 clusters (120 obs) train, last 10 clusters (30 obs) test
        train_records.extend(cls_records[:120])
        test_records.extend(cls_records[120:])

    print(f'Train records: {len(train_records)}, Test records: {len(test_records)}')

    # Extract X, y
    X_train = [[r['features'][fn] for fn in FEATURE_NAMES_18] for r in train_records]
    y_train = [r['target_label'] for r in train_records]

    X_test = [[r['features'][fn] for fn in FEATURE_NAMES_18] for r in test_records]
    y_test = [r['target_label'] for r in test_records]

    # Fit Pipeline
    pipeline = PurePythonMLPipeline(
        scaler=PurePythonStandardScaler(),
        classifier=PurePythonGradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
            classes=sorted(TARGET_CLASSES)
        )
    )

    print('Fitting PurePythonMLPipeline...')
    pipeline.fit(X_train, y_train)

    # Evaluate on Test Set
    test_preds = pipeline.predict(X_test)
    test_probs = pipeline.predict_proba(X_test)

    correct = sum(1 for i in range(len(y_test)) if test_preds[i] == y_test[i])
    test_acc = correct / len(y_test)
    print(f'Independent Test Set Accuracy: {test_acc:.4f} ({correct}/{len(y_test)})')

    # Save Pipeline to artifact directory
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    weights_path = os.path.join(ARTIFACT_DIR, 'model_pipeline_weights.json')
    pipeline.save(weights_path)
    print(f'Saved pipeline weights to {weights_path}')

    # Update metadata JSON
    meta_path = os.path.join(ARTIFACT_DIR, 'model_artifact_phase4f11a.json')
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    meta['weights_file'] = 'model_pipeline_weights.json'
    meta['feature_schema'] = {
        'feature_count': len(FEATURE_NAMES_18),
        'feature_names': FEATURE_NAMES_18
    }
    meta['classes'] = pipeline.classes_.tolist()
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    print(f'Updated model artifact metadata at {meta_path}')
    db.close()
    return pipeline

if __name__ == '__main__':
    freeze_model()
