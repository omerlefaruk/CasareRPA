# Custom Widgets

This guide covers creating custom property widgets for CasareRPA visual nodes, including file pickers, variable integration, and signal handling.

## Widget System Overview

CasareRPA uses NodeGraphQt for canvas rendering, which provides a widget system for node properties:

```
@properties decorator
        |
        v
+------------------+
| Auto-generation  |  <-- Creates widgets from PropertyDef
+------------------+
        |
        v
+------------------+
| NodeBaseWidget   |  <-- NodeGraphQt base widget
+------------------+
        |
        v
+------------------+
| Custom Widget    |  <-- Your custom implementation
+------------------+
```

## Auto-Generated Widgets

The `@properties` decorator automatically generates widgets based on `PropertyType`:

| PropertyType | Widget | Features |
|--------------|--------|----------|
| `STRING` | `VariableAwareLineEdit` | `{x}` button, expression support |
| `TEXT` | Multi-line editor | Larger text area |
| `INTEGER` | `QSpinBox` | Up/down arrows |
| `FLOAT` | `QDoubleSpinBox` | Decimal input |
| `BOOLEAN` | `QCheckBox` | Toggle |
| `CHOICE` | `QComboBox` | Dropdown |
| `FILE_PATH` | Text input | **Replace with `NodeFilePathWidget`** |
| `DIRECTORY_PATH` | Text input | **Replace with `NodeDirectoryPathWidget`** |
| `JSON` | JSON editor | Syntax highlighting |
| `CODE` | Code editor | Language-specific highlighting |
| `COLOR` | Color picker | Visual color selection |

## Key Imports

```python
# File path widgets
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
)

# Variable picker components
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableInfo,
    VariableProvider,
    VariableButton,
    VariablePickerPopup,
    VariableAwareLineEdit,
)

# Theme colors
from casare_rpa.presentation.canvas.ui.theme import (
    THEME,
    get_type_color,
    get_type_badge,
    TYPE_COLORS,
    TYPE_BADGES,
)
```

## File Path Widgets

### NodeFilePathWidget

For file selection with browse button:

```python
from casare_rpa.presentation.canvas.graph.node_widgets import NodeFilePathWidget

widget = NodeFilePathWidget(
    name="file_path",                               # Must match PropertyDef name
    label="Input File",                             # Display label
    file_filter="Excel Files (*.xlsx);;All (*.*)", # File type filter
    placeholder="Select file...",                   # Placeholder text
    text="",                                        # Initial value
)
```

