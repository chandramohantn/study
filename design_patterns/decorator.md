# Decorator Pattern (Structural)

## The One-Line Summary

**Add behavior to an object WITHOUT modifying it — by wrapping it in layers.**

---

## Important Clarification

This is the **structural design pattern** called "Decorator" — NOT Python's `@decorator` syntax. They share the name but are different concepts:

| | Python `@decorator` | Decorator Design Pattern |
|---|---|---|
| What it is | Syntax sugar for wrapping functions | A class that wraps another class |
| Operates on | Functions | Objects (class instances) |
| Composability | Usually applied once | Can be stacked infinitely |
| Interface | Changes the function | Preserves the SAME interface |

The design pattern wraps an object with another object that has the **same interface**, adding behavior before/after the original.

---

## The Problem

You have a working ML prediction function. Now you need to add:
- Logging (for debugging)
- Timing (for performance monitoring)
- Input validation (for safety)
- Caching (for speed)
- Metrics (for observability)

```python
# ❌ WITHOUT DECORATOR PATTERN — everything crammed into one class

class PredictionService:
    def predict(self, features: np.ndarray) -> np.ndarray:
        # Validation
        if features.shape[1] != 20:
            raise ValueError(f"Expected 20 features, got {features.shape[1]}")
        if np.any(np.isnan(features)):
            raise ValueError("NaN in input")

        # Timing
        import time
        start = time.perf_counter()

        # Logging
        logger.info(f"Predicting for {len(features)} samples")

        # Cache check
        cache_key = hash(features.tobytes())
        if cache_key in self._cache:
            logger.info("Cache hit!")
            return self._cache[cache_key]

        # ACTUAL PREDICTION (the only thing this class should do!)
        result = self.model.predict(features)

        # Cache store
        self._cache[cache_key] = result

        # Timing
        elapsed = time.perf_counter() - start

        # Metrics
        self.metrics.record("prediction_latency", elapsed)
        self.metrics.increment("prediction_count")

        # Logging
        logger.info(f"Prediction complete in {elapsed:.3f}s")

        return result
```

**Problems:**
- The class does 6 things instead of 1 (violates Single Responsibility)
- Can't disable logging without modifying the class
- Can't add/remove concerns without touching core logic
- Hard to test (need to mock logger, metrics, cache, model...)
- Every new concern = modify working code

---

## How Decorator Pattern Solves It

**Each concern becomes its own wrapper.** Each wrapper has the SAME interface as the thing it wraps. You stack them like layers:

```
Request → Validation → Timing → Logging → Cache → ACTUAL PREDICTION → back up the chain
```

```python
from typing import Protocol
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


# ─── Step 1: Define the interface ───

class Predictor(Protocol):
    """The interface that ALL predictors (and decorators) share."""
    def predict(self, features: np.ndarray) -> np.ndarray: ...


# ─── Step 2: The core implementation (does ONE thing) ───

class ModelPredictor:
    """Core predictor — ONLY runs the model. Nothing else."""

    def __init__(self, model):
        self.model = model

    def predict(self, features: np.ndarray) -> np.ndarray:
        return self.model.predict(features)


# ─── Step 3: Decorators (each adds ONE concern) ───

class LoggingDecorator:
    """Adds logging. Wraps any Predictor."""

    def __init__(self, wrapped: Predictor):
        self._wrapped = wrapped

    def predict(self, features: np.ndarray) -> np.ndarray:
        logger.info(f"Predicting for {len(features)} samples")
        result = self._wrapped.predict(features)
        logger.info(f"Prediction complete: {len(result)} results")
        return result


class TimingDecorator:
    """Adds performance measurement. Wraps any Predictor."""

    def __init__(self, wrapped: Predictor):
        self._wrapped = wrapped
        self.last_latency_ms: float = 0

    def predict(self, features: np.ndarray) -> np.ndarray:
        start = time.perf_counter()
        result = self._wrapped.predict(features)
        self.last_latency_ms = (time.perf_counter() - start) * 1000
        return result


class ValidationDecorator:
    """Adds input validation. Wraps any Predictor."""

    def __init__(self, wrapped: Predictor, expected_features: int):
        self._wrapped = wrapped
        self._expected = expected_features

    def predict(self, features: np.ndarray) -> np.ndarray:
        if features.ndim != 2:
            raise ValueError(f"Expected 2D array, got {features.ndim}D")
        if features.shape[1] != self._expected:
            raise ValueError(f"Expected {self._expected} features, got {features.shape[1]}")
        if np.any(np.isnan(features)):
            raise ValueError("Input contains NaN values")
        if np.any(np.isinf(features)):
            raise ValueError("Input contains Inf values")

        return self._wrapped.predict(features)


class CachingDecorator:
    """Adds result caching. Wraps any Predictor."""

    def __init__(self, wrapped: Predictor, max_size: int = 1000):
        self._wrapped = wrapped
        self._cache: dict[bytes, np.ndarray] = {}
        self._max_size = max_size
        self.hits = 0
        self.misses = 0

    def predict(self, features: np.ndarray) -> np.ndarray:
        cache_key = features.tobytes()

        if cache_key in self._cache:
            self.hits += 1
            return self._cache[cache_key]

        self.misses += 1
        result = self._wrapped.predict(features)

        # Simple eviction: clear when full
        if len(self._cache) >= self._max_size:
            self._cache.clear()
        self._cache[cache_key] = result

        return result

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0


class MetricsDecorator:
    """Adds metrics collection. Wraps any Predictor."""

    def __init__(self, wrapped: Predictor, metrics_collector):
        self._wrapped = wrapped
        self._metrics = metrics_collector

    def predict(self, features: np.ndarray) -> np.ndarray:
        start = time.perf_counter()
        result = self._wrapped.predict(features)
        elapsed = time.perf_counter() - start

        self._metrics.increment("predictions_total")
        self._metrics.histogram("prediction_latency_seconds", elapsed)
        self._metrics.gauge("prediction_batch_size", len(features))

        return result
```

