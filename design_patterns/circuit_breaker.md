# Circuit Breaker + Retry with Back-off

## The One-Line Summary

**External services fail. Retry for blips, stop hammering when it's dead.**

---

## The Problem

Your ML inference service calls three external services:
1. Feature store (Redis) to get user features
2. Model API (SageMaker) for prediction
3. Database (PostgreSQL) to log results

What happens when the feature store goes down?

```python
# ❌ WITHOUT CIRCUIT BREAKER — Cascading failure

def get_prediction(user_id: str):
    # Feature store is DOWN — each call hangs for 30s timeout
    features = requests.get(f"http://feature-store/users/{user_id}", timeout=30)
    # ...
```

**The cascade:**
1. Feature store is down → every request waits 30 seconds
2. You have 100 requests/sec → 3000 requests pile up waiting
3. Your thread pool exhausts → your service stops responding
4. Downstream services that depend on YOU also start failing
5. **One service being down takes your entire system down**

---

## The Solution: Two Complementary Patterns

### Retry with Back-off

**For transient failures** (network blip, service restarting, momentary overload):
- Try again after a short delay
- Increase the delay each time (exponential back-off)
- Give up after N attempts

### Circuit Breaker

**For sustained failures** (service is actually DOWN):
- After N consecutive failures, STOP trying
- Immediately reject requests (fast-fail) instead of waiting
- Periodically test if the service recovered
- Resume normal operation when it's back

---

## Is This a "Design Pattern" Like Strategy/Adapter?

**Yes, but it's a different category.** Strategy and Adapter are *structural* patterns (how you organize code). Circuit Breaker is a *resilience* pattern (how you handle failure).

The design pattern here is the **State Machine**:

```
States: CLOSED → OPEN → HALF_OPEN → (back to CLOSED or OPEN)

CLOSED   = "Normal. Let requests through. Count failures."
OPEN     = "Service is dead. Reject requests immediately. Wait for timeout."
HALF_OPEN = "Let ONE request through to test. If it works → CLOSED. If not → OPEN."
```

**You DO use Protocols/interfaces** — the pattern works best when you define clear contracts:

```python
from typing import Protocol


class RetryPolicy(Protocol):
    """Strategy pattern INSIDE circuit breaker — pluggable retry behavior."""
    def should_retry(self, attempt: int, error: Exception) -> bool: ...
    def get_delay(self, attempt: int) -> float: ...


class CircuitBreakerPolicy(Protocol):
    """Configurable circuit breaker behavior."""
    def should_open(self, failure_count: int) -> bool: ...
    def should_try_half_open(self, time_since_open: float) -> bool: ...
```

---

## Simplified Implementation

The previous implementation was complex because it combined everything. Let me break it into **clear, simple pieces**:

### Part 1: Retry with Back-off (Standalone)

```python
import time
import random
from typing import TypeVar, Callable
from functools import wraps

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Simple retry decorator with exponential back-off.
    
    This is the pattern you'll use 90% of the time.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise  # Last attempt — give up

                    # Exponential back-off with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay *= 0.5 + random.random()  # Jitter: prevent thundering herd

                    print(f"  Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)

        return wrapper
    return decorator


# ─── Usage ───

@retry(max_attempts=3, base_delay=1.0, exceptions=(ConnectionError, TimeoutError))
def fetch_features(user_id: str) -> dict:
    """This function will automatically retry on network errors."""
    import requests
    response = requests.get(f"http://feature-store/users/{user_id}", timeout=5)
    response.raise_for_status()
    return response.json()


# What happens:
# Attempt 1: ConnectionError → wait ~1s
# Attempt 2: ConnectionError → wait ~2s  
# Attempt 3: Success! → return result
# (or Attempt 3: fails → raise exception to caller)
```

### Part 2: Circuit Breaker (Standalone)

