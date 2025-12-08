# Node & Wire Visual Fixes Plan

## Issues Identified

### 1. Wire Coloring Bug (ALL WIRES WHITE) ✅ FIXED
**File**: `src/casare_rpa/presentation/canvas/graph/custom_pipe.py`
**Root Cause**: In `_get_port_data_type()`, `_port_types.get(port_name)` returns `None` for both:
- Exec ports (intentionally set to None)
- Ports not in the dict (key doesn't exist)

**Fix Applied**: Check if key EXISTS before getting value:
```python
if hasattr(node, "_port_types"):
    if port_name in node._port_types:
        return node._port_types[port_name]  # Could be None for exec
    # Key doesn't exist - fall through to name-based detection
```

### 2. Wire Thickness (Same Issue) ✅ FIXED
Same root cause - computed alongside color. Fix #1 resolved this.

### 3. Reroute Node Registration Error ✅ FIXED
**File**: `src/casare_rpa/presentation/canvas/connections/reroute_insert.py`
**Fix Applied**:
- Added VisualRerouteNode to registry
- Used correct identifier format
- Set port types BEFORE connecting to pass validation

### 4. Reroute Node Visual Bug (Port Triangles/Labels Showing) ✅ FIXED
**File**: `src/casare_rpa/presentation/canvas/visual_nodes/utility/reroute_node.py`
**Root Cause**: NodeGraphQt port rendering happens in PortItem.paint()

**Fix Applied**: Use NodeGraphQt's painter_func parameter with empty function:
```python
def _invisible_port_painter(painter, rect, info):
    pass  # Draw nothing

self.add_input("in", display_name=False, painter_func=_invisible_port_painter)
self.add_output("out", display_name=False, painter_func=_invisible_port_painter)
```

### 5. Flow Animation Not Triggering ✅ ADDED
**File**: `src/casare_rpa/presentation/canvas/controllers/execution_controller.py`
**Fix Applied**: Added `_start_pipe_animations()` and `_stop_pipe_animations()` methods
- Called from `_on_node_started()`, `_on_node_completed()`, `_on_node_error()`

### 6. Node Header Colors (SOLID instead of gradient) ✅ FIXED
**File**: `src/casare_rpa/presentation/canvas/graph/custom_node_item.py`
**Fix Applied**: Changed header to solid colors (no gradient)

### 7. Hotkey 4 + Ctrl+E Disable ✅ UNIFIED
**Files**: `node_controller.py`, `node_graph_widget.py`
**Fix Applied**: Both now use `view.set_disabled()` and sync `casare_node.config["_disabled"]`

### 8. Compatibility Feedback (Red Dashed Line) - PENDING
Need to verify the pipe `set_incompatible()` is called during drag.

### 9. Completion Glow - PENDING
Not implemented yet.

## Files to Modify

1. `src/casare_rpa/presentation/canvas/graph/custom_pipe.py`
   - Fix `_get_port_data_type()` key check

2. `src/casare_rpa/presentation/canvas/connections/reroute_insert.py`
   - Fix node creation to use class instead of string

3. `src/casare_rpa/presentation/canvas/controllers/execution_controller.py`
   - Add pipe animation triggers

4. `src/casare_rpa/presentation/canvas/graph/custom_node_item.py`
   - Change header to solid colors
   - Update `_CATEGORY_HEADER_COLORS` with distinct solid colors

## Category Colors (Solid, Distinct)
```python
_CATEGORY_HEADER_COLORS = {
    "browser": QColor(156, 39, 176),      # Purple - #9C27B0
    "navigation": QColor(103, 58, 183),   # Deep Purple - #673AB7
    "interaction": QColor(63, 81, 181),   # Indigo - #3F51B5
    "data": QColor(76, 175, 80),          # Green - #4CAF50
    "variable": QColor(0, 150, 136),      # Teal - #009688
    "control_flow": QColor(244, 67, 54),  # Red - #F44336
    "error_handling": QColor(255, 87, 34),# Deep Orange - #FF5722
    "wait": QColor(255, 152, 0),          # Orange - #FF9800
    "debug": QColor(158, 158, 158),       # Gray - #9E9E9E
    "utility": QColor(96, 125, 139),      # Blue Gray - #607D8B
    "file_operations": QColor(121, 85, 72),# Brown - #795548
    "database": QColor(33, 150, 243),     # Blue - #2196F3
    "rest_api": QColor(3, 169, 244),      # Light Blue - #03A9F4
    "email": QColor(233, 30, 99),         # Pink - #E91E63
    "office_automation": QColor(33, 123, 75),# Office Green
    "desktop": QColor(0, 188, 212),       # Cyan - #00BCD4
    "triggers": QColor(255, 193, 7),      # Amber - #FFC107
    "messaging": QColor(139, 195, 74),    # Light Green - #8BC34A
    "ai_ml": QColor(171, 71, 188),        # Purple accent
    "document": QColor(255, 152, 0),      # Orange - #FF9800
    "google": QColor(66, 133, 244),       # Google Blue
    "scripts": QColor(205, 220, 57),      # Lime - #CDDC39
    "system": QColor(63, 81, 181),        # Indigo
}
```
