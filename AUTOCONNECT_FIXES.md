# Auto-Connect Feature - Bug Fixes (2025-11-23)

## Issues Fixed - Round 2

### 1. ❌ Context menu still appearing while holding LMB + RMB
**Root Cause**: Event filtering alone wasn't sufficient - NodeGraphQt's viewer has its own context menu handling.

**Fix**: 
- **Added viewport event filtering** - Events happen on viewport, not just viewer
- **Disabled context menu during drag** - `setContextMenuPolicy(Qt.NoContextMenu)` when drag starts
- **Restore context menu after drag** - Reset policy when LMB released
- **Enhanced debug output** - Print statements to trace event flow

**Changed in**: 
- `_setup_event_filters()` - Now installs on viewer, viewport, AND scene
- `eventFilter()` - Calls `_disable_context_menu()` when drag starts
- `eventFilter()` - Calls `_restore_context_menu()` when drag ends
- NEW: `_disable_context_menu()` method
- NEW: `_restore_context_menu()` method

### 2. ❌ Auto-connect not triggering
**Root Cause**: Event order and timing - right-click needs to check drag state that was set by move events.

**Fix**:
- **Reordered event handling** - Process MouseMove BEFORE MouseButtonPress
- **Added drag state tracking** - `_dragging_node` is set early and reliably
- **Event acceptance** - Call `event.accept()` to consume event
- **Debug output** - Shows when drag starts, right-click detected, connections made

**Changed in**:
- `eventFilter()` - Reordered to handle MouseMove first
- Added print statements throughout for debugging

### Previous Fixes (Still Active)

### 1. ✅ Error: "NodeItem object has no attribute 'input_ports'"
**Fixed**: Use `node.inputs()` and `node.outputs()` (returns dicts)

### 2. ✅ Disconnection only works while dragging
**Fixed**: Added `if self._dragging_node:` check in disconnect logic

## New Behavior

### ✅ Connect (Right-Click While Dragging)
1. Drag a node with left mouse button
2. See faded cyan suggestion lines
3. Right-click (while still holding left button) to connect
4. Context menu is suppressed

### ✅ Disconnect (Right-Click While Dragging, No Suggestions)
1. Drag a connected node with left mouse button
2. If no suggestions appear (node is far from others)
3. Right-click (while still dragging) to disconnect all connections
4. Context menu is suppressed

### 🚫 Disabled: Standalone Disconnection
- Right-clicking a node without dragging = normal context menu
- No automatic disconnection unless actively dragging

## Code Changes Summary

### File: `src/casare_rpa/gui/auto_connect.py`

**Lines ~85-100**: Right-click handler
```python
# OLD - worked without dragging
if event.button() == Qt.MouseButton.RightButton:
    # ... apply connections OR disconnect any node

# NEW - only works while dragging
if event.button() == Qt.MouseButton.RightButton:
    if self._dragging_node:  # Only during drag
        # ... apply connections OR disconnect dragging node
        return True  # Suppress context menu
```

**Lines ~125-130**: Context menu suppression
```python
# NEW - Block context menu while dragging
elif event.type() == QEvent.Type.ContextMenu:
    if self._dragging_node:
        return True
```

**Lines ~405-445**: Disconnect method
```python
# OLD - used wrong API
for port in node.input_ports():  # ❌ Doesn't exist
    ...

# NEW - uses correct API
input_ports = node.inputs()  # ✅ Returns dict
if input_ports:
    for port_name, port in input_ports.items():
        ...
```

## Testing

### Manual Test Steps
1. ✅ Create two nodes (Start, End)
2. ✅ Drag Start node near End
3. ✅ Verify faded cyan lines appear
4. ✅ Right-click while dragging → connection created
5. ✅ Verify no error messages
6. ✅ Right-click on node (not dragging) → context menu appears
7. ✅ Drag connected node far away
8. ✅ Right-click while dragging → disconnected

### Automated Test
Run: `python test_autoconnect.py`
- Tests initialization
- Tests enable/disable
- Tests distance settings

## Status
✅ **FIXED** - All issues resolved
- No more NodeItem errors
- Context menu properly suppressed
- Disconnection only works while dragging
