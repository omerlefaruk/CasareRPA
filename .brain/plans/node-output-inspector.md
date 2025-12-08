# Node Output Inspector Feature

## Overview
Middle-click on a node to show output port values in a beautiful popup window, similar to n8n.

## Trigger
- **Middle-click** on any node in the canvas
- Keyboard shortcut: `Ctrl+Shift+O` when node selected

## UI Components

### 1. NodeOutputPopup (Primary)
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/node_output_popup.py`

600x480px popup window with:
- **Header**: Node icon + name, Pin button, Close button
- **Tab Bar**: [Table] [JSON] [Tree] view modes + execution time
- **Content**:
  - Table view (for arrays) - sortable, paginated
  - JSON view (syntax highlighted) - expand/collapse
  - Tree view (hierarchical) - type icons
- **Footer**: Search filter, item count, Copy All button

### 2. JsonSyntaxHighlighter
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/json_syntax_highlighter.py`

Syntax colors (VSCode Dark+):
- Keys: #9CDCFE
- Strings: #CE9178
- Numbers: #B5CEA8
- Booleans: #569CD6

### 3. PortValueHint (Secondary - Phase 2)
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/port_value_hint.py`

Small labels below output ports showing truncated values.

## Implementation Steps

### Phase 1: Core Popup

1. **Create NodeOutputPopup widget**
   - QFrame with frameless window hint
   - Position near clicked node (smart positioning to stay in viewport)
   - Fade-in animation (150ms)

2. **Implement Header**
   - QHBoxLayout: icon (32x32) + name label + spacer + pin + close
   - Pin toggle: keep popup open when clicking elsewhere
   - Close: hide popup

3. **Implement Tab Bar**
   - QTabBar for view mode switching
   - Persist last selected mode per session

4. **Implement Table View**
   - QTableWidget with alternating row colors
   - Columns: Index, Key, Value, Type
   - Sortable headers
   - Pagination widget for >100 items

5. **Implement JSON View**
   - QPlainTextEdit with JsonSyntaxHighlighter
   - Line numbers sidebar
   - Expand/Collapse all buttons
   - Copy button

6. **Implement Tree View**
   - QTreeWidget with type icons
   - Expand/collapse nodes
   - Type-colored values

7. **Implement Footer**
   - Search/filter QLineEdit
   - Item count label
   - Copy All button

### Phase 2: Integration

8. **Hook middle-click in CustomNodeItem**
   - Override `mousePressEvent` for middle button
   - Emit signal to show popup
   - Pass node output data

9. **Store output values in nodes**
   - Add `_last_output: dict` to BaseVisualNode
   - Update after execution via ExecutionController

10. **Handle empty/loading/error states**
    - Empty: "No output data - run workflow"
    - Loading: Spinner during execution
    - Error: Red panel with error message

### Phase 3: Polish

11. **Animations**
    - Fade-in popup appearance
    - Value update highlight flash
    - Port pulse on new data

12. **Keyboard shortcuts**
    - Ctrl+Shift+O: Toggle popup
    - Ctrl+1/2/3: Switch view modes
    - Escape: Close popup

13. **Inline port hints** (optional)
    - Small value labels below ports
    - Toggle via View menu

## Data Flow

```
Node Execution
    │
    ▼
ExecutionController.on_node_complete(node_id, outputs)
    │
    ▼
VisualNode._last_output = outputs
    │
    ▼
EventBus.emit("node.output_updated", node_id)
    │
    ▼
NodeOutputPopup.refresh() (if open for that node)
```

## Event Integration

New events needed:
- `node.output_updated(node_id: str, outputs: dict)` - after execution
- `node.middle_clicked(node_id: str, pos: QPoint)` - trigger popup

## Files to Create/Modify

### Create
- `presentation/canvas/ui/widgets/node_output_popup.py`
- `presentation/canvas/ui/widgets/json_syntax_highlighter.py`

### Modify
- `presentation/canvas/graph/custom_node_item.py` - add middle-click handler
- `presentation/canvas/visual_nodes/base_visual_node.py` - add `_last_output`
- `presentation/canvas/controllers/execution_controller.py` - store outputs
- `presentation/canvas/events/event_bus.py` - add new events

## Open Questions (Resolved)

1. **Pinning**: Pinned popups float above canvas (QDialog with StayOnTop hint)
2. **Multiple popups**: Allow max 3 pinned popups simultaneously
3. **Live updates**: Auto-refresh during execution if popup open
4. **Data limits**: Truncate display at 10MB, show warning

## Dependencies
- None (uses existing Qt/PySide6)

## Testing
- Unit test JsonSyntaxHighlighter patterns
- Integration test middle-click → popup flow
- Manual test all view modes with various data types
