"""
Tests for PredictionService — Using In-Memory Repositories.

=============================================================================
WHY THIS IS POWERFUL:
=============================================================================

These tests run in MILLISECONDS with ZERO infrastructure:
  - No PostgreSQL instance needed
  - No Redis server needed
  - No S3 bucket or AWS credentials needed
  - No Docker containers to spin up
  - No network connectivity required

The PredictionService only depends on Protocols (interfaces).
We inject InMemory implementations that satisfy those Protocols.
The service can't tell the difference — and that's the whole point.

This means:
  1. Tests are FAST (pure Python, no I/O)
  2. Tests are DETERMINISTIC (no flaky network or stale data)
  3. Tests are ISOLATED (each test gets a fresh, empty repo)
  4. Tests are FREE (no cloud charges in CI)
  5. Tests run ANYWHERE (laptop, CI, plane with no WiFi)

Compare with the alternative: mocking boto3 calls, patching SQL drivers,
managing test databases — fragile, complex, and slow.
=============================================================================
"""

import sys
from pathlib import Path

import pytest

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.in_memory_repos import (
    InMemoryFeatureRepository,
    InMemoryModelRepository,
    InMemoryPredictionRepository,
)
from src.prediction_service import PredictionService


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: Build fresh repos for each test (perfect isolation)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def feature_repo():
    """
    A fresh in-memory feature store seeded with test data.
    Each test gets its OWN instance — no shared state, no cleanup needed.
    """
    repo = InMemoryFeatureRepository()
    repo.seed({
        "user_001": {"age": 28, "income": 65, "credit_score": 72, "tenure_months": 24},
        "user_002": {"age": 45, "income": 120, "credit_score": 85, "tenure_months": 60},
        "user_003": {"age": 33, "income": 45, "credit_score": 55, "tenure_months": 6},
    })
    return repo


@pytest.fixture
def prediction_repo():
    """A fresh, empty prediction store."""
    return InMemoryPredictionRepository()


@pytest.fixture
def model_repo():
    """A model registry with one registered model."""
    repo = InMemoryModelRepository()
    repo.save_model(
        model_id="churn_v2",
        model_bytes=b"fake-model-bytes",
        metadata={"algorithm": "xgboost", "accuracy": 0.89},
    )
    return repo


