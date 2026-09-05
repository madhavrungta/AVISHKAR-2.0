import os
import json
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union

TARGET_CLASSES = [
    'AGRICULTURAL_BURNING',
    'GAS_FLARE',
    'INDUSTRIAL_FIRE',
    'MINING_ACTIVITY',
    'WILDFIRE'
]

FEATURE_NAMES_18 = [
    'p50_ratio',
    'p95_ratio',
    'p99_ratio',
    'frp_zscore',
    'bright_ti4_zscore',
    'worldcover_class',
    'persistence_3d_count',
    'dist_to_industrial_m',
    'dist_to_energy_m',
    'dist_to_healthcare_m',
    'dist_to_transport_m',
    'dist_to_railway_m',
    'dist_to_highway_m',
    'dist_to_airport_m',
    'dist_to_port_m',
    'frp',
    'brightness',
    'scan'
]

class PurePythonDecisionNode:
    def __init__(
        self,
        feature: Optional[int] = None,
        threshold: Optional[float] = None,
        left: Optional['PurePythonDecisionNode'] = None,
        right: Optional['PurePythonDecisionNode'] = None,
        value: Optional[float] = None
    ):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    @property
    def is_leaf(self) -> bool:
        return self.value is not None

    def to_dict(self) -> Dict[str, Any]:
        if self.is_leaf:
            return {'value': float(self.value)}
        return {
            'feature': int(self.feature),
            'threshold': float(self.threshold),
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None
        }

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional['PurePythonDecisionNode']:
        if d is None:
            return None
        if 'value' in d:
            return cls(value=float(d['value']))
        return cls(
            feature=d.get('feature'),
            threshold=d.get('threshold'),
            left=cls.from_dict(d.get('left')),
            right=cls.from_dict(d.get('right'))
        )

class PurePythonRegressionTree:
    def __init__(self, max_depth: int = 4, min_samples_split: int = 2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root: Optional[PurePythonDecisionNode] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'PurePythonRegressionTree':
        self.root = self._build_tree(X, y, depth=0)
        return self

    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> PurePythonDecisionNode:
        n_samples, n_features = X.shape
        if depth >= self.max_depth or n_samples < self.min_samples_split or len(np.unique(y)) <= 1:
            return PurePythonDecisionNode(value=float(np.mean(y)))

        best_feat, best_thresh = None, None
        best_var_red = -1.0
        current_var = float(np.var(y) * n_samples)

        for f in range(n_features):
            vals = np.unique(X[:, f])
            if len(vals) > 25:
                vals = np.percentile(vals, np.linspace(4, 96, 24))
            for t in vals:
                left_mask = X[:, f] <= t
                right_mask = ~left_mask
                n_left = int(np.sum(left_mask))
                n_right = n_samples - n_left
                if n_left == 0 or n_right == 0:
                    continue
                left_var = float(np.var(y[left_mask]) * n_left)
                right_var = float(np.var(y[right_mask]) * n_right)
                var_red = current_var - (left_var + right_var)
                if var_red > best_var_red:
                    best_var_red = var_red
                    best_feat = f
                    best_thresh = float(t)

        if best_feat is None or best_var_red <= 1e-7:
            return PurePythonDecisionNode(value=float(np.mean(y)))

        left_mask = X[:, best_feat] <= best_thresh
        left_node = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_node = self._build_tree(X[~left_mask], y[~left_mask], depth + 1)
        return PurePythonDecisionNode(feature=best_feat, threshold=best_thresh, left=left_node, right=right_node)

    def predict_row(self, node: PurePythonDecisionNode, x: np.ndarray) -> float:
        if node.is_leaf:
            return node.value
        if x[node.feature] <= node.threshold:
            return self.predict_row(node.left, x)
        return self.predict_row(node.right, x)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self.predict_row(self.root, x) for x in X], dtype=float)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_depth': self.max_depth,
            'min_samples_split': self.min_samples_split,
            'root': self.root.to_dict() if self.root else None
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'PurePythonRegressionTree':
        tree = cls(max_depth=d.get('max_depth', 4), min_samples_split=d.get('min_samples_split', 2))
        tree.root = PurePythonDecisionNode.from_dict(d.get('root'))
        return tree

