# Factory Pattern

## The One-Line Summary

**Centralize object creation. The caller says WHAT it wants, the factory decides HOW to build it.**

---

## Motivation: Why Factory Exists

### The Real Scenario

You're working on an ML platform. Models are trained daily, evaluated weekly, and served 24/7. Different teams use different algorithms:

- Data Science team A wants XGBoost
- Data Science team B wants LightGBM
- The experimentation framework needs to try 10 algorithms from a YAML config
- The serving layer needs to load a model by name from a model registry

**The question is:** Who decides HOW to create each model? Where does that knowledge live?

### Without Factory: The Pain

```python
# ❌ PROBLEM 1: Creation logic DUPLICATED in multiple places

# In training script:
def train(config):
    if config["algorithm"] == "xgboost":
        from xgboost import XGBClassifier
        model = XGBClassifier(n_estimators=100, max_depth=6, eval_metric="logloss")
    elif config["algorithm"] == "lightgbm":
        from lightgbm import LGBMClassifier
        model = LGBMClassifier(n_estimators=100, num_leaves=31, verbose=-1)
    # ...

# In evaluation script (SAME if/else COPIED):
def evaluate(config):
    if config["algorithm"] == "xgboost":
        from xgboost import XGBClassifier
        model = XGBClassifier(n_estimators=100, max_depth=6, eval_metric="logloss")
    elif config["algorithm"] == "lightgbm":
        from lightgbm import LGBMClassifier
        model = LGBMClassifier(n_estimators=100, num_leaves=31, verbose=-1)
    # ...

# In experiment runner (SAME if/else AGAIN):
def run_experiment(config):
    if config["algorithm"] == "xgboost":
        # ... same thing for the third time ...
```

```python
# ❌ PROBLEM 2: Adding a new algorithm means editing EVERY file

# Team C says: "We want CatBoost support."
# Now you must find and modify:
#   - train.py (add elif)
#   - evaluate.py (add elif)
#   - experiment_runner.py (add elif)
#   - serve.py (add elif)
#   - ... any other place that creates models
# Miss one? Bug. Change one inconsistently? Bug.
```

```python
# ❌ PROBLEM 3: Hard to test

def test_training_pipeline():
    # To test the pipeline, you MUST have xgboost, lightgbm, sklearn installed
    # Even if you only want to test the pipeline LOGIC, not the model creation
    result = train({"algorithm": "xgboost", ...})
    # This imports xgboost just to test if the pipeline works!
```

```python
# ❌ PROBLEM 4: Defaults and configs scattered

# train.py uses: XGBClassifier(max_depth=6)
# evaluate.py uses: XGBClassifier(max_depth=8)  ← inconsistency!
# Nobody knows which is "correct"
```

### What We Need

A **single place** that knows:
1. What algorithms exist
2. How to create each one
3. What the default configs are
4. How to map a config dict/YAML to a ready-to-use object

Everything else just says: "Give me a model for this config."

---

## The Solution: Config-Driven Factory

### Core Implementation

See working code: [`factory/src/model_factory.py`](factory/src/model_factory.py)

```python
class ModelFactory:
    """Registry-based model factory."""

    def __init__(self):
        self._registry: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, creator: Callable[..., Any]) -> None:
        """Register a creator function under a name."""
        if name in self._registry:
            raise ValueError(f"Model '{name}' is already registered")
        self._registry[name] = creator

    def create(self, name: str, **kwargs) -> Any:
        """Create a model by name with given parameters."""
        if name not in self._registry:
            raise ValueError(f"Unknown model: '{name}'. Available: {self.available_models()}")
        return self._registry[name](**kwargs)

    def create_from_config(self, config: dict) -> Any:
        """
        Create from a config dict:
            {"algorithm": "xgboost", "hyperparameters": {"n_estimators": 200}}
        """
        algorithm = config.get("algorithm")
        if not algorithm:
            raise ValueError("Config must have an 'algorithm' key")
        hyperparameters = config.get("hyperparameters", {})
        return self.create(algorithm, **hyperparameters)

    def available_models(self) -> list[str]:
        return sorted(self._registry.keys())
```

