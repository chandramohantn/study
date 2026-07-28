"""
Preprocessing Strategy — Protocol + concrete implementations.

The Protocol defines WHAT a preprocessing strategy must do.
Each implementation defines HOW it scales/transforms features differently.

All strategies are interchangeable: the pipeline doesn't know or care
which one it received. It just calls fit_transform() and transform().
"""

from typing import Protocol

import numpy as np


# ─────────────────────────────────────────────────────────────────────
# Protocol (the "interface" all strategies must satisfy)
# ─────────────────────────────────────────────────────────────────────


class PreprocessingStrategy(Protocol):
    """Any preprocessing strategy must implement these methods."""

    def fit(self, X: np.ndarray) -> None:
        """Learn parameters from training data (e.g., mean, std)."""
        ...

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply the learned transformation to data."""
        ...

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Convenience: fit + transform in one call."""
        ...


# ─────────────────────────────────────────────────────────────────────
# Strategy A: Standard Scaling (z-score normalization)
# ─────────────────────────────────────────────────────────────────────


class StandardScalerStrategy:
    """
    Scales features to zero mean and unit variance.
    Formula: X_scaled = (X - mean) / std

    Best when: features are roughly Gaussian, no extreme outliers.
    """

    def __init__(self):
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> None:
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        # Avoid division by zero for constant features
        self.std_[self.std_ == 0] = 1.0

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.mean_ is None:
            raise RuntimeError("Must call fit() before transform().")
        return (X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

    def __repr__(self) -> str:
        return "StandardScalerStrategy()"


# ─────────────────────────────────────────────────────────────────────
# Strategy B: Robust Scaling (median/IQR, outlier-resistant)
# ─────────────────────────────────────────────────────────────────────


class RobustScalerStrategy:
    """
    Scales features using median and interquartile range (IQR).
    Formula: X_scaled = (X - median) / IQR

    Best when: data has outliers that would skew mean/std.
    """

    def __init__(self):
        self.median_: np.ndarray | None = None
        self.iqr_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> None:
        self.median_ = np.median(X, axis=0)
        q75 = np.percentile(X, 75, axis=0)
        q25 = np.percentile(X, 25, axis=0)
        self.iqr_ = q75 - q25
        # Avoid division by zero for constant features
        self.iqr_[self.iqr_ == 0] = 1.0

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.median_ is None:
            raise RuntimeError("Must call fit() before transform().")
        return (X - self.median_) / self.iqr_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

    def __repr__(self) -> str:
        return "RobustScalerStrategy()"


# ─────────────────────────────────────────────────────────────────────
# Strategy C: No Scaling (pass-through)
# ─────────────────────────────────────────────────────────────────────


class NoScalingStrategy:
    """
    Does nothing — returns data as-is.

    Best when: data is already scaled, or you're using tree-based models
    that don't need scaling.
    """

    def fit(self, X: np.ndarray) -> None:
        pass  # Nothing to learn

    def transform(self, X: np.ndarray) -> np.ndarray:
        return X.copy()  # Return copy to match other strategies' behavior

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

    def __repr__(self) -> str:
        return "NoScalingStrategy()"


# ─────────────────────────────────────────────────────────────────────
# Registry: map config string -> strategy class
# ─────────────────────────────────────────────────────────────────────

PREPROCESSING_REGISTRY: dict[str, type] = {
    "standard": StandardScalerStrategy,
    "robust": RobustScalerStrategy,
    "none": NoScalingStrategy,
}


def create_preprocessing_strategy(name: str) -> "PreprocessingStrategy":
    """Create a preprocessing strategy by name (from config)."""
    if name not in PREPROCESSING_REGISTRY:
        available = ", ".join(PREPROCESSING_REGISTRY.keys())
        raise ValueError(
            f"Unknown preprocessing strategy: '{name}'. Available: {available}"
        )
    return PREPROCESSING_REGISTRY[name]()