---

## Stacking Decorators (The Power)

```python
# ─── Build the decorator stack ───

# Start with the core (innermost)
predictor = ModelPredictor(model=trained_sklearn_model)

# Wrap with validation (catches bad input BEFORE reaching model)
predictor = ValidationDecorator(predictor, expected_features=20)

# Wrap with caching (if same input, skip everything below)
predictor = CachingDecorator(predictor, max_size=5000)

# Wrap with timing (measures how long the below layers take)
predictor = TimingDecorator(predictor)

# Wrap with logging (outermost — logs everything)
predictor = LoggingDecorator(predictor)

# Now calling predict() goes through ALL layers:
result = predictor.predict(input_data)

# Flow:
# LoggingDecorator.predict()
#   → TimingDecorator.predict()
#     → CachingDecorator.predict()
#       → (cache miss) ValidationDecorator.predict()
#         → (valid) ModelPredictor.predict()
#           → model.predict(features)  ← actual computation
#         ← result
#       ← result (stored in cache)
#     ← result (timing recorded)
#   ← result (logged)
# ← result returned to caller
```

### Visual: The Onion Layers

```
┌─────────────────────────────────────────────────────────────┐
│ LoggingDecorator                                             │
│   logs "Predicting for N samples"                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ TimingDecorator                                          │ │
│ │   records latency                                        │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ CachingDecorator                                     │ │ │
│ │ │   returns cached result if available                 │ │ │
│ │ │ ┌─────────────────────────────────────────────────┐ │ │ │
│ │ │ │ ValidationDecorator                              │ │ │ │
│ │ │ │   rejects bad input                             │ │ │ │
│ │ │ │ ┌─────────────────────────────────────────────┐ │ │ │ │
│ │ │ │ │ ModelPredictor (CORE)                        │ │ │ │ │
│ │ │ │ │   model.predict(features)                    │ │ │ │ │
│ │ │ │ └─────────────────────────────────────────────┘ │ │ │ │
│ │ │ └─────────────────────────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This is Powerful

### 1. Add/Remove Concerns Without Touching Core

```python
# Development: no caching, extra logging
predictor = ModelPredictor(model)
predictor = ValidationDecorator(predictor, expected_features=20)
predictor = LoggingDecorator(predictor)

# Production: caching, metrics, no extra logging
predictor = ModelPredictor(model)
predictor = ValidationDecorator(predictor, expected_features=20)
predictor = CachingDecorator(predictor, max_size=10000)
predictor = MetricsDecorator(predictor, prometheus_collector)

