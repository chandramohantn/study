"""
Adapter Pattern — Target Interface (Protocol)

This defines what YOUR system expects every model to look like.
Any model — sklearn, PyTorch, ONNX, remote endpoint — must be adapted
to this interface before your inference service can use it.
"""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class InferenceModel(Protocol):
    """Unified interface that all model adapters must satisfy.

    Your inference service codes against THIS — never against a specific
    ML framework. When a new framework arrives, you write an adapter,
    not modify the service.
    """

    @property
    def model_name(self) -> str:
        """Human-readable identifier for logging/monitoring."""
        ...

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Return class predictions (or regression values).

        Args:
            features: 2D array of shape (n_samples, n_features).

        Returns:
            1D array of shape (n_samples,) with predictions.
        """
        ...

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return probability estimates for each class.

        Args:
            features: 2D array of shape (n_samples, n_features).

        Returns:
            2D array of shape (n_samples, n_classes) with probabilities.
        """
        ...


