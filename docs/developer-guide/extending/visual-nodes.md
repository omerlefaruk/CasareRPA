# Visual Nodes

Visual nodes provide the canvas representation of CasareRPA nodes using PySide6 and NodeGraphQt. This guide covers creating custom visual nodes with proper UI integration.

## Architecture Overview

```
                    NodeGraphQt
                        |
                        v
+------------------------------------------+
|              VisualNode (base)           |
|  - Extends NodeGraphQt.BaseNode          |
|  - Links to CasareRPA BaseNode           |
|  - Auto-generates widgets from schema    |
|  - Manages port types and colors         |
+------------------------------------------+
                        |
                        v
+------------------------------------------+
|         Your Visual Node Class           |
|  - Sets NODE_NAME, NODE_CATEGORY         |
|  - Optionally adds custom widgets        |
|  - Optionally overrides setup_ports()    |
+------------------------------------------+
```

## Basic Visual Node

Most visual nodes require minimal code:

```python
"""Visual node for MyOperationNode."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualMyOperationNode(VisualNode):
    """Visual representation of MyOperationNode."""

    # Required: NodeGraphQt identifier
    __identifier__ = "casare_rpa.mycategory"

    # Required: Display name shown on canvas
    NODE_NAME = "My Operation"

    # Required: Category for palette grouping
    NODE_CATEGORY = "mycategory"

    # Optional: Explicit link to domain class
    # Auto-derived from class name if not set: VisualMyOperationNode -> MyOperationNode
    # CASARE_NODE_CLASS = "MyOperationNode"

    def __init__(self) -> None:
        super().__init__()
        # Widgets are auto-generated from @properties decorator
        # Leave empty unless you need custom widgets
```

## Class Attributes

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `__identifier__` | `str` | NodeGraphQt namespace (e.g., `"casare_rpa.browser"`) |
| `NODE_NAME` | `str` | Display name on canvas |
| `NODE_CATEGORY` | `str` | Category for palette grouping |

### Optional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `CASARE_NODE_CLASS` | `str` | Domain class name (auto-derived from class name) |

### Class Name Auto-Derivation

The domain class is automatically derived by removing "Visual" prefix:

| Visual Class | Domain Class |
|--------------|--------------|
| `VisualClickElementNode` | `ClickElementNode` |
| `VisualReadFileNode` | `ReadFileNode` |
| `VisualHttpGetNode` | `HttpGetNode` |

Set `CASARE_NODE_CLASS` explicitly only when the name doesn't follow this pattern.

## Widget Auto-Generation

The `@properties` decorator on the domain node automatically generates widgets:

```python
# Domain node (nodes/mycategory/my_node.py)
@properties(
    PropertyDef("url", PropertyType.STRING, required=True, essential=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000, tab="advanced"),
    PropertyDef("method", PropertyType.CHOICE, choices=["GET", "POST"]),
)
class MyNode(BaseNode):
    ...

# Visual node - widgets auto-generated, no code needed
class VisualMyNode(VisualNode):
    __identifier__ = "casare_rpa.http"
    NODE_NAME = "My Node"
    NODE_CATEGORY = "http"

    def __init__(self):
        super().__init__()
        # url: Text input (essential, always visible)
        # timeout: Spinner (in advanced section)
        # method: Dropdown with GET/POST options
```

### Widget Mapping

| PropertyType | Generated Widget |
|--------------|------------------|
| `STRING` | Variable-aware text input |
| `TEXT` | Multi-line text area |
| `INTEGER` | Spinner |
| `FLOAT` | Float spinner |
| `BOOLEAN` | Checkbox |
| `CHOICE` | Dropdown combo box |
| `MULTI_CHOICE` | Multi-select list |
| `FILE_PATH` | Text input (replace with `NodeFilePathWidget`) |
| `DIRECTORY_PATH` | Text input (replace with `NodeDirectoryPathWidget`) |
| `JSON` | JSON editor |
| `CODE` | Code editor |
| `SELECTOR` | Variable-aware text input |
| `COLOR` | Color picker |

## Custom Ports

Override `setup_ports()` for custom port configuration:

```python
from casare_rpa.domain.value_objects.types import DataType

class VisualMyNode(VisualNode):
    __identifier__ = "casare_rpa.custom"
    NODE_NAME = "My Custom Node"
    NODE_CATEGORY = "custom"

    def setup_ports(self) -> None:
        """Setup custom ports with types."""
        # Execution ports (exec_in/exec_out added automatically by @node)

        # Typed input ports
        self.add_typed_input("data", DataType.DICT)
        self.add_typed_input("count", DataType.INTEGER)

        # Typed output ports
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("items", DataType.LIST)

        # Multi-connection exec output (for branching)
        self.add_exec_output("on_success")
        self.add_exec_output("on_error")
```

### Port Methods

| Method | Purpose |
|--------|---------|
| `add_typed_input(name, DataType)` | Add typed input port |
| `add_typed_output(name, DataType)` | Add typed output port |
| `add_exec_input(name)` | Add execution input port |
| `add_exec_output(name)` | Add execution output port |

### DataType Values

| DataType | Color | Shape |
|----------|-------|-------|
| `STRING` | Teal | Circle |
| `INTEGER` | Blue | Circle |
| `FLOAT` | Blue-green | Circle |
| `BOOLEAN` | Red | Diamond |
| `LIST` | Orange | Square |
| `DICT` | Purple | Hexagon |
| `ANY` | Gray | Circle |
| Exec (None) | White | Triangle |

## Custom Widgets

### When to Add Custom Widgets

Add custom widgets only when:

1. **File/Directory pickers** - Replace auto-generated text input
2. **Cascading dropdowns** - Dependent selections (e.g., Spreadsheet > Sheet)
3. **Complex custom UI** - Special interaction patterns

### The _replace_widget() Pattern

Use `_replace_widget()` to replace auto-generated widgets:

```python
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
)


def _replace_widget(node: VisualNode, widget) -> None:
    """Replace auto-generated widget with custom widget."""
    prop_name = widget._name
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)


class VisualReadFileNode(VisualNode):
    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read File"
    NODE_CATEGORY = "file"

    def __init__(self) -> None:
        super().__init__()
        # Replace auto-generated text input with file picker
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",  # Must match PropertyDef name
                label="File",
                file_filter="All Files (*.*)",
                placeholder="Select file...",
            ),
        )
```

### Avoiding "Property Already Exists" Error

**Never** manually add widgets for properties already in `@properties`:

```python
# Domain node has: @properties(PropertyDef("selector", ...))

# BAD - Causes error
class VisualMyNode(VisualNode):
    def __init__(self):
        super().__init__()
        self.add_text_input("selector", ...)  # ERROR!

# GOOD - Let schema handle it
class VisualMyNode(VisualNode):
    def __init__(self):
        super().__init__()
        # selector widget auto-generated
```

### Available Custom Widgets

```python
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,       # File selection
    NodeDirectoryPathWidget,  # Directory selection
)
```

## setup_widgets() Method

Override for additional widget setup after auto-generation:

```python
class VisualMyNode(VisualNode):
    __identifier__ = "casare_rpa.custom"
    NODE_NAME = "My Node"
    NODE_CATEGORY = "custom"

    def setup_widgets(self) -> None:
        """
        Setup custom widgets.

        Called BEFORE auto-generation, so custom widgets can override
        schema-based widgets.
        """
        # Add custom widget that will replace auto-generated one
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="Input File",
                file_filter="JSON Files (*.json)",
            ),
        )
```

## Theme Integration

Always use `THEME.*` constants for colors:

```python
from casare_rpa.presentation.canvas.ui.theme import THEME

# In custom widget styling
widget.setStyleSheet(f"""
    QWidget {{
        background-color: {THEME.BACKGROUND_PRIMARY};
        color: {THEME.TEXT_PRIMARY};
        border: 1px solid {THEME.BORDER_PRIMARY};
    }}
""")

# Type colors for badges/indicators
from casare_rpa.presentation.canvas.ui.theme import get_type_color, get_type_badge

color = get_type_color("string")   # Returns teal color
badge = get_type_badge("integer")  # Returns "#"
```

### Type Colors and Badges

| Type | Badge | Color Function |
|------|-------|----------------|
| String | `T` | `get_type_color("string")` |
| Integer | `#` | `get_type_color("integer")` |
| Float | `.` | `get_type_color("float")` |
| Boolean | `?` | `get_type_color("boolean")` |
| List | `[]` | `get_type_color("list")` |
| Dict | `{}` | `get_type_color("dict")` |
| Any | `*` | `get_type_color("any")` |
| None | `empty set` | `get_type_color("none")` |

