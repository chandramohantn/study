# Python async functions and `asyncio`

`asyncio` provides **cooperative concurrency** for work that spends time waiting: HTTP requests, database calls, file I/O, queues, and network services. It is not a way to make ordinary Python CPU work run in parallel.

The core question is not “should this function be `async`?” It is:

> **Does this code reach an `await` that yields control while it waits?**

If yes, asynchronous code can let other tasks make progress. If no, it blocks the event loop even when it is inside an `async def` function.

## 1. Mental model

| Term | Meaning |
| --- | --- |
| Coroutine function | A function declared with `async def`. |
| Coroutine object | Returned when a coroutine function is called; it has not run to completion yet. |
| Awaitable | An object usable with `await`, such as a coroutine, `Task`, or `Future`. |
| Task | A scheduled coroutine that the event loop can run concurrently with other tasks. |
| Event loop | The scheduler that resumes tasks when the operation they are waiting for is ready. |
| Blocking call | A call that occupies the event-loop thread until it returns. |

```python
import asyncio

async def fetch_name() -> str:
    await asyncio.sleep(0.1)
    return "Ada"

async def main() -> None:
    coroutine = fetch_name()       # Creates a coroutine object; it does not finish the work.
    name = await coroutine         # Runs it until completion, yielding at await points.
    print(name)

asyncio.run(main())
```

Call `asyncio.run()` at a top-level program boundary. Do not call it from a FastAPI endpoint, Jupyter cell that already has a running loop, or another coroutine; use `await` there instead.

## 2. `async def` does not make code non-blocking by itself

This endpoint blocks the event loop because `time.sleep()` is synchronous:

```python
import time
from fastapi import FastAPI

app = FastAPI()

@app.get("/bad")
async def bad() -> dict[str, str]:
    time.sleep(2)                  # Blocks every task on this event loop.
    return {"status": "done"}
```

Use an asynchronous library for asynchronous I/O:

```python
import asyncio

@app.get("/good")
async def good() -> dict[str, str]:
    await asyncio.sleep(2)         # Yields control while waiting.
    return {"status": "done"}
```

`asyncio.sleep()` only simulates waiting. It is not a substitute for CPU work.

## 3. Concurrency is not parallelism

- **Concurrency**: several tasks make progress by taking turns while they wait. `asyncio` is excellent for I/O-bound work.
- **Parallelism**: work happens at the same time on multiple CPU cores. Use multiple processes, a job queue, or native code that releases the GIL for CPU-bound work.

A long pure-Python loop inside `async def` still monopolizes the event-loop thread. Adding `async` or sprinkling `await asyncio.sleep(0)` into CPU work does not turn it into a scalable compute solution.

## 4. Awaiting one operation versus starting several

This is sequential because the second call does not start until the first one finishes:

```python
async def fetch_sequentially() -> None:
    first = await fetch_one()
    second = await fetch_two()
```

Use `asyncio.gather()` when independent operations should run concurrently:

```python
async def fetch_concurrently() -> list[object]:
    return await asyncio.gather(
        fetch_one(),
        fetch_two(),
        fetch_three(),
    )
```

`gather()` returns results in input order. By default, the first exception is propagated, but already-running sibling tasks are not automatically cancelled. Use `return_exceptions=True` only when each result is intentionally handled as either a value or an exception.

For new Python 3.11+ code, prefer `asyncio.TaskGroup` when sibling tasks form one unit of work:

```python
import asyncio

async def load_dashboard() -> tuple[dict, dict]:
    async with asyncio.TaskGroup() as group:
        profile_task = group.create_task(fetch_profile())
        orders_task = group.create_task(fetch_orders())

    # The context exits only after both tasks finish.
    # If one fails, TaskGroup cancels the remaining sibling task.
    return profile_task.result(), orders_task.result()
```

Use `asyncio.create_task()` only when you deliberately need a background task. Keep a reference to it and define how failures are observed; otherwise exceptions can be lost and work can outlive the request that started it.

