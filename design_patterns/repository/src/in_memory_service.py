"""
In-Memory Repository Implementations — For testing and local development.

These satisfy the Protocols using plain Python data structures.
No database. No network. No AWS. No dependencies beyond Python stdlib.

Usage:
    repo = InMemoryFeatureRepository()
    repo.seed({"user_1": {"age": 25, "income": 50000}})
    features = repo.get_features("user_1")  # instant, deterministic
"""

from __future__ import annotations

from datetime import datetime, timezone


class InMemoryFeatureRepository:
    """
    In-memory implementation of FeatureRepository Protocol.
    Backed by a simple dict[entity_id, features_dict].
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get_features(self, entity_id: str) -> dict:
        return self._store.get(entity_id, {})

    def get_batch_features(self, entity_ids: list[str]) -> list[dict]:
        results = []
        for eid in entity_ids:
            features = self._store.get(eid)
            if features is not None:
                results.append({"entity_id": eid, **features})
        return results

    def save_features(self, entity_id: str, features: dict) -> None:
        self._store[entity_id] = features

    # ─── Test helpers (not in Protocol — only available in tests) ───

    def seed(self, data: dict[str, dict]) -> None:
        """Pre-populate the store with test data."""
        self._store = dict(data)

    def clear(self) -> None:
        """Reset the store."""
        self._store.clear()

    @property
    def count(self) -> int:
        """Number of entities stored."""
        return len(self._store)


class InMemoryPredictionRepository:
    """
    In-memory implementation of PredictionRepository Protocol.
    Backed by a simple list of prediction dicts.
    """

    def __init__(self) -> None:
        self._predictions: list[dict] = []

    def save_prediction(self, prediction: dict) -> None:
        self._predictions.append(prediction)

    def save_predictions(self, predictions: list[dict]) -> None:
        self._predictions.extend(predictions)

    def get_predictions(self, model_id: str, limit: int = 100) -> list[dict]:
        filtered = [p for p in self._predictions if p.get("model_id") == model_id]
        return filtered[:limit]

    # ─── Test helpers ───

    @property
    def all_predictions(self) -> list[dict]:
        """Access all stored predictions (for test assertions)."""
        return list(self._predictions)

    @property
    def saved_count(self) -> int:
        """Total number of predictions stored."""
        return len(self._predictions)

    def clear(self) -> None:
        self._predictions.clear()


class InMemoryModelRepository:
    """
    In-memory implementation of ModelRepository Protocol.
    Stores model bytes and metadata in a dict.
    """

    def __init__(self) -> None:
        self._models: dict[str, tuple[bytes, dict]] = {}
        self._order: list[str] = []  # track insertion order for get_latest

    def save_model(self, model_id: str, model_bytes: bytes, metadata: dict) -> None:
        enriched_metadata = {
            **metadata,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._models[model_id] = (model_bytes, enriched_metadata)
        if model_id not in self._order:
            self._order.append(model_id)

    def load_model(self, model_id: str) -> tuple[bytes, dict]:
        if model_id not in self._models:
            raise KeyError(f"Model '{model_id}' not found")
        return self._models[model_id]

    def get_latest_model_id(self) -> str:
        if not self._order:
            raise KeyError("No models registered")
        return self._order[-1]

    def list_models(self) -> list[str]:
        return list(self._order)

    # ─── Test helpers ───

    @property
    def count(self) -> int:
        return len(self._models)

    def clear(self) -> None:
        self._models.clear()
        self._order.clear()


