# Dependency Injection in Python

Dependency Injection (DI) is one of those concepts that sounds unnecessarily abstract until you hit systems that are hard to test, hard to evolve, and full of hidden coupling.

The core problem DI solves is not “how to pass objects around.”

The real problem is:

> “How do I build software components that are independently replaceable, testable, configurable, and composable?”

That matters a lot once systems grow beyond small scripts.

---

# 1. First understand the actual problem

Let’s start with a realistic backend service.

Suppose you're building an ML inference platform.

You have:

* API layer
* model inference service
* feature store client
* database
* Kafka producer
* metrics logger
* cache
* authentication service

Now imagine this class:

```python
class PredictionService:
    def __init__(self):
        self.db = PostgreSQLClient()
        self.cache = RedisClient()
        self.model = ResNetModel()
        self.metrics = PrometheusClient()
        self.kafka = KafkaProducer()
```

This looks fine initially.

But now observe the problems.

---

# 2. The hidden coupling problem

`PredictionService` is now tightly coupled to:

* PostgreSQL
* Redis
* Kafka
* Prometheus
* specific model implementation

The class decides:

* WHAT dependencies it needs
* HOW those dependencies are created

That second point is the issue.

The class is doing two responsibilities:

1. business logic
2. dependency construction

This violates separation of concerns.

---

# 3. Why this becomes painful in real systems

## Problem 1: Testing becomes difficult

Suppose you want to test inference logic.

Now your test:

* connects to PostgreSQL
* initializes Redis
* maybe loads a 2GB model
* creates Kafka connection

You don't actually care about those in unit tests.

You only care about:

* prediction logic
* response handling

Without DI, mocking becomes ugly.

---

# 4. Example without DI

```python
class PredictionService:
    def __init__(self):
        self.db = PostgreSQLClient()

    def predict(self, user_id):
        user_data = self.db.fetch(user_id)
        return run_model(user_data)
```

Testing:

```python
service = PredictionService()
service.predict(123)
```

Now your test depends on:

* actual DB
* actual schema
* actual connectivity

This is no longer a unit test.

It became an integration test accidentally.

---

# 5. Dependency Injection fixes this

Instead of the class creating dependencies:

```python
self.db = PostgreSQLClient()
```

you inject them from outside.

```python
class PredictionService:
    def __init__(self, db):
        self.db = db
```

Now:

```python
db = PostgreSQLClient()
service = PredictionService(db)
```

The class no longer cares:

* how DB is created
* whether it's PostgreSQL
* whether it's a mock
* whether it's in-memory

This is the key idea.

---

# 6. Now testing becomes easy

```python
class FakeDB:
    def fetch(self, user_id):
        return {"age": 30}

service = PredictionService(FakeDB())
```

Now:

* no DB connection
* no network
* deterministic
* fast tests

This is one of the biggest reasons DI exists.

---

# 7. Real production benefit: replaceability

Imagine:

Today:

* Redis cache

Tomorrow:

* Memcached

Without DI:

You modify internal code everywhere.

With DI:

```python
cache = RedisCache()
service = PredictionService(cache)
```

Later:

```python
cache = Memcached()
service = PredictionService(cache)
```

Business logic remains untouched.

This becomes extremely important in:

* cloud migrations
* vendor migrations
* experimentation
* A/B infrastructure rollout

---

# 8. Real-world architecture example

Consider a production inference API.

---

## Without DI

```python
class InferenceAPI:
    def __init__(self):
        self.feature_store = FeastClient()
        self.model = XGBoostModel.load()
        self.logger = DatadogLogger()
        self.metrics = PrometheusClient()
```

Problems:

* hardcoded infrastructure
* hard to test
* difficult local development
* difficult staging/prod switching

---

## With DI

```python
class InferenceAPI:
    def __init__(
        self,
        feature_store,
        model,
        logger,
        metrics
    ):
        self.feature_store = feature_store
        self.model = model
        self.logger = logger
        self.metrics = metrics
```

Then composition happens externally:

```python
api = InferenceAPI(
    feature_store=FeastClient(),
    model=XGBoostModel.load(),
    logger=DatadogLogger(),
    metrics=PrometheusClient()
)
```

Now the API logic is infrastructure-agnostic.

This is a major architectural advantage.

---

# 9. DI is really about inversion of control

Normally:

```text
Class controls dependency creation
```

With DI:

```text
External system controls dependency creation
```

This concept is called:

## Inversion of Control (IoC)

The object says:

> "I need a database"

NOT:

> "I will create PostgreSQL specifically."

That distinction matters.

---

# 10. Why frameworks heavily use DI

Frameworks like:

* FastAPI
* Spring Framework
* ASP.NET Core

use DI extensively because enterprise systems require:

* modularity
* testability
* lifecycle management
* configuration abstraction

---

# 11. FastAPI example (real Python DI)

In FastAPI:

```python
from fastapi import Depends

def get_db():
    return PostgreSQLClient()

@app.get("/users/{id}")
def get_user(id: int, db = Depends(get_db)):
    return db.fetch(id)
```

FastAPI injects the dependency automatically.

Why useful?

Because now:

* request-scoped objects
* DB sessions
* auth
* config
* logging

can all be centrally managed.

---

# 12. Bigger production advantage: lifecycle management

Imagine:

* DB connection pooling
* GPU model loading
* Kafka producer reuse

You do NOT want every class creating them independently.

DI containers/frameworks help manage:

* singleton lifecycle
* per-request lifecycle
* lazy loading
* cleanup

This becomes critical in production ML systems.

Example:

* loading a 10GB LLM once globally
* injecting reference into services

instead of loading per request.

---

# 13. Another important point: DI != framework

A lot of people misunderstand this.

You do NOT need:

* special libraries
* containers
* annotations

Basic constructor injection is already DI.

This is DI:

```python
class Service:
    def __init__(self, db):
        self.db = db
```

Frameworks only automate wiring.

---

# 14. Types of dependency injection

## Constructor Injection (most common)

```python
Service(db)
```

Best approach usually.

---

## Setter Injection

```python
service.db = db
```

Less safe.

Dependency may be missing.

---

## Method Injection

```python
def predict(data, model):
```

Useful for stateless functions.

---

# 15. Where DI becomes extremely valuable

DI matters much more in:

* large systems
* microservices
* ML platforms
* distributed systems
* enterprise applications
* systems with infrastructure abstractions

Less important in:

* scripts
* small utilities
* one-file apps

A common anti-pattern is overengineering DI in tiny projects.

---

# 16. Important misconception

People often think:

> “DI is for flexibility.”

Partly true.

But the deeper reason is:

## Controlling coupling

DI reduces:

* hardcoded dependencies
* hidden infrastructure assumptions
* construction coupling

That improves:

* testing
* maintainability
* scalability
* extensibility

---

# 17. Mental model

Think of a restaurant kitchen.

Bad design:

```text
Chef personally goes and buys:
- stove
- vegetables
- utensils
- gas cylinder
```

Good design:

```text
Kitchen infrastructure is provided externally.
Chef focuses only on cooking.
```

DI is exactly this.

The service should focus on:

* business logic

NOT:

* constructing infrastructure

---

# 18. Practical Python advice

For Python specifically:

## Simple apps

Use plain constructor injection.

No framework needed.

---

## Medium/Large apps

Use:

* factories
* application containers
* FastAPI Depends
* lightweight DI containers only if complexity justifies it

---

## Avoid this trap

Do not build:

* overly abstract provider hierarchies
* Java-style DI overengineering

Python is dynamic.

Keep DI explicit and readable.

---

# 19. A realistic ML system example

Suppose you're building:

```text
Fraud Detection API
```

Dependencies:

* feature store
* model registry
* Redis cache
* metrics collector
* Kafka event publisher

With DI:

You can:

* swap model versions
* test with fake feature stores
* run locally without Kafka
* benchmark with mock caches
* inject GPU vs CPU model runners

without rewriting business logic.

That is the actual power of DI in production systems.
