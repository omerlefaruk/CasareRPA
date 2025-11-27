# UI Components Module

**Week 3 Day 3: UI Components Extraction**

This module provides reusable, well-structured UI components for the CasareRPA Canvas application following Clean Architecture principles.

## Overview

All 13+ UI components have been extracted from scattered locations into organized, reusable modules with:
- Consistent design patterns
- Comprehensive signal/slot connections
- Dark theme styling
- Type hints and docstrings
- Full logging integration

## Architecture

```
ui/
├── base_widget.py           # Base classes for all components
├── panels/                  # Dockable panels
│   ├── properties_panel.py
│   ├── debug_panel.py
│   ├── variables_panel.py
│   └── minimap_panel.py
├── toolbars/                # Action toolbars
│   ├── main_toolbar.py
│   ├── debug_toolbar.py
│   └── zoom_toolbar.py
├── dialogs/                 # Modal dialogs
│   ├── node_properties_dialog.py
│   ├── workflow_settings_dialog.py
│   └── preferences_dialog.py
└── widgets/                 # Reusable widgets
    ├── variable_editor_widget.py
    ├── output_console_widget.py
    └── search_widget.py
```

## Component Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                       BaseWidget                            │
│  - Common Qt patterns                                       │
│  - Stylesheet management                                    │
│  - Signal/slot conventions                                  │
│  - State management                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┬────────────────┐
                │             │             │                │
          ┌─────▼─────┐ ┌────▼────┐  ┌────▼─────┐  ┌───────▼────────┐
          │BaseDock   │ │BaseDialog│  │Panels    │  │Toolbars/Widgets│
          │Widget     │ │          │  │          │  │                │
          └───────────┘ └──────────┘  └──────────┘  └────────────────┘
```

## Component List (13 Components)

### 1. Base Classes (3)

#### BaseWidget
- **Location**: `base_widget.py`
- **Purpose**: Abstract base for all UI components
- **Signals**:
  - `value_changed(object)`: Component value changed
  - `state_changed(str, object)`: Component state changed
- **Key Features**:
  - Automatic stylesheet application
  - State management
  - Initialization verification
  - Logging integration

#### BaseDockWidget
- **Location**: `base_widget.py`
- **Purpose**: Base for dockable panels
- **Signals**:
  - `visibility_changed(bool)`: Dock visibility changed
  - Inherits all from BaseWidget
- **Key Features**:
  - Title management
  - Position tracking

#### BaseDialog
- **Location**: `base_widget.py`
- **Purpose**: Base for modal dialogs
- **Signals**:
  - `accepted()`: Dialog accepted
  - `rejected()`: Dialog rejected
  - Inherits all from BaseWidget
- **Key Features**:
  - Validation support
  - Result handling

### 2. Panels (4)

#### PropertiesPanel
- **Location**: `panels/properties_panel.py`
- **Purpose**: Edit selected node properties
- **Signals**:
  - `property_changed(str, str, object)`: node_id, property_name, value
- **Dependencies**: CollapsibleSection
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import PropertiesPanel

  panel = PropertiesPanel(parent)
  panel.property_changed.connect(on_property_changed)
  panel.set_node(selected_node)
  ```

#### DebugPanel
- **Location**: `panels/debug_panel.py`
- **Purpose**: Display execution logs, breakpoints, console
- **Signals**:
  - `navigate_to_node(str)`: node_id
  - `breakpoint_toggled(str, bool)`: node_id, enabled
  - `clear_requested()`
- **Key Features**:
  - Tabs: Logs, Console, Breakpoints
  - Log filtering
  - Auto-scroll
  - Color-coded messages
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import DebugPanel

  panel = DebugPanel(parent)
  panel.navigate_to_node.connect(on_navigate)
  panel.add_log("Info", "Node executed", node_id, node_name)
  ```

#### VariablesPanel
- **Location**: `panels/variables_panel.py`
- **Purpose**: Manage workflow variables
- **Signals**:
  - `variable_added(str, str, object)`: name, type, default_value
  - `variable_changed(str, str, object)`: name, type, default_value
  - `variable_removed(str)`: name
  - `variables_changed(dict)`: all_variables
- **Key Features**:
  - Inline editing
  - Type selection
  - Design/Runtime modes
  - Variable scope indicators
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import VariablesPanel

  panel = VariablesPanel(parent)
  panel.variable_added.connect(on_variable_added)
  panel.add_variable("count", "Integer", 0, "Workflow")
  ```

#### MinimapPanel
- **Location**: `panels/minimap_panel.py`
- **Purpose**: Bird's-eye view of workflow
- **Signals**:
  - `viewport_clicked(QPointF)`: scene_pos
- **Key Features**:
  - Auto-scaling
  - Viewport indicator
  - Click navigation
  - Event-driven updates
- **Dependencies**: MinimapChangeTracker
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import MinimapPanel

  panel = MinimapPanel(parent)
  panel.viewport_clicked.connect(on_viewport_clicked)
  panel.set_graph_view(node_graph_view)
  ```

### 3. Toolbars (3)

#### MainToolbar
- **Location**: `toolbars/main_toolbar.py`
- **Purpose**: Primary workflow actions
- **Signals**:
  - `new_requested()`
  - `open_requested()`
  - `save_requested()`
  - `save_as_requested()`
  - `run_requested()`
  - `pause_requested()`
  - `resume_requested()`
  - `stop_requested()`
  - `undo_requested()`
  - `redo_requested()`
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import MainToolbar

  toolbar = MainToolbar(parent)
  toolbar.run_requested.connect(on_run)
  toolbar.set_execution_state(is_running=True, is_paused=False)
  ```

#### DebugToolbar
- **Location**: `toolbars/debug_toolbar.py`
- **Purpose**: Debug controls
- **Signals**:
  - `debug_mode_toggled(bool)`
  - `step_mode_toggled(bool)`
  - `step_requested()`
  - `continue_requested()`
  - `stop_requested()`
  - `clear_breakpoints_requested()`
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import DebugToolbar

  toolbar = DebugToolbar(parent)
  toolbar.step_requested.connect(on_step)
  toolbar.set_execution_state(is_running=True)
  ```

#### ZoomToolbar
- **Location**: `toolbars/zoom_toolbar.py`
- **Purpose**: Zoom and view controls
- **Signals**:
  - `zoom_in_requested()`
  - `zoom_out_requested()`
  - `zoom_fit_requested()`
  - `zoom_reset_requested()`
  - `zoom_changed(float)`: zoom_level
- **Key Features**:
  - Zoom slider
  - Percentage display
  - Keyboard shortcuts
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import ZoomToolbar

  toolbar = ZoomToolbar(parent)
  toolbar.zoom_changed.connect(on_zoom_changed)
  toolbar.set_zoom(1.5)  # 150%
  ```

### 4. Dialogs (3)

#### NodePropertiesDialog
- **Location**: `dialogs/node_properties_dialog.py`
- **Purpose**: Edit comprehensive node properties
- **Signals**:
  - `properties_changed(dict)`: properties
- **Key Features**:
  - Tabs: Basic, Advanced
  - Timeout settings
  - Retry configuration
  - Logging settings
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import NodePropertiesDialog

  dialog = NodePropertiesDialog(node_id, node_type, properties, parent)
  dialog.properties_changed.connect(on_properties_changed)
  if dialog.exec() == QDialog.Accepted:
      props = dialog.get_properties()
  ```

#### WorkflowSettingsDialog
- **Location**: `dialogs/workflow_settings_dialog.py`
- **Purpose**: Edit workflow-level settings
- **Signals**:
  - `settings_changed(dict)`: settings
- **Key Features**:
  - Tabs: General, Execution, Variables
  - Metadata editing
  - Error handling config
  - Variable scope settings
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import WorkflowSettingsDialog

  dialog = WorkflowSettingsDialog(settings, parent)
  dialog.settings_changed.connect(on_settings_changed)
  if dialog.exec() == QDialog.Accepted:
      settings = dialog.get_settings()
  ```

#### PreferencesDialog
- **Location**: `dialogs/preferences_dialog.py`
- **Purpose**: Edit application preferences
- **Signals**:
  - `preferences_changed(dict)`: preferences
- **Key Features**:
  - Tabs: General, Autosave, Editor, Performance
  - Theme selection
  - Grid/snap settings
  - Performance tuning
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import PreferencesDialog

  dialog = PreferencesDialog(preferences, parent)
  dialog.preferences_changed.connect(on_preferences_changed)
  dialog.exec()
  ```

### 5. Widgets (3)

#### VariableEditorWidget
- **Location**: `widgets/variable_editor_widget.py`
- **Purpose**: Inline variable editing
- **Signals**:
  - `variable_changed(str, str, object)`: name, type, value
- **Key Features**:
  - Name input
  - Type selector
  - Value editor
  - Type conversion
  - Remove button
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import VariableEditorWidget

  editor = VariableEditorWidget("count", "Integer", 0, parent)
  editor.variable_changed.connect(on_variable_changed)
  var_data = editor.get_variable()
  ```

