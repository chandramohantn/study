"""
Training Pipeline - Uses Factory + Strategy + Repository patterns together.

This file demonstrates how Factory doesn't live in isolation.
It works WITH other patterns:

    Factory  → CREATES the model (from config)
    Strategy → The model IS a strategy (interchangeable algorithms)
    Repository → WHERE to store/load models and results
    
Flow:
    1. Load config (YAML)
    2. Factory creates model from config
    3. Pipeline trains using the model (Strategy pattern - pipeline doesn't care which model)
    4. Results are stored via Repository (could be local, S3, database)
"""

from typing import Protocol
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml
import numpy as np
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

# Import from our modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
from model_factory import ModelFactory
from model_creators import setup_factory


# ---------------------------------------------------
# REPOSITORY PATTERN - abstracts where results are stored
# ---------------------------------------------------

class ResultsRepository(Protocol):
    """Where do we store experiment results? This protocol doesn't care."""
    def save_result(self, result: dict) -> None: ...
    def get_results(self) -> list[dict]: ...


class LocalFileRepository:
    """Stores results as JSON files - for development."""

    def __init__(self, output_dir: str = "./results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._results: list[dict] = []

    def save_result(self, result: dict) -> None:
        self._results.append(result)
        # Also write to file
        import json
        filename = f"{result['algorithm']}_{result['timestamp']}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(result, f, indent=2, default=str)

    def get_results(self) -> list[dict]:
        return self._results


class InMemoryRepository:
    """Stores results in memory — for testing."""

    def __init__(self):
        self._results: list[dict] = []

    def save_result(self, result: dict) -> None:
        self._results.append(result)

    def get_results(self) -> list[dict]:
        return self._results


# ---------------------------------------------------
# TRAINING PIPELINE - uses Factory-created models as Strategies
# ---------------------------------------------------

@dataclass
class ExperimentResult:
    algorithm: str
    hyperparameters: dict
    cv_accuracy_mean: float
    cv_accuracy_std: float
    test_accuracy: float
    test_f1: float
    training_time_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "hyperparameters": self.hyperparameters,
            "cv_accuracy_mean": round(self.cv_accuracy_mean, 4),
            "cv_accuracy_std": round(self.cv_accuracy_std, 4),
            "test_accuracy": round(self.test_accuracy, 4),
            "test_f1": round(self.test_f1, 4),
            "training_time_seconds": round(self.training_time_seconds, 3),
            "timestamp": self.timestamp,
        }


class TrainingPipeline:
    """
    The training pipeline.

    Patterns in play:
    - Factory: creates model from config (injected factory)
    - Strategy: model is used polymorphically (fit/predict interface)
    - Repository: results are stored via protocol (injected repo)

    This class doesn't know:
    - WHICH model it's training (Factory decides)
    - WHERE results are stored (Repository decides)
    - HOW the model works internally (Strategy — it just calls fit/predict)
    """

    def __init__(self, factory: ModelFactory, results_repo: ResultsRepository):
        self.factory = factory
        self.results_repo = results_repo

    def run_single(
        self,
        config: dict,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        cv_folds: int = 5,
    ) -> ExperimentResult:
        """
        Train a single model from config.

        Args:
            config: {"algorithm": "xgboost", "hyperparameters": {...}}
            X: Feature matrix
            y: Target vector
            test_size: Fraction for test split
            cv_folds: Number of cross-validation folds
        """
        import time

        algorithm = config["algorithm"]
        hyperparams = config.get("hyperparameters", {})

        # 1. FACTORY creates the model
        model = self.factory.create(algorithm, **hyperparams)

        # 2. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # 3. Cross-validation (STRATEGY — works with any model that has fit/predict)
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring="accuracy")

        # 4. Train on full training set
        start_time = time.perf_counter()
        model.fit(X_train, y_train)
        training_time = time.perf_counter() - start_time

        # 5. Evaluate on test set
        predictions = model.predict(X_test)
        test_accuracy = accuracy_score(y_test, predictions)
        test_f1 = f1_score(y_test, predictions, average="weighted")

        # 6. Build result
        result = ExperimentResult(
            algorithm=algorithm,
            hyperparameters=hyperparams,
            cv_accuracy_mean=cv_scores.mean(),
            cv_accuracy_std=cv_scores.std(),
            test_accuracy=test_accuracy,
            test_f1=test_f1,
            training_time_seconds=training_time,
        )

        # 7. REPOSITORY stores the result
        self.results_repo.save_result(result.to_dict())

        return result

    def run_experiments(
        self,
        configs: list[dict],
        X: np.ndarray,
        y: np.ndarray,
    ) -> list[ExperimentResult]:
        """
        Run multiple experiments from a list of configs.
        Returns results sorted by test F1 score (best first).
        """
        results = []

        for i, config in enumerate(configs, 1):
            algorithm = config["algorithm"]
            print(f"  [{i}/{len(configs)}] Training {algorithm}...", end=" ")

            try:
                result = self.run_single(config, X, y)
                results.append(result)
                print(f"accuracy={result.test_accuracy:.4f}, f1={result.test_f1:.4f}")
            except Exception as e:
                print(f"FAILED: {e}")

        # Sort by F1 score (best first)
        results.sort(key=lambda r: r.test_f1, reverse=True)
        return results

    def run_from_yaml(
        self,
        yaml_path: str,
        X: np.ndarray,
        y: np.ndarray,
    ) -> list[ExperimentResult]:
        """
        Load experiment configs from YAML and run them all.
        """
        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        experiments = config.get("experiments", [])
        if not experiments:
            # Single model config (production.yaml format)
            model_config = config.get("model", {})
            experiments = [model_config]

        print(f"Running {len(experiments)} experiments from {yaml_path}")
        print("-" * 60)
        return self.run_experiments(experiments, X, y)


