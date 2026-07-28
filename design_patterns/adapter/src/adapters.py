"""
Adapter Pattern — Concrete Adapters

Each adapter wraps something with an INCOMPATIBLE interface and translates
it to the InferenceModel protocol your system expects.

SklearnAdapter  — wraps any fitted sklearn estimator
DictInputAdapter — accepts dict features, converts to ndarray before delegating
BatchAdapter    — normalizes single-sample vs batch-sample input shapes
"""

from typing import Any

import numpy as np


class SklearnAdapter:
    """Adapts any sklearn estimator to the InferenceModel protocol.

    Sklearn models already have predict() and predict_proba(), but:
    - They lack a model_name property
    - predict_proba() isn't guaranteed (e.g., SVC without probability=True)
    - We want a uniform error-handling layer

    This adapter bridges those gaps.
    """

    def __init__(self, model: Any, name: str | None = None) -> None:
        self._model = model
        self._name = name or type(model).__name__

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, features: np.ndarray) -> np.ndarray:
        return np.asarray(self._model.predict(features))

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if not hasattr(self._model, "predict_proba"):
            raise NotImplementedError(
                f"{self._name} does not support predict_proba. "
                "Consider using a classifier with probability=True."
            )
        return np.asarray(self._model.predict_proba(features))


class DictInputAdapter:
    """Adapts a model expecting ndarray to accept dict-based input.

    Real-world ML APIs often receive features as JSON dicts from HTTP
    requests. This adapter converts {"feature_a": 1.0, "feature_b": 2.0}
    into a numpy array in the correct column order, then delegates to the
    wrapped InferenceModel.
    """

    def __init__(self, model: Any, feature_order: list[str]) -> None:
        self._model = model
        self._feature_order = feature_order

    @property
    def model_name(self) -> str:
        return f"DictInput({self._model.model_name})"

    def _to_array(self, features: dict | list[dict]) -> np.ndarray:
        """Convert dict or list-of-dicts to a 2D numpy array."""
        if isinstance(features, dict):
            features = [features]
        rows = [[row[col] for col in self._feature_order] for row in features]
        return np.array(rows, dtype=np.float64)

    def predict(self, features: dict | list[dict]) -> np.ndarray:
        array = self._to_array(features)
        return self._model.predict(array)

    def predict_proba(self, features: dict | list[dict]) -> np.ndarray:
        array = self._to_array(features)
        return self._model.predict_proba(array)


class BatchAdapter:
    """Adapts a model to handle single-sample input gracefully.

    Many sklearn models expect 2D input (n_samples, n_features).
    If your caller sends a single 1D feature vector, this adapter
    reshapes it to (1, n_features), calls the model, and squeezes
    the output back to match.
    """

    def __init__(self, model: Any) -> None:
        self._model = model

    @property
    def model_name(self) -> str:
        return f"Batch({self._model.model_name})"

    def _ensure_2d(self, features: np.ndarray) -> tuple[np.ndarray, bool]:
        """Reshape to 2D if needed. Returns (array, was_single)."""
        if features.ndim == 1:
            return features.reshape(1, -1), True
        return features, False

    def predict(self, features: np.ndarray) -> np.ndarray:
        arr, was_single = self._ensure_2d(features)
        result = self._model.predict(arr)
        return result[0] if was_single else result

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        arr, was_single = self._ensure_2d(features)
        result = self._model.predict_proba(arr)
        return result[0] if was_single else result


