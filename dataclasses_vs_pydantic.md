# Python Dataclasses vs Pydantic

A comprehensive guide to understanding dataclasses and Pydantic — what they are, how they differ, and when to use each.

---

## Table of Contents

1. [The Problem They Solve](#the-problem-they-solve)
2. [What Are Dataclasses?](#what-are-dataclasses)
3. [What Is Pydantic?](#what-is-pydantic)
4. [Side-by-Side Comparison](#side-by-side-comparison)
5. [Getters and Setters](#getters-and-setters)
6. [Dataclasses vs Pydantic vs Standard Classes](#dataclasses-vs-pydantic-vs-standard-classes)
7. [Inheritance](#inheritance)
8. [Composition](#composition)
9. [ABCs with Dataclasses and Pydantic](#abcs-with-dataclasses-and-pydantic)
10. [Protocols with Dataclasses and Pydantic](#protocols-with-dataclasses-and-pydantic)
11. [Real-World Scenario: REST API Configuration System](#real-world-scenario-rest-api-configuration-system)
12. [Decision Framework](#decision-framework)
13. [FAQ](#faq)

---

## The Problem They Solve

Without dataclasses or Pydantic, creating a simple data-holding class requires a lot of boilerplate:

```python
# ❌ Plain Python class — tons of repetitive code
class User:
    def __init__(self, name: str, email: str, age: int, active: bool = True):
        self.name = name
        self.email = email
        self.age = age
        self.active = active

    def __repr__(self) -> str:
        return f"User(name={self.name!r}, email={self.email!r}, age={self.age}, active={self.active})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return (self.name, self.email, self.age, self.active) == (
            other.name, other.email, other.age, other.active
        )

    def __hash__(self) -> int:
        return hash((self.name, self.email, self.age, self.active))
```

**Problems with this approach:**
- Repeat every field name 3+ times (`__init__`, `self.x = x`, `__repr__`, `__eq__`)
- Easy to forget `__repr__`, `__eq__`, `__hash__`
- No validation — `User(name=123, email=None, age="old")` silently works
- No immutability support without extra work
- Boring, error-prone boilerplate

Both dataclasses and Pydantic eliminate this boilerplate, but they do it differently and for different purposes.

---

## What Are Dataclasses?

Dataclasses (Python 3.7+, `from dataclasses import dataclass`) are a **stdlib decorator** that auto-generates boilerplate methods for classes that primarily hold data.

### What They Generate

```python
from dataclasses import dataclass, field


@dataclass
class User:
    name: str
    email: str
    age: int
    active: bool = True
    tags: list[str] = field(default_factory=list)
```

This single definition auto-generates:
- `__init__(self, name, email, age, active=True, tags=[])`
- `__repr__(self)` → `User(name='Alice', email='a@b.com', age=30, active=True, tags=[])`
- `__eq__(self, other)` → compares all fields
- Optionally: `__hash__`, `__lt__`, `__le__`, `__gt__`, `__ge__` (with `order=True`)

### Key Features

```python
from dataclasses import dataclass, field, asdict, astuple


# Frozen (immutable) dataclass
@dataclass(frozen=True)
class Point:
    x: float
    y: float


# Post-init processing
@dataclass
class Rectangle:
    width: float
    height: float
    area: float = field(init=False)  # Not in __init__, computed automatically

    def __post_init__(self):
        self.area = self.width * self.height


# Conversion utilities
@dataclass
class Config:
    host: str
    port: int
    debug: bool = False

config = Config(host="localhost", port=8080)
print(asdict(config))   # {'host': 'localhost', 'port': 8080, 'debug': False}
print(astuple(config))  # ('localhost', 8080, False)
```

### What Dataclasses DON'T Do

- ❌ **No validation** — `User(name=123, age="not a number")` works fine
- ❌ **No type coercion** — passing `"42"` to an `int` field stays as `"42"`
- ❌ **No serialization** (no `.json()`, no `.model_dump()`)
- ❌ **No schema generation** (no JSON Schema, no OpenAPI)

Dataclasses trust that you're passing the right types. They're just **boilerplate reduction**, not a validation framework.

---

## What Is Pydantic?

Pydantic (v2, `from pydantic import BaseModel`) is a **third-party library** for data validation, serialization, and settings management. It validates data at runtime and coerces types automatically.

### Basic Usage

```python
from pydantic import BaseModel, Field, field_validator, EmailStr


class User(BaseModel):
    name: str
    email: EmailStr  # Validates email format!
    age: int
    active: bool = True
    tags: list[str] = Field(default_factory=list)
```

### What Pydantic Does

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    name: str
    age: int
    score: float

# ✅ Type coercion — "25" becomes int 25
user = User(name="Alice", age="25", score="99.5")
print(user.age)    # 25 (int, not str)
print(user.score)  # 99.5 (float, not str)

# ✅ Validation — catches invalid data
try:
    User(name="Alice", age="not a number", score=99.5)
except ValidationError as e:
    print(e)
    # 1 validation error for User
    # age
    #   Input should be a valid integer, unable to parse string as an integer

# ✅ Serialization
user = User(name="Bob", age=30, score=85.5)
print(user.model_dump())       # {'name': 'Bob', 'age': 30, 'score': 85.5}
print(user.model_dump_json())  # '{"name":"Bob","age":30,"score":85.5}'

# ✅ Deserialization
user2 = User.model_validate({"name": "Carol", "age": 28, "score": 92.0})
user3 = User.model_validate_json('{"name":"Dave","age":35,"score":88.0}')

# ✅ JSON Schema generation
print(User.model_json_schema())
# {'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}, ...}}
```

### Custom Validators

```python
from pydantic import BaseModel, field_validator, model_validator


class Payment(BaseModel):
    amount: float
    currency: str
    recipient: str

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def currency_must_be_valid(cls, v: str) -> str:
        valid = {"USD", "EUR", "GBP"}
        if v.upper() not in valid:
            raise ValueError(f"Currency must be one of {valid}")
        return v.upper()  # Normalize to uppercase

    @model_validator(mode="after")
    def check_recipient_not_empty(self) -> "Payment":
        if not self.recipient.strip():
            raise ValueError("Recipient cannot be empty")
        return self


# Usage
payment = Payment(amount=100, currency="usd", recipient="Alice")
print(payment.currency)  # "USD" — normalized by validator!

# Validation catches errors
try:
    Payment(amount=-50, currency="BTC", recipient="")
except Exception as e:
    print(e)  # Multiple validation errors
```

### Pydantic's Immutable Models

```python
from pydantic import BaseModel


class FrozenConfig(BaseModel):
    model_config = {"frozen": True}

    host: str
    port: int

config = FrozenConfig(host="localhost", port=8080)
# config.host = "other"  # ❌ ValidationError: Instance is frozen
```

---

## Side-by-Side Comparison

| Feature | Dataclass | Pydantic |
|---------|-----------|----------|
| Source | stdlib (Python 3.7+) | Third-party (`pip install pydantic`) |
| Purpose | Boilerplate reduction | Data validation + serialization |
| Type checking | None at runtime | Full validation + coercion |
| `"42"` → `int` field | Stays as `"42"` (no coercion) | Becomes `42` (coerced) |
| Invalid data | Silently accepted | Raises `ValidationError` |
| Serialization | `asdict()` (basic) | `.model_dump()`, `.model_dump_json()` |
| Deserialization | Manual | `.model_validate()`, `.model_validate_json()` |
| JSON Schema | ❌ | ✅ `.model_json_schema()` |
| Immutability | `frozen=True` | `model_config = {"frozen": True}` |
| Performance | Faster (no validation overhead) | Slower (validates every field) |
| Dependencies | None (stdlib) | Requires `pydantic` package |
| Custom validators | `__post_init__` (limited) | `@field_validator`, `@model_validator` |
| Nested models | Manual | Automatic recursive validation |
| Default factory | `field(default_factory=list)` | `Field(default_factory=list)` |
| Ordering | `@dataclass(order=True)` | Not built-in |
| Best for | Internal data structures | API boundaries, configs, external data |

### The Same Model in Both

```python
# ─── Dataclass version ───
from dataclasses import dataclass, field

@dataclass
class Product:
    name: str
    price: float
    tags: list[str] = field(default_factory=list)
    in_stock: bool = True

p = Product(name="Widget", price="19.99", tags=["sale"])  # price stays as str "19.99"!
print(type(p.price))  # <class 'str'> — no validation!


# ─── Pydantic version ───
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str
    price: float
    tags: list[str] = Field(default_factory=list)
    in_stock: bool = True

p = Product(name="Widget", price="19.99", tags=["sale"])  # price coerced to float
print(type(p.price))  # <class 'float'> — validated and coerced!
print(p.price)        # 19.99
```

---

## Getters and Setters

### In Standard Python (using `@property`)

```python
class User:
    def __init__(self, name: str, age: int):
        self._name = name
        self._age = age

    @property
    def name(self) -> str:
        """Getter — controls read access."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Setter — controls write access with validation."""
        if not value.strip():
            raise ValueError("Name cannot be empty")
        self._name = value.strip()

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        if value < 0 or value > 150:
            raise ValueError("Age must be between 0 and 150")
        self._age = value

    @property
    def is_adult(self) -> bool:
        """Computed property — no setter, read-only."""
        return self._age >= 18


user = User("Alice", 30)
print(user.name)       # Alice (getter)
user.name = "Bob"      # (setter with validation)
print(user.is_adult)   # True (computed)
# user.age = -5        # ValueError: Age must be between 0 and 150
```

### Getters and Setters in Dataclasses

Dataclasses work with `@property`, but it requires extra setup since fields are normally set directly.

```python
from dataclasses import dataclass, field


@dataclass
class User:
    _name: str = field(repr=False)  # Internal storage
    _age: int = field(repr=False)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Name cannot be empty")
        self._name = value.strip()

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        if value < 0:
            raise ValueError("Age must be non-negative")
        self._age = value

    @property
    def is_adult(self) -> bool:
        return self._age >= 18


# ⚠️ Problem: The __init__ uses _name and _age as parameter names
user = User(_name="Alice", _age=30)  # Ugly! Exposes internal names
```

**Better approach — use `__post_init__` for validation:**

```python
from dataclasses import dataclass


@dataclass
class User:
    name: str
    age: int

    def __post_init__(self):
        """Runs after __init__ — validate here."""
        if not self.name.strip():
            raise ValueError("Name cannot be empty")
        self.name = self.name.strip()
        if self.age < 0:
            raise ValueError("Age must be non-negative")

    @property
    def is_adult(self) -> bool:
        return self.age >= 18


user = User(name="Alice", age=30)
print(user.is_adult)  # True
# User(name="", age=30)  # ValueError: Name cannot be empty
```

**The cleanest dataclass approach — property with descriptor pattern:**

```python
from dataclasses import dataclass, field


@dataclass
class Temperature:
    """Dataclass with a true getter/setter using init=False + __post_init__."""
    celsius: float
    _fahrenheit: float = field(init=False, repr=False)

    def __post_init__(self):
        self._fahrenheit = self.celsius * 9 / 5 + 32

    @property
    def fahrenheit(self) -> float:
        """Computed property — always derived from celsius."""
        return self.celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        """Setting fahrenheit updates celsius."""
        self.celsius = (value - 32) * 5 / 9


temp = Temperature(celsius=100)
print(temp.fahrenheit)  # 212.0
temp.fahrenheit = 32
print(temp.celsius)     # 0.0
```

### Getters and Setters in Pydantic

Pydantic has a more elegant system — **computed fields** and **validators** replace the need for manual getters/setters.

```python
from pydantic import BaseModel, field_validator, computed_field


class User(BaseModel):
    name: str
    age: int

    # ─── "Setter" equivalent: validator that runs on assignment ───
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()  # Normalize (like a setter would)

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

    # ─── "Getter" equivalent: computed field ───
    @computed_field
    @property
    def is_adult(self) -> bool:
        return self.age >= 18


user = User(name="  Alice  ", age=30)
print(user.name)      # "Alice" (stripped by validator)
print(user.is_adult)  # True (computed field)
print(user.model_dump())
# {'name': 'Alice', 'age': 30, 'is_adult': True}  — computed field included!
```

**Pydantic with re-validation on assignment:**

```python
from pydantic import BaseModel, field_validator


class Temperature(BaseModel):
    model_config = {"validate_assignment": True}  # Re-validate on every set!

    celsius: float

    @field_validator("celsius")
    @classmethod
    def check_range(cls, v: float) -> float:
        if v < -273.15:
            raise ValueError("Below absolute zero!")
        return v

    @computed_field
    @property
    def fahrenheit(self) -> float:
        return self.celsius * 9 / 5 + 32


temp = Temperature(celsius=100)
print(temp.fahrenheit)  # 212.0
temp.celsius = 0        # Re-validates! ✅
print(temp.fahrenheit)  # 32.0
# temp.celsius = -300   # ❌ ValidationError: Below absolute zero!
```

### Getter/Setter Comparison Summary

| Aspect | Standard Class | Dataclass | Pydantic |
|--------|---------------|-----------|----------|
| Getter | `@property` | `@property` | `@computed_field` + `@property` |
| Setter | `@x.setter` | `@x.setter` (awkward) | `@field_validator` + `validate_assignment` |
| Validation in setter | Manual in setter body | `__post_init__` or setter | `@field_validator` (declarative) |
| Re-validate on change | Manual | Manual | `validate_assignment=True` |
| Computed values | `@property` (not in repr) | `@property` (not in repr) | `@computed_field` (in serialization!) |
| Boilerplate | High | Medium | Low |

---

## Dataclasses vs Pydantic vs Standard Classes

The same domain model implemented three ways:

```python
# ═══════════════════════════════════════════════
# STANDARD CLASS
# ═══════════════════════════════════════════════
class UserStandard:
    def __init__(self, name: str, email: str, age: int, roles: list[str] | None = None):
        # Validation
        if not name.strip():
            raise ValueError("Name required")
        if "@" not in email:
            raise ValueError("Invalid email")
        if age < 0:
            raise ValueError("Age must be positive")

        self.name = name.strip()
        self.email = email.lower()
        self.age = age
        self.roles = roles or []

    def __repr__(self) -> str:
        return f"User(name={self.name!r}, email={self.email!r}, age={self.age})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, UserStandard):
            return NotImplemented
        return (self.name, self.email, self.age) == (other.name, other.email, other.age)

    def __hash__(self) -> int:
        return hash((self.name, self.email, self.age))

    def to_dict(self) -> dict:
        return {"name": self.name, "email": self.email, "age": self.age, "roles": self.roles}

    @classmethod
    def from_dict(cls, data: dict) -> "UserStandard":
        return cls(**data)


# ═══════════════════════════════════════════════
# DATACLASS
# ═══════════════════════════════════════════════
from dataclasses import dataclass, field, asdict

@dataclass
class UserDataclass:
    name: str
    email: str
    age: int
    roles: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Name required")
        if "@" not in self.email:
            raise ValueError("Invalid email")
        if self.age < 0:
            raise ValueError("Age must be positive")
        self.name = self.name.strip()
        self.email = self.email.lower()

    # __repr__, __eq__ are FREE (auto-generated)
    # to_dict is easy:
    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════
# PYDANTIC
# ═══════════════════════════════════════════════
from pydantic import BaseModel, Field, field_validator, EmailStr

class UserPydantic(BaseModel):
    name: str
    email: EmailStr  # Built-in email validation!
    age: int = Field(ge=0)  # ge = greater than or equal
    roles: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name required")
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()

    # __repr__, __eq__, to_dict, from_dict, JSON Schema — ALL FREE
```

### Lines of Code Comparison

| | Standard | Dataclass | Pydantic |
|---|---|---|---|
| Core definition | ~30 lines | ~18 lines | ~16 lines |
| Validation | Manual in `__init__` | Manual in `__post_init__` | Declarative validators |
| `__repr__` | Write it yourself | Free | Free |
| `__eq__` / `__hash__` | Write it yourself | Free | Free |
| Serialization | Write it yourself | `asdict()` (basic) | `.model_dump()` / `.model_dump_json()` |
| Deserialization | Write `from_dict()` | Write it yourself | `.model_validate()` / `.model_validate_json()` |
| Type coercion | Write it yourself | Not available | Automatic |
| Nested validation | Write it yourself | Not available | Automatic (recursive) |

---

## Inheritance

### Dataclass Inheritance

Dataclasses support inheritance naturally. Child fields are appended after parent fields.

```python
from dataclasses import dataclass, field


@dataclass
class BaseEvent:
    event_id: str
    timestamp: str


@dataclass
class UserEvent(BaseEvent):
    user_id: str


@dataclass
class PurchaseEvent(UserEvent):
    product_id: str
    amount: float


# Fields are ordered: event_id, timestamp, user_id, product_id, amount
event = PurchaseEvent(
    event_id="evt_1",
    timestamp="2024-01-01",
    user_id="user_42",
    product_id="prod_99",
    amount=29.99,
)
print(event)
# PurchaseEvent(event_id='evt_1', timestamp='2024-01-01',
#               user_id='user_42', product_id='prod_99', amount=29.99)
```

**⚠️ Gotcha — default values and inheritance:**

```python
from dataclasses import dataclass

@dataclass
class Parent:
    name: str
    value: int = 10  # Has a default

@dataclass
class Child(Parent):
    # ❌ ERROR: non-default argument follows default argument
    # extra: str  # This would fail because parent has a default (value=10)

    # ✅ Must also have a default (or use a different pattern)
    extra: str = "default"


# Workaround: put required fields in parent, defaults in child
@dataclass
class Parent:
    name: str  # No default

@dataclass
class Child(Parent):
    extra: str            # No default — this works!
    value: int = 10       # Default — after non-defaults
```

**Overriding `__post_init__` with inheritance:**

```python
from dataclasses import dataclass


@dataclass
class BaseModel:
    name: str

    def __post_init__(self):
        self.name = self.name.strip()


@dataclass
class User(BaseModel):
    email: str

    def __post_init__(self):
        super().__post_init__()  # Call parent's post_init
        self.email = self.email.lower()


user = User(name="  Alice  ", email="ALICE@Example.COM")
print(user.name)   # "Alice"
print(user.email)  # "alice@example.com"
```

### Pydantic Inheritance

Pydantic models support inheritance with full validator inheritance.

```python
from pydantic import BaseModel, field_validator, Field
from datetime import datetime


class BaseEvent(BaseModel):
    event_id: str
    timestamp: datetime

    @field_validator("event_id")
    @classmethod
    def must_start_with_evt(cls, v: str) -> str:
        if not v.startswith("evt_"):
            raise ValueError("Event ID must start with 'evt_'")
        return v


class UserEvent(BaseEvent):
    """Inherits event_id validator from BaseEvent!"""
    user_id: str


class PurchaseEvent(UserEvent):
    """Inherits ALL validators from the chain."""
    product_id: str
    amount: float = Field(gt=0)


# Validators cascade down the hierarchy
event = PurchaseEvent(
    event_id="evt_1",
    timestamp="2024-01-01T10:00:00",  # Coerced to datetime!
    user_id="user_42",
    product_id="prod_99",
    amount=29.99,
)

# Inherited validator still works:
try:
    PurchaseEvent(
        event_id="bad_id",  # Fails parent's validator!
        timestamp="2024-01-01",
        user_id="u1",
        product_id="p1",
        amount=10,
    )
except Exception as e:
    print(e)  # Event ID must start with 'evt_'
```

**Pydantic model with overridden validators:**

```python
from pydantic import BaseModel, field_validator


class Animal(BaseModel):
    name: str
    sound: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip().title()


class Dog(Animal):
    breed: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Override parent validator."""
        v = v.strip().title()
        if len(v) < 2:
            raise ValueError("Dog names must be at least 2 characters")
        return v


dog = Dog(name="rex", sound="woof", breed="labrador")
print(dog.name)  # "Rex" — child validator ran
```

### Inheritance Comparison

| Aspect | Dataclass | Pydantic |
|--------|-----------|----------|
| Basic inheritance | ✅ Works | ✅ Works |
| Field ordering | Parent first, child appended | Parent first, child appended |
| Validator inheritance | Manual (`super().__post_init__()`) | Automatic (validators cascade) |
| Default value gotcha | Yes (non-default can't follow default) | No (Pydantic handles ordering) |
| Multiple inheritance | Works but complex | Works (model hierarchy) |
| Override validators | Override `__post_init__` | Override `@field_validator` |

---

## Composition

### Dataclass Composition (Nested Dataclasses)

```python
from dataclasses import dataclass, field, asdict


@dataclass
class Address:
    street: str
    city: str
    country: str
    zip_code: str


@dataclass
class ContactInfo:
    email: str
    phone: str | None = None


@dataclass
class Company:
    name: str
    industry: str


@dataclass
class Employee:
    """Composed of multiple dataclasses."""
    name: str
    address: Address           # Has-an Address
    contact: ContactInfo       # Has-a ContactInfo
    company: Company           # Belongs-to a Company
    skills: list[str] = field(default_factory=list)


# Creating a composed object
emp = Employee(
    name="Alice",
    address=Address(street="123 Main St", city="NYC", country="US", zip_code="10001"),
    contact=ContactInfo(email="alice@company.com", phone="+1234567890"),
    company=Company(name="TechCorp", industry="Software"),
    skills=["Python", "AWS"],
)

# asdict() recursively converts all nested dataclasses
print(asdict(emp))
# {'name': 'Alice', 'address': {'street': '123 Main St', 'city': 'NYC', ...}, ...}
```

**⚠️ Limitation:** `asdict()` handles nested dataclasses, but deserializing back (dict → nested dataclasses) requires manual work:

```python
# Deserializing nested dataclasses — must do it manually
data = {
    "name": "Bob",
    "address": {"street": "456 Oak Ave", "city": "LA", "country": "US", "zip_code": "90001"},
    "contact": {"email": "bob@co.com"},
    "company": {"name": "StartupXYZ", "industry": "AI"},
}

# ❌ This doesn't work:
# emp = Employee(**data)  # address would be a dict, not an Address object!

# ✅ Must manually reconstruct:
emp = Employee(
    name=data["name"],
    address=Address(**data["address"]),
    contact=ContactInfo(**data["contact"]),
    company=Company(**data["company"]),
)
```

### Pydantic Composition (Nested Models)

```python
from pydantic import BaseModel, Field, EmailStr


class Address(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str


class ContactInfo(BaseModel):
    email: EmailStr
    phone: str | None = None


class Company(BaseModel):
    name: str
    industry: str


class Employee(BaseModel):
    """Composed of multiple Pydantic models."""
    name: str
    address: Address
    contact: ContactInfo
    company: Company
    skills: list[str] = Field(default_factory=list)


# ✅ Pydantic automatically validates nested models from dicts!
data = {
    "name": "Bob",
    "address": {"street": "456 Oak Ave", "city": "LA", "country": "US", "zip_code": "90001"},
    "contact": {"email": "bob@company.com"},
    "company": {"name": "StartupXYZ", "industry": "AI"},
}

emp = Employee.model_validate(data)  # Recursive validation!
print(type(emp.address))  # <class 'Address'> — properly constructed
print(emp.contact.email)  # bob@company.com (validated as email)

# Serialization also recursive
print(emp.model_dump_json(indent=2))
```

### Composition with Strategy Pattern

```python
from dataclasses import dataclass
from typing import Protocol


# ─── With Dataclass + Protocol ───

class PricingStrategy(Protocol):
    def calculate(self, base_price: float, quantity: int) -> float:
        ...


class BulkDiscount:
    def calculate(self, base_price: float, quantity: int) -> float:
        if quantity > 10:
            return base_price * quantity * 0.9  # 10% off
        return base_price * quantity


class NoDiscount:
    def calculate(self, base_price: float, quantity: int) -> float:
        return base_price * quantity


@dataclass
class Order:
    product: str
    base_price: float
    quantity: int
    pricing: PricingStrategy  # Composed strategy

    @property
    def total(self) -> float:
        return self.pricing.calculate(self.base_price, self.quantity)


order = Order(product="Widget", base_price=10.0, quantity=15, pricing=BulkDiscount())
print(order.total)  # 135.0 (10% discount applied)
```

```python
# ─── With Pydantic (requires some configuration) ───
from pydantic import BaseModel, computed_field
from typing import Any


class PricingConfig(BaseModel):
    """Pydantic models work best for DATA, not strategy objects."""
    strategy: str = "bulk"  # "bulk" or "none"
    bulk_threshold: int = 10
    bulk_discount: float = 0.1


class Order(BaseModel):
    product: str
    base_price: float
    quantity: int
    pricing: PricingConfig = PricingConfig()

    @computed_field
    @property
    def total(self) -> float:
        if self.pricing.strategy == "bulk" and self.quantity > self.pricing.bulk_threshold:
            return self.base_price * self.quantity * (1 - self.pricing.bulk_discount)
        return self.base_price * self.quantity


order = Order(product="Widget", base_price=10.0, quantity=15)
print(order.total)  # 135.0
```

### Composition Comparison

| Aspect | Dataclass | Pydantic |
|--------|-----------|----------|
| Nested objects | Works (manual construction) | Works (auto-validation from dicts) |
| Dict → nested object | Manual (`Address(**data)`) | Automatic (`model_validate(data)`) |
| Serialization | `asdict()` (recursive) | `.model_dump()` (recursive) |
| Non-data dependencies | Easy (any object as field) | Harder (prefers serializable data) |
| Strategy pattern | Natural (accepts any Protocol-matching obj) | Better with config-as-data approach |
| Best for | Composing behavior + data | Composing validated data structures |

---

## ABCs with Dataclasses and Pydantic

### ABC + Dataclass

You can combine ABCs with dataclasses to get both contract enforcement AND boilerplate reduction.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Notifier(ABC):
    """Contract: all notifiers must implement send()."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        ...

    @abstractmethod
    def format_message(self, message: str) -> str:
        ...


@dataclass
class EmailNotifier(Notifier):
    """Dataclass that fulfills an ABC contract."""
    smtp_host: str
    smtp_port: int
    from_address: str

    def send(self, recipient: str, message: str) -> bool:
        formatted = self.format_message(message)
        print(f"📧 Sending from {self.from_address} via {self.smtp_host}:{self.smtp_port}")
        print(f"   To: {recipient} | Body: {formatted}")
        return True

    def format_message(self, message: str) -> str:
        return f"<html><body>{message}</body></html>"


@dataclass
class SlackNotifier(Notifier):
    """Another dataclass fulfilling the same ABC."""
    webhook_url: str
    channel: str

    def send(self, recipient: str, message: str) -> bool:
        formatted = self.format_message(message)
        print(f"💬 Slack [{self.channel}] to {recipient}: {formatted}")
        return True

    def format_message(self, message: str) -> str:
        return f"*{message}*"  # Slack markdown bold


# Usage with polymorphism
notifiers: list[Notifier] = [
    EmailNotifier(smtp_host="smtp.gmail.com", smtp_port=587, from_address="noreply@app.com"),
    SlackNotifier(webhook_url="https://hooks.slack.com/...", channel="#alerts"),
]

for notifier in notifiers:
    notifier.send("team@company.com", "Deployment complete!")
```

### ABC + Pydantic

Pydantic models can also implement ABCs, but with some nuances.

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class Repository(ABC):
    """ABC defining the repository contract."""

    @abstractmethod
    def find_by_id(self, id: str) -> dict | None:
        ...

    @abstractmethod
    def save(self, entity: dict) -> str:
        ...

    @abstractmethod
    def delete(self, id: str) -> bool:
        ...


class DatabaseConfig(BaseModel):
    """Pydantic model for validated config — separate from ABC."""
    host: str
    port: int = Field(ge=1, le=65535)
    database: str
    username: str
    password: str


class PostgresRepository(Repository):
    """
    Implements the ABC contract.
    Uses a Pydantic model for its configuration (composition).
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config  # Validated Pydantic config

    def find_by_id(self, id: str) -> dict | None:
        print(f"SELECT * FROM table WHERE id = '{id}' @ {self.config.host}")
        return {"id": id}

    def save(self, entity: dict) -> str:
        print(f"INSERT INTO table @ {self.config.host}")
        return "new_id"

    def delete(self, id: str) -> bool:
        print(f"DELETE FROM table WHERE id = '{id}' @ {self.config.host}")
        return True


# Pydantic validates the config, ABC enforces the interface
config = DatabaseConfig(
    host="localhost", port=5432, database="myapp",
    username="admin", password="secret"
)
repo = PostgresRepository(config)
repo.save({"name": "Alice"})
```

**⚠️ Important:** You generally DON'T make a Pydantic model directly inherit from an ABC. Pydantic models already inherit from `BaseModel`, and mixing with ABC creates MRO complexities. Instead:
- Use ABC for **behavior contracts** (services, repositories)
- Use Pydantic for **data validation** (configs, DTOs, API payloads)
- Compose them (service class uses Pydantic config)

```python
# ❌ AVOID: Pydantic model inheriting from ABC
class Sendable(ABC):
    @abstractmethod
    def send(self) -> None: ...

class Email(BaseModel, Sendable):  # ⚠️ MRO gets complex
    to: str
    body: str
    def send(self) -> None: ...

# ✅ PREFER: Separate concerns
class EmailData(BaseModel):
    """Pure data — validated by Pydantic."""
    to: str
    body: str

class EmailSender(ABC):
    """Behavior — contract enforced by ABC."""
    @abstractmethod
    def send(self, email: EmailData) -> bool: ...
```

---

## Protocols with Dataclasses and Pydantic

### Protocol + Dataclass

Dataclasses work beautifully with Protocols — they're just regular classes with generated methods.

```python
from dataclasses import dataclass
from typing import Protocol


class Cacheable(Protocol):
    """Any object with a cache_key property satisfies this."""
    @property
    def cache_key(self) -> str:
        ...


class Serializable(Protocol):
    """Any object with these methods satisfies this."""
    def to_dict(self) -> dict:
        ...

    @classmethod
    def from_dict(cls, data: dict) -> "Serializable":
        ...


@dataclass
class UserProfile:
    """Dataclass that satisfies BOTH Protocols — no inheritance needed!"""
    user_id: str
    name: str
    email: str

    @property
    def cache_key(self) -> str:
        return f"user:{self.user_id}"

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(**data)


@dataclass
class ProductListing:
    """Another dataclass satisfying the same Protocols."""
    product_id: str
    title: str
    price: float

    @property
    def cache_key(self) -> str:
        return f"product:{self.product_id}"

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProductListing":
        return cls(**data)


# Functions work with anything satisfying the Protocol
def cache_store(item: Cacheable, cache: dict) -> None:
    cache[item.cache_key] = item
    print(f"Cached: {item.cache_key}")


def serialize_many(items: list[Serializable]) -> list[dict]:
    return [item.to_dict() for item in items]


# Both work without sharing any base class!
cache: dict = {}
user = UserProfile(user_id="u1", name="Alice", email="alice@test.com")
product = ProductListing(product_id="p1", title="Widget", price=9.99)

cache_store(user, cache)     # Cached: user:u1
cache_store(product, cache)  # Cached: product:p1
```

### Protocol + Pydantic

Pydantic models also satisfy Protocols structurally.

```python
from pydantic import BaseModel, computed_field
from typing import Protocol


class HasMetadata(Protocol):
    """Protocol for objects that expose metadata."""
    @property
    def metadata(self) -> dict[str, str]:
        ...


class Exportable(Protocol):
    """Protocol for objects that can be exported."""
    def export(self, format: str) -> str | bytes:
        ...


class Invoice(BaseModel):
    """Pydantic model that satisfies both Protocols."""
    invoice_id: str
    customer: str
    amount: float
    currency: str = "USD"

    @computed_field
    @property
    def metadata(self) -> dict[str, str]:
        return {
            "type": "invoice",
            "id": self.invoice_id,
            "customer": self.customer,
        }

    def export(self, format: str) -> str | bytes:
        if format == "json":
            return self.model_dump_json()
        elif format == "csv":
            return f"{self.invoice_id},{self.customer},{self.amount},{self.currency}"
        raise ValueError(f"Unsupported format: {format}")


class Report(BaseModel):
    """Different Pydantic model, same Protocols."""
    report_id: str
    title: str
    content: str

    @computed_field
    @property
    def metadata(self) -> dict[str, str]:
        return {"type": "report", "id": self.report_id, "title": self.title}

    def export(self, format: str) -> str | bytes:
        if format == "json":
            return self.model_dump_json()
        return self.content


# Functions accept anything matching the Protocol
def log_metadata(item: HasMetadata) -> None:
    print(f"Metadata: {item.metadata}")

def export_all(items: list[Exportable], format: str) -> list[str | bytes]:
    return [item.export(format) for item in items]


invoice = Invoice(invoice_id="INV-001", customer="Acme Corp", amount=500.0)
report = Report(report_id="RPT-001", title="Q4 Summary", content="Revenue up 20%...")

log_metadata(invoice)  # Works!
log_metadata(report)   # Works!
export_all([invoice, report], "json")  # Both exportable!
```

### Protocol Comparison

| Aspect | Dataclass + Protocol | Pydantic + Protocol |
|--------|---------------------|---------------------|
| Satisfies Protocols? | ✅ Yes (structural typing) | ✅ Yes (structural typing) |
| `@property` in Protocol | Use `@property` in dataclass | Use `@computed_field` + `@property` |
| Methods in Protocol | Define normally | Define normally |
| No inheritance needed? | ✅ Correct | ✅ Correct |
| Type checker support | Full (mypy/pyright) | Full (mypy/pyright) |
| Best combination | Protocol for interface + dataclass for internal data | Protocol for interface + Pydantic for validated external data |

---

## Real-World Scenario: REST API Configuration System

A realistic example showing both dataclasses and Pydantic used together in the same project — each where it makes sense.

```python
"""
Scenario: A microservice that:
1. Reads config from YAML/env vars (Pydantic — external data, needs validation)
2. Processes internal domain objects (dataclasses — trusted internal state)
3. Accepts API requests (Pydantic — untrusted external input)
4. Returns API responses (Pydantic — needs serialization)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field, field_validator, computed_field, EmailStr


# ═══════════════════════════════════════════════════════════════
# LAYER 1: CONFIGURATION (Pydantic — external data, needs validation)
# ═══════════════════════════════════════════════════════════════

class DatabaseConfig(BaseModel):
    """Validated from environment variables or config files."""
    host: str
    port: int = Field(ge=1, le=65535)
    name: str
    username: str
    password: str
    pool_size: int = Field(default=5, ge=1, le=100)

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()


class AppConfig(BaseModel):
    """Top-level config — composed of validated sub-configs."""
    app_name: str
    debug: bool = False
    database: DatabaseConfig
    allowed_origins: list[str] = Field(default_factory=list)
    max_request_size_mb: int = Field(default=10, ge=1, le=100)


# ═══════════════════════════════════════════════════════════════
# LAYER 2: API REQUEST/RESPONSE MODELS (Pydantic — external boundary)
# ═══════════════════════════════════════════════════════════════

class CreateUserRequest(BaseModel):
    """Incoming API request — untrusted, needs full validation."""
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)
    department: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        valid = {"engineering", "marketing", "sales", "hr", "finance"}
        if v.lower() not in valid:
            raise ValueError(f"Department must be one of: {valid}")
        return v.lower()


class UserResponse(BaseModel):
    """Outgoing API response — needs serialization to JSON."""
    id: str
    name: str
    email: str
    age: int
    department: str
    created_at: datetime
    is_active: bool

    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.department})"


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size


# ═══════════════════════════════════════════════════════════════
# LAYER 3: DOMAIN MODELS (Dataclasses — internal, trusted, fast)
# ═══════════════════════════════════════════════════════════════

class UserStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class User:
    """
    Internal domain model — no validation needed because:
    - Data was already validated at the API boundary (Pydantic)
    - Only internal code creates these objects
    - We trust our own code
    - Performance matters for internal processing
    """
    id: str
    name: str
    email: str
    age: int
    department: str
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    login_count: int = 0

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE

    def suspend(self) -> None:
        self.status = UserStatus.SUSPENDED

    def record_login(self) -> None:
        self.login_count += 1

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE


@dataclass
class AuditEntry:
    """Internal audit log — pure data, no validation needed."""
    timestamp: datetime
    user_id: str
    action: str
    details: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# LAYER 4: SERVICE LAYER (Protocols + Composition)
# ═══════════════════════════════════════════════════════════════

class UserRepository(Protocol):
    """Protocol — any storage backend that matches this shape."""
    def find_by_id(self, user_id: str) -> User | None: ...
    def find_all(self, page: int, page_size: int) -> list[User]: ...
    def save(self, user: User) -> None: ...
    def count(self) -> int: ...


class AuditLogger(Protocol):
    """Protocol — any audit logging implementation."""
    def log(self, entry: AuditEntry) -> None: ...


class UserService:
    """
    Service layer — uses composition.
    - Receives Pydantic models (validated API input)
    - Works with dataclass domain models (internal logic)
    - Returns Pydantic models (serialized API output)
    """

    def __init__(self, repo: UserRepository, audit: AuditLogger):
        self.repo = repo
        self.audit = audit

    def create_user(self, request: CreateUserRequest) -> UserResponse:
        """
        Flow: Pydantic request → dataclass domain → Pydantic response
        """
        # 1. Convert validated request to domain model
        import uuid
        user = User(
            id=str(uuid.uuid4()),
            name=request.name,
            email=request.email,
            age=request.age,
            department=request.department,
        )

        # 2. Domain logic (on dataclass — fast, no validation overhead)
        user.activate()

        # 3. Persist
        self.repo.save(user)

        # 4. Audit (using dataclass)
        self.audit.log(AuditEntry(
            timestamp=datetime.now(),
            user_id=user.id,
            action="user_created",
            details={"name": user.name, "department": user.department},
        ))

        # 5. Convert to response model (Pydantic — for serialization)
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            age=user.age,
            department=user.department,
            created_at=user.created_at,
            is_active=user.is_active,
        )

    def list_users(self, page: int = 1, page_size: int = 20) -> PaginatedResponse:
        users = self.repo.find_all(page, page_size)
        total = self.repo.count()

        return PaginatedResponse(
            items=[
                UserResponse(
                    id=u.id, name=u.name, email=u.email,
                    age=u.age, department=u.department,
                    created_at=u.created_at, is_active=u.is_active,
                )
                for u in users
            ],
            total=total,
            page=page,
            page_size=page_size,
        )


# ═══════════════════════════════════════════════════════════════
# LAYER 5: INFRASTRUCTURE (Implements Protocols)
# ═══════════════════════════════════════════════════════════════

class InMemoryUserRepository:
    """Satisfies UserRepository Protocol — no inheritance needed."""

    def __init__(self):
        self._users: dict[str, User] = {}

    def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def find_all(self, page: int, page_size: int) -> list[User]:
        all_users = list(self._users.values())
        start = (page - 1) * page_size
        return all_users[start:start + page_size]

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def count(self) -> int:
        return len(self._users)


class ConsoleAuditLogger:
    """Satisfies AuditLogger Protocol."""

    def log(self, entry: AuditEntry) -> None:
        print(f"[AUDIT] {entry.timestamp.isoformat()} | {entry.action} | user={entry.user_id}")


# ═══════════════════════════════════════════════════════════════
# PUTTING IT TOGETHER
# ═══════════════════════════════════════════════════════════════

def main():
    # Load and validate config (Pydantic)
    config = AppConfig.model_validate({
        "app_name": "UserService",
        "debug": True,
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "users_db",
            "username": "admin",
            "password": "secret",
        },
    })
    print(f"Starting {config.app_name} (debug={config.debug})")

    # Wire up service (composition)
    service = UserService(
        repo=InMemoryUserRepository(),
        audit=ConsoleAuditLogger(),
    )

    # Simulate API request (Pydantic validates input)
    request = CreateUserRequest(
        name="  alice johnson  ",
        email="alice@company.com",
        age="28",  # Coerced to int!
        department="Engineering",
    )

    # Process (internal dataclass logic)
    response = service.create_user(request)

    # Return serialized response (Pydantic)
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL BOUNDARY                          │
│              (Untrusted data flows in/out)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐           ┌──────────────────┐        │
│  │ CreateUserRequest│  ──────► │   UserResponse    │        │
│  │   (Pydantic)    │           │   (Pydantic)     │        │
│  │  • Validates    │           │  • Serializes     │        │
│  │  • Coerces     │           │  • JSON Schema    │        │
│  └────────┬────────┘           └────────▲─────────┘        │
│           │                             │                    │
├───────────┼─────────────────────────────┼────────────────────┤
│           │     INTERNAL DOMAIN         │                    │
│           ▼                             │                    │
│  ┌──────────────────────────────────────┴──────┐            │
│  │              UserService                     │            │
│  │         (Composition + Protocols)            │            │
│  │                                              │            │
│  │  Pydantic request → Dataclass → Pydantic response        │
│  └──────────┬───────────────────────┬───────────┘            │
│             │                       │                        │
│  ┌──────────▼──────┐    ┌──────────▼──────┐                │
│  │      User       │    │   AuditEntry    │                │
│  │  (Dataclass)    │    │  (Dataclass)    │                │
│  │  • Fast         │    │  • Internal     │                │
│  │  • Domain logic │    │  • No overhead  │                │
│  │  • Trusted data │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘

PYDANTIC at boundaries: config, API request, API response
DATACLASS internally: domain entities, value objects, events
PROTOCOL for contracts: repository, audit, services
COMPOSITION to wire: service owns repo + audit
```

---

## Decision Framework

### When to Use Dataclass

| Situation | Why Dataclass |
|-----------|---------------|
| Internal domain models | Fast, no validation overhead |
| Value objects (Money, Coordinate) | Lightweight, supports `frozen=True` |
| Event objects | Simple data carriers |
| Already-validated data | Trust the data, skip re-validation |
| Performance-critical paths | No validation = faster |
| No external dependencies wanted | stdlib only |
| Data transfer between internal components | No serialization needed |

### When to Use Pydantic

| Situation | Why Pydantic |
|-----------|--------------|
| API request/response models | Full validation + serialization |
| Configuration loading | Validates from YAML/env/JSON |
| External data ingestion | Can't trust the source |
| JSON Schema needed | OpenAPI docs, API contracts |
| Type coercion required | `"42"` → `42` automatically |
| Complex nested validation | Recursive model validation |
| Database ORM integration | Works with SQLAlchemy, etc. |

### When to Use Standard Class

| Situation | Why Standard Class |
|-----------|-------------------|
| Primarily behavior, little data | Services, controllers, strategies |
| Complex initialization logic | Can't fit in `__post_init__` |
| Need full control over `__init__` | Non-trivial construction |
| Implementing design patterns | Strategy, Observer, Command |
| Non-data classes | Don't need `__repr__`, `__eq__` etc. |

### The Golden Rule

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  EXTERNAL DATA (can't trust it)  →  PYDANTIC               │
│    • API requests                                           │
│    • Config files                                           │
│    • Database results                                       │
│    • User input                                             │
│                                                              │
│  INTERNAL DATA (your own code)   →  DATACLASS              │
│    • Domain entities                                        │
│    • Events / commands                                      │
│    • Value objects                                          │
│    • Inter-service DTOs                                     │
│                                                              │
│  BEHAVIOR (logic, not data)      →  STANDARD CLASS         │
│    • Services                                               │
│    • Repositories                                           │
│    • Controllers                                            │
│    • Strategy implementations                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Quick Decision Flowchart

```
Is this class primarily holding data?
├── NO → Standard class (services, strategies, etc.)
│
└── YES → Does the data come from an external/untrusted source?
    ├── YES → Pydantic
    │   • API input?  → Pydantic
    │   • Config file? → Pydantic
    │   • User input?  → Pydantic
    │
    └── NO → Dataclass
        • Internal model?     → Dataclass
        • Already validated?  → Dataclass
        • Need performance?   → Dataclass
        • No dependencies?    → Dataclass
```

---

## FAQ

### 1. Can a single `field_validator` validate multiple fields in Pydantic?

**Yes.** Pass multiple field names to `@field_validator`.

```python
from pydantic import BaseModel, field_validator


class UserForm(BaseModel):
    first_name: str
    last_name: str
    username: str

    @field_validator("first_name", "last_name", "username")
    @classmethod
    def must_not_be_empty(cls, v: str, info) -> str:
        """This single validator runs for ALL three fields."""
        if not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()


class Product(BaseModel):
    name: str
    description: str
    sku: str
    category: str

    @field_validator("name", "description", "sku", "category")
    @classmethod
    def no_special_chars(cls, v: str) -> str:
        """Shared validation logic for multiple fields."""
        if any(c in v for c in "<>{}[]"):
            raise ValueError("Special characters not allowed")
        return v

    @field_validator("name", "sku")
    @classmethod
    def must_be_uppercase(cls, v: str) -> str:
        """Another shared validator — only for name and sku."""
        return v.upper()


# Usage
product = Product(name="widget", description="A cool thing", sku="abc-123", category="tools")
print(product.name)  # "WIDGET" (uppercased)
print(product.sku)   # "ABC-123" (uppercased)
print(product.description)  # "A cool thing" (not uppercased — not in that validator)
```

**You can also use `info.field_name` to customize behavior per field:**

```python
from pydantic import BaseModel, field_validator
from pydantic import ValidationInfo


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

    @field_validator("street", "city", "state", "zip_code")
    @classmethod
    def validate_all(cls, v: str, info: ValidationInfo) -> str:
        v = v.strip()
        if not v:
            raise ValueError(f"{info.field_name} is required")

        # Different max lengths per field
        max_lengths = {"street": 200, "city": 100, "state": 2, "zip_code": 10}
        max_len = max_lengths.get(info.field_name, 100)
        if len(v) > max_len:
            raise ValueError(f"{info.field_name} must be <= {max_len} chars")

        return v
```

---

### 2. What is the difference between `field_validator` and `model_validator`?

**`field_validator`** runs on a **single field** (or multiple specified fields), one at a time.
**`model_validator`** runs on the **entire model** — has access to ALL fields together.

```python
from pydantic import BaseModel, field_validator, model_validator, Field


class DateRange(BaseModel):
    start_date: str
    end_date: str
    label: str

    # ─── field_validator: validates ONE field at a time ───
    @field_validator("label")
    @classmethod
    def label_not_empty(cls, v: str) -> str:
        """Can only see 'label'. Cannot access start_date or end_date."""
        if not v.strip():
            raise ValueError("Label required")
        return v.strip()

    # ─── model_validator: validates the WHOLE model ───
    @model_validator(mode="after")
    def end_after_start(self) -> "DateRange":
        """Can see ALL fields. Validates cross-field relationships."""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class Transfer(BaseModel):
    from_account: str
    to_account: str
    amount: float = Field(gt=0)
    currency: str

    # Field-level: each field validated independently
    @field_validator("from_account", "to_account")
    @classmethod
    def account_format(cls, v: str) -> str:
        if not v.startswith("ACC-"):
            raise ValueError("Account must start with ACC-")
        return v

    # Model-level: cross-field validation
    @model_validator(mode="after")
    def accounts_must_differ(self) -> "Transfer":
        if self.from_account == self.to_account:
            raise ValueError("Cannot transfer to the same account")
        return self
```

**`mode="before"` vs `mode="after"`:**

```python
from pydantic import BaseModel, model_validator
from typing import Any


class FlexibleInput(BaseModel):
    name: str
    age: int

    @model_validator(mode="before")
    @classmethod
    def preprocess(cls, data: Any) -> Any:
        """
        mode='before': Runs BEFORE field validation.
        Receives raw input (dict, etc). Good for transforming/normalizing
        the raw data before Pydantic processes it.
        """
        if isinstance(data, dict):
            # Normalize keys to lowercase
            data = {k.lower(): v for k, v in data.items()}
            # Handle alternate field names
            if "full_name" in data:
                data["name"] = data.pop("full_name")
        return data

    @model_validator(mode="after")
    def postprocess(self) -> "FlexibleInput":
        """
        mode='after': Runs AFTER all field validation.
        Receives the fully constructed model instance.
        Good for cross-field validation.
        """
        if self.age < 13 and len(self.name) < 2:
            raise ValueError("Young users must have full names")
        return self


# mode='before' allows flexible input
user = FlexibleInput.model_validate({"Full_Name": "Alice", "AGE": "25"})
print(user)  # name='Alice' age=25
```

**Summary table:**

| | `field_validator` | `model_validator` |
|---|---|---|
| Scope | One field (or listed fields) | All fields |
| Access | Only the field being validated | Entire model instance |
| Use case | Format/range/type of single field | Cross-field relationships |
| Modes | `mode="before"` / `mode="after"` | `mode="before"` / `mode="after"` |
| `before` receives | Raw field value | Raw input data (dict) |
| `after` receives | Parsed field value | Constructed model instance |
| Example | "email must contain @" | "end_date must be after start_date" |

---

### 3. Can I validate CSV file columns using Pydantic?

**Yes, absolutely.** This is one of Pydantic's best real-world use cases. Each CSV row becomes a Pydantic model instance, and invalid rows are caught with clear error messages.

```python
import csv
from enum import Enum
from pydantic import BaseModel, Field, field_validator, EmailStr, ValidationError


# ─── Define the row schema ───

class TicketStatus(str, Enum):
    CLOSED = "CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    OPEN = "OPEN"
    REVIEW = "REVIEW"


class CSVRow(BaseModel):
    """Each row in the CSV is validated against this model."""
    first_name: str
    last_name: str
    email: EmailStr
    age: int = Field(ge=1, le=100)
    status: TicketStatus

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


# ─── Validate the CSV ───

def validate_csv(file_path: str) -> tuple[list[CSVRow], list[dict]]:
    """
    Returns (valid_rows, errors).
    Each error includes the row number and what went wrong.
    """
    valid_rows: list[CSVRow] = []
    errors: list[dict] = []

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # start=2 (header is row 1)
            try:
                validated = CSVRow.model_validate(row)
                valid_rows.append(validated)
            except ValidationError as e:
                errors.append({
                    "row": row_num,
                    "data": row,
                    "errors": e.errors(),
                })

    return valid_rows, errors


# ─── Usage ───

# Sample CSV content:
# first_name,last_name,email,age,status
# Alice,Smith,alice@example.com,28,OPEN
# ,Johnson,bad-email,150,INVALID_STATUS
# Bob,Williams,bob@test.com,35,CLOSED

valid, errors = validate_csv("data.csv")

print(f"✅ Valid rows: {len(valid)}")
print(f"❌ Invalid rows: {len(errors)}")

for err in errors:
    print(f"\n  Row {err['row']}: {err['data']}")
    for e in err["errors"]:
        print(f"    - {e['loc'][0]}: {e['msg']}")

# Output:
# ✅ Valid rows: 2
# ❌ Invalid rows: 1
#
#   Row 3: {'first_name': '', 'last_name': 'Johnson', 'email': 'bad-email', 'age': '150', 'status': 'INVALID_STATUS'}
#     - first_name: Name cannot be empty
#     - email: value is not a valid email address
#     - age: Input should be less than or equal to 100
#     - status: Input should be 'CLOSED', 'IN_PROGRESS', 'OPEN' or 'REVIEW'
```

**For large CSVs with pandas:**

```python
import pandas as pd
from pydantic import BaseModel, Field, EmailStr, ValidationError
from enum import Enum


class TicketStatus(str, Enum):
    CLOSED = "CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    OPEN = "OPEN"
    REVIEW = "REVIEW"


class CSVRow(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    age: int = Field(ge=1, le=100)
    status: TicketStatus


def validate_dataframe(df: pd.DataFrame) -> tuple[list[CSVRow], pd.DataFrame]:
    """Validate a pandas DataFrame row-by-row with Pydantic."""
    valid_rows: list[CSVRow] = []
    error_indices: list[int] = []
    error_messages: list[str] = []

    for idx, row in df.iterrows():
        try:
            validated = CSVRow.model_validate(row.to_dict())
            valid_rows.append(validated)
        except ValidationError as e:
            error_indices.append(idx)
            error_messages.append(str(e))

    # Return valid rows + a DataFrame of invalid rows with error details
    error_df = df.loc[error_indices].copy()
    error_df["validation_errors"] = error_messages

    return valid_rows, error_df


# Usage
df = pd.read_csv("data.csv")
valid, errors_df = validate_dataframe(df)
print(f"Valid: {len(valid)}, Invalid: {len(errors_df)}")
if not errors_df.empty:
    errors_df.to_csv("validation_errors.csv", index=False)
```

**Key takeaway:** Pydantic turns CSV validation from messy if/else spaghetti into clean, declarative schemas. Each column constraint is a field definition or validator.

---

### 4. What does `_age: int = field(repr=False)` actually mean in a dataclass?

`field()` customizes how a specific field behaves in the auto-generated methods. `repr=False` means the field is **excluded from `__repr__`** (the printed representation).

**All `field()` options explained:**

```python
from dataclasses import dataclass, field


@dataclass
class User:
    # Normal field — included in __init__, __repr__, __eq__
    name: str

    # repr=False — still in __init__ and __eq__, but NOT printed in repr
    _password: str = field(repr=False)

    # init=False — NOT in __init__, must be set in __post_init__ or later
    login_count: int = field(init=False, default=0)

    # compare=False — NOT used in __eq__ comparison
    cache_key: str = field(default="", compare=False)

    # hash=False — NOT used in __hash__ (if hash is generated)
    metadata: dict = field(default_factory=dict, hash=False, compare=False)

    # default_factory — callable to generate default (for mutable defaults)
    roles: list[str] = field(default_factory=list)


user = User(name="Alice", _password="secret123")
print(user)
# User(name='Alice', login_count=0, cache_key='', metadata={}, roles=[])
#
# Notice: _password is MISSING from output (repr=False)
# But it still EXISTS:
print(user._password)  # "secret123"
```

**Complete `field()` parameter reference:**

| Parameter | Default | Effect |
|-----------|---------|--------|
| `default` | MISSING | Default value for the field |
| `default_factory` | MISSING | Callable to generate default (for `list`, `dict`, etc.) |
| `repr` | `True` | Include in `__repr__` output? |
| `hash` | `None` | Include in `__hash__`? (`None` = same as `compare`) |
| `init` | `True` | Include as `__init__` parameter? |
| `compare` | `True` | Include in `__eq__` and ordering comparisons? |
| `kw_only` | `False` | Force keyword-only in `__init__`? (Python 3.10+) |

**Why use `repr=False`?**
- Hide sensitive data (`_password`, `_api_key`, `_token`)
- Hide verbose fields that clutter output (`large_blob`, `raw_data`)
- Hide internal/private state that's not useful for debugging

```python
from dataclasses import dataclass, field


@dataclass
class APIClient:
    base_url: str
    api_key: str = field(repr=False)  # Don't leak in logs!
    timeout: int = 30
    _session: object = field(init=False, repr=False, compare=False, default=None)

print(APIClient(base_url="https://api.example.com", api_key="sk_live_12345"))
# APIClient(base_url='https://api.example.com', timeout=30)
# api_key and _session are hidden from repr!
```

---

### 5. What does "Dataclass with a true getter/setter using `init=False` + `__post_init__`" mean?

This is a pattern for creating **computed/derived fields** that aren't set directly by the user but are calculated from other fields.

**The problem it solves:**

```python
from dataclasses import dataclass

# ❌ NAIVE: User must pass 'area' manually (error-prone)
@dataclass
class Rectangle:
    width: float
    height: float
    area: float  # User has to calculate this themselves!?

r = Rectangle(width=5, height=3, area=15)  # What if they pass wrong area?
r = Rectangle(width=5, height=3, area=999)  # No error!
```

**The solution — `init=False` + `__post_init__`:**

```python
from dataclasses import dataclass, field


@dataclass
class Rectangle:
    width: float
    height: float
    area: float = field(init=False)  # NOT a constructor parameter!

    def __post_init__(self):
        """Runs automatically after __init__. Compute derived values here."""
        self.area = self.width * self.height


# Now area is ALWAYS correct — user can't set it wrong
r = Rectangle(width=5, height=3)
print(r)       # Rectangle(width=5, height=3, area=15)
print(r.area)  # 15.0

# But there's a problem: if you change width, area is stale!
r.width = 10
print(r.area)  # Still 15.0! 💀 __post_init__ only runs once
```

**The "true getter/setter" pattern fixes staleness:**

```python
from dataclasses import dataclass, field


@dataclass
class Temperature:
    """
    'True getter/setter' means:
    - init=False: the field isn't in __init__
    - __post_init__: initial value is computed
    - @property: getter recomputes dynamically (never stale)
    - @x.setter: setter updates the source field
    """
    celsius: float
    # _fahrenheit exists for internal storage, NOT exposed to users
    _fahrenheit: float = field(init=False, repr=False)

    def __post_init__(self):
        # Initial computation
        self._fahrenheit = self.celsius * 9 / 5 + 32

    @property
    def fahrenheit(self) -> float:
        """TRUE GETTER — always recomputes from celsius. Never stale."""
        return self.celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        """TRUE SETTER — updates the source (celsius) when fahrenheit is set."""
        self.celsius = (value - 32) * 5 / 9


temp = Temperature(celsius=100)
print(temp.fahrenheit)  # 212.0

temp.celsius = 0
print(temp.fahrenheit)  # 32.0 ← Always correct! (property recomputes)

temp.fahrenheit = 212
print(temp.celsius)     # 100.0 ← Setter updated celsius!
```

**Comparison of approaches:**

```python
from dataclasses import dataclass, field


# ─── Approach 1: init=False + __post_init__ (computed once, can go stale) ───
@dataclass
class CircleV1:
    radius: float
    area: float = field(init=False)
    circumference: float = field(init=False)

    def __post_init__(self):
        import math
        self.area = math.pi * self.radius ** 2
        self.circumference = 2 * math.pi * self.radius

c = CircleV1(radius=5)
print(c.area)  # 78.54
c.radius = 10
print(c.area)  # 78.54 ❌ STALE! Still the old value


# ─── Approach 2: @property (true getter, always fresh) ───
@dataclass
class CircleV2:
    radius: float

    @property
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2  # Always recomputed

    @property
    def circumference(self) -> float:
        import math
        return 2 * math.pi * self.radius

c = CircleV2(radius=5)
print(c.area)  # 78.54
c.radius = 10
print(c.area)  # 314.16 ✅ FRESH! Recomputed from current radius


# ─── Approach 3: Hybrid (init=False for cached + property for live) ───
@dataclass
class CircleV3:
    radius: float
    _area_cache: float = field(init=False, repr=False)

    def __post_init__(self):
        self._recompute()

    def _recompute(self):
        import math
        self._area_cache = math.pi * self.radius ** 2

    @property
    def area(self) -> float:
        return self._area_cache

    @area.setter
    def area(self, value: float) -> None:
        raise AttributeError("Cannot set area directly. Change radius instead.")

    def set_radius(self, new_radius: float) -> None:
        """Explicit method to update radius and recompute."""
        self.radius = new_radius
        self._recompute()
```

**When to use which:**

| Approach | Use When |
|----------|----------|
| `init=False` + `__post_init__` | Field computed once, object is immutable after creation |
| `@property` (true getter) | Field must always reflect current state |
| Hybrid (cache + setter) | Computation is expensive, but must stay in sync |

---

### 6. What happens if I use a mutable default (like `list` or `dict`) directly in a dataclass?

**Python will raise an error.** This is a deliberate safety mechanism to prevent the classic "mutable default" bug.

```python
from dataclasses import dataclass, field


# ❌ ERROR: Mutable default not allowed
@dataclass
class BadTeam:
    name: str
    members: list[str] = []  # ValueError: mutable default <class 'list'> is not allowed

# Why? Because ALL instances would share the SAME list object:
# team1.members.append("Alice")
# print(team2.members)  # ["Alice"] ← Leaked between instances!


# ✅ CORRECT: Use field(default_factory=...)
@dataclass
class GoodTeam:
    name: str
    members: list[str] = field(default_factory=list)  # New list for each instance
    config: dict = field(default_factory=dict)         # New dict for each instance
    scores: set[int] = field(default_factory=set)      # New set for each instance


team1 = GoodTeam(name="Alpha")
team2 = GoodTeam(name="Beta")
team1.members.append("Alice")
print(team2.members)  # [] ← Correctly isolated!
```

**Pydantic handles this differently — it's safe by default:**

```python
from pydantic import BaseModel

class Team(BaseModel):
    name: str
    members: list[str] = []  # ✅ Safe! Pydantic copies it for each instance

team1 = Team(name="Alpha")
team2 = Team(name="Beta")
team1.members.append("Alice")
print(team2.members)  # [] ← Already isolated (Pydantic deep-copies defaults)
```

However, best practice in Pydantic is still to use `Field(default_factory=list)` for clarity.

---

### 7. Can Pydantic models be used as dictionary keys or in sets? What about dataclasses?

**Dataclasses:** Yes, if you use `frozen=True` (which auto-generates `__hash__`).
**Pydantic:** Yes, if you use `frozen=True` in config.

```python
from dataclasses import dataclass
from pydantic import BaseModel


# ─── Dataclass ───

@dataclass(frozen=True)
class Coordinate:
    x: float
    y: float

# ✅ Hashable — can use in sets and as dict keys
visited: set[Coordinate] = set()
visited.add(Coordinate(1.0, 2.0))
visited.add(Coordinate(1.0, 2.0))  # Duplicate — set deduplicates
print(len(visited))  # 1

distances: dict[Coordinate, float] = {
    Coordinate(0, 0): 0.0,
    Coordinate(3, 4): 5.0,
}


# ─── Pydantic ───

class PydanticCoordinate(BaseModel):
    model_config = {"frozen": True}
    x: float
    y: float

# ✅ Also hashable
visited_pydantic: set[PydanticCoordinate] = set()
visited_pydantic.add(PydanticCoordinate(x=1.0, y=2.0))


# ❌ Without frozen=True, both are NOT hashable
@dataclass
class MutablePoint:
    x: float
    y: float

# set().add(MutablePoint(1, 2))  # TypeError: unhashable type
```

**Why `frozen=True` is needed:** Python requires objects to be immutable to be hashable (otherwise hash could change after insertion, breaking the set/dict).

---

### 8. What's the performance difference between dataclasses and Pydantic? When does it matter?

**Dataclasses are 5-50x faster** for object creation because they skip validation.

```python
from dataclasses import dataclass
from pydantic import BaseModel
import time


@dataclass
class PointDC:
    x: float
    y: float
    z: float


class PointPydantic(BaseModel):
    x: float
    y: float
    z: float


# Benchmark: create 1 million objects
def benchmark(name, factory, n=1_000_000):
    start = time.perf_counter()
    for i in range(n):
        factory(x=1.0, y=2.0, z=3.0)
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.3f}s ({n/elapsed:.0f} objects/sec)")


benchmark("Dataclass", PointDC)
# Dataclass: ~0.3s (3,000,000+ objects/sec)

benchmark("Pydantic", PointPydantic)
# Pydantic:  ~2.5s (400,000 objects/sec)
```

**When performance matters:**
- Processing millions of records in a tight loop → dataclass
- Creating objects once from an API request → Pydantic (validation cost is negligible)
- Inner loops of data pipelines → dataclass
- Reading a config file once at startup → Pydantic (who cares about 1ms)

**The pattern:** Validate at the boundary (Pydantic), process internally (dataclass):

```python
from pydantic import BaseModel
from dataclasses import dataclass


class EventRequest(BaseModel):
    """Validates once at API boundary."""
    event_type: str
    payload: dict
    timestamp: float


@dataclass
class Event:
    """Used internally — created millions of times in processing."""
    event_type: str
    payload: dict
    timestamp: float


# Convert at boundary, use fast dataclass internally
def handle_request(request: EventRequest) -> None:
    # Validate once (Pydantic)
    event = Event(
        event_type=request.event_type,
        payload=request.payload,
        timestamp=request.timestamp,
    )
    # Process millions of times (fast dataclass)
    process_event(event)
```

---

### 9. Can I make a Pydantic model from an existing dataclass? Can they interoperate?

**Yes.** Pydantic can validate dataclass instances and also has its own `@pydantic.dataclasses.dataclass` decorator.

```python
from dataclasses import dataclass
from pydantic import BaseModel, TypeAdapter
import pydantic.dataclasses


# ─── Option 1: Pydantic model that accepts a dataclass ───

@dataclass
class AddressDC:
    street: str
    city: str
    zip_code: str


class UserWithAddress(BaseModel):
    name: str
    address: AddressDC  # Pydantic accepts dataclass instances!


user = UserWithAddress(
    name="Alice",
    address=AddressDC(street="123 Main", city="NYC", zip_code="10001"),
)
print(user.model_dump())
# {'name': 'Alice', 'address': {'street': '123 Main', 'city': 'NYC', 'zip_code': '10001'}}


# ─── Option 2: Pydantic-powered dataclass (best of both worlds) ───

@pydantic.dataclasses.dataclass
class ValidatedPoint:
    """Looks like a dataclass, validates like Pydantic."""
    x: float
    y: float
    z: float = 0.0

point = ValidatedPoint(x="1.5", y="2.5")  # Coercion works!
print(point.x)  # 1.5 (float, coerced from str)
print(type(point))  # <class 'ValidatedPoint'>

# Still a dataclass — works with asdict, etc.
from dataclasses import asdict
print(asdict(point))  # {'x': 1.5, 'y': 2.5, 'z': 0.0}


# ─── Option 3: TypeAdapter for validating dataclass data ───

@dataclass
class Product:
    name: str
    price: float

adapter = TypeAdapter(Product)
product = adapter.validate_python({"name": "Widget", "price": "9.99"})
print(product)        # Product(name='Widget', price=9.99)
print(type(product))  # <class 'Product'>
```

**When to use `pydantic.dataclasses.dataclass`:**
- You want dataclass syntax + Pydantic validation
- You need `asdict()` / `astuple()` compatibility
- The class is used in contexts that expect real dataclasses
- You're migrating a dataclass to add validation without rewriting

---

### 10. What's the difference between `BaseModel` and `pydantic.dataclasses.dataclass`?

```python
from pydantic import BaseModel
import pydantic.dataclasses


class UserModel(BaseModel):
    name: str
    age: int


@pydantic.dataclasses.dataclass
class UserDC:
    name: str
    age: int
```

| Aspect | `BaseModel` | `pydantic.dataclasses.dataclass` |
|--------|-------------|----------------------------------|
| Type | Pydantic model (inherits BaseModel) | Standard dataclass with validation |
| `model_dump()` | ✅ | ❌ (use `asdict()`) |
| `model_dump_json()` | ✅ | ❌ |
| `model_validate()` | ✅ | ❌ (use `TypeAdapter`) |
| `model_json_schema()` | ✅ | ❌ (use `TypeAdapter`) |
| `asdict()` | ❌ | ✅ |
| `astuple()` | ❌ | ✅ |
| Validation | ✅ | ✅ |
| Coercion | ✅ | ✅ |
| `isinstance(x, dataclass)` | ❌ | ✅ |
| Config/Settings | Full `model_config` | Limited |
| Best for | API models, full Pydantic features | Drop-in replacement for stdlib dataclass |

**Rule of thumb:** Use `BaseModel` for new code. Use `pydantic.dataclasses.dataclass` when you need dataclass compatibility with existing code.

---

### 11. How do I handle optional fields and `None` values differently in dataclasses vs Pydantic?

```python
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


# ─── Dataclass: Optional fields ───

@dataclass
class UserDC:
    name: str
    email: str | None = None          # Optional, defaults to None
    age: int | None = None             # Optional
    tags: list[str] = field(default_factory=list)  # Optional, defaults to empty list

user = UserDC(name="Alice")
print(user.email)  # None
print(user.tags)   # []


# ─── Pydantic: Optional fields (with nuances) ───

class UserPydantic(BaseModel):
    name: str
    email: str | None = None           # Optional, accepts None
    age: int | None = None             # Optional
    tags: list[str] = Field(default_factory=list)

# Pydantic distinguishes between "not provided" and "explicitly None"
user = UserPydantic(name="Alice")
print(user.email)  # None

# With model_dump(exclude_none=True):
print(user.model_dump())
# {'name': 'Alice', 'email': None, 'age': None, 'tags': []}

print(user.model_dump(exclude_none=True))
# {'name': 'Alice', 'tags': []}  ← None fields excluded!

print(user.model_dump(exclude_unset=True))
# {'name': 'Alice'}  ← Only explicitly set fields!
```

**The `exclude_unset` vs `exclude_none` distinction is powerful:**

```python
from pydantic import BaseModel


class UpdateUser(BaseModel):
    """For PATCH requests — distinguish 'not sent' from 'set to null'."""
    name: str | None = None
    email: str | None = None
    age: int | None = None


# User sends: {"email": null}  (explicitly clearing email)
update = UpdateUser.model_validate({"email": None})

print(update.model_dump(exclude_unset=True))
# {'email': None}  ← Only email was sent, and it was set to None

# vs User sends: {"name": "Bob"}  (only updating name)
update2 = UpdateUser.model_validate({"name": "Bob"})
print(update2.model_dump(exclude_unset=True))
# {'name': 'Bob'}  ← Only name was sent

# This lets you build proper PATCH logic:
def apply_patch(existing: dict, update: UpdateUser) -> dict:
    """Only override fields that were explicitly sent."""
    changes = update.model_dump(exclude_unset=True)
    return {**existing, **changes}
```

Dataclasses don't have this `unset` tracking — once created, there's no way to distinguish "defaulted" from "explicitly set."

---

### 12. Can Pydantic validate environment variables? How is this used in real projects?

**Yes — this is one of Pydantic's killer features via `pydantic-settings`.**

```python
# pip install pydantic-settings

from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Reads from environment variables automatically!"""
    model_config = {"env_prefix": "DB_"}  # All vars start with DB_

    host: str = "localhost"
    port: int = 5432
    name: str
    username: str
    password: str
    pool_size: int = Field(default=5, ge=1, le=50)


class AppSettings(BaseSettings):
    """Top-level app settings."""
    model_config = {"env_prefix": "APP_"}

    name: str = "myapp"
    debug: bool = False
    secret_key: str
    allowed_hosts: list[str] = ["localhost"]
    database: DatabaseSettings = DatabaseSettings()


# These environment variables would be set:
# DB_HOST=prod-db.internal
# DB_PORT=5432
# DB_NAME=users
# DB_USERNAME=admin
# DB_PASSWORD=supersecret
# APP_NAME=UserService
# APP_DEBUG=false
# APP_SECRET_KEY=abc123
# APP_ALLOWED_HOSTS=["api.example.com","admin.example.com"]

# In code:
settings = AppSettings()
# Automatically reads from environment!
# Validates types (DB_PORT must be int, APP_DEBUG must be bool)
# Raises clear errors if required vars are missing
```

**Real project pattern:**

```python
# config.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    database_url: str
    redis_url: str = "redis://localhost:6379"
    api_key: str
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Singleton — loaded once, cached forever."""
    return Settings()


# Usage anywhere in the app:
# from config import get_settings
# settings = get_settings()
# print(settings.database_url)
```

---

### 13. What is `model_config` in Pydantic and what are the most useful options?

`model_config` is a dictionary (or `ConfigDict`) that controls how the entire model behaves.

```python
from pydantic import BaseModel, ConfigDict


class StrictUser(BaseModel):
    model_config = ConfigDict(
        # ─── Validation behavior ───
        strict=True,              # No type coercion ("42" won't become int 42)
        validate_assignment=True, # Re-validate when fields are assigned after creation

        # ─── Immutability ───
        frozen=True,              # Make model immutable (like frozen dataclass)

        # ─── Extra fields ───
        extra="forbid",           # Reject fields not in the model (default: "ignore")
                                  # Options: "allow", "ignore", "forbid"

        # ─── Naming ───
        str_strip_whitespace=True,  # Auto-strip all str fields
        str_to_lower=True,          # Auto-lowercase all str fields

        # ─── Serialization ───
        populate_by_name=True,    # Allow both alias and field name
        use_enum_values=True,     # Store enum values instead of enum instances
    )

    name: str
    age: int


# strict=True: no coercion
# StrictUser(name="Alice", age="30")  # ❌ ValidationError (str can't become int)
# StrictUser(name="Alice", age=30)    # ✅ Works

# extra="forbid": rejects unknown fields
# StrictUser(name="Alice", age=30, unknown="x")  # ❌ ValidationError
```

**Most useful configs by situation:**

| Config | When to Use |
|--------|-------------|
| `validate_assignment=True` | Object can be mutated, need re-validation |
| `frozen=True` | Immutable value objects, config that shouldn't change |
| `extra="forbid"` | Strict API schemas — catch typos in field names |
| `extra="allow"` | Forward-compatible APIs — allow unknown fields |
| `strict=True` | When coercion is dangerous (security-sensitive) |
| `str_strip_whitespace=True` | Form input, user-facing data |
| `populate_by_name=True` | API uses camelCase but Python uses snake_case |
| `use_enum_values=True` | When you want `"active"` not `Status.ACTIVE` in dumps |

---

### 14. Spot the bug — what's wrong with this dataclass?

```python
from dataclasses import dataclass


@dataclass
class Config:
    name: str
    debug: bool = False
    tags: list[str] = []  # 🐛 BUG!
    port: int = 8080
```

**Answer:** `tags: list[str] = []` will raise `ValueError: mutable default <class 'list'> is not allowed: use default_factory`.

**Fix:**

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    name: str
    debug: bool = False
    tags: list[str] = field(default_factory=list)  # ✅
    port: int = 8080
```

---

### 15. When should I use `__post_init__` vs `field_validator` vs `model_validator`?

| | `__post_init__` (dataclass) | `@field_validator` (Pydantic) | `@model_validator` (Pydantic) |
|---|---|---|---|
| **When it runs** | After `__init__` | During model construction per field | Before/after all fields |
| **Access to** | All fields via `self` | Only the field being validated | All fields (mode=after) or raw data (mode=before) |
| **Raises** | Any exception | `ValueError` → becomes ValidationError | `ValueError` → becomes ValidationError |
| **Can transform data?** | Yes (modify `self.x`) | Yes (return transformed value) | Yes (return modified model) |
| **Cross-field logic?** | Yes | No (can't see other fields reliably) | Yes |
| **Multiple validations?** | Single function for everything | One per concern, composable | One for cross-field |

**Pattern: Use all three in the same project:**

```python
# Dataclass (internal model) — __post_init__ for simple normalization
@dataclass
class InternalEvent:
    name: str
    priority: int

    def __post_init__(self):
        self.name = self.name.lower()
        if self.priority < 1:
            self.priority = 1


# Pydantic (API model) — validators for external input
class APIEvent(BaseModel):
    name: str
    priority: int = Field(ge=1, le=10)
    start_time: datetime
    end_time: datetime

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def end_after_start(self) -> "APIEvent":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self
```


