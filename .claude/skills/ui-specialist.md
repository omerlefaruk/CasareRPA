---
skill: ui-specialist
description: PySide6 UI development for CasareRPA Canvas with dark theme, signal/slot patterns, and MCP-first research.
---

## MCP-First UI Development

**Always use MCP servers in this order:**

1. **codebase** - Find existing UI patterns
   ```python
   search_codebase("custom widget creation", top_k=10)
   search_codebase("property panel widget", top_k=10)
   ```

2. **filesystem** - Read current theme/constants
   ```python
   read_file("src/casare_rpa/presentation/canvas/theme.py")
   read_file("src/casare_rpa/presentation/canvas/ui/theme.py")
   ```

3. **sequential-thinking** - Plan UI component design
   ```python
   think_step_by_step("""
   Design UI component:
   1. Identify requirements
   2. Find similar components in codebase
   3. Plan widget hierarchy
   4. Define signals/slots
   5. Apply theme constants
   """)
   ```

4. **exa** - Research PySide6 patterns
   ```python
   websearch("PySide6 custom widget dark theme 2025", numResults=5)
   websearch("PySide6 signal slot best practices", numResults=3)
   ```

5. **ref** - PySide6 documentation lookup
   ```python
   search_documentation("QLineEdit", library="PySide6")
   search_documentation("QWidget", library="PySide6")
   ```

6. **git** - Check widget usage across codebase
   ```python
   git_log("-20", "--all", "widget")
   git_diff("HEAD~10..HEAD", "**/widgets/*.py")
   ```

## Theme System

**THEME Constants (MCP-Based Discovery):**
```python
# Step 1: Read theme file
# Use filesystem MCP
read_file("src/casare_rpa/presentation/canvas/ui/theme.py")

# Expected constants:
THEME = {
    'background': '#2d2d2d',
    'surface': '#383838',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'accent': '#0078d4',
    'border': '#444444',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
}
```

**Headless Mode Support:**
```python
import os

# Check for headless environment
IS_HEADLESS = os.environ.get('QT_QPA_PLATFORM') == 'offscreen'

if IS_HEADLESS:
    # Skip expensive visual effects
    # Disable animations
    # Use simple styles
```

## Custom Widget Templates

### Property Input Widget

**MCP-Based Discovery:**
```python
# Step 1: Find existing property widgets
search_codebase("NodeBaseWidget", top_k=10)

# Step 2: Read similar widget
read_file("src/casare_rpa/presentation/canvas/graph/node_widgets.py")

# Step 3: Research widget patterns
websearch("PySide6 property input widget custom", numResults=5)
```

**Template:**
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal, QObject, Slot
from loguru import logger
from ..ui.theme import THEME

class CustomPropertyWidget(QWidget):
    """Custom property input widget with dark theme."""

    value_changed = Signal(object)  # Emitted when value changes

    def __init__(self, property_name: str, property_type: str = "string", parent=None):
        super().__init__(parent)
        self._setup_ui(property_name)

    def _setup_ui(self, property_name: str) -> None:
        """Setup widget UI with dark theme."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Label
        self.label = QLabel(f"{property_name}:")
        self.label.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.label)

        # Input
        self.input = QLineEdit()
        self._apply_theme()
        self.input.textChanged.connect(self.value_changed.emit)
        layout.addWidget(self.input)

    def _apply_theme(self) -> None:
        """Apply dark theme to input."""
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['surface']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME['accent']};
            }}
        """)

    @Slot(object)
    def set_value(self, value: object) -> None:
        """Slot to set widget value."""
        if isinstance(value, str):
            self.input.setText(value)
        logger.debug(f"Set value: {value}")

    def get_value(self) -> object:
        """Get current value."""
        return self.input.text()
```

### File Path Widget

**MCP-Based Discovery:**
```python
# Find existing path widgets
search_codebase("FilePathWidget|DirectoryPathWidget", top_k=10)
```

**Template:**
```python
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Signal, Slot, QStandardPaths
from ..ui.theme import THEME
from pathlib import Path
import subprocess

