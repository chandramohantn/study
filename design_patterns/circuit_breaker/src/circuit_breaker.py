"""
Circuit Breaker Pattern
========================

Prevents cascading failures by short-circuiting calls to unhealthy services.

State Machine:
    CLOSED  ──(failure_threshold reached)──>  OPEN
    OPEN    ──(recovery_timeout elapsed)───>  HALF_OPEN
    HALF_OPEN ──(success)──────────────────>  CLOSED
    HALF_OPEN ──(failure)──────────────────>  OPEN

Use cases for ML engineers:
- Protect inference pipelines from a failing model API
- Prevent ETL jobs from hammering a dead feature store
- Gracefully degrade when a dependency is down
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """The three states of a circuit breaker."""
    CLOSED = "CLOSED"        # Normal operation — requests pass through
    OPEN = "OPEN"            # Failing — requests are blocked immediately
    HALF_OPEN = "HALF_OPEN"  # Testing — allow one request to probe health


@dataclass
class CircuitBreaker:
    """
    A simple circuit breaker implementation.

    Args:
        name: Identifier for this breaker (used in logs).
        failure_threshold: Number of consecutive failures to trip the breaker.
        recovery_timeout: Seconds to wait in OPEN state before transitioning to HALF_OPEN.
        success_threshold: Consecutive successes in HALF_OPEN to close the circuit.

    Usage:
        breaker = CircuitBreaker(name="model-api", failure_threshold=3, recovery_timeout=30)

        if not breaker.allow_request():
            return fallback_response()

        try:
            result = call_service()
            breaker.record_success()
            return result
        except Exception:
            breaker.record_failure()
            raise
    """

    name: str = "default"
    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds
    success_threshold: int = 2  # successes needed in HALF_OPEN to close

    # Internal state (managed automatically)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    failure_count: int = field(default=0, init=False)
    success_count: int = field(default=0, init=False)
    last_failure_time: Optional[float] = field(default=None, init=False)

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed through.

        Returns:
            True if the request can proceed, False if it should be blocked.
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self._recovery_timeout_elapsed():
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow requests through in HALF_OPEN (we're probing)
            return True

        return False

    def record_success(self) -> None:
        """Record a successful call. May close the circuit if in HALF_OPEN."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"[CircuitBreaker:{self.name}] Success in HALF_OPEN "
                f"({self.success_count}/{self.success_threshold})"
            )
            if self.success_count >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call. May open the circuit."""
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN sends us back to OPEN
            logger.warning(
                f"[CircuitBreaker:{self.name}] Failure in HALF_OPEN — reopening circuit"
            )
            self._transition_to(CircuitState.OPEN)

        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            logger.warning(
                f"[CircuitBreaker:{self.name}] Failure "
                f"{self.failure_count}/{self.failure_threshold}"
            )
            if self.failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        self._transition_to(CircuitState.CLOSED)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state, resetting relevant counters."""
        old_state = self.state
        self.state = new_state

        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0
        elif new_state == CircuitState.OPEN:
            self.success_count = 0

        logger.info(
            f"[CircuitBreaker:{self.name}] {old_state.value} -> {new_state.value}"
        )

    def _recovery_timeout_elapsed(self) -> bool:
        """Check if enough time has passed since the last failure."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout


