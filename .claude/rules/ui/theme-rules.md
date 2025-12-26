---
paths: src/casare_rpa/presentation/**/*.py
---

# UI Theme Rules

## Theme System Architecture (CRITICAL)

**UNIFIED THEME SYSTEM:**

Single source of truth for all theme colors:

| Component | Path | Purpose |
|-----------|------|---------|
| **Entry Point** | `canvas/theme.py` | Main import location, re-exports all theme components |
| **Source of Truth** | `canvas/theme_system/colors.py` | CanvasThemeColors, CanvasColors dataclasses |
| **Styles** | `canvas/theme_system/styles.py` | QSS generator functions for widgets |
| **Helpers** | `canvas/theme_system/canvas_helpers.py` | Canvas color helpers (get_category_color, etc.) |
| **Utils** | `canvas/theme_system/utils.py` | Color manipulation (darken, lighten, alpha, etc.) |
| **Constants** | `canvas/theme_system/constants.py` | Spacing, sizes, borders, radii |
| **Cache** | `canvas/theme_system/stylesheet_cache.py` | Disk cache for generated stylesheets |

**When modifying theme colors:**
1. Edit `CanvasThemeColors` (UI colors) or `CanvasColors` (Canvas colors) in `theme_system/colors.py`
2. Bump `_THEME_VERSION` in `stylesheet_cache.py`
3. Clear cache: delete `~/.casare_rpa/cache/stylesheet_cache.*`

## Theme Constants

**ALWAYS** use `THEME.*` from `presentation/canvas/theme.py`

**NEVER** use hardcoded hex color values

## Import Pattern

```python
from casare_rpa.presentation.canvas.theme import THEME, get_canvas_stylesheet

# Direct attribute access (most common)
background = THEME.bg_darkest
text_color = THEME.text_primary
accent = THEME.accent_primary

# Canvas colors (category, wire, status colors)
from casare_rpa.presentation.canvas.theme import (
    get_category_color,
    get_wire_color,
    get_status_color,
)
cat_color = get_category_color("browser")  # Returns "#9C27B0"
wire_color = get_wire_color("string")     # Returns "#CE9178"

# Full stylesheet
stylesheet = get_canvas_stylesheet()  # Cached, fast

# WRONG - Never do this
background = "#1a1a2e"  # NO!
text_color = "white"     # NO!
```

## Available Theme Constants

| Category | THEME.* Attributes |
|----------|-------------------|
| Background | `bg_darkest`, `bg_dark`, `bg_medium`, `bg_light`, `bg_panel`, `bg_header`, `bg_hover` |
| Text | `text_primary`, `text_secondary`, `text_muted`, `text_disabled`, `text_header` |
| Accent | `accent_primary`, `accent_secondary`, `accent_hover`, `accent_success`, `accent_warning`, `accent_error` |
| Status | `status_success`, `status_warning`, `status_error`, `status_info`, `status_running`, `status_idle` |
| Border | `border_dark`, `border`, `border_light`, `border_focus` |
| Node | `node_idle`, `node_running`, `node_success`, `node_error`, `node_skipped`, `node_breakpoint` |
| Wire | `wire_exec`, `wire_data`, `wire_bool`, `wire_string`, `wire_number`, `wire_list`, `wire_dict`, `wire_table` |
| Menu | `menu_bg`, `menu_border`, `menu_hover`, `menu_text`, `menu_separator`, `menu_shadow` |
| Editor | `editor_bg`, `editor_current_line`, `editor_selection`, `syntax_keyword`, `syntax_string`, etc. |

## Qt Widget Styling

### General Styling

```python
from casare_rpa.presentation.canvas.theme import THEME

# CORRECT - Using THEME constants
widget.setStyleSheet(f"""
    background-color: {THEME.bg_darkest};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
""")

# WRONG - Hardcoded values
widget.setStyleSheet("""
    background-color: #1a1a2e;
    color: white;
""")
```

### Context Menus

**ALWAYS use the VS Code/Cursor-style context menu:**

```python
from casare_rpa.presentation.canvas.ui.widgets.context_menu import (
    ContextMenu,
    show_context_menu,
)

# Option 1: Build menu programmatically
menu = ContextMenu(parent=self)
menu.add_item("Copy", callback=copy_func, shortcut="Ctrl+C")
menu.add_item("Paste", callback=paste_func, shortcut="Ctrl+V")
menu.add_separator()
menu.add_item("Delete", callback=delete_func, shortcut="Del")
menu.show_at_position(global_pos)

# Option 2: Quick convenience function
show_context_menu(
    parent=self,
    position=global_pos,
    items=[
        {"text": "Copy", "callback": copy_func, "shortcut": "Ctrl+C"},
        {"separator": True},
        {"text": "Paste", "callback": paste_func, "shortcut": "Ctrl+V"},
    ]
)
```

**For QMenu widgets**, apply the theme style:

```python
from casare_rpa.presentation.canvas.theme import get_menu_styles, THEME

menu.setStyleSheet(get_menu_styles(THEME))
```

## Style Helpers

For widget-specific QSS generators, import from theme_system:

```python
from casare_rpa.presentation.canvas.theme import (
    get_button_styles,
    get_input_styles,
    get_menu_styles,
    get_canvas_stylesheet,
)

# Get stylesheet for specific widget type
button_qss = get_button_styles(THEME)
input_qss = get_input_styles(THEME)
menu_qss = get_menu_styles(THEME)

# Or get the full application stylesheet (cached)
full_stylesheet = get_canvas_stylesheet()
```

## Reference Documentation

For detailed UI standards, see:
- `.brain/docs/ui-standards.md`
- `.brain/docs/widget-rules.md`
- `.claude/rules/ui/popup-rules.md`