class PurePythonStandardScaler:
    def __init__(self):
        self.mean_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.var_: Optional[np.ndarray] = None
        self.n_features_in_: int = 0

    def fit(self, X: Union[np.ndarray, List[List[float]]]) -> 'PurePythonStandardScaler':
        X_arr = np.asarray(X, dtype=float)
        self.n_features_in_ = X_arr.shape[1]
        self.mean_ = np.mean(X_arr, axis=0)
        self.var_ = np.var(X_arr, axis=0)
        self.scale_ = np.sqrt(self.var_)
        self.scale_[self.scale_ < 1e-6] = 1.0
        return self

    def transform(self, X: Union[np.ndarray, List[List[float]]]) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        if self.mean_ is None or self.scale_ is None:
            return X_arr
        return (X_arr - self.mean_) / self.scale_

    def fit_transform(self, X: Union[np.ndarray, List[List[float]]]) -> np.ndarray:
        return self.fit(X).transform(X)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mean_': self.mean_.tolist() if self.mean_ is not None else None,
            'scale_': self.scale_.tolist() if self.scale_ is not None else None,
            'var_': self.var_.tolist() if self.var_ is not None else None,
            'n_features_in_': self.n_features_in_
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'PurePythonStandardScaler':
        scaler = cls()
        if d.get('mean_') is not None:
            scaler.mean_ = np.array(d['mean_'], dtype=float)
        if d.get('scale_') is not None:
            scaler.scale_ = np.array(d['scale_'], dtype=float)
        if d.get('var_') is not None:
            scaler.var_ = np.array(d['var_'], dtype=float)
        scaler.n_features_in_ = d.get('n_features_in_', 0)
        return scaler

class PurePythonGradientBoostingClassifier:
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.05,
        random_state: int = 42,
        classes: Optional[List[str]] = None
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.classes_ = np.array(classes if classes is not None else sorted(TARGET_CLASSES))
        self.n_classes_ = len(self.classes_)
        self.feature_names_in_: List[str] = list(FEATURE_NAMES_18)
        self.n_features_in_: int = len(self.feature_names_in_)
        self.init_logits_: Optional[np.ndarray] = None
        self.estimators_: List[List[PurePythonRegressionTree]] = []

    def fit(self, X: Union[np.ndarray, List[List[float]]], y: Union[np.ndarray, List[str], List[int]]) -> 'PurePythonGradientBoostingClassifier':
        X_arr = np.asarray(X, dtype=float)
        n_samples, n_features = X_arr.shape
        self.n_features_in_ = n_features

        y_raw = list(y)
        if isinstance(y_raw[0], str):
            y_indices = np.array([np.where(self.classes_ == label)[0][0] for label in y_raw], dtype=int)
        else:
            y_indices = np.asarray(y_raw, dtype=int)

        Y_onehot = np.zeros((n_samples, self.n_classes_), dtype=float)
        for i, idx in enumerate(y_indices):
            Y_onehot[i, idx] = 1.0

        class_counts = np.sum(Y_onehot, axis=0)
        class_priors = np.clip(class_counts / n_samples, 1e-5, 1.0 - 1e-5)
        self.init_logits_ = np.log(class_priors) - np.mean(np.log(class_priors))

        F = np.tile(self.init_logits_, (n_samples, 1))
        self.estimators_ = []

        for m in range(self.n_estimators):
            exp_F = np.exp(F - np.max(F, axis=1, keepdims=True))
            P = exp_F / np.sum(exp_F, axis=1, keepdims=True)

            trees_m = []
            for k in range(self.n_classes_):
                residuals = Y_onehot[:, k] - P[:, k]

                tree = PurePythonRegressionTree(max_depth=self.max_depth, min_samples_split=2)
                tree.fit(X_arr, residuals)

                h_k = tree.predict(X_arr)
                F[:, k] += self.learning_rate * h_k
                trees_m.append(tree)

            self.estimators_.append(trees_m)

        return self

    def _compute_logits(self, X: np.ndarray) -> np.ndarray:
        n_samples = len(X)
        if self.init_logits_ is None:
            F = np.zeros((n_samples, self.n_classes_), dtype=float)
        else:
            F = np.tile(self.init_logits_, (n_samples, 1))

        for trees_m in self.estimators_:
            for k in range(self.n_classes_):
                h_k = trees_m[k].predict(X)
                F[:, k] += self.learning_rate * h_k

        return F

    def predict_proba(self, X: Union[np.ndarray, List[List[float]]]) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        if len(X_arr.shape) == 1:
            X_arr = X_arr.reshape(1, -1)

        F = self._compute_logits(X_arr)
        exp_F = np.exp(F - np.max(F, axis=1, keepdims=True))
        probs = exp_F / np.sum(exp_F, axis=1, keepdims=True)
        probs = np.clip(probs, 1e-7, 1.0)
        probs = probs / np.sum(probs, axis=1, keepdims=True)
        return probs

    def predict(self, X: Union[np.ndarray, List[List[float]]]) -> np.ndarray:
        probs = self.predict_proba(X)
        best_indices = np.argmax(probs, axis=1)
        return self.classes_[best_indices]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'random_state': self.random_state,
            'classes_': self.classes_.tolist(),
            'feature_names_in_': self.feature_names_in_,
            'n_features_in_': self.n_features_in_,
            'init_logits_': self.init_logits_.tolist() if self.init_logits_ is not None else None,
            'estimators_': [
                [tree.to_dict() for tree in trees_m]
                for trees_m in self.estimators_
            ]
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'PurePythonGradientBoostingClassifier':
        clf = cls(
            n_estimators=d.get('n_estimators', 100),
            max_depth=d.get('max_depth', 4),
            learning_rate=d.get('learning_rate', 0.05),
            random_state=d.get('random_state', 42),
            classes=d.get('classes_')
        )
        clf.feature_names_in_ = d.get('feature_names_in_', list(FEATURE_NAMES_18))
        clf.n_features_in_ = d.get('n_features_in_', len(clf.feature_names_in_))
        if d.get('init_logits_') is not None:
            clf.init_logits_ = np.array(d['init_logits_'], dtype=float)

        clf.estimators_ = []
        for trees_m_data in d.get('estimators_', []):
            clf.estimators_.append([
                PurePythonRegressionTree.from_dict(tree_data)
                for tree_data in trees_m_data
            ])

        return clf