class FilePathWidget(QWidget):
    """File path picker widget with browse button."""

    path_changed = Signal(str)

    def __init__(self, file_filter: str = "All Files (*.*)", parent=None):
        super().__init__(parent)
        self._setup_ui(file_filter)

    def _setup_ui(self, file_filter: str) -> None:
        """Setup file picker UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Path input
        self.path_edit = QLineEdit()
        self._apply_theme()
        layout.addWidget(self.path_edit, stretch=1)

        # Browse button
        self.browse_btn = QPushButton("Browse")
        self._apply_button_theme()
        self.browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(self.browse_btn)

    def _apply_theme(self) -> None:
        """Apply dark theme to components."""
        self.path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['surface']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent']};
                color: {THEME['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #106ebe8;
            }}
            QPushButton:pressed {{
                background-color: #005a9e;
            }}
        """)

    @Slot()
    def _browse_file(self) -> None:
        """Open file dialog to browse."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
            self.file_filter
        )

        if file_path:
            self.path_edit.setText(file_path)
            self.path_changed.emit(file_path)

    @Slot(str)
    def set_value(self, value: str) -> None:
        """Set file path."""
        self.path_edit.setText(value)

    def get_value(self) -> str:
        """Get current path."""
        return self.path_edit.text()
```

## Signal/Slot Best Practices

**Rule 1: All Slots Must Be Decorated**
```python
from PySide6.QtCore import Slot

# CORRECT
@Slot()
def handle_click(self):
    pass

@Slot(str)
def handle_text_change(self, text: str):
    pass

@Slot(int, float)
def handle_value(self, a: int, b: float):
    pass

# WRONG - Missing decorator
def handle_click(self):
    pass
```

**Rule 2: Use functools.partial for Captures**
```python
from functools import partial

# CORRECT - Using partial for captures
button.clicked.connect(partial(self._handle_click, node_id="node_1"))

# WRONG - Lambda (problematic in Qt)
button.clicked.connect(lambda: self._handle_click("node_1"))
```

**Rule 3: Queued Connections Cross-Thread**
```python
from PySide6.QtCore import Qt

# For cross-thread connections
worker.finished.connect(self._on_worker_finished, Qt.ConnectionType.QueuedConnection)
```

## Panel Component Templates

### Properties Panel

**MCP-Based Discovery:**
```python
# Search for panel implementations
search_codebase("class.*Panel", top_k=10)
```

**Template:**
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PySide6.QtCore import Signal
from ..ui.theme import THEME

class PropertiesPanel(QWidget):
    """Panel for editing node properties."""

    properties_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._property_widgets = {}

    def _setup_ui(self) -> None:
        """Setup properties panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for properties
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {THEME['background']};
                border: none;
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(8)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def update_properties(self, node: object) -> None:
        """Update panel with node properties."""
        # Clear existing widgets
        self._clear_properties()

        # Add new property widgets
        for prop_name, prop_value in node.get_properties().items():
            widget = self._create_property_widget(prop_name, prop_value)
            self._property_widgets[prop_name] = widget
            # Add to layout

    def _clear_properties(self) -> None:
        """Clear all property widgets."""
        for widget in self._property_widgets.values():
            widget.deleteLater()
        self._property_widgets.clear()

    def _apply_panel_theme(self) -> None:
        """Apply dark theme to panel."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME['background']};
                color: {THEME['text_primary']};
            }}
        """)
```

## Visual Node Wrapper Patterns

**MCP-Based Discovery:**
```python
# Find existing visual node patterns
search_codebase("class VisualNode", top_k=10)
```

**Template:**
```python
from NodeGraphQt import BaseNode
from PySide6.QtCore import Slot, Signal
from PySide6.QtGui import QColor
from casare_rpa.nodes.{category}.{node_name} import {NodeName}Node
from ..ui.theme import THEME

class Visual{NodeName}Node(BaseNode):
    """Visual wrapper for {NodeName}Node."""

    # Optional: Custom signals
    properties_updated = Signal()

    def __init__(self):
        super().__init__()
        self._setup_node()

    def _setup_node(self) -> None:
        """Setup visual node."""
        self.logic_node = {NodeName}Node()

        # Set node appearance
        self.set_color(QColor(85, 107, 47))  # Category color
        self.set_name("{Node Display Name}")

        # Add visual ports
        for input_port in self.logic_node.inputs.values():
            self.add_input(input_port.name)

        for output_port in self.logic_node.outputs.values():
            self.add_output(output_port.name)

    def _apply_node_theme(self) -> None:
        """Apply dark theme to node."""
        # Node background
        self.set_color(QColor(*THEME['node_bg']))

    @Slot(object)
    def update_from_logic(self, properties: dict) -> None:
        """Update visual node from logic node properties."""
        for prop_name, prop_value in properties.items():
            self.set_property(prop_name, prop_value)
```

## UI Best Practices

1. **Always use THEME constants** - Never hardcode colors
2. **All slots must use @Slot decorator** - Required for Qt
3. **Use functools.partial for captures** - Avoid lambda in signals
4. **Headless mode support** - Skip expensive effects when QT_QPA_PLATFORM=offscreen
5. **Tight margins for compact nodes** - `setContentsMargins(4, 4, 4, 4)`
6. **Emit signals on value changes** - Immediate feedback
7. **Proper widget cleanup** - Use `deleteLater()` in Qt lifecycle
8. **Async UI operations with qasync** - Run async code in Qt event loop

## Common UI Patterns

| Pattern | MCP Search | Implementation |
|----------|------------|---------------|
| Node color by category | `search_codebase("set_color", top_k=10)` | RGB constants per category |
| Property panel | `search_codebase("PropertiesPanel", top_k=5)` | ScrollArea with form layout |
| Dark mode toggle | `search_codebase("theme", top_k=10)` | Palette switching |
| Dialog styles | `search_codebase("dialog", top_k=10)` | Use `dialog_styles.py` helpers |

## Usage

Invoke this skill when:
- Creating new UI widgets
- Designing node property panels
- Updating theme system
- Fixing signal/slot issues
- Making UI headless-compatible

```python
Task(subagent_type="ui", prompt="""
Use ui-specialist skill with MCP-first approach:

Task: Create custom widget for IfCondition node property editor
Requirements:
- Boolean toggle (checkbox)
- True/False path editors (line edit)
- Dark theme styling
- Signal emission on change

MCP Workflow:
1. codebase: Search for existing condition widgets
2. filesystem: Read theme.py for constants
3. exa: Research PySide6 custom checkbox patterns
4. ref: Look up QCheckBox documentation
5. sequential-thinking: Plan widget structure

Apply CasareRPA UI standards:
- Use THEME constants
- @Slot decorator on all slots
- functools.partial for captures
- Headless mode support
""")
```
