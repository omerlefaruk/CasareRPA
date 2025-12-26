# Theme Refactor Plan - Complete Analysis

**Date**: 2025-12-27
**Agents Used**: 8 (3 quality + 5 explore)

---

## Executive Summary

| Category | Total Files | Violations | Priority |
|----------|-------------|------------|----------|
| **Hardcoded Colors** | 29 files | 100+ instances | P0-P2 |
| **Hardcoded Sizes/Spacing** | 25+ files | 60+ instances | P1-P2 |
| **Partial THEME Usage** | 10 files | Both THEME + hardcoded | P1 |
| **Already Compliant** | 100+ files | None | N/A |

---

## P0 - Critical (High Visibility, User-Facing)

### Files Requiring Immediate Attention

| File | Issue | Count | Fix |
|------|-------|-------|-----|
| `graph/style_manager.py` | `QColor(r,g,b,a)` | 11 | Use THEME tokens |
| `selectors/unified_selector_dialog.py` | Hex colors in sections | 9 | Use THEME.accent_* |
| `ui/panels/panel_ux_helpers.py` | TYPE_COLORS dict | 11 | Use THEME.wire_* |
| `ui/panels/port_legend_panel.py` | Port type colors | 8 | Use get_wire_color() |
| `selectors/element_selector_dialog.py` | `QColor(0,0,0,128)` | 1 | Use THEME.overlay |

### P0 Fixes Required

**1. Add new theme tokens to `theme_system/colors.py`:**
```python
# Selection overlays
SELECTION_OVERLAY_SUCCESS = "#1a3d1a"
SELECTION_OVERLAY_ERROR = "#3d1a1a"
SELECTION_OVERLAY_WARNING = "#3d3a1a"
SELECTION_OVERLAY_INFO = "#1a2d3d"

# Log backgrounds
LOG_BG_WARNING = "#3d3a1a"
LOG_BG_ERROR = "#3d1a1a"
LOG_BG_SUCCESS = "#1a3d1a"

# Overlays
OVERLAY_DARK = "rgba(0, 0, 0, 0.5)"
OVERLAY_LIGHT = "rgba(255, 255, 255, 0.1)"
```

---

## P1 - High (Dialogs, Panels, Selectors)

### Dialog Files

| File | Colors | Replace With |
|------|--------|--------------|
| `google_oauth_dialog.py` | `#4285f4`, `#5a95f5`, `#2d5a9e` | `THEME.brand_google_*` (new tokens) |
| `antigravity_oauth_dialog.py` | `#4285f4`, `#5a95f5`, `#2d5a9e` | `THEME.brand_google_*` (new tokens) |
| `credential_manager_dialog.py` | `#4285F4`, `#5a95f5`, `#9C27B0`, `#B026B8` | `THEME.brand_google_*`, `THEME.brand_gemini_*` |
| `recording_review_dialog.py` | `QColor(0,0,0,0)` | `Qt.GlobalColor.transparent` |

### Panel Files

| File | Colors | Issue |
|------|--------|-------|
| `ui/panels/history_tab.py` | `#1a3d1a`, `#3d1a1a` | Status backgrounds |
| `ui/panels/log_tab.py` | `#3d3a1a`, `#3d1a1a`, `#1a3d1a` | Log level backgrounds |
| `ui/panels/debug_console_panel.py` | 15 colors | Syntax highlighting |

### Widget Files

| File | Issue | Count |
|------|-------|-------|
| `ui/widgets/expression_editor/syntax/*_highlighter.py` | `selection-color: #FFFFFF` | 4 files |

---

## P2 - Medium (Graph, Selectors, Sizes)

### Graph Files

| File | Issue | Count |
|------|-------|-------|
| `graph/background_cache.py` | `QColor(r,g,b)` | 2 |
| `graph/custom_pipe.py` | `QColor(255,255,255,0)` | 1 |
| `graph/subflow_node_item.py` | `QColor(255,255,255)` | 1 |

### Selector Files

| File | Issue | Count |
|------|-------|-------|
| `selectors/element_picker.py` | `QColor(255,0,0,30)` | 2 |
| `selectors/selector_validator.py` | Status color map | 5 |

### Size/Spacing Files (Need TOKENS)

| File | Issue | Should Use |
|------|-------|------------|
| `graph/node_graph_widget.py` | `move(10, 10)` | `TOKENS.spacing.xs` |
| `graph/custom_node_item.py` | `margin = 40/10/6` | `TOKENS.spacing.*` |
| `graph/subflow_node_item.py` | `margin = 6` | `TOKENS.spacing.sm` |
| `ui/widgets/variable_picker.py` | `button_spacing = 2` | `TOKENS.spacing.xxs` (new) |

---

## THEME System Structure (Reference)

### Complete Token Reference

**Colors (THEME):**
- Backgrounds: `bg_darkest`, `bg_dark`, `bg_medium`, `bg_light`, `bg_panel`, `bg_header`, `bg_hover`, `bg_selected`, `bg_canvas`, `bg_node`, `bg_node_selected`, `bg_node_header`
- Borders: `border_dark`, `border`, `border_light`, `border_focus`
- Text: `text_primary`, `text_secondary`, `text_muted`, `text_disabled`, `text_header`, `text_on_accent`
- Status: `status_success`, `status_warning`, `status_error`, `status_info`, `status_running`, `status_idle`
- Node Status: `node_idle`, `node_running`, `node_success`, `node_error`, `node_skipped`, `node_breakpoint`
- Accent: `accent_primary`, `accent_secondary`, `accent_hover`, `accent_success`, `accent_warning`, `accent_error`
- Wires: `wire_exec`, `wire_data`, `wire_bool`, `wire_string`, `wire_number`, `wire_list`, `wire_dict`, `wire_table`

**Sizes (TOKENS.sizes):**
- Buttons: `button_height_sm/md/lg`, `button_width_sm/md/lg`
- Inputs: `input_height_sm/md/lg`, `input_width_sm/md/lg`
- Dialogs: `dialog_width_sm/md/lg/xl`
- Panels: `panel_width_default`, `panel_width_narrow`, `panel_width_wide`
- Toolbar: `toolbar_height`, `toolbar_icon_size`
- Other: `tab_height`, `row_height`, `menu_item_height`, `scrollbar_width`, `checkbox_size`, `border_width`

**Spacing (TOKENS.spacing):**
- `xs(2)`, `sm(4)`, `md(8)`, `lg(12)`, `xl(16)`, `xxl(20)`, `xxxl(32)`
- `form_spacing`, `button_spacing`, `toolbar_spacing`, `grid_spacing`

**Margins (TOKENS.margins):**
- `none`, `tight`, `compact`, `standard`, `comfortable`, `spacious`
- `panel_content`, `panel_header`, `toolbar`, `dialog`, `dialog_header`, `dialog_footer`

**Radii (TOKENS.radii):**
- `none(0)`, `sm(4)`, `md(8)`, `lg(12)`, `xl(20)`, `two_xl(28)`, `full(999)`

**Fonts (TOKENS.fonts):**
- Families: `ui`, `mono`
- Sizes: `size_xs(10)`, `size_sm(11)`, `size_md(12)`, `size_lg(14)`, `xl(16)`, `xxl(20)`, `xxxl(24)`

### Helper Functions

```python
from casare_rpa.presentation.canvas.theme_system import (
    THEME, TOKENS,
    get_wire_color,      # Wire colors by data type
    get_node_status_color,  # Node status colors
    get_status_color,    # General status colors
)

from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_size, set_fixed_width, set_min_width, set_max_width,
    set_margins, set_spacing, set_font,
    margin_none, margin_compact, margin_standard, margin_comfortable,
    set_dialog_size, set_button_size, set_input_size,
)

from casare_rpa.presentation.canvas.theme_system.utils import (
    alpha, darken, lighten, blend,
)
```

---

## Refactoring Template

### Before (Hardcoded)
```python
widget.setStyleSheet(f"""
    background: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 12px;
    color: #ffffff;
""")
widget.setContentsMargins(12, 12, 12, 12)
widget.move(10, 10)
```

### After (THEME + TOKENS)
```python
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import set_margins

widget.setStyleSheet(f"""
    background: {THEME.bg_panel};
    border: 1px solid {THEME.border};
    border-radius: {TOKENS.radii.md}px;
    padding: {TOKENS.spacing.md}px;
    color: {THEME.text_primary};
""")
set_margins(widget.layout(), TOKENS.margins.standard)
widget.move(TOKENS.spacing.xs, TOKENS.spacing.xs)
```

---

## Implementation Order

### Phase 1: Add Missing Tokens (1 day)
1. Add overlay colors to `theme_system/colors.py`
2. Add `TOKENS.spacing.xxs = 2`
3. Add `TOKENS.timing` group for timeouts
4. Add `TOKENS.opacity` group for alpha values

### Phase 2: P0 Files (2-3 days)
1. `graph/style_manager.py`
2. `selectors/unified_selector_dialog.py`
3. `ui/panels/panel_ux_helpers.py`
4. `ui/panels/port_legend_panel.py`
5. `selectors/element_selector_dialog.py`

