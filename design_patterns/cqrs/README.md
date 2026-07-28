# CQRS Pattern — ML System Implementation

## What is CQRS?

**Command Query Responsibility Segregation** separates the code that changes data (commands) from the code that reads data (queries). In an ML context:

- **Command Side**: Training models, ingesting data — slow, batch, GPU-heavy
- **Query Side**: Serving predictions, reading metrics — fast, real-time, CPU-optimized

## Why CQRS for ML?

| Concern | Command Side (Training) | Query Side (Inference) |
|---------|------------------------|----------------------|
| Frequency | Daily/weekly | 10,000 req/sec |
| Latency | Hours OK | Must be < 50ms |
| Resources | GPU, high memory | CPU, low memory |
| Scaling | 1 instance | 50+ instances |
| Failure | Retry tomorrow | User error NOW |

Without CQRS, training locks the DB, hogs memory, and kills inference latency.

## Event Sync Mechanism

The **EventBus** bridges command and query sides:

```
Command Handler              Query Handler
     |                            |
     | 1. Train model             |
     | 2. Save to write store     |
     | 3. Publish "model_trained" |
     |         ─────────────────► |
     |                            | 4. Reload model into memory
     |                            | 5. Serve predictions
```

The event carries metadata (model name, metrics, path). The query side reacts
by loading the new model artifact into memory for fast inference.

In production, replace the in-process EventBus with:
- **Redis Pub/Sub** — low latency, simple
- **Kafka** — durable, ordered, high throughput
- **AWS SQS/SNS** — managed, scalable

## Project Structure

```
cqrs/
├── README.md
├── src/
│   ├── __init__.py
│   ├── events.py          # Event dataclass + EventBus
│   ├── command_side.py    # Commands, write stores, command handlers
│   ├── query_side.py      # Queries, read stores, query handlers
│   └── ml_system.py       # Wires everything together + demo
└── tests/
    ├── __init__.py
    └── test_cqrs.py       # Unit + integration tests
```

## Running

```bash
# Run the demo
cd design_patterns/cqrs
python -m src.ml_system

# Run tests
pytest tests/ -v
```

## Key Design Decisions

1. **EventBus is synchronous** — simple for learning. In production, use async/message queues.
2. **Write store ≠ Read store** — command side saves to ModelStore; query side reads from ReadModelStore. The event triggers the sync.
3. **Query handlers subscribe on init** — they auto-react to events without explicit wiring from the caller.
4. **MLSystem is the composition root** — it creates all components and wires the event subscriptions.

## Flow Summary

```
TrainModelCommand → TrainModelHandler → ModelStore (write)
                                      → EventBus.publish("model_trained")
                                            ↓
                              PredictionQueryHandler._on_model_trained()
                              MetricsQueryHandler._on_model_trained()
                              MLSystem._sync_model_to_read_store()
                                            ↓
                              ReadModelStore now has the new model
                                            ↓
PredictionQuery → PredictionQueryHandler → ReadModelStore (read) → result
```


