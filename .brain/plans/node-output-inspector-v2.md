# Node Output Inspector v2 - Simplified n8n Style

## What's Wrong Currently
- Too complex (Table/JSON/Tree views with row numbers)
- Shows flattened nested data instead of just output ports
- No drag-and-drop support
- Not matching n8n's clean Schema view

## Target UI (n8n style)

```
┌─────────────────────────────────────────────────────┐
│ OUTPUT  ✓  ⓘ    🔍   [Schema] [Table] [JSON]  ✏️  📌 │
├─────────────────────────────────────────────────────┤
│ 2 items                                              │
├─────────────────────────────────────────────────────┤
│  AB  my_field_1      value                          │
│   #  my_field_2      1                              │
│  []  my_array        (3 items)                      │
│  {}  my_object       (2 keys)                       │
└─────────────────────────────────────────────────────┘
```

## Key Changes

### 1. Schema View (Default) - NOT a table
- Simple list showing **only output ports**
- Type icon + port name + value preview
- No row numbers, no columns, no headers
- Just clean rows like n8n

### 2. Type Icons (n8n style)
- `AB` = string (gray badge)
- `#` = number
- `Y/N` = boolean
- `[]` = array (show item count)
- `{}` = object (show key count)

### 3. Drag-and-Drop Variables
- Each row is draggable
- Drag port name to any node's input widget
- Drop inserts `{{node_name.port_name}}` variable reference

### 4. Simpler Header
- "OUTPUT" title with status icon (✓ success, ⚠ error)
- Search icon (expandable)
- Tabs: Schema | Table | JSON
- Pin button

## Implementation Plan

### Phase 1: Rewrite NodeOutputPopup

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/node_output_popup.py`

1. Delete current overcomplicated views
2. Create `OutputSchemaView` - simple list widget with drag support
3. Keep `OutputJsonView` (it's good)
4. Simplify `OutputTableView` - remove row numbers, just Key/Value/Type

### Phase 2: Add Drag-and-Drop

1. Make `OutputSchemaView` items draggable
2. Set MIME type: `application/x-casare-variable`
3. Drag data: `{"node_id": "...", "port_name": "...", "variable": "{{...}}"}`

### Phase 3: Accept Drops in Node Widgets

**File**: `src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py`

1. Enable drop on QLineEdit widgets in node properties
2. On drop, insert the variable reference text

## New Schema View Design

```python
class OutputSchemaView(QListWidget):
    """Simple list of output ports with type icons and values."""

    def __init__(self):
        # Enable drag
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)

    def set_data(self, outputs: Dict[str, Any]):
        """Show only top-level output ports."""
        for port_name, value in outputs.items():
            item = OutputSchemaItem(port_name, value)
            self.addItem(item)
```

## Item Widget Layout

```
┌─────────────────────────────────────────────────────┐
│ [TYPE_BADGE]  port_name         value_preview       │
│    (icon)     (bold, draggable)  (gray, truncated)  │
└─────────────────────────────────────────────────────┘
```

- TYPE_BADGE: Small colored badge with type indicator
- port_name: Bold, white text - this is the draggable part
- value_preview: Gray, truncated value

## Files to Modify

1. **Rewrite**: `presentation/canvas/ui/widgets/node_output_popup.py`
2. **Add drop support**: `presentation/canvas/visual_nodes/base_visual_node.py`
3. **Update**: `presentation/canvas/ui/widgets/__init__.py`

## Questions Resolved

- Q: What gets shown? A: Only top-level output ports (not flattened nested data)
- Q: What's draggable? A: The port name badge
- Q: What gets inserted? A: `{{NodeName.port_name}}` variable reference
