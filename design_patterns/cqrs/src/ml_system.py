"""
ML System — wires command side + query side together via EventBus.

This is the composition root: it creates all components, connects events,
and orchestrates the flow between command and query sides.

Run:  python -m src.ml_system
"""

import numpy as np

from .command_side import (
    IngestDataCommand,
    IngestDataHandler,
    FeatureDataStore,
    ModelStore,
    TrainModelCommand,
    TrainModelHandler,
)
from .events import Event, EventBus
from .query_side import (
    MetricsQuery,
    MetricsQueryHandler,
    MetricsReadStore,
    PredictionQuery,
    PredictionQueryHandler,
    ReadModelStore,
)


class MLSystem:
    """
    Composition root that wires CQRS components together.

    Responsibilities:
    - Creates command and query handlers
    - Connects them via the EventBus
    - Provides a clean API for the application layer
    """

    def __init__(self) -> None:
        # Shared event bus (in production: Kafka/Redis)
        self.event_bus = EventBus()

        # --- Command side stores ---
        self.model_store = ModelStore()
        self.data_store = FeatureDataStore()

        # --- Query side stores (read-optimized) ---
        self.read_model_store = ReadModelStore()
        self.metrics_read_store = MetricsReadStore()

        # --- Command handlers ---
        self.train_handler = TrainModelHandler(self.model_store, self.event_bus)
        self.ingest_handler = IngestDataHandler(self.data_store, self.event_bus)

        # --- Query handlers (auto-subscribe to events) ---
        self.prediction_handler = PredictionQueryHandler(
            self.read_model_store, self.event_bus
        )
        self.metrics_handler = MetricsQueryHandler(
            self.metrics_read_store, self.event_bus
        )

        # --- Bridge: sync model from write store to read store ---
        self.event_bus.subscribe("model_trained", self._sync_model_to_read_store)

    def _sync_model_to_read_store(self, event: Event) -> None:
        """
        When a model is trained, load it into the read store.
        In production: query side downloads from S3 into memory.
        """
        model_name = event.payload["model_name"]
        model = self.model_store.get_model(model_name)
        if model is not None:
            self.read_model_store.load_model(model_name, model)
            print(f"  [MLSystem] synced model '{model_name}' to read store")

    # --- Public API ---

    def train_model(self, command: TrainModelCommand) -> dict:
        """Execute a training command."""
        return self.train_handler.handle(command)

    def ingest_data(self, command: IngestDataCommand) -> dict:
        """Execute a data ingestion command."""
        return self.ingest_handler.handle(command)

    def predict(self, features: np.ndarray, request_id: str = "default") -> dict:
        """Execute a prediction query."""
        query = PredictionQuery(features=features, request_id=request_id)
        return self.prediction_handler.handle(query)

    def get_metrics(self, model_name: str | None = None) -> dict:
        """Execute a metrics query."""
        query = MetricsQuery(model_name=model_name)
        return self.metrics_handler.handle(query)


def demo() -> None:
    """
    Full CQRS demo flow:
    1. Ingest data (command) -> event published
    2. Train model (command) -> event published -> query side reloads
    3. Get predictions (query) -> uses model loaded by event
    4. Get metrics (query) -> uses metrics cached by event
    """
    print("=" * 60)
    print("  CQRS Pattern Demo - ML System")
    print("=" * 60)

    system = MLSystem()

    # Step 1: Ingest Data (Command)
    print("\n--- STEP 1: COMMAND - Ingest Data ---")
    result = system.ingest_data(IngestDataCommand(
        source="s3://ml-data/training_batch_001.parquet",
        n_samples=1000,
        n_features=20,
    ))
    print(f"  Data ingested: {result['n_samples']} samples from {result['source']}")

    # Step 2: Train Model (Command -> Event -> Query side reloads)
    print("\n--- STEP 2: COMMAND - Train Model ---")
    result = system.train_model(TrainModelCommand(
        model_name="fraud_detector_v1",
        n_samples=2000,
        n_features=20,
        hyperparameters={"n_estimators": 50, "max_depth": 8, "random_state": 42},
    ))
    print(f"  Model trained: {result['model_name']}")
    print(f"  Accuracy: {result['metrics']['accuracy']:.4f}")
    print(f"  F1 Score: {result['metrics']['f1_score']:.4f}")

    # Step 3: Predictions (Query - fast, uses in-memory model)
    print("\n--- STEP 3: QUERY - Get Predictions ---")
    features = np.random.randn(20)
    prediction = system.predict(features, request_id="req-001")
    print(
        f"  req-001: prediction={prediction['predictions'][0]}, "
        f"confidence={prediction['confidence'][0]:.3f}"
    )

    batch_features = np.random.randn(5, 20)
    batch_result = system.predict(batch_features, request_id="req-batch")
    print(
        f"  req-batch: {len(batch_result['predictions'])} predictions, "
        f"avg confidence={np.mean(batch_result['confidence']):.3f}"
    )

    # Step 4: Metrics (Query - from read-optimized cache)
    print("\n--- STEP 4: QUERY - Get Metrics ---")
    metrics = system.get_metrics()
    print(f"  Model: {metrics['model_name']}")
    for k, v in metrics["metrics"].items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}")
        else:
            print(f"    {k}: {v}")

    # Step 5: Train v2 - event system auto-updates query side
    print("\n--- STEP 5: COMMAND - Train v2 ---")
    result = system.train_model(TrainModelCommand(
        model_name="fraud_detector_v2",
        n_samples=5000,
        n_features=20,
        hyperparameters={"n_estimators": 200, "max_depth": 12, "random_state": 42},
    ))
    print(f"  Model v2 trained: accuracy={result['metrics']['accuracy']:.4f}")

    # Step 6: Query side now uses v2 automatically
    print("\n--- STEP 6: QUERY - Predictions now use v2 ---")
    prediction = system.predict(np.random.randn(20), request_id="req-v2")
    print(f"  Model used: {prediction['model_name']}")
    print(
        f"  Prediction: {prediction['predictions'][0]}, "
        f"confidence={prediction['confidence'][0]:.3f}"
    )

    # Event history
    print("\n--- EVENT HISTORY ---")
    for event in system.event_bus.history:
        name = event.payload.get("model_name", event.payload.get("source", "N/A"))
        print(f"  {event.timestamp:%H:%M:%S} | {event.event_type:15s} | {name}")

    print("\n  Done! Flow: Command -> Event -> Query side reloads -> Predictions work")


if __name__ == "__main__":
    demo()


