"""Decorator classes — each adds exactly ONE cross-cutting concern.

Each decorator:
  1. Implements the same Predictor interface
  2. Wraps another Predictor (could be core or another decorator)
  3. Adds behavior before/after delegating to the wrapped predictor

Stack order matters:
  - Outer layers execute first on the way in
  - Inner layers execute first on the way out
  - Think of it like middleware in a web framework
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict

import numpy as np

from .predictor_interface import Predictor

logger = logging.getLogger(__name__)


class LoggingDecorator:
    """Logs prediction requests and results. Useful for debugging and auditing."""

    def __init__(self, wrapped: Predictor, log_level: int = logging.INFO) -> None:
        self._wrapped = wrapped
        self._log_level = log_level

    def predict(self, features: np.ndarray) -> np.ndarray:
        logger.log(
            self._log_level,
            f"[Predict] Input shape: {features.shape}, dtype: {features.dtype}",
        )
        result = self._wrapped.predict(features)
        logger.log(
            self._log_level,
            f"[Predict] Output shape: {result.shape}, "
            f"unique values: {np.unique(result).tolist()}",
        )
        return result


class TimingDecorator:
    """Measures prediction latency. Exposes last_latency_ms for monitoring."""

    def __init__(self, wrapped: Predictor) -> None:
        self._wrapped = wrapped
        self.last_latency_ms: float = 0.0
        self.total_calls: int = 0
        self.total_time_ms: float = 0.0

    def predict(self, features: np.ndarray) -> np.ndarray:
        start = time.perf_counter()
        result = self._wrapped.predict(features)
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.last_latency_ms = elapsed_ms
        self.total_calls += 1
        self.total_time_ms += elapsed_ms
        return result

    @property
    def avg_latency_ms(self) -> float:
        """Average latency across all calls."""
        return self.total_time_ms / self.total_calls if self.total_calls > 0 else 0.0


class ValidationDecorator:
    """Validates input before it reaches the model. Fails fast on bad data.

    In ML pipelines, garbage-in-garbage-out is the #1 production issue.
    This decorator catches malformed inputs at the boundary.
    """

    def __init__(self, wrapped: Predictor, expected_features: int) -> None:
        self._wrapped = wrapped
        self._expected_features = expected_features

    def predict(self, features: np.ndarray) -> np.ndarray:
        if features.ndim != 2:
            raise ValueError(
                f"Expected 2D array, got {features.ndim}D. "
                f"Reshape with features.reshape(1, -1) for single sample."
            )

        if features.shape[1] != self._expected_features:
            raise ValueError(
                f"Expected {self._expected_features} features, "
                f"got {features.shape[1]}. Check your feature pipeline."
            )

        if np.any(np.isnan(features)):
            nan_cols = np.where(np.any(np.isnan(features), axis=0))[0]
            raise ValueError(
                f"Input contains NaN values in columns: {nan_cols.tolist()}"
            )

        if np.any(np.isinf(features)):
            inf_cols = np.where(np.any(np.isinf(features), axis=0))[0]
            raise ValueError(
                f"Input contains Inf values in columns: {inf_cols.tolist()}"
            )

        return self._wrapped.predict(features)


class CachingDecorator:
    """Caches predictions by input hash. LRU eviction when full.

    Useful for:
    - API endpoints receiving repeated requests
    - Feature stores where same entity is queried multiple times
    - A/B testing where same user hits the model repeatedly
    """

    def __init__(self, wrapped: Predictor, max_size: int = 1000) -> None:
        self._wrapped = wrapped
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._max_size = max_size
        self.hits: int = 0
        self.misses: int = 0

    def predict(self, features: np.ndarray) -> np.ndarray:
        cache_key = self._compute_key(features)

        if cache_key in self._cache:
            self.hits += 1
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key].copy()

        self.misses += 1
        result = self._wrapped.predict(features)

        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[cache_key] = result.copy()
        return result

    @property
    def hit_rate(self) -> float:
        """Fraction of calls served from cache."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def clear(self) -> None:
        """Flush the cache (e.g., after model retrain)."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _compute_key(features: np.ndarray) -> str:
        """Hash the input array for cache lookup."""
        return hashlib.md5(features.tobytes()).hexdigest()


