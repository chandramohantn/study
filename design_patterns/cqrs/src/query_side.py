"""
Query Side — handles all read operations.

Query handlers are optimized for speed. They keep models in memory,
features in fast-access stores, and return results in <50ms.

In production, this runs on a CPU auto-scaling fleet.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from .events import Event, EventBus


# ═══════════════════════════════════════
# QUERIES (Data Transfer Objects)
# ═══════════════════════════════════════


@dataclass
class PredictionQuery:
    """Request: Get a prediction for given features."""

    features: np.ndarray  # Shape: (n_features,) or (n_samples, n_features)
    request_id: str = "default"


@dataclass
class MetricsQuery:
    """Request: Get metrics for a specific model."""

    model_name: str | None = None  # None = get latest


# ═══════════════════════════════════════
# READ STORES (optimized for fast access)
# ═══════════════════════════════════════


class ReadModelStore:
    """
    Read-optimized model store — keeps models in memory.
    In production: model loaded from S3 into memory on startup,
    reloaded when 'model_trained' event arrives.
    """

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self._latest_model_name: str | None = None

    def load_model(self, model_name: str, model: Any) -> None:
        """Load a model into the read store (triggered by events)."""
        self._models[model_name] = model
        self._latest_model_name = model_name

    def get_model(self, model_name: str | None = None) -> Any:
        """Get a model by name, or the latest if no name given."""
        name = model_name or self._latest_model_name
        if name is None:
            return None
        return self._models.get(name)

    @property
    def latest_model_name(self) -> str | None:
        return self._latest_model_name


class MetricsReadStore:
    """
    Read-optimized metrics store.
    In production: Redis or a pre-computed dashboard cache.
    """

    def __init__(self) -> None:
        self._metrics: dict[str, dict] = {}
        self._latest_model_name: str | None = None

    def update_metrics(self, model_name: str, metrics: dict) -> None:
        self._metrics[model_name] = metrics
        self._latest_model_name = model_name

    def get_metrics(self, model_name: str | None = None) -> dict | None:
        name = model_name or self._latest_model_name
        if name is None:
            return None
        return self._metrics.get(name)

    @property
    def all_metrics(self) -> dict[str, dict]:
        return dict(self._metrics)


# ═══════════════════════════════════════
# QUERY HANDLERS
# ═══════════════════════════════════════


class PredictionQueryHandler:
    """
    Handles prediction queries.

    Keeps the model in memory for fast inference (<50ms).
    Reloads model automatically when 'model_trained' event arrives.
    """

    def __init__(self, read_store: ReadModelStore, event_bus: EventBus) -> None:
        self.read_store = read_store
        event_bus.subscribe("model_trained", self._on_model_trained)

    def handle(self, query: PredictionQuery) -> dict:
        """Execute prediction query — must be fast."""
        model = self.read_store.get_model()
        if model is None:
            raise RuntimeError("No model available. Waiting for model_trained event.")

        features = query.features
        if features.ndim == 1:
            features = features.reshape(1, -1)

        predictions = model.predict(features)
        probabilities = model.predict_proba(features)
        confidence = np.max(probabilities, axis=1)

        return {
            "request_id": query.request_id,
            "predictions": predictions.tolist(),
            "confidence": confidence.tolist(),
            "model_name": self.read_store.latest_model_name,
        }

    def _on_model_trained(self, event: Event) -> None:
        """Event handler: log that a new model is available."""
        model_name = event.payload["model_name"]
        metrics = event.payload.get("metrics", {})
        accuracy = metrics.get("accuracy", 0)
        print(
            f"  [PredictionQueryHandler] new model '{model_name}' "
            f"available (accuracy={accuracy:.4f})"
        )


class MetricsQueryHandler:
    """
    Handles metrics queries — returns model performance data.

    Read-optimized: metrics are cached in a fast store,
    updated when 'model_trained' events arrive.
    """

    def __init__(self, metrics_store: MetricsReadStore, event_bus: EventBus) -> None:
        self.metrics_store = metrics_store
        event_bus.subscribe("model_trained", self._on_model_trained)

    def handle(self, query: MetricsQuery) -> dict:
        """Return metrics for a model."""
        metrics = self.metrics_store.get_metrics(query.model_name)
        if metrics is None:
            return {"error": "No metrics available", "model_name": query.model_name}

        return {
            "model_name": query.model_name or self.metrics_store._latest_model_name,
            "metrics": metrics,
        }

    def _on_model_trained(self, event: Event) -> None:
        """Event handler: cache new metrics in the read store."""
        model_name = event.payload["model_name"]
        metrics = event.payload.get("metrics", {})
        self.metrics_store.update_metrics(model_name, metrics)
        print(f"  [MetricsQueryHandler] cached metrics for '{model_name}'")


