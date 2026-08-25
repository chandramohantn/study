# Event-Driven Systems and Polling in Python

Event-driven and polling systems both respond to change, and a single system can use both. The confusion usually comes from mixing three independent questions:

1. **What does the application model?** A state snapshot, or a record that something happened?
2. **Who initiates delivery?** The producer/server pushes, or the consumer pulls?
3. **What happens on the wire?** Repeated short requests, a held long-poll request, a persistent stream, or OS I/O readiness notifications?

Do not infer the answer to one question from another. A Kafka consumer calls `poll()` (pull delivery) and can still be part of an event-driven application. An `asyncio` event loop can use OS readiness polling internally and still drive application callbacks from events.

## The compact distinction

**Polling** is a consumer-controlled strategy for repeatedly asking a source for data or for a changed state. **Event-driven design** is a producer/system-controlled strategy in which a meaningful occurrence is represented as an event and consumers react to it.

```text
Polling state:       consumer ──"what is true now?"──> source
Event consumption:   producer ──"this happened"──> event channel ──> consumer
```

These often occur together. For example, a service can publish `order.created` events to a broker; consumers pull batches from that broker with long-poll fetch requests. The event is still an explicit fact in the domain, even though the delivery protocol is pull-based.

## Essential vocabulary

| Term | Meaning |
| --- | --- |
| **State** | A current snapshot, such as `order.status = "paid"`. It can be overwritten. |
| **Event** | An immutable record that something happened, such as `order.paid`. It is normally named in the past tense and includes context. |
| **Producer / publisher** | Writes an event or makes data available. |
| **Consumer / subscriber** | Receives an event and performs work in response. |
| **Broker** | An intermediary that stores/routes messages, often giving durability, buffering, and fan-out. |
| **Topic / queue / stream** | A channel for messages. The exact delivery and retention semantics depend on the product. |
| **Offset / cursor** | A consumer’s position in an ordered log or stream. |
| **Acknowledgement / commit** | A durable statement of how far a consumer has processed. |
| **Backpressure** | A mechanism that prevents a fast producer from overwhelming a slow consumer. |

An event is not automatically the source of truth. Many systems store current state in a database and publish events about its changes. Event sourcing is the special case where the event history itself is the authoritative record and state is reconstructed from it.

## Polling, long polling, streaming, and push

### Short polling

The client sends a request at an interval. The server replies immediately, even if there is no change.

```python
import time


def fetch_status() -> str:
    # Placeholder for an HTTP request or database query.
    return "pending"


while True:
    status = fetch_status()
    if status == "ready":
        print("start work")
        break
    time.sleep(5)
```

Advantages: simple, works with almost any HTTP API, and the client controls load. Costs: repeated empty work and latency bounded by the chosen interval. It also needs careful handling of missed transitions: comparing only the current state may not tell you every change that occurred.

### Long polling

The client sends a request, but the server holds it until data arrives or a timeout expires. The client then immediately issues the next request.

```text
consumer ── request ──> broker/server
consumer <── response when event is ready, or timeout ── broker/server
consumer ── next request ──> broker/server
```

This remains **pull-based polling at the transport level**, but avoids most empty responses and reduces latency. The waiting client thread or async task is blocked/suspended on I/O, not burning CPU. It is normal for a consumer loop to run forever.

### Persistent streaming or server push

With WebSockets, Server-Sent Events, gRPC streaming, or a message broker’s push delivery, a connection remains open and the producer/server sends records as they become available. Webhooks are a different push form: the producer sends an HTTP request to a consumer-owned endpoint for each event.

Push reduces the need for repeated client requests, but it does not eliminate reliability concerns. Receivers can be offline or slow; delivery needs retries, buffering, acknowledgements, and authentication.

### Comparison

| Mechanism | Who starts each transfer? | Idle behaviour | Typical risk / trade-off |
| --- | --- | --- | --- |
| Short polling | Consumer | Repeated requests and empty replies | Extra traffic and interval latency |
| Long polling | Consumer | One request waits, then is renewed | Reconnect/timeout handling |
| Persistent stream | Server after connection setup | Connection stays open | Connection lifecycle and backpressure |
| Webhook | Producer | Sends a request per event | Receiver availability, retries, duplicate delivery |
| Broker pull (Kafka-style) | Consumer | Fetch may wait and return batches | Consumer lag and offset management |

## Kafka-style log consumption

