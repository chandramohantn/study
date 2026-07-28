# Strategy Pattern — Working Implementation

A working code example showing how the Strategy pattern lets you swap preprocessing and model algorithms in an ML pipeline without modifying the pipeline itself.

## Directory Structure

```
strategy/
├── README.md                        # This file
├── src/
│   ├── __init__.py
│   ├── preprocessing_strategy.py    # Protocol + 3 scaling strategies
│   ├── model_strategy.py           # Protocol + 3 model strategies (sklearn only)
│   └── training_pipeline.py        # Pipeline that USES both strategies
└── tests/
    ├── __init__.py
    └── test_strategy.py            # Tests with fake strategies for isolation
```

## How to Read This Code

Start here:

1. **`preprocessing_strategy.py`** — The Protocol defines WHAT any scaler must do. Three implementations show HOW: StandardScaler (z-score), RobustScaler (median/IQR), NoScaling (pass-through).

2. **`model_strategy.py`** — Same idea for models. Protocol defines fit/predict/predict_proba. Three sklearn implementations: LogisticRegression, RandomForest, GradientBoosting.

3. **`training_pipeline.py`** — The CONSUMER. It accepts any strategy that satisfies the protocol. It never imports or mentions specific scalers/models. Config dicts drive which strategies are used.

4. **`tests/test_strategy.py`** — Shows the testing power of Strategy: inject `FakePreprocessingStrategy` and `FakeModelStrategy` to test pipeline logic WITHOUT any real ML computation.

## How to Run

```bash
# Run the demo (from the strategy/ directory)
python -m src.training_pipeline

# Run tests
pytest tests/ -v
```

**Requirements:** Only `scikit-learn` and `numpy` (plus `pytest` for tests).

## How Strategies Combine

The key insight: **two independent strategy dimensions combine freely**.

```
Preprocessing Strategy     Model Strategy          Pipeline
─────────────────────     ──────────────────      ────────
StandardScaler        ×   LogisticRegression  →   Experiment 1
NoScaling             ×   RandomForest        →   Experiment 2
RobustScaler          ×   GradientBoosting    →   Experiment 3
StandardScaler        ×   GradientBoosting    →   Experiment 4
...                       ...                     ...
```

3 preprocessing × 3 models = 9 combinations, ALL driven by config:

```python
config = {
    "preprocessing": "robust",           # Pick one
    "model": "gradient_boosting",        # Pick one
    "model_params": {"n_estimators": 200, "learning_rate": 0.05},
}
pipeline = create_pipeline_from_config(config)
```

## Adding a New Strategy

To add MinMaxScaler:

1. Create `MinMaxScalerStrategy` class with `fit()`, `transform()`, `fit_transform()`
2. Add `"minmax": MinMaxScalerStrategy` to `PREPROCESSING_REGISTRY`
3. Done. Pipeline code unchanged. Tests unchanged.

To add a new model (e.g., SVM):

1. Create `SVMStrategy` class with `fit()`, `predict()`, `predict_proba()`
2. Add `"svm": SVMStrategy` to `MODEL_REGISTRY`
3. Done.

## Testing Pattern: Fakes for Isolation

The most powerful benefit of Strategy for testing:

```python
class FakeModelStrategy:
    """Always predicts class 1. Records calls for assertions."""
    def __init__(self):
        self.fit_called = False

    def fit(self, X, y):
        self.fit_called = True

    def predict(self, X):
        return np.ones(len(X))

    def predict_proba(self, X):
        return np.column_stack([np.full(len(X), 0.1), np.full(len(X), 0.9)])

# Test pipeline logic without ANY real ML
pipeline = TrainingPipeline(preprocessing=FakePreprocessing(), model=FakeModelStrategy())
pipeline.train(X, y)
assert fake_model.fit_called  # ✅ Pipeline called fit correctly
```


