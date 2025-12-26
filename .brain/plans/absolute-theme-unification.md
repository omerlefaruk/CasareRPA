# ABSOLUTE THEME UNIFICATION PLAN

> "The most absurd plan to unify all theme and UI related things into one."

## Current State (CHAOS)

```
┌─────────────────────────────────────────────────────────────────┐
│                         THEME MADNESS                            │
├─────────────────────────────────────────────────────────────────┤
│  presentation/canvas/theme.py          (286 lines - wrapper)    │
│  presentation/canvas/theme_system/     (~1500 lines - ACTIVE)   │
│  presentation/canvas/ui/theme.py       (1974 lines - DUPLICATE!) │
└─────────────────────────────────────────────────────────────────┘
```

### The Problem

| File | `THEME` = | Has | Used By |
|------|-----------|-----|---------|
| `canvas/theme.py` | `CanvasThemeColors` | Zinc/Indigo palette | ~58 files |
| `canvas/ui/theme.py` | `_LegacyThemeColors` | VSCode Dark+ palette | ~47 files |

**BOTH ARE CALLED `THEME` BUT HAVE DIFFERENT VALUES!**

### Statistics

| Metric | Value |
|--------|-------|
| Total theme-related files | 3 |
| Files importing themes | ~105 |
| Duplicate `get_canvas_stylesheet()` | 2 (582 lines each!) |
| THEME attributes used | 80+ |
| Canvas color properties | 38 |
| Color definitions | 2 different palettes |

---

## Target State (UNITY)

```
┌─────────────────────────────────────────────────────────────────┐
│                   SINGLE SOURCE OF TRUTH                         │
├─────────────────────────────────────────────────────────────────┤
│  presentation/canvas/theme.py          (ENTRY POINT - wrapper)   │
│  presentation/canvas/theme_system/     (SOURCE OF TRUTH)        │
│                                                                   │
│  presentation/canvas/ui/theme.py       (DELETED - 1974 lines)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: EXPAND theme_system/ (Add Missing Pieces)

### 1.1 Move CanvasColors to theme_system/colors.py

**Current location:** `ui/theme.py:261-383`

**Target:** `theme_system/colors.py`

**Properties to move (38 total):**

#### Category Colors (24)
```python
category_browser: str = "#9C27B0"
category_desktop: str = "#E91E63"
category_control_flow: str = "#F44336"
category_error_handling: str = "#D32F2F"
category_data: str = "#4CAF50"
category_variable: str = "#2196F3"
category_database: str = "#00BCD4"
category_rest_api: str = "#FF5722"
category_file: str = "#FFC107"
category_office_automation: str = "#217346"
category_email: str = "#EA4335"
category_google: str = "#4285F4"
category_triggers: str = "#7C4DFF"
category_messaging: str = "#25D366"
category_document: str = "#FF9800"
category_utility: str = "#607D8B"
category_basic: str = "#3F51B5"
category_scripts: str = "#CDDC39"
category_system: str = "#795548"
category_navigation: str = "#673AB7"
category_interaction: str = "#03A9F4"
category_wait: str = "#FF5722"
category_debug: str = "#9E9E9E"
category_default: str = "#546E7A"
```

#### Wire Colors (19)
```python
wire_exec: str = "#FFFFFF"
wire_string: str = "#CE9178"
wire_integer: str = "#B5CEA8"
wire_float: str = "#B5CEA8"
wire_boolean: str = "#569CD6"
wire_list: str = "#C586C0"
wire_dict: str = "#4EC9B0"
wire_page: str = "#C586C0"
wire_element: str = "#C586C0"
wire_window: str = "#9CDCFE"
wire_desktop_element: str = "#9CDCFE"
wire_db_connection: str = "#4EC9B0"
wire_workbook: str = "#217B4B"
wire_worksheet: str = "#217B4B"
wire_datatable: str = "#569CD6"
wire_document: str = "#FF9800"
wire_any: str = "#808080"
wire_default: str = "#808080"
wire_incompatible: str = "#F44336"
```

#### Wire Effects (5)
```python
wire_flow_dot: str = "#FFFFFF"
wire_flow_glow: str = "#FFFFFF50"
wire_completion_glow: str = "#22C55E99"
wire_hover: str = "#64B5F6"
wire_insert_highlight: str = "#FF8C00"
```

#### Status Colors (8)
```python
status_success: str = "#22C55E"
status_error: str = "#EF4444"
status_warning: str = "#F59E0B"
status_running: str = "#FBBF24"
status_idle: str = "#6B6B6B"
status_skipped: str = "#A1A1AA"
status_disabled: str = "#3F3F46"
status_breakpoint: str = "#EF4444"
```

#### Node Visuals (9)
```python
node_bg: str = "#27272A"
node_bg_header: str = "#3F3F46"
node_border_normal: str = "#3F3F46"
node_border_selected: str = "#FBBF24"
node_border_running: str = "#FBBF24"
node_border_hover: str = "#52525B"
node_text_title: str = "#FAFAFA"
node_text_port: str = "#D4D4D8"
node_text_secondary: str = "#A1A1AA"
```

#### Badges (3)
```python
badge_bg: str = "#18181B"
badge_text: str = "#E4E4E7"
badge_border: str = "#3F3F46"
```

#### Collapse Button (3)
```python
collapse_btn_bg: str = "#3F3F46"
collapse_btn_bg_hover: str = "#52525B"
collapse_btn_symbol: str = "#D4D4D8"
```

#### Labels/Preview (6)
```python
label_bg: str = "#27272A"
label_border: str = "#52525B"
label_text: str = "#D4D4D8"
preview_bg: str = "#32322D"
preview_border: str = "#64645A"
preview_text: str = "#DCDCB4"
```

### 1.2 Add CATEGORY_COLOR_MAP to theme_system/colors.py

**Current location:** `ui/theme.py:458-485`

**Target:** `theme_system/colors.py`

### 1.3 Add CanvasColors helper methods

```python
def get_canvas_category_color(category: str) -> str:
    """Get hex color for a node category."""

