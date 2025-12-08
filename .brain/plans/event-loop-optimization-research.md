# Event Loop Optimization Research (qasync)

**Date**: 2025-12-05
**Focus**: Qt + asyncio Integration Performance
**Status**: Research Complete

---

## Executive Summary

CasareRPA uses qasync to bridge PySide6's event loop with Python's asyncio, enabling async workflows (Playwright) to run within the Qt application. This research identifies optimization opportunities, monitoring techniques, and common pitfalls.

---

## Current Implementation Analysis

### qasync Integration (app.py:115-117)
```python
self._loop = QEventLoop(self._app)
asyncio.set_event_loop(self._loop)
```

**Observations:**
- Standard qasync pattern - creates QEventLoop as the asyncio loop
- Loop runs via `self._loop.run_forever()` in `run()` method
- All asyncio operations (Playwright, HTTP) share this loop

### Timer Usage Patterns Found

| Component | Interval | Purpose |
|-----------|----------|---------|
| ViewportCulling | 33ms (~30 FPS) | Node/pipe visibility updates |
| EventBatcher | 16ms (~60 FPS) | High-frequency event batching |
| ValidationTimer | Deferred | Workflow validation |
| AutosaveController | Configurable | Background saves |

### Thread-Safety Patterns

**Good patterns found:**
- `_ThreadSafeLogBridge` - Uses Qt signals for cross-thread log forwarding
- `_ThreadSafeTerminalBridge` - Qt signals for stdout/stderr
- `Qt.ConnectionType.QueuedConnection` - Used for cross-thread signal connections
- `QMetaObject.invokeMethod` with `QueuedConnection` - Thread-safe method calls
- `QTimer.singleShot(0, ...)` - Main thread marshaling

---

## qasync Tuning Recommendations

### 1. Avoid Blocking the Event Loop

**Current Issues Found:**
- `time.sleep()` calls in nodes (navigation_nodes.py, wait_nodes.py, browser_nodes.py)
- Synchronous file I/O in some paths
- CPU-intensive operations in main thread

**Recommendations:**
```python
# BAD - blocks both Qt and asyncio
time.sleep(1)

# GOOD - yields to event loop
await asyncio.sleep(1)

# GOOD - run CPU-bound work in executor
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, cpu_intensive_function)
```

### 2. Enable Debug Mode for Development

```python
# In app.py during development
self._loop.set_debug(True)
self._loop.slow_callback_duration = 0.05  # Warn at 50ms (default 100ms)
```

**Benefits:**
- Logs callbacks taking > threshold
- Detects never-awaited coroutines
- Shows detailed tracebacks

### 3. Optimize Timer Coalescing

**Current:** Multiple independent timers
**Recommended:** Consider consolidating related timers

```python
# Example: Single update timer driving multiple systems
class CoordinatedUpdateManager:
    def __init__(self, interval_ms=16):
        self._timer = QTimer()
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)
        self._update_callbacks = []

    def _tick(self):
        for callback in self._update_callbacks:
            callback()
```

### 4. Priority Scheduling

qasync doesn't have built-in priority scheduling, but you can implement it:

```python
# High-priority: Use call_soon_threadsafe for critical updates
loop.call_soon_threadsafe(critical_ui_update)

# Low-priority: Use call_later for deferrable work
loop.call_later(0.1, background_task)
```

---

## Event Loop Monitoring Techniques

### 1. Built-in Slow Callback Detection

```python
import asyncio
import logging

# Enable asyncio debug logging
logging.getLogger("asyncio").setLevel(logging.DEBUG)

# Or set environment variable
# PYTHONASYNCIODEBUG=1
```

### 2. Custom Blocking Detection

```python
class EventLoopMonitor:
    """Monitor event loop for blocking operations."""

    def __init__(self, loop, threshold_ms=50):
        self._loop = loop
        self._threshold = threshold_ms / 1000
        self._last_tick = None
        self._warning_count = 0

    async def monitor(self):
        import time
        while True:
            now = time.monotonic()
            if self._last_tick:
                delta = now - self._last_tick
                if delta > self._threshold:
                    logger.warning(
                        f"Event loop blocked for {delta*1000:.1f}ms "
                        f"(threshold: {self._threshold*1000:.0f}ms)"
                    )
                    self._warning_count += 1
            self._last_tick = now
            await asyncio.sleep(0.01)  # 10ms tick
```

### 3. Qt Event Dispatcher Monitoring

```python
from PySide6.QtCore import QAbstractEventDispatcher

def setup_qt_monitoring():
    dispatcher = QAbstractEventDispatcher.instance()
    if dispatcher:
        dispatcher.aboutToBlock.connect(on_about_to_block)
        dispatcher.awake.connect(on_awake)

def on_about_to_block():
    # Event loop is idle, about to wait for events
    pass

def on_awake():
    # Event loop woke up, has events to process
    pass
```

### 4. Third-Party Tools

