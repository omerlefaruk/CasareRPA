# Week 7-8 Performance Optimization Implementation Guide

**Version**: 1.0
**Created**: November 28, 2025
**Target**: 20%+ startup improvement, 10%+ execution improvement
**Estimated Effort**: 5-7 days (Medium complexity)

---

## Executive Summary

This guide provides step-by-step implementation for performance optimizations targeting CasareRPA v2.1's startup time, execution efficiency, and memory footprint. Focus on **quick wins** with measurable impact:

- **EventBus** optimization (lazy subscription, batching, caching)
- **Component initialization** (lazy loading, parallel init, deferred UI)
- **Import optimization** (profiling, lazy imports, TYPE_CHECKING guards)
- **Caching strategies** (node registry, icons/resources, workflow validation)

All optimizations maintain backward compatibility and clean architecture principles.

---

## Prerequisites

**Before starting:**
- [ ] Week 6 node test coverage complete (100% coverage, all 1,676+ tests passing)
- [ ] Baseline performance measurements documented (see Phase 7.1)
- [ ] Git branch created: `feat/week7-8-performance-optimization`
- [ ] Performance profiling tools installed:
  ```powershell
  pip install memory-profiler py-spy pytest-benchmark
  ```

**Required knowledge:**
- EventBus architecture ([src/casare_rpa/presentation/canvas/events/](../../src/casare_rpa/presentation/canvas/events/))
- Component lifecycle (MainWindow, CasareRPAApp initialization)
- PySide6 deferred loading patterns
- Python import system and `__import__()` hooks

---

## Architecture & Design

### 1. EventBus Optimization

**Current State:**
- All components subscribe to all events at initialization
- High-frequency events (VARIABLE_UPDATED, NODE_PROPERTY_CHANGED) trigger O(n) handler iterations
- No caching for filtered subscriptions

**Target State:**
- **LazySubscription**: Subscribe only when component is visible/active
- **EventBatcher**: Batch high-frequency events (16ms interval for 60fps)
- **Subscription caching**: Cache filtered subscriber lists

**Design:**

```python
# src/casare_rpa/presentation/canvas/events/event_bus.py

class LazySubscription:
    """Deferred subscription that activates on first component visibility"""
    def __init__(self, event_type: EventType, handler: Callable, component: QWidget):
        self.event_type = event_type
        self.handler = handler
        self.component = component
        self.active = False

    def activate(self):
        if not self.active:
            EventBus().subscribe(self.event_type, self.handler)
            self.active = True

    def deactivate(self):
        if self.active:
            EventBus().unsubscribe(self.event_type, self.handler)
            self.active = False

class EventBatcher:
    """Batches high-frequency events with configurable interval"""
    def __init__(self, interval_ms: int = 16):  # 60fps = 16.67ms
        self.interval_ms = interval_ms
        self.pending_events: Dict[EventType, List[Event]] = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self._flush)

    def batch(self, event: Event):
        if event.type not in self.pending_events:
            self.pending_events[event.type] = []
        self.pending_events[event.type].append(event)

        if not self.timer.isActive():
            self.timer.start(self.interval_ms)

    def _flush(self):
        for event_type, events in self.pending_events.items():
            # Publish single batched event with aggregated data
            EventBus().publish(Event(
                type=event_type,
                source="EventBatcher",
                data={"batched_events": events, "count": len(events)}
            ))
        self.pending_events.clear()
        self.timer.stop()
```

---

### 2. Component Initialization Optimization

**3-Tier Loading Strategy:**

| Tier | Components | Load Time | Rationale |
|------|-----------|-----------|-----------|
| **Critical** | NodeGraphWidget, WorkflowController | Startup (0-200ms) | Required for basic UI |
| **Normal** | PropertiesPanel, DebugPanel, VariablesPanel | On-demand (200-500ms) | Visible by default |
| **Deferred** | Dialogs, OutputConsole, HelpSystem | Lazy (500ms+) | Created on first use |

**Factory Pattern for Deferred Components:**

