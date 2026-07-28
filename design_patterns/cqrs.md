# CQRS — Command Query Responsibility Segregation

## The One-Line Summary

**Separate the code that CHANGES data from the code that READS data, because they have completely different needs.**

---

## The Exact Problem (ML Context)

Imagine you have a single service that handles both model training AND model inference:

```python
# ❌ WITHOUT CQRS — Single service doing everything

class MLService:
    def __init__(self, db):
        self.db = db
        self.model = None

    def train_model(self, dataset_path: str):
        """WRITE operation — slow, heavy, runs for hours."""
        data = load_large_dataset(dataset_path)  # 50GB, takes 10 min
        self.model = train_xgboost(data)         # Takes 2 hours on GPU
        self.db.save_model(self.model)           # Locks DB for large write
        self.db.update_metrics(evaluate(self.model))

    def predict(self, user_id: str):
        """READ operation — must be fast, <50ms."""
        features = self.db.get_features(user_id)  # DB query
        return self.model.predict(features)        # Must be instant

    def get_model_metrics(self):
        """READ operation — dashboard query."""
        return self.db.query("SELECT * FROM metrics ORDER BY date DESC")
```

**What goes wrong:**

1. Training locks the database → predictions fail during training
2. Training hogs CPU/memory → prediction latency spikes
3. You need 1 training job/day but 10,000 predictions/sec → can't scale independently
4. A bug in training code crashes the service → predictions go down too
5. Training needs a GPU cluster; inference needs a CPU fleet → different infrastructure

**The root cause:** Reads and writes have fundamentally different requirements:

| | Training (Write/Command) | Inference (Read/Query) |
|---|---|---|
| Frequency | Once per day/week | 10,000 per second |
| Latency | Hours acceptable | Must be < 50ms |
| Resources | GPU, high memory | CPU, low memory |
| Data format | Raw, full dataset | Denormalized, features only |
| Consistency | Eventual is fine | Needs latest model |
| Failure impact | Retry tomorrow | User sees error NOW |

---

## How CQRS Solves It

**Split into two separate paths:**

```
┌─────────────────────────────────────────────────────┐
│                 COMMAND SIDE                          │
│            (Writes / Mutations)                       │
│                                                      │
│  "Train model"  ─────► Command Handler              │
│  "Ingest data"  ─────► (slow, batch, GPU)           │
│  "Update features" ──► Writes to Write Store        │
│                                                      │
│  Storage: S3, PostgreSQL (write-optimized)           │
│  Scale: 1 instance, scheduled jobs                   │
└──────────────────────────┬───────────────────────────┘
                           │
                    EVENT / SYNC
                    "model_trained"
                    "features_updated"
                           │
┌──────────────────────────▼───────────────────────────┐
│                 QUERY SIDE                            │
│              (Reads / Queries)                        │
│                                                      │
│  "Get prediction" ◄──── Query Handler               │
│  "Get features"   ◄──── (fast, real-time)           │
│  "Get metrics"    ◄──── Reads from Read Store       │
│                                                      │
│  Storage: Redis, model in memory (read-optimized)    │
│  Scale: 50 instances, auto-scaling                   │
└──────────────────────────────────────────────────────┘
```

---

## How the Sync/Event Works

**Q: "How does the query side know when the command side changes something?"**

There are multiple approaches, from simple to complex:

### Approach 1: Direct Sync (Simplest — for small teams)

```python
class TrainModelHandler:
    def __init__(self, write_store, read_store):
        self.write_store = write_store
        self.read_store = read_store  # Directly updates read side

    def handle(self, command):
        model = train_model(command.data)

        # Write to primary store
        self.write_store.save_model(model)

        # Directly update the read store
        self.read_store.load_model(model)  # ← Direct sync
        self.read_store.update_cache(model.metadata)
```

**Pros:** Simple, no infrastructure.
**Cons:** Tightly couples command and query sides. If read store fails, training "fails."

