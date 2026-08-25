# API Logging in FastAPI

This reference explains how to design logging for a FastAPI service: what to log, how standard Python logging is configured, how request context flows through the application, and how logs reach a centralized system.

## Goals

A production API should provide logs that are useful to developers, operators, and security teams without exposing sensitive information.

1. **Structured**: emit predictable fields, preferably JSON in production.
2. **Correlated**: include a request/correlation ID and tracing identifiers when available.
3. **Layered**: distinguish request, business, persistence, and security events by fields rather than unrelated logging systems.
4. **Safe**: redact secrets and minimize personal data.
5. **Operational**: choose levels intentionally, avoid unbounded local storage, and make logs searchable centrally.
6. **Environment-aware**: readable text locally; machine-readable logs in deployed environments.

```text
application code → logging API → enrichment/filter → formatter → handler
                → platform collector → central storage → search, dashboards, alerts
```

## The default strategy

Use the standard `logging` module as the application API. Configure it once, early in startup. Application code should only create named loggers and emit meaningful events; it should not decide where logs are stored or how they are formatted.

```python
import logging

logger = logging.getLogger(__name__)
logger.info("user_created", extra={"user_id": user_id})
```

In a containerized deployment, the normal default is JSON logs to stdout/stderr. The platform or a log collector ships them to a centralized service. File logging is an acceptable alternative when a deployment specifically requires it, but it must use rotation and bounded retention.

## What to log

Log events that explain what the system did, what it decided, or why it failed. Do not log every function call.

| Layer | Useful events | Important fields | Avoid |
| --- | --- | --- | --- |
| Request / API | request completed, unhandled error, rate limit | method, route template, status, duration, request ID | full request/response bodies by default |
| Business | order created, job started, workflow decision | operation, business ID, outcome, request ID | noisy implementation detail |
| Persistence | query/transaction failure, slow query, connection issue | database/service, duration, error class | SQL values that contain sensitive data |
| External dependency | retry, timeout, circuit open, failed call | dependency, operation, duration, retry count | credentials and full sensitive payloads |
| Authentication | login result, token validation issue | actor ID when safe, outcome, reason category | passwords, raw tokens, session IDs |
| Authorization | access denied, policy failure | actor ID, resource type, decision | unnecessary policy internals |

A useful entry answers: **what happened, where, when, for which request or actor, how long it took, and what failed**.

### Core log schema

Use stable field names. A typical record contains:

```json
{
  "timestamp": "2026-08-25T09:00:00Z",
  "level": "ERROR",
  "service": "user-service",
  "environment": "production",
  "logger": "app.users.service",
  "message": "user_create_failed",
  "request_id": "a1b2c3",
  "operation": "create_user",
  "error_type": "UniqueConstraintViolation",
  "duration_ms": 120
}
```

Add fields only when they are safe and useful. Prefer identifiers such as `user_id` over names, email addresses, or arbitrary request payloads.

## Log levels

| Level | Use it for |
| --- | --- |
| `DEBUG` | Developer diagnostics and internal state; usually disabled in production. |
| `INFO` | Expected lifecycle and business events: request completed, job started, user created. |
| `WARNING` | Unexpected but recoverable conditions: retry, fallback, slow query, invalid client input. |
| `ERROR` | A requested operation failed: unhandled 5xx, failed dependency call, database error. |
| `CRITICAL` | The service is unavailable, unsafe, or at material risk of data loss. |

A useful test is: “Would an operator need to investigate or be alerted?” If yes, use `ERROR` or `CRITICAL`; otherwise choose the lower level that accurately describes the operational impact.

## Python logging architecture

Python logging is a pipeline. Each layer has a separate responsibility.

| Layer | Responsibility |
| --- | --- |
| Logger | Application-facing named object that emits a `LogRecord`. |
| Filter / enrichment | Adds or rejects fields such as request ID, service name, and environment. |
| Formatter | Serializes a record as plain text or JSON. |
| Handler | Sends formatted records to stdout, a file, a queue, socket, or other destination. |
| Root logger | Fallback parent for named loggers that do not override handling. |
| Collector | Platform agent that ships stdout/file logs to a central backend. |
| Backend / UI | Stores, searches, visualizes, and alerts on logs. |

