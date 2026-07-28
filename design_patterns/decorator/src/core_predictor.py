"""Core predictor — the innermost layer that actually runs the ML model.

This class does ONE thing: delegate to the sklearn model's predict method.
All cross-cutting concerns (logging, timing, caching, validation) live in decorators.
"""

import numpy as np


class ModelPredictor:
    """Wraps a trained sklearn model. Does nothing but call model.predict().

    This is the "Component" in Decorator pattern terminology — the real object
    that all the decorators ultimately delegate to.
    """

    def __init__(self, model) -> None:
        """
        Args:
            model: A trained sklearn estimator with a .predict() method
                   (e.g., RandomForestClassifier, GradientBoostingRegressor).
        """
        self._model = model

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Run model inference. No frills, no side effects."""
        return self._model.predict(features)