def get_canvas_category_qcolor(category: str) -> QColor:
    """Get QColor for a node category (cached)."""
```

### 1.4 Add missing THEME mappings

**Missing attributes** (found in analysis):
```python
"status_online": c.success
"status_busy": c.warning
"progress_bg": c.surface
```

---

## Phase 2: TRANSFORM ui/theme.py into Thin Wrapper

### 2.1 Delete duplicate `get_canvas_stylesheet()` (582 lines!)

**Current:** Lines 1277-1858 in `ui/theme.py`

**Action:** DELETE - use `theme_system/styles.py` version

### 2.2 Delete duplicate `Colors` dataclass

**Current:** Lines 56-144 in `ui/theme.py`

**Action:** DELETE - use `CanvasThemeColors` from `theme_system/colors.py`

### 2.3 Refactor Theme class to import from theme_system

```python
# NEW ui/theme.py (thin wrapper)
from casare_rpa.presentation.canvas.theme_system.colors import (
    CanvasThemeColors,
    DARK_CANVAS_COLORS,  # After move
    CATEGORY_COLOR_MAP,  # After move
)

class Theme:
    """Thin wrapper around theme_system for backward compatibility."""

    @classmethod
    def get_colors(cls) -> Colors:
        # Returns legacy Colors for compatibility
        # Maps from CanvasThemeColors

    @classmethod
    def get_canvas_colors(cls) -> CanvasColors:
        # Returns DARK_CANVAS_COLORS

    @classmethod
    def get_category_color(cls, category: str) -> str:
        # Returns category color

    # Preserve only used helper methods:
    # - context_menu_style()
    # - message_box_style()
    # - get_status_qcolor()
    # - get_category_qcolor()
