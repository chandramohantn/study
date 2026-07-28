# Strategy Pattern

## The One-Line Summary

**You have ONE job to do, but MULTIPLE ways to do it. Let the caller pick which way.**

---

## The Problem

You're building an ML training pipeline. Today you use XGBoost. Tomorrow someone asks "can we try LightGBM?" Next week: "What about a neural net?"

Without Strategy, your code looks like this:

```python
# ❌ WITHOUT STRATEGY — growing if/else mess

class TrainingPipeline:
    def train(self, data, algorithm: str):
        if algorithm == "xgboost":
            from xgboost import XGBClassifier
            model = XGBClassifier(n_estimators=100)
            model.fit(data.X, data.y)
            return model
        elif algorithm == "lightgbm":
            from lightgbm import LGBMClassifier
            model = LGBMClassifier(n_estimators=100)
            model.fit(data.X, data.y)
            return model
        elif algorithm == "neural_net":
            import torch
            # ... 50 lines of PyTorch training ...
            return model
        elif algorithm == "random_forest":
            # ... more code ...
            pass
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
```

**Problems:**
- Every new algorithm = modify this class (Open/Closed Principle violation)
- Can't test the pipeline without importing every ML library
- The pipeline class has too many responsibilities
- Adding a new algorithm means touching code that already works

---

## How Strategy Solves It

**Separate the "what varies" (the algorithm) from "what stays the same" (the pipeline steps).**

```python
# ✅ WITH STRATEGY — each algorithm is its own class

from typing import Protocol
import numpy as np


# 1. Define WHAT a strategy must do (the interface)
class ModelStrategy(Protocol):
    def fit(self, X: np.ndarray, y: np.ndarray) -> None: ...
    def predict(self, X: np.ndarray) -> np.ndarray: ...


# 2. Implement each strategy independently
class XGBoostStrategy:
    def __init__(self, n_estimators: int = 100):
        self.n_estimators = n_estimators
        self._model = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        from xgboost import XGBClassifier
        self._model = XGBClassifier(n_estimators=self.n_estimators)
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)


class LightGBMStrategy:
    def __init__(self, n_estimators: int = 100):
        self.n_estimators = n_estimators
        self._model = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        from lightgbm import LGBMClassifier
        self._model = LGBMClassifier(n_estimators=self.n_estimators)
        self._model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)


# 3. The pipeline just USES whatever strategy it receives
class TrainingPipeline:
    def __init__(self, model: ModelStrategy):
        self.model = model  # Doesn't know or care which one

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        self.model.fit(X, y)
        predictions = self.model.predict(X)
        accuracy = (predictions == y).mean()
        return {"accuracy": accuracy}


# 4. Caller picks the strategy
pipeline = TrainingPipeline(model=XGBoostStrategy(n_estimators=200))
pipeline.train(X, y)

# Swap to a different strategy — ZERO changes to TrainingPipeline
pipeline = TrainingPipeline(model=LightGBMStrategy(n_estimators=50))
pipeline.train(X, y)
```

---

## The Key Insight: Strategy is About CHOICE

The strategies are **interchangeable alternatives** that solve **the same problem differently**:

```
Problem: "Classify this data"
  ├── Strategy A: XGBoost (tree-based, gradient boosting)
  ├── Strategy B: LightGBM (tree-based, leaf-wise growth)
  ├── Strategy C: Logistic Regression (linear, fast baseline)
  └── Strategy D: Neural Network (deep learning)

All strategies have the SAME interface: fit(X, y) → predict(X)
The caller CHOOSES which one based on the situation.
```

---

## Strategy vs Adapter — The Core Difference

This is where people get confused. Let me be very clear:

| | Strategy | Adapter |
|---|---|---|
| **Intent** | Choose between ALTERNATIVES | Make INCOMPATIBLE things work together |
| **Who you control** | You control all implementations | You DON'T control the adaptee |
| **Interface** | All strategies share the SAME interface FROM THE START | Adapter TRANSLATES from one interface to another |
| **When** | You DESIGN the interface upfront | You DISCOVER the incompatibility later |
| **Analogy** | Choosing which restaurant to eat at (all serve food) | Using a power plug adapter in a foreign country |

### The Restaurant Analogy

**Strategy:** You're hungry. You can choose Italian, Japanese, or Mexican. All restaurants serve food. You pick one.

**Adapter:** You have a US laptop with a US plug. You're in Europe. The European outlet has a different shape. You need an adapter to TRANSLATE your US plug into the European shape. You didn't CHOOSE to have different plugs — you're dealing with an existing incompatibility.

### In Code: The Difference is Crystal Clear

```python
# ─── STRATEGY: You designed all these to share the same interface ───
# All strategies were BUILT to be interchangeable from day one.

class ScalerStrategy(Protocol):
    def fit_transform(self, X: np.ndarray) -> np.ndarray: ...

class StandardScaler:  # Strategy A — you wrote this
    def fit_transform(self, X): ...

class RobustScaler:    # Strategy B — you wrote this
    def fit_transform(self, X): ...

class MinMaxScaler:    # Strategy C — you wrote this
    def fit_transform(self, X): ...


# ─── ADAPTER: You're bridging something that DOESN'T match your interface ───
# The adaptee (third-party library) has a DIFFERENT interface.
# You can't change it. You wrap it.

# Your system expects this interface:
class InferenceModel(Protocol):
    def predict(self, features: np.ndarray) -> np.ndarray: ...

# But TensorFlow's SavedModel has a DIFFERENT interface:
# tf_model.signatures["serving_default"](tf.constant(data))  ← NOT predict()!

# Adapter translates TensorFlow's interface to YOUR interface:
class TensorFlowAdapter:
    """I don't CHOOSE TensorFlow vs PyTorch. I ADAPT TensorFlow to fit my interface."""

    def __init__(self, saved_model_path: str):
        import tensorflow as tf
        self._model = tf.saved_model.load(saved_model_path)

    def predict(self, features: np.ndarray) -> np.ndarray:
        import tensorflow as tf
        # TRANSLATE: my interface → TensorFlow's interface
        tensor = tf.constant(features, dtype=tf.float32)
        output = self._model.signatures["serving_default"](tensor)
        return output["predictions"].numpy()
```

