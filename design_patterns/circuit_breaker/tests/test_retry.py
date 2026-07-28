"""Tests for the retry decorator."""

import time
import sys
import os

import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.retry import retry


class TestRetryBasicBehavior:
    """Test that retry calls the function the right number of times."""

    def test_succeeds_on_first_try(self):
        """Function that succeeds immediately should only be called once."""
        mock_fn = MagicMock(return_value="ok")

        @retry(max_attempts=3, base_delay=0.01)
        def fn():
            return mock_fn()

        result = fn()
        assert result == "ok"
        assert mock_fn.call_count == 1

    def test_succeeds_on_second_try(self):
        """Function that fails once then succeeds should be called twice."""
        mock_fn = MagicMock(side_effect=[ConnectionError("fail"), "ok"])

        @retry(max_attempts=3, base_delay=0.01)
        def fn():
            return mock_fn()

        result = fn()
        assert result == "ok"
        assert mock_fn.call_count == 2

    def test_exhausts_all_attempts(self):
        """Function that always fails should raise after max_attempts."""
        mock_fn = MagicMock(side_effect=ConnectionError("always fails"))

        @retry(max_attempts=3, base_delay=0.01)
        def fn():
            return mock_fn()

        with pytest.raises(ConnectionError, match="always fails"):
            fn()

        assert mock_fn.call_count == 3

    def test_single_attempt(self):
        """With max_attempts=1, no retry should happen."""
        mock_fn = MagicMock(side_effect=ValueError("fail"))

        @retry(max_attempts=1, base_delay=0.01)
        def fn():
            return mock_fn()

        with pytest.raises(ValueError):
            fn()

        assert mock_fn.call_count == 1


class TestRetryExponentialBackoff:
    """Test that delays increase exponentially."""

    def test_backoff_timing(self):
        """Verify that delays increase between retries."""
        mock_fn = MagicMock(
            side_effect=[ConnectionError("1"), ConnectionError("2"), "ok"]
        )

        @retry(max_attempts=3, base_delay=0.05, backoff_factor=2.0)
        def fn():
            return mock_fn()

        start = time.time()
        result = fn()
        elapsed = time.time() - start

        assert result == "ok"
        # Attempt 1 fails -> wait 0.05s (0.05 * 2^0)
        # Attempt 2 fails -> wait 0.10s (0.05 * 2^1)
        # Attempt 3 succeeds
        # Total delay >= 0.15s
        assert elapsed >= 0.14
        assert elapsed < 1.0


class TestRetrySelectiveExceptions:
    """Test that only specified exceptions trigger retry."""

    def test_retries_only_specified_exceptions(self):
        """Non-retryable exceptions should propagate immediately."""
        mock_fn = MagicMock(side_effect=ValueError("not retryable"))

        @retry(
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError,),
        )
        def fn():
            return mock_fn()

        with pytest.raises(ValueError, match="not retryable"):
            fn()

        # Should only be called once — ValueError is not retryable
        assert mock_fn.call_count == 1

    def test_retries_matching_exception(self):
        """Retryable exceptions should trigger retry."""
        mock_fn = MagicMock(
            side_effect=[ConnectionError("transient"), "recovered"]
        )

        @retry(
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError,),
        )
        def fn():
            return mock_fn()

        result = fn()
        assert result == "recovered"
        assert mock_fn.call_count == 2


class TestRetryPreservesFunctionMetadata:
    """Test that the decorator preserves the original function's metadata."""

    def test_preserves_function_name(self):
        @retry(max_attempts=2, base_delay=0.01)
        def my_special_function():
            """My docstring."""
            pass

        assert my_special_function.__name__ == "my_special_function"
        assert my_special_function.__doc__ == "My docstring."

    def test_passes_arguments_through(self):
        """Arguments and kwargs should be passed to the wrapped function."""

        @retry(max_attempts=2, base_delay=0.01)
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2, extra=3) == 6


