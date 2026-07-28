"""
Retry Decorator with Exponential Backoff
=========================================

A simple, standalone retry decorator useful for:
- Calling flaky external APIs (feature stores, model endpoints)
- Handling transient network errors in ETL pipelines
- Retrying failed model inference requests

Usage:
    @retry(max_attempts=3, base_delay=1.0, backoff_factor=2.0)
    def call_model_api(payload):
        ...
"""

import time
import functools
import logging
from typing import Tuple, Type

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including the first call).
        base_delay: Initial delay in seconds between retries.
        backoff_factor: Multiplier applied to delay after each retry.
                        delay = base_delay * (backoff_factor ** attempt_number)
        retryable_exceptions: Tuple of exception types that trigger a retry.
                              Non-matching exceptions propagate immediately.

    Returns:
        Decorated function that retries on failure.

    Example:
        @retry(max_attempts=3, base_delay=0.5, backoff_factor=2.0)
        def fetch_features(user_id):
            response = requests.get(f"http://feature-store/users/{user_id}")
            response.raise_for_status()
            return response.json()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"[Retry] {func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    return result

                except retryable_exceptions as e:
                    last_exception = e
                    # Don't sleep after the last attempt
                    if attempt < max_attempts - 1:
                        delay = base_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"[Retry] {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): "
                            f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[Retry] {func.__name__} failed after {max_attempts} attempts: "
                            f"{type(e).__name__}: {e}"
                        )

            # All attempts exhausted — raise the last exception
            raise last_exception

        return wrapper

    return decorator