### Decision: "Do I need Strategy or Adapter?"

Ask yourself:

1. **Am I choosing between things I built?** → Strategy
2. **Am I wrapping something with a different interface?** → Adapter
3. **Did I design the interface, and implementations follow it?** → Strategy
4. **Does the thing exist already with its own interface?** → Adapter

---

## When to Use Strategy

- You have multiple algorithms for the same task (model selection, preprocessing, scoring)
- You want to A/B test different approaches
- You need to swap behavior based on config/runtime conditions
- You want to test the consumer (pipeline) without real ML libraries

---

## Complete ML Example: Feature Engineering Strategies

```python
from typing import Protocol
import pandas as pd
import numpy as np


class FeatureEngineeringStrategy(Protocol):
    """Different ways to engineer features from raw data."""
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...
    @property
    def feature_names(self) -> list[str]: ...


class SimpleFeatures:
    """Basic features — fast, interpretable."""
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "age": df["age"],
            "income_log": np.log1p(df["income"]),
            "tenure_years": df["tenure_days"] / 365,
        })

    @property
    def feature_names(self) -> list[str]:
        return ["age", "income_log", "tenure_years"]


class RichFeatures:
    """Complex features — slower but more predictive."""
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "age": df["age"],
            "age_squared": df["age"] ** 2,
            "income_log": np.log1p(df["income"]),
            "income_percentile": df["income"].rank(pct=True),
            "tenure_years": df["tenure_days"] / 365,
            "tenure_bucket": pd.cut(df["tenure_days"], bins=5, labels=False),
            "income_per_year_tenure": df["income"] / (df["tenure_days"] / 365 + 1),
        })

    @property
    def feature_names(self) -> list[str]:
        return ["age", "age_squared", "income_log", "income_percentile",
                "tenure_years", "tenure_bucket", "income_per_year_tenure"]


class EmbeddingFeatures:
    """Neural embedding features — for deep learning models."""
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        embeddings = self.embedding_model.encode(df.to_numpy())
        return pd.DataFrame(
            embeddings,
            columns=[f"emb_{i}" for i in range(embeddings.shape[1])],
        )

    @property
    def feature_names(self) -> list[str]:
        return [f"emb_{i}" for i in range(128)]


# The training pipeline doesn't care which feature strategy is used
class ChurnPredictionPipeline:
    def __init__(
        self,
        feature_strategy: FeatureEngineeringStrategy,
        model_strategy: ModelStrategy,
    ):
        self.features = feature_strategy
        self.model = model_strategy

    def train(self, raw_data: pd.DataFrame, labels: np.ndarray) -> dict:
        # 1. Feature engineering (strategy)
        X = self.features.transform(raw_data)

        # 2. Train model (strategy)
        self.model.fit(X.values, labels)

        # 3. Evaluate
        predictions = self.model.predict(X.values)
        accuracy = (predictions == labels).mean()

        return {
            "features_used": self.features.feature_names,
            "num_features": len(self.features.feature_names),
            "accuracy": accuracy,
        }


# Experiment: try different combinations
experiments = [
    ("simple+xgboost", SimpleFeatures(), XGBoostStrategy()),
    ("rich+xgboost", RichFeatures(), XGBoostStrategy()),
    ("simple+lightgbm", SimpleFeatures(), LightGBMStrategy()),
    ("rich+lightgbm", RichFeatures(), LightGBMStrategy()),
]

for name, features, model in experiments:
    pipeline = ChurnPredictionPipeline(feature_strategy=features, model_strategy=model)
    result = pipeline.train(raw_data, labels)
    print(f"{name}: accuracy={result['accuracy']:.4f} ({result['num_features']} features)")
```

---

## Testing with Strategy

Strategy makes testing trivial — inject a fake strategy:

```python
import pytest
import numpy as np


class FakeModelStrategy:
    """Test double — always predicts class 1."""
    def __init__(self):
        self.fit_called = False
        self.fit_X = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.fit_called = True
        self.fit_X = X

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.ones(len(X))


def test_pipeline_calls_fit_with_features():
    fake_model = FakeModelStrategy()
    pipeline = TrainingPipeline(model=fake_model)

    X = np.random.randn(10, 5)
    y = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    pipeline.train(X, y)

    assert fake_model.fit_called
    assert fake_model.fit_X.shape == (10, 5)
```

---

## Working Implementation

See the `strategy/` folder for a complete, runnable example:

```
strategy/
├── README.md                        # How to run and how strategies combine
├── src/
│   ├── __init__.py
│   ├── preprocessing_strategy.py    # Protocol + 3 scaling strategies
│   ├── model_strategy.py           # Protocol + 3 model strategies (sklearn only)
│   └── training_pipeline.py        # Pipeline that USES both strategies
└── tests/
    ├── __init__.py
    └── test_strategy.py            # Tests with fake strategies for isolation
```

**Run the demo:**

```bash
cd design_patterns/strategy
python3 -m src.training_pipeline
```

**Run the tests:**

```bash
python3 -m pytest tests/ -v
```

The implementation shows:
- Two independent strategy dimensions (preprocessing × model) that combine freely
- Config-driven strategy selection via registry dicts
- Fake strategies for isolated pipeline testing (no real ML in unit tests)
- 3 preprocessing × 3 models = 9 possible experiments, zero pipeline code changes


