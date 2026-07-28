"""Tests for circuit breaker state transitions."""

import time
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerClosed:
    """Tests for CLOSED state behavior."""

    def test_starts_in_closed_state(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    def test_allows_requests_when_closed(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        assert cb.allow_request() is True

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0


class TestCircuitBreakerTransitionToOpen:
    """Tests for CLOSED -> OPEN transition."""

    def test_opens_at_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_blocks_requests_when_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=60)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False


class TestCircuitBreakerHalfOpen:
    """Tests for OPEN -> HALF_OPEN transition."""

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(
            name="test", failure_threshold=2, recovery_timeout=0.1
        )
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Next allow_request call should transition to HALF_OPEN
        assert cb.allow_request() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_does_not_transition_before_timeout(self):
        cb = CircuitBreaker(
            name="test", failure_threshold=2, recovery_timeout=10.0
        )
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerRecovery:
    """Tests for HALF_OPEN -> CLOSED and HALF_OPEN -> OPEN transitions."""

    def _make_half_open_breaker(self) -> CircuitBreaker:
        """Helper: create a breaker in HALF_OPEN state."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.05,
            success_threshold=2,
        )
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.06)
        cb.allow_request()  # triggers transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
        return cb

    def test_closes_after_enough_successes(self):
        cb = self._make_half_open_breaker()
        cb.record_success()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_reopens_on_failure_in_half_open(self):
        cb = self._make_half_open_breaker()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_needs_all_successes_to_close(self):
        """One success isn't enough if threshold is 2."""
        cb = self._make_half_open_breaker()
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN
        # Still needs one more success
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerReset:
    """Tests for manual reset."""

    def test_reset_from_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.allow_request() is True