class PurePythonMLPipeline:
    def __init__(
        self,
        scaler: Optional[PurePythonStandardScaler] = None,
        classifier: Optional[PurePythonGradientBoostingClassifier] = None
    ):
        self.scaler = scaler if scaler is not None else PurePythonStandardScaler()
        self.classifier = classifier if classifier is not None else PurePythonGradientBoostingClassifier()

    @property
    def classes_(self) -> np.ndarray:
        return self.classifier.classes_

    @property
    def feature_names_in_(self) -> List[str]:
        return self.classifier.feature_names_in_

    def fit(self, X: Union[np.ndarray, List[List[float]]], y: Union[np.ndarray, List[str], List[int]]) -> 'PurePythonMLPipeline':
        X_arr = np.asarray(X, dtype=float)
        X_scaled = self.scaler.fit_transform(X_arr)
        self.classifier.fit(X_scaled, y)
        return self

    def predict_proba(self, X: Union[np.ndarray, List[List[float]]]) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X_arr)
        return self.classifier.predict_proba(X_scaled)

    def predict(self, X: Union[np.ndarray, List[List[float]]]) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X_arr)
        return self.classifier.predict(X_scaled)

    def save(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {
            'pipeline_version': '4F.13_CONTINUOUS_PROB',
            'scaler': self.scaler.to_dict(),
            'classifier': self.classifier.to_dict()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'PurePythonMLPipeline':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        scaler = PurePythonStandardScaler.from_dict(data['scaler'])
        classifier = PurePythonGradientBoostingClassifier.from_dict(data['classifier'])
        return cls(scaler=scaler, classifier=classifier)

if __name__ == '__main__':
    import shutil
    target = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'ml', 'gradient_boosting.py'))
    shutil.copyfile(__file__, target)
    print(f'Copied to {target}')
