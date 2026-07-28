"""Demo: bare predictor vs fully-decorated predictor.

Run with:  python -m src
From:      design_patterns/decorator/
"""

import logging

import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from .core_predictor import ModelPredictor
from .stack_builder import build_prediction_stack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    print("=" * 70)
    print("DECORATOR PATTERN DEMO — ML Prediction Stack")
    print("=" * 70)

    # Train a real model
    X, y = make_classification(
        n_samples=500, n_features=10, n_informative=6, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    # ─── Demo 1: Bare predictor ───
    print("\n--- Demo 1: BARE predictor (no decorators) ---")
    bare = ModelPredictor(model)
    result_bare = bare.predict(X_test[:5])
    print(f"  Input shape: {X_test[:5].shape}")
    print(f"  Output:      {result_bare}")

    # ─── Demo 2: Fully decorated ───
    print("\n--- Demo 2: FULLY DECORATED predictor ---")
    config_full = {
        "enable_validation": True,
        "expected_features": 10,
        "enable_caching": True,
        "cache_size": 100,
        "enable_timing": True,
        "enable_logging": True,
    }
    decorated = build_prediction_stack(model, config_full)
    result_decorated = decorated.predict(X_test[:5])
    print(f"  Output:      {result_decorated}")
    print(f"  Same result? {np.array_equal(result_bare, result_decorated)}")

    # ─── Demo 3: Cache hit ───
    print("\n--- Demo 3: CACHE HIT (same input, model not called again) ---")
    result_cached = decorated.predict(X_test[:5])
    print(f"  Output:      {result_cached}")
    print(f"  Same result? {np.array_equal(result_bare, result_cached)}")

    # ─── Demo 4: Validation catches bad input ───
    print("\n--- Demo 4: VALIDATION catches bad input ---")
    bad_input = np.random.randn(3, 7)
    try:
        decorated.predict(bad_input)
    except ValueError as e:
        print(f"  Caught: {e}")

    bad_nan = np.random.randn(3, 10)
    bad_nan[1, 3] = np.nan
    try:
        decorated.predict(bad_nan)
    except ValueError as e:
        print(f"  Caught: {e}")

    # ─── Demo 5: Different configs, same core ───
    print("\n--- Demo 5: DIFFERENT STACKS, same model ---")
    config_batch = {
        "enable_validation": False,
        "enable_caching": False,
        "enable_timing": True,
        "enable_logging": False,
    }
    batch_predictor = build_prediction_stack(model, config_batch)
    result_batch = batch_predictor.predict(X_test[:5])
    print(f"  Batch (minimal layers): {result_batch}")
    print(f"  Same as bare?           {np.array_equal(result_bare, result_batch)}")

    print("\n" + "=" * 70)
    print("KEY TAKEAWAY: Adding/removing layers NEVER changes the core prediction.")
    print("=" * 70)


if __name__ == "__main__":
    main()


