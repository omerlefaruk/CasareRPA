# Canvas Presentation Index

Quick reference for UI components. Use for fast discovery.

## Directory Structure

| Directory | Purpose | Index |
|-----------|---------|-------|
| `graph/` | Node graph widget, pipes, selection | [graph/_index.md](graph/_index.md) |
| `managers/` | Panel and popup management | See below |
| `ui/` | Theme, panels, dialogs, widgets | [ui/_index.md](ui/_index.md) |
| `controllers/` | UI logic (MVC pattern) | [controllers/_index.md](controllers/_index.md) |
| `visual_nodes/` | Visual wrappers (~405 nodes) | [visual_nodes/_index.md](visual_nodes/_index.md) |
| `selectors/` | Element picker, UI explorer | [selectors/_index.md](selectors/_index.md) |
| `events/` | EventBus, Qt signal bridge | [events/_index.md](events/_index.md) |
| `debugger/` | Debug controller, breakpoints | - |
| `execution/` | Execution panel runtime | - |
| `serialization/` | Workflow I/O | - |
| `components/` | MainWindow extractors | - |
| `services/` | WebSocket, trigger handlers | - |

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `main_window.py` | Main application window | ~800 |
| `app.py` | Application initialization | ~300 |
| `managers/popup_manager.py` | Centralized popup lifecycle | ~200 |
| `managers/panel_manager.py` | Dock panel management | ~150 |
| `ui/theme.py` | THEME.* constants | ~400 |
| `graph/node_graph_widget.py` | Main canvas widget | ~2400 |
| `visual_nodes/__init__.py` | _VISUAL_NODE_REGISTRY | ~610 |

## Entry Points

```python
# Theme colors (MANDATORY for all UI)
from casare_rpa.presentation.canvas.ui.theme import THEME
color = THEME.ACCENT_PRIMARY

# Event bus
from casare_rpa.presentation.canvas.events import EventBus
EventBus.emit("node_selected", node_id=id)

# Base classes
from casare_rpa.presentation.canvas.ui import BaseWidget, BaseDockWidget, BaseDialog

# Controller pattern
from casare_rpa.presentation.canvas.controllers import BaseController
```

## Managers

### PopupManager

Centralized click-outside-to-close handling for all popup windows.

```python
from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager

# In popup showEvent or show_at_position:
PopupManager.register(self)

# In popup closeEvent:
PopupManager.unregister(self)

# For pinned popups (don't close on click-outside):
PopupManager.register(self, pinned=True)
```

**Features:**
- Single app-level event filter (efficient)
- WeakSet for automatic cleanup (no memory leaks)
- Pin state support
- `close_popup()`, `close_all_popups()` helper methods

See `.claude/rules/ui/popup-rules.md` for full popup development guidelines.

## Visual Nodes (405 total)

See [visual_nodes/_index.md](visual_nodes/_index.md) for full registry.

| Category | Count | Examples |
|----------|-------|----------|
| `basic/` | 3 | VisualStartNode, VisualEndNode |
| `browser/` | 23 | VisualNavigateNode, VisualClickNode |
| `desktop_automation/` | 36 | VisualClickDesktopNode |
| `system/` | 67 | VisualMessageBoxNode, VisualTooltipNode |
| `data_operations/` | 32 | VisualSetVariableNode |

## Registration

New visual nodes require:
1. `visual_nodes/{category}/nodes.py` - Define class
2. `visual_nodes/__init__.py` - Add to _VISUAL_NODE_REGISTRY

## Related Indexes

- [nodes/_index.md](../../nodes/_index.md) - Domain node implementations
- [domain/_index.md](../../domain/_index.md) - Base classes, decorators
- [infrastructure/_index.md](../../infrastructure/_index.md) - External adapters
