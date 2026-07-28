"""
Tests for the CQRS ML system.

Tests cover:
- Event bus publish/subscribe
- Command handlers (train, ingest)
- Query handlers (prediction, metrics)
- Event propagation (command -> event -> query side update)
"""

import numpy as np
import pytest

from src.events import Event, EventBus
from src.command_side import (
    FeatureDataStore,
    IngestDataCommand,
    IngestDataHandler,
    ModelStore,
    TrainModelCommand,
    TrainModelHandler,
)
from src.query_side import (
    MetricsQuery,
    MetricsQueryHandler,
    MetricsReadStore,
    PredictionQuery,
    PredictionQueryHandler,
    ReadModelStore,
)
from src.ml_system import MLSystem


# ═══════════════════════════════════════
# EVENT BUS TESTS
# ═══════════════════════════════════════


class TestEventBus:
    def test_publish_calls_subscriber(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda e: received.append(e))

        event = Event(event_type="test_event", payload={"key": "value"})
        bus.publish(event)

        assert len(received) == 1
        assert received[0].payload == {"key": "value"}

    def test_multiple_subscribers(self):
        bus = EventBus()
        results_a = []
        results_b = []
        bus.subscribe("test_event", lambda e: results_a.append(e))
        bus.subscribe("test_event", lambda e: results_b.append(e))

        bus.publish(Event(event_type="test_event", payload={}))

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_subscriber_only_receives_matching_events(self):
        bus = EventBus()
        received = []
        bus.subscribe("type_a", lambda e: received.append(e))

        bus.publish(Event(event_type="type_b", payload={}))

        assert len(received) == 0

    def test_history_tracks_all_events(self):
        bus = EventBus()
        bus.publish(Event(event_type="first", payload={"n": 1}))
        bus.publish(Event(event_type="second", payload={"n": 2}))

        assert len(bus.history) == 2
        assert bus.history[0].event_type == "first"
        assert bus.history[1].event_type == "second"

    def test_clear_resets_bus(self):
        bus = EventBus()
        bus.subscribe("x", lambda e: None)
        bus.publish(Event(event_type="x", payload={}))

        bus.clear()

        assert len(bus.history) == 0


# ═══════════════════════════════════════
# COMMAND HANDLER TESTS
# ═══════════════════════════════════════


class TestTrainModelHandler:
    def setup_method(self):
        self.event_bus = EventBus()
        self.model_store = ModelStore()
        self.handler = TrainModelHandler(self.model_store, self.event_bus)

    def test_train_produces_model(self):
        command = TrainModelCommand(
            model_name="test_model",
            n_samples=200,
            n_features=10,
            hyperparameters={"n_estimators": 10, "max_depth": 3, "random_state": 42},
        )
        result = self.handler.handle(command)

        assert result["model_name"] == "test_model"
        assert "accuracy" in result["metrics"]
        assert result["metrics"]["accuracy"] > 0.5

    def test_train_saves_to_store(self):
        command = TrainModelCommand(
            model_name="stored_model",
            n_samples=200,
            n_features=10,
            hyperparameters={"n_estimators": 10, "max_depth": 3, "random_state": 42},
        )
        self.handler.handle(command)

        model = self.model_store.get_model("stored_model")
        assert model is not None
        assert hasattr(model, "predict")

    def test_train_publishes_event(self):
        command = TrainModelCommand(
            model_name="event_model",
            n_samples=200,
            n_features=10,
            hyperparameters={"n_estimators": 10, "max_depth": 3, "random_state": 42},
        )
        self.handler.handle(command)

        assert len(self.event_bus.history) == 1
        event = self.event_bus.history[0]
        assert event.event_type == "model_trained"
        assert event.payload["model_name"] == "event_model"
        assert "metrics" in event.payload

    def test_trained_model_can_predict(self):
        command = TrainModelCommand(
            model_name="predict_model",
            n_samples=500,
            n_features=15,
            hyperparameters={"n_estimators": 20, "max_depth": 5, "random_state": 42},
        )
        self.handler.handle(command)

        model = self.model_store.get_model("predict_model")
        features = np.random.randn(1, 15)
        prediction = model.predict(features)
        assert prediction.shape == (1,)
        assert prediction[0] in [0, 1]


class TestIngestDataHandler:
    def setup_method(self):
        self.event_bus = EventBus()
        self.data_store = FeatureDataStore()
        self.handler = IngestDataHandler(self.data_store, self.event_bus)

    def test_ingest_saves_data(self):
        command = IngestDataCommand(
            source="s3://test/data.parquet",
            n_samples=100,
            n_features=10,
        )
        result = self.handler.handle(command)

        assert result["status"] == "ingested"
        assert "s3://test/data.parquet" in self.data_store.datasets

    def test_ingest_publishes_event(self):
        command = IngestDataCommand(
            source="s3://test/batch.csv",
            n_samples=50,
            n_features=5,
        )
        self.handler.handle(command)

        assert len(self.event_bus.history) == 1
        event = self.event_bus.history[0]
        assert event.event_type == "data_ingested"
        assert event.payload["source"] == "s3://test/batch.csv"


