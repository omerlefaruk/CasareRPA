# Thread/Process Pool Patterns Research

**Date**: 2025-12-05
**Focus**: concurrent.futures, threading, Qt integration
**Context**: CasareRPA uses Python 3.12+, PySide6, qasync (Qt+asyncio)

---

## Executive Summary

CasareRPA already employs several threading patterns. This research consolidates best practices for:
- Choosing threads vs processes
- Pool sizing
- Qt/asyncio integration

---

## 1. ThreadPoolExecutor vs ProcessPoolExecutor

### Key Differences

| Aspect | ThreadPoolExecutor | ProcessPoolExecutor |
|--------|-------------------|---------------------|
| Memory | Shared memory space | Isolated per process |
| GIL | Subject to GIL | Bypasses GIL |
| Overhead | Low (thread spawn ~0.1ms) | High (process spawn ~50ms) |
| Data Passing | Direct reference | Pickle serialization required |
| Best For | I/O-bound | CPU-bound |
| Failure Mode | Thread crash = app crash | Process crash = isolated |

### Decision Matrix

| Workload Type | Recommended | Rationale |
|---------------|-------------|-----------|
| Network I/O (HTTP, WebSocket) | Thread | GIL releases during I/O wait |
| File I/O | Thread | GIL releases during syscalls |
| Database queries | Thread | Network-bound, GIL released |
| OCR/Image processing | Process | CPU-bound, bypasses GIL |
| PDF parsing | Process | Heavy computation |
| Data transformation | Depends | Small = Thread, Large = Process |
| Browser automation | Thread | Playwright already async |
| Desktop automation | Thread | UIAutomation is mostly wait |

### GIL Release Points

The GIL is released during:
- I/O operations (file, network, database)
- `time.sleep()` calls
- Waiting on locks
- C extension calls (NumPy, PIL)
- `asyncio.to_thread()` operations

---

## 2. Optimal Pool Sizing

### ThreadPoolExecutor

**Default (Python 3.8+)**: `min(32, os.cpu_count() + 4)`

**Formula for I/O-bound**:
```
optimal_threads = cpu_count * (1 + wait_time / compute_time)
```

**Practical Guidelines**:
| Workload | Recommended Size |
|----------|------------------|
| Pure I/O (network calls) | 20-50 threads |
| Mixed I/O + light compute | 10-20 threads |
| Database connections | Match connection pool size |
| Light background tasks | 4-8 threads |

**Current CasareRPA Usage**:
- `LLMModelProvider`: Uses `max_workers=3` (conservative, good for API calls)
- `DesktopContext._run_async()`: Uses default (one-shot, acceptable)

### ProcessPoolExecutor

**Default**: `os.cpu_count()` (number of CPU cores)

**Guidelines**:
| Workload | Recommended Size |
|----------|------------------|
| CPU-bound computation | `cpu_count()` |
| Mixed CPU/memory-heavy | `cpu_count() - 1` (leave headroom) |
| Memory-intensive | Reduce based on RAM |

**Memory Consideration**:
```python
# Each process copies Python interpreter + memory
# Rule of thumb: max_workers = available_ram_mb / (process_memory_mb * 1.5)
```

---

## 3. Asyncio Integration Patterns

### Pattern 1: `asyncio.to_thread()` (Python 3.9+)

**Best for**: Simple blocking functions.
```python
# Clean, simple approach
result = await asyncio.to_thread(blocking_function, arg1, arg2)
```

**Current Usage in CasareRPA**:
- `ScreenCapture.capture_screenshot()` - Correct usage
- `FormInteractor`, `WaitManager`, `WindowManager` - Correct usage

### Pattern 2: `loop.run_in_executor()` with Custom Pool

**Best for**: Controlled pool size, reusable executor.
```python
# At startup
self._executor = ThreadPoolExecutor(max_workers=10)
loop.set_default_executor(self._executor)

# Usage
result = await loop.run_in_executor(None, blocking_func, arg)
# or with specific executor
result = await loop.run_in_executor(self._executor, blocking_func, arg)
```

**Current Usage in CasareRPA**:
- `ocr_tab.py`, `image_match_tab.py` - Uses `run_in_executor`
- `google_client.py`, `cv_healer.py` - Uses `run_in_executor`

### Pattern 3: Wrapping Blocking APIs

**Decorator approach**:
```python
def async_wrap(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper
```

### Pattern 4: Sync-to-Async Bridge (Current in DesktopContext)

```python
def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        # Already in async context - use thread
        with ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No loop - safe to use asyncio.run()
        return asyncio.run(coro)
```

**Warning**: This pattern creates nested event loops. Consider refactoring to pure async.

---

## 4. Qt Thread Patterns

### Pattern 1: QThread Subclass (Current in CasareRPA)

