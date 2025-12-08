# PySide6/Qt Performance Optimization Research

**Date**: 2025-12-05
**Focus**: Canvas application performance optimization
**Researcher**: Claude (Research Specialist)

---

## Executive Summary

This research identifies Qt/PySide6 performance optimization techniques applicable to CasareRPA's node-based canvas. The codebase already implements several best practices (viewport culling, animation coordination, cache disabling). This report documents additional optimization opportunities.

---

## 1. QGraphicsView Optimization

### 1.1 Viewport Update Modes

| Mode | Use Case | Performance |
|------|----------|-------------|
| `FullViewportUpdate` | Simple scenes | Slowest |
| `MinimalViewportUpdate` | Complex, changing scenes | Better |
| `SmartViewportUpdate` | Default, auto-decides | Good |
| `BoundingRectViewportUpdate` | Many overlapping items | Fast |
| `NoViewportUpdate` | Manual control | Fastest |

**Recommendation**: For node canvas, use `BoundingRectViewportUpdate`. CasareRPA nodes don't heavily overlap, and this mode only repaints affected regions.

### 1.2 Item Caching

| Cache Mode | Use Case | Trade-off |
|------------|----------|-----------|
| `NoCache` | Dynamic items (moving/animating) | No memory, always repaints |
| `ItemCoordinateCache` | Items that move but don't change internally | Medium memory |
| `DeviceCoordinateCache` | Static items at fixed scale | High memory, scale issues |

**CasareRPA Status**: Already correctly disabled caching in `node_graph_widget.py` (lines 51-66) because NodeGraphQt's `DeviceCoordinateCache` causes zoom/pan glitches.

**Recommendation**: Keep `NoCache`. For static elements (background grid), consider `DeviceCoordinateCache` if regenerating at zoom levels.

### 1.3 BSP Tree Indexing

```python
# For 100+ nodes, tune BSP tree
scene.setItemIndexMethod(QGraphicsScene.BspTreeIndex)
scene.setBspTreeDepth(4)  # Default is auto, 4 is good for ~100-500 items
```

For scenes with many moving items (during drag operations), temporarily switch:
```python
scene.setItemIndexMethod(QGraphicsScene.NoIndex)  # During bulk operations
scene.setItemIndexMethod(QGraphicsScene.BspTreeIndex)  # After
```

### 1.4 Optimization Flags

```python
view.setOptimizationFlags(
    QGraphicsView.DontSavePainterState |  # Skip painter save/restore
    QGraphicsView.DontAdjustForAntialiasing  # If not using antialiasing
)
```

**CasareRPA Status**: Not currently set. Adding these could improve paint performance.

---

## 2. Paint Event Optimization

### 2.1 Update Regions

Only repaint what changed:
```python
def paintEvent(self, event):
    painter = QPainter(self)
    rect = event.rect()  # Dirty region only
    # Paint only within rect
```

### 2.2 Double Buffering

Qt handles double buffering automatically. To disable for custom control:
```python
widget.setAttribute(Qt.WA_PaintOnScreen, True)  # Disable double buffer
```

### 2.3 Opaque Widgets

```python
# For widgets that fill their background completely
widget.setAttribute(Qt.WA_OpaquePaintEvent, True)
```

This tells Qt not to clear the background before painting.

### 2.4 Batch Updates

```python
# During bulk operations
widget.setUpdatesEnabled(False)
# ... perform many changes ...
widget.setUpdatesEnabled(True)  # Triggers single repaint
```

**CasareRPA Opportunity**: Use during workflow loading/deserialization.

---

## 3. Widget Creation/Destruction Patterns

### 3.1 Avoid Dynamic Creation

**Problem**: Creating/destroying widgets is expensive (memory allocation, signal setup, style calculation).

**Patterns**:
1. **Object Pool**: Pre-create widgets, hide/show instead of create/delete
2. **QStackedWidget**: Keep multiple views, switch visibility
3. **Model-View**: For lists, use `QListView` + delegates instead of per-item widgets

```python
class WidgetPool:
    def __init__(self, factory, initial_size=10):
        self._available = [factory() for _ in range(initial_size)]
        self._factory = factory

    def acquire(self):
        if self._available:
            widget = self._available.pop()
            widget.show()
            return widget
        return self._factory()

    def release(self, widget):
        widget.hide()
        widget.setParent(None)
        self._available.append(widget)
```

