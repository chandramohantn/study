# Decorator Pattern — ML Prediction Stack

## What This Demonstrates

The **structural Decorator pattern** (not Python's `@decorator` syntax) applied to ML inference.
Each cross-cutting concern (logging, timing, validation, caching) is a separate class that wraps
the same interface, forming "onion layers" around the core prediction logic.

## The Onion Layers Concept

```
Request arrives
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  LoggingDecorator    (logs input/output)                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  TimingDecorator   (measures latency)             │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  CachingDecorator  (returns cached result) │  │  │
│  │  │  ┌──────────────────────────────────────┐  │  │  │
│  │  │  │  ValidationDecorator (rejects bad in) │  │  │  │
│  │  │  │  ┌────────────────────────────────┐  │  │  │  │
│  │  │  │  │  ModelPredictor (CORE)          │  │  │  │  │
│  │  │  │  │  model.predict(features)        │  │  │  │  │
│  │  │  │  └────────────────────────────────┘  │  │  │  │
│  │  │  └──────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
    │
    ▼
Response returned
```

Each layer:
1. Receives the call from the layer above
2. Does its own work (before and/or after)
3. Delegates to the layer below via `self._wrapped.predict(features)`
4. Returns the result back up

## File Structure

```
decorator/
├── README.md
├── src/
│   ├── __init__.py
│   ├── __main__.py              # Demo: python -m src
│   ├── predictor_interface.py   # Protocol (the shared interface)
│   ├── core_predictor.py        # ModelPredictor (wraps sklearn model)
│   ├── decorators.py            # All decorator classes
│   └── stack_builder.py         # Config-driven stack assembly
└── tests/
    ├── __init__.py
    └── test_decorators.py       # Each decorator tested in isolation
```

## Running

```bash
# Run the demo
cd design_patterns/decorator
python -m src

# Run tests
pytest tests/ -v
```

## How to Add a New Concern

Adding a new decorator takes 3 steps. You never modify existing code.

### Step 1: Create the decorator class

```python
# In src/decorators.py (or a new file)

class RateLimitingDecorator:
    """Rejects requests that exceed a rate threshold."""

    def __init__(self, wrapped: Predictor, max_per_second: int = 100) -> None:
        self._wrapped = wrapped
        self._max_per_second = max_per_second
        self._call_times: list[float] = []

    def predict(self, features: np.ndarray) -> np.ndarray:
        import time
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < 1.0]

        if len(self._call_times) >= self._max_per_second:
            raise RuntimeError(f"Rate limit exceeded: {self._max_per_second}/sec")

        self._call_times.append(now)
        return self._wrapped.predict(features)
```

### Step 2: Add it to the stack builder (optional)

```python
# In build_prediction_stack():
if config.get("enable_rate_limiting", False):
    predictor = RateLimitingDecorator(
        predictor, max_per_second=config.get("max_rps", 100)
    )
```

### Step 3: Write an isolated test

```python
class TestRateLimitingDecorator:
    def test_allows_under_limit(self):
        inner = FakePredictor()
        limited = RateLimitingDecorator(inner, max_per_second=10)
        data = np.random.randn(1, 5)
        limited.predict(data)  # Should not raise

    def test_blocks_over_limit(self):
        inner = FakePredictor()
        limited = RateLimitingDecorator(inner, max_per_second=2)
        data = np.random.randn(1, 5)
        limited.predict(data)
        limited.predict(data)
        with pytest.raises(RuntimeError, match="Rate limit"):
            limited.predict(data)
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Protocol (not ABC) | Structural typing — no inheritance needed |
| Config dict for stacking | Easy to load from YAML/env vars |
| LRU cache (not simple dict) | Bounded memory in production |
| Copy on cache return | Prevents callers from corrupting cache |
| Each decorator holds `_wrapped` | Composition over inheritance |

## When to Use This Pattern

✅ Multiple optional concerns around a core operation
✅ Different environments need different combinations (dev/staging/prod)
✅ You want to test each concern independently
✅ New requirements should not require modifying existing code

❌ Only one concern — just put it in the class
❌ The combination never changes — premature abstraction
❌ Three classes total in your project — not worth the indirection