Used in: `MigrationWorker`, `InstallWorker`

```python
class Worker(QThread):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int, int)

    def run(self):
        # Work happens here
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._async_work())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
```

**Pros**: Simple, self-contained
**Cons**: Creates new event loop per thread

### Pattern 2: QThreadPool + QRunnable

**Best for**: Many short-lived tasks.

```python
class WorkerSignals(QObject):
    finished = Signal()
    result = Signal(object)
    error = Signal(tuple)
    progress = Signal(int)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit((type(e), e))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

# Usage
pool = QThreadPool.globalInstance()
pool.setMaxThreadCount(8)
worker = Worker(my_function, arg1, arg2)
worker.signals.result.connect(handle_result)
pool.start(worker)
```

### Pattern 3: qasync Integration (Recommended for CasareRPA)

CasareRPA uses `qasync` - leverage it fully:

```python
# In Qt widget
async def async_operation(self):
    result = await some_async_function()
    self.update_ui(result)

# Trigger from Qt
def on_button_click(self):
    asyncio.ensure_future(self.async_operation())
```

**No need for QThread when using qasync** - prefer async/await.

---

## 5. Work Stealing Patterns

Python's `concurrent.futures` does NOT implement work stealing (like Go or Rust). Each worker gets tasks from a shared queue.

**Alternative**: `multiprocessing.Pool` with `maxtasksperchild` for memory cleanup.

**For true work stealing**, consider:
- `ray` library (distributed computing)
- `joblib` with `loky` backend
- Custom implementation with task queues

---

## 6. Context Switching Overhead

### Thread Context Switch

- Cost: ~1-10 microseconds
- Involves: Save/restore registers, stack pointer
- GIL: Additional contention (~5-10 microseconds)

### Process Context Switch

- Cost: ~10-100 microseconds
- Involves: Full memory space switch, TLB flush
- No GIL contention (independent interpreters)

### Practical Impact

| Scenario | Thread Overhead | Process Overhead |
|----------|-----------------|------------------|
| 100 tasks, 10ms each | ~1% | ~1-2% |
| 100 tasks, 1ms each | ~10% | ~20% |
| 1000 tasks, 0.1ms each | ~50%+ | ~90%+ |

**Rule**: Don't use pools for sub-millisecond tasks.

---

## 7. Recommendations for CasareRPA

### Current State Analysis

| Component | Current Pattern | Assessment |
|-----------|----------------|------------|
| `LLMModelProvider` | ThreadPoolExecutor(3) | Good - limited API concurrency |
| `DesktopContext._run_async` | One-shot ThreadPoolExecutor | Okay - but could be refactored |
| `ScreenCapture` | asyncio.to_thread | Correct |
| `MigrationWorker` | QThread | Correct for long-running |
| `InstallWorker` | QThread | Correct |
| Browser nodes | Direct async | Correct |

### Recommended Changes

1. **Global Executor for Canvas**
```python
# In app.py or similar
class CanvasApp:
    def __init__(self):
        self._io_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="io_")
        self._cpu_executor = ProcessPoolExecutor(max_workers=os.cpu_count())
```

2. **Prefer asyncio.to_thread over run_in_executor**
   - Simpler API
   - Uses default executor (can be configured globally)

3. **Use QThread only for**:
   - Long-running operations (>1 second)
   - Operations needing progress updates
   - Operations that create their own event loop

4. **Use qasync for most Qt async**:
   - Short async operations
   - Network calls from UI
   - No need for separate threads

5. **Consider ProcessPoolExecutor for**:
   - OCR batch processing
   - Image comparison
   - PDF parsing
   - Any CPU-intensive node

### Pool Configuration Template

```python
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class ExecutorConfig:
    """Centralized executor configuration."""

    # I/O-bound: HTTP, file, database
    IO_WORKERS = min(20, os.cpu_count() * 2 + 4)

    # CPU-bound: OCR, image processing
    CPU_WORKERS = max(1, os.cpu_count() - 1)

    # Light background tasks
    BACKGROUND_WORKERS = 4

    @classmethod
    def create_io_executor(cls):
        return ThreadPoolExecutor(
            max_workers=cls.IO_WORKERS,
            thread_name_prefix="casare_io_"
        )

    @classmethod
    def create_cpu_executor(cls):
        return ProcessPoolExecutor(max_workers=cls.CPU_WORKERS)
```

---

## 8. Unresolved Questions

1. Should CasareRPA implement a global executor registry?
2. Is the nested event loop in `DesktopContext._run_async()` causing issues?
3. Would ProcessPoolExecutor help OCR/image processing performance significantly?
4. Should QThreadPool be used instead of individual QThread instances?

---

## References

- Python concurrent.futures documentation
- PySide6 Threading documentation
- qasync library patterns
- GIL implementation details (PEP 703 for future reference)