# Testing: bare — no decorators at all!
predictor = ModelPredictor(fake_model)
```

### 2. Test Each Layer Independently

```python
import pytest
import numpy as np
from unittest.mock import MagicMock


class TestValidationDecorator:
    """Test validation WITHOUT any model, logging, caching, etc."""

    @pytest.fixture
    def inner(self):
        """Fake inner predictor — just returns zeros."""
        fake = MagicMock()
        fake.predict.return_value = np.zeros(5)
        return fake

    @pytest.fixture
    def validator(self, inner):
        return ValidationDecorator(inner, expected_features=10)

    def test_passes_valid_input(self, validator):
        valid = np.random.randn(5, 10)
        result = validator.predict(valid)
        assert len(result) == 5

    def test_rejects_wrong_feature_count(self, validator):
        wrong = np.random.randn(5, 7)  # 7 instead of 10
        with pytest.raises(ValueError, match="Expected 10 features"):
            validator.predict(wrong)

    def test_rejects_nan(self, validator):
        with_nan = np.random.randn(5, 10)
        with_nan[0, 0] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            validator.predict(with_nan)

    def test_rejects_1d_input(self, validator):
        flat = np.random.randn(10)  # 1D instead of 2D
        with pytest.raises(ValueError, match="2D"):
            validator.predict(flat)


class TestCachingDecorator:
    """Test caching independently."""

    @pytest.fixture
    def inner(self):
        fake = MagicMock()
        fake.predict.return_value = np.array([1, 0, 1])
        return fake

    @pytest.fixture
    def cached(self, inner):
        return CachingDecorator(inner, max_size=100)

    def test_first_call_is_miss(self, cached, inner):
        data = np.array([[1.0, 2.0, 3.0]])
        cached.predict(data)
        assert cached.misses == 1
        assert cached.hits == 0
        inner.predict.assert_called_once()

    def test_second_same_call_is_hit(self, cached, inner):
        data = np.array([[1.0, 2.0, 3.0]])
        cached.predict(data)
        cached.predict(data)  # Same input again
        assert cached.hits == 1
        assert inner.predict.call_count == 1  # Model called only ONCE

    def test_different_input_is_miss(self, cached, inner):
        cached.predict(np.array([[1.0, 2.0, 3.0]]))
        cached.predict(np.array([[4.0, 5.0, 6.0]]))
        assert cached.misses == 2
        assert inner.predict.call_count == 2

    def test_hit_rate_calculation(self, cached):
        data = np.array([[1.0, 2.0, 3.0]])
        cached.predict(data)  # miss
        cached.predict(data)  # hit
        cached.predict(data)  # hit
        assert cached.hit_rate == pytest.approx(2 / 3)
```

### 3. Open/Closed Principle

New concern? Write a NEW decorator class. Don't touch existing code.

```python
# ─── New requirement: "Add rate limiting" ───
# Don't touch ModelPredictor, ValidationDecorator, etc.
# Just write a new decorator:

class RateLimitingDecorator:
    """New concern — added without modifying ANY existing code."""

    def __init__(self, wrapped: Predictor, max_per_second: int = 100):
        self._wrapped = wrapped
        self._max_per_second = max_per_second
        self._call_times: list[float] = []

    def predict(self, features: np.ndarray) -> np.ndarray:
        import time
        now = time.time()
        # Remove calls older than 1 second
        self._call_times = [t for t in self._call_times if now - t < 1.0]

        if len(self._call_times) >= self._max_per_second:
            raise RuntimeError(f"Rate limit exceeded: {self._max_per_second}/sec")

        self._call_times.append(now)
        return self._wrapped.predict(features)


# Plug it in:
predictor = ModelPredictor(model)
predictor = RateLimitingDecorator(predictor, max_per_second=1000)
predictor = CachingDecorator(predictor)
predictor = LoggingDecorator(predictor)
```

---

## Real-World ML Example: Full Inference Stack

```python
from typing import Protocol
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


class Predictor(Protocol):
    def predict(self, features: np.ndarray) -> np.ndarray: ...


