# Houdini-style Dot/Reroute Node System

**Status**: PLAN READY
**Created**: 2025-12-05
**Author**: Research Agent

---

## Overview

Implement a Houdini-style "dot" or "reroute" node system that allows users to:
1. Hold Alt and click on a connection line (pipe) to create a routing dot
2. Drag dots to organize connection paths for cleaner workflows
3. Chain multiple dots for complex routing

---

## Current System Analysis

### Connection/Pipe System

**File**: `src/casare_rpa/presentation/canvas/graph/custom_pipe.py`

- `CasarePipe` extends NodeGraphQt's `PipeItem`
- Handles hover highlighting, insert highlighting (for node-on-pipe drop)
- Tracks `input_port` and `output_port` items
- Supports output value preview on hover
- Uses QPainterPath for bezier curve rendering

**Key Observations**:
- Pipes are QGraphicsItem-based, drawn between port items
- `setAcceptHoverEvents(True)` enables hover detection
- No mousePressEvent handler currently - events pass through to underlying items
- `path()` returns the QPainterPath for intersection testing

### Node Insertion System

**File**: `src/casare_rpa/presentation/canvas/connections/node_insert.py`

- `NodeInsertManager` handles dragging nodes onto pipes to insert them
- Uses timer-based polling (50ms) to detect node overlap with pipes
- `_find_closest_intersecting_exec_pipe()` finds pipes under dragged nodes
- `_insert_node_on_pipe()` disconnects old connection, creates two new ones
- `_auto_space_nodes()` positions nodes with 50px gaps

**Key Pattern**: Split a pipe by:
1. Getting source/target ports from pipe item
2. Finding model-level nodes by iterating `graph.all_nodes()`
3. Disconnecting source -> target
4. Connecting source -> new_node -> target

### Connection Cutter System

**File**: `src/casare_rpa/presentation/canvas/connections/connection_cutter.py`

- `ConnectionCutter` handles Y + LMB drag to cut connections
- Event filter pattern for keyboard + mouse combo detection
- `_item_intersects_cut()` uses QPainterPathStroker for hit testing
- Finds pipes by iterating scene items

**Key Pattern**: Detecting clicks on pipes:
- Iterate `viewer.scene().items()` and filter by class name containing "Pipe"
- Use `sceneBoundingRect()` for rough detection
- Use `QPainterPathStroker` on `item.path()` for accurate hit testing

### Visual Node System

**File**: `src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py`

- `VisualNode` extends `NodeGraphQtBaseNode`
- Has `__identifier__`, `NODE_NAME`, `NODE_CATEGORY` class attributes
- `setup_ports()` defines input/output ports
- `add_exec_input()`, `add_exec_output()` for execution flow ports
- `add_typed_input()`, `add_typed_output()` for data ports with DataType

### Event Filter Pattern

**File**: `src/casare_rpa/presentation/canvas/graph/event_filters.py`

- Event filters installed on `viewer.viewport()` for mouse events
- Pattern: Check `event.type()`, `event.button()`, get `scene_pos`
- Can consume events by returning `True`

### Node Graph Widget

**File**: `src/casare_rpa/presentation/canvas/graph/node_graph_widget.py`

- Central integration point for all connection managers
- Registers: AutoConnectManager, ConnectionCutter, NodeInsertManager
- Uses `CasarePipe` for all connections (set via `viewer._PIPE_ITEM`)

---

## Implementation Approach

### Core Concept

A "dot node" (reroute node) is a minimal node with:
- One input port (accepting one connection)
- One output port (can connect to multiple targets)
- No execution logic (just passes data through)
- Minimal visual representation (small circle, no header)
- **Critical**: Must preserve data type from input to output

### Alt+Click Detection Strategy

**Option A**: Event Filter on Pipe Items (Complex)
- Would require modifying CasarePipe to handle mouse events
- Conflicts with existing scene event handling

**Option B**: Event Filter on Viewport (Recommended)
- Install filter on `viewer.viewport()`
- Check for Alt+LMB on `MouseButtonPress`
- Find pipe at click position using QPainterPath intersection
- If pipe found, create dot node and reconnect

### Dot Node Visual Design

Based on existing patterns and Houdini reference:

```
    [  ]  <- Small square/circle, ~12-16px
     |
     |
```

Visual properties:
- Minimal size (no header, no widgets)
- Slightly transparent background
- Port colors match connected data type
- Subtle border on selection

