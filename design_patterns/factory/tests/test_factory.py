"""
Tests for the Factory Pattern implementation.

These tests demonstrate:
1. Testing the factory itself (unit tests)
2. Testing the pipeline with fake models (Repository pattern in action!)
3. How the factory makes testing easy (no real ML libraries needed for pipeline tests)
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from model_factory import ModelFactory


# ═══════════════════════════════════════════════════
# UNIT TESTS: ModelFactory (core factory logic)
# ═══════════════════════════════════════════════════

class TestModelFactory:
    """Test the factory itself — registration, creation, error handling."""

    @pytest.fixture
    def factory(self):
        """Fresh factory with simple fake creators."""
        f = ModelFactory()
        f.register("model_a", lambda **kw: {"type": "a", **kw})
        f.register("model_b", lambda **kw: {"type": "b", **kw})
        return f

    # ─── Registration ───

    def test_register_adds_model(self, factory):
        assert factory.is_registered("model_a")
        assert factory.is_registered("model_b")

    def test_register_duplicate_raises(self, factory):
        with pytest.raises(ValueError, match="already registered"):
            factory.register("model_a", lambda: None)

    def test_available_models_returns_sorted(self, factory):
        assert factory.available_models() == ["model_a", "model_b"]

    def test_is_registered_false_for_unknown(self, factory):
        assert factory.is_registered("unknown") is False

    # ─── Creation ───

    def test_create_returns_correct_object(self, factory):
        result = factory.create("model_a")
        assert result["type"] == "a"

    def test_create_passes_kwargs(self, factory):
        result = factory.create("model_a", x=1, y=2)
        assert result == {"type": "a", "x": 1, "y": 2}

    def test_create_unknown_raises(self, factory):
        with pytest.raises(ValueError, match="Unknown model"):
            factory.create("nonexistent")

    def test_create_error_shows_available_models(self, factory):
        with pytest.raises(ValueError, match="model_a"):
            factory.create("bad_name")

    # ─── Config-driven creation ───

    def test_create_from_config(self, factory):
        config = {"algorithm": "model_a", "hyperparameters": {"x": 10}}
        result = factory.create_from_config(config)
        assert result == {"type": "a", "x": 10}

    def test_create_from_config_no_hyperparameters(self, factory):
        config = {"algorithm": "model_b"}
        result = factory.create_from_config(config)
        assert result == {"type": "b"}

    def test_create_from_config_missing_algorithm_raises(self, factory):
        with pytest.raises(ValueError, match="algorithm"):
            factory.create_from_config({"hyperparameters": {"x": 1}})

    def test_create_from_config_empty_dict_raises(self, factory):
        with pytest.raises(ValueError, match="algorithm"):
            factory.create_from_config({})


# ═══════════════════════════════════════════════════
# UNIT TESTS: Model creators (verify defaults work)
# ═══════════════════════════════════════════════════

class TestModelCreators:
    """
    Test that each creator function works with defaults.
    These tests DO require the ML libraries installed.
    Mark them so they can be skipped in CI without ML deps.
    """

    @pytest.fixture
    def factory(self):
        from model_creators import setup_factory
        return setup_factory()

    @pytest.mark.skipif(
        not _has_sklearn(), reason="scikit-learn not installed"
    )
    def test_create_random_forest(self, factory):
        model = factory.create("random_forest")
        assert hasattr(model, "fit")
        assert hasattr(model, "predict")
        assert model.n_estimators == 100  # Default

    @pytest.mark.skipif(
        not _has_sklearn(), reason="scikit-learn not installed"
    )
    def test_create_logistic_regression(self, factory):
        model = factory.create("logistic_regression")
        assert hasattr(model, "fit")
        assert model.max_iter == 1000  # Default

    @pytest.mark.skipif(
        not _has_sklearn(), reason="scikit-learn not installed"
    )
    def test_create_random_forest_with_overrides(self, factory):
        model = factory.create("random_forest", n_estimators=50, max_depth=5)
        assert model.n_estimators == 50
        assert model.max_depth == 5

    @pytest.mark.skipif(
        not _has_sklearn(), reason="scikit-learn not installed"
    )
    def test_all_sklearn_models_registered(self, factory):
        assert factory.is_registered("random_forest")
        assert factory.is_registered("logistic_regression")
        assert factory.is_registered("gradient_boosting")


# ═══════════════════════════════════════════════════
# INTEGRATION TESTS: Pipeline with Factory
# ═══════════════════════════════════════════════════

class TestTrainingPipeline:
    """
    Test the pipeline with FAKE models.
    
    This demonstrates the POWER of Factory + Repository:
    - We inject a factory with fake creators (no ML libraries needed!)
    - We inject an in-memory repository (no filesystem/S3 needed!)
    - We test the PIPELINE LOGIC, not the models.
    """

    @pytest.fixture
    def fake_factory(self):
        """Factory with fake models — no ML libraries needed."""

        class FakeModel:
            """Mimics sklearn interface."""
            def __init__(self, **kwargs):
                self.params = kwargs
                self._fitted = False

            def fit(self, X, y):
                self._fitted = True
                return self

            def predict(self, X):
                # Always predict class 1
                return np.ones(len(X), dtype=int)

            def predict_proba(self, X):
                n = len(X)
                return np.column_stack([np.zeros(n), np.ones(n)])

            def get_params(self, deep=True):
                return self.params

        factory = ModelFactory()
        factory.register("fake_model", lambda **kw: FakeModel(**kw))
        factory.register("another_fake", lambda **kw: FakeModel(**kw))
        return factory

    @pytest.fixture
    def memory_repo(self):
        from training_pipeline import InMemoryRepository
        return InMemoryRepository()

    @pytest.fixture
    def pipeline(self, fake_factory, memory_repo):
        from training_pipeline import TrainingPipeline
        return TrainingPipeline(factory=fake_factory, results_repo=memory_repo)

    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = np.random.randint(0, 2, 100)
        return X, y

    def test_run_single_returns_result(self, pipeline, sample_data):
        X, y = sample_data
        config = {"algorithm": "fake_model"}
        result = pipeline.run_single(config, X, y)

        assert result.algorithm == "fake_model"
        assert 0 <= result.test_accuracy <= 1
        assert 0 <= result.test_f1 <= 1
        assert result.training_time_seconds >= 0

    def test_run_single_stores_in_repository(self, pipeline, sample_data, memory_repo):
        X, y = sample_data
        pipeline.run_single({"algorithm": "fake_model"}, X, y)

        assert len(memory_repo.get_results()) == 1
        stored = memory_repo.get_results()[0]
        assert stored["algorithm"] == "fake_model"

    def test_run_experiments_returns_sorted_by_f1(self, pipeline, sample_data):
        X, y = sample_data
        configs = [
            {"algorithm": "fake_model"},
            {"algorithm": "another_fake"},
        ]
        results = pipeline.run_experiments(configs, X, y)

        assert len(results) == 2
        # Results should be sorted by F1 (descending)
        assert results[0].test_f1 >= results[1].test_f1

    def test_run_experiments_stores_all_results(self, pipeline, sample_data, memory_repo):
        X, y = sample_data
        configs = [
            {"algorithm": "fake_model"},
            {"algorithm": "another_fake"},
            {"algorithm": "fake_model", "hyperparameters": {"x": 1}},
        ]
        pipeline.run_experiments(configs, X, y)

        assert len(memory_repo.get_results()) == 3

    def test_hyperparameters_passed_to_model(self, pipeline, sample_data):
        X, y = sample_data
        config = {"algorithm": "fake_model", "hyperparameters": {"n_estimators": 999}}
        result = pipeline.run_single(config, X, y)

        assert result.hyperparameters == {"n_estimators": 999}


# ═══════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════

def _has_sklearn() -> bool:
    try:
        import sklearn
        return True
    except ImportError:
        return False