```

### 2.4 Keep TYPE_COLORS and TYPE_BADGES

These are unique to `ui/theme.py` and not duplicated:

```python
TYPE_COLORS: dict[str, str] = { ... }  # Keep
TYPE_BADGES: dict[str, str] = { ... }  # Keep
```

---

## Phase 3: UNIFY IMPORTS

### 3.1 Update files importing `canvas/theme` → add canvas/theme_system

**58 files to verify** - ensure all get colors from unified system

### 3.2 Update files importing `ui/theme` → verify compatibility

**47 files** - ensure Theme class methods still work

### 3.3 Fix relative imports

**3 files with relative imports:**
- `selectors/element_tree_widget.py`
- `selectors/selector_dialog.py`
- `visual_nodes/base_visual_node.py`

Change `from ..ui.theme import` → `from casare_rpa.presentation.canvas.theme import`

---

## Phase 4: ADD MISSING COLORS TO CanvasThemeColors

### 4.1 Add attributes not currently in CanvasThemeColors

```python
# From _LegacyThemeColors mapping, add to CanvasThemeColors:
@dataclass
class CanvasThemeColors:
    # ... existing colors ...

    # Additional colors for widgets
    accent_darker: str = "#1D4ED8"
    error_bg: str = "#5A1D1D"
    link: str = "#569CD6"
    link_hover: str = "#9CDCFE"
    selector_text: str = "#60A5FA"

    # JSON syntax colors
    json_key: str = "#9CDCFE"
    json_string: str = "#CE9178"
    json_number: str = "#B5CEA8"
    json_boolean: str = "#569CD6"

    # Orchestrator-specific
    status_online: str = "#10B981"
    status_busy: str = "#F59E0B"
    progress_bg: str = "#3F3F46"
```

---

## Phase 5: UPDATE DOCUMENTATION

### 5.1 Update `.brain/docs/ui-standards.md`
- Remove dual-system references
- Document single source of truth

### 5.2 Update `.claude/rules/ui/theme-rules.md`
- Reflect unified architecture
- Update cache invalidation steps

### 5.3 Update `_index.md` files
- Remove duplicate theme references

---

## Phase 6: TESTING CHECKLIST

- [ ] Canvas loads without errors
- [ ] Node colors render correctly (all 24 categories)
- [ ] Wire colors render correctly (all types)
- [ ] Context menus have VS Code styling
- [ ] All panels use consistent colors
- [ ] Expression editor highlights correctly
- [ ] Variable picker badges display
- [ ] Status indicators show correct colors
- [ ] Dialog buttons render properly
- [ ] Orchestrator colors work

---

## File Impact Summary

| Action | Files | Lines Added | Lines Removed |
|--------|-------|-------------|---------------|
| Move CanvasColors | 1 | 123 | 123 (moved) |
| Delete duplicate get_canvas_stylesheet | 1 | 0 | -582 |
| Refactor Theme class | 1 | ~50 | ~400 |
| Update imports | ~105 | ~50 | ~50 |
| Update docs | 5 | ~100 | ~50 |
| **TOTAL** | ~113 | ~323 | ~1005 |

**Net code reduction: ~682 lines**

---

## Execution Order

1. **EXPAND** - Add missing pieces to `theme_system/`
2. **TEST** - Verify theme_system is complete
3. **TRANSFORM** - Refactor `ui/theme.py` to thin wrapper
4. **VERIFY** - Ensure no import errors
5. **UPDATE** - Fix imports across codebase
6. **TEST** - Full integration test
7. **DOCUMENT** - Update all documentation
8. **CLEANUP** - Remove deprecated code

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking imports | Preserve Theme class wrapper |
| Color value changes | Keep existing values, just move |
| Missing colors | Comprehensive analysis done |
| Cache issues | Bump version, clear cache |

---

## Success Criteria

- [ ] Single `CanvasThemeColors` dataclass contains ALL colors
- [ ] `theme_system/` is the ONLY source of color definitions
- [ ] `ui/theme.py` is <500 lines (from 1974)
- [ ] All 105 files still work correctly
- [ ] Zero duplicate color definitions
- [ ] Documentation reflects unified architecture

---

*Generated: 2025-12-26*
*Status: DRAFT - Awaiting Approval*
