# GPU Acceleration Research: PySide6/Qt Node Graph

**Date**: 2025-12-06
**Focus**: GPU acceleration opportunities for CasareRPA's visual node editor
**Researcher**: Claude (Research Specialist)

---

## Executive Summary

CasareRPA already implements QOpenGLWidget viewport with OpenGL 3.3 Core Profile, 4x MSAA, and vsync disabled. This document evaluates additional GPU acceleration techniques, categorizing them by feasibility and impact.

### Current GPU Setup (Already Implemented)

```python
# From node_graph_widget.py lines 499-524
gl_format = QSurfaceFormat()
gl_format.setVersion(3, 3)  # OpenGL 3.3+
gl_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
gl_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
gl_format.setSwapInterval(0)  # Disabled vsync
gl_format.setSamples(4)  # 4x MSAA

gl_widget = QOpenGLWidget()
gl_widget.setFormat(gl_format)
viewer.setViewport(gl_widget)
```

---

## 1. Viable Options (Low-Medium Effort)

### 1.1 LOD Rendering Enhancement

**Already Implemented** - CasareRPA has LOD rendering at < 30% zoom in `custom_node_item.py` and `custom_pipe.py`. Can be enhanced:

| Current | Enhancement | Impact |
|---------|-------------|--------|
| 30% zoom threshold | Dynamic threshold based on node count | Better scaling |
| Simplified shapes | Cached pixmaps at each LOD level | Faster paint |
| Per-item check | Batch LOD detection per frame | Less overhead |

**Code Example - Batch LOD Check:**
```python
class ViewportLODManager:
    """Determine LOD level once per frame, apply to all items."""

    LOD_THRESHOLDS = [0.15, 0.30, 0.50, 1.0]  # zoom levels
    LOD_LEVELS = ['ultra_low', 'low', 'medium', 'full']

    def __init__(self):
        self._current_lod = 'full'
        self._last_zoom = 1.0

    def update_lod_for_viewport(self, view):
        zoom = view.transform().m11()
        if abs(zoom - self._last_zoom) < 0.01:
            return self._current_lod  # No change

        self._last_zoom = zoom
        for threshold, level in zip(self.LOD_THRESHOLDS, self.LOD_LEVELS):
            if zoom < threshold:
                self._current_lod = level
                return level
        self._current_lod = 'full'
        return 'full'
```

### 1.2 Texture Atlas for Node Icons

**Concept**: Combine all node icons into a single texture atlas to reduce GPU texture binding switches.

**Benefits**:
- Fewer state changes between nodes
- Better GPU cache utilization
- ~10-20% improvement for icon-heavy workflows

**Implementation Strategy**:
```python
from PySide6.QtGui import QPixmap, QPainter

class NodeIconAtlas:
    """Pre-combined texture atlas for node icons."""

    ATLAS_SIZE = 1024  # 1024x1024 atlas
    ICON_SIZE = 64     # 64x64 per icon
    ICONS_PER_ROW = ATLAS_SIZE // ICON_SIZE  # 16

    def __init__(self):
        self._atlas = QPixmap(self.ATLAS_SIZE, self.ATLAS_SIZE)
        self._atlas.fill(Qt.transparent)
        self._icon_positions: dict[str, tuple[int, int]] = {}
        self._next_slot = 0

    def add_icon(self, name: str, pixmap: QPixmap) -> tuple[int, int]:
        """Add icon to atlas, return (x, y) position."""
        row = self._next_slot // self.ICONS_PER_ROW
        col = self._next_slot % self.ICONS_PER_ROW

        x = col * self.ICON_SIZE
        y = row * self.ICON_SIZE

        painter = QPainter(self._atlas)
        painter.drawPixmap(x, y, self.ICON_SIZE, self.ICON_SIZE,
                          pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE))
        painter.end()

        self._icon_positions[name] = (x, y)
        self._next_slot += 1
        return (x, y)

    def get_atlas(self) -> QPixmap:
        return self._atlas

    def get_icon_rect(self, name: str) -> QRect:
        x, y = self._icon_positions.get(name, (0, 0))
        return QRect(x, y, self.ICON_SIZE, self.ICON_SIZE)
```

### 1.3 Shader-Based Selection Glow

**Current**: Yellow border drawn with QPainter
**Enhanced**: GPU fragment shader for smooth animated glow

**Why Better**:
- Glow calculation offloaded to GPU
- Smooth animation without CPU overhead
- Consistent visual quality at all zoom levels