# ═══════════════════════════════════════
# QUERY HANDLER TESTS
# ═══════════════════════════════════════


class TestPredictionQueryHandler:
    def setup_method(self):
        self.event_bus = EventBus()
        self.read_store = ReadModelStore()
        self.handler = PredictionQueryHandler(self.read_store, self.event_bus)

    def test_predict_raises_when_no_model(self):
        query = PredictionQuery(features=np.random.randn(10))
        with pytest.raises(RuntimeError, match="No model available"):
            self.handler.handle(query)

    def test_predict_single_sample(self):
        # Train a model and load into read store
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification

        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        self.read_store.load_model("test_model", model)

        query = PredictionQuery(features=np.random.randn(10), request_id="req-1")
        result = self.handler.handle(query)

        assert result["request_id"] == "req-1"
        assert len(result["predictions"]) == 1
        assert result["predictions"][0] in [0, 1]
        assert 0.0 <= result["confidence"][0] <= 1.0
        assert result["model_name"] == "test_model"

    def test_predict_batch(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification

        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        self.read_store.load_model("batch_model", model)

        query = PredictionQuery(features=np.random.randn(5, 10), request_id="batch")
        result = self.handler.handle(query)

        assert len(result["predictions"]) == 5
        assert len(result["confidence"]) == 5


class TestMetricsQueryHandler:
    def setup_method(self):
        self.event_bus = EventBus()
        self.metrics_store = MetricsReadStore()
        self.handler = MetricsQueryHandler(self.metrics_store, self.event_bus)

    def test_no_metrics_returns_error(self):
        result = self.handler.handle(MetricsQuery())
        assert "error" in result

    def test_metrics_after_update(self):
        self.metrics_store.update_metrics("model_a", {"accuracy": 0.95})

        result = self.handler.handle(MetricsQuery())
        assert result["metrics"]["accuracy"] == 0.95
        assert result["model_name"] == "model_a"

    def test_metrics_for_specific_model(self):
        self.metrics_store.update_metrics("v1", {"accuracy": 0.80})
        self.metrics_store.update_metrics("v2", {"accuracy": 0.90})

        result = self.handler.handle(MetricsQuery(model_name="v1"))
        assert result["metrics"]["accuracy"] == 0.80


# ═══════════════════════════════════════
# INTEGRATION: EVENT PROPAGATION
# ═══════════════════════════════════════


class TestEventPropagation:
    """Tests the full flow: command -> event -> query side update."""

    def test_train_event_updates_query_side(self):
        """The core CQRS flow: training publishes event, query side reloads."""
        system = MLSystem()

        # Before training, prediction should fail
        with pytest.raises(RuntimeError):
            system.predict(np.random.randn(20))

        # Train a model (command)
        system.train_model(TrainModelCommand(
            model_name="integration_model",
            n_samples=300,
            n_features=20,
            hyperparameters={"n_estimators": 10, "max_depth": 5, "random_state": 42},
        ))

        # Now prediction should work (event propagated to query side)
        result = system.predict(np.random.randn(20), request_id="integration")
        assert result["model_name"] == "integration_model"
        assert result["predictions"][0] in [0, 1]

    def test_metrics_propagated_via_event(self):
        """Metrics are cached in query side after training."""
        system = MLSystem()

        system.train_model(TrainModelCommand(
            model_name="metrics_model",
            n_samples=300,
            n_features=20,
            hyperparameters={"n_estimators": 10, "max_depth": 5, "random_state": 42},
        ))

        metrics = system.get_metrics()
        assert "metrics" in metrics
        assert metrics["metrics"]["accuracy"] > 0.5

    def test_second_model_replaces_first(self):
        """Training v2 makes query side use v2 automatically."""
        system = MLSystem()

        system.train_model(TrainModelCommand(
            model_name="v1",
            n_samples=200,
            n_features=20,
            hyperparameters={"n_estimators": 10, "max_depth": 3, "random_state": 42},
        ))
        result_v1 = system.predict(np.random.randn(20))
        assert result_v1["model_name"] == "v1"

        system.train_model(TrainModelCommand(
            model_name="v2",
            n_samples=200,
            n_features=20,
            hyperparameters={"n_estimators": 50, "max_depth": 8, "random_state": 42},
        ))
        result_v2 = system.predict(np.random.randn(20))
        assert result_v2["model_name"] == "v2"

    def test_event_history_is_complete(self):
        """All events are recorded in the event bus history."""
        system = MLSystem()

        system.ingest_data(IngestDataCommand(source="s3://x", n_samples=50))
        system.train_model(TrainModelCommand(
            model_name="hist_model",
            n_samples=200,
            n_features=20,
            hyperparameters={"n_estimators": 10, "max_depth": 3, "random_state": 42},
        ))

        types = [e.event_type for e in system.event_bus.history]
        assert "data_ingested" in types
        assert "model_trained" in types


