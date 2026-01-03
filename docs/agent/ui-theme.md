---
paths:
  - src/casare_rpa/presentation/**/*.py
  - src/casare_rpa/presentation/canvas/theme/**/*.py
---

# UI Theme Rules (Design System 2025)

This is the authoritative rule set for Desktop Canvas styling. It exists to prevent ad-hoc colors/sizing and keep the UI consistent.

## Theme system architecture (critical)

Single source of truth for Canvas theme and design tokens:

| Component | Path | Purpose |
|---|---|---|
| **Preferred imports** | `src/casare_rpa/presentation/canvas/theme/` | Canonical `THEME` + `TOKENS` + v2 exports |
| Compatibility re-export | `src/casare_rpa/presentation/canvas/theme.py` | Legacy import location (re-exports theme) |
| Theme colors (v1) | `theme/colors.py` | `CanvasThemeColors` + helpers (`get_status_color`, `get_wire_color`) |
| Theme colors (v2) | `theme/tokens_v2.py` | `THEME_V2` + `TOKENS_V2` (Cursor-like, dark-only) |
| Design tokens | `theme/design_tokens.py` | `DesignTokens` singleton (`TOKENS`) |
| QSS generators (v1) | `theme/styles.py` | Widget/style QSS builders |
| QSS generators (v2) | `theme/styles_v2.py` | V2 widget/style QSS builders |
| Widget helpers | `theme/helpers.py` | Qt sizing/margins/font helpers using `TOKENS` |
| Color utils | `theme/utils.py` | `alpha`, `darken`, `lighten`, etc. |
| Stylesheet cache | `theme/stylesheet_cache.py` | Disk cache for generated QSS |
| Font loader | `theme/font_loader.py` | Geist Sans/Mono bundling (Epic 1.2) |
| Icon provider v2 | `theme/icons_v2.py` | Cursor-like line icons (Epic 2.1) |
| Primitive gallery | `theme/primitive_gallery.py` | Component library v2 showcase (Epic 5.1) |

## Token system versions

**V1 (`TOKENS`)** - Legacy design tokens:
- Zinc-based neutral scale
- Indigo accent (#6366f1)
- Standard typography sizes
- 4px grid spacing
- Radii: 0/4/8/12/20

**V2 (`TOKENS_V2`)** - Design System 2025 (target):
- Dark-only, Cursor-like neutral ramp (darker blacks)
- Electric blue accent (#0066ff)
- Compact typography (1 step smaller)
- 4px grid spacing (6px exception)
- Radii: 0/2/3/4/6
- Zero-motion animations (0ms)

When modifying theme colors:

1. Edit `ThemeColorsV2` in `theme/tokens_v2.py`
2. Update QSS generators in `theme/styles_v2.py` if needed

## Hard rules

- Never use hardcoded hex colors (`"#..."`) in `src/casare_rpa/presentation/` (except token/theme definitions).
- Never use raw widget styling that bypasses tokens (spacing, radius, typography, z-index).
- Always use semantic tokens (`THEME.*`) and design tokens (`TOKENS.*`).

Enforcement:

- `scripts/check_theme_colors.py` blocks new hardcoded `#hex` in presentation code (incremental).

## Import pattern (preferred)

**Theme tokens (v2-only):**
```python
from casare_rpa.presentation.canvas.theme import THEME, TOKENS

layout.setSpacing(TOKENS.spacing.md)
widget.setStyleSheet(
    f"background-color: {THEME.bg_surface}; color: {THEME.text_primary};"
)
```

**Explicit v2 import (equivalent):**
```python
from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2

layout.setSpacing(TOKENS_V2.spacing.md)
widget.setStyleSheet(
    f"background-color: {THEME_V2.bg_surface}; color: {THEME_V2.text_primary};"
)
```

**V2 typography (compact):**
```python
font = QFont()
font.setFamily(TOKENS_V2.typography.ui)  # "Geist Sans" (with fallbacks)
font.setPointSize(TOKENS_V2.typography.body)  # 11
widget.setFont(font)
```

**V2 QSS helpers:**
```python
from casare_rpa.presentation.canvas.theme import (
    get_canvas_stylesheet_v2,
    get_button_styles_v2,
    get_input_styles_v2,
)

# Full canvas stylesheet
app.setStyleSheet(get_canvas_stylesheet_v2())

# Component-specific styles
button.setStyleSheet(get_button_styles_v2())
input.setStyleSheet(get_input_styles_v2())
```

## QSS helpers (preferred over ad-hoc strings)

```python
from casare_rpa.presentation.canvas.theme import get_canvas_stylesheet_v2, get_menu_styles_v2

app.setStyleSheet(get_canvas_stylesheet_v2())
menu.setStyleSheet(get_menu_styles_v2())
```

## Reference documentation

- `docs/unified-system-spec.md`
- `.brain/docs/design-system-2025.md`
- `.brain/docs/ui-standards.md`
- `.brain/docs/widget-rules.md`
- `.claude/rules/ui/popup-rules.md`

