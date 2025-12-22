---
paths: src/casare_rpa/presentation/**/*.py
---

# UI Theme Rules

## Theme Constants

**ALWAYS** use `THEME.*` from `presentation/canvas/ui/theme.py`

**NEVER** use hardcoded hex color values

## Import Pattern

```python
from casare_rpa.presentation.canvas.ui.theme import THEME

# Correct - lowercase attribute names
background = THEME.bg_darkest
text_color = THEME.text_primary
accent = THEME.accent_primary

# WRONG - Never do this
background = "#1a1a2e"  # NO!
text_color = "white"     # NO!
```

## Available Theme Constants

| Category | Constants |
|----------|-----------|
| Background | `bg_darkest`, `bg_dark`, `bg_medium`, `bg_light` |
| Text | `text_primary`, `text_secondary`, `text_muted` |
| Accent | `accent_primary`, `accent_secondary`, `accent_hover` |
| Status | `success`, `warning`, `error`, `info` |
| Border | `border_primary`, `border_secondary` |

## Qt Widget Styling

```python
# Correct - Using THEME with lowercase attributes
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

## Reference Documentation

For detailed UI standards, see:
- `.brain/docs/ui-standards.md`
- `.brain/docs/widget-rules.md`
