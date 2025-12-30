# Epic 3.1: CommandPaletteV2

**Created**: 2025-12-30
**Status**: CANCELED (Do Not Ship)
**Epic**: Command Palette v2 with fuzzy search

## Decision (2025-12-30)
Command palette will not ship in v2. This plan is retained for historical context only.

## Removal Checklist (Replaces Implementation)
- [ ] Delete v2 palette: `src/casare_rpa/presentation/canvas/ui/widgets/popups/command_palette_v2.py`
- [ ] Delete legacy palette: `src/casare_rpa/presentation/canvas/search/command_palette.py`
- [ ] Remove Ctrl+Shift+P bindings in v2 window and any menu/controller wiring
- [ ] Remove `IMainWindow.get_command_palette()` and any call sites (e.g. menu controller)
- [ ] Verify: `rg "command[_ ]palette|CommandPalette" src/casare_rpa/presentation/canvas` returns 0

## Overview

VS Code-style command palette for quick keyboard access to all 63 ActionManagerV2 actions.

## Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Ctrl+Shift+P to open command palette | P0 |
| R2 | Fuzzy search through all ActionManagerV2 commands | P0 |
| R3 | Display keyboard shortcuts for each command | P0 |
| R4 | Category filtering (File, Edit, View, Run, etc.) | P1 |
| R5 | THEME_V2/TOKENS_V2 only (zero hardcoded colors) | P0 |
| R6 | Use PopupWindowBase as base class | P0 |
| R7 | Keyboard: Up/Down/Enter/Esc/Tab navigation | P0 |
| R8 | Auto-select first match on open | P1 |

## Technical Design

### File Structure

```
src/casare_rpa/presentation/canvas/ui/widgets/popups/
    command_palette_v2.py  # Main implementation
```

### Class Structure

```python
class CommandItem:
    """Dataclass for a single command."""
    id: str              # Action name (e.g., "run")
    label: str           # Display text (e.g., "Run")
    shortcut: str        # Current shortcut (e.g., "F5")
    category: str        # ActionCategory name
    description: str     # Status tip
    action: QAction      # Reference to QAction

class CommandListItem(QFrame):
    """Visual widget for single command in list."""
    # Shows: category badge, label, shortcut, description
    # Selected state highlight

class CommandPaletteV2(PopupWindowBase):
    """Main command palette popup."""
    # Input field for search
    # QListWidget for results
    # Fuzzy matching (reuse from autocomplete_v2.py)
    # Signals: command_executed(str)
```

### Integration with ActionManagerV2

```python
# In NewMainWindow or main_window.py
from casare_rpa.presentation.canvas.ui.widgets.popups import CommandPaletteV2
from casare_rpa.presentation.canvas.ui.chrome import ActionManagerV2

# Create command palette
self._command_palette = CommandPaletteV2(parent=self)
self._command_palette.load_from_action_manager(self._action_manager_v2)

# Connect Ctrl+Shift+P shortcut
palette_shortcut = QAction("Command Palette", self)
palette_shortcut.setShortcut(QKeySequence("Ctrl+Shift+P"))
palette_shortcut.triggered.connect(self._command_palette.show_palette)
self.addAction(palette_shortcut)
```

### Fuzzy Search Algorithm

Reuse `fuzzy_match()` from `autocomplete_v2.py`:
- Exact prefix match (score=0, best)
- Contains match (score=position)
- Character-by-character fuzzy match (score=gaps * 2)

### UI Layout

```
+------------------------------------------+
| Command Palette              [×]         |
+------------------------------------------+
| [Search input___________]                |
+------------------------------------------+
| [FILE] New Workflow            Ctrl+N    |
| [FILE] Open...                Ctrl+O    |
| [RUN]  Run                     F5        | <- selected
| [RUN]  Run All                 Shift+F3  |
| ...                                   |
+------------------------------------------+
| 63 commands | Enter to execute            |
+------------------------------------------+
```

## Implementation Checklist

| Step | Task | Status |
|------|------|--------|
| 3.1.1 | Create `command_palette_v2.py` | Pending |
| 3.1.2 | Implement `CommandItem` dataclass | Pending |
| 3.1.3 | Implement `CommandListItem` widget | Pending |
| 3.1.4 | Implement `CommandPaletteV2` main class | Pending |
| 3.1.5 | Add `load_from_action_manager()` method | Pending |
| 3.1.6 | Integrate Ctrl+Shift+P in NewMainWindow | Pending |
| 3.1.7 | Write tests | Pending |
| 3.1.8 | Update __init__.py exports | Pending |

## Dependencies

- `PopupWindowBase` (Epic 3.1 - exists)
- `ActionManagerV2` (Epic 1.2 - exists)
- `THEME_V2`/`TOKENS_V2` (Epic 1.1 - exists)
- `fuzzy_match()` from `autocomplete_v2.py` (exists)

## Test Cases

```python
def test_command_palette_loads_actions():
    """Verify all 63 actions load correctly."""
    palette = CommandPaletteV2()
    palette.load_from_action_manager(action_manager)
    assert len(palette._commands) == 63

def test_fuzzy_search_filters_correctly():
    """Verify fuzzy search works."""
    palette.set_filter_text("run")
    # Should match "Run", "Run All", "Run This Node", etc.

def test_keyboard_shortcut_opens_palette():
    """Verify Ctrl+Shift+P opens palette."""
    # Simulate Ctrl+Shift+P key press
    # Verify palette is visible and focused

def test_enter_executes_command():
    """Verify Enter executes selected command."""
    palette.set_filter_text("run")
    palette._confirm_selection()
    # Verify "run" action was triggered

def test_category_filter():
    """Verify category filtering works."""
    palette.set_category_filter(ActionCategory.RUN)
    assert all(c.category == "RUN" for c in palette._filtered_commands)
```

## Notes

- The legacy `search/command_palette.py` exists but uses old THEME/TOKENS
- This new implementation replaces it with v2 theming
- Consider deprecating old command_palette.py after migration

## References

- `ui/chrome/action_manager_v2.py` - 63 actions
- `ui/widgets/popups/autocomplete_v2.py` - Fuzzy match reference
- `ui/widgets/popups/popup_window_base.py` - Base class
- `theme_system/tokens_v2.py` - Design tokens