### Creator Functions

See working code: [`factory/src/model_creators.py`](factory/src/model_creators.py)

Each creator function encapsulates:
- The import (lazy — only imported when that model is actually created)
- Sensible defaults
- The ability to override any parameter via kwargs

```python
def create_xgboost(**kwargs) -> Any:
    from xgboost import XGBClassifier

    defaults = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "eval_metric": "logloss",
        "random_state": 42,
    }
    params = {**defaults, **kwargs}
    return XGBClassifier(**params)


def create_lightgbm(**kwargs) -> Any:
    from lightgbm import LGBMClassifier

    defaults = {
        "n_estimators": 100,
        "num_leaves": 31,
        "learning_rate": 0.1,
        "verbose": -1,
        "random_state": 42,
    }
    params = {**defaults, **kwargs}
    return LGBMClassifier(**params)
```

### Registration (Explicit, No Decorators)

```python
def setup_factory() -> ModelFactory:
    """Single place where all models are registered."""
    factory = ModelFactory()
    factory.register("xgboost", create_xgboost)
    factory.register("lightgbm", create_lightgbm)
    factory.register("random_forest", create_random_forest)
    factory.register("logistic_regression", create_logistic_regression)
    factory.register("gradient_boosting", create_gradient_boosting)
    return factory
```

### Config-Driven Usage (YAML → Model)

```yaml
# configs/baseline_experiment.yaml
experiments:
  - algorithm: logistic_regression

  - algorithm: xgboost
    hyperparameters:
      n_estimators: 50
      max_depth: 4

  - algorithm: lightgbm
    hyperparameters:
      n_estimators: 50
      num_leaves: 15
```

```python
# The pipeline reads YAML and creates models — zero if/else
for experiment in config["experiments"]:
    model = factory.create_from_config(experiment)
    model.fit(X_train, y_train)
```

---

## How Factory Combines With Other Patterns

Factory is rarely used alone. In the working implementation (`factory/src/training_pipeline.py`), it combines naturally with Strategy and Repository:

```
YAML Config
    │
    ▼
┌──────────────────┐
│  MODEL FACTORY   │  ← Factory Pattern: CREATES the model from config
└────────┬─────────┘
         │ returns model
         ▼
┌──────────────────┐
│TRAINING PIPELINE │  ← Strategy Pattern: USES model.fit()/model.predict()
│                  │    without knowing which algorithm it is
└────────┬─────────┘
         │ stores results
         ▼
┌──────────────────┐
│   REPOSITORY     │  ← Repository Pattern: STORES results (file/S3/memory)
└──────────────────┘
```

```python
class TrainingPipeline:
    def __init__(self, factory: ModelFactory, results_repo: ResultsRepository):
        self.factory = factory          # Factory creates models
        self.results_repo = results_repo  # Repository stores results

    def run_single(self, config: dict, X, y):
        model = self.factory.create_from_config(config)  # Factory
        model.fit(X_train, y_train)                      # Strategy (model is interchangeable)
        result = evaluate(model, X_test, y_test)
        self.results_repo.save_result(result)            # Repository
```

### Why They Need Each Other

| Without... | Problem |
|---|---|
| Factory | Pipeline has if/else to create models. Adding new model = change pipeline. |
| Strategy | You create the model cleanly but then do `if isinstance(model, XGB)` everywhere. |
| Repository | Results hardcoded to file system. Can't test without disk. Can't swap to S3. |

---

## Adding a New Model (The Payoff)

Change ONE file (`model_creators.py`):

```python
# 1. Write the creator
def create_catboost(**kwargs):
    from catboost import CatBoostClassifier
    defaults = {"iterations": 100, "depth": 6, "verbose": 0, "random_state": 42}
    params = {**defaults, **kwargs}
    return CatBoostClassifier(**params)

# 2. Register it in setup_factory()
factory.register("catboost", create_catboost)
```

**Zero changes** to training pipeline, evaluation scripts, experiment runner, or serving layer. They all automatically support CatBoost because they just call `factory.create_from_config(config)`.

