# Factory Pattern — Working Implementation

A working code example showing how the Factory pattern is used in ML systems, and how it naturally combines with Strategy and Repository patterns.

## Directory Structure

```
factory/
├── configs/                         # YAML experiment configs
│   ├── baseline_experiment.yaml     # Compare all models with defaults
│   ├── xgboost_tuning.yaml          # Hyperparameter tuning for one model
│   └── production.yaml              # Final production model config
├── src/
│   ├── model_factory.py             # Core factory (the pattern itself)
│   ├── model_creators.py            # Creator functions + setup_factory()
│   └── training_pipeline.py         # Pipeline that USES the factory
└── tests/
    └── test_factory.py              # Unit + integration tests
```

## How to Read This Code

Start here:

1. **`model_factory.py`** — The core pattern. A registry dict + `create()` method. Dead simple.
2. **`model_creators.py`** — Each function knows how to create ONE model type. Registered via `setup_factory()`.
3. **`training_pipeline.py`** — Shows how the factory is USED. The pipeline doesn't know which model it's training.

## How Patterns Combine

This is the key insight: **Factory doesn't live alone.** In a real ML system, it works WITH other patterns:

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   YAML Config                                               │
│   ─────────                                                 │
│   algorithm: xgboost                                        │
│   hyperparameters:                                          │
│     n_estimators: 200                                       │
│                                                              │
│          │                                                   │
│          ▼                                                   │
│   ┌─────────────────┐                                       │
│   │  MODEL FACTORY   │  ← Factory Pattern                   │
│   │  Creates model   │    "WHAT to build from config"       │
│   │  from config     │                                       │
│   └────────┬─────────┘                                       │
│            │                                                  │
│            ▼  returns a model (XGBoost, LightGBM, etc.)      │
│   ┌─────────────────┐                                       │
│   │ TRAINING PIPELINE│  ← Strategy Pattern                   │
│   │ Uses the model   │    "HOW to use it (fit/predict)"     │
│   │ (doesn't care    │    Pipeline is the same regardless   │
│   │  which one)      │    of which model was created        │
│   └────────┬─────────┘                                       │
│            │                                                  │
│            ▼  stores results                                  │
│   ┌─────────────────┐                                       │
│   │   REPOSITORY     │  ← Repository Pattern                │
│   │ Stores results   │    "WHERE to store results"          │
│   │ (file/S3/memory) │    Tests use InMemory, prod uses S3  │
│   └─────────────────┘                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Pattern Roles

| Pattern | Role in This Code | File |
|---------|-------------------|------|
| **Factory** | Creates the right model from config | `model_factory.py` + `model_creators.py` |
| **Strategy** | Model is used polymorphically by the pipeline | `training_pipeline.py` (pipeline calls `model.fit()`/`model.predict()`) |
| **Repository** | Abstracts where results are stored | `training_pipeline.py` (`ResultsRepository` protocol) |

### Why They Need Each Other

- **Factory without Strategy:** You create a model but then... `if isinstance(model, XGBClassifier)` everywhere. Pointless.
- **Strategy without Factory:** You have interchangeable models but create them with scattered if/else. Messy.
- **Both without Repository:** You can train any model from config, but results go to hardcoded files. Can't test without filesystem.

**Together:** Config → Factory creates → Pipeline uses (Strategy) → Results stored (Repository). Clean, testable, extensible.

## Running

```bash
# Run the demo
cd src
python training_pipeline.py

# Run tests
cd ..
pytest tests/ -v
```

## Adding a New Model

1. Write a creator function in `model_creators.py`:
   ```python
   def create_catboost(**kwargs):
       from catboost import CatBoostClassifier
       defaults = {"iterations": 100, "depth": 6, "verbose": 0}
       params = {**defaults, **kwargs}
       return CatBoostClassifier(**params)
   ```

2. Register it in `setup_factory()`:
   ```python
   factory.register("catboost", create_catboost)
   ```

3. Use it in any config:
   ```yaml
   algorithm: catboost
   hyperparameters:
     iterations: 500
     depth: 8
   ```

**Zero changes** to `training_pipeline.py`, `test_factory.py`, or any other consumer.


