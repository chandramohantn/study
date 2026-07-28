"""
Repository Protocols — Define WHAT data operations exist, not HOW they work.

These are the contracts your business logic depends on.
Any class that implements these methods satisfies the Protocol.
No inheritance required (structural subtyping / duck typing).
"""

from __future__ import annotations

from typing import Protocol


class FeatureRepository(Protocol):
    """
    Contract for accessing ML features.

    Could be backed by: Redis, PostgreSQL, Feast, a CSV file, or a Python dict.
    Your service code doesn't know and doesn't care.
    """

    def get_features(self, entity_id: str) -> dict:
        """Retrieve feature vector for a single entity."""
        ...

    def get_batch_features(self, entity_ids: list[str]) -> list[dict]:
        """Retrieve feature vectors for multiple entities."""
        ...

    def save_features(self, entity_id: str, features: dict) -> None:
        """Persist a feature vector for an entity."""
        ...


class PredictionRepository(Protocol):
    """
    Contract for storing and retrieving predictions.

    Could be backed by: S3, DynamoDB, PostgreSQL, a JSON file, or a Python list.
    """

    def save_prediction(self, prediction: dict) -> None:
        """Store a single prediction result."""
        ...

    def save_predictions(self, predictions: list[dict]) -> None:
        """Store a batch of prediction results."""
        ...

    def get_predictions(self, model_id: str, limit: int = 100) -> list[dict]:
        """Retrieve predictions made by a specific model."""
        ...


class ModelRepository(Protocol):
    """
    Contract for model artifact storage and retrieval.

    Could be backed by: S3 + DynamoDB, MLflow, local filesystem, or a dict.
    """

    def save_model(self, model_id: str, model_bytes: bytes, metadata: dict) -> None:
        """Persist a serialized model and its metadata."""
        ...

    def load_model(self, model_id: str) -> tuple[bytes, dict]:
        """Load a serialized model and its metadata. Raises KeyError if not found."""
        ...

    def get_latest_model_id(self) -> str:
        """Return the ID of the most recently saved model. Raises KeyError if empty."""
        ...

    def list_models(self) -> list[str]:
        """Return all registered model IDs."""
        ...


