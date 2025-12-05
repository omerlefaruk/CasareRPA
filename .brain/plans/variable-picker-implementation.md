# Variable Picker Implementation Plan

**Date**: 2025-12-05
**Status**: COMPLETE ✓
**Priority**: High (UX Enhancement)
**Completion Date**: 2025-12-05

---

## Goal

Add a variable insertion button (`{x}` icon) that appears on hover for node widget parameters. When clicked, shows a dropdown with all available variables. Keyboard navigation (arrow keys) and click selection inserts `{{varName}}` into the input field.

---

## Implementation Summary

### Files Created

| File | Purpose |
|------|---------|
| `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py` | VariableInfo, VariableProvider, VariablePickerPopup, VariableButton, VariableAwareLineEdit |
| `tests/presentation/ui/test_variable_picker.py` | 30 unit tests (all passing) |

### Files Modified

| File | Changes |
|------|---------|
| `src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py` | Added `_add_variable_aware_text_input()` - creates standard text input then replaces internal QLineEdit with VariableAwareLineEdit |
| `src/casare_rpa/presentation/canvas/graph/node_widgets.py` | Integrated VariableAwareLineEdit into create_file_path_widget and create_directory_path_widget |
| `src/casare_rpa/presentation/canvas/ui/widgets/__init__.py` | Exported VariableInfo, VariableProvider, VariablePickerPopup, VariableButton, VariableAwareLineEdit, create_variable_aware_line_edit |
| `src/casare_rpa/presentation/canvas/initializers/ui_component_initializer.py` | Added `_connect_variable_provider()` to connect singleton to MainWindow |
| `src/casare_rpa/presentation/canvas/graph/node_graph_widget.py` | Added `_update_variable_picker_context()` called on node creation |

### Key Features Implemented

