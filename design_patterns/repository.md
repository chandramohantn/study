# Repository Pattern

## The One-Line Summary

**Hide WHERE data lives behind an interface. Your business logic never knows if it's talking to PostgreSQL, Redis, S3, or a fake in-memory store.**

---

## The Problem (Why You Can't Test Without Real Infrastructure)

Here's the typical ML service code without Repository pattern:

```python
# ❌ WITHOUT REPOSITORY — database is hardcoded everywhere

import boto3
import pandas as pd
from sqlalchemy import create_engine


class FeatureService:
    def __init__(self):
        # Hardcoded infrastructure
        self.engine = create_engine("postgresql://prod:password@db.internal:5432/features")
        self.s3 = boto3.client("s3")

    def get_user_features(self, user_id: str) -> dict:
        # Direct SQL — coupled to PostgreSQL
        query = f"SELECT * FROM user_features WHERE user_id = '{user_id}'"
        df = pd.read_sql(query, self.engine)
        return df.iloc[0].to_dict() if len(df) > 0 else {}

    def save_predictions(self, predictions: list[dict]) -> None:
        # Direct S3 call — coupled to AWS
        df = pd.DataFrame(predictions)
        buffer = df.to_parquet()
        self.s3.put_object(Bucket="predictions", Key="latest.parquet", Body=buffer)

    def get_model_metrics(self, model_id: str) -> dict:
        query = f"SELECT * FROM model_metrics WHERE model_id = '{model_id}'"
        df = pd.read_sql(query, self.engine)
        return df.to_dict(orient="records")
```

**Now try to write a unit test:**

```python
# ❌ How do you test this without a real PostgreSQL and real S3?

def test_get_user_features():
    service = FeatureService()  # 💀 Connects to REAL production DB!
    features = service.get_user_features("user_123")
    assert "age" in features
```

**You can't.** The tests require:
- A running PostgreSQL instance with test data
- AWS credentials for S3
- Network connectivity
- Test data setup/teardown

This makes tests:
- **Slow** (network calls)
- **Flaky** (network issues, stale data)
- **Expensive** (AWS costs)
- **Dangerous** (accidentally touching prod data)

---

## How Repository Pattern Solves It

**Put a Protocol (interface) between your business logic and the data store.** Your code talks to the Protocol. The actual storage is injected.

```python
from typing import Protocol
import pandas as pd


# ─── Step 1: Define WHAT operations you need (not HOW they work) ───

class FeatureRepository(Protocol):
    """Interface: what the business logic needs from a feature store."""
    def get_user_features(self, user_id: str) -> dict: ...
    def save_user_features(self, user_id: str, features: dict) -> None: ...
    def get_batch_features(self, user_ids: list[str]) -> pd.DataFrame: ...


class PredictionRepository(Protocol):
    """Interface: what the business logic needs for predictions."""
    def save_predictions(self, predictions: list[dict]) -> None: ...
    def get_predictions(self, model_id: str, limit: int = 100) -> list[dict]: ...


class ModelRepository(Protocol):
    """Interface: what the business logic needs for model management."""
    def save_model(self, model_id: str, model_bytes: bytes, metadata: dict) -> None: ...
    def load_model(self, model_id: str) -> tuple[bytes, dict]: ...
    def get_latest_model_id(self) -> str: ...
```

```python
# ─── Step 2: REAL implementation (used in production) ───

class PostgresFeatureRepository:
    """Production implementation — talks to real PostgreSQL."""

    def __init__(self, connection_string: str):
        from sqlalchemy import create_engine
        self.engine = create_engine(connection_string)

    def get_user_features(self, user_id: str) -> dict:
        query = "SELECT * FROM user_features WHERE user_id = %s"
        df = pd.read_sql(query, self.engine, params=[user_id])
        return df.iloc[0].to_dict() if len(df) > 0 else {}

    def save_user_features(self, user_id: str, features: dict) -> None:
        df = pd.DataFrame([{"user_id": user_id, **features}])
        df.to_sql("user_features", self.engine, if_exists="append", index=False)

    def get_batch_features(self, user_ids: list[str]) -> pd.DataFrame:
        placeholders = ",".join(["%s"] * len(user_ids))
        query = f"SELECT * FROM user_features WHERE user_id IN ({placeholders})"
        return pd.read_sql(query, self.engine, params=user_ids)


class S3PredictionRepository:
    """Production implementation — stores predictions in S3."""

    def __init__(self, bucket: str):
        import boto3
        self.s3 = boto3.client("s3")
        self.bucket = bucket

    def save_predictions(self, predictions: list[dict]) -> None:
        import io, json
        from datetime import datetime
        key = f"predictions/{datetime.now().strftime('%Y-%m-%d/%H%M%S')}.json"
        body = json.dumps(predictions)
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=body)

    def get_predictions(self, model_id: str, limit: int = 100) -> list[dict]:
        # ... S3 listing and reading logic ...
        pass
```

