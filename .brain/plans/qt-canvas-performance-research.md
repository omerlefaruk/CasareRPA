# Qt/PySide6 High-Performance Canvas Research

**Research Date**: 2025-12-09
**Objective**: Achieve 120+ FPS in node graph editor

---

## Executive Summary

This research covers optimization techniques for Qt Graphics View framework, specifically for achieving high frame rates (60-120+ FPS) in node graph editors. The findings include QGraphicsView configuration, item-level caching, GPU acceleration, and profiling strategies.

**Key Finding**: CasareRPA already implements many best practices. The top opportunities for improvement are:
1. Batch rendering (drawPixmapFragments)
2. Scene indexing optimization (NoIndex for animated content)
3. PySide6 enum lookup optimization
4. Connection pooling for pipe rendering

---

## Top 10 Optimization Techniques (Ranked by Impact)

### 1. OpenGL/GPU Viewport (HIGH IMPACT - Already Implemented)

**Description**: Use QOpenGLWidget as the viewport for hardware-accelerated rendering.

**Impact**: 2-5x performance improvement for complex scenes.

**Current Status**: CasareRPA implements this in `node_graph_widget.py`:
```python
# Already implemented
from PySide6.QtOpenGLWidgets import QOpenGLWidget
gl_widget = QOpenGLWidget()
viewer.setViewport(gl_widget)
```

**Best Practice Configuration**:
```python
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat

gl_format = QSurfaceFormat()
gl_format.setVersion(3, 3)
gl_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
gl_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
gl_format.setSwapInterval(0)  # Disable vsync for max FPS (use 1 for 60fps cap)
gl_format.setSamples(4)  # 4x MSAA

gl_widget = QOpenGLWidget()
gl_widget.setFormat(gl_format)
view.setViewport(gl_widget)
```

**Caveat**: When using OpenGL, must use `FullViewportUpdate` mode since OpenGL cannot do partial updates.