@pytest.fixture
def service(feature_repo, prediction_repo, model_repo):
    """
    Fully wired PredictionService with all in-memory repos.

    THIS IS THE KEY PATTERN:
    - The service accepts Protocols in its constructor
    - We pass in-memory implementations
    - The service works exactly the same as in production
    - But without any real infrastructure
    """
    return PredictionService(
        feature_repo=feature_repo,
        prediction_repo=prediction_repo,
        model_repo=model_repo,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Single Prediction
# ─────────────────────────────────────────────────────────────────────────────


class TestPredictForEntity:
    """Test single-entity prediction flow."""

    def test_returns_prediction_for_known_entity(self, service):
        """Happy path: entity exists, model exists, prediction is returned."""
        result = service.predict_for_entity("user_001")

        assert result["entity_id"] == "user_001"
        assert result["model_id"] == "churn_v2"
        assert 0.0 <= result["score"] <= 1.0
        assert "features_used" in result
        assert "timestamp" in result

    def test_uses_correct_features(self, service):
        """Verify the service fetched the right features for the entity."""
        result = service.predict_for_entity("user_001")

        # These are the features we seeded for user_001
        expected_features = ["age", "income", "credit_score", "tenure_months"]
        assert sorted(result["features_used"]) == sorted(expected_features)

    def test_saves_prediction_to_repo(self, service, prediction_repo):
        """
        After predicting, the result should be persisted.

        WHY THIS IS POWERFUL:
        We can directly inspect the in-memory repo to verify the service
        stored the prediction. No need to query a real database.
        """
        service.predict_for_entity("user_001")

        assert prediction_repo.saved_count == 1
        saved = prediction_repo.all_predictions[0]
        assert saved["entity_id"] == "user_001"
        assert saved["model_id"] == "churn_v2"

    def test_raises_for_unknown_entity(self, service):
        """
        If entity has no features, the service raises a clear error.
        No ambiguous database errors — just clean business logic.
        """
        with pytest.raises(ValueError, match="No features found for entity 'ghost'"):
            service.predict_for_entity("ghost")

    def test_raises_for_unknown_model(self, service):
        """If an explicit model_id doesn't exist, KeyError is raised."""
        with pytest.raises(KeyError, match="nonexistent_model"):
            service.predict_for_entity("user_001", model_id="nonexistent_model")

    def test_uses_latest_model_when_none_specified(self, service, model_repo):
        """When model_id is None, service picks the latest registered model."""
        # Register a newer model
        model_repo.save_model("churn_v3", b"newer-model", {"version": "3.0"})

        result = service.predict_for_entity("user_001")

        # Should use the latest (churn_v3), not the original (churn_v2)
        assert result["model_id"] == "churn_v3"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Batch Prediction
# ─────────────────────────────────────────────────────────────────────────────


class TestPredictBatch:
    """Test batch prediction flow."""

    def test_returns_predictions_for_all_known_entities(self, service):
        results = service.predict_batch(["user_001", "user_002", "user_003"])
        assert len(results) == 3

    def test_skips_unknown_entities(self, service):
        """
        Unknown entities are silently skipped — no crash.
        This is how batch processing should work: best effort.
        """
        results = service.predict_batch(["user_001", "nonexistent", "user_002"])
        # Only user_001 and user_002 have features
        assert len(results) == 2
        entity_ids = [r["entity_id"] for r in results]
        assert "user_001" in entity_ids
        assert "user_002" in entity_ids

    def test_returns_empty_list_when_no_entities_found(self, service):
        results = service.predict_batch(["ghost_1", "ghost_2"])
        assert results == []

    def test_batch_saves_all_predictions(self, service, prediction_repo):
        """All batch results should be persisted in a single save call."""
        service.predict_batch(["user_001", "user_002", "user_003"])
        assert prediction_repo.saved_count == 3

    def test_batch_uses_specified_model(self, service, model_repo):
        """Explicit model_id is used for all entities in the batch."""
        model_repo.save_model("churn_v3", b"newer", {"version": "3"})

        results = service.predict_batch(["user_001"], model_id="churn_v3")
        assert results[0]["model_id"] == "churn_v3"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Retrieving Stored Predictions
# ─────────────────────────────────────────────────────────────────────────────


class TestGetModelPredictions:
    """Test prediction retrieval."""

    def test_returns_predictions_for_model(self, service, prediction_repo):
        """After making predictions, we can retrieve them by model_id."""
        service.predict_for_entity("user_001")
        service.predict_for_entity("user_002")

        stored = service.get_model_predictions("churn_v2")
        assert len(stored) == 2

    def test_returns_empty_for_unknown_model(self, service):
        stored = service.get_model_predictions("model_that_never_ran")
        assert stored == []

    def test_respects_limit(self, service, prediction_repo):
        """Limit parameter caps the number of results."""
        service.predict_batch(["user_001", "user_002", "user_003"])

        stored = service.get_model_predictions("churn_v2", limit=2)
        assert len(stored) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Demonstrate repo isolation (each test is independent)
# ─────────────────────────────────────────────────────────────────────────────


class TestIsolation:
    """
    Prove that tests don't leak state.

    WHY THIS MATTERS:
    With a real database, test A might insert data that breaks test B.
    With in-memory repos, each test gets a FRESH instance via the fixture.
    No cleanup needed. No ordering dependencies. Pure isolation.
    """

    def test_first_prediction(self, service, prediction_repo):
        service.predict_for_entity("user_001")
        assert prediction_repo.saved_count == 1  # Only this test's prediction

    def test_second_prediction(self, service, prediction_repo):
        service.predict_for_entity("user_002")
        # Still 1 — NOT 2! This test got its own fresh prediction_repo.
        assert prediction_repo.saved_count == 1

    def test_third_no_predictions(self, prediction_repo):
        # Even without calling predict, the repo is empty — no leftover state.
        assert prediction_repo.saved_count == 0