```python
# ─── Step 3: FAKE implementation (used in tests) ───

class InMemoryFeatureRepository:
    """
    Test implementation — NO database, NO network, NO AWS.
    Just a Python dict. Blazing fast.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def get_user_features(self, user_id: str) -> dict:
        return self._store.get(user_id, {})

    def save_user_features(self, user_id: str, features: dict) -> None:
        self._store[user_id] = features

    def get_batch_features(self, user_ids: list[str]) -> pd.DataFrame:
        rows = []
        for uid in user_ids:
            if uid in self._store:
                rows.append({"user_id": uid, **self._store[uid]})
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    # Test helpers (not in Protocol — only available in tests)
    def seed(self, data: dict[str, dict]) -> None:
        """Pre-populate with test data."""
        self._store = data.copy()

    def clear(self) -> None:
        self._store.clear()


class InMemoryPredictionRepository:
    """Test implementation for predictions."""

    def __init__(self):
        self._predictions: list[dict] = []

    def save_predictions(self, predictions: list[dict]) -> None:
        self._predictions.extend(predictions)

    def get_predictions(self, model_id: str, limit: int = 100) -> list[dict]:
        filtered = [p for p in self._predictions if p.get("model_id") == model_id]
        return filtered[:limit]

    # Test helper
    @property
    def saved_count(self) -> int:
        return len(self._predictions)
```

```python
# ─── Step 4: Business logic uses the Protocol (not the implementation) ───

class PredictionService:
    """
    Business logic — ONLY depends on Protocols.
    Doesn't know if it's talking to PostgreSQL, S3, or an in-memory dict.
    """

    def __init__(
        self,
        feature_repo: FeatureRepository,
        prediction_repo: PredictionRepository,
    ):
        self.features = feature_repo
        self.predictions = prediction_repo
        self.model = None  # Loaded separately

    def predict_for_user(self, user_id: str) -> dict:
        # Get features (from whatever repository is injected)
        features = self.features.get_user_features(user_id)
        if not features:
            raise ValueError(f"No features found for user {user_id}")

        # Run prediction
        import numpy as np
        feature_array = np.array([list(features.values())])
        prediction = self.model.predict(feature_array)[0]

        result = {
            "user_id": user_id,
            "prediction": int(prediction),
            "features_used": list(features.keys()),
        }

        # Save prediction (to whatever repository is injected)
        self.predictions.save_predictions([result])

        return result

    def predict_batch(self, user_ids: list[str]) -> list[dict]:
        features_df = self.features.get_batch_features(user_ids)
        if features_df.empty:
            return []

        # ... batch prediction logic ...
        results = []
        for _, row in features_df.iterrows():
            results.append({"user_id": row["user_id"], "prediction": 1})

        self.predictions.save_predictions(results)
        return results
```

---

## Testing Without Infrastructure (The Payoff)

**This is where Repository pattern shines.** Look how easy testing becomes:

```python
# tests/test_prediction_service.py
import pytest
import numpy as np
from unittest.mock import MagicMock


class TestPredictionService:
    """
    These tests run in MILLISECONDS.
    No PostgreSQL. No S3. No AWS. No network.
    Just Python objects in memory.
    """

    @pytest.fixture
    def feature_repo(self):
        """In-memory feature repository with test data."""
        repo = InMemoryFeatureRepository()
        repo.seed({
            "user_1": {"age": 25, "income": 50000, "tenure": 365},
            "user_2": {"age": 35, "income": 80000, "tenure": 730},
            "user_3": {"age": 45, "income": 120000, "tenure": 1095},
        })
        return repo

    @pytest.fixture
    def prediction_repo(self):
        """In-memory prediction repository."""
        return InMemoryPredictionRepository()

    @pytest.fixture
    def fake_model(self):
        """Fake model that always predicts 1."""
        model = MagicMock()
        model.predict.return_value = np.array([1])
        return model

    @pytest.fixture
    def service(self, feature_repo, prediction_repo, fake_model):
        """Fully wired service with all fakes."""
        svc = PredictionService(
            feature_repo=feature_repo,
            prediction_repo=prediction_repo,
        )
        svc.model = fake_model
        return svc

    # ─── Tests ───

    def test_predict_returns_result_for_known_user(self, service):
        result = service.predict_for_user("user_1")

        assert result["user_id"] == "user_1"
        assert result["prediction"] == 1
        assert "features_used" in result

    def test_predict_raises_for_unknown_user(self, service):
        with pytest.raises(ValueError, match="No features found"):
            service.predict_for_user("nonexistent_user")

    def test_predict_saves_prediction(self, service, prediction_repo):
        service.predict_for_user("user_1")

        assert prediction_repo.saved_count == 1

    def test_predict_uses_correct_features(self, service, fake_model):
        service.predict_for_user("user_1")

        # Verify model was called with the right feature values
        call_args = fake_model.predict.call_args[0][0]
        assert call_args.shape == (1, 3)  # 3 features: age, income, tenure

    def test_predict_batch_returns_all_results(self, service):
        results = service.predict_batch(["user_1", "user_2"])
        assert len(results) == 2

    def test_predict_batch_empty_for_unknown_users(self, service):
        results = service.predict_batch(["unknown_1", "unknown_2"])
        assert results == []

    def test_predict_batch_saves_all_predictions(self, service, prediction_repo):
        service.predict_batch(["user_1", "user_2", "user_3"])
        assert prediction_repo.saved_count == 3


class TestFeatureRepository:
    """Test the in-memory repo itself (useful for verifying test infrastructure)."""

    def test_get_returns_empty_for_unknown_user(self):
        repo = InMemoryFeatureRepository()
        assert repo.get_user_features("unknown") == {}

    def test_save_and_get_roundtrip(self):
        repo = InMemoryFeatureRepository()
        repo.save_user_features("user_1", {"age": 30, "score": 0.8})
        result = repo.get_user_features("user_1")
        assert result == {"age": 30, "score": 0.8}

    def test_get_batch_returns_dataframe(self):
        repo = InMemoryFeatureRepository()
        repo.seed({
            "u1": {"age": 25},
            "u2": {"age": 35},
        })
        df = repo.get_batch_features(["u1", "u2"])
        assert len(df) == 2
        assert "user_id" in df.columns
```

### Compare: Test Speed and Reliability

| | Without Repository | With Repository |
|---|---|---|
| Test speed | 2-10 seconds (network) | 2-10 milliseconds (in-memory) |
| Dependencies | PostgreSQL, Redis, S3, network | None |
| Flakiness | High (network issues, data state) | Zero (deterministic) |
| CI setup | Complex (Docker, test DBs) | Simple (just Python) |
| Data isolation | Hard (shared DB) | Perfect (fresh dict each test) |
| Cost | AWS charges in CI | Free |

---

## The Pattern Applied to Your ML Work

### Feature Store Repository

