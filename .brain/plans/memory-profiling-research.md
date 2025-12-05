# Memory Profiling Tools and Techniques for CasareRPA

**Research Date**: 2025-12-05
**Focus**: Python memory profiling for PySide6 desktop RPA application

---

## Executive Summary

For CasareRPA (Python 3.12+ / PySide6 / Playwright), recommended profiling stack:
1. **tracemalloc** - Primary tool (built-in, low overhead)
2. **objgraph** - Reference cycle detection
3. **Pympler muppy** - Heap analysis
4. **psutil** - Runtime monitoring

---

## Tool Comparison Matrix

| Tool | Overhead | Best For | PySide6 Compatible | Active (2024) |
|------|----------|----------|-------------------|---------------|
| **tracemalloc** | 5-20% | Allocation tracking, snapshots | Yes | Yes (stdlib) |
| **memory_profiler** | Medium | Line-by-line analysis | Yes | Yes |
| **objgraph** | Low | Reference cycles, visualization | Yes | Yes |
| **Pympler** | Medium | Object size, muppy heap view | Yes | Yes |
| **Guppy3/Heapy** | High | Deep heap analysis | Partial | Limited |
| **Memray** | Low | Flame graphs, native code | Linux/macOS | Yes |
| **Scalene** | Low | CPU+Memory profiling | Yes | Yes |
| **mprofile** | Very Low | Sampling-based | Yes | Yes |

---

## Recommended Tools for CasareRPA

### 1. tracemalloc (PRIMARY)

**Why**: Built-in, no dependencies, Python 3.12 native support, snapshot comparison.

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Take baseline snapshot
snapshot1 = tracemalloc.take_snapshot()

# ... run operations ...

# Take comparison snapshot
snapshot2 = tracemalloc.take_snapshot()

# Compare and find growth
top_stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in top_stats[:10]:
    print(stat)
```

**Best Practices**:
- Take snapshots before/after workflow execution
- Filter by `tracemalloc.Filter(inclusive=True, filename_pattern="*casare_rpa*")`
- Store snapshots for trend analysis

### 2. objgraph (REFERENCE CYCLES)

**Why**: Visualizes object relationships, essential for Qt signal/slot leaks.

```python
import objgraph
import gc

gc.collect()

# Find most common types
objgraph.show_most_common_types(limit=20)

# Find growth between calls
objgraph.show_growth(limit=10)

# Find what's keeping an object alive
objgraph.show_backrefs(
    objgraph.by_type('QWidget')[0],
    max_depth=10,
    filename='widget_refs.png'
)
```

**Qt-Specific Use**: Find widgets/signals not being garbage collected.

### 3. Pympler muppy (HEAP ANALYSIS)

**Why**: Pure Python, no native dependencies, works on Windows.

```python
from pympler import muppy, summary

# Get all objects
all_objects = muppy.get_objects()

# Summary by type
sum1 = summary.summarize(all_objects)
summary.print_(sum1)

# Compare summaries
# ... do operations ...
all_objects2 = muppy.get_objects()
sum2 = summary.summarize(all_objects2)
diff = summary.get_diff(sum1, sum2)
summary.print_(diff)
```

### 4. psutil (RUNTIME MONITORING)

**Why**: Lightweight, production-safe, cross-platform.

```python
import psutil
import os

process = psutil.Process(os.getpid())

# Get memory info
mem_info = process.memory_info()
print(f"RSS: {mem_info.rss / 1024 / 1024:.2f} MB")
print(f"VMS: {mem_info.vms / 1024 / 1024:.2f} MB")

# Monitor over time
def log_memory():
    mem = process.memory_info()
    return {
        'rss_mb': mem.rss / 1024 / 1024,
        'vms_mb': mem.vms / 1024 / 1024,
        'percent': process.memory_percent()
    }
```

---

## PySide6/Qt-Specific Considerations

### Common Memory Leak Patterns in Qt

1. **Signal/Slot Connections Without Disconnect**
```python
# BAD: Connection keeps object alive
button.clicked.connect(handler)  # handler's object won't be GC'd

