# How Python Executes Code: CPython, the GIL, Threads, and `asyncio`

This is a practical mental model for the standard Python implementation, **CPython**. It explains what happens when a Python program runs, why the GIL changes the behaviour of threads, and how `asyncio` achieves high-concurrency I/O. It deliberately separates guarantees in the Python language from CPython implementation details.

## Start with the right model

When you run `python app.py`, the operating system starts a **process** containing the Python interpreter. The program begins with one **main OS thread**. A process owns resources such as memory, open files, sockets, environment variables, and signal handlers. Threads within that process share those resources, while each thread has its own execution state and native stack.

```text
Operating system
└── Python process
    ├── shared process resources: heap, modules, sockets, files
    ├── main OS thread
    └── optional additional OS threads
```

A `threading.Thread` is a native OS thread, not a lightweight Python-only construct. The OS decides when runnable threads run and preempts them; Python code does not manually choose OS thread switches.

## What CPython does with a `.py` file

“Python” is a language; **CPython** is the common interpreter implementation, written primarily in C. The exact internals vary by implementation and version, but the useful CPython pipeline is:

```text
source (.py)
  → tokenize and parse
  → compile to CPython code objects / bytecode
  → CPython evaluation loop executes that bytecode
  → calls Python functions, built-ins, C extensions, and OS APIs as needed
```

- **Bytecode** is an intermediate instruction format for CPython’s virtual machine. It is not CPU machine code and must not be treated as stable across Python releases or other Python implementations.
- `dis` displays the bytecode CPython generated for a function or code object.
- Imported modules can be cached as `.pyc` files in `__pycache__` to avoid recompiling source on later imports when the cache is valid. Compilation can also happen in memory; do not depend on a `.pyc` file being written for every execution.

```python
import dis


def total(values: list[int]) -> int:
    return sum(values) + 1


dis.dis(total)  # Inspect the bytecode for this CPython version.
```

The bytecode for this example will differ between Python versions. That is expected.

## The GIL in one sentence

In the usual GIL-enabled build of CPython, the **Global Interpreter Lock (GIL)** is a lock that a thread must hold while operating on Python objects or invoking most of CPython’s C API. Consequently, only one thread at a time executes Python bytecode in a given interpreter.

The GIL exists because CPython’s runtime state and object-management machinery must be protected from concurrent access. It protects interpreter internals; it does **not** make a multi-step operation in your program logically atomic.

### What the GIL does and does not mean

| Statement | Accurate interpretation |
| --- | --- |
| “Python starts with one thread.” | Yes: a program starts with a main thread. It may later create more OS threads. |
| “Threads do not run.” | False. They are real OS threads and can wait, perform I/O, and be scheduled independently. |
| “Threads run Python CPU code in parallel.” | Not in normal GIL-enabled CPython: one thread executes Python bytecode at a time. |
| “The GIL makes shared state safe.” | False. Use synchronization for invariants and multi-step updates. |
| “The GIL is a Python-language rule.” | No. It is primarily a CPython runtime detail. |

### Important current exception: free-threaded CPython

Since Python 3.13, CPython provides an **optional free-threaded build** that can run with the GIL disabled. It is not the usual default build, and extension support and performance trade-offs still matter. Write correct synchronization regardless: code should not rely on the GIL for application-level thread safety.

You can inspect a build that supports this mode with `sysconfig.get_config_var("Py_GIL_DISABLED")`; use `sys._is_gil_enabled()` only when targeting Python versions where it is available.

## Why I/O allows useful threaded concurrency

The phrase “I/O does not need the GIL” is too broad. The accurate sequence for a blocking operation such as a socket read is:

1. Python bytecode evaluates the call, so the thread holds the GIL.
2. CPython enters the implementation of the operation.
3. For many blocking I/O operations, CPython releases the GIL while it waits in the OS or a C library.
4. Another thread can acquire the GIL and execute Python bytecode.
5. When I/O completes, the original thread reacquires the GIL before returning a Python result.