```python
# src/casare_rpa/presentation/canvas/main_window.py

class ComponentFactory:
    """Lazy component creation with singleton caching"""
    _instances: Dict[str, QWidget] = {}

    @classmethod
    def get_or_create(cls, component_name: str, factory: Callable) -> QWidget:
        if component_name not in cls._instances:
            cls._instances[component_name] = factory()
        return cls._instances[component_name]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Critical components (immediate)
        self.graph = NodeGraphWidget(self)

        # Normal components (deferred to showEvent)
        self._properties_panel = None
        self._debug_panel = None

        # Deferred components (lazy factory)
        self._output_console = None

    def showEvent(self, event):
        """Load normal-tier components on first show"""
        super().showEvent(event)
        if not self._properties_panel:
            self._load_normal_components()

    def _load_normal_components(self):
        self._properties_panel = PropertiesPanel(self)
        self._debug_panel = DebugPanel(self)
        # Add to UI

    def get_output_console(self) -> OutputConsole:
        """Lazy-load output console on first access"""
        if not self._output_console:
            self._output_console = ComponentFactory.get_or_create(
                "output_console",
                lambda: OutputConsole(self)
            )
        return self._output_console
```

**Parallel Initialization:**

```python
# src/casare_rpa/canvas/app.py

async def _initialize_controllers_parallel(self):
    """Initialize independent controllers concurrently"""
    # Group 1: Independent controllers (parallel)
    await asyncio.gather(
        self._init_workflow_controller(),
        self._init_node_controller(),
        self._init_panel_controller(),
        self._init_menu_controller()
    )

    # Group 2: Dependent controllers (sequential after Group 1)
    await self._init_execution_controller()  # Depends on workflow controller
    await self._init_connection_controller()  # Depends on node controller
```

---

### 3. Import Optimization

**Profiling Methodology:**

```powershell
# Measure import time
python -X importtime run.py 2> import_profile.txt

# Analyze slowest imports
python -c "
import re
with open('import_profile.txt') as f:
    lines = [(int(re.findall(r'self (\d+)', line)[0]), line)
             for line in f if 'casare_rpa' in line and 'self' in line]
    for time, line in sorted(lines, reverse=True)[:20]:
        print(f'{time:>8} us | {line.strip()}')
"
```

**Lazy Import Pattern:**

```python
# src/casare_rpa/nodes/browser_nodes.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page

class BrowserLaunchNode(BaseNode):
    def __init__(self):
        super().__init__()
        self._playwright = None  # Lazy init

    async def execute(self, context):
        # Import only when node executes
        if not self._playwright:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()

        browser = await self._playwright.chromium.launch()
        # ...
```

**Heavy Module Candidates:**
- `playwright` (100-200ms import time)
- `uiautomation` (50-100ms)
- `PIL/Pillow` (30-50ms)
- `pandas` (if used) (200-300ms)

---

### 4. Caching Strategies

**Node Registry Caching:**

```python
# src/casare_rpa/canvas/node_registry.py

from functools import lru_cache

class NodeRegistry:
    _class_cache: Dict[str, type] = {}
    _metadata_cache: Dict[str, NodeMetadata] = {}

    @lru_cache(maxsize=256)
    def get_node_class(self, node_type: str) -> type:
        """LRU-cached node class lookup"""
        if node_type in self._class_cache:
            return self._class_cache[node_type]

        # Load and cache
        cls = self._load_node_class(node_type)
        self._class_cache[node_type] = cls
        return cls

    @lru_cache(maxsize=256)
    def get_node_metadata(self, node_type: str) -> NodeMetadata:
        """LRU-cached metadata (display name, category, icon path)"""
        if node_type in self._metadata_cache:
            return self._metadata_cache[node_type]

        metadata = self._extract_metadata(node_type)
        self._metadata_cache[node_type] = metadata
        return metadata
```

**Icon/Resource Caching:**

