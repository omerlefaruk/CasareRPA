# UI Components Quick Start Guide

## Import Everything

```python
from casare_rpa.presentation.canvas.ui import (
    # Base Classes
    BaseWidget,
    BaseDockWidget,
    BaseDialog,
    # Panels
    PropertiesPanel,
    DebugPanel,
    VariablesPanel,
    MinimapPanel,
    # Toolbars
    MainToolbar,
    DebugToolbar,
    ZoomToolbar,
    # Dialogs
    NodePropertiesDialog,
    WorkflowSettingsDialog,
    PreferencesDialog,
    # Widgets
    VariableEditorWidget,
    OutputConsoleWidget,
    SearchWidget,
)
```

## Quick Examples

### 1. Add Properties Panel to Window

```python
# Create panel
properties_panel = PropertiesPanel(main_window)

# Connect signal
properties_panel.property_changed.connect(
    lambda node_id, prop_name, value:
        print(f"Node {node_id}: {prop_name} = {value}")
)

# Add to window
main_window.addDockWidget(Qt.RightDockWidgetArea, properties_panel)

# Update with node
properties_panel.set_node(selected_node)
```

### 2. Add Debug Panel

```python
# Create panel
debug_panel = DebugPanel(main_window)

# Connect navigation
debug_panel.navigate_to_node.connect(
    lambda node_id: graph_view.center_on_node(node_id)
)

# Add to window
main_window.addDockWidget(Qt.BottomDockWidgetArea, debug_panel)

# Add logs
debug_panel.add_log("Info", "Workflow started")
debug_panel.add_log("Error", "Node failed", "node123", "Click Button")
debug_panel.add_console_output(">> Execution output...")
```

### 3. Add Variables Panel

```python
# Create panel
variables_panel = VariablesPanel(main_window)

# Connect signals
variables_panel.variable_added.connect(on_variable_added)
variables_panel.variable_changed.connect(on_variable_changed)

# Add to window
main_window.addDockWidget(Qt.RightDockWidgetArea, variables_panel)

# Add variables
variables_panel.add_variable("counter", "Integer", 0, "Workflow")
variables_panel.add_variable("username", "String", "", "Global")

# Switch to runtime mode
variables_panel.set_runtime_mode(True)
variables_panel.update_variable_value("counter", 5)
```

### 4. Add Main Toolbar

```python
# Create toolbar
main_toolbar = MainToolbar(main_window)

# Connect actions
main_toolbar.run_requested.connect(workflow_runner.run)
main_toolbar.save_requested.connect(workflow_manager.save)
main_toolbar.undo_requested.connect(undo_stack.undo)

# Add to window
main_window.addToolBar(Qt.TopToolBarArea, main_toolbar)

# Update state
main_toolbar.set_execution_state(is_running=True, is_paused=False)
main_toolbar.set_undo_enabled(undo_stack.canUndo())
```

### 5. Add Debug Toolbar

```python
# Create toolbar
debug_toolbar = DebugToolbar(main_window)

# Connect signals
debug_toolbar.debug_mode_toggled.connect(
    lambda enabled: workflow_runner.set_debug_mode(enabled)
)
debug_toolbar.step_requested.connect(workflow_runner.step_next)

# Add to window
main_window.addToolBar(Qt.TopToolBarArea, debug_toolbar)

# Update state
debug_toolbar.set_execution_state(is_running=True)
```

### 6. Add Zoom Toolbar

```python
# Create toolbar
zoom_toolbar = ZoomToolbar(main_window)

# Connect signals
zoom_toolbar.zoom_changed.connect(
    lambda zoom: graph_view.setZoom(zoom)
)
zoom_toolbar.zoom_fit_requested.connect(graph_view.fitInView)

# Add to window (status bar)
main_window.statusBar().addPermanentWidget(zoom_toolbar)

# Set zoom
zoom_toolbar.set_zoom(1.5)  # 150%
```

### 7. Show Node Properties Dialog

```python
# Show dialog
dialog = NodePropertiesDialog(
    node_id="node123",
    node_type="Click",
    properties={"name": "Click Button", "timeout": 30},
    parent=main_window
)

# Connect signal
dialog.properties_changed.connect(
    lambda props: node_manager.update_node_properties("node123", props)
)

# Execute
if dialog.exec() == QDialog.Accepted:
    updated_props = dialog.get_properties()
    print(f"Updated properties: {updated_props}")
```

### 8. Show Workflow Settings Dialog