### Data Type Propagation

The dot node must propagate the data type:
1. When created on a typed connection, inherit the DataType
2. Store as property for serialization
3. Update input/output port colors to match

---

## Files to Create

### 1. Domain Node: `src/casare_rpa/nodes/utility_nodes.py` (extend)

Add `RerouteNode` to existing utility_nodes module:

```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.value_objects.types import DataType

@executable_node
class RerouteNode(BaseNode):
    """
    Passthrough node for organizing connection routing.

    Does not modify data - simply passes input to output.
    Preserves data type from source connection.
    """

    node_type = "RerouteNode"

    def __init__(self):
        super().__init__()
        # DataType is set dynamically when connected
        self.data_type = DataType.ANY

    async def execute(self, context) -> dict:
        """Pass input directly to output."""
        value = self.get_input_value("in")
        self.set_output_value("out", value)
        return {"success": True}
```

### 2. Visual Node: `src/casare_rpa/presentation/canvas/visual_nodes/utility/reroute_node.py`

```python
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType

class VisualRerouteNode(VisualNode):
    """
    Minimal reroute node for connection organization.

    Visual appearance:
    - Small circle (~16px)
    - No header/title
    - Port colors match data type
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Reroute"
    NODE_CATEGORY = "utility"

    # Hide from node menu (created via Alt+Click only)
    HIDDEN_IN_MENU = True

    def __init__(self):
        # Use custom minimal graphics item
        super().__init__(qgraphics_item=RerouteNodeItem)
        self._data_type = DataType.ANY

    def setup_ports(self):
        """Setup single input and output port."""
        self.add_typed_input("in", DataType.ANY)
        self.add_typed_output("out", DataType.ANY)

    def set_data_type(self, data_type: DataType):
        """Update port data types to match connected wire."""
        self._data_type = data_type
        self._port_types["in"] = data_type
        self._port_types["out"] = data_type
        self._configure_port_colors()
```

### 3. Custom Graphics Item: `src/casare_rpa/presentation/canvas/graph/reroute_node_item.py`

```python
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from NodeGraphQt.qgraphics.node_base import NodeItem

class RerouteNodeItem(NodeItem):
    """
    Minimal graphics item for reroute/dot nodes.

    Visual: Small circle with no header or widgets.
    Size: ~16x16 pixels
    """

    DOT_SIZE = 16

    def __init__(self, name="dot", parent=None):
        super().__init__(name, parent)
        self._data_type_color = QColor(200, 200, 200)  # Default gray

    def boundingRect(self) -> QRectF:
        """Override to provide minimal bounding rect."""
        return QRectF(0, 0, self.DOT_SIZE, self.DOT_SIZE)

    def paint(self, painter, option, widget):
        """Paint minimal dot appearance."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.boundingRect()

        # Selection highlight
        if self.isSelected():
            pen = QPen(QColor(255, 215, 0), 2)  # Yellow selection
        else:
            pen = QPen(self._data_type_color.darker(120), 1)

        painter.setPen(pen)
        painter.setBrush(QBrush(self._data_type_color))

        # Draw circle
        painter.drawEllipse(rect.adjusted(2, 2, -2, -2))

    def set_data_type_color(self, color: QColor):
        """Set the color based on data type."""
        self._data_type_color = color
        self.update()
```

### 4. Dot Creator Manager: `src/casare_rpa/presentation/canvas/connections/dot_creator.py`

