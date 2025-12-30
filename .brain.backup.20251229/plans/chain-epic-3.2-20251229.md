# Epic 3.2: Popup Variants Implementation Plan

**Status**: PLANNING
**Created**: 2025-12-29
**Dependencies**: Epic 3.1 (PopupWindowBase) - COMPLETE

---

## Overview

Implement standardized popup variants using `PopupWindowBase` from Epic 3.1. All variants follow V2 design system (Cursor-like aesthetic, no animations, THEME_V2 tokens).

---

## Variants to Implement

| Variant | Purpose | Complexity | Parallel |
|---------|---------|------------|----------|
| **ContextMenu** | Right-click menu with items, icons, shortcuts, separators | Medium | Yes |
| **Dropdown** | Single-selection dropdown menu surface | Low | Yes |
| **Tooltip** | Rich tooltip/hint bubble with HTML support | Low | Yes |
| **Toast** | Non-modal notification (timer-based dismiss, NO animations) | Medium | Yes |
| **Inspector** | General-purpose property/value inspector popover | Medium | Yes |
| **Autocomplete** | Text field autocomplete popup | Medium | Yes |

All 6 variants can be built **in parallel** after shared utilities are created.

---

## Files to Create

### 1. Shared Utilities (Prerequisite)
```
src/casare_rpa/presentation/canvas/ui/widgets/popups/
├── __init__.py                    # Export all variants + utilities
├── popup_items.py                 # MenuItem, Separator, MenuItemGroup (shared)
└── popup_utils.py                 # Position helpers, type badges (shared)
```

### 2. Variant Implementations
```
src/casare_rpa/presentation/canvas/ui/widgets/popups/
├── context_menu_v2.py             # VS Code/Cursor-style context menu
├── dropdown_v2.py                 # Single-selection dropdown
├── tooltip_v2.py                  # Rich tooltip with HTML support
├── toast_v2.py                    # Non-modal notification (no animations)
├── inspector_v2.py                # Property/value inspector popover
└── autocomplete_v2.py             # Text field autocomplete popup
```

### 3. Test Files
```
tests/presentation/canvas/ui/widgets/popups/
├── test_popup_items.py            # Shared items tests
├── test_context_menu_v2.py
├── test_dropdown_v2.py
├── test_tooltip_v2.py
├── test_toast_v2.py
├── test_inspector_v2.py
└── test_autocomplete_v2.py
```

---

## Class Structure

### 1. PopupWindowBase (Already Exists)
```python
class PopupWindowBase(QWidget):
    """Base class with: draggable header, corner resize, click-outside, pin, escape, clamping"""
    closed: Signal
    pin_changed: Signal(bool)
```

### 2. ContextMenuV2
```python
class ContextMenuItem(QWidget):
    """Single menu item with icon, text, shortcut, checkmark"""
    clicked: Signal
    def __init__(self, text, callback, shortcut=None, icon=None, enabled=True, checkable=False)

class ContextMenuSeparator(QWidget):
    """Horizontal divider line"""

class ContextMenuV2(PopupWindowBase):
    """VS Code/Cursor-style context menu
    - scrollable list of items
    - keyboard: Up/Down/Enter/Esc
    - type: icon/text/shortcut/separator support
    """
    item_selected: Signal(str)  # item_id
```

### 3. DropdownV2
```python
class DropdownItem(QWidget):
    """Single dropdown option with icon + text"""
    selected: Signal

class DropdownV2(PopupWindowBase):
    """Single-selection dropdown menu
    - search/filter input in header
    - list of selectable items
    - keyboard: Up/Down/Enter/Esc
    - current selection highlighting
    """
    selection_changed: Signal(object)  # selected data
```

### 4. TooltipV2
```python
class TooltipV2(PopupWindowBase):
    """Rich tooltip with HTML support
    - no header (clean window)
    - rich text/HTML content
    - follow mouse mode (optional)
    - auto-dismiss on mouse leave
    """
    # Minimal header (close only), no pin
```

### 5. ToastV2
```python
class ToastLevel(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class ToastV2(PopupWindowBase):
    """Non-modal notification
    - NO animations (0ms fade)
    - timer-based auto-dismiss
    - close button
    - level-based border color (left accent)
    - stacked toasts support
    """
    dismissed: Signal()
    MIN_WIDTH = 300
    DEFAULT_DURATION_MS = 3000
```

### 6. InspectorV2
```python
class InspectorRow(QWidget):
    """Key-value pair row with drag support"""
    value_changed: Signal(object)

class InspectorV2(PopupWindowBase):
    """Property/value inspector popover
    - table-like key-value display
    - editable values (optional)
    - type badges
    - search/filter
    """
    value_changed: Signal(str, object)  # key, new_value
```

### 7. AutocompleteV2
```python
class AutocompleteItem(QWidget):
    """Autocomplete suggestion item"""
    selected: Signal()

class AutocompleteV2(PopupWindowBase):
    """Text field autocomplete popup
    - fuzzy search input
    - filtered list with scores
    - keyboard: Up/Down/Enter/Esc/Tab
    - type badges for variables
    - shows value preview
    """
    item_selected: Signal(str)  # insertion_text
```