1. **VariableInfo dataclass**: name, var_type, source, value, children, path
2. **VariableProvider singleton**: Custom + workflow + system variables
3. **VariablePickerPopup**: Search, grouped sections, type badges, keyboard nav
4. **VariableButton**: {x} icon, appears on hover
5. **VariableAwareLineEdit**: Hover button, Ctrl+Space, {{ trigger

### System Variables

- `$currentDate`: Current date (YYYY-MM-DD)
- `$currentTime`: Current time (HH:MM:SS)
- `$currentDateTime`: ISO datetime
- `$timestamp`: Unix timestamp

### Type Badges (VSCode colors)

| Type | Badge | Color |
|------|-------|-------|
| String | T | #4ec9b0 |
| Integer | # | #569cd6 |
| Float | . | #9cdcfe |
| Boolean | ? | #c586c0 |
| List | [] | #ce9178 |
| Dict | {} | #dcdcaa |
| DataTable | tbl | #d16d9e |

---

## Design Decision Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Syntax** | `{{varName}}` | Already used in codebase (variable_resolver.py) |
| **Primary trigger** | Hover button (x icon) | Discoverability for RPA users |
| **Secondary trigger** | `Ctrl+Space` | Developer familiarity |
| **Tertiary trigger** | `{{` typing | Quick inline insertion |
| **Position** | Right side of input field | Power Automate style |
| **Dropdown** | Below button, left-aligned | Standard UX pattern |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  NodeTextInputWidget (enhanced)                              │
│  ┌─────────────────────────────────────────────┐ ┌────┐     │
│  │ Enter URL...                                │ │ {x}│     │
│  └─────────────────────────────────────────────┘ └────┘     │
│                                                   ↓          │
│                              ┌─────────────────────────────┐ │
│                              │ VARIABLES                   │ │
│                              │  ► url          String      │ │
│                              │    counter      Integer     │ │
│                              │────────────────────────────│ │
│                              │ FROM: Read CSV              │ │
│                              │    row_data     Dict        │ │
│                              │────────────────────────────│ │
│                              │ SYSTEM                      │ │
│                              │    $currentDate DateTime   │ │
│                              └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Components to Create

### 1. VariablePickerPopup (QWidget)
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py`

```python
class VariablePickerPopup(QWidget):
    """Dropdown popup showing available variables."""

    variable_selected = Signal(str)  # Emits "{{varName}}"

    def __init__(self, parent=None):
        # Frameless, popup window
        # QListWidget with custom item delegate
        # Search filter QLineEdit at top
        # Grouped sections: Variables, Node Outputs, System

    def show_at(self, global_pos: QPoint):
        """Position and show popup below the button."""

    def set_variables(self, variables: List[VariableInfo]):
        """Populate list with available variables."""

    def keyPressEvent(self, event):
        """Handle arrow keys, Enter, Escape."""
```

### 2. VariableButton (QPushButton)
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py`

```python
class VariableButton(QPushButton):
    """Small 'x' button that appears on hover."""

    def __init__(self, parent=None):
        # Fixed size: 20x20
        # Icon: "x" or "{x}" or variable icon
        # Tooltip: "Insert variable (Ctrl+Space)"
        # Initially hidden, shown on parent hover
```

### 3. VariableAwareLineEdit (QLineEdit)
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py`

```python
class VariableAwareLineEdit(QLineEdit):
    """LineEdit with variable picker integration."""

    def __init__(self, parent=None):
        # Install event filter for Ctrl+Space
        # Install event filter for "{{" trigger
        # Create VariableButton (hidden by default)

    def enterEvent(self, event):
        """Show variable button on hover."""

    def leaveEvent(self, event):
        """Hide button (with delay for click)."""

    def keyPressEvent(self, event):
        """Handle Ctrl+Space trigger."""

    def insert_variable(self, var_text: str):
        """Insert {{varName}} at cursor position."""
```

### 4. VariableProvider (Protocol/Interface)
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py`

```python
@dataclass
class VariableInfo:
    name: str
    type: str  # String, Integer, Float, etc.
    source: str  # "workflow", "node:NodeName", "system"
    value: Optional[Any] = None  # Current value for preview

class VariableProvider(Protocol):
    """Interface for getting available variables."""

    def get_workflow_variables(self) -> List[VariableInfo]:
        """Get user-defined workflow variables."""

    def get_node_outputs(self, current_node_id: str) -> List[VariableInfo]:
        """Get outputs from upstream nodes."""

    def get_system_variables(self) -> List[VariableInfo]:
        """Get built-in system variables."""
```

---

## Integration Points

### 1. Update node_widgets.py

Modify `create_file_path_widget()` and existing text widgets:

```python
# Replace QLineEdit with VariableAwareLineEdit
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableAwareLineEdit,
    VariablePickerPopup,
)

line_edit = VariableAwareLineEdit()  # Instead of QLineEdit()
line_edit.set_variable_provider(...)  # Connect to variable source
```

### 2. Update NodeBaseWidget patches

In `_install_widget_init_patches()`, add variable picker to text inputs:

```python
# After creating NodeLineEdit
original_lineedit_init = NodeLineEdit.__init__

def patched_lineedit_init(self, ...):
    original_lineedit_init(self, ...)
    VariablePickerIntegration.enhance(self)
```

### 3. Variable Source Connection

Connect to existing variable storage:
- `ExecutionState.variables` - Runtime variables
- `WorkflowController` - Access to workflow variables
- `NodeGraph` - Access to node outputs

```python
# In MainWindow or ComponentFactory
def create_variable_provider(self) -> VariableProvider:
    return WorkflowVariableProvider(
        workflow_controller=self._workflow_controller,
        node_graph=self._graph,
    )
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `Ctrl+Space` | Open/toggle popup |
| `↑` / `↓` | Navigate list items |
| `Enter` | Select highlighted item |
| `Tab` | Select and move to next field |
| `Escape` | Close popup |
| `{{` | Trigger inline autocomplete |
| Type | Filter variables by name |

---

## Styling

```python
VARIABLE_BUTTON_STYLE = """
QPushButton {
    background: transparent;
    border: none;
    color: #808080;
    font-size: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background: #3c3c50;
    color: #0078d4;
    border-radius: 3px;
}
"""

VARIABLE_POPUP_STYLE = """
QWidget {
    background: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 6px 10px;
    border-radius: 3px;
}
QListWidget::item:hover {
    background: #2a2d2e;
}
QListWidget::item:selected {
    background: #094771;
    color: white;
}
"""
```

---

## Type Badges

| Type | Color | Icon |
|------|-------|------|
| String | Green (#4ec9b0) | `"T"` |
| Integer | Blue (#569cd6) | `"#"` |
| Float | Cyan (#9cdcfe) | `"."` |
| Boolean | Purple (#c586c0) | `"?"` |
| List | Orange (#ce9178) | `"[]"` |
| Dict | Yellow (#dcdcaa) | `"{}"` |
| DataTable | Pink (#d16d9e) | table icon |

---

## Implementation Phases

### Phase 1: Core Widget (MVP)
1. Create `VariablePickerPopup` with basic list
2. Create `VariableButton` with hover behavior
3. Create `VariableAwareLineEdit` wrapper
4. Connect to workflow variables only
5. Basic keyboard navigation (arrows, Enter, Escape)

### Phase 2: Enhanced UX
1. Add search/filter functionality
2. Add type badges and icons
3. Add Ctrl+Space keyboard shortcut
4. Add `{{` trigger for inline autocomplete
5. Grouped sections (Variables, Node Outputs, System)

### Phase 3: Full Integration
1. Integrate with all text input widgets in nodes
2. Add node output variables (upstream connections)
3. Add system variables ($currentDate, etc.)
4. Add variable preview on hover
5. Unit tests

---

## Files to Create/Modify

### New Files
- `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py` (main implementation)

### Modified Files
- `src/casare_rpa/presentation/canvas/graph/node_widgets.py` (integrate VariableAwareLineEdit)
- `src/casare_rpa/presentation/canvas/ui/widgets/__init__.py` (export new widgets)
- `src/casare_rpa/presentation/canvas/component_factory.py` (variable provider setup)

---

## Unresolved Questions

1. **Scope visibility**: Show all variables or only in-scope (upstream nodes)?
   - Recommendation: Show all, mark out-of-scope as grayed

2. **Nested access**: Support `{{data.field}}` or `{{list[0]}}`?
   - Recommendation: Phase 2, start with simple `{{varName}}`

3. **Value preview**: Show current value on hover?
   - Recommendation: Yes, in tooltip - helps debugging

4. **Expression support**: Allow `{{counter + 1}}`?
   - Recommendation: No, variables only. Expressions are separate feature.

5. **Graphics scene integration**: How to handle popup in QGraphicsScene?
   - Use QDialog with Qt.Popup flag, position using mapToGlobal()

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Popup clipping in graphics scene | High | Use Qt.Popup flag, test z-order |
| Performance with many variables | Medium | Virtualized list, lazy loading |
| Focus stealing from line edit | Medium | Proper focus management |
| Widget replacement breaking existing nodes | High | Gradual rollout, feature flag |

---

## Testing Plan

1. **Unit tests**: VariablePickerPopup, keyboard navigation
2. **Integration tests**: Variable insertion, cursor position
3. **Visual tests**: Hover behavior, popup positioning
4. **Manual tests**: Test with 50+ variables, test in all node types