```text
Thread A: bytecode → call socket/file API → release GIL → wait for I/O
Thread B:                                      acquire GIL → run bytecode
Thread A: I/O ready → reacquire GIL → resume Python code
```

This is why threads are often a good fit for a moderate number of independent, blocking I/O operations. It is not a promise that every library call releases the GIL. Read the library’s documentation, and measure the workload that matters.

## Threads: memory, scheduling, and locks

### Shared memory and private stack

Threads share the process address space: Python objects on the heap, globals, imported modules, file descriptors, and other process resources. Each native thread still needs a private native **stack** for call/return state, C-level local variables, and saved execution context. Stack allocation and default size are platform- and configuration-dependent; “1 MB per thread” is only a rough, non-portable rule of thumb.

Python frame objects and ordinary Python values are managed by the runtime and live primarily on the heap. Do not model Python locals as simply being native C-stack variables.

### Context switching

The OS scheduler may pause one runnable thread and resume another. It saves and restores CPU state such as instruction and stack pointers and registers. Switching also tends to reduce cache locality. With huge numbers of threads, memory reserved for stacks, scheduler work, and cache disruption can dominate useful work.

```text
T1 runs → OS preempts T1 → save T1 state → restore T2 state → T2 runs
```

The exact timing and cost depend on the operating system, CPU, workload, and whether threads are blocking. Treat fixed claims such as “a switch always costs N microseconds” as unreliable.

### Why a `Lock` is still needed

The GIL protects CPython internals, not your business invariant. A read-modify-write operation can interleave with another thread between the individual steps.

```python
import threading

count = 0
count_lock = threading.Lock()


def increment() -> None:
    global count
    with count_lock:
        count += 1
```

Use `threading.Lock`, `Queue`, and other synchronization primitives to make ownership and invariants explicit. Avoid relying on whether a particular list or dictionary operation appears atomic in one CPython version; that is not a sound concurrency design and is especially unsafe for a free-threaded future.

### When to select threads

Choose threads when you have synchronous/blocking I/O APIs, need compatibility with an existing blocking library, or need modest concurrency with simple code. Bound concurrency with an executor or a semaphore instead of creating unbounded threads.

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def read_size(path: Path) -> int:
    return len(path.read_bytes())


def total_size(paths: list[Path]) -> int:
    with ThreadPoolExecutor(max_workers=16) as executor:
        return sum(executor.map(read_size, paths))
```

For CPU-heavy pure-Python work on a normal GIL-enabled build, prefer processes rather than threads.

## Processes: genuine CPU parallelism, separate memory

A process has an independent memory space and, normally, its own interpreter and GIL. Multiple processes can therefore run Python CPU work on different cores. The trade-off is higher startup, memory, and communication cost. Inputs and results often need to be serialized (pickled) to cross process boundaries.

```python
from concurrent.futures import ProcessPoolExecutor


def square(value: int) -> int:
    return value * value


def main() -> None:
    with ProcessPoolExecutor() as executor:
        print(list(executor.map(square, range(10))))


if __name__ == "__main__":
    main()
```

Keep process-pool target functions at module scope and protect program entry with `if __name__ == "__main__":`, especially for portable code using spawn-based process creation.

## `asyncio`: one thread, many cooperative tasks

`asyncio` is useful when you have a large number of independent operations that use non-blocking, async-compatible APIs.

- A **coroutine function** is declared with `async def`.
- Calling it creates a **coroutine object**; it does not run it immediately.
- An `asyncio.Task` wraps a coroutine and schedules it on an event loop.
- An **event loop** runs ready callbacks and, typically, one task at a time in its thread. It watches timers and I/O readiness and resumes tasks when the operation they await has progressed.

```python
import asyncio


async def fetch_one(name: str) -> str:
    await asyncio.sleep(0.1)  # stand-in for async network I/O
    return f"finished {name}"


async def main() -> None:
    tasks = [asyncio.create_task(fetch_one(str(i))) for i in range(3)]
    results = await asyncio.gather(*tasks)
    print(results)