**CasareRPA Opportunity**: Node property widgets could benefit from pooling if many nodes are created/deleted rapidly.

### 3.2 deleteLater() Usage

Always use `deleteLater()` instead of `del` or `delete`:
```python
widget.deleteLater()  # Safe - deferred to event loop
# NOT: del widget  # Dangerous - immediate, may crash if signals pending
```

**CasareRPA Status**: Should audit codebase for direct widget deletion.

---

## 4. Signal/Slot Performance

### 4.1 Performance Overhead

| Connection Type | Overhead vs Direct Call |
|-----------------|-------------------------|
| Direct (same thread) | ~10x slower |
| Queued (same thread) | ~50x slower |
| Queued (cross-thread) | ~100x slower |

**Key Insight**: The ~10x overhead is negligible compared to any heap allocation. Signal/slot overhead only matters in tight loops.

### 4.2 Optimization Strategies

1. **Use direct connections for in-thread**:
   ```python
   signal.connect(slot, Qt.DirectConnection)
   ```

2. **Batch emissions**: Emit once with all data, not multiple times
   ```python
   # Bad
   for item in items:
       self.item_added.emit(item)

   # Good
   self.items_added.emit(items)
   ```

3. **Disconnect unused signals**:
   ```python
   connection = signal.connect(slot)
   # Later...
   signal.disconnect(connection)  # Or QObject.disconnect(connection)
   ```

4. **Use context objects for auto-disconnect**:
   ```python
   # Connection auto-disconnects when context_obj is destroyed
   signal.connect(lambda: ..., context_obj, Qt.QueuedConnection)
   ```

**CasareRPA Status**: EventBus already centralizes events. Consider coalescing high-frequency events.

---

## 5. QTimer vs QThread Patterns

### 5.1 When to Use Each

| Scenario | Use |
|----------|-----|
| Periodic UI updates | QTimer |
| Polling (short intervals) | QTimer |
| CPU-intensive work | QThread + Worker |
| I/O operations | QThread or asyncio |
| Animations | QTimer (or QPropertyAnimation) |

### 5.2 Worker Pattern (Recommended for QThread)

```python
class Worker(QObject):
    finished = Signal()
    result = Signal(object)

    def run(self):
        # Heavy work here
        self.result.emit(data)
        self.finished.emit()

# Usage
thread = QThread()
worker = Worker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
worker.finished.connect(worker.deleteLater)
thread.finished.connect(thread.deleteLater)
thread.start()
```

### 5.3 Timer Optimization

```python
# Coalesce timer events
timer.setTimerType(Qt.CoarseTimer)  # ~5% accuracy, lower CPU

# For one-shot delays
QTimer.singleShot(1000, callback)  # More efficient than creating timer
```

**CasareRPA Status**:
- Animation coordinator uses single shared timer (50ms/20 FPS) - GOOD
- Viewport culling uses 33ms timer (30 FPS) - GOOD
- Consider `CoarseTimer` for both to reduce wake-ups

---

## 6. Stylesheet (QSS) Performance

### 6.1 Performance Impact

- Startup: Large QSS files add 2-4 seconds to startup
- Widget creation: QSS reapplied on every widget instantiation
- Reparenting: Style reset on parent change

### 6.2 Optimization Strategies

| Strategy | Impact |
|----------|--------|
| Keep QSS minimal | Faster parsing |
| Generic selectors | Less matching overhead |
| Apply after construction | Batch style calculation |
| Dynamic properties over QSS changes | Faster updates |

```python
# Use dynamic properties for state changes
widget.setProperty("state", "running")
widget.style().polish(widget)  # Force style recalc

# QSS uses property selector
# QPushButton[state="running"] { ... }
```

### 6.3 Alternatives to QSS

For performance-critical widgets:
1. **QStyle subclass**: Maximum control, no parsing overhead
2. **Custom paint**: Direct `paintEvent()` implementation
3. **QML/Qt Quick**: Hardware-accelerated rendering

**CasareRPA Status**: Uses dataclass-based theme (`theme.py`). This is efficient - values accessed directly, not parsed from QSS.

---

## 7. Memory Management

### 7.1 Parent-Child Ownership