```python
from typing import Optional
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QPainterPath, QPainterPathStroker
from NodeGraphQt import NodeGraph

class DotCreator(QObject):
    """
    Manages creation of reroute/dot nodes via Alt+Click on pipes.

    Workflow:
    1. Detect Alt+LMB on viewport
    2. Find pipe at click position
    3. Create RerouteNode
    4. Disconnect original pipe
    5. Connect source -> reroute -> target
    6. Position reroute at click location
    """

    def __init__(self, graph: NodeGraph, parent=None):
        super().__init__(parent)
        self._graph = graph
        self._active = True
        self._setup_event_filter()

    def _setup_event_filter(self):
        """Install event filter on viewport."""
        viewer = self._graph.viewer()
        if viewer and viewer.viewport():
            viewer.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle Alt+LMB to create dot on pipe."""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QMouseEvent

        if not self._active:
            return False

        if event.type() != QEvent.Type.MouseButtonPress:
            return False

        if not isinstance(event, QMouseEvent):
            return False

        # Check for Alt + Left Mouse Button
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        if not (event.modifiers() & Qt.KeyboardModifier.AltModifier):
            return False

        # Get scene position
        viewer = self._graph.viewer()
        scene_pos = viewer.mapToScene(event.pos())

        # Find pipe at position
        pipe = self._find_pipe_at_position(scene_pos)
        if not pipe:
            return False

        # Create dot on this pipe
        self._create_dot_on_pipe(pipe, scene_pos)

        return True  # Consume event

    def _find_pipe_at_position(self, scene_pos):
        """Find a pipe item at the given scene position."""
        viewer = self._graph.viewer()
        if not viewer or not viewer.scene():
            return None

        # Use stroker for hit testing on thin pipe paths
        stroker = QPainterPathStroker()
        stroker.setWidth(12)  # Hit area width

        for item in viewer.scene().items():
            if "Pipe" not in item.__class__.__name__:
                continue

            # Skip incomplete pipes (being dragged)
            if not hasattr(item, "input_port") or not item.input_port:
                continue
            if not hasattr(item, "output_port") or not item.output_port:
                continue

            # Check if click is on this pipe's path
            if hasattr(item, "path"):
                pipe_path = item.path()
                stroked = stroker.createStroke(pipe_path)
                scene_path = item.mapToScene(stroked)

                # Create point path for intersection test
                point_path = QPainterPath()
                point_path.addEllipse(scene_pos, 2, 2)

                if scene_path.intersects(point_path):
                    return item

        return None

    def _create_dot_on_pipe(self, pipe, scene_pos):
        """Create a reroute node on the given pipe at scene_pos."""
        # Get source and target from pipe
        output_port_item = pipe.output_port
        input_port_item = pipe.input_port

        if not output_port_item or not input_port_item:
            return

        # Find model nodes and ports (same pattern as node_insert.py)
        source_node, source_port = self._get_model_port(output_port_item, is_output=True)
        target_node, target_port = self._get_model_port(input_port_item, is_output=False)

        if not source_port or not target_port:
            return

        # Create reroute node at click position
        reroute = self._graph.create_node(
            "casare_rpa.utility.VisualRerouteNode",
            pos=(scene_pos.x(), scene_pos.y())
        )

        # Get data type from source port (if typed)
        data_type = self._get_port_data_type(source_node, source_port)
        if data_type and hasattr(reroute, "set_data_type"):
            reroute.set_data_type(data_type)

        # Disconnect original
        source_port.disconnect_from(target_port)

        # Connect through reroute
        reroute_in = reroute.get_input("in")
        reroute_out = reroute.get_output("out")

        source_port.connect_to(reroute_in)
        reroute_out.connect_to(target_port)

    def _get_model_port(self, port_item, is_output: bool):
        """Get model-level node and port from view-level port item."""
        # Get node item from port item
        node_item = port_item.parentItem()
        if not node_item or not hasattr(node_item, "id"):
            return None, None

        node_id = node_item.id
        port_name = port_item.name() if callable(port_item.name) else port_item.name

        # Find model node
        model_node = None
        for node in self._graph.all_nodes():
            nid = node.id() if callable(node.id) else node.id
            if nid == node_id:
                model_node = node
                break

        if not model_node:
            return None, None

        # Get port
        if is_output:
            port = model_node.get_output(port_name)
        else:
            port = model_node.get_input(port_name)

        return model_node, port

    def _get_port_data_type(self, node, port):
        """Get DataType for a port if available."""
        if hasattr(node, "get_port_type"):
            return node.get_port_type(port.name())
        return None
```

---

## Files to Modify

### 1. `src/casare_rpa/presentation/canvas/graph/node_graph_widget.py`

Add DotCreator to initialization:

```python
# In __init__():
from casare_rpa.presentation.canvas.connections.dot_creator import DotCreator

# After other managers
self._dot_creator = DotCreator(self._graph, self)
```

### 2. `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`

Export the visual reroute node:

```python
from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import VisualRerouteNode

# Add to __all__ and ALL_VISUAL_NODE_CLASSES
```

### 3. `src/casare_rpa/nodes/__init__.py`

Register RerouteNode in _NODE_REGISTRY:

```python
_NODE_REGISTRY = {
    ...
    "RerouteNode": "utility_nodes",
}
```