**Implementation (QML Approach)**:
```qml
// SelectionGlow.qml
import QtQuick 2.15
import QtQuick.Effects

Rectangle {
    id: nodeRect
    property bool isSelected: false

    MultiEffect {
        source: nodeRect
        anchors.fill: parent
        visible: isSelected

        // Glow effect (GPU accelerated)
        glowEnabled: true
        glowColor: "#FFD700"  // Yellow
        glow: 0.8
        glowMax: 1.0

        // Animated pulse
        PropertyAnimation on glow {
            from: 0.4
            to: 0.8
            duration: 1000
            loops: Animation.Infinite
            easing.type: Easing.InOutSine
        }
    }
}
```

### 1.4 Pre-Rendered Node Backgrounds

**Concept**: Render node body backgrounds to pixmaps once, reuse for identical node types.

```python
class NodeBackgroundCache:
    """Cache rendered node backgrounds by type and size."""

    def __init__(self):
        self._cache: dict[tuple[str, int, int], QPixmap] = {}

    def get_background(self, node_type: str, width: int, height: int) -> QPixmap:
        key = (node_type, width, height)
        if key not in self._cache:
            self._cache[key] = self._render_background(node_type, width, height)
        return self._cache[key]

    def _render_background(self, node_type: str, w: int, h: int) -> QPixmap:
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw rounded rect, header bar, etc.
        # ... (node-type specific drawing)

        painter.end()
        return pm
```

---

## 2. High-Effort Options (Significant Gains)

### 2.1 Qt Quick/QML Migration

**Overview**: Replace QGraphicsView entirely with Qt Quick's GPU-native scene graph.

**Benefits**:
- Native GPU batching (automatic)
- Texture atlases (automatic)
- Hardware-accelerated effects
- Better threading (separate render thread)
- True GPU instancing for similar nodes

**Trade-offs**:
- Major rewrite (3-6 months)
- NodeGraphQt library not compatible
- Different programming model (declarative)
- PySide6 QML integration complexity

**Architecture Comparison**:

| Feature | QGraphicsView | Qt Quick Scene Graph |
|---------|---------------|---------------------|
| Rendering | Software + GL viewport | Native GPU |
| Batching | Manual | Automatic |
| Effects | CPU (QGraphicsEffect) | GPU (MultiEffect) |
| Threading | Main thread | Separate render thread |
| Draw calls | Per item | Batched by material |

**Hybrid Approach** (Recommended Path):
```python
# Keep QGraphicsView for complex interaction, embed QML for nodes
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

class HybridNodeView(QGraphicsView):
    """QGraphicsView with QML overlay for GPU effects."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # QML overlay for GPU effects
        self._effect_overlay = QQuickWidget(self)
        self._effect_overlay.setSource(QUrl("qrc:/effects/NodeEffects.qml"))
        self._effect_overlay.setAttribute(Qt.WA_TranslucentBackground)
        self._effect_overlay.setAttribute(Qt.WA_AlwaysStackOnTop)
```

### 2.2 Custom OpenGL Node Renderer

**Concept**: Bypass QPainter for node rendering, use direct OpenGL/GLSL.

**Implementation Stages**:

1. **Stage 1: Background Grid** (Easy)
   - Render infinite grid with fragment shader
   - No geometry needed (fullscreen quad)

2. **Stage 2: Node Bodies** (Medium)
   - Instanced quads for all nodes
   - Texture atlas for icons
   - Uniform buffer for node positions/colors

3. **Stage 3: Bezier Connections** (Hard)
   - Geometry shader for curve tessellation
   - OR compute shader for path generation
   - GPU-based anti-aliasing

**Basic Node Instancing Shader (GLSL 3.3):**

