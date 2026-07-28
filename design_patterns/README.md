# Design Patterns for AI/ML Development

Individual pattern reference files — each self-contained with motivation, problem, solution, and code.

## Patterns

| File | Pattern | One-Line Summary |
|------|---------|-----------------|
| [strategy_pattern.md](strategy_pattern.md) | Strategy | Multiple ways to do the same job — let the caller pick |
| [adapter_pattern.md](adapter_pattern.md) | Adapter | Wrap something incompatible to make it fit your interface |
| [circuit_breaker_pattern.md](circuit_breaker_pattern.md) | Circuit Breaker + Retry | Retry for blips, stop hammering when it's dead |
| [cqrs_pattern.md](cqrs_pattern.md) | CQRS | Separate reads from writes — they have different needs |
| [factory_pattern.md](factory_pattern.md) | Factory | Centralize object creation from configuration |
| [repository_pattern.md](repository_pattern.md) | Repository | Hide storage behind an interface — test without infra |
| [decorator_pattern.md](decorator_pattern.md) | Decorator | Add behaviors (logging, caching) by wrapping in layers |

## Quick Decision Guide

```
"I need to swap algorithms"                    → Strategy
"I need to integrate a third-party lib"        → Adapter
"External service is flaky"                    → Circuit Breaker + Retry
"Training is killing my inference performance" → CQRS
"I need to create objects from config"         → Factory
"I can't test because I need real DB/S3"       → Repository
"My class does too many things"                → Decorator
```

## Also See

- `../design_patterns_ml.md` — Original overview file with all patterns in one place