#### OutputConsoleWidget
- **Location**: `widgets/output_console_widget.py`
- **Purpose**: Console-style execution output
- **Key Features**:
  - Color-coded messages
  - Timestamps
  - Auto-scroll
  - Copy to clipboard
  - Line limiting
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import OutputConsoleWidget

  console = OutputConsoleWidget(parent)
  console.append_info("Workflow started")
  console.append_error("Node failed: timeout")
  console.append_success("Workflow completed")
  ```

#### SearchWidget
- **Location**: `widgets/search_widget.py`
- **Purpose**: Search with fuzzy matching
- **Signals**:
  - `item_selected(str, object)`: item_text, item_data
  - `search_cleared()`
- **Key Features**:
  - Live search
  - Fuzzy matching support
  - Keyboard navigation
  - Results count
- **Usage**:
  ```python
  from casare_rpa.presentation.canvas.ui import SearchWidget

  search = SearchWidget("Search nodes...", parent)
  search.item_selected.connect(on_item_selected)
  search.set_items([("Click Node", node1), ("Type Node", node2)])
  ```

## Signal/Slot Connection Map

### Common Patterns

All components follow consistent signal patterns:

1. **Value Changes**: `<property>_changed(value)`
2. **Requests**: `<action>_requested()`
3. **State Updates**: `<state>_<change>(params)`

### Example Connection Flow

```python
# Application Setup
main_window = MainWindow()

# Create components
properties_panel = PropertiesPanel(main_window)
debug_panel = DebugPanel(main_window)
variables_panel = VariablesPanel(main_window)
main_toolbar = MainToolbar(main_window)
debug_toolbar = DebugToolbar(main_window)

# Connect workflow actions
main_toolbar.run_requested.connect(workflow_runner.run)
main_toolbar.stop_requested.connect(workflow_runner.stop)
main_toolbar.save_requested.connect(workflow_manager.save)

# Connect debug features
debug_toolbar.debug_mode_toggled.connect(workflow_runner.set_debug_mode)
debug_toolbar.step_requested.connect(workflow_runner.step_next)
debug_panel.navigate_to_node.connect(graph_view.center_on_node)

# Connect property updates
properties_panel.property_changed.connect(node_manager.update_property)

# Connect variable management
variables_panel.variable_added.connect(workflow_state.add_variable)
variables_panel.variable_changed.connect(workflow_state.update_variable)

# Connect execution feedback
workflow_runner.node_executed.connect(debug_panel.add_log)
workflow_runner.execution_started.connect(
    lambda: main_toolbar.set_execution_state(True)
)
workflow_runner.execution_stopped.connect(
    lambda: main_toolbar.set_execution_state(False)
)
```

## Styling

All components use consistent dark theme styling:

- **Background**: `#252525` (main), `#2d2d2d` (panels), `#3d3d3d` (inputs)
- **Text**: `#e0e0e0` (primary), `#888888` (muted), `#666666` (disabled)
- **Accent**: `#5a8a9a` (focus/selected)
- **Borders**: `#4a4a4a`
- **Error**: `#f44747`
- **Warning**: `#cca700`
- **Success**: `#89d185`

## Testing Components

Example unit test structure:

```python
import pytest
from PySide6.QtWidgets import QApplication
from casare_rpa.presentation.canvas.ui import PropertiesPanel

@pytest.fixture
def app():
    return QApplication([])

def test_properties_panel_initialization(app):
    panel = PropertiesPanel()
    assert panel.is_initialized()
    assert panel.get_title() == "Properties"

def test_properties_panel_set_node(app):
    panel = PropertiesPanel()
    # Create mock node
    mock_node = create_mock_node()
    panel.set_node(mock_node)
    # Verify properties displayed

def test_properties_panel_property_change_signal(app, qtbot):
    panel = PropertiesPanel()
    with qtbot.waitSignal(panel.property_changed):
        # Trigger property change
        pass
```

## Migration Guide

### From Old Code to New Components

**Before** (scattered code):
```python
# main_window.py - 500 lines
class MainWindow(QMainWindow):
    def __init__(self):
        # Inline properties panel setup
        self.properties_dock = QDockWidget("Properties")
        container = QWidget()
        layout = QVBoxLayout()
        # ... 50+ lines of UI setup
```

**After** (using components):
```python
# main_window.py - cleaner
from casare_rpa.presentation.canvas.ui import PropertiesPanel

class MainWindow(QMainWindow):
    def __init__(self):
        self.properties_panel = PropertiesPanel(self)
        self.properties_panel.property_changed.connect(self.on_property_changed)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel)
```

## Best Practices

1. **Always use BaseWidget** for new components
2. **Emit signals** for all state changes
3. **Log important events** using loguru
4. **Apply type hints** to all methods
5. **Document signals** in docstrings
6. **Handle errors gracefully** with try/except
7. **Test components** in isolation

## Future Enhancements

Potential additions:
- **TimelinePanel**: Visual execution timeline
- **MetricsPanel**: Performance metrics dashboard
- **ComparisonDialog**: Compare workflow versions
- **ExportDialog**: Export workflow options
- **ThemeSelector**: Theme customization widget

## Summary

**Components Created**: 13+
**Lines of Code**: ~3,500
**Test Coverage**: Ready for testing
**Reusability**: High
**Maintenance**: Centralized

All UI components are now:
- ✅ Extracted and organized
- ✅ Following consistent patterns
- ✅ Fully documented
- ✅ Type-safe
- ✅ Signal-based
- ✅ Theme-consistent
- ✅ Ready for use