asyncio.run(main())
```

### What “a coroutine pauses itself” means

At an `await` of an unfinished awaitable, the current task suspends and gives control back to the event loop. The event loop runs another ready task or waits for I/O/timers. When the awaited result is ready, it schedules the suspended task to resume.

```text
Task A runs → await socket read → Task A suspends
Event loop runs Task B
socket becomes ready → event loop marks Task A ready
Task A resumes later
```

This is **cooperative** scheduling: a coroutine must reach an `await` (or return) to give other tasks a chance to run. CPU-heavy or blocking code inside an `async def` blocks the event loop and delays every task on it.

```python
import asyncio
import time


def legacy_blocking_call() -> str:
    time.sleep(1)
    return "done"


async def main() -> None:
    result = await asyncio.to_thread(legacy_blocking_call)
    print(result)


asyncio.run(main())
```

`asyncio.to_thread()` keeps the event loop responsive by moving a blocking function to a thread. It does not make CPU-bound Python code parallel under a normal GIL-enabled build; use a process pool for that case.

### Coroutines and generators: related idea, distinct language features

Generators introduced the useful idea that execution can yield a value and later resume from saved state. They are excellent for streaming values lazily. Native `async def` coroutines use a related suspension/resumption model, but they are a distinct language feature: `yield` produces values for an iterator; `await` waits for an awaitable and hands control back to the event loop. Do not treat `await` as simply `yield` with another spelling.

```python
from collections.abc import Iterator


def error_lines(lines: list[str]) -> Iterator[str]:
    for line in lines:
        if "ERROR" in line:
            yield line


for line in error_lines(["INFO started", "ERROR failed"]):
    print(line)
```

## Coroutines, Tasks, and Futures: lifecycle, cancellation, and errors

These terms are related but describe different layers of asynchronous work.

| Object | What it represents | Who schedules/completes it? | Cancellation and errors |
| --- | --- | --- | --- |
| **Coroutine object** | The suspended computation created by calling an `async def` function. It has not necessarily started. | Nothing schedules it until it is awaited or wrapped in a Task. | It has no `cancel()` API. The caller owns the decision to await it, close it, or hand it to a Task. If it raises while directly awaited, the awaiting caller receives the exception. Forgetting it commonly produces a “coroutine was never awaited” warning. |
| **`asyncio.Task`** | A Future-like object that drives one coroutine on an event loop. | The event loop schedules it; the creator retains the Task handle and should define its lifetime. | `task.cancel()` requests cancellation by injecting `CancelledError` at a cancellation point. It is cooperative, so cleanup must use `try`/`finally` and normally re-raise `CancelledError`. The Task stores the coroutine’s result, exception, or cancelled state; `await task` observes it. |
| **`asyncio.Future`** | A low-level placeholder for one eventual result. It is often the bridge from callbacks or I/O to `await`. | The producer that performs the operation resolves it with `set_result()` or `set_exception()`; application code normally should not create one. | A consumer may call `future.cancel()`, but an underlying operation may need its own cancellation handling. Awaiters observe its result, exception, or cancellation. |

A `Task` is itself a specialized `Future`. Prefer `asyncio.create_task()` to manually constructing Tasks, keep a reference to every background task, and use `asyncio.TaskGroup` when a group should have one explicit owner and failure policy.

```python
import asyncio


async def work() -> int:
    await asyncio.sleep(0.1)
    return 42


async def main() -> None:
    coroutine = work()  # Created, but not scheduled yet.
    task = asyncio.create_task(coroutine)  # Now scheduled by the event loop.
    print(await task)  # Retrieves 42, or re-raises work()'s exception.


asyncio.run(main())
```

Cancellation is not automatically “an error to ignore.” The creator of a Task owns the policy (for example, a request timeout, shutdown, or a `TaskGroup` sibling failure); the coroutine owns prompt cleanup and should generally allow `CancelledError` to propagate.

```python
import asyncio


