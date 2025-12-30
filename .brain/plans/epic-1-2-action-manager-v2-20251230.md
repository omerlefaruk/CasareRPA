# Epic 1.2: ActionManagerV2 - Centralized Action/Shortcut Management

**Created**: 2025-12-30
**Status**: In Progress
**Parent**: Phase 1 Epic 1 (Theme System v2)

## Overview

Centralized action and keyboard shortcut management for NewMainWindow v2.

### Goals
1. Single source of truth for 50+ application actions
2. Persistent shortcut customization via QSettings
3. THEME_V2/TOKENS_V2 styling only (no hardcoded colors)
4. Compatible with IMainWindow interface protocol
5. Support for action state updates (enable/disable)

## Components

### 1. ActionManagerV2 Class

**File**: `src/casare_rpa/presentation/canvas/ui/chrome/action_manager_v2.py`

**Responsibilities**:
- Register all QAction instances with defaults
- Load/save custom shortcuts via QSettings
- Provide action lookup by name
- Batch enable/disable actions by category
- Signal emission for shortcut changes

**Key Features**:
```python
class ActionManagerV2:
    def __init__(self, main_window: IMainWindow)
    def register_action(name: str, text: str, shortcut: QKeySequence, ...)
    def get_action(name: str) -> QAction | None
    def get_all_actions() -> dict[str, QAction]
    def set_shortcut(name: str, shortcut: str) -> bool
    def reset_shortcuts() -> None
    def enable_category(category: ActionCategory) -> None
    def disable_category(category: ActionCategory) -> None
```

### 2. Action Categories

```python
class ActionCategory(StrEnum):
    FILE = "file"          # New, Open, Save, Exit
    EDIT = "edit"          # Undo, Redo, Cut, Copy, Paste
    VIEW = "view"          # Zoom, Pan, Minimap
    RUN = "run"            # Execute, Pause, Stop
    NODE = "node"          # Create, Delete, Connect
    PANEL = "panel"        # Toggle panels
    HELP = "help"          # Docs, Preferences
```

### 3. Default Shortcuts

Based on v1 ActionManager with VS Code-like standards:
- File: Ctrl+N (New), Ctrl+O (Open), Ctrl+S (Save)
- Edit: Ctrl+Z (Undo), Ctrl+Y (Redo), Ctrl+C/V/X (Copy/Paste/Cut)
- Run: F5 (Run), F6 (Pause), F7 (Stop), F8 (Restart)
- View: F (Focus), G (Home), Ctrl+M (Minimap)
- Node: F2 (Rename), Del (Delete), Ctrl+D (Duplicate)

### 4. QSettings Integration

**Settings Keys**:
- `shortcuts/{action_name}` - Custom shortcut string
- `shortcuts/version` - Format version for migrations

**Storage Format**:
```json
{
  "shortcuts": {
    "new": "Ctrl+N",
    "run": "F5",
    "custom_action": "Ctrl+Shift+X"
  },
  "version": 1
}
```

## Action Registry

### File Actions (8)
- new, open, reload, save, save_as, exit
- save_layout, reset_layout

### Edit Actions (10)
- undo, redo, cut, copy, paste, duplicate, delete
- select_all, find_node, rename_node

### View Actions (8)
- focus_view, home_all, toggle_minimap, zoom_in/out/reset
- toggle_panel, toggle_side_panel, fleet_dashboard

### Run Actions (10)
- run, run_all, pause, stop, restart
- run_to_node, run_single_node
- start_listening, stop_listening

### Node Actions (12)
- toggle_collapse, select_nearest, get_exec_out
- toggle_disable, disable_all_selected, toggle_cache
- create_frame, auto_connect, toggle_grid_snap
- auto_layout, layout_selection, quick_node_mode

### Automation Actions (6)
- validate, record_workflow, pick_selector
- desktop_selector_builder, quick_node_config

### Help Actions (5)
- documentation, keyboard_shortcuts, preferences
- check_updates, about

### Project Actions (1)
- project_manager

### Credentials Actions (1)
- credential_manager

### Performance Actions (2)
- performance_dashboard, high_performance_mode

### AI Actions (1)
- ai_assistant

**Total: 64 actions**

## Integration Points

### NewMainWindow
```python
from .ui.chrome import ActionManagerV2

class NewMainWindow:
    def __init__(self):
        self._action_manager = ActionManagerV2(self)
        self._action_manager.register_all_actions()
```

### ToolbarV2
```python
# Get actions from ActionManagerV2
action_new = action_manager.get_action("new")
toolbar.addAction(action_new)
```

### MenuBuilderV2 (Future)
```python
# Build menus from registered actions
menu_file = menu_bar.addMenu("&File")
menu_file.addAction(action_manager.get_action("new"))
```

## Testing

**File**: `tests/presentation/canvas/ui/chrome/test_action_manager_v2.py`

- Test action registration
- Test shortcut persistence (load/save)
- Test action lookup
- Test category enable/disable
- Test reset to defaults
- Test signal emission

## Dependencies

- `PySide6.QtWidgets` - QAction, QKeySequence
- `PySide6.QtCore` - QSettings, Signal, Slot
- `casare_rpa.presentation.canvas.theme_system.tokens_v2` - THEME_V2, TOKENS_V2
- `casare_rpa.presentation.canvas.interfaces` - IMainWindow protocol

## Timeline

1. [ ] Create ActionManagerV2 class
2. [ ] Implement default shortcuts registry
3. [ ] Implement QSettings persistence
4. [ ] Implement category-based state management
5. [ ] Create comprehensive tests
6. [ ] Update chrome/__init__.py exports
7. [ ] Integrate with NewMainWindow

## Success Criteria

- All 64 actions registered with defaults
- Shortcuts persist across app restarts
- Actions can be enabled/disabled by category
- Compatible with IMainWindow protocol
- Zero hardcoded colors (THEME_V2 only)
- 80%+ test coverage