Named loggers are hierarchical. `logging.getLogger(__name__)` gives each module a natural logger name and allows targeted level configuration later.

```text
app.api.users → app.api → app → root
```

## Central configuration

Keep configuration in one module, for example:

```text
app/
├── logging/
│   ├── __init__.py
│   ├── config.py
│   └── middleware.py
└── main.py
```

Call `setup_logging()` once before the app starts serving requests. `dictConfig` is the standard declarative configuration interface.

```python
# app/logging/config.py
import logging
import os
import sys
from logging.config import dictConfig

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "plain",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn.access": {"level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
    },
}


def setup_logging() -> None:
    dictConfig(LOGGING_CONFIG)
```

```python
# app/main.py
from fastapi import FastAPI
from app.logging.config import setup_logging

setup_logging()
app = FastAPI()
```

### What the main configuration keys mean

- `version`: the `dictConfig` schema version; use `1`.
- `disable_existing_loggers`: leave `False` unless you deliberately want to disable loggers already created by dependencies such as Uvicorn.
- `formatters`: named output shapes.
- `handlers`: named destinations; a handler selects one formatter and may have its own minimum level.
- `root`: fallback logger configuration inherited by loggers that propagate upward.
- `loggers`: named overrides for application modules or dependencies.

A record must pass both the logger’s effective level and the handler’s level to be emitted. If a named logger has its own handlers, set `propagate: False` only when you intentionally want to prevent the record also reaching parent handlers; otherwise duplicate logs are easy to create.

### Multiple formatters and handlers

It is normal to use plain text locally and JSON in production, configured through different handlers or an environment-specific config. Application code does not choose a formatter or handler.

```json
"handlers": {
    "console": {"class": "logging.StreamHandler", "formatter": "plain"},
    "security": {"class": "logging.StreamHandler", "level": "WARNING", "formatter": "json"},
},
"loggers": {
    "app.auth": {
        "handlers": ["console", "security"],
        "level": "INFO",
        "propagate": False,
    },
}
```

Separate handlers are justified for audited security logs, compliance retention, or a deliberately isolated high-volume stream. For most services, one stdout handler plus fields such as `layer="db"` or `layer="auth"` is simpler and easier to operate.

## Structured JSON logging

JSON supports searching and aggregation by field. A JSON formatter from a maintained logging library can be registered in `dictConfig`; the application still uses `logging` normally.

```json
"formatters": {
    "json": {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
    },
},
"handlers": {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "json",
        "stream": "ext://sys.stdout",
    },
},
```

Be careful with custom fields in a standard text formatter. A format containing `%(request_id)s` fails if a record does not provide that field unless a filter supplies a default. JSON formatters have their own behaviour; test the chosen formatter with logs emitted both inside and outside a request.

## Request context and the enrichment layer

**Enrichment** adds reusable context to a log record so every call site does not repeat boilerplate. Typical fields are `request_id`, `trace_id`, service name, deployment environment, route, and—when safe—an actor identifier.

FastAPI middleware is an appropriate place to create request-scoped context, time the request, and emit one request-summary log. `contextvars` lets code further down the same async request obtain the current request ID without passing it through every function argument.

```python
# app/logging/context.py
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
```

```python
# app/logging/middleware.py
import logging
import time
import uuid
from fastapi import Request
from app.logging.context import request_id_var

logger = logging.getLogger("app.middleware")


async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000)
        status_code = response.status_code if response is not None else 500
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )
        request_id_var.reset(token)
        if response is not None:
            response.headers["X-Request-ID"] = request_id
```

```python
app.middleware("http")(logging_middleware)
```

The `finally` block records a summary even when downstream code raises. Exception handling is still responsible for converting unhandled failures into an appropriate response and logging traceback details once; avoid accidental duplicate error logs across middleware and exception handlers.

For automatic context on every record, add a `logging.Filter` that reads `request_id_var` and sets a default `record.request_id`. Configure that filter on the handler. This is preferable to manually passing the same field in every `logger.info()` call, but explicit event-specific fields still belong at the call site.

## Endpoint, business, database, and security logging

Use middleware for request lifecycle fields. Use explicit logging inside endpoint and service code for meaningful business events.

