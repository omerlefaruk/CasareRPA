# Python Async Performance Patterns Research

**Date**: 2025-12-05
**Research Type**: Technical Analysis
**Scope**: Async optimization for CasareRPA Windows RPA platform

---

## Executive Summary

This research identifies key async optimization patterns for Python-based RPA workloads. Key findings:

1. **uvloop not viable on Windows** - CasareRPA must use standard asyncio or qasync
2. **TaskGroup preferred over gather** - Better exception handling, slightly faster
3. **qasync integration adds minimal overhead** - Acceptable for GUI RPA
4. **Semaphore-based concurrency limiting already implemented** in `parallel_executor.py`

---

## 1. Event Loop Selection

### uvloop vs Standard Event Loop

| Criteria | uvloop | Standard asyncio |
|----------|--------|------------------|
| Windows Support | **NO** | YES |
| Performance | 2-4x faster | Baseline |
| Compatibility | Unix-only (libuv) | Cross-platform |
| Qt Integration | Requires custom loop | qasync works |

**Recommendation for CasareRPA**: Standard asyncio with qasync.

uvloop does NOT support Windows - it relies on libuv Unix-specific features (epoll/kqueue). Since CasareRPA is Windows Desktop RPA, uvloop is not an option.

```python
# CasareRPA current approach (app.py line 116-117)
from qasync import QEventLoop
self._loop = QEventLoop(self._app)
asyncio.set_event_loop(self._loop)
```

### qasync Specific Optimizations

Current implementation is correct. Additional optimizations:

1. **Avoid sync-in-async**: Never call `time.sleep()` or blocking I/O in async functions
2. **Use `asyncio.create_task()`** for fire-and-forget operations
3. **Batch Qt signal emissions** to reduce event loop context switches
4. **Prefer `QTimer.singleShot`** over `asyncio.sleep()` for UI timing

---

## 2. asyncio.gather vs TaskGroup

### Performance Comparison

| Criteria | asyncio.gather | TaskGroup (3.11+) |
|----------|----------------|-------------------|
| Performance | Baseline | Slightly faster |
| Exception Handling | Returns exceptions in list | Auto-cancels remaining tasks |
| Structured Concurrency | No | Yes |
| Syntax | Functional | Context manager |

### When to Use Each

**Use TaskGroup when:**
- Tasks may schedule subtasks
- Need automatic cancellation on failure
- Want structured concurrency guarantees

**Use gather when:**
- Simple parallel execution
- Need to collect all results even if some fail (`return_exceptions=True`)
- Python < 3.11 compatibility required

### Current CasareRPA Usage

```python
# parallel_executor.py line 224
await asyncio.gather(*async_tasks, return_exceptions=True)
```

**Recommendation**: Migrate to TaskGroup for error handling benefits.

```python
# Proposed pattern
async def execute_parallel_v2(self, tasks):
    results = {}
    async with asyncio.TaskGroup() as tg:
        for task_id, coro_func in tasks:
            tg.create_task(self._run_with_capture(task_id, coro_func, results))
    return results
```

---

## 3. Concurrency Limiting Patterns

### Semaphore Best Practices

CasareRPA already implements this correctly in `parallel_executor.py`:

```python
# Current implementation (lines 181-218)
self._semaphore = asyncio.Semaphore(self._max_concurrency)

async def run_task(task_id: str, coro_func: Callable) -> None:
    async with self._semaphore:
        # Task execution
```

**Pattern Rating**: Correct implementation.

### Additional Recommendations

1. **Use BoundedSemaphore** for debug builds to catch release-without-acquire bugs
2. **Per-resource semaphores** for different resource types:

```python
class ResourceLimiter:
    browser_sem = asyncio.Semaphore(3)    # Max 3 browser contexts
    http_sem = asyncio.Semaphore(10)      # Max 10 concurrent HTTP
    file_sem = asyncio.Semaphore(5)       # Max 5 file operations
```

3. **Adaptive concurrency** based on system load (future enhancement)

---

## 4. Avoiding Event Loop Blocking

### Detection

Enable asyncio debug mode for development:

```python
# In development settings
asyncio.get_event_loop().set_debug(True)
asyncio.get_event_loop().slow_callback_duration = 0.1  # Log >100ms callbacks
```

### Solutions

| Blocking Type | Solution |
|---------------|----------|
| CPU-bound | `run_in_executor(ProcessPoolExecutor)` |
| Blocking I/O | `run_in_executor(ThreadPoolExecutor)` |
| File system | Thread pool (OS limitation) |
| Heavy computation | Process pool |

### Current CasareRPA Patterns

Found in codebase:
- `src/casare_rpa/nodes/interaction_nodes.py` - uses executor for blocking ops
- `src/casare_rpa/desktop/context.py` - executor for desktop automation
- `src/casare_rpa/infrastructure/browser/healing/cv_healer.py` - executor for CV ops

**Pattern**:
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function, *args)
```

**Recommendation**: Standardize with a utility function:

```python
async def run_blocking(func, *args, executor=None):
    """Run blocking function without blocking event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)
```

---

## 5. Async Queue Patterns

### asyncio.Queue vs queue.Queue

| Criteria | asyncio.Queue | queue.Queue |
|----------|---------------|-------------|
| Thread Safety | NO (single loop only) | YES |
| Event Loop Blocking | Never | Always |
| Use Case | Async producer/consumer | Multi-threaded |

**Pattern for Mixed Threading/Async**:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# For thread -> async communication
def thread_function(loop, async_queue):
    # Run from thread
    asyncio.run_coroutine_threadsafe(
        async_queue.put("data"),
        loop
    )
```

---

## 6. Async Generator Patterns

### Memory-Efficient Streaming

```python
async def stream_large_dataset(source):
    """Process data without loading all into memory."""
    async for chunk in source.read_chunks():
        processed = await process_chunk(chunk)
        yield processed

# Usage - lazy evaluation
async for item in stream_large_dataset(db):
    await handle_item(item)  # One at a time
```

### Backpressure Handling

Async generators naturally provide backpressure - producer waits for consumer.

**RPA Application**: Use for large table scraping, file streaming, log processing.

---

## 7. RPA-Specific Concurrency Patterns

### Browser Context Pooling

```python
class BrowserPool:
    """Pooled browser contexts with semaphore limiting."""

    def __init__(self, max_contexts=3):
        self._semaphore = asyncio.Semaphore(max_contexts)
        self._contexts = []

    async def acquire(self):
        await self._semaphore.acquire()
        return await self._get_or_create_context()

    def release(self, context):
        self._contexts.append(context)
        self._semaphore.release()
```

### Workflow Branch Parallelization

CasareRPA already implements this in `parallel_executor.py` with:
- `DependencyGraph` for dependency analysis
- `get_independent_groups()` for topological sorting
- `execute_batches()` for sequential batch execution with parallel tasks within

**Current architecture is sound.**

---

## 8. Performance Recommendations

### Immediate Actions

1. **Keep current qasync setup** - correct for Windows + Qt
2. **Consider TaskGroup migration** - better error handling than gather
3. **Add resource-specific semaphores** - separate browser/http/file limits

### Future Enhancements

1. **Async context manager pooling** for frequently used resources
2. **Adaptive concurrency** based on system metrics
3. **Debug mode slow callback logging** in development builds

### What NOT to Do

1. Do NOT attempt uvloop on Windows
2. Do NOT use `queue.Queue` in async code
3. Do NOT call `time.sleep()` in async functions
4. Do NOT perform CPU-bound work directly in event loop

---

## Code References

| File | Pattern |
|------|---------|
| `app.py:116-117` | qasync event loop setup |
| `parallel_executor.py:181-224` | Semaphore-limited parallel execution |
| `parallel_executor.py:56-73` | Dependency graph ready node detection |
| `nodes/interaction_nodes.py` | run_in_executor for blocking |

---

## Conclusion

CasareRPA's async architecture is fundamentally correct for Windows RPA:

1. **qasync integration** properly bridges Qt and asyncio
2. **Semaphore concurrency limiting** already implemented
3. **run_in_executor** used appropriately for blocking operations

Primary optimization opportunity: Migrate from `asyncio.gather` to `TaskGroup` for improved structured concurrency and exception handling in workflow execution.