## 5. Calling several FastAPI APIs concurrently

Use one shared `httpx.AsyncClient` for a logical batch of requests. Creating a client per request loses connection pooling.

```python
import asyncio
import httpx

async def post_json(client: httpx.AsyncClient, url: str, payload: dict) -> dict:
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json()

async def call_all(payload: dict) -> list[dict]:
    urls = [
        "http://localhost:8000/api1",
        "http://localhost:8000/api2",
        "http://localhost:8000/api3",
    ]
    timeout = httpx.Timeout(15.0, connect=3.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        return await asyncio.gather(*(post_json(client, url, payload) for url in urls))

if __name__ == "__main__":
    print(asyncio.run(call_all({"input": "example"})))
```

Concurrency should be bounded when a batch may be large. Otherwise the client can exhaust connections or overload the downstream service:

```python
async def bounded_post(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    url: str,
    payload: dict,
) -> dict:
    async with semaphore:
        return await post_json(client, url, payload)

async def call_many(urls: list[str], payload: dict) -> list[dict]:
    semaphore = asyncio.Semaphore(10)
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await asyncio.gather(
            *(bounded_post(semaphore, client, url, payload) for url in urls)
        )
```

## 6. FastAPI: choose `async def` or `def` based on the dependency

Use `async def` when the endpoint calls awaitable libraries:

```python
from fastapi import APIRouter
import httpx

router = APIRouter()

@router.post("/score")
async def score(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post("https://scoring.example/api", json=payload)
        response.raise_for_status()
    return response.json()
```

Use a normal `def` endpoint when its work is entirely blocking and synchronous. FastAPI runs normal path-operation functions in its threadpool. Alternatively, keep an `async def` endpoint and explicitly offload one blocking call with `asyncio.to_thread()`.

Do not use `async def` merely because an endpoint is slow. The right choice depends on whether its dependencies are async or blocking.

## 7. Integrating a synchronous metric library

A function that returns a `float` is not awaitable:

```python
score = metric.measure(test_case)  # A regular value, not a coroutine.
```

This is invalid:

```python
async def incorrect() -> float:
    return await metric.measure(test_case)  # TypeError at runtime if the method returns float.
```

If the library exposes only a blocking synchronous API—even if it performs remote I/O internally—offload the complete blocking call so it does not block the event loop:

```python
import asyncio
from fastapi import APIRouter, HTTPException

router = APIRouter()

class MetricService:
    def summary_metric(
        self,
        user_input: str,
        output: str,
        assessment_questions: list[str],
    ) -> float:
        test_case = LLMTestCase(input=user_input, actual_output=output)
        metric = SummarizationMetric(
            threshold=self.threshold,
            model=self.model,
            assessment_questions=assessment_questions,
        )
        metric.measure(test_case)   # Synchronous library call.
        return metric.score

service = MetricService()

@router.post("/summary")
async def summary(payload: SummaryPayload) -> dict[str, float]:
    try:
        score = await asyncio.to_thread(
            service.summary_metric,
            payload.input,
            payload.output,
            payload.assessment_questions,
        )
        return {"score": score}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to calculate summary score") from exc
```

The important syntax is:

```python
async def correct() -> object:
    return await asyncio.to_thread(function, arg1, arg2)
```

not:

```python
async def incorrect() -> object:
    return await asyncio.to_thread(function(arg1, arg2))  # Wrong: passes a result, not a callable.
```

`asyncio.to_thread()` keeps the event loop responsive for **blocking I/O and synchronous libraries**. It does not make pure-Python CPU work parallel; for CPU-heavy work, use a process pool or an external worker system.

## 8. If the library has a genuine async API, await it directly

When a dependency explicitly provides an awaitable API, make the wrapper asynchronous and await it:

```python
async def summary_metric(
    async_client: httpx.AsyncClient,
    user_input: str,
    output: str,
    assessment_questions: list[str],
) -> float:
    response = await async_client.post(
        "https://scoring.example/summary",
        json={
            "input": user_input,
            "output": output,
            "assessment_questions": assessment_questions,
        },
    )
    response.raise_for_status()
    return float(response.json()["score"])

@router.post("/summary")
async def summary(payload: SummaryPayload) -> dict[str, float]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        score = await summary_metric(
            client,
            payload.input,
            payload.output,
            payload.assessment_questions,
        )
    return {"score": score}
```

Do not pass an `async def` function to `asyncio.to_thread()`. A thread would call it and receive a coroutine object rather than its result. A downstream error such as `'coroutine' object has no attribute 'choices'` usually means an async call was made without `await` somewhere in the call chain.

Before choosing an approach, inspect the library API:

| Dependency behavior | Correct integration |
| --- | --- |
| Returns an awaitable and documents `await` | Call it with `await`. |
| Returns a normal value and blocks | Call it in `asyncio.to_thread()` or from a FastAPI `def` endpoint. |
| Is CPU-heavy Python work | Use processes, a worker queue, or a suitable external service. |
| Has both sync and async clients | Prefer the async client from an `async def` endpoint. |

## 9. Timeouts, cancellation, and cleanup

Every remote dependency needs a timeout. Prefer the client's timeout support, and use an application-level timeout when an operation has a strict total budget:

```python
import asyncio

async def fetch_with_budget() -> dict:
    try:
        async with asyncio.timeout(10):  # Python 3.11+
            return await fetch_remote_data()
    except TimeoutError:
        raise RemoteServiceTimeout()
```

For Python 3.10 and earlier, use `asyncio.wait_for(fetch_remote_data(), timeout=10)`.

Cancellation is normal: it may happen during shutdown, after a client disconnect, or when a `TaskGroup` sibling fails. Use `try/finally` to release resources, and do not silently swallow `asyncio.CancelledError`.

```python
async def stream_data() -> None:
    resource = await open_resource()
    try:
        await consume(resource)
    finally:
        await resource.aclose()
```

## 10. Common mistakes

| Mistake | Why it fails | Correct approach |
| --- | --- | --- |
| `await` a `float`, `dict`, or other regular value | Only awaitables can be awaited. | Remove `await`, or use the dependency's actual async API. |
| `asyncio.to_thread(func(...))` | Calls `func` immediately and passes its result instead of a callable. | `asyncio.to_thread(func, ...)` |
| Call `requests.get()` in `async def` | Blocks the event loop. | Use `httpx.AsyncClient`, or offload the sync call. |
| Wrap CPU-bound Python work in `to_thread()` | It usually still contends for the GIL. | Use processes or a work queue. |
| Create an `AsyncClient` for each item in a large loop | Loses pooling and can exhaust resources. | Reuse a client and bound concurrency. |
| Use `asyncio.run()` inside FastAPI | An event loop is already running. | Use `await` or create a task deliberately. |
| Catch every exception and return its text to users | Leaks internal details and hides cancellation. | Log server details; return a safe error message. |

## 11. Practical checklist

Before marking a function `async`, ask:

1. Does it call an async library and use `await`? Use `async def`.
2. Does it call blocking synchronous I/O? Use the library's async alternative, `asyncio.to_thread()`, or a FastAPI `def` endpoint.
3. Is it CPU-bound? Move it to processes or workers.
4. Are independent operations concurrent? Use `TaskGroup` or `gather()`.
5. Is concurrency bounded? Add a semaphore or connection limits for large batches.
6. Are timeouts, retries, and cancellation behavior defined for remote calls?
7. Are shared clients and resources closed properly?

## References

- [Python `asyncio`: Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- [FastAPI: Concurrency and `async` / `await`](https://fastapi.tiangolo.com/async/)
- [HTTPX: Async Support](https://www.python-httpx.org/async/)