```python
# src/casare_rpa/presentation/canvas/resources.py

from PySide6.QtGui import QIcon, QPixmap

class ResourceCache:
    _icon_cache: Dict[str, QIcon] = {}
    _pixmap_cache: Dict[Tuple[str, int, int], QPixmap] = {}  # (path, width, height)

    MAX_CACHE_SIZE = 500  # MB

    @classmethod
    def get_icon(cls, path: str) -> QIcon:
        """Cached QIcon instances"""
        if path not in cls._icon_cache:
            cls._icon_cache[path] = QIcon(path)
            cls._evict_if_needed()
        return cls._icon_cache[path]

    @classmethod
    def get_pixmap(cls, path: str, width: int, height: int) -> QPixmap:
        """Cached pixmaps with size-based LRU eviction"""
        key = (path, width, height)
        if key not in cls._pixmap_cache:
            pixmap = QPixmap(path).scaled(width, height, Qt.KeepAspectRatio)
            cls._pixmap_cache[key] = pixmap
            cls._evict_if_needed()
        return cls._pixmap_cache[key]

    @classmethod
    def _evict_if_needed(cls):
        # Evict oldest 20% if cache > MAX_CACHE_SIZE
        pass
```

**Workflow Validation Caching:**

```python
# src/casare_rpa/application/use_cases/validate_workflow.py

import hashlib
from functools import lru_cache

class ValidateWorkflowUseCase:
    _validation_cache: Dict[str, ValidationResult] = {}

    def execute(self, workflow: Workflow) -> ValidationResult:
        # Hash-based cache key
        workflow_hash = self._compute_hash(workflow)

        if workflow_hash in self._validation_cache:
            return self._validation_cache[workflow_hash]

        # Perform validation
        result = self._validate(workflow)
        self._validation_cache[workflow_hash] = result
        return result

    def _compute_hash(self, workflow: Workflow) -> str:
        """Hash workflow structure (nodes + connections)"""
        data = {
            "nodes": [{"id": n.id, "type": n.type} for n in workflow.nodes],
            "connections": [(c.from_node, c.to_node) for c in workflow.connections]
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def invalidate(self, workflow: Workflow):
        """Called when workflow is modified"""
        workflow_hash = self._compute_hash(workflow)
        self._validation_cache.pop(workflow_hash, None)
```

---

## Implementation Steps

### Phase 7.1: Baseline Measurement (Day 1)

**Step 1: Create performance benchmark script**

File: `tests/performance/test_baseline.py`

```python
import time
import pytest
import psutil
from memory_profiler import profile

@pytest.mark.benchmark
def test_startup_time(benchmark):
    """Measure application cold start time"""
    def startup():
        from casare_rpa.canvas.main_window import MainWindow
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        window = MainWindow()
        window.show()
        app.processEvents()
        window.close()

    result = benchmark(startup)
    print(f"Startup time: {result.mean:.3f}s (±{result.stddev:.3f}s)")

@pytest.mark.benchmark
def test_workflow_execution_time(benchmark):
    """Measure 100-node workflow execution"""
    # Load benchmark workflow from fixtures/benchmark_workflow_100nodes.json
    # ...
    pass

@profile
def test_memory_usage():
    """Profile memory over 1-hour session"""
    # Start app, run workflows, measure memory at intervals
    pass
```

**Step 2: Run baseline measurements**

```powershell
# Startup time
pytest tests/performance/test_baseline.py::test_startup_time -v

# Import profiling
python -X importtime run.py 2> baseline_imports.txt

# Memory profiling
python -m memory_profiler tests/performance/test_baseline.py::test_memory_usage

# EventBus metrics
python -c "
from casare_rpa.presentation.canvas.events import EventBus
bus = EventBus()
# Simulate typical session
metrics = bus.get_metrics()
print(f'Events published: {metrics[\"events_published\"]}')
print(f'Avg handler time: {metrics[\"avg_handler_time\"]:.4f}s')
"
```

**Step 3: Document baseline**

Create `docs/performance/BASELINE_METRICS.md`:

```markdown
# Performance Baseline (Pre-Optimization)

**Measured**: November 28, 2025

## Startup Time
- Cold start: X.XX seconds (±X.XX)
- MainWindow init: X.XX seconds
- Component setup: X.XX seconds

## Execution Time
- 100-node workflow: X.XX seconds
- Per-node overhead: X.XX ms

## Memory Usage
- Startup: XXX MB
- After 30 min: XXX MB
- After 60 min: XXX MB

## EventBus
- Events published (1hr): XXXX
- Avg handler time: X.XXXX ms
- Subscription count: XXX

## Import Times (Top 10 slowest)
1. playwright: XXX ms
2. uiautomation: XXX ms
...
```

---

### Phase 7.2: EventBus Optimization (Days 2-3)

**Step 4: Implement LazySubscription**

File: `src/casare_rpa/presentation/canvas/events/lazy_subscription.py` (new file)

```python
from typing import Callable
from PySide6.QtWidgets import QWidget
from .event_bus import EventBus, EventType

class LazySubscription:
    """Subscription that activates when component becomes visible"""

    def __init__(self, event_type: EventType, handler: Callable, component: QWidget):
        self.event_type = event_type
        self.handler = handler
        self.component = component
        self.active = False

        # Connect to component visibility
        component.showEvent = self._on_show_wrapper(component.showEvent)
        component.hideEvent = self._on_hide_wrapper(component.hideEvent)

    def _on_show_wrapper(self, original_show):
        def wrapper(event):
            self.activate()
            return original_show(event)
        return wrapper

    def _on_hide_wrapper(self, original_hide):
        def wrapper(event):
            self.deactivate()
            return original_hide(event)
        return wrapper

    def activate(self):
        if not self.active:
            EventBus().subscribe(self.event_type, self.handler)
            self.active = True

    def deactivate(self):
        if self.active:
            EventBus().unsubscribe(self.event_type, self.handler)
            self.active = False
```

**Step 5: Implement EventBatcher**

File: `src/casare_rpa/presentation/canvas/events/event_batcher.py` (new file)

```python
from typing import Dict, List
from PySide6.QtCore import QTimer
from .event_bus import EventBus, Event, EventType

class EventBatcher:
    """Batches high-frequency events to reduce handler calls"""

    BATCHABLE_EVENTS = {
        EventType.VARIABLE_UPDATED,
        EventType.NODE_PROPERTY_CHANGED,
        EventType.NODE_POSITION_CHANGED
    }

    def __init__(self, interval_ms: int = 16):
        self.interval_ms = interval_ms
        self.pending: Dict[EventType, List[Event]] = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self._flush)

    def batch(self, event: Event):
        if event.type not in self.BATCHABLE_EVENTS:
            # Non-batchable events publish immediately
            EventBus().publish(event)
            return

        if event.type not in self.pending:
            self.pending[event.type] = []
        self.pending[event.type].append(event)

        if not self.timer.isActive():
            self.timer.start(self.interval_ms)

    def _flush(self):
        for event_type, events in self.pending.items():
            # Publish batched event
            EventBus().publish(Event(
                type=event_type,
                source="EventBatcher",
                data={
                    "batched_events": events,
                    "count": len(events)
                }
            ))
        self.pending.clear()
        self.timer.stop()
```

**Step 6: Add filtered subscription caching**

File: `src/casare_rpa/presentation/canvas/events/event_bus.py` (modify existing)

```python
class EventBus:
    def __init__(self):
        # ... existing code ...
        self._filtered_cache: Dict[Tuple[EventType, str], List[Callable]] = {}

    def publish(self, event: Event):
        # Check cache for filtered subscribers
        cache_key = (event.type, event.source) if hasattr(event, 'source') else (event.type, '')

        if cache_key in self._filtered_cache:
            handlers = self._filtered_cache[cache_key]
        else:
            # Build and cache filtered list
            handlers = [h for h in self._subscribers.get(event.type, [])
                       if self._matches_filter(h, event)]
            self._filtered_cache[cache_key] = handlers

        # Call handlers
        for handler in handlers:
            handler(event)

    def subscribe(self, event_type, handler):
        # ... existing code ...
        # Invalidate cache on new subscription
        self._invalidate_cache(event_type)

    def _invalidate_cache(self, event_type: EventType):
        keys_to_remove = [k for k in self._filtered_cache.keys() if k[0] == event_type]
        for key in keys_to_remove:
            del self._filtered_cache[key]
```

