# Reroute/Dot Node Implementation Research

## Executive Summary

Research on professional node editors (Houdini, Nuke, Blender, Unreal Engine) reveals consistent patterns for reroute/dot nodes. The core challenge in NodeGraphQt is that pipe drawing uses port scene positions, but ports are positioned at node edges by default.

---

## 1. Professional Tool Analysis

### Houdini Network Dots

**Source**: [SideFX Docs - Wiring Nodes](https://www.sidefx.com/docs/houdini/network/wire.html), [Network Editor Tutorial](https://www.sidefx.com/tutorials/network-editor-dots-and-wires/)

**Visual Design**:
- Small circular dot (approximately 10-14px diameter)
- Color inherits from connected wire/data type
- Two states: **Pinned** and **Unpinned**
  - Pinned: Persists even when all connections removed (scaffolding)
  - Unpinned: Auto-deleted when input/output connections cut

**Interaction**:
- **Create**: Alt+LMB on wire creates dot at click position
- **Move**: Drag the dot directly
- **Toggle Pin**: Alt+Click on existing dot
- **Delete**: Unpinned dots auto-delete when disconnected

**Known Issue**: At zoom-out, selecting dots is difficult - system tries to drag wire instead of select dot.

---

### Nuke Dot Node

**Source**: [Foundry Nuke Docs](https://learn.foundry.com/nuke/content/getting_started/using_interface/working_nodes.html), [Connection Tips](https://learn.foundry.com/nuke/content/tutorials/written_tutorials/tutorial1/connection_tips.html)

**Visual Design**:
- Small dot/diamond shape
- Yellow highlight when creating via Ctrl key
- Minimal visual footprint

**Interaction**:
- **Create**: Hold Ctrl, yellow diamond appears, click to create
- **Alternative**: Drag from connection, select "Dot" from menu
- **Named Dots**: Can be labeled for long-distance routing
- Custom scripts add shortcuts like Ctrl+Shift+. for named dots

**Purpose**: "A pinned dot is very much like a dot in Nuke, and lets you build chunks of networks, with dangling dots as scaffolding which you can connect to later."

---

### Blender Reroute Node

**Source**: [Blender Manual - Reroute](https://docs.blender.org/manual/en/2.90/interface/controls/nodes/reroute.html), [Blender Dev Blog](https://code.blender.org/2025/08/new-socket-shapes/)

**Visual Design**:
- Single small socket/circle
- Color inherits from connected socket type (dynamic typing)
- Circle shape indicates "flexible data type"
- Label propagation feature (auto-labels through chains)

**Connection Behavior**:
- **One input, multiple outputs** - acts like a splitter
- Socket type propagates through chain
- "Curved node links always attach horizontally to the reroute node to avoid breaking the visual flow"

**Interaction**:
- **Create**: Shift+LMB sweep across link inserts reroute
- **Move**: G key (grab mode)
- **Alternative**: Cut Links tool with Shift held

**Technical Note**: Blender 3.2+ ensures pipes attach horizontally to maintain visual flow.

---

### Unreal Engine Blueprint Reroute

**Source**: [UE5 Docs - Connecting Nodes](https://dev.epicgames.com/documentation/en-us/unreal-engine/connecting-nodes-in-unreal-engine), [CBGameDev Tips](https://www.cbgamedev.com/blog/2020/12/16/quick-dev-tip-4-ue4-reroute-nodes)

**Visual Design**:
- Small knot/pin shape
- Color matches wire type (exec = white, data = colored)
- Called "reroute" or "knot" internally (UK2Node_Knot)

**Interaction**:
- **Create**: Double-click on wire
- **Alternative**: Drag from pin, select "Add Reroute Node"
- **Alternative**: LMB while dragging wire creates reroute
- **Named Reroute**: Materials-only feature for reference by name

**Implementation**:
- Class: `UK2Node_Knot`
- Override: `DrawNodeAsVariable()` returns true for minimal appearance
- Override: `ShouldDrawCompact()` returns true

**Best Practice**: "Bring a single strand closer to where the information is needed and split to the required places from there."

---

## 2. Common Patterns Across Tools

| Aspect | Houdini | Nuke | Blender | Unreal |
|--------|---------|------|---------|--------|
| Size | ~10-14px | ~10px | ~12px | ~10px |
| Shape | Circle | Diamond/Dot | Circle | Knot/Pin |
| Color | Wire type | Wire type | Socket type | Wire type |
| Create | Alt+Click | Ctrl+Click | Shift+Sweep | Double-click |
| Ports Visible | No | No | No (single socket) | No |
| Multi-output | Yes | Yes | Yes | Yes |
| Auto-delete | Unpinned only | No | No | No |

### Key Visual Characteristics

1. **Size**: 10-16px diameter (small but clickable)
2. **Ports Hidden**: All tools hide traditional port visuals
3. **Connections to Center**: Wires connect to visual center, not edges
4. **Type Inheritance**: Color/type flows from connected wires
5. **Selection State**: Glow or border highlight when selected

---

## 3. NodeGraphQt Technical Analysis

### Current Pipe Drawing (pipe.py lines 293-367)

```python
def draw_path(self, start_port, end_port=None, cursor_pos=None):
    # Get start / end positions from PORT scene positions
    pos1 = start_port.scenePos()
    pos1.setX(pos1.x() + (start_port.boundingRect().width() / 2))
    pos1.setY(pos1.y() + (start_port.boundingRect().height() / 2))

    if end_port:
        pos2 = end_port.scenePos()
        pos2.setX(pos2.x() + (start_port.boundingRect().width() / 2))
        pos2.setY(pos2.y() + (start_port.boundingRect().height() / 2))
```

**Key Insight**: Pipe endpoints are calculated from `port.scenePos()` + half bounding rect. This means:
- Port position determines where pipe connects
- If port is at node edge, pipe goes to edge
- If port is at node center, pipe goes to center

### Port Positioning

Ports are children of the node graphics item. Their position relative to the node determines where pipes connect.

### Current Reroute Implementation Issues

Your `RerouteNodeItem` attempts to:
1. Hide port visuals via `paint = empty_paint`
2. Set port position to (0, 0) via `child.setPos(0, 0)`
3. Use QTimer delays to override NodeGraphQt layout

**Problem**: NodeGraphQt's node layout system repositions ports AFTER your initialization, overriding the (0, 0) position.

---

## 4. Technical Solutions

### Option A: Override Port Scene Position (Recommended)

Create a custom port class that reports center position regardless of actual position:

```python
class CenteringPortItem(PortItem):
    """Port that reports scene position at parent node center."""

    def scenePos(self):
        # Return node center instead of actual port position
        if self.parentItem():
            return self.parentItem().scenePos()
        return super().scenePos()
```

**Pros**: Clean, minimal code changes, respects NodeGraphQt architecture
**Cons**: Requires custom port registration

### Option B: Custom Pipe Drawing for Reroute

Subclass PipeItem to detect reroute nodes and draw to center:

```python
class ReroutePipeItem(PipeItem):
    def draw_path(self, start_port, end_port=None, cursor_pos=None):
        # Check if either port belongs to reroute node
        if self._is_reroute_port(start_port):
            pos1 = start_port.node.scenePos()  # Node center
        else:
            pos1 = ... # Normal calculation

        # Similar for end_port
        ...
```

**Pros**: Full control over drawing
**Cons**: Need to ensure all pipes use this class

### Option C: Override NodeItem Positioning (Current Approach, Improved)

Keep ports at (0, 0) but use `ItemSendsScenePositionChanges` flag and intercept repositioning:

```python
class RerouteNodeItem(NodeItem):
    def itemChange(self, change, value):
        result = super().itemChange(change, value)

        # After ANY change, force ports back to center
        if change in (ItemPositionHasChanged, ItemChildAddedChange):
            for child in self.childItems():
                if "Port" in child.__class__.__name__:
                    child.setPos(0, 0)

        return result
```

**Pros**: Works with existing node class
**Cons**: Fighting against NodeGraphQt, requires constant reposition

### Option D: Use NodeGraphQt's CircleNode

NodeGraphQt includes `base_node_circle.py` with `NodeItemCircle` - a circular node shape. Could extend this:

```python
from NodeGraphQt.qgraphics.node_circle import NodeItemCircle

class RerouteDotItem(NodeItemCircle):
    # Already circular, just make smaller
    pass
```

**Pros**: Uses existing circular node infrastructure
**Cons**: May still have port positioning issues

---

## 5. Recommended Implementation

### Visual Design Specification

```
Size: 16px diameter (8px radius)
Hit Area: 24px diameter (larger for easy clicking)
Colors:
  - Default: Inherit from connection data type
  - Exec Flow: White (#FFFFFF)
  - Selected Border: Yellow (#FFD700) with 3px glow
  - Selected Glow: Yellow at 30% opacity

States:
  - Normal: Solid fill, subtle border
  - Hover: Slight brightness increase
  - Selected: Yellow glow + border
  - Dragging: Semi-transparent
```

### Interaction Patterns

```
CREATE:
  - Alt+Click on pipe: Create at click position (current)
  - Drag from port to empty space + context menu: "Add Reroute"

CONNECT:
  - Drag from any port to reroute dot
  - Reroute accepts connection at center (not visible ports)

MOVE:
  - Click and drag dot directly
  - Pipes update in real-time

DELETE:
  - Delete key: Removes dot, cuts connections (no reconnection)
  - Optional: Shift+Delete reconnects original source/target
```

### Technical Approach (Hybrid A+C)

1. **Custom Port Class** for reroute nodes that reports center position:

```python
# In reroute_node_item.py

class ReroutePortItem(PortItem):
    """Port item that reports position at node center."""

    def scenePos(self):
        """Return node center for pipe drawing."""
        parent = self.parentItem()
        if parent:
            return parent.scenePos()
        return super().scenePos()

    def paint(self, painter, option, widget):
        """Don't paint - port is invisible."""
        pass

    def boundingRect(self):
        """Minimal bounding rect at center."""
        return QRectF(-2, -2, 4, 4)
```

2. **Use Custom Ports** in RerouteNodeItem:

```python
class RerouteNodeItem(NodeItem):
    def __init__(self, name="reroute", parent=None):
        super().__init__(name, parent)
        # Replace standard ports with centering ports
        self._use_custom_ports = True

    def _create_port(self, port_type, ...):
        """Override to create ReroutePortItem."""
        return ReroutePortItem(...)
```

3. **Register Custom Node** with NodeGraphQt that uses these ports.

---

## 6. Implementation Checklist

- [ ] Create `ReroutePortItem` class with center-reporting `scenePos()`
- [ ] Update `RerouteNodeItem` to use custom ports
- [ ] Ensure ports are created at initialization, not added later
- [ ] Test pipe drawing connects to visual center
- [ ] Verify selection works (larger hit area)
- [ ] Test zoom behavior (dot remains clickable at various zooms)
- [ ] Add keyboard shortcut documentation
- [ ] Test deletion behavior (cuts connection)

---

## 7. Open Questions

1. **Should reroute support pinned/unpinned states like Houdini?**
   - Current: All reroutes are "pinned" (persist when disconnected)
   - Alternative: Auto-delete unpinned when disconnected

2. **Should Delete reconnect original nodes?**
   - Current: Cuts connection
   - Alternative: Shift+Delete to reconnect

3. **Should we support chaining reroutes?**
   - Reroute -> Reroute -> Node
   - Type/color should propagate through chain

4. **Zoom scaling behavior?**
   - Fixed size regardless of zoom?
   - Or scale with zoom (harder to click when zoomed out)?

---

## Sources

- [SideFX Houdini - Wiring Nodes](https://www.sidefx.com/docs/houdini/network/wire.html)
- [SideFX Houdini - Network Dots Tutorial](https://www.sidefx.com/tutorials/network-editor-dots-and-wires/)
- [SideFX Forum - Organizing Wires](https://www.sidefx.com/forum/topic/97966/)
- [Foundry Nuke - Working with Nodes](https://learn.foundry.com/nuke/content/getting_started/using_interface/working_nodes.html)
- [Foundry Nuke - Connection Tips](https://learn.foundry.com/nuke/content/tutorials/written_tutorials/tutorial1/connection_tips.html)
- [Blender Manual - Reroute Node](https://docs.blender.org/manual/en/2.90/interface/controls/nodes/reroute.html)
- [Blender Dev Blog - New Socket Shapes](https://code.blender.org/2025/08/new-socket-shapes/)
- [Unreal Engine 5 - Connecting Nodes](https://dev.epicgames.com/documentation/en-us/unreal-engine/connecting-nodes-in-unreal-engine)
- [CBGameDev - Reroute Nodes Tips](https://www.cbgamedev.com/blog/2020/12/16/quick-dev-tip-4-ue4-reroute-nodes)
- [NodeGraphQt GitHub](https://github.com/jchanvfx/NodeGraphQt)