# ---------------------------------------------------
# MAIN - demonstrates the full flow
# ---------------------------------------------------

def main():
    """Run the complete factory + pipeline demonstration."""
    from sklearn.datasets import make_classification

    # 1. Generate sample data
    print("=" * 60)
    print("FACTORY + STRATEGY + REPOSITORY PATTERN DEMO")
    print("=" * 60)
    print("\nGenerating sample classification data...")
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=10,
        n_classes=2,
        random_state=42,
    )
    print(f"  Data shape: X={X.shape}, y={y.shape}")
    print(f"  Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # 2. Setup factory (FACTORY PATTERN)
    print("\nSetting up model factory...")
    factory = setup_factory()
    print(f"  Available models: {factory.available_models()}")

    # 3. Setup repository (REPOSITORY PATTERN)
    results_repo = InMemoryRepository()

    # 4. Create pipeline (combines Factory + Strategy + Repository)
    pipeline = TrainingPipeline(factory=factory, results_repo=results_repo)

    # 5. Run experiments from config
    print("\n" + "=" * 60)
    print("EXPERIMENT: Baseline Comparison")
    print("=" * 60)

    configs_dir = Path(__file__).parent.parent / "configs"
    baseline_path = configs_dir / "baseline_experiment.yaml"

    if baseline_path.exists():
        results = pipeline.run_from_yaml(str(baseline_path), X, y)
    else:
        # Fallback: inline configs if YAML not found
        configs = [
            {"algorithm": "logistic_regression"},
            {"algorithm": "random_forest", "hyperparameters": {"n_estimators": 50}},
            {"algorithm": "xgboost", "hyperparameters": {"n_estimators": 50}},
        ]
        results = pipeline.run_experiments(configs, X, y)

    # 6. Print leaderboard
    print("\n" + "=" * 60)
    print("LEADERBOARD (sorted by F1 score)")
    print("=" * 60)
    print(f"{'Rank':<5} {'Algorithm':<25} {'Accuracy':<12} {'F1':<12} {'Time (s)':<10}")
    print("-" * 64)
    for i, r in enumerate(results, 1):
        print(f"{i:<5} {r.algorithm:<25} {r.test_accuracy:<12.4f} {r.test_f1:<12.4f} {r.training_time_seconds:<10.3f}")

    # 7. Show stored results (Repository)
    print(f"\nTotal results stored in repository: {len(results_repo.get_results())}")

    # 8. Demonstrate single config-driven creation
    print("\n" + "=" * 60)
    print("SINGLE MODEL: Config-driven creation")
    print("=" * 60)
    single_config = {
        "algorithm": "xgboost",
        "hyperparameters": {"n_estimators": 200, "max_depth": 8, "learning_rate": 0.05},
    }
    print(f"  Config: {single_config}")
    model = factory.create_from_config(single_config)
    print(f"  Created: {type(model).__name__}")
    print(f"  Params: n_estimators={model.n_estimators}, max_depth={model.max_depth}")


if __name__ == "__main__":
    main()