### Phase 3: P1 Dialogs (1-2 days)
1. `google_oauth_dialog.py`
2. `antigravity_oauth_dialog.py`
3. `credential_manager_dialog.py`
4. `recording_review_dialog.py`

### Phase 4: P1 Panels (1-2 days)
1. `ui/panels/history_tab.py`
2. `ui/panels/log_tab.py`
3. `ui/panels/debug_console_panel.py`

### Phase 5: P2 Files (2-3 days)
1. Graph files (background_cache, custom_pipe, subflow_node_item)
2. Selector files (element_picker, selector_validator)
3. Widget syntax highlighters (4 files)
4. Size/spacing fixes (8 files)

### Phase 6: Validation (1 day)
1. Run anti-pattern scan to verify no remaining hardcoded colors
2. Visual testing of all refactored components
3. Update documentation

---

## New Tokens Required

### Colors (theme_system/colors.py)
```python
class CanvasThemeColors:
    # ... existing ...
    
    # Selection overlays (NEW)
    selection_success_bg = "#1a3d1a"
    selection_error_bg = "#3d1a1a"
    selection_warning_bg = "#3d3a1a"
    selection_info_bg = "#1a2d3d"
    
    # Log backgrounds (NEW)
    log_success_bg = "#1a3d1a"
    log_error_bg = "#3d1a1a"
    log_warning_bg = "#3d3a1a"
    log_info_bg = "#1a2d3d"
    
    # Brand colors (NEW - for OAuth)
    brand_google = "#4285f4"
    brand_google_hover = "#5a95f5"
    brand_google_disabled = "#2d5a9e"
    brand_gemini = "#9C27B0"
    brand_gemini_hover = "#B026B8"
    
    # Overlays (NEW)
    overlay_dark = "rgba(0, 0, 0, 128)"
    overlay_light = "rgba(255, 255, 255, 10)"
```

### Spacing (tokens.py)
```python
class UISpacing:
    xs = 2   # Already exists
    sm = 4   # Already exists
    md = 8   # Already exists
    # ... existing ...
    
    xxs = 2  # Duplicate for clarity, or keep only xs
```

### Timing (NEW - tokens.py)
```python
class UITiming:
    # Status messages
    status_short = 2000
    status_normal = 3000
    status_long = 5000
    
    # Refresh intervals
    refresh_fast = 10000
    refresh_normal = 30000
    refresh_slow = 60000
    
    # Pulse/timer
    pulse_fast = 350
    pulse_normal = 500
```

### Opacity (NEW - tokens.py)
```python
class UIOpacity:
    transparent = 0
    preview = 10
    semi_transparent = 50
    mostly_opaque = 90
    opaque = 100
```

---

## Test Verification Commands

After refactoring, verify with:

```bash
# Find remaining hardcoded colors
rg 'QColor\("#[0-9A-Fa-f]{6}"\)' src/casare_rpa/presentation/canvas/
rg 'QColor\([0-9]{1,3},\s*[0-9]{1,3},\s*[0-9]{1,3}' src/casare_rpa/presentation/canvas/

# Find hardcoded sizes
rg 'setFixedWidth\([0-9]+\)' src/casare_rpa/presentation/canvas/
rg 'setContentsMargins\([0-9,]+\)' src/casare_rpa/presentation/canvas/

# Find files not using THEME
rg 'from theme_system import' src/casare_rpa/presentation/canvas/ -l
```

---

## Files Already Compliant (No Action Needed)

### Graph (Recently Refactored)
- `custom_pipe.py`, `custom_node_item.py`, `custom_port_item.py`
- `custom_widgets.py`, `node_widgets.py`, `minimap.py`
- `node_registry.py`, `port_shapes.py`, `frame_factory.py`
- `focus_ring.py`, `node_frame.py`, `background_cache.py`
- `casare_font.py`, `composite_node_creator.py`, `auto_layout_manager.py`

### UI Widgets
- `toast.py`, `collapsible_section.py`, `validated_input.py`

### Dialogs
- `environment_editor.py`, `fleet_dashboard.py`
- All `fleet_tabs/` files

### Theme System (Reference Files - Intentional)
- `theme_system/colors.py` - Source of truth
- `theme_system/tokens.py` - Source of truth
- `theme_system/helpers.py` - Helper functions
- `theme_system/utils.py` - Color utilities
- `ui/theme.py` - Theme definition
- `ui/icons.py` - Icon color mappings
