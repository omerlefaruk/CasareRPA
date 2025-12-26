---
paths: src/casare_rpa/presentation/**/*.py
---

# UI Theme Rules

## Theme Constants

**ALWAYS** use `Theme.get_colors()` or `THEME.*` from `presentation/canvas/ui/theme.py`

**NEVER** use hardcoded hex color values

## Import Pattern

```python
from casare_rpa.presentation.canvas.ui.theme import Theme, THEME

# Modern approach (preferred)
c = Theme.get_colors()
background = c.background
text_color = c.text_primary
accent = c.accent

# Legacy approach (backward compatible)
background = THEME.bg_darkest
text_color = THEME.text_primary
accent = THEME.accent_primary

# WRONG - Never do this
background = "#1a1a2e"  # NO!
text_color = "white"     # NO!
```

## Available Theme Constants

| Category | Constants (Modern) | Legacy (THEME.*) |
|----------|-------------------|------------------|
| Background | `background`, `background_alt`, `surface` | `bg_darkest`, `bg_dark`, `bg_medium` |
| Text | `text_primary`, `text_secondary`, `text_muted` | `text_primary`, `text_secondary`, `text_muted` |
| Accent | `accent`, `accent_hover`, `primary` | `accent_primary`, `accent_secondary` |
| Status | `success`, `warning`, `error`, `info` | `success`, `warning`, `error`, `info` |
| Border | `border`, `border_light`, `border_focus` | `border_primary`, `border_secondary` |
| **Menu** | `menu_bg`, `menu_border`, `menu_hover` | `menu_bg`, `menu_border`, `menu_hover` |

## Qt Widget Styling

### General Styling

```python
# Correct - Using Theme.get_colors()
c = Theme.get_colors()
widget.setStyleSheet(f"""
    background-color: {c.background};
    color: {c.text_primary};
    border: 1px solid {c.border};
""")

# Or using legacy THEME
widget.setStyleSheet(f"""
    background-color: {THEME.bg_darkest};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border_primary};
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
from casare_rpa.presentation.canvas.ui.theme import Theme

menu.setStyleSheet(Theme.context_menu_style())
```

## Style Helpers

Theme provides helper methods for common widgets:

```python
# Button styles
style = Theme.button_style("md", "primary")

# Input styles
style = Theme.input_style()

# Context menu styles
style = Theme.context_menu_style()

# Panel styles
style = Theme.panel_style()
```

## Reference Documentation

For detailed UI standards, see:
- `.brain/docs/ui-standards.md`
- `.brain/docs/widget-rules.md`
- `.claude/rules/ui/popup-rules.md`