Kafka is an important counterexample to the simplistic equation “`poll()` means a polling architecture.” A Kafka consumer does use a pull API, and a client application commonly has a loop. It reads records from its assigned partitions beginning at its current position.

```text
producer appends event at offset 106
broker retains ordered partition log: ... 104, 105, 106
consumer has processed through 105
consumer fetches from 106 → receives the next available records
consumer processes records → commits a safe offset when appropriate
```

Conceptually, `poll()` coordinates the consumer, heartbeats/group membership, local buffering, and network fetches. A fetch names partitions and positions and asks for available records. If the configured minimum data is not available, a broker may wait up to a configured maximum before responding; this gives batching and long-poll-like behaviour.

A consumer does not need a separate Python thread per topic. Subscription leads to assignment of **partitions**, and one consumer client can fetch data for multiple assigned partitions. The library can multiplex network work; the application gets batches from `poll()` and processes them. Exact API behaviour and thread-safety are client-library-specific, so follow that client’s documentation.

### Consumer loop: what is blocked?

```python
# Pseudocode; use the configuration and API of your Kafka client.
while running:
    records = consumer.poll(timeout=1.0)
    for record in records:
        handle(record)
    consumer.commit_processed_offsets()
```

During a blocking fetch, the **calling thread** waits on I/O. That does not consume a CPU core, and the operating system can run other threads and processes. It does mean this particular synchronous thread cannot simultaneously execute other Python work. Options are:

- Keep this one thread focused on consuming and hand work to a bounded worker pool or queue.
- Use an async-compatible client and `await` its I/O.
- Run additional consumers in the same consumer group when partition-level parallelism is available.

Do not process records for too long without respecting the consumer client’s liveness/polling requirements. Slow processing, rebalances, retry policy, and offset-commit strategy must be designed together.

## Event-driven architecture: what matters beyond transport

An event-driven system is not merely a `while True` loop or a callback. It has a clear event contract and reaction path:

```text
business action
  → durable state change
  → publish event
  → broker / delivery channel
  → consumer reaction
  → acknowledgement or recorded progress
```

A useful event includes an event ID, type and version, occurrence time, producer/aggregate identity, correlation or causation ID when relevant, and the minimum data needed by consumers. Avoid treating a mutable database row or an ambiguous “data changed” message as a complete event contract.

### Events, commands, and queries

| Message | Meaning | Example |
| --- | --- | --- |
| **Command** | A request to do something; it may be rejected. | `CreateOrder` |
| **Event** | A fact that already happened. | `OrderCreated` |
| **Query** | A request for current information. | `GetOrderStatus` |

This distinction makes ownership clearer. A producer owns its facts; a consumer owns how it reacts. Consumers should not assume an event is a command they must execute exactly once.

## Python patterns

### In-process events with `asyncio.Queue`

A queue is useful within one Python process. It provides buffering and backpressure via `maxsize`, but it is not durable: a process crash loses in-memory events.

```python
import asyncio


async def producer(events: asyncio.Queue[str | None]) -> None:
    for order_id in ("A-101", "A-102"):
        await events.put(f"order.created:{order_id}")
    await events.put(None)  # Demo shutdown sentinel.


async def consumer(events: asyncio.Queue[str | None]) -> None:
    while True:
        event = await events.get()
        try:
            if event is None:
                return
            print(f"handle {event}")
        finally:
            events.task_done()


async def main() -> None:
    events: asyncio.Queue[str | None] = asyncio.Queue(maxsize=100)
    async with asyncio.TaskGroup() as group:
        group.create_task(producer(events))
        group.create_task(consumer(events))


asyncio.run(main())
```

The consumer is “waiting for an event,” but it does not busy-loop: `await events.get()` suspends the task until an item becomes available, letting the event loop run other tasks.

### Readiness-driven socket I/O

At a lower level, an `asyncio` event loop commonly waits for the operating system to report that a socket is readable or writable. On Unix this uses a selector-based mechanism; on Windows the default event loop uses I/O completion ports. This is event-driven application scheduling even though some OS APIs are historically called “poll” or “select.”

```python
import asyncio


async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    data = await reader.readline()  # Suspend until socket data is available.
    writer.write(data.upper())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main() -> None:
    server = await asyncio.start_server(serve, "127.0.0.1", 8888)
    async with server:
        await server.serve_forever()


# Run deliberately when you want to start the demo server:
# asyncio.run(main())
```

## Reliability: the mandatory part of event-driven design

The transport is only the beginning. Production systems must define how they behave under retries, crashes, and duplicate delivery.

