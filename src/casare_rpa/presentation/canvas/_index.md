# Canvas Presentation Index

Quick reference for UI components. Use for fast discovery.

## Directory Structure

| Directory | Purpose |
|-----------|---------|
| `graph/` | Node graph widget, pipes, selection |
| `ui/widgets/` | Reusable UI widgets |
| `ui/panels/` | Dock panels (properties, variables) |
| `ui/dialogs/` | Modal dialogs |
| `controllers/` | UI logic (MVC pattern) |
| `visual_nodes/` | Visual wrappers for nodes |
| `selectors/` | Element picker, UI explorer |
| `events/` | EventBus, Qt signal bridge |
| `debugger/` | Debug controller, breakpoints |

## Key Files

| File | Purpose |
|------|---------|
| `graph/node_graph_widget.py` | Main canvas widget (2.4K lines) |
| `graph/custom_node_item.py` | Node visual item |
| `graph/custom_pipe.py` | Connection pipe |
| `ui/theme.py` | THEME.* constants - use for all colors |
| `ui/widgets/variable_picker.py` | Variable insertion widget |
| `ui/widgets/node_output_popup.py` | MMB output popup |
| `ui/panels/properties_panel.py` | Node properties editor |
| `controllers/main_window_controller.py` | Main window logic |

## Common Patterns

```python
# Theme colors
from casare_rpa.presentation.canvas.ui.theme import THEME
color = THEME.ACCENT_PRIMARY

# Event bus
from casare_rpa.presentation.canvas.events import EventBus
EventBus.emit("node_selected", node_id=id)

# Controller pattern
class MyController(BaseController):
    def __init__(self, view: QWidget):
        self._view = view
```

## Visual Nodes

Located in `visual_nodes/{category}/nodes.py`:

| Category | Visual Nodes |
|----------|--------------|
| `basic/` | VisualStartNode, VisualEndNode |
| `browser/` | VisualNavigateNode, VisualClickNode |
| `desktop_automation/` | VisualClickDesktopNode |
| `control_flow/` | VisualIfNode, VisualLoopNode |
| `data_operations/` | VisualSetVariableNode |
| `triggers/` | VisualScheduleTriggerNode |

## Registration

New visual nodes require:
1. `visual_nodes/{category}/nodes.py` - Define class
2. `visual_nodes/__init__.py` - Add to _VISUAL_NODE_REGISTRY