```python
# Show dialog
dialog = WorkflowSettingsDialog(
    settings={
        "name": "My Workflow",
        "author": "John Doe",
        "global_timeout": 3600,
    },
    parent=main_window
)

# Connect signal
dialog.settings_changed.connect(
    lambda settings: workflow_manager.update_settings(settings)
)

# Execute
dialog.exec()
```

### 9. Show Preferences Dialog

```python
# Show dialog
dialog = PreferencesDialog(
    preferences={
        "theme": "Dark",
        "autosave_enabled": True,
        "autosave_interval": 5,
    },
    parent=main_window
)

# Connect signal
dialog.preferences_changed.connect(
    lambda prefs: app.apply_preferences(prefs)
)

# Execute
dialog.exec()
```

### 10. Use Variable Editor Widget

```python
# Create widget
editor = VariableEditorWidget("count", "Integer", 0, parent)

# Connect signal
editor.variable_changed.connect(
    lambda name, type, value: print(f"{name} ({type}) = {value}")
)

# Add to layout
layout.addWidget(editor)

# Get variable data
var_data = editor.get_variable()
# {'name': 'count', 'type': 'Integer', 'value': 0}

# Connect remove button
editor.get_remove_button().clicked.connect(
    lambda: layout.removeWidget(editor)
)
```

### 11. Use Output Console Widget

```python
# Create widget
console = OutputConsoleWidget(parent)

# Add to layout
layout.addWidget(console)

# Add messages
console.append_info("Workflow started")
console.append_warning("Node execution slow")
console.append_error("Node failed: timeout")
console.append_success("Workflow completed")

# Configure
console.set_auto_scroll(True)
console.set_show_timestamps(True)
console.set_max_lines(500)

# Get text
all_output = console.get_text()
```

### 12. Use Search Widget

```python
# Create widget
search = SearchWidget("Search nodes...", parent)

# Set items
search.set_items([
    ("Click Node", node1_data),
    ("Type Node", node2_data),
    ("Wait Node", node3_data),
])

# Connect signal
search.item_selected.connect(
    lambda text, data: print(f"Selected: {text}, Data: {data}")
)

# Add to layout
layout.addWidget(search)

# Custom fuzzy match
def fuzzy_match(query, text):
    # Custom matching logic
    return all(c in text.lower() for c in query.lower())

search.set_fuzzy_match_function(fuzzy_match)

# Focus search
search.focus_search()
```

## Complete Integration Example

```python
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt
from casare_rpa.presentation.canvas.ui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CasareRPA Canvas")
        self.setGeometry(100, 100, 1400, 900)

        # Create all components
        self._create_panels()
        self._create_toolbars()
        self._connect_signals()

    def _create_panels(self):
        # Properties Panel (Right)
        self.properties_panel = PropertiesPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel)

        # Debug Panel (Bottom)
        self.debug_panel = DebugPanel(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.debug_panel)

        # Variables Panel (Right, tabbed with Properties)
        self.variables_panel = VariablesPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.variables_panel)
        self.tabifyDockWidget(self.properties_panel, self.variables_panel)

        # Minimap (Bottom-right corner as overlay)
        self.minimap_panel = MinimapPanel(self)
        # Position as overlay in corner

    def _create_toolbars(self):
        # Main Toolbar (Top)
        self.main_toolbar = MainToolbar(self)
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)

        # Debug Toolbar (Top)
        self.debug_toolbar = DebugToolbar(self)
        self.addToolBar(Qt.TopToolBarArea, self.debug_toolbar)

        # Zoom Toolbar (Status Bar)
        self.zoom_toolbar = ZoomToolbar(self)
        self.statusBar().addPermanentWidget(self.zoom_toolbar)

    def _connect_signals(self):
        # Main toolbar → Workflow manager
        self.main_toolbar.run_requested.connect(self.run_workflow)
        self.main_toolbar.save_requested.connect(self.save_workflow)
        self.main_toolbar.undo_requested.connect(self.undo)

        # Debug toolbar → Workflow runner
        self.debug_toolbar.debug_mode_toggled.connect(self.set_debug_mode)
        self.debug_toolbar.step_requested.connect(self.step_next)

        # Properties panel → Node manager
        self.properties_panel.property_changed.connect(self.update_node_property)

        # Variables panel → Workflow state
        self.variables_panel.variable_changed.connect(self.update_variable)

        # Debug panel → Graph view
        self.debug_panel.navigate_to_node.connect(self.navigate_to_node)

        # Zoom toolbar → Graph view
        self.zoom_toolbar.zoom_changed.connect(self.set_graph_zoom)

    def run_workflow(self):
        self.debug_panel.add_log("Info", "Workflow started")
        # ... workflow execution logic

    def save_workflow(self):
        self.debug_panel.add_log("Info", "Workflow saved")
        # ... save logic

    # ... other handler methods


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
```