```python
from typing import Protocol
import numpy as np


class FeatureStore(Protocol):
    """Your ML pipeline's interface to features."""
    def get_online_features(self, entity_id: str, feature_names: list[str]) -> dict: ...
    def get_training_features(self, entity_ids: list[str]) -> pd.DataFrame: ...
    def save_features(self, entity_id: str, features: dict) -> None: ...


# Production: Redis
class RedisFeatureStore:
    def __init__(self, redis_url: str):
        import redis
        self._client = redis.from_url(redis_url)

    def get_online_features(self, entity_id: str, feature_names: list[str]) -> dict:
        import json
        data = self._client.hgetall(f"features:{entity_id}")
        return {k.decode(): json.loads(v) for k, v in data.items() if k.decode() in feature_names}

    def get_training_features(self, entity_ids: list[str]) -> pd.DataFrame:
        rows = [self.get_online_features(eid, []) for eid in entity_ids]
        return pd.DataFrame(rows)

    def save_features(self, entity_id: str, features: dict) -> None:
        import json
        mapping = {k: json.dumps(v) for k, v in features.items()}
        self._client.hset(f"features:{entity_id}", mapping=mapping)


# Testing: In-Memory
class InMemoryFeatureStore:
    def __init__(self):
        self._data: dict[str, dict] = {}

    def get_online_features(self, entity_id: str, feature_names: list[str]) -> dict:
        all_features = self._data.get(entity_id, {})
        if feature_names:
            return {k: v for k, v in all_features.items() if k in feature_names}
        return all_features

    def get_training_features(self, entity_ids: list[str]) -> pd.DataFrame:
        rows = [{"entity_id": eid, **self._data.get(eid, {})} for eid in entity_ids]
        return pd.DataFrame(rows)

    def save_features(self, entity_id: str, features: dict) -> None:
        self._data[entity_id] = features
```

### Model Registry Repository

```python
from typing import Protocol, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelArtifact:
    model_id: str
    version: str
    path: str
    metrics: dict
    created_at: datetime


class ModelRegistry(Protocol):
    def save(self, model_id: str, model_bytes: bytes, metadata: dict) -> ModelArtifact: ...
    def load(self, model_id: str) -> tuple[bytes, ModelArtifact]: ...
    def get_latest(self) -> ModelArtifact: ...
    def list_models(self) -> list[ModelArtifact]: ...


# Production: S3 + DynamoDB
class S3ModelRegistry:
    def __init__(self, bucket: str, table_name: str):
        import boto3
        self.s3 = boto3.client("s3")
        self.dynamodb = boto3.resource("dynamodb").Table(table_name)
        self.bucket = bucket

    def save(self, model_id: str, model_bytes: bytes, metadata: dict) -> ModelArtifact:
        key = f"models/{model_id}/model.pkl"
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=model_bytes)

        artifact = ModelArtifact(
            model_id=model_id, version="1.0", path=f"s3://{self.bucket}/{key}",
            metrics=metadata.get("metrics", {}), created_at=datetime.now(),
        )
        self.dynamodb.put_item(Item={"model_id": model_id, "metadata": str(metadata)})
        return artifact

    def load(self, model_id: str) -> tuple[bytes, ModelArtifact]:
        key = f"models/{model_id}/model.pkl"
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        model_bytes = response["Body"].read()
        # ... also load metadata from DynamoDB ...
        return model_bytes, ModelArtifact(model_id=model_id, version="1.0", path=key,
                                          metrics={}, created_at=datetime.now())

    def get_latest(self) -> ModelArtifact:
        # Query DynamoDB for latest
        pass

    def list_models(self) -> list[ModelArtifact]:
        pass


# Testing: In-Memory
class InMemoryModelRegistry:
    def __init__(self):
        self._models: dict[str, tuple[bytes, ModelArtifact]] = {}

    def save(self, model_id: str, model_bytes: bytes, metadata: dict) -> ModelArtifact:
        artifact = ModelArtifact(
            model_id=model_id, version="1.0", path=f"memory://{model_id}",
            metrics=metadata.get("metrics", {}), created_at=datetime.now(),
        )
        self._models[model_id] = (model_bytes, artifact)
        return artifact

    def load(self, model_id: str) -> tuple[bytes, ModelArtifact]:
        if model_id not in self._models:
            raise KeyError(f"Model {model_id} not found")
        return self._models[model_id]

    def get_latest(self) -> ModelArtifact:
        if not self._models:
            raise KeyError("No models registered")
        latest_id = list(self._models.keys())[-1]
        return self._models[latest_id][1]

    def list_models(self) -> list[ModelArtifact]:
        return [artifact for _, artifact in self._models.values()]
```