# GOOD: Disconnect when done
connection = button.clicked.connect(handler)
# Later:
button.clicked.disconnect(handler)
```

2. **Missing Parent in QObject Hierarchy**
```python
# BAD: No parent, may leak or be prematurely GC'd
widget = QWidget()

# GOOD: Set parent for automatic cleanup
widget = QWidget(parent=self)
```

3. **Closures Capturing Self**
```python
# BAD: Lambda captures self, prevents GC
self.timer.timeout.connect(lambda: self.do_something())

# GOOD: Use weak reference or explicit method
self.timer.timeout.connect(self.do_something)
```

4. **C++/Python Ownership Conflicts**
```python
# Use shiboken6 to check if C++ object is alive
from shiboken6 import isValid
if isValid(widget):
    widget.do_something()
```

### Qt Memory Debugging

```python
from PySide6.QtCore import QObject

# Track QObject destruction
def debug_destruction(obj, name):
    obj.destroyed.connect(lambda: print(f"{name} destroyed"))

# Use deleteLater for safe cleanup
widget.deleteLater()  # Schedules deletion after event loop
```

---

## Profiling Workflow for CasareRPA

### Development Phase

```
1. BASELINE
   - tracemalloc.start()
   - snapshot_baseline = take_snapshot()

2. OPERATION
   - Execute workflow(s)
   - Run UI interactions

3. ANALYZE
   - snapshot_after = take_snapshot()
   - Compare snapshots
   - Run objgraph.show_growth()

4. INVESTIGATE
   - objgraph.show_backrefs() for suspicious objects
   - Pympler summary for detailed breakdown

5. FIX
   - Add proper cleanup
   - Fix signal/slot connections
   - Add parents to QObjects
```

### Integration into CasareRPA

**Suggested Implementation**:

```python
# src/casare_rpa/utils/memory/profiler.py

import tracemalloc
import gc
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemorySnapshot:
    timestamp: datetime
    snapshot: tracemalloc.Snapshot
    rss_mb: float

class MemoryProfiler:
    """Memory profiling utility for CasareRPA development."""

    def __init__(self):
        self._snapshots: list[MemorySnapshot] = []
        self._enabled = False

    def start(self, nframe: int = 10):
        """Start memory tracking."""
        tracemalloc.start(nframe)
        self._enabled = True
        self.take_snapshot("start")

    def take_snapshot(self, label: str = ""):
        """Take a memory snapshot."""
        if not self._enabled:
            return
        import psutil
        import os

        gc.collect()
        snapshot = tracemalloc.take_snapshot()
        rss = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        self._snapshots.append(MemorySnapshot(
            timestamp=datetime.now(),
            snapshot=snapshot,
            rss_mb=rss
        ))

    def compare_last(self, top_n: int = 10):
        """Compare last two snapshots."""
        if len(self._snapshots) < 2:
            return []

        old = self._snapshots[-2].snapshot
        new = self._snapshots[-1].snapshot

        return new.compare_to(old, 'lineno')[:top_n]

    def get_trend(self):
        """Get RSS memory trend."""
        return [(s.timestamp, s.rss_mb) for s in self._snapshots]

    def stop(self):
        """Stop tracking and return summary."""
        tracemalloc.stop()
        self._enabled = False
        return self.get_trend()
```

### Continuous Monitoring Pattern

```python
# For long-running robot processes
import threading
import time

class MemoryMonitor:
    """Background memory monitor for production."""

    def __init__(self, interval_seconds: int = 60, threshold_mb: float = 500):
        self.interval = interval_seconds
        self.threshold = threshold_mb
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _monitor_loop(self):
        import psutil
        import os
        process = psutil.Process(os.getpid())

        while self._running:
            rss_mb = process.memory_info().rss / 1024 / 1024
            if rss_mb > self.threshold:
                logger.warning(f"Memory usage high: {rss_mb:.1f} MB")
                # Could trigger: gc.collect(), snapshot, alert
            time.sleep(self.interval)

    def stop(self):
        self._running = False