```python
import time
from enum import Enum
from dataclasses import dataclass, field


class State(Enum):
    CLOSED = "closed"        # Normal — requests pass through
    OPEN = "open"            # Dead — reject immediately
    HALF_OPEN = "half_open"  # Testing — allow one request


@dataclass
class CircuitBreaker:
    """
    Simple Circuit Breaker.
    
    Usage:
        breaker = CircuitBreaker(name="feature-store", failure_threshold=5)
        
        if breaker.allow_request():
            try:
                result = call_service()
                breaker.record_success()
            except Exception:
                breaker.record_failure()
        else:
            # Circuit is open — use fallback
            result = fallback_value
    """
    name: str
    failure_threshold: int = 5         # Failures before opening
    recovery_timeout: float = 30.0     # Seconds before testing recovery

    # Internal state
    _state: State = field(default=State.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)

    @property
    def state(self) -> State:
        # Auto-transition: OPEN → HALF_OPEN after timeout
        if self._state == State.OPEN:
            if time.time() - self._opened_at >= self.recovery_timeout:
                self._state = State.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        """Should we let this request through?"""
        return self.state != State.OPEN

    def record_success(self) -> None:
        """Call after a successful request."""
        self._failure_count = 0
        if self._state == State.HALF_OPEN:
            self._state = State.CLOSED
            print(f"  ✅ Circuit '{self.name}' CLOSED (recovered)")

    def record_failure(self) -> None:
        """Call after a failed request."""
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = State.OPEN
            self._opened_at = time.time()
            print(f"  🔴 Circuit '{self.name}' OPEN (threshold reached)")
        elif self._state == State.HALF_OPEN:
            self._state = State.OPEN
            self._opened_at = time.time()
            print(f"  🔴 Circuit '{self.name}' OPEN (failed in half-open)")
```

### Part 3: Using Them Together

```python
class ResilientService:
    """
    Clean combination: Circuit Breaker guards the outer call,
    Retry handles transient failures within.
    
    This is how it's used in production.
    """

    def __init__(self):
        self.feature_store_breaker = CircuitBreaker(
            name="feature-store", failure_threshold=5, recovery_timeout=30
        )
        self.model_api_breaker = CircuitBreaker(
            name="model-api", failure_threshold=3, recovery_timeout=15
        )

    def get_features(self, user_id: str) -> dict:
        """Get features with circuit breaker + retry."""

        # 1. Check circuit breaker FIRST (fast-fail if service is known to be down)
        if not self.feature_store_breaker.allow_request():
            print(f"  ⚡ Circuit OPEN — using fallback features")
            return self._default_features(user_id)

        # 2. Try the call with retry
        try:
            result = self._fetch_features_with_retry(user_id)
            self.feature_store_breaker.record_success()
            return result
        except Exception as e:
            self.feature_store_breaker.record_failure()
            print(f"  ⚠️ Feature store failed: {e} — using fallback")
            return self._default_features(user_id)

    @retry(max_attempts=2, base_delay=0.5, exceptions=(ConnectionError, TimeoutError))
    def _fetch_features_with_retry(self, user_id: str) -> dict:
        """The actual network call — retried automatically."""
        import requests
        response = requests.get(
            f"http://feature-store/users/{user_id}",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def _default_features(self, user_id: str) -> dict:
        """Fallback when service is down — return safe defaults."""
        return {"user_id": user_id, "risk_score": 0.5, "source": "fallback"}
```

---

## Industry Approach

**Is the decorator approach used in industry?** Yes, but production systems typically use libraries:

| Library | Language | Notes |
|---------|----------|-------|
| `tenacity` | Python | Most popular retry library. Production-ready. |
| `pybreaker` | Python | Circuit breaker implementation. |
| `circuitbreaker` | Python | Another circuit breaker library. |
| Resilience4j | Java | Gold standard for JVM. |
| Polly | .NET | Widely used in .NET ecosystem. |

### Using `tenacity` (Production Recommendation)

```python
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)
import logging

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def fetch_features(user_id: str) -> dict:
    """Production retry with tenacity — battle-tested library."""
    import requests
    response = requests.get(f"http://feature-store/users/{user_id}", timeout=5)
    response.raise_for_status()
    return response.json()
```

### Using `pybreaker` (Production Recommendation)

```python
import pybreaker

# Create a circuit breaker
feature_store_breaker = pybreaker.CircuitBreaker(
    fail_max=5,           # Open after 5 failures
    reset_timeout=30,     # Try half-open after 30s
    name="feature-store",
)


@feature_store_breaker
def fetch_features(user_id: str) -> dict:
    """Calls wrapped by circuit breaker — auto state management."""
    import requests
    response = requests.get(f"http://feature-store/users/{user_id}", timeout=5)
    response.raise_for_status()
    return response.json()


# Catch the circuit breaker open error
try:
    features = fetch_features("user_123")
except pybreaker.CircuitBreakerError:
    features = default_features()  # Fallback
```