## Signal Handling

### @Slot Decorator (Required)

All signal handlers must use `@Slot`:

```python
from PySide6.QtCore import Slot

class VisualMyNode(VisualNode):
    __identifier__ = "casare_rpa.custom"
    NODE_NAME = "My Node"
    NODE_CATEGORY = "custom"

    @Slot()
    def _on_button_clicked(self) -> None:
        """Handle button click."""
        pass

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """Handle text change."""
        pass

    @Slot(bool)
    def _on_toggled(self, checked: bool) -> None:
        """Handle toggle."""
        pass
```

### No Lambda Connections

Use named methods or `functools.partial`:

```python
from functools import partial

# BAD - Lambda
button.clicked.connect(lambda: self._do_thing())

# GOOD - Named method
@Slot()
def _on_button_clicked(self) -> None:
    self._do_thing()

button.clicked.connect(self._on_button_clicked)

# GOOD - functools.partial for parameters
button.clicked.connect(partial(self._handle_action, "param"))
```

## Collapsed State

Visual nodes start collapsed by default. Properties marked `essential=True` remain visible when collapsed:

```python
PropertyDef("selector", PropertyType.SELECTOR, essential=True),  # Visible when collapsed
PropertyDef("timeout", PropertyType.INTEGER, tab="advanced"),    # Hidden when collapsed
```

### Node Frames
Node Frames can also be collapsed. When collapsed, any connections from internal nodes to external nodes remain visible and attach to indicators on the frame's edge.

## Ports


### Visibility Levels

| Visibility | Behavior |
|------------|----------|
| `essential` | Always visible, even collapsed |
| `normal` | Visible when expanded |
| `advanced` | In "Advanced" collapsible section |
| `internal` | Never shown in UI |

## Category Colors

Nodes are automatically colored by category:

```python
# From node_icons.py
CATEGORY_COLORS = {
    "browser": QColor("#569cd6"),     # Blue
    "desktop": QColor("#c586c0"),     # Purple
    "file": QColor("#dcdcaa"),        # Yellow
    "data": QColor("#4ec9b0"),        # Cyan
    "control_flow": QColor("#ce9178"), # Orange
    "http": QColor("#9cdcfe"),        # Light blue
    "triggers": QColor("#6a9955"),    # Green
    ...
}
```

## Complete Example

```python
"""Visual node for ExcelReadNode with file picker."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import NodeFilePathWidget
from casare_rpa.domain.value_objects.types import DataType


def _replace_widget(node, widget):
    """Replace auto-generated widget with custom widget."""
    prop_name = widget._name
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)


class VisualExcelReadNode(VisualNode):
    """Visual representation of ExcelReadNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Read"
    NODE_CATEGORY = "office"

    def __init__(self) -> None:
        super().__init__()
        # Replace auto-generated text input with file picker
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="Excel File",
                file_filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
                placeholder="Select Excel file...",
            ),
        )

    def setup_ports(self) -> None:
        """Setup additional output ports."""
        # exec_in/exec_out added automatically
        self.add_typed_output("data", DataType.LIST)
        self.add_typed_output("headers", DataType.LIST)
        self.add_typed_output("row_count", DataType.INTEGER)
```

## File Structure

```
src/casare_rpa/presentation/canvas/visual_nodes/
├── __init__.py              # Exports all visual nodes
├── base_visual_node.py      # VisualNode base class
│
├── browser/
│   ├── __init__.py
│   └── nodes.py             # VisualClickNode, VisualTypeNode, etc.
│
├── file_operations/
│   ├── __init__.py
│   └── nodes.py             # VisualReadFileNode, VisualWriteFileNode, etc.
│
├── office_automation/
│   ├── __init__.py
│   └── nodes.py             # VisualExcelReadNode, etc.
│
└── triggers/
    ├── __init__.py
    ├── base.py              # VisualTriggerNode
    └── nodes.py             # VisualWebhookTriggerNode, etc.
```

## Next Steps

- [Creating Nodes](creating-nodes.md) - Domain node implementation
- [Creating Triggers](creating-triggers.md) - Trigger node development
- [Custom Widgets](custom-widgets.md) - Property widget development