def build_inference_stack(
    model,
    feature_count: int,
    cache_size: int = 5000,
    enable_logging: bool = True,
    enable_cache: bool = True,
    enable_validation: bool = True,
) -> Predictor:
    """
    Factory function that builds the decorator stack from config.
    Each layer is optional and configurable.
    """
    # Core (always present)
    predictor: Predictor = ModelPredictor(model)

    # Validation (optional — disable in trusted internal calls)
    if enable_validation:
        predictor = ValidationDecorator(predictor, expected_features=feature_count)

    # Caching (optional — disable for training evaluation)
    if enable_cache:
        predictor = CachingDecorator(predictor, max_size=cache_size)

    # Timing (always — we always want latency metrics)
    predictor = TimingDecorator(predictor)

    # Logging (optional — disable in high-throughput batch)
    if enable_logging:
        predictor = LoggingDecorator(predictor)

    return predictor


# ─── Usage in different contexts ───

# API endpoint: full stack
api_predictor = build_inference_stack(
    model=production_model,
    feature_count=20,
    cache_size=10000,
    enable_logging=True,
    enable_cache=True,
)

# Batch evaluation: no cache, no logging (speed matters)
batch_predictor = build_inference_stack(
    model=production_model,
    feature_count=20,
    enable_logging=False,
    enable_cache=False,
)

# Testing: bare minimum
test_predictor = ModelPredictor(model=fake_model)
```

---

## When to Use Decorator Pattern

| ✅ Use When | ❌ Don't Use When |
|---|---|
| You need to add logging/timing/caching/validation | You only have one concern (just put it in the class) |
| Different contexts need different combinations | The concerns are always the same everywhere |
| You want to test each concern independently | The added complexity isn't worth it for a simple script |
| You need to enable/disable features at runtime | You'll never change the behavior stack |
| Open/Closed: add new concerns without modifying core | You have 1-2 classes total in your project |

---

## Summary

```
DECORATOR answers: "How do I add behaviors (logging, caching, timing) 
                    without making my core class a tangled mess?"

1. Define a Protocol (interface)
2. Implement the CORE class (does one thing)
3. Implement DECORATOR classes (each adds one concern, wraps the same interface)
4. STACK them in the order you want

Key insight: Each decorator HAS the same interface as what it wraps.
             So you can stack infinitely: Logging(Timing(Cache(Validation(Core))))
             
             Each layer only knows about the layer below it.
             None of them know about the layers above.
             
             ← That's loose coupling. That's the power.
```

---

## Working Implementation

The full working implementation lives in `design_patterns/decorator/`:

```
decorator/
├── README.md                        # Onion layers explanation, how to add new concerns
├── src/
│   ├── __init__.py
│   ├── __main__.py                  # Demo: python -m src
│   ├── predictor_interface.py       # Predictor Protocol (the shared interface)
│   ├── core_predictor.py            # ModelPredictor (wraps sklearn RandomForestClassifier)
│   ├── decorators.py                # LoggingDecorator, TimingDecorator, ValidationDecorator, CachingDecorator
│   └── stack_builder.py             # build_prediction_stack(model, config) — config-driven assembly
└── tests/
    ├── __init__.py
    └── test_decorators.py           # Each decorator tested in isolation with FakePredictor
```

### Run the demo

```bash
cd design_patterns/decorator
python3 -m src
```

### Run the tests

```bash
cd design_patterns/decorator
python3 -m pytest tests/ -v
```

### Key files

- **`src/predictor_interface.py`** — The `Predictor` Protocol. Every layer (core + decorators) implements this same `predict(np.ndarray) -> np.ndarray` interface.
- **`src/core_predictor.py`** — `ModelPredictor` does ONE thing: calls `model.predict()`. No logging, no timing, no validation.
- **`src/decorators.py`** — Four decorators, each adding exactly one concern. Each wraps any `Predictor` and is itself a `Predictor`.
- **`src/stack_builder.py`** — `build_prediction_stack(model, config)` assembles layers based on a config dict (mirrors how you'd wire this from YAML/env vars in production).
- **`tests/test_decorators.py`** — 21 tests proving each decorator works independently using a `FakePredictor` (no sklearn, no real model needed for tests).

### Demo output shows

1. **Bare predictor** produces result `[0 1 0 1 1]`
2. **Fully decorated predictor** (logging + timing + caching + validation) produces the same `[0 1 0 1 1]`
3. **Cache hit** — same input again, model not called, same result
4. **Validation** — catches wrong feature count and NaN inputs before reaching the model
5. **Different stacks** — minimal batch config (no validation/caching/logging) still produces `[0 1 0 1 1]`

Adding/removing decorator layers **never changes the core prediction output**.
