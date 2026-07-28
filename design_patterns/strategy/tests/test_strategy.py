"""
Tests for the Strategy pattern implementation.

Key testing insight: because TrainingPipeline depends on PROTOCOLS (not
concrete classes), we can inject FAKE strategies to test the pipeline
in complete isolation — no sklearn needed for pipeline logic tests.
"""

import numpy as np
import pytest

from src.model_strategy import (
    GradientBoostingStrategy,
    LogisticRegressionStrategy,
    RandomForestStrategy,
    create_model_strategy,
)
from src.preprocessing_strategy import (
    NoScalingStrategy,
    RobustScalerStrategy,
    StandardScalerStrategy,
    create_preprocessing_strategy,
)
from src.training_pipeline import TrainingPipeline, create_pipeline_from_config


# ═══════════════════════════════════════════════════════════════════════
# FAKE STRATEGIES — for isolation testing
# ═══════════════════════════════════════════════════════════════════════


class FakePreprocessingStrategy:
    """
    Test double for PreprocessingStrategy.
    Records all calls for assertions. Passes data through unchanged.
    """

    def __init__(self):
        self.fit_called = False
        self.transform_called = False
        self.fit_X = None

    def fit(self, X: np.ndarray) -> None:
        self.fit_called = True
        self.fit_X = X

    def transform(self, X: np.ndarray) -> np.ndarray:
        self.transform_called = True
        return X

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)


