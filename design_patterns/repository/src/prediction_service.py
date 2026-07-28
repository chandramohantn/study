"""
PredictionService — Business logic that depends ONLY on Protocols.

Key insight:
    This file does NOT import boto3, sqlalchemy, redis, or any storage library.
    It only knows about the Protocols (interfaces). The actual implementation
    is injected at construction time.

    This means:
    - You can test it with in-memory fakes (fast, no infrastructure)
    - You can swap storage backends without touching business logic
    - You can run locally with file repos and in prod with S3/PostgreSQL
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.protocols import FeatureRepository, ModelRepository, PredictionRepository


class PredictionService:
    """
    ML prediction service that orchestrates:
    1. Loading features from a feature store
    2. Loading a model from a model registry
    3. Running inference
    4. Storing predictions

    It NEVER knows what's behind those repositories.
    """

    def __init__(
        self,
        feature_repo: FeatureRepository,
        prediction_repo: PredictionRepository,
        model_repo: ModelRepository,
    ) -> None:
        self._features = feature_repo
        self._predictions = prediction_repo
        self._models = model_repo

    def predict_for_entity(self, entity_id: str, model_id: str | None = None) -> dict:
        """
        Run prediction for a single entity.

        1. Fetch features from feature repository
        2. Load model from model repository
        3. Run inference (simplified — computes a score from features)
        4. Save prediction to prediction repository
        5. Return the result
        """
        # Step 1: Get features
        features = self._features.get_features(entity_id)
        if not features:
            raise ValueError(f"No features found for entity '{entity_id}'")

        # Step 2: Resolve model
        if model_id is None:
            model_id = self._models.get_latest_model_id()

        model_bytes, model_metadata = self._models.load_model(model_id)

        # Step 3: Run inference (simplified)
        # In production you'd deserialize model_bytes and call model.predict()
        numeric_values = [v for v in features.values() if isinstance(v, (int, float))]
        score = sum(numeric_values) / (len(numeric_values) * 100) if numeric_values else 0.0
        score = max(0.0, min(1.0, score))  # clamp to [0, 1]

        # Step 4: Build and save prediction
        prediction = {
            "entity_id": entity_id,
            "model_id": model_id,
            "score": round(score, 4),
            "features_used": list(features.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._predictions.save_prediction(prediction)

        return prediction

    def predict_batch(self, entity_ids: list[str], model_id: str | None = None) -> list[dict]:
        """
        Run predictions for a batch of entities.
        Skips entities without features (doesn't fail).
        """
        if model_id is None:
            model_id = self._models.get_latest_model_id()

        # Load model once for the batch
        model_bytes, model_metadata = self._models.load_model(model_id)

        batch_features = self._features.get_batch_features(entity_ids)
        if not batch_features:
            return []

        predictions = []
        for row in batch_features:
            eid = row["entity_id"]
            feature_vals = {k: v for k, v in row.items() if k != "entity_id"}
            numeric_values = [v for v in feature_vals.values() if isinstance(v, (int, float))]
            score = sum(numeric_values) / (len(numeric_values) * 100) if numeric_values else 0.0
            score = max(0.0, min(1.0, score))

            predictions.append({
                "entity_id": eid,
                "model_id": model_id,
                "score": round(score, 4),
                "features_used": list(feature_vals.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Save all predictions in one call
        self._predictions.save_predictions(predictions)

        return predictions

    def get_model_predictions(self, model_id: str, limit: int = 50) -> list[dict]:
        """Retrieve historical predictions for a model."""
        return self._predictions.get_predictions(model_id, limit=limit)


# ─────────────────────────────────────────────────────────────────────────────
# Demo: Run with in-memory repos (no infrastructure needed)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Notice: we import ONLY in-memory repos here.
    # In production, you'd import PostgresFeatureRepo, S3PredictionRepo, etc.
    from src.in_memory_repos import (
        InMemoryFeatureRepository,
        InMemoryModelRepository,
        InMemoryPredictionRepository,
    )

    print("=" * 60)
    print("Repository Pattern Demo — PredictionService")
    print("=" * 60)
    print()

    # ─── Set up in-memory repos with fake data ───
    feature_repo = InMemoryFeatureRepository()
    feature_repo.seed({
        "user_001": {"age": 28, "income": 65, "credit_score": 72, "tenure_months": 24},
        "user_002": {"age": 45, "income": 120, "credit_score": 85, "tenure_months": 60},
        "user_003": {"age": 33, "income": 45, "credit_score": 55, "tenure_months": 6},
    })

    prediction_repo = InMemoryPredictionRepository()

    model_repo = InMemoryModelRepository()
    model_repo.save_model(
        model_id="churn_model_v2",
        model_bytes=b"fake-serialized-model-bytes",
        metadata={"algorithm": "xgboost", "accuracy": 0.89, "version": "2.0"},
    )

    # ─── Create service (injection happens here) ───
    service = PredictionService(
        feature_repo=feature_repo,
        prediction_repo=prediction_repo,
        model_repo=model_repo,
    )

    # ─── Run single prediction ───
    print("--- Single Prediction ---")
    result = service.predict_for_entity("user_001")
    print(f"  Entity:   {result['entity_id']}")
    print(f"  Model:    {result['model_id']}")
    print(f"  Score:    {result['score']}")
    print(f"  Features: {result['features_used']}")
    print()

    # ─── Run batch prediction ───
    print("--- Batch Prediction ---")
    results = service.predict_batch(["user_001", "user_002", "user_003"])
    for r in results:
        print(f"  {r['entity_id']}: score={r['score']}")
    print()

    # ─── Retrieve stored predictions ───
    print("--- Stored Predictions ---")
    stored = service.get_model_predictions("churn_model_v2")
    print(f"  Total predictions stored: {len(stored)}")
    print()

    # ─── Try unknown entity ───
    print("--- Error Handling ---")
    try:
        service.predict_for_entity("nonexistent_user")
    except ValueError as e:
        print(f"  Caught expected error: {e}")

    print()
    print("=" * 60)
    print("KEY POINT: This entire demo ran without any database,")
    print("S3, Redis, or network call. The PredictionService doesn't")
    print("know — or care — that it's using in-memory dicts.")
    print("=" * 60)