---

## Opinion on Decorators in Factory Pattern

### The Decorator Approach

```python
# Some people do this:
@ModelFactory.register("xgboost")
def create_xgboost(**kwargs):
    ...
```

### Why I Recommend Against It (for Factory specifically)

| Issue | Explanation |
|-------|-------------|
| **Hidden side effects** | Registration happens at import time, as a side effect. Not explicit. |
| **Import order bugs** | Forget to import the file? Model silently missing. No error until runtime. |
| **Harder to grep** | "Where is xgboost registered?" Harder to find than `factory.register("xgboost", ...)` |
| **Team readability** | ML engineers who aren't Python experts find explicit `.register()` immediately obvious. |

### Industry Evidence

scikit-learn, Hugging Face, MLflow, FastAPI, PyTorch Lightning — all use **explicit dict registration**, not decorators for this pattern.

**Verdict:** `factory.register("xgboost", create_xgboost)` is clear, greppable, and obvious. Use it.

---

## Factory vs Strategy vs Adapter

| | Factory | Strategy | Adapter |
|---|---|---|---|
| **Question** | "How do I BUILD this from config?" | "How do I CHOOSE between alternatives?" | "How do I make X FIT my interface?" |
| **Focus** | Object CREATION | Object USAGE | Interface TRANSLATION |
| **Input** | Config/name → object | Already-created object → used by consumer | Incompatible object → wrapped |

They work together: **Factory creates → Strategy uses → Adapter bridges**

---

## Other Scenarios Where Factory Pattern is Useful

### AI/ML Scenarios

| Scenario | What the Factory Creates | Why Factory Helps |
|----------|--------------------------|-------------------|
| **Model selection from config** | Different ML algorithms (XGBoost, LightGBM, etc.) | Run experiments from YAML without code changes |
| **Preprocessing pipeline steps** | Scalers, encoders, imputers from config | Different preprocessing per feature set |
| **Feature engineering strategies** | Different feature generators | Swap feature engineering without touching pipeline |
| **Data loaders** | Readers for CSV, Parquet, Avro, JSON | Add new format support without changing ETL |
| **Model serving adapters** | Inference wrappers for ONNX, TorchScript, pickle | Deploy models in any format from config |
| **Embedding models** | Sentence-BERT, OpenAI, local embeddings | Swap embedding provider without changing RAG pipeline |
| **LLM providers** | OpenAI, Anthropic, local LLM, HuggingFace | Switch LLM providers from environment variable |
| **Vector store backends** | Pinecone, Weaviate, ChromaDB, FAISS | Swap vector DB per environment |
| **Metrics collectors** | Prometheus, StatsD, CloudWatch, in-memory | Different monitoring in dev vs prod |
| **Experiment trackers** | MLflow, W&B, Neptune, simple file logger | Swap tracking tool without touching training code |

### Data Pipeline Scenarios

| Scenario | What the Factory Creates | Why Factory Helps |
|----------|--------------------------|-------------------|
| **Data source connectors** | S3, GCS, Azure Blob, local file, SFTP readers | Add new source types without changing pipeline |
| **Data sink connectors** | PostgreSQL, BigQuery, Snowflake, Parquet writers | Swap destination from config |
| **Data validators** | Schema validators for different table schemas | Validate different tables with same framework |
| **Transformation steps** | Different transform functions registered by name | Compose pipelines from config files |
| **Notification channels** | Email, Slack, PagerDuty, Teams alerters | Add new notification channel without touching alerting code |
| **Scheduler backends** | Airflow, Prefect, Cron, manual triggers | Swap orchestration tool per environment |
| **File format parsers** | CSV, Parquet, Avro, JSON-Lines, XML parsers | Handle any input format from config |
| **Quality check rules** | Null checks, range checks, uniqueness checks | Add new rules by registering them |

### General Software Engineering Scenarios