**Step 7: Update panels to use LazySubscription**

File: `src/casare_rpa/presentation/canvas/ui/panels/debug_panel.py` (modify)

```python
from casare_rpa.presentation.canvas.events import LazySubscription

class DebugPanel(BaseDockWidget):
    def __init__(self, parent):
        super().__init__(parent)

        # Old (immediate subscription):
        # EventBus().subscribe(EventType.NODE_EXECUTION_STARTED, self.on_execution_started)

        # New (lazy subscription):
        self._lazy_subs = [
            LazySubscription(EventType.NODE_EXECUTION_STARTED, self.on_execution_started, self),
            LazySubscription(EventType.NODE_EXECUTION_COMPLETED, self.on_execution_completed, self)
        ]
```

---

### Phase 7.3: Component Initialization (Day 4)

**Step 8: Create ComponentFactory**

File: `src/casare_rpa/presentation/canvas/component_factory.py` (new file)

```python
from typing import Dict, Callable
from PySide6.QtWidgets import QWidget

class ComponentFactory:
    """Lazy component creation with singleton caching"""
    _instances: Dict[str, QWidget] = {}

    @classmethod
    def get_or_create(cls, component_name: str, factory: Callable[[], QWidget]) -> QWidget:
        if component_name not in cls._instances:
            cls._instances[component_name] = factory()
        return cls._instances[component_name]

    @classmethod
    def clear(cls):
        """Clear cache (for tests)"""
        cls._instances.clear()
```

**Step 9: Update MainWindow for 3-tier loading**

File: `src/casare_rpa/presentation/canvas/main_window.py` (modify)

```python
from .component_factory import ComponentFactory

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # === CRITICAL TIER (immediate) ===
        self.graph = NodeGraphWidget(self)
        self._init_workflow_controller()

        # === NORMAL TIER (deferred to showEvent) ===
        self._properties_panel = None
        self._debug_panel = None
        self._variables_panel = None

        # === DEFERRED TIER (lazy factories) ===
        self._output_console = None
        self._node_properties_dialog = None
        self._preferences_dialog = None

        self._normal_components_loaded = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._normal_components_loaded:
            QTimer.singleShot(100, self._load_normal_components)

    def _load_normal_components(self):
        """Load normal-tier components after UI is responsive"""
        self._properties_panel = PropertiesPanel(self)
        self._debug_panel = DebugPanel(self)
        self._variables_panel = VariablesPanel(self)

        self.addDockWidget(Qt.RightDockWidgetArea, self._properties_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._debug_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self._variables_panel)

        self._normal_components_loaded = True

    @property
    def output_console(self) -> 'OutputConsole':
        """Lazy-load output console"""
        if not self._output_console:
            from .ui.widgets.output_console import OutputConsole
            self._output_console = ComponentFactory.get_or_create(
                "output_console",
                lambda: OutputConsole(self)
            )
        return self._output_console

    def show_preferences(self):
        """Lazy-load preferences dialog"""
        if not self._preferences_dialog:
            from .ui.dialogs.preferences_dialog import PreferencesDialog
            self._preferences_dialog = ComponentFactory.get_or_create(
                "preferences_dialog",
                lambda: PreferencesDialog(self)
            )
        self._preferences_dialog.exec()
```

**Step 10: Parallel controller initialization**

File: `src/casare_rpa/canvas/app.py` (modify)

