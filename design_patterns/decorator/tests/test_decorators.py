"""Tests for each decorator in isolation.

Key principle: each decorator is tested with a FakePredictor (no real model needed).
This proves that decorators are truly independent — they don't care what's inside.
"""

import numpy as np
import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.decorators import (
    CachingDecorator,
    LoggingDecorator,
    TimingDecorator,
    ValidationDecorator,
)


# ─── Fake Predictor (test double) ────────────────────────────────────────────────


class FakePredictor:
    """A minimal predictor for testing. Returns predictable output."""

    def __init__(self, output: np.ndarray | None = None) -> None:
        self.call_count = 0
        self.last_input: np.ndarray | None = None
        self._output = output

    def predict(self, features: np.ndarray) -> np.ndarray:
        self.call_count += 1
        self.last_input = features
        if self._output is not None:
            return self._output.copy()
        return np.zeros(features.shape[0])


# ─── ValidationDecorator Tests ───────────────────────────────────────────────────


class TestValidationDecorator:
    """Validation can be tested without any model or other decorators."""

    def setup_method(self):
        self.inner = FakePredictor()
        self.validator = ValidationDecorator(self.inner, expected_features=5)

    def test_passes_valid_input(self):
        valid = np.random.randn(3, 5)
        result = self.validator.predict(valid)
        assert result.shape == (3,)
        assert self.inner.call_count == 1

    def test_rejects_wrong_feature_count(self):
        wrong = np.random.randn(3, 8)
        with pytest.raises(ValueError, match="Expected 5 features, got 8"):
            self.validator.predict(wrong)
        assert self.inner.call_count == 0  # Model never called

    def test_rejects_1d_input(self):
        flat = np.random.randn(5)
        with pytest.raises(ValueError, match="Expected 2D array, got 1D"):
            self.validator.predict(flat)

    def test_rejects_nan(self):
        data = np.random.randn(3, 5)
        data[1, 2] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            self.validator.predict(data)

    def test_rejects_inf(self):
        data = np.random.randn(3, 5)
        data[0, 4] = np.inf
        with pytest.raises(ValueError, match="Inf"):
            self.validator.predict(data)

    def test_nan_reports_column_indices(self):
        data = np.random.randn(3, 5)
        data[0, 1] = np.nan
        data[2, 3] = np.nan
        with pytest.raises(ValueError, match=r"\[1, 3\]"):
            self.validator.predict(data)


# ─── TimingDecorator Tests ───────────────────────────────────────────────────────


class TestTimingDecorator:
    """Timing can be tested without real model — just measures elapsed time."""

    def setup_method(self):
        self.inner = FakePredictor()
        self.timed = TimingDecorator(self.inner)

    def test_records_latency(self):
        data = np.random.randn(5, 3)
        self.timed.predict(data)
        assert self.timed.last_latency_ms > 0

    def test_tracks_call_count(self):
        data = np.random.randn(5, 3)
        self.timed.predict(data)
        self.timed.predict(data)
        self.timed.predict(data)
        assert self.timed.total_calls == 3

    def test_avg_latency(self):
        data = np.random.randn(5, 3)
        self.timed.predict(data)
        self.timed.predict(data)
        assert self.timed.avg_latency_ms > 0
        assert self.timed.avg_latency_ms == self.timed.total_time_ms / 2

    def test_delegates_to_inner(self):
        data = np.random.randn(5, 3)
        result = self.timed.predict(data)
        assert self.inner.call_count == 1
        assert np.array_equal(result, np.zeros(5))


# ─── CachingDecorator Tests ──────────────────────────────────────────────────────