| Scenario | What the Factory Creates | Why Factory Helps |
|----------|--------------------------|-------------------|
| **Database connections** | PostgreSQL, MySQL, SQLite, DynamoDB clients | Same code works against different DBs |
| **Cache backends** | Redis, Memcached, in-memory, file-based | Swap cache per environment |
| **Authentication strategies** | JWT, OAuth2, API key, session auth handlers | Add new auth method without touching routes |
| **Payment gateways** | Stripe, PayPal, Square, Braintree clients | Support new payment providers from config |
| **Email providers** | SendGrid, SES, Mailgun, SMTP senders | Swap email backend without touching business logic |
| **Storage backends** | Local disk, S3, GCS, Azure Blob | Dev uses local, prod uses cloud — same code |
| **Serialization formats** | JSON, MessagePack, Protocol Buffers, Avro | Support different wire formats |
| **HTTP clients** | requests, httpx, aiohttp — configured with auth/retry | Centralize HTTP client creation with proper defaults |
| **Logger configurations** | Structured JSON logger, plain text, CloudWatch | Different logging per environment |
| **Report generators** | PDF, Excel, HTML, Markdown report builders | Generate reports in any format from config |

### Concrete Examples

```python
# ─── Example: Data Source Factory ───

source_factory = DataSourceFactory()
source_factory.register("s3", create_s3_reader)
source_factory.register("gcs", create_gcs_reader)
source_factory.register("local", create_local_reader)
source_factory.register("postgres", create_postgres_reader)

# Config says where to read from — code doesn't change:
source = source_factory.create_from_config({"type": "s3", "bucket": "data-lake", "path": "raw/"})
df = source.read()


# ─── Example: Notification Factory ───

notification_factory = NotificationFactory()
notification_factory.register("slack", create_slack_notifier)
notification_factory.register("email", create_email_notifier)
notification_factory.register("pagerduty", create_pagerduty_notifier)

# Pipeline failure → notify via config:
notifier = notification_factory.create(config["alert_channel"], webhook_url=config["webhook"])
notifier.send("Pipeline failed: data quality check")


# ─── Example: Embedding Model Factory ───

embedding_factory = EmbeddingFactory()
embedding_factory.register("openai", create_openai_embeddings)
embedding_factory.register("sentence_bert", create_sbert_embeddings)
embedding_factory.register("local_llama", create_local_embeddings)

# RAG pipeline uses whatever embedding model is configured:
embedder = embedding_factory.create(config["embedding_model"])
vectors = embedder.encode(documents)
```

---

## Working Implementation

See the [`factory/`](factory/) directory for a complete working example:

```
factory/
├── configs/                         # YAML experiment configs
│   ├── baseline_experiment.yaml     # Compare all models with defaults
│   ├── xgboost_tuning.yaml          # Hyperparameter tuning
│   └── production.yaml              # Final production config
├── src/
│   ├── model_factory.py             # Core factory (registry + create)
│   ├── model_creators.py            # Creator functions + setup
│   └── training_pipeline.py         # Pipeline using Factory + Strategy + Repository
└── tests/
    └── test_factory.py              # Unit + integration tests
```

---

## When to Use Factory

| ✅ Use When | ❌ Don't Use When |
|---|---|
| Multiple places create the same kinds of objects | Only one place creates objects |
| Creation logic is complex (many params, imports) | Construction is trivial: `MyClass(x)` |
| You create objects from config/YAML/environment | You always know the exact class at code time |
| Adding new types should require minimal changes | You have exactly 1-2 types and won't add more |
| You want centralized defaults and validation | Defaults are simple and obvious |
| Different environments need different implementations | Same implementation everywhere |

---

## Summary

```
FACTORY answers: "Where does the knowledge of HOW to build things live?"

Without Factory: Scattered across files. Duplicated. Inconsistent.
With Factory:    One place. One source of truth. Change once, works everywhere.

Industry standard:
  1. A registry (dict mapping names → creators)
  2. Explicit .register() calls
  3. A .create(name, **params) method
  4. Creator functions with sensible defaults
  5. A .create_from_config(dict) method for YAML/JSON driven workflows

That's it. No magic. No decorators. Just a well-organized dict.
```