---

## Wiring: Production vs Testing

```python
# ─── Production wiring (in your app's startup/DI container) ───

def create_production_service() -> PredictionService:
    return PredictionService(
        feature_repo=PostgresFeatureRepository("postgresql://prod:pw@db:5432/features"),
        prediction_repo=S3PredictionRepository(bucket="ml-predictions"),
    )


# ─── Test wiring (in conftest.py) ───

@pytest.fixture
def service():
    """Service wired with in-memory repos — no infrastructure needed."""
    feature_repo = InMemoryFeatureRepository()
    feature_repo.seed({
        "user_1": {"age": 25, "score": 0.8},
        "user_2": {"age": 35, "score": 0.6},
    })

    return PredictionService(
        feature_repo=feature_repo,
        prediction_repo=InMemoryPredictionRepository(),
    )
```

---

## When to Use Repository

| ✅ Use When | ❌ Don't Use When |
|---|---|
| You need to test business logic without infrastructure | Your script is a one-off data processing job |
| Multiple storage backends (dev=local, prod=S3/DB) | You'll only ever use one storage backend |
| You want to swap storage later without rewriting logic | The storage is trivial (one file read/write) |
| Your CI/CD should be fast and not need Docker DBs | You already have integration test infrastructure |
| Multiple services share the same storage interface | Only one class ever accesses the storage |

---

## Summary

```
REPOSITORY answers: "How do I test my business logic without needing real databases/S3/Redis?"

1. Define a Protocol (interface) for data operations
2. Implement a REAL version (PostgreSQL, S3, Redis)
3. Implement a FAKE version (in-memory dict)
4. Inject the right one:
   - Production → Real implementation
   - Tests → In-memory fake

Your business logic NEVER imports boto3, sqlalchemy, or redis.
It only knows about the Protocol. That's the power.

                  ┌───────────────────┐
                  │  Business Logic    │
                  │  (PredictionService)│
                  │                    │
                  │  Uses: Protocol    │
                  └────────┬───────────┘
                           │
              ┌────────────┼────────────┐
              │                         │
    ┌─────────▼─────────┐   ┌──────────▼──────────┐
    │ PostgresRepository │   │ InMemoryRepository  │
    │ (Production)       │   │ (Tests)             │
    │ - Real DB queries  │   │ - Python dict       │
    │ - Network calls    │   │ - Instant           │
    │ - Needs infra      │   │ - No dependencies   │
    └────────────────────┘   └─────────────────────┘
```

## Working Implementation

A complete, runnable implementation lives in the `repository/` folder:

```
design_patterns/
└── repository/
    ├── README.md
    ├── src/
    │   ├── __init__.py
    │   ├── protocols.py           ← Protocol definitions (FeatureRepository, PredictionRepository, ModelRepository)
    │   ├── in_memory_repos.py     ← In-memory implementations (for testing — zero infrastructure)
    │   ├── file_repos.py          ← Local file implementations (JSON — real but simple)
    │   └── prediction_service.py  ← Business logic that depends ONLY on Protocols
    └── tests/
        ├── __init__.py
        └── test_prediction_service.py  ← Tests that inject in-memory repos
```

### How to Run

```bash
# Run the demo (no infrastructure required)
cd design_patterns/repository/
python3 -m src.prediction_service

# Run the tests
pytest tests/ -v
```

### Key Files

| File | Purpose |
|------|---------|
| `src/protocols.py` | Defines the contracts — WHAT operations exist, not HOW |
| `src/in_memory_repos.py` | Testing implementations — Python dicts, instant, deterministic |
| `src/file_repos.py` | Development implementations — JSON on disk, no cloud needed |
| `src/prediction_service.py` | Business logic that NEVER imports a storage library |
| `tests/test_prediction_service.py` | Comprehensive tests running in milliseconds with zero infrastructure |

### What It Proves

The `PredictionService` orchestrates feature retrieval, model loading, inference, and prediction storage — all without knowing whether it's talking to Redis, S3, PostgreSQL, or a Python dict. Tests inject `InMemory*` repos and run instantly. Production injects real implementations. The service code is identical in both cases.


