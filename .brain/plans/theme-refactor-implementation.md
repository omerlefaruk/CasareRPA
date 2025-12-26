# Theme Refactor Implementation Plan

**Date**: 2025-12-27
**Status**: Ready for Execution
**Estimated Time**: 3 hours for P0 files

---

## Overview

This plan provides exact replacements for refactoring hardcoded colors to THEME tokens in P0 priority files.

**Files to modify:**
1. `theme_system/colors.py` - Add missing tokens
2. `graph/style_manager.py` - Replace QColor RGB values
3. `selectors/unified_selector_dialog.py` - Replace accent_color defaults
4. `ui/panels/port_legend_panel.py` - Update LEGEND_ENTRIES
5. `ui/panels/panel_ux_helpers.py` - Add documentation

---

## Phase 1: Add Missing Theme Tokens

### File: `theme_system/colors.py`

#### Add to CanvasThemeColors class (after `accent_error` ~line 135):

```python
    # Selection overlays (for badges, status indicators)
    selection_success_bg: str = "#1a3d1a"
    selection_error_bg: str = "#3d1a1a"
    selection_warning_bg: str = "#3d3a1a"
    selection_info_bg: str = "#1a2d3d"
    
    # Brand colors (for OAuth providers)
    brand_google: str = "#4285f4"
    brand_google_hover: str = "#5a95f5"
    brand_gemini: str = "#9C27B0"
    brand_gemini_hover: str = "#B026B8"
    
    # Overlays (for modal backgrounds)
    overlay_dark: str = "rgba(0, 0, 0, 128)"
    overlay_light: str = "rgba(255, 255, 255, 10)"
```

#### Add new helper function (at end of file after `get_status_color()`):

```python
def get_selection_overlay_color(status: str, theme: CanvasThemeColors = None) -> str:
    """Get background color for selection overlay badges."""
    if theme is None:
        theme = CanvasThemeColors()
    
    status_map = {
        "success": theme.selection_success_bg,
        "error": theme.selection_error_bg,
        "warning": theme.selection_warning_bg,
        "info": theme.selection_info_bg,
    }
    return status_map.get(status.lower(), theme.selection_info_bg)
```

---

## Phase 2: P0 File Replacements

### File 1: `graph/style_manager.py`

| Line | Action | Details |
|------|--------|---------|
| 34-48 | DELETE | FRAME_COLOR_PALETTE dict (unused) |
| 51-61 | DELETE | FRAME_COLORS dict (unused) |
| 64 | REPLACE | `DEFAULT_FRAME_COLOR = QColor(...)` → `QColor(THEME.bg_node)` |
| 66 | REPLACE | `DEFAULT_PORT_COLOR = QColor(...)` → `QColor(THEME.wire_data)` |
| 76-97 | REPLACE | get_frame_color() method body |
| 145-153 | REPLACE | CollapseButtonStyle colors |

#### get_frame_color() Replacement:

```python
@staticmethod
def get_frame_color(color_name: str) -> QColor:
    from casare_rpa.presentation.canvas.ui.theme import Theme
    
    color_map = {
        "blue": Theme.get_canvas_colors().wire_data,
        "purple": THEME.wire_list,
        "green": THEME.wire_number,
        "orange": THEME.wire_string,
        "red": THEME.status_error,
        "yellow": THEME.status_warning,
        "teal": THEME.wire_dict,
        "pink": THEME.node_skipped,
        "gray": THEME.text_secondary,
    }
    
    return QColor(color_map.get(color_name.lower(), THEME.bg_node))
```

#### CollapseButtonStyle Replacement:

```python
BACKGROUND_NORMAL = QColor(THEME.bg_medium)
BACKGROUND_NORMAL.setAlpha(180)
BACKGROUND_HOVER = QColor(THEME.bg_hover)
BORDER_COLOR = QColor(THEME.border)
SYMBOL_COLOR = QColor(THEME.text_primary)
```

---

### File 2: `selectors/unified_selector_dialog.py`

Replace all `accent_color: str = "#..."` defaults:

| Line | Old Value | New Value |
|------|-----------|-----------|
| 73 | `"#60a5fa"` | `THEME.status_info` |
| 246 | `"#fbbf24"` | `THEME.status_warning` |
| 310 | `"#10b981"` | `THEME.status_success` |
| 358 | `"#3b82f6"` | `THEME.status_info` |
| 386 | `"#f59e0b"` | `THEME.status_warning` |
| 421 | `"#8b5cf6"` | `THEME.wire_list` |
| 463 | `"#ec4899"` | `THEME.node_skipped` |
| 582 | `"#60a5fa"` | `THEME.status_info` |

---

### File 3: `ui/panels/port_legend_panel.py`

Replace LEGEND_ENTRIES (lines 34-43):

```python
LEGEND_ENTRIES: list[tuple[str, str, str, str]] = [
    ("", "Execution", THEME.text_primary, "Control flow between nodes"),
    ("", "String", THEME.wire_string, "Text data"),
    ("", "Integer", THEME.wire_number, "Whole numbers"),
    ("", "Float", THEME.wire_number, "Decimal numbers"),
    ("", "Boolean", THEME.wire_bool, "True/False values"),
    ("", "List", THEME.wire_list, "Array of values"),
    ("", "Dict", THEME.wire_dict, "Key-value mapping"),
    ("", "Page", THEME.status_info, "Browser page"),
    ("", "Element", THEME.wire_list, "Web element"),
    ("", "Any", THEME.text_secondary, "Wildcard type"),
]
```

---

### File 4: `ui/panels/panel_ux_helpers.py`

Add documentation comment after line 52:

```python
# TYPE COLORS: Syntax highlighting colors for variable type badges
# NOTE: These are data visualization colors (VSCode Dark+ syntax style),
# NOT UI theme colors. They should remain distinct from THEME.wire_* colors
# which are for connection wires in the node graph.
TYPE_COLORS = {  # syntax highlighting colors - not UI theme colors
```

---

## Verification Commands

```bash
# Find remaining hardcoded QColor RGB
rg 'QColor\([0-9]{1,3},\s*[0-9]{1,3},\s*[0-9]{1,3}' src/casare_rpa/presentation/canvas/

# Find hardcoded hex colors
rg '"#[0-9A-Fa-f]{6}"' src/casare_rpa/presentation/canvas/

# Verify THEME imports
rg 'from.*theme import THEME' src/casare_rpa/presentation/canvas/ -l
```

---

## Visual Testing Checklist

- [ ] Frame colors render correctly
- [ ] Selector dialog accents match status types
- [ ] Port legend colors match wire colors
- [ ] No broken styling

---

## Token Reference

### Available THEME colors:

- **Backgrounds**: bg_darkest, bg_dark, bg_medium, bg_light, bg_panel, bg_header, bg_hover, bg_selected
- **Borders**: border_dark, border, border_light, border_focus
- **Text**: text_primary, text_secondary, text_muted, text_disabled, text_header
- **Status**: status_success, status_warning, status_error, status_info, status_running, status_idle
- **Node**: node_idle, node_running, node_success, node_error, node_skipped, node_breakpoint
- **Accent**: accent_primary, accent_secondary, accent_hover, accent_success, accent_warning, accent_error
- **Wires**: wire_exec, wire_data, wire_bool, wire_string, wire_number, wire_list, wire_dict, wire_table