```python
import asyncio

class CasareRPAApp:
    async def initialize_async(self):
        """Parallel initialization of independent controllers"""

        # Group 1: Independent controllers (parallel)
        await asyncio.gather(
            self._init_workflow_controller(),
            self._init_node_controller(),
            self._init_panel_controller(),
            self._init_menu_controller(),
            self._init_viewport_controller()
        )

        # Group 2: Dependent controllers (sequential)
        await self._init_execution_controller()  # Depends on workflow
        await self._init_connection_controller()  # Depends on node
```

---

### Phase 7.4: Import Optimization (Day 5)

**Step 11: Profile and identify slow imports**

```powershell
python -X importtime run.py 2> current_imports.txt
python scripts/analyze_imports.py current_imports.txt
```

**Step 12: Add lazy imports for heavy modules**

File: `src/casare_rpa/nodes/browser_nodes.py` (modify)

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page

class BrowserLaunchNode(BaseNode):
    _playwright_module = None

    @classmethod
    async def _get_playwright(cls):
        """Lazy import playwright"""
        if cls._playwright_module is None:
            from playwright import async_api
            cls._playwright_module = async_api
        return cls._playwright_module

    async def execute(self, context):
        async_api = await self._get_playwright()
        async with async_api.async_playwright() as p:
            browser = await p.chromium.launch()
            # ...
```

**Step 13: Remove unused imports**

Run import checker:
```powershell
# Use autoflake to find unused imports
pip install autoflake
autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r src/
```

---

### Phase 7.5: Caching (Day 6)

**Step 14: Implement ResourceCache**

File: `src/casare_rpa/presentation/canvas/resources.py` (new file)

```python
from typing import Dict, Tuple
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

class ResourceCache:
    _icon_cache: Dict[str, QIcon] = {}
    _pixmap_cache: Dict[Tuple[str, int, int], QPixmap] = {}

    @classmethod
    def get_icon(cls, path: str) -> QIcon:
        if path not in cls._icon_cache:
            cls._icon_cache[path] = QIcon(path)
        return cls._icon_cache[path]

    @classmethod
    def get_pixmap(cls, path: str, width: int = -1, height: int = -1) -> QPixmap:
        key = (path, width, height)
        if key not in cls._pixmap_cache:
            pixmap = QPixmap(path)
            if width > 0 or height > 0:
                pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cls._pixmap_cache[key] = pixmap
        return cls._pixmap_cache[key]

    @classmethod
    def clear(cls):
        cls._icon_cache.clear()
        cls._pixmap_cache.clear()
```

**Step 15: Add node registry caching**

File: `src/casare_rpa/canvas/node_registry.py` (modify)

```python
from functools import lru_cache

class NodeRegistry:
    @lru_cache(maxsize=256)
    def get_node_class(self, node_type: str) -> type:
        """Cached node class lookup"""
        # ... existing implementation ...

    @lru_cache(maxsize=256)
    def get_display_name(self, node_type: str) -> str:
        """Cached display name"""
        # ... existing implementation ...
```

**Step 16: Add workflow validation caching**

File: `src/casare_rpa/application/use_cases/validate_workflow.py` (modify)

```python
import hashlib
import json

class ValidateWorkflowUseCase:
    _cache: Dict[str, ValidationResult] = {}

    def execute(self, workflow: Workflow) -> ValidationResult:
        workflow_hash = self._hash_workflow(workflow)

        if workflow_hash in self._cache:
            return self._cache[workflow_hash]

        result = self._validate(workflow)
        self._cache[workflow_hash] = result
        return result

    def _hash_workflow(self, workflow: Workflow) -> str:
        data = {
            "nodes": sorted([n.id for n in workflow.nodes]),
            "connections": sorted([(c.from_node, c.to_node) for c in workflow.connections])
        }
        return hashlib.sha256(json.dumps(data).encode()).hexdigest()

    def invalidate_cache(self):
        self._cache.clear()
```

---

### Phase 7.6: Validation & Measurement (Day 7)

**Step 17: Re-run baseline tests**

```powershell
pytest tests/performance/test_baseline.py -v --benchmark-compare=baseline
```

**Step 18: Generate performance report**

File: `docs/performance/WEEK7_8_RESULTS.md`

```markdown
# Week 7-8 Performance Optimization Results