---

## Shared Utilities (popup_items.py)

```python
# Reusable components across variants
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable

class MenuItemType(Enum):
    ACTION = "action"
    SEPARATOR = "separator"
    CHECKABLE = "checkable"
    SUBMENU = "submenu"

@dataclass(frozen=True)
class MenuItemSpec:
    """Specification for a menu item"""
    id: str
    text: str
    callback: Callable[[], Any] | None = None
    shortcut: str | None = None
    icon: str | None = None
    enabled: bool = True
    checkable: bool = False
    checked: bool = False

class MenuItem(QWidget):
    """Shared menu item widget for ContextMenu and Dropdown"""
    clicked: Signal()
    hovered: Signal()

class MenuSeparator(QWidget):
    """Shared separator widget"""

class TypeBadge(QLabel):
    """Type badge for autocomplete/inspector (AB, #, Y/N, [], {})"""
    @staticmethod
    def for_value(value: Any) -> str: ...
    @staticmethod
    def color_for_type(type_name: str) -> str: ...
```

---

## Design System Alignment

### THEME_V2 Usage (MANDATORY)
```python
# Backgrounds
THEME_V2.bg_elevated      # Popup background
THEME_V2.bg_component     # Header background
THEME_V2.bg_hover         # Item hover
THEME_V2.bg_selected      # Selected item

# Borders
THEME_V2.border           # Default border
THEME_V2.border_focus     # Focus ring

# Text
THEME_V2.text_primary     # Main text
THEME_V2.text_secondary   # Secondary text
THEME_V2.text_muted       # Disabled/hint text

# Status
THEME_V2.success / warning / error / info

# Tokens
TOKENS_V2.spacing.*       # All spacing
TOKENS_V2.radius.*        # Border radius
TOKENS_V2.typography.*    # Font sizes
```

### NO Animation Policy
```python
# ZERO motion - all durations 0ms
TOKENS_V2.motion.instant = 0
TOKENS_V2.motion.fast = 0
TOKENS_V2.motion.normal = 0

# ToastV2: Use QTimer.singleShot with 0ms for immediate show/hide
# No QPropertyAnimation for opacity/geometry
```

---

## Test Strategy

### Module-Scoped QApplication (from PopupWindowBase tests)
```python
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
```

### Test Patterns Per Variant
```python
class Test{Variant}Creation:
    def test_instantiation(self)
    def test_initial_state(self)
    def test_signals_exist(self)

class Test{Variant}Display:
    def test_show_and_close(self)
    def test_show_at_position(self)
    def test_content_display(self)

class Test{Variant}Interaction:
    def test_mouse_click(self)
    def test_keyboard_navigation(self)
    def test_escape_closes(self)

class Test{Variant}Signals:
    def test_selection_signal(self)
    def test_closed_signal(self)

class Test{Variant}Integration:
    def test_popup_manager_registration(self)
    def test_click_outside_to_close(self)
    def test_pin_state(self)
```

### Integration Tests
```python
class TestPopupStacking:
    """Multiple toasts stack without overlap"""
    def test_toasts_stack_vertically(self)

class TestPopupLifecycle:
    """Popups cleanup properly"""
    def test_memory_cleanup_on_close(self)
```

---

## Parallel Opportunities

### Phase 1: Shared Utilities (BLOCKS OTHERS)
| File | Description | Dependencies |
|------|-------------|--------------|
| `popup_items.py` | MenuItem, Separator, TypeBadge | None |
| `popup_utils.py` | Position helpers, badge utilities | None |
| `__init__.py` | Export all variants | After variants |

### Phase 2: Variants (ALL IN PARALLEL)
| Variant | Can Start After | Est. Lines |
|---------|----------------|------------|
| ContextMenuV2 | Phase 1 complete | ~350 |
| DropdownV2 | Phase 1 complete | ~250 |
| TooltipV2 | Phase 1 complete | ~150 |
| ToastV2 | Phase 1 complete | ~200 |
| InspectorV2 | Phase 1 complete | ~300 |
| AutocompleteV2 | Phase 1 complete | ~300 |

### Phase 3: Tests (IN PARALLEL)
| Test File | Variant | Dependencies |
|-----------|---------|--------------|
| `test_popup_items.py` | Shared | Phase 1 |
| `test_context_menu_v2.py` | ContextMenuV2 | Phase 2 |
| `test_dropdown_v2.py` | DropdownV2 | Phase 2 |
| `test_tooltip_v2.py` | TooltipV2 | Phase 2 |
| `test_toast_v2.py` | ToastV2 | Phase 2 |
| `test_inspector_v2.py` | InspectorV2 | Phase 2 |
| `test_autocomplete_v2.py` | AutocompleteV2 | Phase 2 |

---

## Risks and Mitigation