**Sources**:
- [Qt OpenGL Canvas](https://doc.qt.io/archives/qq/qq26-openglcanvas.html)
- [Qt Graphics Performance Blog](https://www.qt.io/blog/2010/01/06/qt-graphics-and-performance-opengl)

---

### 2. Viewport Update Mode (HIGH IMPACT - Already Implemented)

**Description**: Configure how QGraphicsView determines what regions to repaint.

**Modes**:
- `MinimalViewportUpdate` (default): Calculates smallest dirty region. Best for software rendering with few changes.
- `FullViewportUpdate`: Redraws everything. **Required for OpenGL**. Best when many small items change frequently.
- `SmartViewportUpdate`: Qt chooses based on scene complexity.
- `BoundingRectViewportUpdate`: Uses bounding rect of all changed items.

**Current Status**: CasareRPA uses `FullViewportUpdate` (correct for OpenGL):
```python
viewer.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
```

**Recommendation**: Keep `FullViewportUpdate` since OpenGL is enabled.

**Sources**:
- [QGraphicsView Performance](https://forum.qt.io/topic/140557/how-to-optimize-qgraphicsview-performance)
- [Hands-On High Performance Qt](https://www.oreilly.com/library/view/hands-on-high-performance/9781789531244/)

---

### 3. Item Caching Modes (HIGH IMPACT - Partially Implemented)

**Description**: Cache item rendering to pixmaps to avoid repeated paint() calls.

**Cache Modes**:
- `NoCache`: Default. Paint called every frame.
- `ItemCoordinateCache`: Cache at item resolution. Invalidated on scale/rotation.
- `DeviceCoordinateCache`: Cache at screen resolution. Best quality, more memory.

**When to Use Each**:
| Scenario | Recommended Mode |
|----------|------------------|
| Static items | `ItemCoordinateCache` with logicalCacheSize |
| Items with frequent transforms | `DeviceCoordinateCache` |
| Items changing every frame | `NoCache` (caching overhead > benefit) |
| Large static backgrounds | `ItemCoordinateCache` |

**Current Status**: CasareRPA has `NodeBackgroundCache` for node backgrounds, but individual items don't use Qt's built-in caching.

**Recommendation - Add to Node Items**:
```python
class CustomNodeItem(NodeItem):
    def __init__(self, ...):
        super().__init__(...)
        # Enable caching for static node content
        self.setCacheMode(QGraphicsItem.CacheMode.ItemCoordinateCache)
```

**Caveat**: Disable caching during animation (running state) since cache regeneration is expensive:
```python
def set_running_state(self, running: bool):
    if running:
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)
    else:
        self.setCacheMode(QGraphicsItem.CacheMode.ItemCoordinateCache)
```

**Sources**:
- [QGraphicsItem Class Reference](https://doc.qt.io/qt-6/qgraphicsitem.html)
- [QGraphicsView Performance Forum](https://forum.qt.io/topic/6793/qgraphicsview-performance-with-lots-of-items)

---

### 4. Optimization Flags (MEDIUM-HIGH IMPACT - Already Implemented)

**Description**: QGraphicsView optimization flags that reduce painter overhead.

**Flags**:
| Flag | Effect | Performance Gain |
|------|--------|------------------|
| `DontSavePainterState` | Skips QPainter save/restore between items | 10-20% in dense scenes |
| `DontAdjustForAntialiasing` | Skips bounding rect adjustment for AA | 5-10% |
| `IndirectPainting` | Uses intermediate buffer for complex items | Varies |

**Current Status**: All three flags are enabled in CasareRPA:
```python
viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.IndirectPainting, True)
```

**Sources**:
- [Qt Forum - Optimizing QGraphicsView](https://interest.qt-project.narkive.com/qkLSr79U/optimizing-qgraphicsview)

---

### 5. Batch Draw Calls with drawPixmapFragments (MEDIUM IMPACT - NOT Implemented)

**Description**: Combine multiple pixmap draws into a single call to reduce GPU state changes.

**Standard Approach** (slow with many items):
```python
def paint_icons(self, painter, nodes):
    for node in nodes:
        painter.drawPixmap(node.icon_rect, node.icon)  # State change per node!
```

**Batched Approach** (fast):
```python
from PySide6.QtGui import QPainter

def paint_icons_batched(self, painter, nodes):
    fragments = []
    for node in nodes:
        fragment = QPainter.PixmapFragment.create(
            node.icon_rect.center(),  # Position
            source_rect,              # Source rect in atlas
            scaleX=1.0, scaleY=1.0,
            rotation=0.0,
            opacity=1.0
        )
        fragments.append(fragment)

    painter.drawPixmapFragments(fragments, atlas_pixmap)
```

**Current Status**: CasareRPA has an `IconTextureAtlas` but draws icons individually in each node's paint().

**Recommendation**: Create a scene-level icon renderer that batches all visible node icons in a single `drawPixmapFragments` call.

**Measured Benefit**: Qt blog reports 5.2ms -> 3.9ms (25% reduction) for 40 pixmaps.

**Sources**:
- [Qt Graphics Performance - Cost of Convenience](https://www.qt.io/blog/2010/01/11/qt-graphics-and-performance-the-cost-of-convenience)
- [QPainter drawPixmapFragments](https://doc.qt.io/qt-6/qpainter.html)

---

### 6. Scene Indexing Strategy (MEDIUM IMPACT - Default Setting)

**Description**: QGraphicsScene uses indexing to speed up item discovery. The default `BspTreeIndex` is optimal for static scenes but can hurt performance for animated scenes.

**Index Methods**:
- `BspTreeIndex` (default): Binary space partition. Excellent for static scenes with many items.
- `NoIndex`: No indexing. Better for dynamic scenes where items move frequently.

**When to Use NoIndex**:
- Many items animate simultaneously
- Frequent item position changes (dragging)
- Scene experiences slowdowns during animation

**Current Status**: CasareRPA uses default `BspTreeIndex`.

**Recommendation**:
```python
from PySide6.QtWidgets import QGraphicsScene

# For workflow editing (mostly static):
scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)

# During workflow execution (nodes animating):
scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
```

**Implementation Strategy**:
```python
def on_execution_started(self):
    self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

def on_execution_finished(self):
    self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)
```

**Sources**:
- [QGraphicsScene Documentation](https://doc.qt.io/qt-6/qgraphicsscene.html)
- [Qt Forum - Performance Problems](https://www.qtcentre.org/threads/32077-QGraphicsView-performance-problems)

---

### 7. PySide6 Enum Lookup Optimization (MEDIUM IMPACT - NOT Implemented)

**Description**: In PySide6, looking up enum values like `Qt.DisplayRole` searches through a massive object. Using fully qualified enums is significantly faster.

**Slow (searched every call)**:
```python
# In paint() - called 1000s of times
painter.setRenderHint(Qt.Antialiasing)  # Slow lookup!
```

**Fast (direct reference)**:
```python
# In paint() - direct enum access
painter.setRenderHint(Qt.RenderHint.Antialiasing)  # Fast!
```

**Current Status**: CasareRPA generally uses qualified enums but should audit all paint() methods.

**High-Priority Locations to Audit**:
- `custom_node_item.py` paint()
- `custom_pipe.py` paint()
- `subflow_node_item.py` paint()
- Any QGraphicsItem paint() override

**Module-Level Caching for Maximum Performance**:
```python
# At module level - single lookup at import time
_RENDER_ANTIALIASING = Qt.RenderHint.Antialiasing
_TRANSPARENT = Qt.GlobalColor.transparent

# In paint() - zero lookup overhead
painter.setRenderHint(_RENDER_ANTIALIASING)
```

**Measured Benefit**: Significant improvement in table models; same applies to paint().

**Sources**:
- [basysKom - Pitfalls in PySide6](https://www.basyskom.de/en/pitfalls-in-pyside6/)

---

### 8. LOD (Level of Detail) Rendering (MEDIUM IMPACT - Already Implemented)

**Description**: Reduce rendering detail at low zoom levels.

**Current Status**: CasareRPA has excellent LOD implementation in `lod_manager.py`:
```python
class LODLevel(Enum):
    ULTRA_LOW = auto()  # < 15% zoom - just colored rectangles
    LOW = auto()        # < 30% zoom - simplified
    MEDIUM = auto()     # < 50% zoom - reduced detail
    FULL = auto()       # >= 50% zoom - full detail
```

**Enhancement Opportunities**:
1. Add hysteresis to prevent LOD flickering (already implemented: 2% threshold)
2. Disable antialiasing at low LOD (already implemented)
3. Consider viewport-level LOD batching

---

### 9. Viewport Culling / Spatial Partitioning (MEDIUM IMPACT - Already Implemented)

**Description**: Only render items visible in the current viewport.

**Current Status**: CasareRPA has comprehensive implementation in `viewport_culling.py`:
- Grid-based spatial hash (`SpatialHash` class)
- 500px cell size
- 200px margin for edge cases
- Pipe visibility tied to node visibility

**Enhancement**: Consider integrating with Qt's built-in `items(viewport_rect)` for comparison.

---

### 10. Signal/Slot Overhead Mitigation (LOW-MEDIUM IMPACT)

**Description**: Qt signals have overhead (~10x a direct function call). In performance-critical paths, consider direct calls.

**Overhead Factors**:
- Connection lookup
- Thread-safety checks
- Parameter marshalling

**Mitigation Strategies**:
1. Use `Qt.ConnectionType.DirectConnection` explicitly when same-thread is guaranteed
2. Batch updates instead of per-item signals
3. Consider direct method calls for performance-critical paths

**Example - Batched Updates**:
```python
# Slow: Signal per node
for node in nodes:
    self.node_updated.emit(node.id)

# Fast: Single signal with batch
self.nodes_updated.emit([n.id for n in nodes])
```

**Sources**:
- [Qt Signals & Slots](https://doc.qt.io/qt-6/signalsandslots.html)
- [Signal Slot Performance Comparison](https://sii.pl/blog/en/performance-comparison-of-the-qt-signals-and-slots-mechanism/)

---

## NodeGraphQt-Specific Findings

### Known Issues

1. **Architecture**: NodeGraphQt wraps QGraphicsView but wasn't designed for GPU optimization
2. **No Official Fork for Performance**: The QuiltiX fork focuses on features, not performance
3. **No Batched Rendering**: Each node/pipe paints independently

### Alternative Libraries

| Library | Pros | Cons |
|---------|------|------|
| [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt) | Feature-complete, active | Performance not optimized |
| [Ryven](https://github.com/leon-thomm/Ryven) | Headless mode, clean design | Less visual polish |
| [QtNodes](https://github.com/paceholder/nodeeditor) | MVC architecture, Python bindings | Less Python-native |
| [qtpynodeeditor](https://github.com/klauer/qtpynodeeditor) | Pure Python, undo/redo | Smaller community |
| [Nodz](https://github.com/LeGoffLoic/Nodz) | Simple, lightweight | Limited features |

**Recommendation**: Continue with NodeGraphQt + custom optimizations. The existing CasareRPA customizations (LOD, culling, caching) already surpass what alternatives offer.

---

## Profiling Approach

### Recommended Toolchain

1. **cProfile + SnakeViz** - Function-level profiling
   ```bash
   python -m cProfile -o profile.prof run.py
   snakeviz profile.prof  # Visual analysis
   ```

2. **line_profiler** - Line-by-line profiling for hot functions
   ```bash
   pip install line_profiler
   kernprof -l -v script.py
   ```

3. **line-profiler-gui** - Qt-based visualization
   ```bash
   pip install line-profiler-gui[PySide6]
   ```

4. **Qt QML Profiler / GammaRay** - Qt-specific profiling
   - Shows item counts, paint times
   - Property introspection at runtime

### Profiling PySide6 Caveat

Python profilers only measure Python code. Qt/C++ internals are charged to the calling Python function. Use Qt's built-in tools for QPainter profiling.

### Custom FPS Counter

```python
from PySide6.QtCore import QElapsedTimer

class FPSCounter:
    def __init__(self):
        self._timer = QElapsedTimer()
        self._frame_count = 0
        self._last_fps = 0.0
        self._timer.start()

    def tick(self):
        self._frame_count += 1
        elapsed = self._timer.elapsed()
        if elapsed >= 1000:
            self._last_fps = self._frame_count * 1000.0 / elapsed
            self._frame_count = 0
            self._timer.restart()

    @property
    def fps(self) -> float:
        return self._last_fps
```

**Sources**:
- [line_profiler](https://github.com/pyutils/line_profiler)
- [SnakeViz](https://jiffyclub.github.io/snakeviz/)
- [Python Profiling Guide](https://www.machinelearningplus.com/python/cprofile-how-to-profile-your-python-code/)

---

## Common Anti-Patterns to Avoid

### 1. QPainter State Save/Restore Abuse
```python
# Bad: Unnecessary save/restore
def paint(self, painter, ...):
    painter.save()
    painter.drawLine(...)  # drawLine doesn't change state!
    painter.restore()

# Good: Only save when state actually changes
def paint(self, painter, ...):
    painter.drawLine(...)  # No state change needed
```

### 2. Allocations in paint()
```python
# Bad: Allocates every frame
def paint(self, painter, ...):
    pen = QPen(QColor(255, 0, 0), 2)  # Allocation!

# Good: Pre-allocate at module level
_RED_PEN = QPen(QColor(255, 0, 0), 2)
def paint(self, painter, ...):
    painter.setPen(_RED_PEN)
```

### 3. Boundless update() Calls
```python
# Bad: Full item update
self.update()

# Good: Minimal dirty region
self.update(changed_rect)
```

### 4. Bounding Rect Too Large
```python
# Bad: Oversized boundingRect triggers unnecessary repaints
def boundingRect(self):
    return QRectF(-1000, -1000, 2000, 2000)

# Good: Tight boundingRect
def boundingRect(self):
    return self._calculated_tight_bounds
```

---

## Implementation Priority

Based on current CasareRPA implementation, recommended priority:

| Priority | Optimization | Status | Effort | Impact |
|----------|--------------|--------|--------|--------|
| 1 | drawPixmapFragments batching | Not done | Medium | High |
| 2 | Scene index switching (NoIndex during execution) | Not done | Low | Medium |
| 3 | PySide6 enum module-level caching | Partial | Low | Medium |
| 4 | ItemCoordinateCache on nodes | Not done | Low | Medium |
| 5 | Direct connection signals | Not done | Low | Low-Medium |

**Already Implemented (Good)**:
- OpenGL viewport
- FullViewportUpdate (required for OpenGL)
- Optimization flags
- LOD manager
- Viewport culling
- Background cache
- Icon texture atlas

---

## Code Examples for Priority Items

### 1. Batch Icon Rendering

```python
# scene_renderer.py

from PySide6.QtGui import QPainter
from typing import List
from casare_rpa.presentation.canvas.graph.icon_atlas import get_icon_atlas

class BatchedIconRenderer:
    """Renders all visible node icons in a single draw call."""

    def __init__(self):
        self._atlas = get_icon_atlas()

    def render_icons(self, painter: QPainter, nodes: List) -> None:
        """
        Batch-render icons for all visible nodes.

        Call from QGraphicsScene::drawForeground() or similar.
        """
        if not self._atlas.get_atlas():
            return

        fragments = []
        for node in nodes:
            if not node.isVisible():
                continue

            node_type = node.node_type
            if not self._atlas.has_icon(node_type):
                continue

            # Get icon rect in scene coordinates
            icon_rect = node.get_icon_rect_scene()
            source_rect = self._atlas.get_icon_rect(node_type)

            fragment = QPainter.PixmapFragment.create(
                icon_rect.center(),
                source_rect,
            )
            fragments.append(fragment)

        if fragments:
            painter.drawPixmapFragments(
                fragments,
                self._atlas.get_atlas()
            )
```

### 2. Scene Index Switching

```python
# execution_manager.py

from PySide6.QtWidgets import QGraphicsScene

class ExecutionManager:
    def __init__(self, scene: QGraphicsScene):
        self._scene = scene

    def on_execution_started(self):
        """Switch to NoIndex for animation performance."""
        self._scene.setItemIndexMethod(
            QGraphicsScene.ItemIndexMethod.NoIndex
        )

    def on_execution_finished(self):
        """Restore BspTreeIndex for static scene."""
        self._scene.setItemIndexMethod(
            QGraphicsScene.ItemIndexMethod.BspTreeIndex
        )
```

### 3. Module-Level Enum Caching

```python
# custom_node_item.py (top of file)

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

# Pre-cached Qt constants (avoid per-paint lookup overhead)
_ANTIALIASING = Qt.RenderHint.Antialiasing
_SMOOTH_PIXMAP = Qt.RenderHint.SmoothPixmapTransform
_TRANSPARENT = Qt.GlobalColor.transparent
_SOLID_LINE = Qt.PenStyle.SolidLine
```

---

## Sources

### Qt Official Documentation
- [QGraphicsView Class](https://doc.qt.io/qt-6/qgraphicsview.html)
- [QGraphicsScene Class](https://doc.qt.io/qt-6/qgraphicsscene.html)
- [QGraphicsItem Class](https://doc.qt.io/qt-6/qgraphicsitem.html)
- [QPainter Class](https://doc.qt.io/qt-6/qpainter.html)

### Qt Blogs & Tutorials
- [Qt Graphics Performance Blog](https://www.qt.io/blog/2010/01/06/qt-graphics-and-performance-opengl)
- [Qt Graphics Performance - Cost of Convenience](https://www.qt.io/blog/2010/01/11/qt-graphics-and-performance-the-cost-of-convenience)
- [Accelerate with OpenGL](https://doc.qt.io/archives/qq/qq26-openglcanvas.html)
- [Using Hardware Acceleration](https://www.qt.io/blog/2009/03/13/using-hardware-acceleration-for-graphics)

### Community Resources
- [Qt Forum - QGraphicsView Optimization](https://forum.qt.io/topic/140557/how-to-optimize-qgraphicsview-performance)
- [Qt Forum - Performance with Many Items](https://forum.qt.io/topic/6793/qgraphicsview-performance-with-lots-of-items)
- [Qt Wiki - Smooth Zoom](https://wiki.qt.io/Smooth_Zoom_In_QGraphicsView)
- [Dave Smith - Improving QGraphicsView Performance](https://thesmithfam.org/blog/2007/02/03/qt-improving-qgraphicsview-performance/)

### PySide6-Specific
- [basysKom - Pitfalls in PySide6](https://www.basyskom.de/en/pitfalls-in-pyside6/)
- [Python GUIs - PySide6 Tutorial](https://www.pythonguis.com/pyside6-tutorial/)

### Node Graph Libraries
- [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt)
- [Ryven](https://github.com/leon-thomm/Ryven)
- [QtNodes](https://github.com/paceholder/nodeeditor)
- [qtpynodeeditor](https://github.com/klauer/qtpynodeeditor)
- [Nodz](https://github.com/LeGoffLoic/Nodz)

### Profiling Tools
- [line_profiler](https://github.com/pyutils/line_profiler)
- [line-profiler-gui](https://pypi.org/project/line-profiler-gui/)
- [SnakeViz](https://jiffyclub.github.io/snakeviz/)
- [Python Profilers Documentation](https://docs.python.org/3/library/profile.html)

---

## Conclusion

CasareRPA already implements many of the most impactful optimizations:
- OpenGL viewport with proper configuration
- FullViewportUpdate for OpenGL compatibility
- All three optimization flags
- Sophisticated LOD manager with hysteresis
- Grid-based spatial culling
- Background pixmap caching
- Icon texture atlas

The remaining high-value improvements are:
1. **Batch rendering with drawPixmapFragments** - Would benefit icon and potentially background rendering
2. **Dynamic scene indexing** - Switch to NoIndex during execution
3. **Enum caching audit** - Ensure all paint() methods use module-level cached enums
4. **ItemCoordinateCache for nodes** - Enable Qt's built-in caching for static states

With these additional optimizations, 120+ FPS should be achievable for workflows with 50-100+ nodes on modern hardware.