```glsl
// vertex.glsl
#version 330 core

layout(location = 0) in vec2 a_vertex;     // Quad vertices (0-1)
layout(location = 1) in vec4 a_rect;       // Instance: x, y, w, h
layout(location = 2) in vec4 a_color;      // Instance: RGBA
layout(location = 3) in vec4 a_iconUV;     // Instance: atlas UV rect

uniform mat4 u_viewMatrix;

out vec2 v_texCoord;
out vec4 v_color;
out vec4 v_iconUV;

void main() {
    vec2 pos = a_rect.xy + a_vertex * a_rect.zw;
    gl_Position = u_viewMatrix * vec4(pos, 0.0, 1.0);

    v_texCoord = a_vertex;
    v_color = a_color;
    v_iconUV = a_iconUV;
}

// fragment.glsl
#version 330 core

in vec2 v_texCoord;
in vec4 v_color;
in vec4 v_iconUV;

uniform sampler2D u_iconAtlas;
uniform float u_cornerRadius;

out vec4 fragColor;

float roundedBox(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
}

void main() {
    // Rounded rectangle SDF
    vec2 uv = v_texCoord * 2.0 - 1.0;
    float d = roundedBox(uv, vec2(0.95), u_cornerRadius);
    float alpha = 1.0 - smoothstep(0.0, 0.02, d);

    // Sample icon from atlas
    vec2 iconUV = v_iconUV.xy + v_texCoord * v_iconUV.zw;
    vec4 icon = texture(u_iconAtlas, iconUV);

    // Composite
    vec4 color = v_color;
    color = mix(color, icon, icon.a);
    color.a *= alpha;

    fragColor = color;
}
```

### 2.3 GPU Layout Algorithms

**Concept**: Compute auto-layout on GPU for large workflows.

**Applicable Algorithms**:
- Force-directed layout (Fruchterman-Reingold)
- Hierarchical layout (Sugiyama)
- Orthogonal routing

**Implementation using Compute Shaders**:

```glsl
// layout_compute.glsl
#version 430 core

layout(local_size_x = 256) in;

struct Node {
    vec2 position;
    vec2 velocity;
    float mass;
    uint connections[8];  // Max 8 connections per node
    uint connectionCount;
};

layout(std430, binding = 0) buffer Nodes {
    Node nodes[];
};

uniform float u_repulsion;
uniform float u_attraction;
uniform float u_damping;
uniform uint u_nodeCount;

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx >= u_nodeCount) return;

    Node node = nodes[idx];
    vec2 force = vec2(0.0);

    // Repulsion from all other nodes
    for (uint i = 0; i < u_nodeCount; i++) {
        if (i == idx) continue;

        vec2 diff = node.position - nodes[i].position;
        float dist = max(length(diff), 0.1);
        force += normalize(diff) * u_repulsion / (dist * dist);
    }

    // Attraction to connected nodes
    for (uint i = 0; i < node.connectionCount; i++) {
        uint target = node.connections[i];
        vec2 diff = nodes[target].position - node.position;
        float dist = length(diff);
        force += normalize(diff) * u_attraction * dist;
    }

    // Update velocity and position
    node.velocity = (node.velocity + force / node.mass) * u_damping;
    node.position += node.velocity;

    nodes[idx] = node;
}
```

**Python Interface**:
```python
from PySide6.QtOpenGL import QOpenGLShaderProgram, QOpenGLShader
from PySide6.QtGui import QOpenGLFunctions

class GPULayoutEngine:
    """GPU-accelerated graph layout using compute shaders."""

    def __init__(self, gl_context):
        self.gl = QOpenGLFunctions(gl_context)
        self._compile_shaders()
        self._create_buffers()

    def compute_layout(self, nodes: list, iterations: int = 100):
        """Run force-directed layout on GPU."""
        self._upload_nodes(nodes)

        for _ in range(iterations):
            self._compute_program.bind()
            self.gl.glDispatchCompute(
                (len(nodes) + 255) // 256, 1, 1
            )
            self.gl.glMemoryBarrier(
                self.gl.GL_SHADER_STORAGE_BARRIER_BIT
            )

        return self._download_positions()
```

---

## 3. Not Worth It

### 3.1 QGraphicsEffect GPU Acceleration

**Why Not**:
- QGraphicsEffect is CPU-only by design
- Effects trigger pixmap capture + CPU processing
- Adding GPU effects requires complete effect rewrite
- Better to skip effects or migrate to QML MultiEffect

