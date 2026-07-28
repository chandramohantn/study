# Repository Pattern — Working Implementation

## What This Demonstrates

The **PredictionService** orchestrates ML inference: fetching features, loading models, running predictions, and storing results. It does ALL of this **without importing any storage library** (no boto3, sqlalchemy, redis, etc.).

How? It depends only on **Protocols** (interfaces). The actual storage is **injected**.

## Folder Structure

```
repository/
├── README.md
├── src/
│   ├── __init__.py
│   ├── protocols.py           ← Defines WHAT operations exist (contracts)
│   ├── in_memory_repos.py     ← Testing: Python dicts/lists (zero infra)
│   ├── file_repos.py          ← Dev: JSON files on disk (real but simple)
│   └── prediction_service.py  ← Business logic (depends ONLY on Protocols)
└── tests/
    ├── __init__.py
    └── test_prediction_service.py  ← Fast tests with in-memory repos
```

## The Key Insight

```python
# prediction_service.py imports:
from src.protocols import FeatureRepository, ModelRepository, PredictionRepository

# It does NOT import:
# import boto3          ← NO
# import sqlalchemy     ← NO
# import redis          ← NO
```

The service receives repositories through its constructor. It never creates them. It never knows what's behind them.

## How Testing Works Without Infrastructure

```python
# In tests — inject in-memory fakes:
service = PredictionService(
    feature_repo=InMemoryFeatureRepository(),     # ← Python dict
    prediction_repo=InMemoryPredictionRepository(), # ← Python list
    model_repo=InMemoryModelRepository(),         # ← Python dict
)

# In production — inject real implementations:
service = PredictionService(
    feature_repo=RedisFeatureRepository(redis_url),  # ← Real Redis
    prediction_repo=S3PredictionRepository(bucket),  # ← Real S3
    model_repo=MLflowModelRepository(tracking_uri),  # ← Real MLflow
)
```

The service code is **identical** in both cases. Only the wiring changes.

## Running

```bash
# Run the demo (uses in-memory repos)
cd repository/
python -m src.prediction_service

# Run the tests (no infrastructure needed)
pytest tests/ -v
```

## Why This Matters for ML Engineers

| Without Repository | With Repository |
|---|---|
| Tests need Docker + real DBs | Tests need nothing |
| 5-30 sec per test (network I/O) | 1-5 ms per test (in-memory) |
| CI needs AWS credentials | CI needs only Python |
| Flaky tests (network issues) | Deterministic tests |
| Can't test on a plane | Works offline |
| Changing from S3 to GCS = rewrite service | Changing storage = new repo class only |