async def worker() -> None:
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        print("release resources")


async def main() -> None:
    task = asyncio.create_task(worker())
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("caller observed cancellation")


asyncio.run(main())
```

## Demonstrating and fixing a shared-counter race

A race condition is a correctness bug caused by the outcome depending on timing. The GIL does not protect a multi-step invariant such as “read the current count, add one, then write it back.” The following deliberately coordinates two threads to expose the lost update. The barriers are for the demonstration only; the `time.sleep(0)` creates an explicit point where another thread can run.

```python
import threading
import time

ITERATIONS = 1_000
counter = 0
read_barrier = threading.Barrier(2)
write_barrier = threading.Barrier(2)


def racy_increment() -> None:
    global counter
    for _ in range(ITERATIONS):
        observed = counter
        read_barrier.wait()   # Both threads have read the same value.
        time.sleep(0)         # Deliberately permit an interleaving.
        counter = observed + 1
        write_barrier.wait()  # Start the next iteration together.


threads = [threading.Thread(target=racy_increment) for _ in range(2)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print(counter)  # 1000, not the expected 2000: one update is lost each round.
```

Make the read-modify-write operation one critical section with a `Lock`.

```python
import threading

ITERATIONS = 1_000
counter = 0
counter_lock = threading.Lock()


def safe_increment() -> None:
    global counter
    for _ in range(ITERATIONS):
        with counter_lock:
            counter += 1


threads = [threading.Thread(target=safe_increment) for _ in range(2)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print(counter)  # 2000
```

For more complex state, a `queue.Queue` is often clearer: workers send increment messages and one owner thread updates the counter. This avoids sharing write ownership rather than guarding every mutation with a lock.

```python
import queue
import threading

messages: queue.Queue[int | None] = queue.Queue()
counter = 0


def owner() -> None:
    global counter
    while True:
        value = messages.get()
        try:
            if value is None:
                return
            counter += value
        finally:
            messages.task_done()


def producer() -> None:
    for _ in range(1_000):
        messages.put(1)


owner_thread = threading.Thread(target=owner)
workers = [threading.Thread(target=producer) for _ in range(2)]
owner_thread.start()
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
messages.put(None)
messages.join()
owner_thread.join()
print(counter)  # 2000
```

## Demonstrating event-loop blocking—and fixing it

An `async def` function is not automatically non-blocking. The event loop can run another task only when the current task returns control, usually at `await`. Calling `time.sleep()` or doing long CPU work directly inside an async function blocks the loop; timers, network callbacks, and other Tasks stall behind it.

```python
import asyncio
import time


async def ticker() -> None:
    for _ in range(3):
        print(f"tick at {time.perf_counter():.2f}")
        await asyncio.sleep(0.1)


async def blocks_event_loop() -> None:
    time.sleep(0.5)  # Wrong in async code: blocks the event-loop thread.


async def main() -> None:
    await asyncio.gather(ticker(), blocks_event_loop())


asyncio.run(main())
```

The ticks pause for roughly half a second after the first one. For a blocking **I/O** function from a synchronous library, move it to a thread. The event loop remains responsive while that thread waits, though the thread still consumes a bounded worker-pool slot.

```python
import asyncio
import time


def blocking_io() -> str:
    time.sleep(0.5)  # Stand-in for a synchronous network or file operation.
    return "done"


async def main() -> None:
    result = await asyncio.to_thread(blocking_io)
    print(result)


asyncio.run(main())
```

For **CPU-heavy pure-Python** work, `asyncio.to_thread()` keeps the event loop responsive but normally does not give parallel CPU execution in GIL-enabled CPython. Move the work to a process pool instead. Keep the worker function at module scope and use the entry-point guard for portable process creation.

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor


def cpu_bound(limit: int) -> int:
    return sum(number * number for number in range(limit))


async def main() -> None:
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_bound, 1_000_000)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

Use `asyncio.to_thread()` for blocking I/O and a process pool for CPU-heavy Python work. In both cases, bound concurrency, retain the returned Task/Future, set timeouts where appropriate, and decide how cancellation should reach the underlying operation.

## Choosing the model

| Workload | Default choice | Reason |
| --- | --- | --- |
| CPU-heavy pure Python | processes | Can use multiple cores without one process’s GIL serializing bytecode. |
| A small/moderate number of blocking I/O calls | threads | Works with synchronous libraries; OS waits release the CPU. |
| Many network operations with async client libraries | `asyncio` | Many lightweight tasks share an event-loop thread. |
| Blocking work inside an async application | `asyncio.to_thread()` for I/O; process pool for CPU | Keeps the event loop from being blocked. |

There are no universal numeric cut-offs such as “threads fail at 1,000 and asyncio always handles 100,000.” File descriptors, network limits, server rate limits, memory, connection pooling, and workload behaviour determine the safe concurrency. Use bounds and measure.

## Example decision: clone or download 1,000 repositories

This workload is mostly network and disk I/O, but it also has server, authentication, disk, subprocess, and rate-limit constraints.

- If using an async HTTP API/client: use `asyncio` with a bounded semaphore or bounded worker queue.
- If calling a blocking SDK or `git` subprocess API: a bounded thread pool or bounded subprocess concurrency may be simpler.
- Do **not** start 1,000 threads, tasks, processes, or `git` commands at once. Bound parallelism, use timeouts, retry only safe failures with backoff, and respect service limits.

## Essential rules and common mistakes

1. Keep shared mutable state small; pass data through queues or return values where possible.
2. Bound concurrency. A task is lightweight, but its socket, response body, remote-service slot, and memory use are not free.
3. Never call blocking I/O or long CPU loops directly in an event-loop task.
4. Set timeouts and handle cancellation deliberately. Cancellation is a normal control path in async programs.
5. Use a process-safe design for processes: top-level functions, serializable arguments, and explicit entry-point guards.
6. Profile before optimizing. Determine whether time is spent on CPU, network wait, disk wait, or lock contention.
7. Keep Python-version and implementation assumptions explicit; the GIL and bytecode details are CPython-specific.
8. Treat `eval()` and `exec()` as dynamic code execution, not a normal control-flow tool. Never use them on untrusted input; use a parser, whitelist, or a dedicated data format instead.

## Questions worth exploring next

1. What does `dis.dis()` show for a simple expression on my exact Python version, and why should I avoid treating those instructions as a stable API?
3. How do `sys.setswitchinterval()` and OS preemption differ, and why should application correctness not depend on either timing?
4. Which calls in a library I use actually release the GIL or offer an async API? How can I verify this from its documentation and a benchmark?
5. What changes when I run the same CPU benchmark with threads, a process pool, and a free-threaded CPython build?
7. How does an event loop learn that a socket is ready, and how do readiness mechanisms such as `select`, `epoll`, and `kqueue` relate to that?
9. How would I design a bounded downloader with connection limits, timeouts, retries, backoff, and graceful shutdown?
10. What invariants does my shared state require, and can I redesign it so one thread/task owns the state instead of locking it everywhere?
11. What are the costs of sending a large object to a process pool, and when is shared memory worth considering?
12. How do signals, subprocesses, threads, and event loops interact in the application platform I deploy to?

## Primary references

- [Python execution model](https://docs.python.org/3/reference/executionmodel.html)
- [CPython GIL and thread states](https://docs.python.org/3/c-api/threads.html)
- [`threading` and GIL performance considerations](https://docs.python.org/3/library/threading.html)
- [Free-threaded CPython](https://docs.python.org/3/howto/free-threading-python.html)
- [`asyncio` coroutines and tasks](https://docs.python.org/3/library/asyncio-task.html)
- [The `dis` bytecode disassembler](https://docs.python.org/3/library/dis.html)
- [`concurrent.futures` executors](https://docs.python.org/3/library/concurrent.futures.html)
- [`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html)
