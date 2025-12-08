# Alt+Drag Node Duplication (Houdini-style)

## Status: IMPLEMENTED

## Goal
Alt+LMB drag on a node creates a duplicate that follows the mouse cursor.

## Implementation

### Location
`src/casare_rpa/presentation/canvas/graph/node_graph_widget.py`

### Changes Made

1. **`__init__`** (line ~192): Added `self._alt_drag_node = None` tracking attribute

2. **`_get_node_at_view_pos()`** (lines 1219-1252): Helper to find node at cursor
   - Uses `scene.itemAt()` + walks up parent chain to find NodeItem
   - Returns the NodeGraphQt node object

3. **`_alt_drag_duplicate()`** (lines 1274-1362): Main duplicate logic
   - Gets node under cursor
   - Copies + pastes to duplicate
   - Positions duplicate centered at cursor
   - Sends synthetic mouse press event to initiate drag

4. **`eventFilter()`** (lines 1003-1009): Alt+LMB detection
   - Checks for `LeftButton + AltModifier`
   - Calls `_alt_drag_duplicate()` if conditions met

5. **Mouse release cleanup** (lines 1035-1038): Clears `_alt_drag_node` reference

### Usage
Hold Alt + LMB click-drag on any node to create and drag a duplicate.
