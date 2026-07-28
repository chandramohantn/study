"""
Adapter Pattern — Inference Service (Client Code)

This service depends ONLY on the InferenceModel protocol.
It doesn't know about sklearn, PyTorch, or any specific framework.
Swap adapters and it just works.
"""

import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from src.adapters import BatchAdapter, DictInputAdapter, SklearnAdapter
from src.model_interface import InferenceModel


class InferenceService:
    """Production-style inference service.

    Accepts ANY object satisfying InferenceModel — doesn't care
    whether it's sklearn, PyTorch, or a remote endpoint behind an adapter.
    """

    def __init__(self, model: InferenceModel) -> None:
        self._model = model

    def predict(self, features: np.ndarray) -> dict:
        """Run inference and return a structured response."""
        predictions = self._model.predict(features)
        return {
            "model": self._model.model_name,
            "predictions": predictions.tolist(),
            "count": len(predictions),
        }

    def predict_with_confidence(self, features: np.ndarray) -> dict:
        """Run inference with probability scores."""
        predictions = self._model.predict(features)
        probabilities = self._model.predict_proba(features)
        confidence = probabilities.max(axis=1)
        return {
            "model": self._model.model_name,
            "predictions": predictions.tolist(),
            "confidence": confidence.tolist(),
            "count": len(predictions),
        }

    def health_check(self) -> dict:
        """Verify model can serve predictions."""
        dummy = np.zeros((1, 4))
        try:
            self._model.predict(dummy)
            return {"status": "healthy", "model": self._model.model_name}
        except Exception as e:
            return {"status": "unhealthy", "model": self._model.model_name, "error": str(e)}


def _train_demo_models():
    """Train two different sklearn models on synthetic data."""
    X, y = make_classification(
        n_samples=200, n_features=4, n_informative=3,
        n_redundant=1, n_classes=2, random_state=42,
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X_train, y_train)

    lr = LogisticRegression(random_state=42)
    lr.fit(X_train, y_train)

    return rf, lr, X_test, y_test


if __name__ == "__main__":
    print("=" * 60)
    print("  ADAPTER PATTERN DEMO — ML Inference Service")
    print("=" * 60)

    rf_model, lr_model, X_test, y_test = _train_demo_models()
    sample = X_test[:5]

    # 1. SklearnAdapter
    print("\n── 1. SklearnAdapter ──")
    print("Same service, different models — zero code changes.\n")

    rf_adapter = SklearnAdapter(rf_model, name="RandomForest-v1")
    lr_adapter = SklearnAdapter(lr_model, name="LogisticRegression-v1")

    service_rf = InferenceService(rf_adapter)
    service_lr = InferenceService(lr_adapter)

    result_rf = service_rf.predict_with_confidence(sample)
    result_lr = service_lr.predict_with_confidence(sample)

    print(f"  RF predictions:  {result_rf['predictions']}")
    print(f"  RF confidence:   {[f'{c:.3f}' for c in result_rf['confidence']]}")
    print(f"  LR predictions:  {result_lr['predictions']}")
    print(f"  LR confidence:   {[f'{c:.3f}' for c in result_lr['confidence']]}")

    # 2. DictInputAdapter
    print("\n── 2. DictInputAdapter ──")
    print("Accepts JSON-style dicts (like an HTTP request body).\n")

    feature_names = ["feat_0", "feat_1", "feat_2", "feat_3"]
    dict_adapter = DictInputAdapter(rf_adapter, feature_order=feature_names)

    api_request = [
        {name: float(val) for name, val in zip(feature_names, row)}
        for row in sample[:3]
    ]
    print(f"  Input (dict):    {api_request[0]}")
    preds = dict_adapter.predict(api_request)
    print(f"  Predictions:     {preds.tolist()}")

    # 3. BatchAdapter
    print("\n── 3. BatchAdapter ──")
    print("Normalizes 1D single-sample input to 2D batch.\n")

    batch_adapter = BatchAdapter(rf_adapter)

    single_sample = X_test[0]  # shape (4,)
    print(f"  Input shape:     {single_sample.shape} (single sample)")
    single_pred = batch_adapter.predict(single_sample)
    print(f"  Prediction:      {single_pred}")

    batch_pred = batch_adapter.predict(sample)
    print(f"  Batch shape:     {sample.shape}")
    print(f"  Batch preds:     {batch_pred.tolist()}")

    # 4. Composed adapters
    print("\n── 4. Composed Adapters ──")
    print("BatchAdapter wrapping SklearnAdapter — adapters compose.\n")

    composed = BatchAdapter(SklearnAdapter(rf_model, name="RF-Composed"))
    service_composed = InferenceService(composed)

    health = service_composed.health_check()
    print(f"  Health check:    {health}")
    result = service_composed.predict(sample)
    print(f"  Model name:      {result['model']}")
    print(f"  Predictions:     {result['predictions']}")

    # 5. Protocol verification
    print("\n── 5. Protocol Verification ──")
    print(f"  SklearnAdapter satisfies InferenceModel? {isinstance(rf_adapter, InferenceModel)}")
    print(f"  BatchAdapter satisfies InferenceModel?   {isinstance(batch_adapter, InferenceModel)}")

    print("\n" + "=" * 60)
    print("  All adapters work with the SAME InferenceService.")
    print("  Add PyTorch? Write PyTorchAdapter. Service stays unchanged.")
    print("=" * 60)


