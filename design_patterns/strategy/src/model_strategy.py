"""
Model Strategy — Protocol + concrete implementations.

Each model strategy wraps a sklearn classifier with the same interface.
The pipeline doesn't care which model it trains — it just calls fit() and predict().

All strategies use sklearn only, so no extra dependencies needed.
"""

from typing import Protocol

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression


# ─────────────────────────────────────────────────────────────────────
# Protocol (the "interface" all model strategies must satisfy)
# ─────────────────────────────────────────────────────────────────────


class ModelStrategy(Protocol):
    """Any model strategy must implement these methods."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the model on labeled data."""
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions for new data."""
        ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate probability estimates (for metrics like AUC)."""
        ...


# ─────────────────────────────────────────────────────────────────────
# Strategy A: Logistic Regression (fast baseline)
# ─────────────────────────────────────────────────────────────────────


class LogisticRegressionStrategy:
    """
    Linear model — fast, interpretable, good baseline.

    Best when: you need a quick baseline, features are well-engineered,
    or you need model interpretability (coefficients).
    """

    def __init__(self, C: float = 1.0, max_iter: int = 1000):
        self.C = C
        self.max_iter = max_iter
        self._model = LogisticRegression(C=self.C, max_iter=self.max_iter)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)

    def __repr__(self) -> str:
        return f"LogisticRegressionStrategy(C={self.C})"


# ─────────────────────────────────────────────────────────────────────
# Strategy B: Random Forest (ensemble of trees)
# ─────────────────────────────────────────────────────────────────────


class RandomForestStrategy:
    """
    Ensemble of decision trees — robust, handles non-linearity.

    Best when: you want decent performance without much tuning,
    features have non-linear relationships, or you need feature importances.
    """

    def __init__(self, n_estimators: int = 100, max_depth: int | None = None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self._model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=42,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)

    def __repr__(self) -> str:
        return f"RandomForestStrategy(n_estimators={self.n_estimators})"


# ─────────────────────────────────────────────────────────────────────
# Strategy C: Gradient Boosting (sequential ensemble)
# ─────────────────────────────────────────────────────────────────────


class GradientBoostingStrategy:
    """
    Sequential boosting — builds trees that correct previous errors.

    Best when: you want strong performance and can afford slower training.
    Similar in spirit to XGBoost/LightGBM but uses sklearn only.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 3,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self._model = GradientBoostingClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_state=42,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)

    def __repr__(self) -> str:
        return (
            f"GradientBoostingStrategy("
            f"n_estimators={self.n_estimators}, "
            f"lr={self.learning_rate})"
        )


# ─────────────────────────────────────────────────────────────────────
# Registry: map config string -> strategy class + default params
# ─────────────────────────────────────────────────────────────────────

MODEL_REGISTRY: dict[str, type] = {
    "logistic_regression": LogisticRegressionStrategy,
    "random_forest": RandomForestStrategy,
    "gradient_boosting": GradientBoostingStrategy,
}


def create_model_strategy(name: str, **kwargs) -> "ModelStrategy":
    """
    Create a model strategy by name (from config).

    Args:
        name: Key from MODEL_REGISTRY
        **kwargs: Hyperparameters passed to the strategy constructor

    Example:
        model = create_model_strategy("random_forest", n_estimators=200)
    """
    if name not in MODEL_REGISTRY:
        available = ", ".join(MODEL_REGISTRY.keys())
        raise ValueError(
            f"Unknown model strategy: '{name}'. Available: {available}"
        )
    return MODEL_REGISTRY[name](**kwargs)