---

## The Design Pattern Structure

Even though Circuit Breaker looks different from Strategy/Adapter, it uses the same principles:

```python
from typing import Protocol


# ─── The Protocols (interfaces) in Circuit Breaker ───

class RetryPolicy(Protocol):
    """Pluggable retry strategy — this IS the Strategy pattern inside Circuit Breaker!"""
    def should_retry(self, attempt: int, error: Exception) -> bool: ...
    def get_delay(self, attempt: int) -> float: ...


class FallbackStrategy(Protocol):
    """What to do when the service is down — also a Strategy!"""
    def get_fallback(self, *args, **kwargs): ...


class CircuitBreakerListener(Protocol):
    """Observer pattern — get notified on state changes."""
    def on_state_change(self, old_state: str, new_state: str) -> None: ...
    def on_failure(self, error: Exception) -> None: ...


# ─── Implementations ───

class ExponentialBackoff:
    """Satisfies RetryPolicy Protocol."""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def should_retry(self, attempt: int, error: Exception) -> bool:
        return attempt < self.max_retries

    def get_delay(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)


class CachedFallback:
    """Satisfies FallbackStrategy — return cached value when service is down."""
    def __init__(self, cache: dict):
        self._cache = cache

    def get_fallback(self, key: str) -> dict:
        return self._cache.get(key, {"source": "fallback"})


class MetricsListener:
    """Satisfies CircuitBreakerListener — logs metrics on state changes."""
    def on_state_change(self, old_state: str, new_state: str) -> None:
        print(f"📊 Circuit: {old_state} → {new_state}")

    def on_failure(self, error: Exception) -> None:
        print(f"📊 Failure recorded: {error}")
```

---

## When to Use

| Situation | Use Retry | Use Circuit Breaker | Use Both |
|-----------|-----------|--------------------:|----------|
| Network blips (rare, transient) | ✅ | ❌ | ❌ |
| Service overloaded temporarily | ✅ | ❌ | ✅ |
| Service completely down | ❌ | ✅ | ✅ |
| Database connection pool exhausted | ✅ | ✅ | ✅ |
| Local file system operation | ❌ | ❌ | ❌ |
| GPU out of memory | ❌ | ❌ | ❌ (fix the code) |

---

## Summary

```
RETRY = "Try again — it might work next time" (transient failures)
CIRCUIT BREAKER = "Stop trying — it's dead" (sustained failures)

Together: Retry handles blips. Circuit Breaker prevents cascade when it's truly down.

Normal:          Request → Service → Response ✅
Transient fail:  Request → Service → ❌ → Retry → Service → Response ✅  
Sustained fail:  Request → Circuit OPEN → Fallback immediately ⚡ (no waiting)
```


## Working Implementation

A complete, runnable implementation lives in `circuit_breaker/`:

```
circuit_breaker/
├── README.md                        # Pattern explanation, state diagram, usage guide
├── src/
│   ├── __init__.py
│   ├── retry.py                     # Retry decorator with exponential backoff
│   ├── circuit_breaker.py           # CircuitBreaker dataclass with state machine
│   └── resilient_service.py         # ML inference service demo (simulated failures)
└── tests/
    ├── __init__.py
    ├── test_retry.py                # 9 tests covering retry behavior
    └── test_circuit_breaker.py      # 12 tests covering state transitions
```

### Running

```bash
# Run the interactive demo (no external services needed)
cd design_patterns/circuit_breaker
python3 -m src.resilient_service

# Run all tests (21 tests)
python3 -m pytest tests/ -v
```

### Key files

- **`src/retry.py`** — Standalone retry decorator. Use it anywhere you call a flaky service.
- **`src/circuit_breaker.py`** — Dataclass-based circuit breaker with CLOSED/OPEN/HALF_OPEN states.
- **`src/resilient_service.py`** — Shows how to combine both patterns in an ML inference pipeline with fallback logic. Uses `SimulatedService` to fail N times then succeed, so you can observe the retry + circuit breaker interaction without any real services.