```python
import logging

logger = logging.getLogger(__name__)


def create_user(user_id: str) -> None:
    logger.info(
        "user_creation_started",
        extra={"layer": "business", "user_id": user_id},
    )
    # Perform the operation.
    logger.info(
        "user_created",
        extra={"layer": "business", "user_id": user_id},
    )
```

Use summaries and durations rather than raw payloads. For database calls, log failures and slow operations, but parameterized SQL values can contain secrets. For authentication and authorization, log the outcome and reason category, never passwords, bearer tokens, cookies, or private keys.

## Timing: middleware, decorators, and metrics

- **Request latency** belongs in middleware because it surrounds the complete request.
- **A specific expensive operation** can use a decorator or an explicit timing block.
- **Metrics** are often better than logs for high-cardinality or high-frequency latency monitoring; logs retain the contextual diagnostic trail.

Use `functools.wraps` in decorators so FastAPI and debugging tools retain the wrapped function’s metadata. Use separate wrappers for synchronous and asynchronous functions.

```python
import functools
import logging
import time

logger = logging.getLogger(__name__)


def measure_sync(operation: str):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                logger.info(
                    "operation_completed",
                    extra={
                        "operation": operation,
                        "duration_ms": round((time.perf_counter() - start) * 1000),
                    },
                )
        return wrapper
    return decorator
```

```python
@measure_sync("db.save_user")
def save_user(user_id: str) -> None:
    pass
```

Decorators are optional. They are good for a narrowly defined cross-cutting concern, but can hide behaviour and make customization or debugging harder. Do not use a decorator as a replacement for request middleware or for clear, explicit business-event logs.

## Uvicorn and FastAPI logs

Uvicorn supplies loggers such as `uvicorn.access` and `uvicorn.error`. Keep them enabled unless you have a deliberate replacement; configure their levels and output consistently with application logs. Avoid attaching overlapping handlers to both them and the root logger unless you understand propagation, or each message may appear twice.

## Shipping and storing logs

The application should emit logs; the platform should collect, retain, and expose them. A common pipeline is:

```text
FastAPI → stdout/stderr → collector/agent → central log store → query and alert UI
```

Collectors include tools such as Fluent Bit, Vector, Filebeat, or a cloud provider’s logging agent. Backends include Loki/Grafana, OpenSearch/Elasticsearch/Kibana, CloudWatch, Datadog, Splunk, and other managed observability services. Centralized logging lets operators trace one request across many services by `request_id`, `trace_id`, `service`, and environment.

If your platform already collects container stdout, do not add an application-managed file solely to feed another collector. If you lack permission to access Docker internals and need local collection, a shared project-volume file can be practical, but use rotation and document the retention limit.

### File rotation when files are required

Never leave a plain `FileHandler` to grow forever. Rotate by size or time and cap old files.

```json
"handlers": {
    "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": "/app/logs/app.log",
        "formatter": "json",
        "maxBytes": 104857600,
        "backupCount": 10,
    },
},
```

A file-tailing collector should track positions and be configured to follow the active file and its rotation pattern. Confirm collector-specific rotation behaviour in its documentation; do not assume all agents behave identically.

## Runtime log-level changes

A deployment environment variable is the simplest controlled mechanism:

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app
```

You may change a logger programmatically for short-lived diagnosis:

```python
import logging

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("app.db").setLevel(logging.DEBUG)
```

An administrative endpoint can do this only when it is strongly authenticated, audited, scoped to named loggers, and ideally time-limited. Exposing a public “set any log level” endpoint is a security and operational risk.

## Production checklist

- [ ] Configure logging once, before serving requests.
- [ ] Use `logging.getLogger(__name__)`, not `print()`.
- [ ] Emit structured JSON in deployed environments.
- [ ] Add request/correlation IDs and return the request ID to callers.
- [ ] Log request summaries, meaningful business events, slow/failing dependencies, and security outcomes.
- [ ] Never log passwords, tokens, secrets, or unreviewed payloads.
- [ ] Send logs to stdout/stderr when the platform collects them; rotate and cap files when file logging is required.
- [ ] Avoid duplicate handlers and test configuration with Uvicorn logs.
- [ ] Set timeouts, retries, and error handling so failures produce one useful error record with traceback/context.
- [ ] Centralize logs and verify operators can query by request ID, service, environment, level, and event name.
