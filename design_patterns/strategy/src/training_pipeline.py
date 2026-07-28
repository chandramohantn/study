"""
Training Pipeline — uses PreprocessingStrategy + ModelStrategy.

This is the CONSUMER of strategies. It doesn't know or care which
preprocessing or model it's using. It just calls the protocol methods.

Key insight: the pipeline's logic NEVER changes when you add a new
scaler or a new model. You just create a new strategy class and pass it in.
"""

import numpy as np
from sklearn.datasets import make_classification
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .model_strategy import ModelStrategy, create_model_strategy
from .preprocessing_strategy import PreprocessingStrategy, create_preprocessing_strategy


# ─────────────────────────────────────────────────────────────────────
# The Pipeline (context that uses strategies)
# ─────────────────────────────────────────────────────────────────────


class TrainingPipeline:
    """
    ML training pipeline that accepts interchangeable strategies.

    This class is CLOSED for modification but OPEN for extension:
    - New preprocessing? Create a new strategy class. Pipeline unchanged.
    - New model? Create a new strategy class. Pipeline unchanged.
    """

    def __init__(
        self,
        preprocessing: PreprocessingStrategy,
        model: ModelStrategy,
    ):
        self.preprocessing = preprocessing
        self.model = model

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
    ) -> None:
        """Preprocess and fit the model."""
        # Strategy 1: preprocessing (could be standard, robust, or none)
        X_processed = self.preprocessing.fit_transform(X_train)
        # Strategy 2: model training (could be logistic, RF, or GB)
        self.model.fit(X_processed, y_train)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> dict[str, float]:
        """Preprocess test data and compute metrics."""
        # Use transform (not fit_transform) — learned params from training
        X_processed = self.preprocessing.transform(X_test)
        predictions = self.model.predict(X_processed)
        probas = self.model.predict_proba(X_processed)

        # Handle binary vs multiclass for AUC
        if probas.shape[1] == 2:
            auc = roc_auc_score(y_test, probas[:, 1])
        else:
            auc = roc_auc_score(y_test, probas, multi_class="ovr")

        return {
            "accuracy": accuracy_score(y_test, predictions),
            "f1": f1_score(y_test, predictions, average="weighted"),
            "auc": auc,
        }

    def train_and_evaluate(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> dict[str, float]:
        """Full workflow: train then evaluate."""
        self.train(X_train, y_train)
        return self.evaluate(X_test, y_test)


# ─────────────────────────────────────────────────────────────────────
# Config-driven pipeline creation
# ─────────────────────────────────────────────────────────────────────


def create_pipeline_from_config(config: dict) -> TrainingPipeline:
    """
    Build a pipeline from a config dict.

    In production, this config comes from YAML/JSON. Here we show the structure:

        config = {
            "preprocessing": "standard",
            "model": "random_forest",
            "model_params": {"n_estimators": 200, "max_depth": 10},
        }
    """
    preprocessing = create_preprocessing_strategy(config["preprocessing"])
    model_params = config.get("model_params", {})
    model = create_model_strategy(config["model"], **model_params)
    return TrainingPipeline(preprocessing=preprocessing, model=model)


# ─────────────────────────────────────────────────────────────────────
# Demo: run multiple experiments by swapping strategies
# ─────────────────────────────────────────────────────────────────────


def run_experiment(config: dict, X_train, y_train, X_test, y_test) -> dict:
    """Run a single experiment and return results."""
    pipeline = create_pipeline_from_config(config)
    metrics = pipeline.train_and_evaluate(X_train, y_train, X_test, y_test)
    return {
        "config": config,
        "preprocessing": pipeline.preprocessing,
        "model": pipeline.model,
        "metrics": metrics,
    }


if __name__ == "__main__":
    # ─── Generate sample data ────────────────────────────────────────
    print("=" * 60)
    print("Strategy Pattern Demo — ML Training Pipeline")
    print("=" * 60)
    print()

    X, y = make_classification(
        n_samples=500,
        n_features=10,
        n_informative=6,
        n_redundant=2,
        random_state=42,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Dataset: {X_train.shape[0]} train / {X_test.shape[0]} test samples")
    print(f"Features: {X.shape[1]}")
    print()

    # ─── Define experiments (swap strategies via config) ─────────────
    experiments = [
        {
            "name": "Baseline: LogReg + StandardScaler",
            "preprocessing": "standard",
            "model": "logistic_regression",
            "model_params": {"C": 1.0},
        },
        {
            "name": "Random Forest + No Scaling",
            "preprocessing": "none",
            "model": "random_forest",
            "model_params": {"n_estimators": 100},
        },
        {
            "name": "Gradient Boosting + Robust Scaling",
            "preprocessing": "robust",
            "model": "gradient_boosting",
            "model_params": {"n_estimators": 150, "learning_rate": 0.05},
        },
        {
            "name": "Gradient Boosting + Standard Scaling",
            "preprocessing": "standard",
            "model": "gradient_boosting",
            "model_params": {"n_estimators": 200, "learning_rate": 0.1},
        },
    ]

    # ─── Run all experiments ─────────────────────────────────────────
    print("Running experiments...")
    print("-" * 60)

    results = []
    for exp in experiments:
        result = run_experiment(exp, X_train, y_train, X_test, y_test)
        results.append(result)

        metrics = result["metrics"]
        print(f"\n  {exp['name']}")
        print(f"    Preprocessing: {result['preprocessing']}")
        print(f"    Model:         {result['model']}")
        print(f"    Accuracy:      {metrics['accuracy']:.4f}")
        print(f"    F1 Score:      {metrics['f1']:.4f}")
        print(f"    AUC:           {metrics['auc']:.4f}")

    # ─── Summary ─────────────────────────────────────────────────────
    print()
    print("-" * 60)
    best = max(results, key=lambda r: r["metrics"]["auc"])
    print(f"\n  Best by AUC: {best['config']['name']}")
    print(f"    AUC = {best['metrics']['auc']:.4f}")
    print()
    print("Key takeaway: We ran 4 experiments by ONLY changing config dicts.")
    print("The TrainingPipeline class was NEVER modified.")


