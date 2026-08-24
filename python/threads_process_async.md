# Threads, processes, and `asyncio` in Python

Threads, processes, and `asyncio` solve different problems. They can improve throughput and responsiveness, but none is automatically “better CPU utilisation”. Choose based on the work being done and the libraries available.

## 1. Decision table

| Workload | First choice | Why |
| --- | --- | --- |
| Many blocking synchronous I/O calls (`requests`, file access, legacy SDK) | Thread pool | Threads can wait independently without blocking the caller. |
| Many async I/O calls (`httpx.AsyncClient`, async database driver) | `asyncio` | One event loop can coordinate many waiting operations with low overhead. |
| Pure-Python CPU-heavy work (image transforms, simulations, parsing) | Process pool or worker system | Separate processes can run on multiple CPU cores despite the GIL. |
| Long, retryable, durable jobs | Queue/worker service | Requests should not hold web-server workers for minutes or hours. |
| Numerical/native code that releases the GIL | Benchmark | Threads may parallelize effectively; the library determines this. |

## 2. The concepts that matter

### Concurrency versus parallelism

- **Concurrency** means multiple operations make progress during the same period, usually by waiting independently.
- **Parallelism** means work executes at the same time on multiple CPU cores.
- **Throughput** is completed work per unit time; **latency** is the time for one item to finish.
- **Backpressure** limits queued or in-flight work so a fast producer cannot exhaust memory, connections, or downstream capacity.

### The GIL

In standard CPython, the Global Interpreter Lock means only one thread executes Python bytecode at a time. Therefore:

- Threads are excellent for waiting on blocking I/O.
- Threads usually do not speed up pure-Python CPU work.
- Separate processes bypass the GIL because each has its own interpreter and memory space.
- Native libraries can release the GIL; measure before assuming threads cannot help.

## 3. Threads: shared memory, best for blocking I/O

Threads run inside one process and share its memory. Sharing makes communication easy, but shared mutable state requires synchronization (`Lock`, `Queue`, or a carefully designed ownership model).

Use `ThreadPoolExecutor` rather than starting one thread per item:

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def fetch_status(url: str) -> tuple[str, int]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return url, response.status_code

def fetch_all(urls: list[str]) -> list[tuple[str, int]]:
    with ThreadPoolExecutor(max_workers=20) as executor:
        return list(executor.map(fetch_status, urls))
```

The pool has a fixed number of workers. Extra work waits in a queue instead of creating more operating-system threads.

### Thread-pool rules

- Reuse a pool for related work; creating a pool per item defeats pooling.
- Set request, connect, and read timeouts for all network calls.
- Pick `max_workers` from measurements and downstream limits, not from an arbitrary large number.
- A `Future.cancel()` only cancels work that has not started; Python cannot safely kill a running thread.
- Protect shared state, or preferably send results back to one owner through a thread-safe queue.

For an unbounded or very large input stream, do not eagerly call `submit()` millions of times. Use bounded batches, a queue with worker threads, or Python 3.14+'s `Executor.map(..., buffersize=...)` to cap in-flight submissions.

## 4. Processes: isolated memory, best for CPU-bound work

Processes have separate interpreters and memory, enabling true multi-core execution. The trade-offs are startup cost, memory overhead, and serialization: arguments and results must generally be picklable.

```python
from concurrent.futures import ProcessPoolExecutor

def count_primes(limit: int) -> int:
    count = 0
    for candidate in range(2, limit):
        if all(candidate % divisor for divisor in range(2, int(candidate**0.5) + 1)):
            count += 1
    return count

def main() -> None:
    limits = [50_000, 60_000, 70_000, 80_000]
    with ProcessPoolExecutor(max_workers=4) as executor:
        counts = list(executor.map(count_primes, limits))
    print(counts)

if __name__ == "__main__":
    main()
```

### Process-pool rules

- Define worker functions at module level. Lambdas, local functions, and REPL-defined functions are often not picklable.
- Protect process creation with `if __name__ == "__main__":`, especially on Windows and macOS, and with `spawn`/`forkserver` start methods.
- Avoid moving large Python objects between processes repeatedly; serialization can erase the expected speedup.
- Keep worker inputs and outputs small, or use shared memory / files / object storage deliberately.
- For long iterables, `ProcessPoolExecutor.map(..., chunksize=N)` can reduce scheduling overhead; benchmark the chunk size.
- Use a context manager so workers shut down cleanly.

Processes are not a good default for network calls. Their startup, memory, and IPC costs are usually unnecessary for I/O-bound work.

## 5. `asyncio`: cooperative concurrency for async I/O

`asyncio` runs tasks on an event loop. A task gives other tasks a chance to run only when it reaches an `await` on an awaitable operation.

```python
import asyncio

async def fetch_one() -> str:
    await asyncio.sleep(0.1)  # Represents non-blocking I/O.
    return "done"

async def main() -> None:
    results = await asyncio.gather(fetch_one(), fetch_one(), fetch_one())
    print(results)

asyncio.run(main())
```

`async def` alone does not make synchronous code safe. Calling `requests.get()`, `time.sleep()`, a synchronous database driver, or a CPU-heavy loop inside an async function blocks the event loop.

### Async HTTP with bounded concurrency

Reuse one async client and limit in-flight requests. A semaphore limits active requests, but a worker queue also prevents creating millions of task objects at once:

```python
import asyncio
import httpx