**Features:**
- Browse button opens file dialog
- Variable picker (`{x}` button) for dynamic paths
- Blue button color (#0078d4)

### NodeDirectoryPathWidget

For directory selection:

```python
from casare_rpa.presentation.canvas.graph.node_widgets import NodeDirectoryPathWidget

widget = NodeDirectoryPathWidget(
    name="output_dir",
    label="Output Folder",
    placeholder="Select folder...",
    text="",
)
```

**Features:**
- Browse button opens directory dialog
- Variable picker for dynamic paths
- Orange button color (#d97706) to distinguish from file picker

### Using in Visual Nodes

```python
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import NodeFilePathWidget


def _replace_widget(node, widget):
    """Replace auto-generated widget with custom widget."""
    prop_name = widget._name
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)


class VisualReadCSVNode(VisualNode):
    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read CSV"
    NODE_CATEGORY = "file"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="CSV File",
                file_filter="CSV Files (*.csv);;All Files (*.*)",
                placeholder="Select CSV file...",
            ),
        )
```

## The _replace_widget() Pattern

### Why Replace Instead of Add?

The `@properties` decorator generates widgets **before** your `__init__` runs. Adding a widget with the same name causes `NodePropertyError: "property already exists"`.

### The Pattern

```python
def _replace_widget(node: VisualNode, widget) -> None:
    """
    Replace auto-generated widget with custom widget.

    Args:
        node: The visual node instance
        widget: The custom widget to use
    """
    prop_name = widget._name
    # Remove from model properties
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        # Remove from widget cache
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]
    # Add custom widget
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)
```

### Decision Tree

```
Does PropertyDef exist for this property?
    |
    +-- YES --> Use _replace_widget()
    |
    +-- NO --> Use add_custom_widget() directly
```

## Variable Picker Integration

### VariableAwareLineEdit

Text input with variable picker button:

```python
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableAwareLineEdit,
    VariableProvider,
)

# Create line edit
line_edit = VariableAwareLineEdit()
line_edit.setText("Initial value")
line_edit.setPlaceholderText("Enter value or {{variable}}")

# Connect to variable provider
line_edit.set_provider(VariableProvider.get_instance())
```

### Variable Syntax

Users can insert variables using:

| Syntax | Description | Example |
|--------|-------------|---------|
| `{{varName}}` | Simple variable | `{{username}}` |
| `{{data.field}}` | Nested dict access | `{{response.data.id}}` |
| `{{list[0]}}` | List index access | `{{items[0]}}` |
| `{{$currentDate}}` | System variable | `{{$timestamp}}` |

### System Variables

| Variable | Value |
|----------|-------|
| `$currentDate` | Current date (YYYY-MM-DD) |
| `$currentTime` | Current time (HH:MM:SS) |
| `$currentDateTime` | ISO datetime |
| `$timestamp` | Unix timestamp |

### Variable Sources

1. **Workflow variables** - From Variables tab
2. **Upstream node outputs** - From connected nodes
3. **System variables** - Built-in values

## Signal Handling (Critical)

### The setText() Problem

Qt's `setText()` does NOT emit `editingFinished` signal. You must manually sync values:

```python
def on_browse():
    path, _ = QFileDialog.getOpenFileName(...)
    if path:
        line_edit.setText(path)
        # CRITICAL: Manual sync after setText()
        widget.on_value_changed()
```

### @Slot Decorator (Required)

All signal handlers must use `@Slot`:

```python
from PySide6.QtCore import Slot

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
    """Handle toggle state change."""
    pass
```

### No Lambda Connections

Use `functools.partial` instead of lambdas:

```python
from functools import partial

# BAD - Lambda
button.clicked.connect(lambda: self._do_thing())

# GOOD - functools.partial
button.clicked.connect(partial(self._handle_action, "param"))

@Slot()
def _handle_action(self, param: str, *args) -> None:
    """Handle action with parameter."""
    pass
```

## Creating Custom Widgets

### Factory Function Pattern

Create widgets using factory functions:

```python
def create_my_custom_widget(
    name: str,
    label: str,
    options: list,
) -> NodeBaseWidget:
    """
    Factory function for custom widget.

    Args:
        name: Property name
        label: Display label
        options: List of options

    Returns:
        NodeBaseWidget with custom implementation
    """
    from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox

    # Create container
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    # Add custom widgets
    combo = QComboBox()
    combo.addItems(options)
    layout.addWidget(combo)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)

    # Override get_value/set_value
    def get_value():
        return combo.currentText()

    def set_value(value):
        index = combo.findText(str(value))
        if index >= 0:
            combo.setCurrentIndex(index)

    widget.get_value = get_value
    widget.set_value = set_value

    # Connect signals
    combo.currentTextChanged.connect(widget.on_value_changed)

    return widget
```

### Class-Based Pattern

For more complex widgets:

```python
class MyCustomWidget:
    """
    Custom widget for special functionality.

    Usage:
        widget = MyCustomWidget(name="my_prop", label="My Property")
        self.add_custom_widget(widget)
    """

    def __new__(cls, name: str, label: str, **kwargs):
        """Create widget instance."""
        return cls._create_widget(name, label, **kwargs)

    @classmethod
    def _create_widget(cls, name: str, label: str, **kwargs):
        """Internal widget creation."""
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        # Create and configure widget...
        widget = NodeBaseWidget(parent=None, name=name, label=label)

        # ... setup logic ...

        return widget
```

## Theme Integration

### Using THEME Constants

Never hardcode colors:

```python
from casare_rpa.presentation.canvas.ui.theme import THEME

# Style a widget
widget.setStyleSheet(f"""
    QWidget {{
        background-color: {THEME.BACKGROUND_PRIMARY};
        color: {THEME.TEXT_PRIMARY};
        border: 1px solid {THEME.BORDER_PRIMARY};
    }}
    QWidget:focus {{
        border: 1px solid {THEME.ACCENT_PRIMARY};
    }}
""")
```

### Type Colors and Badges

```python
from casare_rpa.presentation.canvas.ui.theme import get_type_color, get_type_badge

# Get color for data type
string_color = get_type_color("string")   # Teal
integer_color = get_type_color("integer") # Blue

# Get badge character
string_badge = get_type_badge("string")   # "T"
integer_badge = get_type_badge("integer") # "#"
```

### Wire Colors

```python
from casare_rpa.presentation.canvas.ui.theme import get_wire_color

exec_color = get_wire_color("exec")     # White (execution flow)
string_color = get_wire_color("string") # Teal
list_color = get_wire_color("list")     # Orange
dict_color = get_wire_color("dict")     # Purple
```

## Widget Categories Using File Pickers

| Category | Widgets Needed |
|----------|----------------|
| file_operations | `NodeFilePathWidget`, `NodeDirectoryPathWidget` |
| desktop_automation | `NodeFilePathWidget` (screenshots, apps) |
| browser | `NodeFilePathWidget` (screenshots) |
| office_automation | `NodeFilePathWidget` (Excel, Word) |

## Complete Example: Cascading Dropdowns

```python
"""Cascading dropdown widget for Google Sheets selection."""

from functools import partial
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel

from casare_rpa.presentation.canvas.ui.theme import THEME


def create_sheets_selector(name: str, label: str):
    """
    Create cascading Spreadsheet > Sheet selector.

    Returns:
        NodeBaseWidget with two cascading dropdowns
    """
    from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

    # Container
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Spreadsheet selector
    spreadsheet_label = QLabel("Spreadsheet")
    spreadsheet_label.setStyleSheet(f"color: {THEME.TEXT_SECONDARY};")
    layout.addWidget(spreadsheet_label)

    spreadsheet_combo = QComboBox()
    spreadsheet_combo.setPlaceholderText("Select spreadsheet...")
    layout.addWidget(spreadsheet_combo)

    # Sheet selector
    sheet_label = QLabel("Sheet")
    sheet_label.setStyleSheet(f"color: {THEME.TEXT_SECONDARY};")
    layout.addWidget(sheet_label)

    sheet_combo = QComboBox()
    sheet_combo.setPlaceholderText("Select sheet...")
    sheet_combo.setEnabled(False)  # Disabled until spreadsheet selected
    layout.addWidget(sheet_combo)

    # Create widget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)

    # Store references
    widget._spreadsheet_combo = spreadsheet_combo
    widget._sheet_combo = sheet_combo

    @Slot(str)
    def on_spreadsheet_changed(spreadsheet_id: str) -> None:
        """Load sheets when spreadsheet changes."""
        if spreadsheet_id:
            sheet_combo.setEnabled(True)
            # Load sheets for spreadsheet_id...
            # sheet_combo.clear()
            # sheet_combo.addItems(sheets)
        else:
            sheet_combo.setEnabled(False)
            sheet_combo.clear()
        widget.on_value_changed()

    spreadsheet_combo.currentTextChanged.connect(on_spreadsheet_changed)
    sheet_combo.currentTextChanged.connect(widget.on_value_changed)

    # Value accessors
    def get_value():
        return {
            "spreadsheet_id": spreadsheet_combo.currentData() or "",
            "sheet_name": sheet_combo.currentText() or "",
        }

    def set_value(value):
        if isinstance(value, dict):
            # Set spreadsheet
            spreadsheet_id = value.get("spreadsheet_id", "")
            idx = spreadsheet_combo.findData(spreadsheet_id)
            if idx >= 0:
                spreadsheet_combo.setCurrentIndex(idx)
            # Set sheet
            sheet_name = value.get("sheet_name", "")
            idx = sheet_combo.findText(sheet_name)
            if idx >= 0:
                sheet_combo.setCurrentIndex(idx)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget
```

## Best Practices

1. **Always use @Slot decorator** - All signal handlers
2. **Never use lambdas in connections** - Use `functools.partial`
3. **Call on_value_changed() after setText()** - Manual sync required
4. **Use _replace_widget() for schema properties** - Avoid duplicate errors
5. **Use THEME constants** - No hardcoded colors
6. **Set minimum sizes** - Ensure visibility in canvas
7. **Connect editingFinished** - Not textChanged (performance)

## Next Steps

- [Creating Nodes](creating-nodes.md) - Domain node implementation
- [Creating Triggers](creating-triggers.md) - Trigger node development
- [Visual Nodes](visual-nodes.md) - Visual node configuration
