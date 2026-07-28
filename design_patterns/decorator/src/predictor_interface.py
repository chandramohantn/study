"""Predictor Protocol — the shared interface for core predictors and all decorators.

Every decorator and the core predictor must implement this same interface.
This is what makes stacking possible: each layer looks identical from the outside.
"""

from typing import Protocol

import numpy as np


class Predictor(Protocol):
    """Interface that all predictors (core and decorators) must satisfy.

    The structural Decorator pattern works because every layer shares
    the same interface. A caller cannot tell whether it's talking to
    the bare model or a stack of 5 decorators — that's the point.
    """

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Run prediction on a batch of feature vectors.

        Args:
            features: 2D array of shape (n_samples, n_features).

        Returns:
            1D array of predictions, shape (n_samples,).
        """
        ...