class TestCachingDecorator:
    """Caching tested independently — proves cache logic works without a model."""

    def setup_method(self):
        self.inner = FakePredictor(output=np.array([1, 0, 1]))
        self.cached = CachingDecorator(self.inner, max_size=3)

    def test_first_call_is_miss(self):
        data = np.array([[1.0, 2.0, 3.0]])
        self.cached.predict(data)
        assert self.cached.misses == 1
        assert self.cached.hits == 0
        assert self.inner.call_count == 1

    def test_second_same_call_is_hit(self):
        data = np.array([[1.0, 2.0, 3.0]])
        self.cached.predict(data)
        self.cached.predict(data)
        assert self.cached.hits == 1
        assert self.inner.call_count == 1  # Model called only once

    def test_different_input_is_miss(self):
        self.cached.predict(np.array([[1.0, 2.0, 3.0]]))
        self.cached.predict(np.array([[4.0, 5.0, 6.0]]))
        assert self.cached.misses == 2
        assert self.inner.call_count == 2

    def test_hit_rate(self):
        data = np.array([[1.0, 2.0, 3.0]])
        self.cached.predict(data)  # miss
        self.cached.predict(data)  # hit
        self.cached.predict(data)  # hit
        assert self.cached.hit_rate == pytest.approx(2 / 3)

    def test_lru_eviction(self):
        # Fill cache (max_size=3)
        self.cached.predict(np.array([[1.0, 1.0, 1.0]]))
        self.cached.predict(np.array([[2.0, 2.0, 2.0]]))
        self.cached.predict(np.array([[3.0, 3.0, 3.0]]))
        # This should evict the first entry
        self.cached.predict(np.array([[4.0, 4.0, 4.0]]))
        # First entry should be a miss now
        self.cached.predict(np.array([[1.0, 1.0, 1.0]]))
        assert self.cached.misses == 5  # All unique + re-request of evicted

    def test_clear_resets_stats(self):
        data = np.array([[1.0, 2.0, 3.0]])
        self.cached.predict(data)
        self.cached.clear()
        assert self.cached.hits == 0
        assert self.cached.misses == 0
        assert self.cached.hit_rate == 0.0

    def test_cached_result_is_copy(self):
        """Mutating cached result should not corrupt the cache."""
        data = np.array([[1.0, 2.0, 3.0]])
        result1 = self.cached.predict(data)
        result1[0] = 999  # Mutate
        result2 = self.cached.predict(data)  # Should still be [1, 0, 1]
        assert np.array_equal(result2, np.array([1, 0, 1]))


# ─── LoggingDecorator Tests ──────────────────────────────────────────────────────


class TestLoggingDecorator:
    """Logging tested independently — just verify it delegates correctly."""

    def setup_method(self):
        self.inner = FakePredictor(output=np.array([0, 1, 0]))
        self.logged = LoggingDecorator(self.inner)

    def test_delegates_and_returns_result(self):
        data = np.random.randn(3, 5)
        result = self.logged.predict(data)
        assert np.array_equal(result, np.array([0, 1, 0]))
        assert self.inner.call_count == 1

    def test_logs_are_emitted(self, caplog):
        data = np.random.randn(3, 5)
        with caplog.at_level("INFO"):
            self.logged.predict(data)
        assert "Input shape: (3, 5)" in caplog.text
        assert "Output shape: (3,)" in caplog.text


# ─── Integration: Stacking Tests ─────────────────────────────────────────────────


class TestStacking:
    """Prove that any combination of decorators produces correct results."""

    def test_all_decorators_stacked(self):
        inner = FakePredictor(output=np.array([1, 0, 1]))
        stack = ValidationDecorator(inner, expected_features=3)
        stack = CachingDecorator(stack, max_size=10)
        stack = TimingDecorator(stack)
        stack = LoggingDecorator(stack)

        data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
        result = stack.predict(data)
        assert np.array_equal(result, np.array([1, 0, 1]))

    def test_order_independence_of_result(self):
        """Core result is the same regardless of decorator order."""
        inner1 = FakePredictor(output=np.array([1, 1, 0]))
        inner2 = FakePredictor(output=np.array([1, 1, 0]))

        # Order A: Validation -> Timing -> Logging
        stack_a = ValidationDecorator(inner1, expected_features=4)
        stack_a = TimingDecorator(stack_a)
        stack_a = LoggingDecorator(stack_a)

        # Order B: Timing -> Validation -> Logging
        stack_b = TimingDecorator(inner2)
        stack_b = ValidationDecorator(stack_b, expected_features=4)
        stack_b = LoggingDecorator(stack_b)

        data = np.random.randn(3, 4)
        assert np.array_equal(stack_a.predict(data), stack_b.predict(data))