```python
# Child deleted when parent deleted
child = QWidget(parent=parent_widget)

# NEVER mix with smart pointers
# BAD: unique_ptr<QWidget> child(new QWidget(parent))  # Double-delete!
```

### 7.2 Safe Deletion Patterns

```python
# Always safe for QObjects
obj.deleteLater()

# For widgets, hide first for visual cleanup
widget.hide()
widget.deleteLater()

# For items in QGraphicsScene
scene.removeItem(item)
# item will be deleted if scene owned it
```

### 7.3 QPointer for Weak References

```python
from PySide6.QtCore import QPointer

# Tracks object, becomes None when deleted
weak_ref = QPointer(widget)
if weak_ref:  # Check before use
    weak_ref.doSomething()
```

---

## 8. CasareRPA-Specific Recommendations

Based on codebase analysis:

### 8.1 Already Implemented (Good)

| Pattern | Location |
|---------|----------|
| Viewport culling | `viewport_culling.py` |
| Spatial hashing | `SpatialHash` class |
| Animation coordination | `AnimationCoordinator` singleton |
| Cache disabled | `node_graph_widget.py` lines 51-66 |
| Centralized event bus | `event_bus.py` |
| Theme as dataclass | `theme.py` |

### 8.2 Opportunities for Improvement

| Area | Recommendation | Priority |
|------|----------------|----------|
| View optimization flags | Add `DontSavePainterState` | Medium |
| Timer precision | Use `CoarseTimer` for culling/animation | Low |
| BSP tuning | Set explicit depth for 100+ nodes | Medium |
| Bulk updates | `setUpdatesEnabled(False)` during load | High |
| Widget pooling | Pool property widgets | Medium |
| Signal batching | Batch high-frequency events | Medium |

### 8.3 Implementation Snippets

**Add optimization flags** (in `NodeGraphWidget.__init__`):
```python
viewer = self._graph.viewer()
viewer.setOptimizationFlags(
    QGraphicsView.DontSavePainterState
)
```

**Use CoarseTimer** (in `AnimationCoordinator`):
```python
self._timer.setTimerType(Qt.CoarseTimer)
```

**Batch updates during load** (in workflow deserializer):
```python
def deserialize(self, data):
    view = self._graph.viewer()
    view.setUpdatesEnabled(False)
    try:
        # ... create all nodes ...
    finally:
        view.setUpdatesEnabled(True)
```

---

## Sources

- [Qt 6 Signals & Slots](https://doc.qt.io/qt-6/signalsandslots.html)
- [Qt Signal/Slot Performance - Stack Overflow](https://stackoverflow.com/questions/10838013/does-large-use-of-signals-and-slots-affect-application-performance)
- [Signal/Slot Performance Comparison](https://sii.pl/blog/en/performance-comparison-of-the-qt-signals-and-slots-mechanism-and-the-native-c-implementation/)
- [QSS Performance - Stack Overflow](https://stackoverflow.com/questions/18187376/stylesheet-performance-hits-with-qt)
- [Say No to Qt Style Sheets - KDAB](https://www.kdab.com/say-no-to-qt-style-sheets/)
- [Qt Memory Management](http://silmor.de/qtstuff.garbcol.php)
- [Qt Memory Management - Stack Overflow](https://stackoverflow.com/questions/2491707/memory-management-in-qt)
- [deleteLater: Managing QObject Lifecycle](https://sep.com/blog/deletelater-managing-the-qobject-lifecycle-in-c/)
- [QGraphicsItem Class](https://doc.qt.io/qt-6/qgraphicsitem.html)
- [Improving QGraphicsView Performance](https://thesmithfam.org/blog/2007/02/03/qt-improving-qgraphicsview-performance/)

---

## Conclusion

CasareRPA already implements many Qt performance best practices:
- Spatial hashing with viewport culling
- Centralized animation timer
- Disabled item caching
- Theme as dataclass (not QSS)

Key remaining optimizations:
1. **High priority**: Use `setUpdatesEnabled(False)` during bulk operations
2. **Medium priority**: Add `DontSavePainterState` optimization flag
3. **Medium priority**: Tune BSP tree depth for large workflows
4. **Low priority**: Switch to `CoarseTimer` for minor CPU savings

These changes can be implemented incrementally without architectural changes.