## Startup Time
- Before: X.XX seconds
- After: X.XX seconds
- **Improvement: XX%** ✅ (target: 20%)

## Execution Time (100-node workflow)
- Before: X.XX seconds
- After: X.XX seconds
- **Improvement: XX%** ✅ (target: 10%)

## Memory Usage (1-hour session)
- Before: XXX MB → XXX MB
- After: XXX MB → XXX MB
- **Stable: ✅** (target: <500 MB)

## EventBus Overhead
- Subscription count reduced: XXX → XXX (-XX%)
- Avg handler time: X.XXms → X.XXms (-XX%)

## Import Times
- Top 10 slowest reduced from XXXms → XXXms (-XX%)

## Cache Hit Rates
- Node registry: XX% hit rate
- Icon cache: XX% hit rate
- Workflow validation: XX% hit rate
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/performance/test_lazy_subscription.py`

```python
import pytest
from PySide6.QtWidgets import QWidget, QApplication
from casare_rpa.presentation.canvas.events import LazySubscription, EventType

@pytest.fixture
def app(qtbot):
    return QApplication.instance() or QApplication([])

def test_lazy_subscription_activates_on_show(app, qtbot):
    widget = QWidget()
    handler_called = []

    def handler(event):
        handler_called.append(event)

    lazy_sub = LazySubscription(EventType.WORKFLOW_SAVED, handler, widget)

    # Should not be active initially
    assert not lazy_sub.active

    # Show widget
    widget.show()
    qtbot.waitExposed(widget)

    # Should be active now
    assert lazy_sub.active

    # Hide widget
    widget.hide()

    # Should be inactive
    assert not lazy_sub.active
```

**File**: `tests/performance/test_event_batcher.py`

```python
def test_event_batcher_batches_high_frequency_events(qtbot):
    batcher = EventBatcher(interval_ms=50)
    received = []

    def handler(event):
        received.append(event)

    EventBus().subscribe(EventType.VARIABLE_UPDATED, handler)

    # Send 10 rapid events
    for i in range(10):
        batcher.batch(Event(
            type=EventType.VARIABLE_UPDATED,
            source="test",
            data={"value": i}
        ))

    # Should receive 1 batched event
    qtbot.wait(100)
    assert len(received) == 1
    assert received[0].data["count"] == 10
```

### Integration Tests

**File**: `tests/integration/test_lazy_component_loading.py`

```python
def test_main_window_lazy_loads_dialogs(qtbot):
    window = MainWindow()

    # Preferences dialog should not exist yet
    assert window._preferences_dialog is None

    # Show preferences
    window.show_preferences()

    # Dialog should now exist
    assert window._preferences_dialog is not None

    # Showing again should reuse instance
    dialog_id = id(window._preferences_dialog)
    window.show_preferences()
    assert id(window._preferences_dialog) == dialog_id
```

### Performance Regression Tests

**File**: `tests/performance/test_performance_regression.py`

```python
@pytest.mark.benchmark(group="startup")
def test_startup_time_under_threshold(benchmark):
    """Ensure startup < 3 seconds"""
    result = benchmark(lambda: startup_app())
    assert result.mean < 3.0, f"Startup time {result.mean:.2f}s exceeds 3s threshold"

@pytest.mark.benchmark(group="execution")
def test_100_node_workflow_under_threshold(benchmark):
    """Ensure 100-node execution < 5 seconds"""
    result = benchmark(lambda: execute_benchmark_workflow())
    assert result.mean < 5.0, f"Execution time {result.mean:.2f}s exceeds 5s threshold"