class FakeModelStrategy:
    """
    Test double for ModelStrategy.
    Always predicts class 1 with 0.9 probability.
    Records calls for assertions.
    """

    def __init__(self):
        self.fit_called = False
        self.fit_X = None
        self.fit_y = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.fit_called = True
        self.fit_X = X
        self.fit_y = y

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.ones(len(X), dtype=int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        # Return [0.1, 0.9] for each sample (binary classification)
        n = len(X)
        return np.column_stack([np.full(n, 0.1), np.full(n, 0.9)])


# ═══════════════════════════════════════════════════════════════════════
# PIPELINE TESTS (using fakes — no real ML happening)
# ═══════════════════════════════════════════════════════════════════════


class TestPipelineWithFakes:
    """Test pipeline logic in isolation using fake strategies."""

    def setup_method(self):
        self.fake_preprocessing = FakePreprocessingStrategy()
        self.fake_model = FakeModelStrategy()
        self.pipeline = TrainingPipeline(
            preprocessing=self.fake_preprocessing,
            model=self.fake_model,
        )
        # Simple test data
        self.X_train = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        self.y_train = np.array([0, 1, 0, 1])
        self.X_test = np.array([[2, 3], [4, 5]])
        self.y_test = np.array([1, 1])

    def test_train_calls_preprocessing_fit_transform(self):
        """Pipeline must preprocess before training."""
        self.pipeline.train(self.X_train, self.y_train)
        assert self.fake_preprocessing.fit_called

    def test_train_calls_model_fit(self):
        """Pipeline must train the model."""
        self.pipeline.train(self.X_train, self.y_train)
        assert self.fake_model.fit_called

    def test_train_passes_correct_data_shape(self):
        """Model receives data with correct shape."""
        self.pipeline.train(self.X_train, self.y_train)
        assert self.fake_model.fit_X.shape == (4, 2)
        assert self.fake_model.fit_y.shape == (4,)

    def test_evaluate_returns_metrics_dict(self):
        """Evaluate returns dict with accuracy, f1, auc."""
        self.pipeline.train(self.X_train, self.y_train)
        metrics = self.pipeline.evaluate(self.X_test, self.y_test)
        assert "accuracy" in metrics
        assert "f1" in metrics
        assert "auc" in metrics

    def test_evaluate_uses_transform_not_fit(self):
        """Evaluate should use transform (not fit_transform) on test data."""
        self.pipeline.train(self.X_train, self.y_train)
        # Reset tracking
        self.fake_preprocessing.fit_called = False
        self.pipeline.evaluate(self.X_test, self.y_test)
        # transform was called but fit was NOT re-called
        assert self.fake_preprocessing.transform_called
        # fit_called was reset and should still be False
        assert not self.fake_preprocessing.fit_called


# ═══════════════════════════════════════════════════════════════════════
# PREPROCESSING STRATEGY TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestStandardScalerStrategy:
    """Test that StandardScalerStrategy produces zero-mean, unit-variance."""

    def test_zero_mean_after_transform(self):
        X = np.array([[1.0, 100.0], [2.0, 200.0], [3.0, 300.0]])
        scaler = StandardScalerStrategy()
        X_scaled = scaler.fit_transform(X)
        # Mean should be ~0
        np.testing.assert_array_almost_equal(X_scaled.mean(axis=0), [0, 0])

    def test_unit_variance_after_transform(self):
        X = np.array([[1.0, 100.0], [2.0, 200.0], [3.0, 300.0]])
        scaler = StandardScalerStrategy()
        X_scaled = scaler.fit_transform(X)
        # Std should be ~1
        np.testing.assert_array_almost_equal(X_scaled.std(axis=0), [1, 1])

    def test_transform_without_fit_raises(self):
        scaler = StandardScalerStrategy()
        with pytest.raises(RuntimeError):
            scaler.transform(np.array([[1, 2]]))


class TestRobustScalerStrategy:
    """Test RobustScalerStrategy uses median/IQR."""

    def test_median_becomes_zero(self):
        X = np.array([[1.0], [2.0], [3.0], [4.0], [100.0]])  # outlier
        scaler = RobustScalerStrategy()
        X_scaled = scaler.fit_transform(X)
        # Median of original is 3.0 -> should map to 0
        median_idx = 2  # value 3.0
        assert abs(X_scaled[median_idx, 0]) < 1e-10

    def test_transform_without_fit_raises(self):
        scaler = RobustScalerStrategy()
        with pytest.raises(RuntimeError):
            scaler.transform(np.array([[1, 2]]))


class TestNoScalingStrategy:
    """Test NoScalingStrategy passes data through unchanged."""

    def test_data_unchanged(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        scaler = NoScalingStrategy()
        X_out = scaler.fit_transform(X)
        np.testing.assert_array_equal(X, X_out)

    def test_returns_copy_not_reference(self):
        X = np.array([[1.0, 2.0]])
        scaler = NoScalingStrategy()
        X_out = scaler.fit_transform(X)
        # Modifying output shouldn't affect input
        X_out[0, 0] = 999.0
        assert X[0, 0] == 1.0


# ═══════════════════════════════════════════════════════════════════════
# MODEL STRATEGY TESTS (lightweight integration tests)
# ═══════════════════════════════════════════════════════════════════════


class TestModelStrategies:
    """Quick smoke tests that each model strategy works end-to-end."""

    def setup_method(self):
        np.random.seed(42)
        self.X = np.random.randn(50, 4)
        self.y = (self.X[:, 0] > 0).astype(int)

    def test_logistic_regression_fits_and_predicts(self):
        model = LogisticRegressionStrategy()
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        assert preds.shape == (50,)
        assert set(preds).issubset({0, 1})

    def test_random_forest_fits_and_predicts(self):
        model = RandomForestStrategy(n_estimators=10)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        assert preds.shape == (50,)

    def test_gradient_boosting_fits_and_predicts(self):
        model = GradientBoostingStrategy(n_estimators=10)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        assert preds.shape == (50,)

    def test_predict_proba_returns_probabilities(self):
        model = RandomForestStrategy(n_estimators=10)
        model.fit(self.X, self.y)
        probas = model.predict_proba(self.X)
        # Probabilities should sum to 1 per row
        np.testing.assert_array_almost_equal(probas.sum(axis=1), 1.0)


# ═══════════════════════════════════════════════════════════════════════
# REGISTRY / FACTORY FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestRegistries:
    """Test that registry lookup functions work correctly."""

    def test_create_preprocessing_standard(self):
        strategy = create_preprocessing_strategy("standard")
        assert isinstance(strategy, StandardScalerStrategy)

    def test_create_preprocessing_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown preprocessing"):
            create_preprocessing_strategy("minmax")

    def test_create_model_with_params(self):
        model = create_model_strategy("random_forest", n_estimators=50)
        assert isinstance(model, RandomForestStrategy)
        assert model.n_estimators == 50

    def test_create_model_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            create_model_strategy("xgboost")

    def test_create_pipeline_from_config(self):
        config = {
            "preprocessing": "robust",
            "model": "gradient_boosting",
            "model_params": {"n_estimators": 50},
        }
        pipeline = create_pipeline_from_config(config)
        assert isinstance(pipeline.preprocessing, RobustScalerStrategy)
        assert isinstance(pipeline.model, GradientBoostingStrategy)