### Risk 1: Memory Leaks from Event Filters
**Mitigation**: Use `PopupManager.register/unregister` in `showEvent/closeEvent`. WeakSet in PopupManager prevents circular references.

### Risk 2: Animation Code Creeping In
**Mitigation**: Explicit `TOKENS_V2.motion.instant = 0` policy. Code review gate for any `QPropertyAnimation` usage.

### Risk 3: Inconsistent Styling
**Mitigation**: Single `popup_items.py` source for shared widgets. All colors from `THEME_V2` only.

### Risk 4: Toast Stacking Overlap
**Mitigation**: `ToastManager` singleton tracks active toasts and calculates vertical offsets.

### Risk 5: Escape Key Conflicts
**Mitigation**: Event filter pattern from PopupWindowBase - install on all child widgets + viewports.

### Risk 6: Race Conditions in Click-Outside
**Mitigation**: PopupManager checks `is_dragging()` before closing. Drag operations set flag during drag.

---

## Migration Path

### Existing Popups to Migrate

| Current Location | Target Variant | Migration Effort |
|------------------|----------------|------------------|
| `ui/widgets/context_menu.py` | `ContextMenuV2` | Low - already well-designed |
| `ui/widgets/toast.py` | `ToastV2` | Medium - remove animations, use V2 theme |
| `ui/widgets/node_output_popup.py` | `InspectorV2` | High - custom features (tracking, views) |
| `expression_editor/widgets/variable_autocomplete.py` | `AutocompleteV2` | Medium - adapt to PopupWindowBase |

### Migration Steps Per Popup
1. **Create new variant** alongside old (no breaking change)
2. **Add feature flags** to switch between old/new
3. **Run tests** on both variants
4. **Update call sites** one at a time
5. **Remove old implementation** after validation

### Example Migration
```python
# Before
from casare_rpa.presentation.canvas.ui.widgets.context_menu import ContextMenu

# After (with feature flag)
USE_V2_POPUPS = True  # Feature flag

if USE_V2_POPUPS:
    from casare_rpa.presentation.canvas.ui.widgets.popups import ContextMenuV2 as ContextMenu
else:
    from casare_rpa.presentation.canvas.ui.widgets.context_menu import ContextMenu
```

---

## Implementation Order

### Sprint 1: Foundation
1. `popup_utils.py` - Position helpers, badge utilities
2. `popup_items.py` - MenuItem, Separator, TypeBadge
3. Update `__init__.py` with planned exports

### Sprint 2: Simple Variants
4. `TooltipV2` - Simplest, good test of base
5. `DropdownV2` - Reuses MenuItem pattern

### Sprint 3: Medium Variants
6. `ContextMenuV2` - Most complex menu system
7. `ToastV2` - Requires timer management, no animations

### Sprint 4: Complex Variants
8. `InspectorV2` - Table-like display, editable values
9. `AutocompleteV2` - Fuzzy search, keyboard navigation

### Sprint 5: Tests & Migration
10. All test files
11. Migration of existing popups
12. Documentation updates

---

## Success Criteria

- [ ] All 6 variants implement using PopupWindowBase
- [ ] All use THEME_V2 tokens (no hardcoded colors)
- [ ] Zero animations (0ms durations)
- [ ] All variants register with PopupManager correctly
- [ ] Escape key closes all variants
- [ ] Pin state works on all variants
- [ ] Click-outside-to-close works (unpinned only)
- [ ] Test coverage > 80% per variant
- [ ] No memory leaks (verified with test cycles)
- [ ] Migration path documented for existing popups

---

## Dependencies

| Item | Status | Notes |
|------|--------|-------|
| PopupWindowBase | COMPLETE | Epic 3.1 delivered |
| PopupManager | COMPLETE | Handles click-outside, WeakSet |
| THEME_V2 tokens | COMPLETE | Epic 1.1 delivered |
| Geist Sans/Mono fonts | COMPLETE | Epic 1.2 delivered |

---

## Open Questions

1. **Toast stacking behavior**: Should toasts stack from top-right or bottom-right? Cursor uses top-right. -> **Decision: Top-right, below any existing toasts**

2. **Inspector editability**: Should InspectorV2 support inline editing or display-only? -> **Decision: Display-only in v1, edit via optional param**

3. **Autocomplete debouncing**: Should AutocompleteV2 debounce filter input? -> **Decision: Yes, 150ms debounce for performance**

4. **HTML support in Tooltip**: Full HTML or limited markdown? -> **Decision: Limited HTML (bold, italic, code, links) for security**

---

## References

- `src/casare_rpa/presentation/canvas/ui/widgets/popups/popup_window_base.py` - Base class
- `src/casare_rpa/presentation/canvas/managers/popup_manager.py` - Click-outside handling
- `src/casare_rpa/presentation/canvas/theme_system/tokens_v2.py` - Design tokens
- `src/casare_rpa/presentation/canvas/ui/widgets/context_menu.py` - Legacy pattern (keep good parts)
- `tests/presentation/canvas/ui/widgets/popups/test_popup_window_base.py` - Test patterns