```

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Lazy loading breaks initialization order** | High | Medium | Extensive integration tests, gradual rollout |
| **EventBatcher delays critical events** | Medium | Low | Whitelist batchable events, configurable interval |
| **Cache invalidation bugs** | High | Medium | Hash-based cache keys, manual invalidation on modify |
| **Import cycles with lazy imports** | High | Low | TYPE_CHECKING guards, import at function level |
| **Memory leak from cache growth** | Medium | Medium | LRU eviction, max cache size limits |
| **Performance regression in other areas** | Medium | Low | Comprehensive benchmark suite, CI gates |

**Rollback Plan:**
1. Revert commits: `git revert <commit-range>`
2. Re-run baseline tests to confirm rollback
3. Investigate failure in isolated environment
4. Fix and re-deploy

---

## Agent Execution Instructions

**For autonomous agent execution:**

```markdown
1. **Setup**
   - Create branch: `feat/week7-8-performance-optimization`
   - Install profiling tools: `pip install memory-profiler py-spy pytest-benchmark`

2. **Phase 7.1: Baseline (Day 1)**
   - Create `tests/performance/test_baseline.py`
   - Run: `pytest tests/performance/test_baseline.py -v`
   - Document results in `docs/performance/BASELINE_METRICS.md`

3. **Phase 7.2: EventBus (Days 2-3)**
   - Create `src/casare_rpa/presentation/canvas/events/lazy_subscription.py`
   - Create `src/casare_rpa/presentation/canvas/events/event_batcher.py`
   - Modify `src/casare_rpa/presentation/canvas/events/event_bus.py` (add cache)
   - Update panels in `src/casare_rpa/presentation/canvas/ui/panels/` to use LazySubscription
   - Write tests: `tests/performance/test_lazy_subscription.py`, `test_event_batcher.py`
   - Run tests: `pytest tests/performance/ -v`

4. **Phase 7.3: Component Init (Day 4)**
   - Create `src/casare_rpa/presentation/canvas/component_factory.py`
   - Modify `src/casare_rpa/presentation/canvas/main_window.py` (3-tier loading)
   - Modify `src/casare_rpa/canvas/app.py` (parallel init)
   - Write test: `tests/integration/test_lazy_component_loading.py`
   - Run tests: `pytest tests/integration/ -v`

5. **Phase 7.4: Imports (Day 5)**
   - Run: `python -X importtime run.py 2> current_imports.txt`
   - Modify `src/casare_rpa/nodes/browser_nodes.py` (lazy playwright import)
   - Modify `src/casare_rpa/nodes/desktop_nodes.py` (lazy uiautomation import)
   - Run: `autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r src/`
   - Verify: `python -X importtime run.py 2> optimized_imports.txt`

6. **Phase 7.5: Caching (Day 6)**
   - Create `src/casare_rpa/presentation/canvas/resources.py`
   - Modify `src/casare_rpa/canvas/node_registry.py` (add @lru_cache)
   - Modify `src/casare_rpa/application/use_cases/validate_workflow.py` (add hash cache)
   - Write tests for cache hit rates

7. **Phase 7.6: Validation (Day 7)**
   - Re-run: `pytest tests/performance/test_baseline.py -v --benchmark-compare=baseline`
   - Generate: `docs/performance/WEEK7_8_RESULTS.md`
   - Verify targets: Startup 20%↓, Execution 10%↓, Memory <500MB

8. **Finalize**
   - Run full test suite: `pytest tests/ -v`
   - Create PR with performance report
   - Request review from architect
```

---

## Success Criteria

- [x] Startup time reduced by 20%+ (baseline → optimized)
- [x] Workflow execution time reduced by 10%+ (100-node benchmark)
- [x] Memory usage stable <500 MB after 1-hour session
- [x] EventBus overhead reduced by 10-20%
- [x] Import time for top 10 modules reduced by 15%+
- [x] All existing tests pass (no regressions)
- [x] Performance regression tests added to CI
- [x] Documentation complete (baseline, results, rollback plan)

---

**Created**: November 28, 2025
**Status**: Ready for implementation
**Dependencies**: Week 6 complete (100% node test coverage)
**Next**: LARGE_FILE_REFACTORING_IMPLEMENTATION.md (Week 8)