### 4. `src/casare_rpa/utils/workflow/workflow_loader.py`

Add RerouteNode to NODE_TYPE_MAP:

```python
from casare_rpa.nodes.utility_nodes import RerouteNode

NODE_TYPE_MAP = {
    ...
    "RerouteNode": RerouteNode,
}
```

### 5. Menu Builder (Optional)

Hide RerouteNode from context menu by checking `HIDDEN_IN_MENU` attribute:

```python
# In menu building logic:
if getattr(node_class, "HIDDEN_IN_MENU", False):
    continue  # Skip adding to menu
```

---

## Step-by-Step Implementation

### Phase 1: Core Domain Node (Est: 30 min)

1. Add `RerouteNode` to `utility_nodes.py`
2. Register in `_NODE_REGISTRY` and `NODE_TYPE_MAP`
3. Test: Import succeeds, node can be instantiated

### Phase 2: Visual Node + Graphics (Est: 1 hour)

1. Create `RerouteNodeItem` graphics class
2. Create `VisualRerouteNode` using custom graphics
3. Export from `visual_nodes/__init__.py`
4. Test: Node can be created manually, appears as small dot

### Phase 3: Alt+Click Creator (Est: 1.5 hours)

1. Create `DotCreator` event filter
2. Implement pipe hit detection
3. Implement node creation and reconnection
4. Integrate into `NodeGraphWidget`
5. Test: Alt+Click on pipe creates dot

### Phase 4: Data Type Propagation (Est: 30 min)

1. Read data type from source port
2. Set reroute node data type
3. Update port colors to match
4. Test: Dot inherits type color from connection

### Phase 5: Polish & Edge Cases (Est: 1 hour)

1. Handle exec ports (should dots work on exec connections?)
2. Dragging/positioning refinements
3. Undo/redo support
4. Serialization/deserialization
5. Hide from menu if desired

---

## Visual Appearance Concepts

### Option A: Minimal Dot (Recommended)
```
     [o]    <- 12px circle
      |     <- Connection continues through
```
- Pros: Cleanest, matches Houdini
- Cons: May be hard to select

### Option B: Small Square with Ports
```
   in->[ ]->out    <- 20px square
```
- Pros: Familiar node-like
- Cons: More visual clutter

### Option C: Diamond Shape
```
     [<>]   <- Diamond shape
```
- Pros: Distinctive, easy to spot
- Cons: Non-standard

**Recommendation**: Option A with slightly larger hit area (20px for selection, 12px visual).

---

## Considerations

### Exec Port Handling

Should dots work on exec connections?

**Arguments FOR**:
- Consistent behavior
- May help organize complex control flow

**Arguments AGAINST**:
- Exec connections are typically short
- Could confuse execution order visually

**Recommendation**: Support both but test carefully for execution order correctness.

### Chaining Dots

Users should be able to create multiple dots in sequence:
- Alt+Click on existing dot's output connection creates new dot
- Connections between dots should maintain type

### Performance

- Viewport culling should include dots
- Dots should use same optimization as other nodes

### Serialization

Dots must serialize/deserialize with:
- Position
- Data type
- Connection references

---

## Unresolved Questions

1. **Should dots appear in context menu?**
   - Recommendation: No, Alt+Click only

2. **Can dots be created on exec connections?**
   - Need to test execution order preservation

3. **Should dots auto-delete when only one connection?**
   - UiPath/Houdini: No, they persist
   - Could add a "cleanup unused dots" command

4. **Should we support multi-output from dots?**
   - NodeGraphQt ports naturally support this
   - Visual: Output can fan out to multiple targets

5. **What about copy/paste of dots?**
   - Standard node copy/paste should work
   - Test with connected chains

6. **Should Alt+Click work during live connection drag?**
   - Complex interaction state
   - Recommendation: No, require completed connection first

---

## Testing Checklist

- [ ] Create dot on data connection (String, Integer, etc.)
- [ ] Create dot on exec connection
- [ ] Dot preserves correct data type color
- [ ] Drag dot to new position
- [ ] Delete dot (X key) - connections reform
- [ ] Chain multiple dots on same path
- [ ] Undo/redo dot creation
- [ ] Save/load workflow with dots
- [ ] Copy/paste nodes including dots
- [ ] Alt+Click on empty space (should do nothing)
- [ ] Alt+Click on node (should do nothing)
- [ ] Performance with 50+ dots
