# Canvas Reference

The Canvas is CasareRPA's visual workflow editor, providing a node-based interface for designing automation workflows.

## Entry Point

```
run.py → casare_rpa.canvas.app:CasareRPAApp
```

## Main Components

### CasareRPAApp (`app.py`)

The main application class integrating Qt with asyncio via qasync.

```python
class CasareRPAApp:
    """Main application integrating Qt with asyncio."""

    # Key attributes
    _app: QApplication          # Qt application instance
    _loop: QEventLoop           # qasync event loop
    _main_window: MainWindow    # Primary UI window
    _node_graph: NodeGraphWidget # Node editor widget
    _workflow_runner: WorkflowRunner  # Execution engine
    _selector_integration: SelectorIntegration  # Element picker
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `run()` | Start the application event loop |
| `run_workflow()` | Execute the current workflow |
| `stop_workflow()` | Stop workflow execution |
| `pause_workflow()` | Pause workflow execution |
| `resume_workflow()` | Resume paused workflow |
| `save_workflow()` | Save current workflow to file |
| `load_workflow()` | Load workflow from file |

### MainWindow (`main_window.py`)

Primary UI container with menus, toolbar, and dock widgets.

```python
class MainWindow(QMainWindow):
    """Main application window."""

    # Signals
    workflow_new = Signal()
    workflow_open = Signal(str)
    workflow_save = Signal()
    workflow_run = Signal()
    workflow_stop = Signal()
```

**Components:**
- Menu bar (File, Edit, View, Run, Help)
- Toolbar (New, Open, Save, Run, Stop, Debug)
- Status bar (execution status, node count)
- Dock widgets (Log Viewer, Variable Inspector)
- Minimap overlay

### NodeGraphWidget (`node_graph_widget.py`)

Wrapper around NodeGraphQt providing the visual node editor canvas.

**Features:**
- Drag-and-drop node creation
- Connection routing between nodes
- Multi-selection and grouping
- Zoom and pan navigation
- Undo/redo support

### Node Registry (`node_registry.py`)

Manages registration and lookup of available node types.

```python
registry = get_node_registry()
registry.register_all_nodes(graph)
node_info = registry.get_node_info("LaunchBrowser")
categories = registry.get_categories()
```

## Visual Node System

### Visual Nodes (`visual_nodes/`)

Each node type has a visual wrapper that provides Qt widgets for configuration.

| File | Node Types |
|------|------------|
| `desktop_visual.py` | Desktop automation visual nodes |

**Visual Node Base:**
```python
class VisualNodeBase(BaseNode):
    NODE_CLASS = None  # Logic class reference

    def __init__(self):
        # Create property widgets
        # Setup ports from logic class
```

### Node Frame (`node_frame.py`)

Visual grouping system for organizing nodes.

```python
class NodeFrame(QGraphicsRectItem):
    """Visual frame for grouping nodes."""

    # Features
    - Automatic bounds calculation
    - Collapsible frames
    - Custom colors and titles
    - Node containment tracking
```

**FrameBoundsManager:**
Singleton for efficient multi-frame bounds checking:
```python
manager = FrameBoundsManager.get_instance()
manager.register_frame(frame)
manager.unregister_frame(frame)
```

## UI Components

### Node Search Dialog (`node_search_dialog.py`)

Fuzzy search dialog for finding and inserting nodes.

**Features:**
- Fuzzy string matching
- Category filtering
- Keyboard navigation
- Recent nodes list

### Searchable Menu (`searchable_menu.py`)

Right-click context menu with search functionality.

### Minimap (`minimap.py`)

Overview navigation overlay showing the entire workflow.

```python
class Minimap(QGraphicsView):
    """Minimap overlay for workflow navigation."""

    # Features
    - Click-to-navigate
    - Drag viewport rectangle
    - Auto-scaling
    - Visibility toggle
