"""
Command Side — handles all write/mutation operations.

Commands represent intents: "I want to train a model", "I want to ingest data".
Handlers execute those intents and publish events for the query side.

In production, this runs on GPU clusters for training,
or on batch processing nodes for data ingestion.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from .events import Event, EventBus


# ═══════════════════════════════════════
# COMMANDS (Data Transfer Objects)
# ═══════════════════════════════════════


@dataclass
class TrainModelCommand:
    """Intent: Train a new ML model."""

    model_name: str
    n_samples: int = 1000
    n_features: int = 20
    algorithm: str = "random_forest"
    hyperparameters: dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42,
    })
    test_size: float = 0.2


@dataclass
class IngestDataCommand:
    """Intent: Ingest new data into the feature store."""

    source: str  # e.g., "s3://bucket/data.parquet"
    n_samples: int = 500
    n_features: int = 20


# ═══════════════════════════════════════
# WRITE STORES
# ═══════════════════════════════════════


class ModelStore:
    """
    Write-optimized model storage.
    In production: S3 + model registry (MLflow, SageMaker).
    """

    def __init__(self) -> None:
        self.models: dict[str, Any] = {}
        self.metadata: dict[str, dict] = {}
        self.metrics: dict[str, dict] = {}

    def save_model(self, model_name: str, model: Any, metadata: dict) -> None:
        self.models[model_name] = model
        self.metadata[model_name] = metadata

    def save_metrics(self, model_name: str, metrics: dict) -> None:
        self.metrics[model_name] = metrics

    def get_model(self, model_name: str) -> Any:
        return self.models.get(model_name)


class FeatureDataStore:
    """
    Write-optimized feature storage.
    In production: S3/Delta Lake for raw features.
    """

    def __init__(self) -> None:
        self.datasets: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    def save(self, source: str, X: np.ndarray, y: np.ndarray) -> None:
        self.datasets[source] = (X, y)


# ═══════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════


class TrainModelHandler:
    """
    Handles TrainModelCommand — trains a model and publishes event.

    This handler is slow (training takes time). That's intentional.
    The query side stays fast because it only reloads the final artifact.
    """

    def __init__(self, model_store: ModelStore, event_bus: EventBus) -> None:
        self.model_store = model_store
        self.event_bus = event_bus

    def handle(self, command: TrainModelCommand) -> dict:
        """Execute training pipeline and publish event."""
        # 1. Generate/load data
        X, y = make_classification(
            n_samples=command.n_samples,
            n_features=command.n_features,
            n_informative=command.n_features // 2,
            random_state=42,
        )

        # 2. Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=command.test_size, random_state=42
        )

        # 3. Train
        model = RandomForestClassifier(**command.hyperparameters)
        model.fit(X_train, y_train)

        # 4. Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred, average="weighted"),
            "precision": precision_score(y_test, y_pred, average="weighted"),
            "recall": recall_score(y_test, y_pred, average="weighted"),
            "n_train_samples": len(X_train),
            "n_test_samples": len(X_test),
        }

        # 5. Persist to write store
        metadata = {
            "model_name": command.model_name,
            "algorithm": command.algorithm,
            "hyperparameters": command.hyperparameters,
            "trained_at": datetime.now().isoformat(),
            "n_features": command.n_features,
        }
        self.model_store.save_model(command.model_name, model, metadata)
        self.model_store.save_metrics(command.model_name, metrics)

        # 6. Publish event — query side will react
        self.event_bus.publish(Event(
            event_type="model_trained",
            payload={
                "model_name": command.model_name,
                "metrics": metrics,
                "metadata": metadata,
            },
        ))

        return {"model_name": command.model_name, "metrics": metrics}


class IngestDataHandler:
    """
    Handles IngestDataCommand — ingests data and publishes event.

    In production: reads from S3, transforms, writes to feature store.
    """

    def __init__(self, data_store: FeatureDataStore, event_bus: EventBus) -> None:
        self.data_store = data_store
        self.event_bus = event_bus

    def handle(self, command: IngestDataCommand) -> dict:
        """Execute data ingestion and publish event."""
        X, y = make_classification(
            n_samples=command.n_samples,
            n_features=command.n_features,
            random_state=123,
        )

        # Persist to write store
        self.data_store.save(command.source, X, y)

        # Publish event
        self.event_bus.publish(Event(
            event_type="data_ingested",
            payload={
                "source": command.source,
                "n_samples": command.n_samples,
                "n_features": command.n_features,
                "ingested_at": datetime.now().isoformat(),
            },
        ))

        return {
            "source": command.source,
            "n_samples": command.n_samples,
            "status": "ingested",
        }


