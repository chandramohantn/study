# Circuit Breaker + Retry Pattern

A working implementation of two complementary resilience patterns, designed for ML engineers working with ETL pipelines, API endpoints, and inference services.

## The Problem

When your ML inference pipeline calls external services (feature stores, model APIs, databases), those services can:
- Be temporarily unavailable (network blips, cold starts)
- Be permanently down (outage, misconfiguration)
- Be slow (overloaded, degraded)

Without resilience patterns, one failing dependency can cascade and bring down your entire pipeline.

## The Solution: Two Complementary Patterns

### Retry with Exponential Backoff

**What:** Automatically retry failed operations with increasing delays.

**When to use:**
- Transient failures (network timeouts, 503s, rate limits)
- Operations that are likely to succeed on retry
- Short-lived disruptions

**When NOT to use:**
- The service is completely down (you'll just waste time and resources)
- Non-idempotent operations (risk of duplicate actions)
- Client errors (400, 401, 404 — these won't fix themselves)

### Circuit Breaker

**What:** Detect that a service is down and stop calling it immediately ("fail fast").

**When to use:**
- Protecting against prolonged outages
- Preventing cascade failures across services
- Allowing graceful degradation with fallbacks

**State Machine:**

```
     ┌─────────────────────────────────────────────────┐
     │                                                 │
     ▼                                                 │
  ┌──────┐    failure_threshold     ┌──────┐           │
  │CLOSED│ ──── reached ──────────> │ OPEN │           │
  └──────┘                          └──────┘           │
     ▲                                 │               │
     │                                 │ recovery      │
     │ success_threshold               │ timeout       │
     │ reached                         │ elapsed       │
     │                                 ▼               │
     │                           ┌──────────┐          │
     └────────────────────────── │HALF_OPEN │ ─failure─┘
                                 └──────────┘
```

**States explained:**
- **CLOSED** — Normal operation. Requests pass through. Failures are counted.
- **OPEN** — Service is considered unhealthy. Requests are blocked immediately (fail fast). After a timeout, transitions to HALF_OPEN.
- **HALF_OPEN** — Probing phase. A limited number of requests are allowed through. If they succeed, circuit closes. If they fail, circuit reopens.

## Combining Both Patterns

The recommended architecture:

```
Request
  └─> Circuit Breaker (fail fast if service is known-down)
        └─> Retry (handle transient failures)
              └─> External Service Call
                    └─> (failure) -> Fallback Response
```

The circuit breaker wraps the retry logic. This means:
1. If the service is known to be down → fail fast, use fallback
2. If the service might work → retry with backoff
3. If all retries fail → record failure in circuit breaker, use fallback

## Project Structure

```
circuit_breaker/
├── README.md
├── src/
│   ├── __init__.py
│   ├── retry.py               # Retry decorator with exponential backoff
│   ├── circuit_breaker.py     # CircuitBreaker class with state machine
│   └── resilient_service.py   # Example ML inference service (with demo)
└── tests/
    ├── __init__.py
    ├── test_retry.py           # Unit tests for retry decorator
    └── test_circuit_breaker.py # Unit tests for state transitions
```

## Running

```bash
# Run the demo (simulates failures, no real services needed)
cd circuit_breaker
python -m src.resilient_service

# Run tests
pytest tests/ -v
```

## Real-World Examples for ML Engineers

| Scenario | Retry | Circuit Breaker |
|----------|-------|-----------------|
| Feature store timeout | Yes (2-3 retries) | Yes (trip after 5 failures) |
| Model API 503 | Yes (with backoff) | Yes (fallback to cached model) |
| Database connection lost | Yes (short backoff) | Yes (switch to read replica) |
| S3 upload in ETL | Yes (5 retries) | No (S3 is rarely "down") |
| Kafka producer send | Yes (built-in) | Optional |
| Training checkpoint save | Yes (to local then remote) | No |

## Key Configuration Decisions

- **failure_threshold**: How many failures before tripping? (3-5 for critical paths)
- **recovery_timeout**: How long to wait before probing? (30-60s typically)
- **max_attempts**: How many retries? (2-3 for latency-sensitive, 5+ for batch ETL)
- **base_delay**: Starting backoff delay? (0.1-1.0s for APIs, longer for rate limits)