## Creating Custom Components

### Custom Panel

```python
from casare_rpa.presentation.canvas.ui import BaseDockWidget
from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal

class CustomPanel(BaseDockWidget):
    # Custom signals
    action_triggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Custom Panel", parent)

    def setup_ui(self):
        """Setup custom UI."""
        from PySide6.QtWidgets import QWidget

        container = QWidget()
        layout = QVBoxLayout(container)

        # Add widgets
        self.label = QLabel("Custom Panel Content")
        layout.addWidget(self.label)

        self.button = QPushButton("Action")
        layout.addWidget(self.button)

        self.setWidget(container)

    def connect_signals(self):
        """Connect internal signals."""
        self.button.clicked.connect(self._on_button_clicked)

    def _on_button_clicked(self):
        """Handle button click."""
        self.action_triggered.emit("button_clicked")
```

### Custom Widget

```python
from casare_rpa.presentation.canvas.ui import BaseWidget
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Signal

class CustomWidget(BaseWidget):
    # Custom signals
    value_submitted = Signal(str)

    def setup_ui(self):
        """Setup UI."""
        layout = QHBoxLayout(self)

        self.input = QLineEdit()
        layout.addWidget(self.input)

        self.submit_btn = QPushButton("Submit")
        layout.addWidget(self.submit_btn)

    def connect_signals(self):
        """Connect signals."""
        self.submit_btn.clicked.connect(self._on_submit)
        self.input.returnPressed.connect(self._on_submit)

    def _on_submit(self):
        """Handle submit."""
        value = self.input.text()
        if value:
            self.value_submitted.emit(value)
            self.input.clear()
```

## Common Patterns

### 1. Update Component from External State

```python
# When external state changes, update UI
def on_workflow_loaded(workflow_data):
    # Update variables panel
    variables_panel.clear_variables()
    for var_name, var_data in workflow_data.get("variables", {}).items():
        variables_panel.add_variable(
            var_name,
            var_data["type"],
            var_data["default"],
            var_data.get("scope", "Workflow")
        )
```

### 2. Batch Updates Without Signals

```python
# Prevent signals during batch updates
properties_panel.blockSignals(True)
for prop_name, prop_value in properties.items():
    properties_panel._update_property(prop_name, prop_value)
properties_panel.blockSignals(False)
```

### 3. State Synchronization

```python
# Sync toolbar state with execution state
def on_execution_started():
    main_toolbar.set_execution_state(is_running=True, is_paused=False)
    debug_toolbar.set_execution_state(is_running=True)

def on_execution_paused():
    main_toolbar.set_execution_state(is_running=True, is_paused=True)

def on_execution_stopped():
    main_toolbar.set_execution_state(is_running=False, is_paused=False)
    debug_toolbar.set_execution_state(is_running=False)
```

### 4. Dialog Result Handling

```python
# Show dialog and handle result
dialog = WorkflowSettingsDialog(current_settings, main_window)

# Option 1: Using exec() return value
if dialog.exec() == QDialog.Accepted:
    new_settings = dialog.get_settings()
    apply_settings(new_settings)

# Option 2: Using signal
dialog.settings_changed.connect(apply_settings)
dialog.exec()
```

## Troubleshooting

### Component Not Showing
```python
# Check if initialized
assert panel.is_initialized()

# Check if visible
panel.setVisible(True)

# Check parent
print(panel.parent())
```

### Signals Not Working
```python
# Check connection
assert panel.property_changed.isSignalConnected(slot)

# Check if blocked
assert not panel.signalsBlocked()

# Enable logging
from loguru import logger
logger.enable("casare_rpa.presentation.canvas.ui")
```

### Styling Issues
```python
# Reapply stylesheet
panel.apply_stylesheet()

# Check current stylesheet
print(panel.styleSheet())

# Override stylesheet
panel.setStyleSheet(panel.styleSheet() + """
    /* Custom overrides */
""")
```

---

**Quick Start Status**: ✅ READY
**Last Updated**: November 27, 2025