### Approach 2: Event Bus (In-Process — Medium teams)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass
class Event:
    event_type: str
    payload: dict
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """Simple in-process event bus. Decouples command from query."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.event_type, []):
            handler(event)


# Command side publishes events:
class TrainModelHandler:
    def __init__(self, write_store, event_bus: EventBus):
        self.write_store = write_store
        self.event_bus = event_bus

    def handle(self, command):
        model = train_model(command.data)
        self.write_store.save_model(model)

        # Publish event — doesn't know who's listening
        self.event_bus.publish(Event(
            event_type="model_trained",
            payload={"model_id": model.id, "version": model.version, "path": model.path},
        ))


# Query side subscribes to events:
class PredictionQueryHandler:
    def __init__(self, event_bus: EventBus):
        self._model = None
        event_bus.subscribe("model_trained", self._on_model_trained)

    def _on_model_trained(self, event: Event):
        """React to new model — reload for inference."""
        self._model = load_model(event.payload["path"])
        print(f"Query side: loaded model {event.payload['model_id']}")

    def predict(self, features):
        return self._model.predict(features)
```

**Pros:** Decoupled. Query side doesn't know about command side.
**Cons:** Same process. If the service restarts, events are lost.

### Approach 3: Message Queue (Production — for real separation)

```python
# Using Redis Pub/Sub, Kafka, SQS, or RabbitMQ

# ─── Command side (separate service/pod) ───
import redis
import json

class TrainModelHandler:
    def __init__(self, write_store, redis_client):
        self.write_store = write_store
        self.redis = redis_client

    def handle(self, command):
        model = train_model(command.data)
        self.write_store.save_model(model)

        # Publish to message queue
        self.redis.publish("ml-events", json.dumps({
            "event_type": "model_trained",
            "model_id": model.id,
            "model_path": "s3://models/latest.pkl",
            "metrics": {"accuracy": 0.95},
        }))


# ─── Query side (different service/pod, subscribes to events) ───

class InferenceService:
    def __init__(self, redis_client):
        self._model = None
        self.redis = redis_client

    def start_listening(self):
        """Background thread: listen for model update events."""
        pubsub = self.redis.pubsub()
        pubsub.subscribe("ml-events")

        for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                if event["event_type"] == "model_trained":
                    self._reload_model(event["model_path"])

    def _reload_model(self, path: str):
        self._model = load_model_from_s3(path)
        print(f"Model reloaded from {path}")

    def predict(self, features):
        return self._model.predict(features)
```

### Approach 4: Kafka (Enterprise — for high-throughput, ordered events)

```python
# Command side → produces events to Kafka topic
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers="kafka:9092")
producer.send("model-events", json.dumps({
    "event_type": "model_trained",
    "model_id": "v42",
    "timestamp": "2024-01-15T10:30:00Z",
}).encode())


# Query side → consumes events from Kafka topic
from kafka import KafkaConsumer

consumer = KafkaConsumer("model-events", bootstrap_servers="kafka:9092")
for message in consumer:
    event = json.loads(message.value)
    if event["event_type"] == "model_trained":
        reload_model(event["model_id"])
```

### Which Sync Approach to Use?

| Approach | Complexity | When to Use |
|----------|-----------|-------------|
| Direct sync | Simple | Same service, small team, starting out |
| In-process event bus | Medium | Monolith, multiple handlers for same event |
| Redis Pub/Sub | Medium | Separate services, low volume, acceptable loss |
| Kafka/SQS/RabbitMQ | High | Separate services, high volume, need durability |

---

## Complete Implementation: ML System with CQRS

### The Scenario

You have:
- A **training pipeline** that runs daily on a GPU cluster
- An **inference API** that serves predictions at 5000 req/sec
- A **feature store** that gets updated hourly
- A **monitoring dashboard** that queries metrics

**Without CQRS:** All of this is one monolithic service. Training kills inference performance.

**With CQRS:** Each concern is separated with its own optimized path.

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, Any
import numpy as np


# ═══════════════════════════════════════
# SHARED TYPES
# ═══════════════════════════════════════

@dataclass
class ModelInfo:
    model_id: str
    version: str
    accuracy: float
    trained_at: datetime
    path: str


# ═══════════════════════════════════════
# COMMAND SIDE (Writes)
# ═══════════════════════════════════════

class ModelRegistry(Protocol):
    """Write-optimized store for model artifacts."""
    def save_model(self, model: Any, info: ModelInfo) -> None: ...
    def save_training_metrics(self, model_id: str, metrics: dict) -> None: ...


class EventPublisher(Protocol):
    """Publishes events for the query side to consume."""
    def publish(self, event_type: str, data: dict) -> None: ...


@dataclass
class TrainCommand:
    """Intent: 'I want to train a new model.'"""
    dataset_path: str
    algorithm: str
    hyperparameters: dict


class TrainCommandHandler:
    """
    COMMAND HANDLER — handles the training workflow.
    This runs on a GPU machine. It's slow. That's fine.
    """

    def __init__(self, registry: ModelRegistry, events: EventPublisher):
        self.registry = registry
        self.events = events

    def execute(self, command: TrainCommand) -> ModelInfo:
        import uuid

        # 1. Load data (slow — that's fine, this is the command side)
        X, y = self._load_data(command.dataset_path)

        # 2. Train (slow — GPU, hours)
        model = self._train(command.algorithm, command.hyperparameters, X, y)

        # 3. Evaluate
        from sklearn.metrics import accuracy_score
        accuracy = accuracy_score(y, model.predict(X))

        # 4. Create metadata
        info = ModelInfo(
            model_id=str(uuid.uuid4())[:8],
            version="1.0",
            accuracy=accuracy,
            trained_at=datetime.now(),
            path=f"s3://models/{command.algorithm}_latest.pkl",
        )

        # 5. Save to write store
        self.registry.save_model(model, info)
        self.registry.save_training_metrics(info.model_id, {"accuracy": accuracy})

        # 6. Notify query side: "Hey, there's a new model!"
        self.events.publish("model_trained", {
            "model_id": info.model_id,
            "path": info.path,
            "accuracy": info.accuracy,
        })

        return info

    def _load_data(self, path: str):
        from sklearn.datasets import make_classification
        return make_classification(n_samples=5000, n_features=20, random_state=42)

    def _train(self, algorithm, hyperparams, X, y):
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(**hyperparams, random_state=42)
        model.fit(X, y)
        return model


# ═══════════════════════════════════════
# QUERY SIDE (Reads)
# ═══════════════════════════════════════

class FeatureStore(Protocol):
    """Read-optimized feature lookups (Redis, DynamoDB, etc)."""
    def get_features(self, user_id: str) -> np.ndarray: ...


class PredictionQueryHandler:
    """
    QUERY HANDLER — handles prediction requests.
    This runs on a CPU fleet. Must be FAST (<50ms).
    """

    def __init__(self, feature_store: FeatureStore):
        self.feature_store = feature_store
        self._model = None
        self._model_info: ModelInfo | None = None

    def predict(self, user_id: str) -> dict:
        """The read path — optimized for speed."""
        if self._model is None:
            raise RuntimeError("No model loaded. Waiting for model_trained event.")

        # Fast feature lookup (from read-optimized store like Redis)
        features = self.feature_store.get_features(user_id)

        # Fast inference (model already in memory)
        prediction = self._model.predict(features.reshape(1, -1))[0]
        probabilities = self._model.predict_proba(features.reshape(1, -1))[0]

        return {
            "user_id": user_id,
            "prediction": int(prediction),
            "confidence": float(max(probabilities)),
            "model_id": self._model_info.model_id,
        }

    def on_model_trained(self, event_data: dict) -> None:
        """
        EVENT HANDLER — called when command side publishes 'model_trained'.
        Reloads the model into memory for fast inference.
        """
        import joblib
        # In production: download from S3 path in event_data
        # self._model = joblib.load(download_from_s3(event_data["path"]))
        print(f"  📥 Query side: reloading model {event_data['model_id']}")
        # For demo, just note that we'd reload here
        self._model_info = ModelInfo(
            model_id=event_data["model_id"],
            version="latest",
            accuracy=event_data["accuracy"],
            trained_at=datetime.now(),
            path=event_data["path"],
        )


# ═══════════════════════════════════════
# WIRING — How it all connects
# ═══════════════════════════════════════

class SimpleEventBus:
    """Simple sync mechanism — in production, replace with Kafka/Redis."""
    def __init__(self):
        self._subscribers: dict[str, list] = {}

    def subscribe(self, event_type: str, handler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, data: dict) -> None:
        for handler in self._subscribers.get(event_type, []):
            handler(data)


class InMemoryRegistry:
    """Satisfies ModelRegistry Protocol."""
    def __init__(self):
        self.models = {}
        self.metrics = {}

    def save_model(self, model, info: ModelInfo) -> None:
        self.models[info.model_id] = (model, info)

    def save_training_metrics(self, model_id: str, metrics: dict) -> None:
        self.metrics[model_id] = metrics


class InMemoryFeatureStore:
    """Satisfies FeatureStore Protocol."""
    def get_features(self, user_id: str) -> np.ndarray:
        # In production: Redis/DynamoDB lookup
        np.random.seed(hash(user_id) % 2**32)
        return np.random.randn(20)


# ─── Usage ───

def demo():
    # Setup
    event_bus = SimpleEventBus()
    registry = InMemoryRegistry()
    feature_store = InMemoryFeatureStore()

    # Create handlers
    train_handler = TrainCommandHandler(registry=registry, events=event_bus)
    predict_handler = PredictionQueryHandler(feature_store=feature_store)

    # Subscribe query side to events from command side
    event_bus.subscribe("model_trained", predict_handler.on_model_trained)

    # ─── Command: Train a model (slow, batch) ───
    print("=== COMMAND SIDE: Training ===")
    command = TrainCommand(
        dataset_path="s3://data/training.parquet",
        algorithm="random_forest",
        hyperparameters={"n_estimators": 50, "max_depth": 5},
    )
    model_info = train_handler.execute(command)
    print(f"  Model trained: {model_info.model_id} (accuracy={model_info.accuracy:.4f})")

    # At this point, the event "model_trained" was published
    # and predict_handler.on_model_trained() was called automatically

    # ─── Query: Get predictions (fast, real-time) ───
    print("\n=== QUERY SIDE: Predicting ===")
    # In reality, predict_handler would have reloaded the model
    # For demo, let's manually set it:
    predict_handler._model = registry.models[model_info.model_id][0]

    result = predict_handler.predict("user_123")
    print(f"  Prediction: {result}")

    result = predict_handler.predict("user_456")
    print(f"  Prediction: {result}")


if __name__ == "__main__":
    demo()
```

---

## When to Use CQRS

| ✅ Use CQRS When | ❌ Don't Use When |
|---|---|
| Reads and writes have different performance needs | Simple CRUD app with equal read/write load |
| You need to scale reads independently (10000x) | Small dataset, low traffic |
| Write operations are slow/batch (training) | Writes are fast and simple |
| Read operations need denormalized/cached views | Read model = write model (same schema) |
| You want different storage for each side | One database is sufficient |
| Training and inference need different infrastructure | Everything runs on one machine |

---

## Summary

```
CQRS = "Don't make your fast read path suffer because of your slow write path."

COMMAND: "Train this model" → Takes hours → Writes to S3/DB → Publishes event
QUERY:   "Predict this"    → Takes 10ms  → Reads from Redis/Memory → Returns result

The EVENT is the bridge:
  Command finishes → publishes "model_trained" → Query side reloads model
```

## Working Implementation

A fully runnable implementation lives in `design_patterns/cqrs/`:

```
cqrs/
├── README.md              # Explains CQRS in ML context + event sync mechanism
├── src/
│   ├── __init__.py
│   ├── events.py          # Event dataclass + EventBus (in-process, dict-based)
│   ├── command_side.py    # TrainModelCommand, IngestDataCommand + handlers (uses sklearn)
│   ├── query_side.py      # PredictionQuery, PredictionQueryHandler, MetricsQueryHandler
│   └── ml_system.py       # Composition root wiring command + query via EventBus
└── tests/
    ├── __init__.py
    └── test_cqrs.py       # 21 tests covering handlers, events, and propagation
```

### Running

```bash
# Demo: train → event → query side reload → predictions
cd design_patterns/cqrs
python3 -m src.ml_system

# Tests
python3 -m pytest tests/ -v
```

### Key Files

| File | Role |
|------|------|
| `events.py` | `Event` dataclass + `EventBus` with subscribe/publish/history |
| `command_side.py` | Commands (TrainModel, IngestData), write stores, handlers that train with sklearn and publish events |
| `query_side.py` | Queries (Prediction, Metrics), read stores, handlers that auto-subscribe to events |
| `ml_system.py` | Wires both sides together; bridge syncs model from write→read store on event |

### Demo Output Flow

```
COMMAND: TrainModelCommand("fraud_detector_v1")
  → TrainModelHandler trains RandomForest via sklearn
  → Saves model to ModelStore (write side)
  → Publishes Event("model_trained") on EventBus
  → PredictionQueryHandler._on_model_trained() fires
  → MLSystem._sync_model_to_read_store() loads model into ReadModelStore

QUERY: PredictionQuery(features)
  → PredictionQueryHandler reads from ReadModelStore (in-memory)
  → Returns prediction + confidence in <50ms
```