```

### Custom Pipe (`custom_pipe.py`)

Connection line rendering between nodes.

**Features:**
- Bezier curve routing
- Color coding by data type
- Animation during execution
- Hover highlighting

### Debug Toolbar (`debug_toolbar.py`)

Execution control toolbar for debugging workflows.

```python
class DebugToolbar(QToolBar):
    # Actions
    - Run (F5)
    - Pause (F6)
    - Stop (Shift+F5)
    - Step Over (F10)
    - Step Into (F11)
    - Step Out (Shift+F11)
```

### Log Viewer (`log_viewer.py`)

Real-time log display dock widget.

**Features:**
- Color-coded log levels
- Timestamp display
- Search/filter
- Auto-scroll
- Copy to clipboard

### Variable Inspector (`variable_inspector.py`)

Runtime variable viewer dock widget.

```python
class VariableInspectorPanel(QDockWidget):
    """Displays workflow variables during execution."""

    # Columns: Name, Value, Type
    # Auto-updates during execution
```

### Execution History Viewer (`execution_history_viewer.py`)

Execution trace and timeline viewer.

### Template Browser (`template_browser.py`)

Workflow template selection dialog.

## Selector System

### Selector Dialog (`selector_dialog.py`)

Web element selector builder dialog.

**Features:**
- Multiple selector strategies (CSS, XPath, Text)
- Live element highlighting
- Selector validation
- Preview mode

### Desktop Selector Builder (`desktop_selector_builder.py`)

Windows UI Automation element selector builder.

### Element Picker (`element_picker.py`)

Live element selection tool.

```python
class ElementPicker:
    """Captures element under cursor."""

    async def pick_element() -> ElementInfo:
        # Shows overlay, waits for click
        # Returns element selector
```

### Element Tree Widget (`element_tree_widget.py`)

UI Automation element tree viewer.

### Selector Strategy (`selector_strategy.py`)

Selector generation algorithms:
- CSS selector
- XPath
- Text content
- Accessibility attributes
- Automation ID

### Selector Validator (`selector_validator.py`)

Validates selector uniqueness and reliability.

### Selector Integration (`selector_integration.py`)

Integrates selector dialogs with node property editors.

## Recording System

### Recording Dialog (`recording_dialog.py`)

Web action recording interface.

### Desktop Recording Panel (`desktop_recording_panel.py`)

Desktop action recording interface.

```python
class DesktopRecordingPanel(QDockWidget):
    """Panel for recording desktop automation actions."""

    # Features
    - Start/stop recording
    - Action list display
    - Generate workflow from recording
```

## Configuration

### Hotkey Manager (`hotkey_manager.py`)

Global keyboard shortcut management.

### Node Icons (`node_icons.py`)

SVG icon definitions for node types.

### Rich Comment Node (`rich_comment_node.py`)

Markdown-enabled comment/annotation nodes.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New workflow |
| `Ctrl+O` | Open workflow |
| `Ctrl+S` | Save workflow |
| `Ctrl+Shift+S` | Save as |
| `F5` | Run workflow |
| `Shift+F5` | Stop workflow |
| `F6` | Pause/Resume |
| `F10` | Step over |
| `F11` | Step into |
| `Shift+F11` | Step out |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+C` | Copy nodes |
| `Ctrl+V` | Paste nodes |
| `Ctrl+A` | Select all |
| `Delete` | Delete selected |
| `Tab` | Open node search |
| `Space` | Toggle minimap |
| `MMB` | Pan canvas |
| `Scroll` | Zoom |

## Event Integration

The Canvas subscribes to execution events for visual feedback:

```python
# Visual feedback during execution
EventType.NODE_STARTED    → Yellow border
EventType.NODE_COMPLETED  → Green border
EventType.NODE_ERROR      → Red border
EventType.NODE_SKIPPED    → Gray border
```

## File Format

Workflows are saved as JSON files in `workflows/` directory.

See `ARCHITECTURE.md` for schema details.