```

---

## Memory Optimization Patterns

### 1. Use __slots__ for Data Classes

```python
# Reduces memory per instance by ~40%
class WorkflowNode:
    __slots__ = ['id', 'type', 'properties', 'connections']

    def __init__(self, id, type, properties, connections):
        self.id = id
        self.type = type
        self.properties = properties
        self.connections = connections
```

### 2. Weak References for Caches

```python
import weakref

class NodeRegistry:
    def __init__(self):
        self._nodes = weakref.WeakValueDictionary()

    def register(self, node_id: str, node):
        self._nodes[node_id] = node

    def get(self, node_id: str):
        return self._nodes.get(node_id)  # Returns None if GC'd
```

### 3. Context Managers for Resources

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def browser_context():
    """Ensures browser cleanup."""
    browser = await playwright.chromium.launch()
    try:
        yield browser
    finally:
        await browser.close()
```

### 4. Generator for Large Data

```python
# BAD: Loads all into memory
def get_all_results():
    return [process(item) for item in huge_list]

# GOOD: Yields one at a time
def get_all_results():
    for item in huge_list:
        yield process(item)
```

### 5. Clear References Explicitly

```python
def process_workflow(workflow):
    data = load_large_data()
    result = process(data)

    # Explicit cleanup for large objects
    del data
    gc.collect()

    return result
```

---

## Recommended Profiling Commands

### Quick Memory Check
```bash
# Run with tracemalloc
python -X tracemalloc=10 run.py
```

### Profile Specific Workflow
```python
# In Python REPL or test
from casare_rpa.utils.memory.profiler import MemoryProfiler

profiler = MemoryProfiler()
profiler.start()

# Run workflow...
profiler.take_snapshot("after_workflow")

for stat in profiler.compare_last():
    print(stat)
```

### Find Reference Cycles
```python
import objgraph
import gc

gc.collect()
objgraph.show_growth(limit=30)

# After suspected leak
gc.collect()
objgraph.show_growth(limit=30)  # Shows what grew
```

---

## Dependencies to Add

```toml
# pyproject.toml - development dependencies
[project.optional-dependencies]
profiling = [
    "objgraph>=3.6.0",
    "pympler>=1.0.0",
    "psutil>=5.9.0",  # May already be present
]
```

---

## Summary Recommendations

| Scenario | Tool | Usage |
|----------|------|-------|
| Find memory growth | tracemalloc snapshots | Before/after comparison |
| Find reference cycles | objgraph | show_backrefs on suspects |
| Qt widget leaks | objgraph + destroyed signal | Track QObject lifecycle |
| Production monitoring | psutil | Lightweight RSS tracking |
| Deep heap analysis | Pympler muppy | Object-by-type breakdown |
| Visual flame graphs | Memray (Linux/macOS) | Allocation visualization |

---

## Sources

- [tracemalloc - Python Documentation](https://docs.python.org/3/library/tracemalloc.html)
- [memory-profiler - PyPI](https://pypi.org/project/memory-profiler/)
- [Pympler Documentation](https://pympler.readthedocs.io/en/latest/related.html)
- [Pympler GitHub](https://github.com/pympler/pympler)
- [Guppy 3 Documentation](https://zhuyifei1999.github.io/guppy3/)
- [Memory Profiling in Python - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2024/06/memory-profiling-in-python/)
- [Introduction to Memory Profiling - DataCamp](https://www.datacamp.com/tutorial/memory-profiling-python)
- [Top 5 Python Memory Profilers - Stackify](https://stackify.com/top-5-python-memory-profilers/)
- [Top 5 Python Libraries for Memory Optimization - JSSchools](https://jsschools.com/python/top-5-python-libraries-for-memory-optimization-and/)
- [Memory profiling with tracemalloc - Red Gate](https://www.red-gate.com/simple-talk/development/python/memory-profiling-in-python-with-tracemalloc/)
