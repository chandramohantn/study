# Inheritance vs Composition in Python

A comprehensive guide to understanding when and how to use inheritance, composition, Protocols, and Abstract Base Classes (ABCs) in Python.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Inheritance — The "is-a" Relationship](#inheritance--the-is-a-relationship)
3. [Composition — The "has-a" Relationship](#composition--the-has-a-relationship)
4. [Head-to-Head Comparison](#head-to-head-comparison)
5. [Abstract Base Classes (ABCs)](#abstract-base-classes-abcs)
6. [Protocols — Structural Subtyping](#protocols--structural-subtyping)
7. [ABCs vs Protocols — When to Use Which](#abcs-vs-protocols--when-to-use-which)
8. [Real-World Scenario: Payment Processing System](#real-world-scenario-payment-processing-system)
9. [Decision Framework](#decision-framework)
10. [Common Pitfalls](#common-pitfalls)
11. [FAQ](#faq)

---

## Core Concepts

| Concept | Relationship | Key Idea |
|---------|-------------|----------|
| Inheritance | "is-a" | A Dog **is an** Animal |
| Composition | "has-a" | A Car **has an** Engine |

The fundamental question: **Should your class BE something, or should it HAVE something?**

---

## Inheritance — The "is-a" Relationship

Inheritance creates a parent-child hierarchy. The child class inherits all attributes and methods from the parent and can override or extend them.

### Basic Example

```python
class Animal:
    def __init__(self, name: str, sound: str):
        self.name = name
        self.sound = sound

    def speak(self) -> str:
        return f"{self.name} says {self.sound}!"

    def describe(self) -> str:
        return f"I am {self.name}, an animal."


class Dog(Animal):
    def __init__(self, name: str):
        super().__init__(name, sound="Woof")

    def fetch(self) -> str:
        return f"{self.name} fetches the ball!"


class Cat(Animal):
    def __init__(self, name: str):
        super().__init__(name, sound="Meow")

    def purr(self) -> str:
        return f"{self.name} is purring..."


# Usage
dog = Dog("Rex")
print(dog.speak())      # Rex says Woof!
print(dog.describe())   # I am Rex, an animal.
print(dog.fetch())      # Rex fetches the ball!
```

### When Inheritance Works Well

- True "is-a" relationships (a Dog really IS an Animal)
- You want to reuse a well-defined parent implementation
- The hierarchy is shallow (1-2 levels deep)
- The parent class is stable and unlikely to change frequently

### The Problem with Deep Inheritance

```python
# ❌ This gets messy fast
class Vehicle:
    pass

class MotorVehicle(Vehicle):
    pass

class FourWheelVehicle(MotorVehicle):
    pass

class Car(FourWheelVehicle):
    pass

class ElectricCar(Car):
    pass

class TeslaModelS(ElectricCar):
    pass
# Now you need a change in Vehicle... it cascades through 6 levels!
```

### The Diamond Problem (Multiple Inheritance)

```python
class A:
    def greet(self):
        return "Hello from A"

class B(A):
    def greet(self):
        return "Hello from B"

class C(A):
    def greet(self):
        return "Hello from C"

class D(B, C):
    pass

# Which greet() does D use?
d = D()
print(d.greet())  # "Hello from B" — Python uses MRO (Method Resolution Order)
print(D.__mro__)  # Shows: D -> B -> C -> A -> object
```

Python resolves this with MRO (C3 linearization), but it creates confusion and tight coupling.

---

## Composition — The "has-a" Relationship

Composition means building complex objects by combining simpler ones. Instead of inheriting behavior, you **delegate** to other objects.

### Basic Example

```python
class Engine:
    def __init__(self, horsepower: int):
        self.horsepower = horsepower
        self._running = False

    def start(self) -> str:
        self._running = True
        return f"Engine ({self.horsepower}hp) started"

    def stop(self) -> str:
        self._running = False
        return "Engine stopped"


class GPS:
    def navigate(self, destination: str) -> str:
        return f"Navigating to {destination}..."


class Car:
    def __init__(self, engine: Engine, gps: GPS | None = None):
        self.engine = engine  # Car HAS an Engine
        self.gps = gps        # Car HAS a GPS (optional)

    def start(self) -> str:
        return self.engine.start()

    def drive_to(self, destination: str) -> str:
        if self.gps:
            return self.gps.navigate(destination)
        return "No GPS available"


# Usage — you can swap components easily
sports_engine = Engine(horsepower=450)
economy_engine = Engine(horsepower=120)

sports_car = Car(engine=sports_engine, gps=GPS())
economy_car = Car(engine=economy_engine)

print(sports_car.start())          # Engine (450hp) started
print(sports_car.drive_to("NYC"))  # Navigating to NYC...
```

### Why Composition is Preferred

1. **Flexibility** — swap components at runtime
2. **Testability** — mock individual components easily
3. **Low coupling** — changing one component doesn't break others
4. **No diamond problem** — no MRO confusion
5. **Single Responsibility** — each class does one thing

### Composition with Dependency Injection

```python
class Logger:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")


class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def query(self, sql: str) -> list:
        return [{"id": 1, "name": "Alice"}]


class UserService:
    """UserService doesn't inherit from anything.
    It COMPOSES a database and logger."""

    def __init__(self, db: Database, logger: Logger):
        self.db = db
        self.logger = logger

    def get_user(self, user_id: int) -> dict:
        self.logger.log(f"Fetching user {user_id}")
        results = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        return results[0] if results else {}


# Easy to test — just pass mock objects
service = UserService(db=Database("sqlite://test.db"), logger=Logger())
```

---

## Head-to-Head Comparison

| Aspect | Inheritance | Composition |
|--------|-------------|-------------|
| Relationship | "is-a" | "has-a" |
| Coupling | Tight (child depends on parent internals) | Loose (depends only on interface) |
| Flexibility | Static (set at class definition) | Dynamic (swap at runtime) |
| Code Reuse | Through class hierarchy | Through delegation |
| Testing | Hard to isolate (parent included) | Easy to mock components |
| Hierarchy Depth | Gets fragile when deep | Flat by nature |
| Encapsulation | Breaks encapsulation (child sees parent internals) | Preserves encapsulation |
| When to Use | True taxonomies, framework extension points | Almost everything else |

### The Litmus Test

Ask yourself: **"Would it make sense to substitute the child anywhere the parent is used?"**

- If YES → inheritance might be appropriate (Liskov Substitution Principle)
- If NO → use composition

```python
# ✅ Good inheritance — a Square IS a Shape
class Shape:
    def area(self) -> float: ...

class Square(Shape):
    def area(self) -> float: ...

# ❌ Bad inheritance — a Stack is NOT a List (it just uses one internally)
class Stack(list):  # DON'T DO THIS
    pass
# Now Stack exposes .insert(), .sort(), etc. which break stack semantics

# ✅ Good composition — a Stack HAS a list
class Stack:
    def __init__(self):
        self._items: list = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop()
```

---

## Abstract Base Classes (ABCs)

ABCs define a **contract** that subclasses MUST fulfill. They enforce that certain methods exist at class definition time (not at runtime when the method is called).

### When to Use ABCs

- You want to **enforce a contract** — "every subclass MUST implement these methods"
- You're building a **framework or library** where others will extend your code
- You need **shared implementation** alongside the contract (mixin behavior)
- You want **runtime isinstance() checks** to work

### Basic ABC Example

```python
from abc import ABC, abstractmethod


class NotificationSender(ABC):
    """Contract: every notification sender must implement send()."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        """Send a notification. Returns True if successful."""
        ...

    def validate_recipient(self, recipient: str) -> bool:
        """Shared implementation — all subclasses get this for free."""
        return "@" in recipient or recipient.startswith("+")


class EmailSender(NotificationSender):
    def send(self, recipient: str, message: str) -> bool:
        print(f"📧 Sending email to {recipient}: {message}")
        return True


class SMSSender(NotificationSender):
    def send(self, recipient: str, message: str) -> bool:
        print(f"📱 Sending SMS to {recipient}: {message}")
        return True


# This will raise TypeError at instantiation time:
class BrokenSender(NotificationSender):
    pass  # forgot to implement send()

# sender = BrokenSender()
# TypeError: Can't instantiate abstract class BrokenSender
#            with abstract method send
```

### ABC with Abstract Properties

```python
from abc import ABC, abstractmethod


class Repository(ABC):
    """Base repository contract."""

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Each repo must declare its table."""
        ...

    @abstractmethod
    def find_by_id(self, id: int) -> dict | None:
        ...

    @abstractmethod
    def save(self, entity: dict) -> None:
        ...

    def find_all(self) -> list[dict]:
        """Default implementation — subclasses can override."""
        print(f"SELECT * FROM {self.table_name}")
        return []


class UserRepository(Repository):
    @property
    def table_name(self) -> str:
        return "users"

    def find_by_id(self, id: int) -> dict | None:
        print(f"SELECT * FROM {self.table_name} WHERE id = {id}")
        return {"id": id, "name": "Alice"}

    def save(self, entity: dict) -> None:
        print(f"INSERT INTO {self.table_name} VALUES ...")
```

### Key Characteristics of ABCs

1. **Nominal subtyping** — classes must explicitly inherit from the ABC
2. **Fail-fast** — errors at instantiation, not at method call time
3. **Can have concrete methods** — shared logic lives in the ABC
4. **isinstance() works** — `isinstance(email_sender, NotificationSender)` → True
5. **Part of Python stdlib** — `collections.abc` provides many useful ABCs

---

## Protocols — Structural Subtyping

Protocols (PEP 544, Python 3.8+) define a contract based on **structure**, not inheritance. If an object has the right methods/attributes, it satisfies the Protocol — no explicit inheritance needed.

This is **duck typing with type-checker support**: "If it walks like a duck and quacks like a duck, it's a duck."

### When to Use Protocols

- You want **duck typing** but with type safety
- You're writing code that should work with **any object that has certain methods**
- You **don't control** the classes that need to conform (third-party code)
- You want **loose coupling** — no forced inheritance hierarchy
- You're doing **composition** and need to type-hint the components

### Basic Protocol Example

```python
from typing import Protocol


class Drawable(Protocol):
    """Any object with a draw() method satisfies this Protocol."""

    def draw(self) -> str:
        ...


class Circle:
    """Note: does NOT inherit from Drawable!"""

    def draw(self) -> str:
        return "Drawing a circle ⭕"


class Square:
    """Also does NOT inherit from Drawable!"""

    def draw(self) -> str:
        return "Drawing a square ⬜"


class Text:
    """This also satisfies Drawable — it has draw()."""

    def __init__(self, content: str):
        self.content = content

    def draw(self) -> str:
        return f"Drawing text: {self.content}"


def render(shapes: list[Drawable]) -> None:
    """Accepts anything that has a draw() method."""
    for shape in shapes:
        print(shape.draw())


# All of these work — no inheritance needed!
render([Circle(), Square(), Text("Hello")])
```

### Protocol with Attributes and Multiple Methods

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Serializable(Protocol):
    """Objects that can be serialized and deserialized."""

    format: str  # Must have a 'format' attribute

    def serialize(self) -> bytes:
        ...

    def deserialize(self, data: bytes) -> None:
        ...


class JSONDocument:
    format: str = "json"

    def __init__(self, data: dict | None = None):
        self.data = data or {}

    def serialize(self) -> bytes:
        import json
        return json.dumps(self.data).encode()

    def deserialize(self, data: bytes) -> None:
        import json
        self.data = json.loads(data.decode())


class XMLDocument:
    format: str = "xml"

    def serialize(self) -> bytes:
        return b"<doc>...</doc>"

    def deserialize(self, data: bytes) -> None:
        pass


# @runtime_checkable enables isinstance() checks (with limitations)
doc = JSONDocument({"key": "value"})
print(isinstance(doc, Serializable))  # True (checks methods exist, not signatures)


def save_document(doc: Serializable, path: str) -> None:
    """Works with ANY object matching the Serializable structure."""
    data = doc.serialize()
    print(f"Saving {doc.format} document ({len(data)} bytes) to {path}")
```

### Protocols for Callbacks and Strategy Pattern

```python
from typing import Protocol


class RetryStrategy(Protocol):
    def should_retry(self, attempt: int, error: Exception) -> bool:
        ...

    def get_delay(self, attempt: int) -> float:
        ...


class ExponentialBackoff:
    """Satisfies RetryStrategy without inheriting from it."""

    def __init__(self, base_delay: float = 1.0, max_retries: int = 5):
        self.base_delay = base_delay
        self.max_retries = max_retries

    def should_retry(self, attempt: int, error: Exception) -> bool:
        return attempt < self.max_retries

    def get_delay(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)


class NoRetry:
    """Also satisfies RetryStrategy."""

    def should_retry(self, attempt: int, error: Exception) -> bool:
        return False

    def get_delay(self, attempt: int) -> float:
        return 0


class HTTPClient:
    def __init__(self, retry_strategy: RetryStrategy):
        self.retry = retry_strategy

    def fetch(self, url: str) -> str:
        for attempt in range(10):
            try:
                return f"Response from {url}"
            except Exception as e:
                if not self.retry.should_retry(attempt, e):
                    raise
                delay = self.retry.get_delay(attempt)
                print(f"Retrying in {delay}s...")
        return ""


# Swap strategies without changing HTTPClient
client = HTTPClient(retry_strategy=ExponentialBackoff(max_retries=3))
```

---

## ABCs vs Protocols — When to Use Which

| Aspect | ABC | Protocol |
|--------|-----|----------|
| Subtyping | Nominal (must inherit) | Structural (just match the shape) |
| Coupling | Higher (forced inheritance) | Lower (no inheritance needed) |
| Error Timing | Instantiation time | Type-check time (mypy) |
| Shared Implementation | ✅ Can have concrete methods | ❌ No shared implementation |
| isinstance() | ✅ Works naturally | ⚠️ Only with @runtime_checkable |
| Third-party Classes | ❌ Must modify them to inherit | ✅ Works without modification |
| Discovery | Easy (just look at parent class) | Harder (grep for Protocol) |
| Best For | Frameworks, enforced contracts | Loose coupling, duck typing |

### Decision Flowchart

```
Do you need shared implementation in the base?
├── YES → Use ABC
│
└── NO → Do you control all implementing classes?
    ├── NO → Use Protocol (can't force them to inherit)
    │
    └── YES → Do you want isinstance() checks at runtime?
        ├── YES → Use ABC (or @runtime_checkable Protocol)
        │
        └── NO → Do you want maximum flexibility?
            ├── YES → Use Protocol
            └── NO → Either works, prefer Protocol for loose coupling
```

### Using Both Together

In real projects, you often combine them:

```python
from abc import ABC, abstractmethod
from typing import Protocol


# Protocol for external/loose contracts
class Loggable(Protocol):
    def get_log_data(self) -> dict:
        ...


# ABC for internal framework with shared logic
class BaseService(ABC):
    """Internal services must extend this ABC."""

    def __init__(self, service_name: str):
        self.service_name = service_name

    @abstractmethod
    def health_check(self) -> bool:
        ...

    def get_log_data(self) -> dict:
        """Also satisfies the Loggable protocol!"""
        return {"service": self.service_name, "healthy": self.health_check()}


class UserService(BaseService):
    def __init__(self):
        super().__init__("user-service")

    def health_check(self) -> bool:
        return True


# A function that accepts any Loggable — not just BaseService subclasses
def log_status(component: Loggable) -> None:
    data = component.get_log_data()
    print(f"Status: {data}")


# Works with our ABC-based service
log_status(UserService())

# Also works with a completely unrelated class!
class ThirdPartyWidget:
    def get_log_data(self) -> dict:
        return {"widget": "active", "version": "2.1"}

log_status(ThirdPartyWidget())  # ✅ Satisfies Loggable Protocol
```

---

## Real-World Scenario: Payment Processing System

Let's build a realistic payment system that demonstrates when to use inheritance, composition, Protocols, and ABCs together.

### The Requirements

- Support multiple payment methods (credit card, PayPal, crypto)
- Validate payments before processing
- Log all transactions
- Support retry logic for failed payments
- Make it testable and extensible

### Architecture Using All Concepts

```python
from abc import ABC, abstractmethod
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────
# 1. DATA MODELS
# ─────────────────────────────────────────────

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class PaymentRequest:
    amount: float
    currency: str
    customer_id: str
    idempotency_key: str


@dataclass
class PaymentResult:
    status: PaymentStatus
    transaction_id: str | None = None
    error: str | None = None


# ─────────────────────────────────────────────
# 2. PROTOCOLS — for loose coupling / duck typing
# ─────────────────────────────────────────────

class Logger(Protocol):
    """Any object with a log() method works."""
    def log(self, level: str, message: str, **context) -> None:
        ...


class MetricsCollector(Protocol):
    """Any metrics backend — Prometheus, StatsD, DataDog..."""
    def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
        ...

    def histogram(self, metric: str, value: float) -> None:
        ...


class RetryPolicy(Protocol):
    """Pluggable retry behavior."""
    def should_retry(self, attempt: int, error: str) -> bool:
        ...

    def get_delay_seconds(self, attempt: int) -> float:
        ...


# ─────────────────────────────────────────────
# 3. ABC — for the core payment gateway contract
# ─────────────────────────────────────────────

class PaymentGateway(ABC):
    """
    ABC because:
    - We own all implementations
    - We want shared validation logic
    - We want fail-fast if someone forgets to implement a method
    - We need isinstance() checks for gateway routing
    """

    SUPPORTED_CURRENCIES: list[str] = ["USD", "EUR", "GBP"]

    @abstractmethod
    def charge(self, request: PaymentRequest) -> PaymentResult:
        """Process the payment. Must be implemented by each gateway."""
        ...

    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        """Refund a transaction. Must be implemented by each gateway."""
        ...

    @property
    @abstractmethod
    def gateway_name(self) -> str:
        """Identifier for this gateway."""
        ...

    # Shared implementation — all gateways get this for free
    def validate_request(self, request: PaymentRequest) -> str | None:
        """Returns error message if invalid, None if valid."""
        if request.amount <= 0:
            return "Amount must be positive"
        if request.currency not in self.SUPPORTED_CURRENCIES:
            return f"Unsupported currency: {request.currency}"
        return None


# ─────────────────────────────────────────────
# 4. CONCRETE GATEWAYS — Inheritance from ABC
# ─────────────────────────────────────────────

class StripeGateway(PaymentGateway):
    """Stripe implementation — inherits shared validation."""

    @property
    def gateway_name(self) -> str:
        return "stripe"

    def charge(self, request: PaymentRequest) -> PaymentResult:
        # In reality, this would call Stripe's API
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id=f"stripe_txn_{request.idempotency_key}"
        )

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id=f"refund_{transaction_id}"
        )


class PayPalGateway(PaymentGateway):
    """PayPal implementation."""

    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "AUD"]  # Override parent

    @property
    def gateway_name(self) -> str:
        return "paypal"

    def charge(self, request: PaymentRequest) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id=f"pp_txn_{request.idempotency_key}"
        )

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id=f"pp_refund_{transaction_id}"
        )


# ─────────────────────────────────────────────
# 5. PROTOCOL IMPLEMENTATIONS — no inheritance needed
# ─────────────────────────────────────────────

class ConsoleLogger:
    """Satisfies Logger Protocol without inheriting from anything."""

    def log(self, level: str, message: str, **context) -> None:
        timestamp = datetime.now().isoformat()
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        print(f"[{timestamp}] {level.upper()}: {message} {ctx}")


class PrometheusMetrics:
    """Satisfies MetricsCollector Protocol."""

    def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
        print(f"COUNTER {metric} +1 {tags or {}}")

    def histogram(self, metric: str, value: float) -> None:
        print(f"HISTOGRAM {metric} = {value}")


class ExponentialBackoff:
    """Satisfies RetryPolicy Protocol."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def should_retry(self, attempt: int, error: str) -> bool:
        return attempt < self.max_retries

    def get_delay_seconds(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)


# ─────────────────────────────────────────────
# 6. THE SERVICE — uses COMPOSITION to wire everything together
# ─────────────────────────────────────────────

class PaymentService:
    """
    COMPOSITION in action:
    - Has a gateway (ABC — enforced contract)
    - Has a logger (Protocol — any logger works)
    - Has metrics (Protocol — any metrics backend)
    - Has retry policy (Protocol — pluggable strategy)

    This class doesn't inherit from anything!
    It composes behaviors from injected dependencies.
    """

    def __init__(
        self,
        gateway: PaymentGateway,
        logger: Logger,
        metrics: MetricsCollector,
        retry_policy: RetryPolicy,
    ):
        self.gateway = gateway
        self.logger = logger
        self.metrics = metrics
        self.retry_policy = retry_policy

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        # 1. Validate (using shared ABC method)
        error = self.gateway.validate_request(request)
        if error:
            self.logger.log("error", "Validation failed", error=error)
            self.metrics.increment("payment.validation_failed")
            return PaymentResult(status=PaymentStatus.FAILED, error=error)

        # 2. Attempt payment with retry
        import time
        attempt = 0

        while True:
            self.logger.log(
                "info",
                f"Processing payment attempt {attempt + 1}",
                gateway=self.gateway.gateway_name,
                amount=str(request.amount),
            )

            result = self.gateway.charge(request)

            if result.status == PaymentStatus.SUCCESS:
                self.metrics.increment(
                    "payment.success",
                    tags={"gateway": self.gateway.gateway_name}
                )
                self.logger.log("info", "Payment successful", txn=result.transaction_id)
                return result

            # Payment failed — should we retry?
            if not self.retry_policy.should_retry(attempt, result.error or "unknown"):
                self.metrics.increment("payment.failed")
                self.logger.log("error", "Payment failed permanently", error=result.error)
                return result

            delay = self.retry_policy.get_delay_seconds(attempt)
            self.logger.log("warn", f"Retrying in {delay}s", attempt=str(attempt))
            time.sleep(delay)
            attempt += 1


# ─────────────────────────────────────────────
# 7. WIRING IT ALL TOGETHER
# ─────────────────────────────────────────────

def main():
    # Compose the service with concrete implementations
    service = PaymentService(
        gateway=StripeGateway(),
        logger=ConsoleLogger(),
        metrics=PrometheusMetrics(),
        retry_policy=ExponentialBackoff(max_retries=3),
    )

    # Process a payment
    request = PaymentRequest(
        amount=99.99,
        currency="USD",
        customer_id="cust_123",
        idempotency_key="key_abc",
    )

    result = service.process_payment(request)
    print(f"\nFinal result: {result}")


# ─────────────────────────────────────────────
# 8. TESTING — composition makes this trivial
# ─────────────────────────────────────────────

class FakeLogger:
    """Test double — satisfies Logger Protocol."""
    def __init__(self):
        self.messages: list[str] = []

    def log(self, level: str, message: str, **context) -> None:
        self.messages.append(f"{level}: {message}")


class FakeMetrics:
    """Test double — satisfies MetricsCollector Protocol."""
    def __init__(self):
        self.counters: dict[str, int] = {}

    def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
        self.counters[metric] = self.counters.get(metric, 0) + 1

    def histogram(self, metric: str, value: float) -> None:
        pass


class NoRetry:
    """Test double — satisfies RetryPolicy Protocol."""
    def should_retry(self, attempt: int, error: str) -> bool:
        return False

    def get_delay_seconds(self, attempt: int) -> float:
        return 0


def test_successful_payment():
    """Look how easy testing is with composition + protocols!"""
    logger = FakeLogger()
    metrics = FakeMetrics()

    service = PaymentService(
        gateway=StripeGateway(),
        logger=logger,
        metrics=metrics,
        retry_policy=NoRetry(),
    )

    result = service.process_payment(PaymentRequest(
        amount=50.0,
        currency="USD",
        customer_id="test_customer",
        idempotency_key="test_key",
    ))

    assert result.status == PaymentStatus.SUCCESS
    assert "payment.success" in metrics.counters
    assert any("successful" in msg for msg in logger.messages)
```

### Why This Architecture Works

```
┌─────────────────────────────────────────────────────────────┐
│                     PaymentService                            │
│                   (uses COMPOSITION)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌────────────┐  ┌───────────────────┐   │
│  │ PaymentGateway│  │   Logger   │  │ MetricsCollector  │   │
│  │    (ABC)      │  │ (Protocol) │  │    (Protocol)     │   │
│  └──────┬───────┘  └─────┬──────┘  └────────┬──────────┘   │
│         │                 │                   │              │
│  ┌──────┴───────┐  ┌─────┴──────┐  ┌────────┴──────────┐   │
│  │StripeGateway │  │ConsoleLogger│  │PrometheusMetrics  │   │
│  │PayPalGateway │  │ FileLogger  │  │  DataDogMetrics   │   │
│  │CryptoGateway │  │ TestLogger  │  │   TestMetrics     │   │
│  └──────────────┘  └────────────┘  └───────────────────┘   │
│                                                              │
│  ┌──────────────────┐                                       │
│  │  RetryPolicy      │                                       │
│  │   (Protocol)      │                                       │
│  ├──────────────────┤                                       │
│  │ExponentialBackoff │                                       │
│  │ LinearBackoff     │                                       │
│  │   NoRetry         │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘

ABC used for: PaymentGateway (we own it, need shared validation, want fail-fast)
Protocol used for: Logger, Metrics, Retry (loose coupling, easy testing, swappable)
Composition used for: PaymentService wires all pieces together
```

---

## Decision Framework

### Quick Reference: What to Reach For

| Situation | Use |
|-----------|-----|
| Building a plugin system / framework extension | ABC |
| Need shared base implementation | ABC |
| Want fail-fast on missing methods | ABC |
| Working with third-party classes you can't modify | Protocol |
| Type-hinting callback functions / strategies | Protocol |
| Maximum decoupling and testability | Protocol + Composition |
| True "is-a" taxonomy (Animal → Dog) | Inheritance |
| Object needs multiple capabilities | Composition |
| Wiring dependencies together | Composition + DI |

### Rules of Thumb

1. **Start with composition** — it's almost always the right default
2. **Use Protocols** for type-hinting composed dependencies
3. **Use ABCs** when you own the hierarchy AND need shared implementation
4. **Use inheritance** only for true "is-a" relationships with shallow hierarchies
5. **Prefer Protocol over ABC** when you don't need shared implementation
6. **Combine them** — real systems use all four concepts together

---

## Common Pitfalls

### 1. Inheriting for Code Reuse (Instead of "is-a")

```python
# ❌ BAD: Inheriting just to reuse methods
class JSONMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)

class User(JSONMixin):  # A User is NOT a JSONMixin
    def __init__(self, name: str):
        self.name = name

# ✅ BETTER: Composition or standalone function
import json

def to_json(obj) -> str:
    return json.dumps(obj.__dict__)

class User:
    def __init__(self, name: str):
        self.name = name

print(to_json(User("Alice")))
```

### 2. God Base Classes

```python
# ❌ BAD: Base class does everything
class BaseService:
    def log(self): ...
    def cache(self): ...
    def validate(self): ...
    def send_email(self): ...
    def connect_db(self): ...

# ✅ BETTER: Compose specific capabilities
class UserService:
    def __init__(self, logger, cache, validator, emailer, db):
        self.logger = logger
        self.cache = cache
        # ... each does ONE thing
```

### 3. Using @runtime_checkable Protocol as a Substitute for ABC

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Processable(Protocol):
    def process(self) -> None: ...

class Broken:
    def process(self, data: str) -> None:  # Different signature!
        ...

# ⚠️ isinstance() only checks method NAME exists, not signature
print(isinstance(Broken(), Processable))  # True! (misleading)

# If you need strict enforcement, use ABC instead.
```

### 4. Over-Engineering with Abstractions

```python
# ❌ YAGNI: Don't create Protocol/ABC for a single implementation
class UserRepositoryProtocol(Protocol):
    def get_user(self, id: int) -> dict: ...

class UserRepository:  # Only ever one implementation
    def get_user(self, id: int) -> dict: ...

# ✅ Just use the class directly until you actually need a second implementation
```

---

## Summary

```
┌────────────────────────────────────────────────────────────┐
│                    MENTAL MODEL                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  INHERITANCE: "I am a kind of X"                          │
│  → Use for true taxonomies with shared behavior           │
│                                                            │
│  COMPOSITION: "I use X to do my job"                      │
│  → Default choice. Flexible, testable, maintainable.      │
│                                                            │
│  ABC: "You MUST implement these methods (I'll check)"     │
│  → Enforced contracts with optional shared logic          │
│                                                            │
│  PROTOCOL: "I don't care what you are, just do this"      │
│  → Duck typing with type safety. Maximum flexibility.      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

> **The 80/20 rule in practice:**
> - 80% of your design should use **composition + protocols**
> - 20% might genuinely need **inheritance + ABCs**
> - When in doubt, compose.


---

## FAQ

### 1. Protocol Method Bodies — `...` vs `pass` vs Real Implementation

### Short Answer

Use `...` (Ellipsis). It's the convention. The body is **never executed** by conforming classes.

### Detailed Explanation

```python
from typing import Protocol


# ✅ CONVENTION: Use ... (Ellipsis)
class Logger(Protocol):
    def log(self, level: str, message: str, **context) -> None:
        ...


# ✅ ALSO VALID: Use pass
class Logger(Protocol):
    def log(self, level: str, message: str, **context) -> None:
        pass


# ✅ ALSO VALID: Docstring + Ellipsis
class Logger(Protocol):
    def log(self, level: str, message: str, **context) -> None:
        """Log a message at the given level."""
        ...


# ✅ VALID BUT UNUSUAL: Actual implementation
class Logger(Protocol):
    def log(self, level: str, message: str, **context) -> None:
        print(f"[{level}] {message}")  # This exists but is NEVER called
```

### Why the Body Doesn't Matter

A Protocol defines a **structural contract** — it tells the type checker "any object with methods matching these signatures is valid." The body is purely decorative. Conforming classes **never inherit** from the Protocol, so they never call `super().log()`.

```python
class ConsoleLogger:
    """This does NOT inherit from Logger Protocol."""
    def log(self, level: str, message: str, **context) -> None:
        # This is the ONLY implementation that runs
        print(f"[{level}] {message}")


def notify(logger: Logger) -> None:
    logger.log("info", "hello")  # Calls ConsoleLogger.log, NOT Logger.log
```

### Comparison with ABC

| Aspect | Protocol | ABC |
|--------|----------|-----|
| Body of abstract method | Ignored (use `...`) | Also ignored when `@abstractmethod` |
| Body of concrete method | Ignored (no inheritance) | **Inherited and executed** by subclasses |
| Convention | `...` | `pass` or `raise NotImplementedError` |

```python
from abc import ABC, abstractmethod

class NotificationSender(ABC):
    @abstractmethod
    def send(self, to: str, msg: str) -> bool:
        ...  # or pass — never runs, subclass MUST override

    def validate(self, to: str) -> bool:
        # THIS runs! Subclasses inherit it via super()
        return "@" in to


class EmailSender(NotificationSender):
    def send(self, to: str, msg: str) -> bool:
        if self.validate(to):  # Calls parent's concrete method
            print(f"Sending to {to}")
            return True
        return False
```

### The Rule

| Writing a... | Method has `@abstractmethod`? | What to put in body |
|---|---|---|
| Protocol | N/A (never use @abstractmethod) | `...` — it's a signature declaration |
| ABC | Yes | `...` or `pass` — it won't run |
| ABC | No (concrete method) | **Real implementation** — subclasses inherit this |

**TL;DR:** In Protocols, always use `...`. The body is a type-checker hint, not executable code.

---

### 2. Can a class satisfy BOTH a Protocol AND inherit from an ABC at the same time?

**Yes, absolutely.** This is common in real projects.

```python
from abc import ABC, abstractmethod
from typing import Protocol


class Auditable(Protocol):
    """Protocol — any class with these methods satisfies it."""
    def get_audit_trail(self) -> list[str]:
        ...


class BaseGateway(ABC):
    """ABC — enforced contract with shared logic."""
    @abstractmethod
    def process(self) -> None:
        ...

    def log_action(self, action: str) -> None:
        print(f"[{self.__class__.__name__}] {action}")


class StripeGateway(BaseGateway):
    """Inherits from ABC AND satisfies Auditable Protocol."""

    def __init__(self):
        self._trail: list[str] = []

    def process(self) -> None:
        self._trail.append("processed")
        self.log_action("Payment processed")

    def get_audit_trail(self) -> list[str]:
        return self._trail


# This function accepts ANY Auditable — doesn't care about BaseGateway
def audit(component: Auditable) -> None:
    print(component.get_audit_trail())

gateway = StripeGateway()
gateway.process()
audit(gateway)  # ✅ Works — StripeGateway has get_audit_trail()
```

**Key insight:** The Protocol doesn't know or care that `StripeGateway` inherits from an ABC. It only checks structure. This lets you write functions that accept objects from completely different hierarchies as long as they have the right methods.

---

### 3. If I have a Protocol and later realize I need shared implementation, can I migrate to an ABC? What breaks?

**Yes, but it's a breaking change** for all existing conforming classes.

```python
# BEFORE: Protocol — classes just need matching methods
from typing import Protocol

class Storage(Protocol):
    def save(self, key: str, data: bytes) -> None:
        ...
    def load(self, key: str) -> bytes:
        ...

class FileStorage:  # No inheritance needed
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class S3Storage:  # No inheritance needed
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...
```

```python
# AFTER: Migrating to ABC — ALL classes must now inherit
from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def load(self, key: str) -> bytes: ...

    # The shared implementation you needed:
    def exists(self, key: str) -> bool:
        try:
            self.load(key)
            return True
        except FileNotFoundError:
            return False

class FileStorage(Storage):  # ← Must add inheritance
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class S3Storage(Storage):  # ← Must add inheritance
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...
```

**What breaks:**
- Every conforming class must add `(Storage)` to their class definition
- Third-party classes that used to "just work" now fail type checks
- `isinstance()` checks change behavior

**Better alternative — keep the Protocol, add a mixin:**

```python
from typing import Protocol

class Storage(Protocol):
    """Keep the Protocol for loose coupling."""
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...


class StorageMixin:
    """Optional mixin — classes can use it if they want shared logic."""
    def exists(self, key: str) -> bool:
        try:
            self.load(key)  # type: ignore
            return True
        except FileNotFoundError:
            return False


class FileStorage(StorageMixin):
    """Gets shared logic from mixin, still satisfies Protocol."""
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...


class S3Storage:
    """Can skip the mixin — still satisfies Protocol."""
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool:
        # Own implementation
        return True
```

---

### 4. What happens if my class has a method with the same name as the Protocol but a different signature?

**The type checker (mypy) will catch it. But `@runtime_checkable` isinstance() will NOT.**

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Sender(Protocol):
    def send(self, message: str) -> bool:
        ...


class BrokenSender:
    def send(self, message: str, retries: int) -> bool:  # Extra param!
        return True


class WrongReturn:
    def send(self, message: str) -> str:  # Wrong return type!
        return "sent"


# Runtime: isinstance() only checks method NAME exists
print(isinstance(BrokenSender(), Sender))  # True! ⚠️ MISLEADING
print(isinstance(WrongReturn(), Sender))   # True! ⚠️ MISLEADING

# But mypy would flag this at type-check time:
def notify(sender: Sender) -> None:
    sender.send("hello")

notify(BrokenSender())  # mypy error: Argument 1 has incompatible type
notify(WrongReturn())   # mypy error: Argument 1 has incompatible type
```

**Lesson:** `@runtime_checkable` is a shallow check (method names only). For signature enforcement, rely on mypy/pyright. For bulletproof runtime enforcement, use an ABC.

---

### 5. When should I use a Protocol with a single method vs just a `Callable` type hint?

**Use `Callable` for simple function signatures. Use Protocol when you need named methods, state, or multiple methods.**

```python
from typing import Protocol, Callable


# ─── Option A: Callable (simpler) ───
def retry_with_callback(
    action: Callable[[], bool],      # Takes nothing, returns bool
    should_retry: Callable[[int, str], bool],  # Takes attempt + error, returns bool
) -> bool:
    ...


# ─── Option B: Protocol (more expressive) ───
class RetryPolicy(Protocol):
    def should_retry(self, attempt: int, error: str) -> bool:
        ...

    def get_delay(self, attempt: int) -> float:
        ...

def retry_with_policy(action: Callable[[], bool], policy: RetryPolicy) -> bool:
    ...
```

**Use `Callable` when:**
- It's a single function with a simple signature
- You don't need named methods (just "something callable")
- It's a one-off callback

**Use Protocol when:**
- You need **multiple related methods** (retry needs both should_retry + get_delay)
- You want **self-documenting method names** (more readable than `Callable[[int, str], bool]`)
- The implementation might have **state** (instance attributes)
- Complex signatures that are unreadable as `Callable[...]`

```python
# ❌ Unreadable Callable
handler: Callable[[str, dict[str, Any], list[tuple[str, int]]], Awaitable[Response]]

# ✅ Self-documenting Protocol
class RequestHandler(Protocol):
    def handle(
        self, path: str, headers: dict[str, Any], params: list[tuple[str, int]]
    ) -> Awaitable[Response]:
        ...
```

---

### 6. Can I use `@abstractmethod` inside a Protocol? What happens?

**No. Never use `@abstractmethod` in a Protocol.** They serve fundamentally different mechanisms.

```python
from abc import abstractmethod
from typing import Protocol


# ❌ DON'T DO THIS
class BadProtocol(Protocol):
    @abstractmethod
    def process(self) -> None:
        ...

# This technically "works" in Python (no syntax error), but it's semantically wrong:
# - Protocol = structural subtyping (match the shape)
# - @abstractmethod = nominal subtyping (must inherit)
# - Mixing them contradicts the purpose of Protocol
```

**Why it's wrong:**
- `@abstractmethod` enforces that **subclasses** implement the method
- But Protocol conformers **don't subclass** the Protocol
- So `@abstractmethod` has no enforcement effect on Protocol users
- It only confuses readers and type checkers

**What to do instead:**

```python
# ✅ Protocol — just declare the signature
class Processor(Protocol):
    def process(self) -> None:
        ...

# ✅ ABC — use @abstractmethod for enforcement
from abc import ABC, abstractmethod

class Processor(ABC):
    @abstractmethod
    def process(self) -> None:
        ...
```

---

### 7. In the payment system example, why is `PaymentGateway` an ABC but `Logger` is a Protocol? Could they be swapped?

**They could technically be swapped, but it would be a worse design.** Here's why each was chosen:

| | PaymentGateway (ABC) | Logger (Protocol) |
|---|---|---|
| **Shared logic?** | Yes — `validate_request()` | No — each logger is independent |
| **We own all implementations?** | Yes — Stripe, PayPal, Crypto | No — could use structlog, loguru, custom |
| **Need fail-fast?** | Yes — forgetting `charge()` is critical | No — a missing `log()` is caught by mypy |
| **Runtime isinstance()?** | Yes — for gateway routing | No — we just call `.log()` |
| **Number of implementations?** | Few (we control) | Many (third-party loggers exist) |

**If you swapped them:**

```python
# ❌ Logger as ABC — forces all loggers to inherit from it
class Logger(ABC):
    @abstractmethod
    def log(self, level: str, message: str, **context) -> None: ...

# Now structlog, loguru, and any third-party logger WON'T work
# unless you write adapters for each one. Unnecessary coupling!


# ❌ PaymentGateway as Protocol — loses shared validation
class PaymentGateway(Protocol):
    def charge(self, request: PaymentRequest) -> PaymentResult: ...
    def refund(self, transaction_id: str, amount: float) -> PaymentResult: ...
    def validate_request(self, request: PaymentRequest) -> str | None: ...

# Now every gateway MUST re-implement validate_request()
# even though it's identical for all gateways. Code duplication!
```

**Decision rule:** ABC when you need shared code + enforcement. Protocol when you need flexibility + decoupling.

---

### 8. What's the difference between composition and aggregation? Does Python distinguish them?

**Python doesn't distinguish them syntactically**, but they represent different ownership semantics.

```python
# ─── COMPOSITION: Child dies with the parent ───
class Engine:
    """Created BY the car, lives and dies with it."""
    def __init__(self, hp: int):
        self.hp = hp

class Car:
    def __init__(self):
        self.engine = Engine(200)  # Car CREATES the engine
        # If Car is garbage collected, Engine goes too

    def __del__(self):
        # Engine is destroyed when Car is destroyed
        pass


# ─── AGGREGATION: Child exists independently ───
class Driver:
    """Exists independently of any car."""
    def __init__(self, name: str):
        self.name = name

class Car:
    def __init__(self, driver: Driver):
        self.driver = driver  # Car RECEIVES the driver
        # Driver continues to exist even if Car is deleted


# In practice:
driver = Driver("Alice")
car = Car(driver)
del car
print(driver.name)  # "Alice" — driver still exists!
```

| | Composition | Aggregation |
|---|---|---|
| Ownership | Parent **owns** child | Parent **uses** child |
| Lifecycle | Child dies with parent | Child outlives parent |
| Creation | Parent creates child internally | Child is passed in (DI) |
| UML notation | Filled diamond ◆ | Empty diamond ◇ |

**In Python, the practical distinction is:** Did you create it inside `__init__`, or did you receive it as a parameter?

Most of what we call "composition" in Python design discussions (dependency injection, protocol-based design) is technically **aggregation**. But the community uses "composition" loosely to mean "has-a relationship with delegation" regardless of ownership.

---

### 9. Can a Protocol inherit from another Protocol? How does that work?

**Yes. Protocol inheritance creates a more specific structural contract.**

```python
from typing import Protocol


class Readable(Protocol):
    def read(self, size: int = -1) -> bytes:
        ...


class Writable(Protocol):
    def write(self, data: bytes) -> int:
        ...


class ReadWritable(Readable, Writable, Protocol):
    """Must have BOTH read() AND write() to satisfy this."""
    ...


class Closeable(Protocol):
    def close(self) -> None:
        ...


class Stream(ReadWritable, Closeable, Protocol):
    """Must have read(), write(), AND close()."""
    ...


# This class satisfies Stream without inheriting from anything
class FileStream:
    def read(self, size: int = -1) -> bytes:
        return b"data"

    def write(self, data: bytes) -> int:
        return len(data)

    def close(self) -> None:
        pass


def process(stream: Stream) -> None:
    data = stream.read()
    stream.write(b"processed")
    stream.close()

process(FileStream())  # ✅ Works — has all required methods
```

**Important:** When inheriting Protocols, you MUST include `Protocol` in the bases of the child Protocol class. Otherwise it becomes a regular class.

```python
# ❌ WRONG: Missing Protocol — this is a regular abstract class now
class ReadWritable(Readable, Writable):
    ...

# ✅ CORRECT: Include Protocol
class ReadWritable(Readable, Writable, Protocol):
    ...
```

---

### 10. If composition is "almost always" better, when is inheritance genuinely the RIGHT choice?

**Inheritance is the right choice when ALL of these are true:**

1. The relationship is truly "is-a" (Liskov Substitution holds)
2. You need polymorphism (substitute child for parent everywhere)
3. The hierarchy is shallow (2 levels max)
4. The parent is stable (won't change frequently)
5. Shared implementation belongs in the parent

**Genuine good examples:**

```python
# ✅ Framework extension points (Django, Flask)
from django.views import View

class UserListView(View):
    """Django EXPECTS you to inherit. The framework uses isinstance() checks,
    calls super() methods, and relies on the class hierarchy."""
    def get(self, request):
        return HttpResponse("users")


# ✅ Exception hierarchies
class PaymentError(Exception):
    """All payment errors IS-A Exception."""
    pass

class InsufficientFundsError(PaymentError):
    """IS-A PaymentError. Caught by `except PaymentError`."""
    pass

class CardDeclinedError(PaymentError):
    pass

# This catch block works because of inheritance:
try:
    process_payment()
except PaymentError as e:  # Catches ALL payment errors
    handle_failure(e)


# ✅ Data model hierarchies (when shared state matters)
@dataclass
class Shape:
    color: str
    x: float
    y: float

    def move(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy

@dataclass
class Circle(Shape):
    radius: float

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

@dataclass
class Rectangle(Shape):
    width: float
    height: float

    def area(self) -> float:
        return self.width * self.height

# All shapes share position + move() — inheritance is natural here
```

**Red flags that inheritance is WRONG:**

- You're inheriting from a concrete class (not ABC/base)
- The hierarchy is 3+ levels deep
- You're overriding most parent methods
- Child classes don't pass the "is-a" test
- You find yourself needing multiple inheritance to combine features

---

### 11. How do Protocols interact with dataclasses and NamedTuples?

**Dataclasses and NamedTuples can satisfy Protocols — they're just regular classes with generated methods.**

```python
from typing import Protocol
from dataclasses import dataclass
from typing import NamedTuple


class HasCoordinates(Protocol):
    x: float
    y: float


class Movable(Protocol):
    x: float
    y: float

    def distance_to(self, other: "Movable") -> float:
        ...


# ✅ Dataclass satisfies Protocol
@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: "Movable") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


# ✅ NamedTuple satisfies HasCoordinates (has x and y attributes)
class Coordinate(NamedTuple):
    x: float
    y: float


def print_position(obj: HasCoordinates) -> None:
    print(f"Position: ({obj.x}, {obj.y})")


print_position(Point(1.0, 2.0))       # ✅ Works
print_position(Coordinate(3.0, 4.0))  # ✅ Works


# Even a plain class with x and y works:
class Enemy:
    def __init__(self):
        self.x = 10.0
        self.y = 20.0

print_position(Enemy())  # ✅ Works — has x and y attributes
```

**Caveat with NamedTuples:** They're immutable, so they won't satisfy Protocols that expect mutable attributes or setter methods.

---

### 12. What's wrong with this code? (Spot the design smell)

```python
class Animal:
    def speak(self) -> str:
        raise NotImplementedError

    def swim(self) -> str:
        raise NotImplementedError

    def fly(self) -> str:
        raise NotImplementedError


class Dog(Animal):
    def speak(self) -> str:
        return "Woof"

    def swim(self) -> str:
        return "Dog paddle!"

    def fly(self) -> str:
        raise NotImplementedError  # Dogs can't fly!


class Eagle(Animal):
    def speak(self) -> str:
        return "Screech"

    def swim(self) -> str:
        raise NotImplementedError  # Eagles don't swim!

    def fly(self) -> str:
        return "Soaring!"
```

**Answer: Interface Segregation Principle violation + bad use of inheritance.**

Problems:
1. `Animal` forces ALL subclasses to deal with methods they don't support
2. `Dog` must handle `fly()` even though it can't fly
3. `Eagle` must handle `swim()` even though it can't swim
4. `raise NotImplementedError` at runtime = ticking time bomb

**Fix with Protocols (composition of capabilities):**

```python
from typing import Protocol


class CanSpeak(Protocol):
    def speak(self) -> str: ...

class CanSwim(Protocol):
    def swim(self) -> str: ...

class CanFly(Protocol):
    def fly(self) -> str: ...


class Dog:
    """Only implements what it can actually do."""
    def speak(self) -> str:
        return "Woof"

    def swim(self) -> str:
        return "Dog paddle!"


class Eagle:
    def speak(self) -> str:
        return "Screech"

    def fly(self) -> str:
        return "Soaring!"


# Functions request only what they need:
def make_noise(animal: CanSpeak) -> None:
    print(animal.speak())

def water_race(swimmer: CanSwim) -> None:
    print(swimmer.swim())

def air_show(flyer: CanFly) -> None:
    print(flyer.fly())


make_noise(Dog())    # ✅
make_noise(Eagle())  # ✅
water_race(Dog())    # ✅
air_show(Eagle())    # ✅
# water_race(Eagle())  # ❌ mypy error — Eagle doesn't satisfy CanSwim
# air_show(Dog())      # ❌ mypy error — Dog doesn't satisfy CanFly
```

**The lesson:** Don't put all capabilities into one base class. Use small, focused Protocols so classes only need to implement what they actually support. Errors are caught by the type checker at development time, not at runtime with `NotImplementedError`.

---

### 13. My team lead says "always use dependency injection." Is DI just composition by another name?

**DI is a specific technique for achieving composition.** They're related but not identical.

```python
# ─── Composition WITHOUT DI ───
class PaymentService:
    def __init__(self):
        self.gateway = StripeGateway()  # Hardcoded! Composition, but not DI.
        self.logger = ConsoleLogger()   # Can't swap in tests.


# ─── Composition WITH DI ───
class PaymentService:
    def __init__(self, gateway: PaymentGateway, logger: Logger):
        self.gateway = gateway  # Injected! Caller decides which one.
        self.logger = logger    # Testable, swappable.
```

| Concept | What it is |
|---------|-----------|
| **Composition** | Building objects from other objects ("has-a") |
| **Dependency Injection** | Passing dependencies in from outside (not creating them internally) |
| **Inversion of Control** | The broader principle — don't call us, we'll call you |

**You can have composition without DI** (create dependencies internally), but it's harder to test. DI is the standard way to make composition testable and flexible.

**The relationship:**
```
Inversion of Control (principle)
  └── Dependency Injection (technique)
        └── Composition (relationship)
```

---

### 14. When I write a fake/test double for testing, should it inherit from the Protocol or just match the methods?

**Just match the methods. That's the entire point of Protocols.**

```python
from typing import Protocol


class EmailClient(Protocol):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        ...


# ✅ CORRECT: Fake just matches the shape
class FakeEmailClient:
    def __init__(self):
        self.sent_emails: list[dict] = []

    def send_email(self, to: str, subject: str, body: str) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True


# ❌ UNNECESSARY: Inheriting from the Protocol
class FakeEmailClient(EmailClient):  # Don't do this!
    ...
```

**But for ABCs, you MUST inherit:**

```python
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: float) -> bool: ...

    def validate(self, amount: float) -> bool:
        return amount > 0


# ✅ REQUIRED: Must inherit from ABC
class FakeGateway(PaymentGateway):
    def charge(self, amount: float) -> bool:
        return True
    # Gets validate() for free from parent

# ❌ WON'T WORK: isinstance() check fails
class FakeGateway:
    def charge(self, amount: float) -> bool:
        return True

isinstance(FakeGateway(), PaymentGateway)  # False!
```

| Test double for... | Inherit? | Why |
|---|---|---|
| Protocol | No | Structural typing — just match methods |
| ABC | Yes | Nominal typing — must be in the class tree |
| Concrete class | Depends | If code uses isinstance(), then yes |