**Evidence**: "Graphics effects, especially complex ones like blurs or shadows with large radii, are computationally expensive. Qt renders these effects by taking a pixmap of the widget and then applying transformations, which can be slow." ([Stack Overflow](https://stackoverflow.com/questions/28579659/qgraphicsblureffect-degrades-the-performance))

### 3.2 DirectX Interop via ANGLE

**Why Not**:
- Qt already handles backend selection via RHI
- ANGLE adds overhead, not performance gain
- Modern Qt6 can use Vulkan/Metal/D3D12 directly
- Windows-specific, breaks cross-platform

### 3.3 GPU Collision Detection for Viewport Culling

**Why Not**:
- Already using SpatialHash (O(1) per cell)
- GPU transfer overhead exceeds benefit
- Viewport culling is not the bottleneck
- ~30 FPS culling timer is sufficient

### 3.4 Item Coordinate Caching

**Why Not**:
- Already disabled (NoCache) due to zoom/pan artifacts
- DeviceCoordinateCache causes stale cached images
- CasareRPA correctly identified this issue
- Would need complete caching rewrite for proper invalidation

---

## 4. Recommended Approach

### Priority Order

| Priority | Enhancement | Effort | Gain | Dependencies |
|----------|-------------|--------|------|--------------|
| 1 | LOD Manager (batch check) | Low | Medium | None |
| 2 | Node Background Cache | Low | Medium | None |
| 3 | Icon Texture Atlas | Medium | Medium | None |
| 4 | Shader Selection Glow | Medium | High | QML overlay |
| 5 | Custom GL Grid Renderer | Medium | Low | OpenGL context |
| 6 | QML Hybrid Nodes | High | Very High | Architecture change |

### Phase 1: Quick Wins (1-2 weeks)

1. **Implement LOD Manager**
   - Batch LOD detection per frame
   - Add 'ultra_low' LOD for < 15% zoom
   - Cache LOD decisions

2. **Add Node Background Cache**
   - Pre-render common node backgrounds
   - Reuse pixmaps for same-sized nodes
   - Clear cache on theme change

### Phase 2: GPU Enhancements (2-4 weeks)

3. **Create Icon Texture Atlas**
   - Combine all node icons at startup
   - Single texture bind per paint
   - Source rect calculation for each icon

4. **QML Effect Overlay**
   - Create transparent QQuickWidget overlay
   - Implement GPU glow for selection
   - Animate running state with MultiEffect

### Phase 3: Future Architecture (3-6 months)

5. **Evaluate Full QML Migration**
   - Prototype node rendering in pure QML
   - Benchmark against current implementation
   - Plan incremental migration path

---

## 5. Code Examples

### Example 1: Batch LOD with ViewportLODManager

```python
# In node_graph_widget.py

class NodeGraphWidget(QWidget):
    def __init__(self, ...):
        ...
        self._lod_manager = ViewportLODManager()

        # Update LOD on viewport change
        self._viewport_update_timer.timeout.connect(self._update_lod)

    def _update_lod(self):
        viewer = self._graph.viewer()
        lod = self._lod_manager.update_lod_for_viewport(viewer)

        # Broadcast LOD to all items (avoid per-item zoom check)
        for node in self._graph.all_nodes():
            if hasattr(node, 'view') and hasattr(node.view, 'set_lod_level'):
                node.view.set_lod_level(lod)
```

### Example 2: Pre-rendered Background Usage

```python
# In custom_node_item.py

class CasareNodeItem(NodeItem):
    _bg_cache = NodeBackgroundCache()  # Shared class-level cache

    def paint(self, painter, option, widget):
        if self._current_lod == 'ultra_low':
            self._paint_lod(painter)
            return

        rect = self._get_node_rect()

        # Use cached background
        bg = self._bg_cache.get_background(
            self._node_type,
            int(rect.width()),
            int(rect.height())
        )
        painter.drawPixmap(rect.topLeft(), bg)

        # Draw dynamic content (icons, status, text) on top
        self._draw_dynamic_content(painter, rect)
```

### Example 3: Icon Atlas Integration

```python
# In node_icons.py

class NodeIconManager:
    _atlas: NodeIconAtlas = None

    @classmethod
    def initialize_atlas(cls):
        """Call once at startup to build atlas."""
        cls._atlas = NodeIconAtlas()

        # Load all node type icons
        from casare_rpa.nodes import get_all_node_types
        for node_type in get_all_node_types():
            icon = node_type.get_icon()
            if icon:
                cls._atlas.add_icon(node_type.identifier, icon)

    @classmethod
    def draw_icon(cls, painter, node_type: str, rect: QRectF):
        """Draw icon from atlas."""
        if cls._atlas is None:
            cls.initialize_atlas()

        atlas = cls._atlas.get_atlas()
        source_rect = cls._atlas.get_icon_rect(node_type)
        painter.drawPixmap(rect.toRect(), atlas, source_rect)
```

---

## 6. Performance Expectations

### Current Baseline (estimated)
- 100 nodes: 60 FPS (smooth)
- 500 nodes: 45 FPS (slight lag on pan)
- 1000 nodes: 25 FPS (noticeable lag)

### After Phase 1+2 (estimated)
- 100 nodes: 60 FPS
- 500 nodes: 55-60 FPS
- 1000 nodes: 40-50 FPS

### After QML Migration (estimated)
- 100 nodes: 60 FPS
- 500 nodes: 60 FPS
- 1000 nodes: 55-60 FPS
- 5000 nodes: 40 FPS (with LOD)

---

## Sources

### Qt Documentation
- [Qt Quick Scene Graph](https://doc.qt.io/qt-6/qtquick-visualcanvas-scenegraph.html)
- [Scene Graph - Custom QSGRenderNode](https://doc.qt.io/qt-6/qtquick-scenegraph-customrendernode-example.html)
- [QRhiGraphicsPipeline Class](https://doc.qt.io/qt-6/qrhigraphicspipeline.html)
- [Simple RHI Widget Example](https://doc.qt.io/qt-6/qtwidgets-rhi-simplerhiwidget-example.html)
- [PySide6 QGraphicsView](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsView.html)
- [QOpenGLWidget Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtOpenGLWidgets/QOpenGLWidget.html)
- [MultiEffect QML Type](https://doc.qt.io/qt-6/qml-qtquick-effects-multieffect.html)

### Performance Research
- [QGraphicsView Performance (Stack Overflow)](https://stackoverflow.com/questions/43826317/how-to-optimize-qgraphicsviews-performance)
- [QGraphicsView Thousands of Items (Qt Forum)](https://forum.qt.io/topic/73056/qgraphicsview-rendering-thousands-of-items)
- [QGraphicsBlurEffect Performance (Stack Overflow)](https://stackoverflow.com/questions/28579659/qgraphicsblureffect-degrades-the-performance)
- [Using OpenGL Shader on QGraphicsView (Stack Overflow)](https://stackoverflow.com/questions/11298449/using-opengl-shader-on-a-qgraphicsview)

### GPU Graph Layout
- [GraphWaGu: GPU Powered Graph Layout](https://stevepetruzza.io/pubs/graphwagu-2022.pdf)
- [ParaGraphL: WebGL Graph Layout](https://nblintao.github.io/ParaGraphL/)
- [RAPIDS cuGraph GPU Graph Visualization](https://medium.com/rapids-ai/large-graph-visualization-with-rapids-cugraph-590d07edce33)
- [Multi-Level Graph Layout on GPU (IEEE)](https://ieeexplore.ieee.org/document/4376155/)

### Node Editor References
- [Blender GPU Module](https://developer.blender.org/docs/features/gpu/overview/)
- [Houdini VOP Networks](https://www.sidefx.com/docs/houdini/nodes/vop/index.html)
- [Unreal Engine Blueprint Overview](https://docs.unrealengine.com/4.27/en-US/ProgrammingAndScripting/Blueprints/Overview/)

### Texture Atlas & Batching
- [Sprite Batching (LearnOpenGL)](https://learnopengl.com/In-Practice/2D-Game/Final-thoughts)
- [Python Arcade Texture Atlas](https://api.arcade.academy/en/2.6.14/advanced/texture_atlas.html)
- [QtQuick3D Instanced Rendering](https://www.qt.io/blog/qtquick3d-instanced-rendering)

### PySide6 OpenGL
- [PyQt6/PySide6 OpenGL Changes (GameDev)](https://www.gamedev.net/blogs/entry/2273817-a-few-basic-changes-in-pyqt6-and-pyside6-regarding-shader-based-opengl-graphics/)
- [basysKom RHI Tutorial](https://www.basyskom.de/en/hello-rhi-how-to-get-started-with-qt-rhi/)
- [Qt Blog: Custom Shader Effects](https://www.qt.io/blog/in-depth-custom-shader-effects)

---

## Conclusion

CasareRPA's current GPU setup (QOpenGLWidget + OpenGL 3.3 + MSAA) provides a solid foundation. The codebase already implements several performance optimizations:

**Already Done Well**:
- QOpenGLWidget viewport (GPU-accelerated)
- Viewport culling with spatial hash
- LOD rendering at low zoom
- Centralized animation coordinator
- Pre-cached QPen/QColor/QFont objects

**Best Next Steps**:
1. Batch LOD detection per frame (low effort, immediate gain)
2. Node background pixmap caching (low effort)
3. Icon texture atlas (medium effort, cumulative gain)
4. QML overlay for GPU effects (medium effort, high visual impact)

The full QML migration offers the largest performance gains but requires significant architectural changes. The hybrid approach (QML overlay) provides a pragmatic middle ground.