async def fetch_url(client: httpx.AsyncClient, url: str) -> tuple[str, int]:
    response = await client.get(url)
    response.raise_for_status()
    return url, response.status_code

async def worker(
    queue: asyncio.Queue[str | None],
    client: httpx.AsyncClient,
    results: list[tuple[str, int]],
) -> None:
    while True:
        url = await queue.get()
        try:
            if url is None:
                return
            results.append(await fetch_url(client, url))
        finally:
            queue.task_done()

async def fetch_many(urls: list[str], concurrency: int = 20) -> list[tuple[str, int]]:
    queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=concurrency * 2)
    results: list[tuple[str, int]] = []
    timeout = httpx.Timeout(15.0, connect=3.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        workers = [
            asyncio.create_task(worker(queue, client, results))
            for _ in range(concurrency)
        ]
        for url in urls:
            await queue.put(url)  # Waits when the queue is full: backpressure.
        for _ in workers:
            await queue.put(None)
        await queue.join()
        await asyncio.gather(*workers)

    return results
```

`asyncio.gather()` schedules awaitables concurrently and returns results in input order. For Python 3.11+, prefer `asyncio.TaskGroup` when tasks are one failure unit: if one task fails, it cancels remaining siblings and raises an `ExceptionGroup` after cleanup.

## 6. Combining async code with blocking code

An async endpoint or program sometimes must call a blocking library. Do not call it directly in the event-loop thread. Use `asyncio.to_thread()` for blocking I/O or synchronous libraries:

```python
import asyncio

def blocking_metric(text: str) -> float:
    return legacy_metric_client.score(text)

async def score(text: str) -> float:
    return await asyncio.to_thread(blocking_metric, text)
```

Pass the callable and its arguments separately:

```python
async def correct() -> object:
    return await asyncio.to_thread(function, arg1, arg2)
```

This is wrong because it evaluates `function` before the thread receives it:

```python
async def incorrect() -> object:
    return await asyncio.to_thread(function(arg1, arg2))
```

`to_thread()` preserves event-loop responsiveness, but it does not make pure-Python CPU work parallel. For CPU-bound work from async code, use a managed process pool:

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

PROCESS_POOL = ProcessPoolExecutor(max_workers=4)

def expensive_transform(value: int) -> int:
    return value * value

async def transform(value: int) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(PROCESS_POOL, expensive_transform, value)
```

Create and shut down long-lived executors at an application lifecycle boundary, not once per request.

## 7. FastAPI guidance

| Endpoint implementation | Use when |
| --- | --- |
| `async def` | Dependencies provide async APIs (`httpx.AsyncClient`, async DB driver, async SDK). |
| Plain `def` | The endpoint is entirely blocking; FastAPI runs it in its threadpool. |
| `async def` + `asyncio.to_thread()` | Mostly async endpoint with one clearly scoped blocking library call. |
| Background worker / job queue | The job is CPU-heavy, long-running, retryable, or must survive a web-server restart. |

Do not use `asyncio.run()` inside a FastAPI request; the server already has an event loop. Use `await`.

For a remote API, prefer an async client if the library offers one. If a library's synchronous method performs remote I/O internally, it is still synchronous from your code's perspective; use `to_thread()` or run it from a normal `def` endpoint.

## 8. Timeouts, retries, cancellation, and errors

Concurrency without resource control is fragile.

- Set client timeouts. A connection timeout and a total/read timeout are different failure modes.
- Limit concurrency based on server capacity, connection pools, quotas, and rate limits.
- Retry only transient failures, with exponential backoff and jitter. Do not blindly retry non-idempotent operations.
- Make operations idempotent where possible, especially for queues and HTTP retries.
- Cancellation is expected during shutdown, client disconnects, and structured-concurrency failure. Release resources in `finally` blocks and do not swallow `asyncio.CancelledError`.
- Use context managers for clients, pools, files, and locks.
- Capture errors per item when partial success is acceptable; otherwise let the batch fail as one unit.

## 9. Common mistakes

| Mistake | Better approach |
| --- | --- |
| One thread, process, or task for every item | Use a fixed-size pool or bounded queue. |
| Thread pool for pure-Python CPU work | Use processes or an external worker system. |
| Process pool for many tiny operations | Batch work; IPC overhead can dominate. |
| Blocking call inside `async def` | Use an async library or `asyncio.to_thread()`. |
| `await` a normal return value | Await only coroutine/Task/Future-like objects. |
| Share mutable state between threads without coordination | Use ownership, immutable data, queues, or locks. |
| Send huge objects repeatedly to processes | Minimize serialization and data movement. |
| Create an HTTP client for each request | Reuse a client/session for a logical workload or app lifecycle. |
| Unbounded retry and unbounded concurrency | Add budgets, timeouts, rate limits, and backpressure. |

## 10. Final checklist

1. Classify each task as async I/O, blocking I/O, or CPU-bound.
2. Start with the simplest model that matches the dependency APIs.
3. Bound workers, in-flight tasks, connections, and queues.
4. Define timeouts, retries, cancellation, and partial-failure behavior.
5. Measure throughput, latency, CPU, memory, and downstream errors under realistic load.
6. Move long-running or durable work out of request handlers into worker infrastructure.
7. Revisit the design when the workload or dependency library changes.

## References

- [Python: `concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html)
- [Python: `multiprocessing`](https://docs.python.org/3/library/multiprocessing.html)
- [Python: `asyncio` Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- [FastAPI: Concurrency and `async` / `await`](https://fastapi.tiangolo.com/async/)