| Tool | Purpose |
|------|---------|
| [loopmon](https://pypi.org/project/loopmon/) | Detects throttling and blocking coroutines |
| [BlockBuster](https://dev.to/cbornet/introducing-blockbuster-is-my-asyncio-event-loop-blocked-3487) | Monkey-patches blocking methods to raise errors |
| yappi | CPU profiling for async code |
| py-spy | Sampling profiler for runtime analysis |

---

## Common Performance Pitfalls

### 1. Signal Emission Spam
**Found:** EventBus publish was logging at DEBUG level for every event
**Fixed:** Already addressed in canvas performance optimization

### 2. High-Frequency Timers
**Found:** 60 FPS (16ms) culling timer
**Fixed:** Reduced to 30 FPS (33ms) - still smooth for humans

### 3. Synchronous File I/O
**Risk:** File operations in main thread block event loop
**Solution:** Use `run_in_executor` for file operations

```python
async def read_file_async(path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: Path(path).read_text())
```

### 4. Database Operations
**Risk:** Synchronous DB queries block event loop
**Current:** Uses asyncpg/aiomysql (async - good)

### 5. QTimer vs asyncio.sleep

```python
# QTimer - Qt event loop native, good for UI updates
QTimer.singleShot(100, callback)

# asyncio.sleep - asyncio native, good for coroutines
await asyncio.sleep(0.1)

# Both work in qasync, but mixing can cause timing inconsistencies
```

---

## Alternative: PySide6.QtAsyncio

Qt 6 introduced official asyncio support:

```python
from PySide6 import QtAsyncio

# Instead of qasync
QtAsyncio.run(main_coroutine(), quit_qapp=False)
```

**Comparison:**

| Aspect | qasync | QtAsyncio |
|--------|--------|-----------|
| Maturity | Stable, well-tested | Technical preview |
| Python Version | 3.6+ | 3.10+ |
| Maintenance | Community | Qt official |
| API Coverage | Full asyncio | Basic (no transports) |

**Recommendation:** Stay with qasync for now. QtAsyncio is not yet production-ready.

---

## Signal Queue Optimization

### Current Pattern (execution_controller.py)
```python
# Good: QueuedConnection for cross-thread safety
self._log_bridge.log_received.connect(
    on_log_received, Qt.ConnectionType.QueuedConnection
)
```

### Optimization Opportunities

1. **Batch Signal Emissions**
   - Already implemented: `EventBatcher` batches high-frequency events

2. **Avoid Signal Chains**
   - Each signal connection adds overhead
   - Consider direct method calls when thread-safe

3. **Use Direct Connections When Same Thread**
```python
# If you KNOW it's same thread, DirectConnection is faster
widget.clicked.connect(handler, Qt.ConnectionType.DirectConnection)

# Default AutoConnection checks at runtime
widget.clicked.connect(handler)  # Auto-detects
```

---

## Thread Safety Patterns

### Pattern 1: QTimer.singleShot for Main Thread
```python
# From background thread, schedule on main
def background_operation():
    # ... do work ...
    QTimer.singleShot(0, lambda: update_ui(result))
```

### Pattern 2: Signal Bridge
```python
class ThreadSafeBridge(QObject):
    update_requested = Signal(dict)

    def request_update(self, data):
        self.update_requested.emit(data)  # Thread-safe
```

### Pattern 3: QMetaObject.invokeMethod
```python
QMetaObject.invokeMethod(
    target_object,
    "method_name",
    Qt.ConnectionType.QueuedConnection,
    Q_ARG(str, argument)
)
```

---

## Recommended Monitoring Setup

### Development Configuration

```python
# In __init__ of CasareRPAApp
import os
import logging

if os.environ.get("CASARE_DEBUG_ASYNCIO"):
    logging.getLogger("asyncio").setLevel(logging.DEBUG)
    self._loop.set_debug(True)
    self._loop.slow_callback_duration = 0.05
    logger.info("Asyncio debug mode enabled (50ms threshold)")
```

### Production Monitoring

```python
# Periodic health check
async def event_loop_health_check():
    """Log event loop statistics periodically."""
    while True:
        await asyncio.sleep(60)  # Every minute

        # Get number of pending callbacks
        loop = asyncio.get_event_loop()

        # Log pending tasks
        pending = [t for t in asyncio.all_tasks() if not t.done()]
        if len(pending) > 10:
            logger.warning(f"High pending task count: {len(pending)}")
```

---

## Unresolved Questions

1. **QtAsyncio Migration**: When Qt stabilizes QtAsyncio, should CasareRPA migrate?
2. **Executor Pool Size**: What's optimal for `run_in_executor` workloads?
3. **Timer Consolidation**: Worth consolidating all timers into one coordinator?
4. **Profiling Integration**: Should we add optional py-spy/yappi integration?

---

## Sources

- [qasync GitHub](https://github.com/CabbageDevelopment/qasync)
- [qasync PyPI](https://pypi.org/project/qasync/)
- [PySide6.QtAsyncio Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtAsyncio/index.html)
- [Python asyncio Development](https://docs.python.org/3/library/asyncio-dev.html)
- [Qt Threads Events QObjects](https://wiki.qt.io/Threads_Events_QObjects)
- [loopmon - Event Loop Monitor](https://pypi.org/project/loopmon/)
- [BlockBuster - Blocking Detection](https://dev.to/cbornet/introducing-blockbuster-is-my-asyncio-event-loop-blocked-3487)
- [Qt Forum - Event Loop Blocking](https://forum.qt.io/topic/155473/how-am-i-blocking-the-event-loop)