1. **At-most-once**: an event may be lost, but is not intentionally redelivered. Low duplication, weaker reliability.
2. **At-least-once**: an event is retried until acknowledged. Stronger delivery, but consumers can receive duplicates.
3. **Exactly-once**: only meaningful when its boundaries are specified. It usually requires coordinated transactional/idempotent design and is much harder across external side effects.
4. **Idempotency**: safely applying the same event more than once has the same result as applying it once. Use event IDs, deduplication storage, or naturally idempotent operations.
5. **Ordering**: ordering is often guaranteed only within a partition/key, not across an entire topic or all consumers.
6. **Backpressure and limits**: bound queues, batches, concurrency, and retries. A faster producer must not create unlimited memory growth or overload a downstream service.
7. **Failure handling**: define retryable versus permanent errors, retry with backoff and jitter, and route poison events to an observable dead-letter workflow when appropriate.
8. **Publish consistency**: if a database update and event publish must both happen, consider the transactional outbox pattern or another explicit consistency mechanism; do not silently assume two independent writes are atomic.
9. **Observability**: track event age, consumer lag, queue depth, success/failure rate, retries, duplicate rate, and correlation IDs.

## Choosing a design

| Situation | Start with | Why |
| --- | --- | --- |
| A simple external API exposes only current state | Periodic polling, conditional requests, or scheduled sync | It is the available contract; make interval and missed-change behaviour explicit. |
| A remote service can call your endpoint reliably | Webhook / push event | Lower latency and no empty checks; secure and retry it. |
| Several services need durable, replayable events | Brokered event stream | Decoupling, buffering, fan-out, retention, and independent consumers. |
| High-volume client updates to a connected UI | WebSocket or SSE | Persistent connection and low-latency delivery. |
| Work inside one Python process | `asyncio.Queue` or `queue.Queue` | Simple hand-off and bounded local backpressure; no crash durability. |
| Change data from a database | CDC or an outbox-backed event publisher | Captures changes without each consumer scanning database state. |

There is no universal winner. Polling is often the simplest and most robust solution at low scale. Event-driven systems earn their added operational complexity when latency, fan-out, decoupling, reliable history, or high change volume matter.

## Common misconceptions

- **“A `poll()` method means the system is not event-driven.”** No. It describes a pull API; the application can still consume explicit events.
- **“Push is always better.”** No. Pull lets consumers control rate and batch size, which is valuable for backpressure.
- **“Events guarantee no data loss.”** No. Durability, acknowledgements, retention, offsets, and failure policy determine that.
- **“One event equals one action exactly once.”** Usually no. Expect duplicates and make handlers idempotent.
- **“An async wait is a busy loop.”** No. `await` generally suspends the task until readiness; CPU is available for other work.
- **“Event-driven means no state.”** No. Events and state frequently coexist; the question is what is authoritative and how changes propagate.

## Questions to explore next

1. How would I use ETags, `If-Modified-Since`, or a change token to make a polling API cheaper and more correct?
2. What delivery guarantee does a particular broker/client really provide, and where can duplicates still appear?
3. How would I design an idempotency key and storage policy for a payment or order event?
4. What should happen if a webhook consumer returns a 500, times out, or receives the same event three times?
5. How do consumer lag, batch size, processing time, and partition count determine throughput in a Kafka consumer group?
6. How would I implement backpressure when a producer is faster than a database-writing consumer?
7. What are the failure windows around “write to database, then publish event,” and how does the transactional outbox pattern close them?
8. When does a persistent stream become less suitable than long polling—for example through corporate proxies, mobile clients, or connection limits?
9. How do `select`, `poll`, `epoll`, `kqueue`, and I/O completion ports differ, and which one does my runtime use?
10. Can I trace one event end-to-end with a correlation ID and measure its production time, delivery time, processing time, and final side effect?
11. How would I replay historical events safely without causing duplicate external side effects?
12. Which parts of my current system truly need events, and which are simpler, clearer, and safer as periodic polling?

## Primary references

- [Python `asyncio` event loop documentation](https://docs.python.org/3/library/asyncio-eventloop.html)
- [Python `asyncio` queues](https://docs.python.org/3/library/asyncio-queue.html)
- [Python `asyncio` Tasks and structured concurrency](https://docs.python.org/3/library/asyncio-task.html)
- [Apache Kafka consumer configuration](https://kafka.apache.org/documentation/#consumerconfigs)
- [Apache Kafka design documentation](https://kafka.apache.org/documentation/#design)
