# Theme Refactor Implementation Plan v2

**Date**: 2025-12-27
**Status**: Ready for Execution
**Estimated Time**: 2-3 days for P0 files

---

## Executive Summary

This plan provides exact replacements for refactoring hardcoded colors to THEME tokens. The approach uses Serena's `replace_content` tool with regex patterns for precision.

**Key Changes:**
- Phase 1: Add missing theme tokens to `theme_system/colors.py`
- Phase 2: Fix P0 files in priority order

---

## Phase 1: Add Missing Theme Tokens

### File: `src/casare_rpa/presentation/canvas/theme_system/colors.py`

#### 1.1 Add Selection Overlay Colors (after line ~135)

**Location**: After `accent_error` in `CanvasThemeColors` class

**Add**:
```python
    # Selection overlays (for badges, status indicators)
    selection_success_bg: str = "#1a3d1a"  # Dark green for success badges
    selection_error_bg: str = "#3d1a1a"    # Dark red for error badges
    selection_warning_bg: str = "#3d3a1a"  # Dark amber for warning badges
    selection_info_bg: str = "#1a2d3d"     # Dark blue for info badges
```

#### 1.2 Add Brand Colors for OAuth (after selection overlays)

**Add**:
```python
    # Brand colors (for OAuth providers)
    brand_google: str = "#4285f4"         # Google Blue
    brand_google_hover: str = "#5a95f5"   # Google Blue hover
    brand_gemini: str = "#9C27B0"         # Gemini Purple
    brand_gemini_hover: str = "#B026B8"   # Gemini Purple hover
```

#### 1.3 Add Overlay Colors (after brand colors)

**Add**:
```python
    # Overlays (for modal backgrounds, drop shadows)
    overlay_dark: str = "rgba(0, 0, 0, 128)"  # Semi-transparent black
    overlay_light: str = "rgba(255, 255, 255, 10)"  # Semi-transparent white
```

#### 1.4 Update helper functions at end of file

**Add new helper function** after `get_status_color()`:
```python
def get_selection_overlay_color(status: str, theme: CanvasThemeColors = None) -> str:
    """
    Get background color for selection overlay badges.
    
    Args:
        status: Status type (success, error, warning, info)
        theme: Optional theme instance
    
    Returns:
        Hex color string for the badge background.
    """
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

#### 1.5 Update `CanvasThemeColors` dataclass export in `theme.py`

**Location**: `src/casare_rpa/presentation/canvas/theme.py`

**Add to `__all__` list**:
```python
    "get_selection_overlay_color",
```

---

## Phase 2: P0 Files - Exact Replacements

### File 1: `src/casare_rpa/presentation/canvas/graph/style_manager.py`

**Issue**: Uses `QColor(r,g,b,a)` with `TOKENS.sizes.*` values as RGB channels

**Lines to Replace**:

| Line(s) | Pattern | Replacement |
|---------|---------|-------------|
| 34-48 | `FRAME_COLOR_PALETTE` dict | Delete - unused |
| 51-61 | `FRAME_COLORS` dict | Delete - unused |
| 64-66 | `DEFAULT_FRAME_COLOR`, `DEFAULT_PORT_COLOR` | Replace with THEME colors |

#### Replacement 1: Delete FRAME_COLOR_PALETTE (lines 34-48)

**Old**:
```python
FRAME_COLOR_PALETTE: dict[str, QColor] = {
    "Gray": QColor(TOKENS.sizes.button_min_width, TOKENS.sizes.button_min_width, TOKENS.sizes.button_min_width, TOKENS.sizes.button_min_width),
    ...
}
```

**Action**: Delete entire dict (15 lines)

#### Replacement 2: Delete FRAME_COLORS (lines 51-61)

**Old**:
```python
FRAME_COLORS: dict[str, QColor] = {
    "blue": QColor(TOKENS.sizes.button_width_sm, 181, 246, 60),
    ...
}
```

**Action**: Delete entire dict (11 lines)

#### Replacement 3: Replace DEFAULT_FRAME_COLOR (line 64)

**Old**:
```python
DEFAULT_FRAME_COLOR = QColor(TOKENS.sizes.button_width_sm, TOKENS.sizes.button_min_width, TOKENS.sizes.button_width_sm, TOKENS.sizes.button_min_width)
```

**New**:
```python
DEFAULT_FRAME_COLOR = QColor(THEME.bg_node)
```

#### Replacement 4: Replace DEFAULT_PORT_COLOR (line 66)

**Old**:
```python
DEFAULT_PORT_COLOR = QColor(TOKENS.sizes.button_width_sm, 181, 246)
```

**New**:
```python
DEFAULT_PORT_COLOR = QColor(THEME.wire_data)
```

#### Replacement 5: Update get_frame_color method (lines 76-97)

**Old**:
```python
@staticmethod
def get_frame_color(color_name: str) -> QColor:
    color_name = color_name.lower()
    if lower_name in FRAME_COLORS:
        return FRAME_COLORS[lower_name]
    title_name = color_name.title()
    if title_name in FRAME_COLOR_PALETTE:
        return FRAME_COLOR_PALETTE[title_name]
    return DEFAULT_FRAME_COLOR
```

**New**:
```python
@staticmethod
def get_frame_color(color_name: str) -> QColor:
    """Get frame color by name using theme colors."""
    from casare_rpa.presentation.canvas.ui.theme import Theme
    
    # Map color names to theme wire colors
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
    
    lower_name = color_name.lower()
    if lower_name in color_map:
        return QColor(color_map[lower_name])
    
    return DEFAULT_FRAME_COLOR
```

#### Replacement 6: Replace CollapseButtonStyle colors (lines 145-153)

**Old**:
```python
BACKGROUND_NORMAL = QColor(60, 60, 60, 180)
BACKGROUND_HOVER = QColor(TOKENS.sizes.button_min_width, TOKENS.sizes.button_min_width, TOKENS.sizes.button_min_width, TOKENS.sizes.panel_width_min)
BORDER_COLOR = QColor(TOKENS.sizes.button_width_sm, TOKENS.sizes.button_width_sm, TOKENS.sizes.button_width_sm)
SYMBOL_COLOR = QColor(220, 220, 220)
```

**New**:
```python
BACKGROUND_NORMAL = QColor(THEME.bg_medium)
BACKGROUND_NORMAL.setAlpha(180)
BACKGROUND_HOVER = QColor(THEME.bg_hover)
BORDER_COLOR = QColor(THEME.border)
SYMBOL_COLOR = QColor(THEME.text_primary)
```

---

### File 2: `src/casare_rpa/presentation/canvas/selectors/unified_selector_dialog.py`

**Issue**: Has `accent_color` parameter defaults using hardcoded hex colors

**Lines to Replace**:

| Line | Pattern | Replacement |
|------|---------|-------------|
| ~73 | `accent_color: str = "#60a5fa"` | `accent_color: str = THEME.status_info` |
| ~77 | `self._accent_color = accent_color` | No change (uses parameter) |
| ~246 | `accent_color: str = "#fbbf24"` | `accent_color: str = THEME.status_warning` |
| ~310 | `accent_color: str = "#10b981"` | `accent_color: str = THEME.status_success` |
| ~358 | `accent_color: str = "#3b82f6"` | `accent_color: str = THEME.status_info` |
| ~386 | `accent_color: str = "#f59e0b"` | `accent_color: str = THEME.status_warning` |
| ~421 | `accent_color: str = "#8b5cf6"` | `accent_color: str = THEME.wire_list` |
| ~463 | `accent_color: str = "#ec4899"` | `accent_color: str = THEME.node_skipped` |
| ~582 | `accent_color: str = "#60a5fa"` | `accent_color: str = THEME.status_info` |

#### Replacement Pattern (regex):

```python
# Find all occurrences
accent_color: str = "#[0-9a-fA-F]{6}"

# Replace with
accent_color: str = THEME.status_info  # or appropriate THEME color
```

**Specific replacements**:

1. Line 73 (CollapsibleSection default):
   - `"#60a5fa"` → `THEME.status_info`

2. Line 246 (Anchor section):
   - `"#fbbf24"` → `THEME.status_warning`

3. Line 310 (Target section):
   - `"#10b981"` → `THEME.status_success`

4. Line 358 (Strict selector):
   - `"#3b82f6"` → `THEME.status_info`

5. Line 386 (Fuzzy selector):
   - `"#f59e0b"` → `THEME.status_warning`

6. Line 421 (CV selector):
   - `"#8b5cf6"` → `THEME.wire_list`

7. Line 463 (Image selector):
   - `"#ec4899"` → `THEME.node_skipped`

8. Line 582 (Strategies section):
   - `"#60a5fa"` → `THEME.status_info`

---

### File 3: `src/casare_rpa/presentation/canvas/ui/panels/panel_ux_helpers.py`

**Issue**: `TYPE_COLORS` dict has hardcoded colors for syntax highlighting

**Decision Point**: Should TYPE_COLORS use syntax colors (VSCode style) or wire colors?

**Analysis**: 
- `TYPE_COLORS` is used for variable type badges in `VariablesTableWidget`
- Current colors: `#4ec9b0` (String), `#b5cea8` (Integer), etc.
- These are data visualization colors, NOT UI theme colors
- Similar colors exist in `ui/theme.py` as `TYPE_COLORS` (line 292)

**Decision**: Keep as data visualization colors (they serve different purpose than UI theme)
- BUT: Document clearly that these are SYNTAX HIGHLIGHTING colors, not UI colors
- Consider renaming to `SYNTAX_TYPE_COLORS` for clarity

**Action**: Add comment header to clarify purpose:

**Add after line 52**:
```python
# TYPE COLORS: Syntax highlighting colors for variable type badges
# NOTE: These are data visualization colors (VSCode Dark+ syntax style),
# NOT UI theme colors. They should remain distinct from THEME.wire_* colors
# which are for connection wires in the node graph.
TYPE_COLORS = {  # syntax highlighting colors - not UI theme colors
```

**Alternative**: If full refactor is desired:
```python
# Import syntax colors from theme
from casare_rpa.presentation.canvas.theme_system.colors import (
    syntax_string, syntax_number, syntax_boolean, etc.
)
```

**Recommendation**: Add documentation comment only (no code change)

---

### File 4: `src/casare_rpa/presentation/canvas/ui/panels/port_legend_panel.py`

**Issue**: `LEGEND_ENTRIES` has hardcoded hex colors and `{THEME.*}` placeholders

**Lines 34-43**:

**Old**:
```python
LEGEND_ENTRIES: list[tuple[str, str, str, str]] = [
    ("", "Execution", "{THEME.text_primary}", "Control flow between nodes"),
    ("", "String", "#FFC107", "Text data"),
    ("", "Integer", "{THEME.status_success}", "Whole numbers"),
    ("", "Float", "#8BC34A", "Decimal numbers"),
    ("", "Boolean", "#9C27B0", "True/False values"),
    ("", "List", "{THEME.status_warning}", "Array of values"),
    ("", "Dict", "{THEME.status_error}", "Key-value mapping"),
    ("", "Page", "{THEME.status_info}", "Browser page"),
    ("", "Element", "#00BCD4", "Web element"),
    ("", "Any", "#969696", "Wildcard type"),
]
```

**Problem**: This file already uses `get_port_type_registry()` for colors at runtime. The `LEGEND_ENTRIES` is only used as fallback/data structure.

**Analysis**: The actual colors come from `registry.get_type_color(data_type)` in `LegendRow.__init__()` (line 143-144).

**Action**: The hardcoded colors in LEGEND_ENTRIES are NEVER used. Remove them or update to be consistent:

**Option 1**: Remove color column (not used)
```python
LEGEND_ENTRIES: list[tuple[str, str, str]] = [
    ("Execution", "Control flow between nodes"),
    ("String", "Text data"),
    ("Integer", "Whole numbers"),
    # ...
]
```

**Option 2**: Use THEME colors for consistency
```python
LEGEND_ENTRIES: list[tuple[str, str, str, str]] = [
    ("Execution", THEME.text_primary, "Control flow between nodes"),
    ("String", THEME.wire_string, "Text data"),
    ("Integer", THEME.wire_number, "Whole numbers"),
    ("Float", THEME.wire_number, "Decimal numbers"),
    ("Boolean", THEME.wire_bool, "True/False values"),
    ("List", THEME.wire_list, "Array of values"),
    ("Dict", THEME.wire_dict, "Key-value mapping"),
    ("Page", THEME.status_info, "Browser page"),
    ("Element", THEME.wire_list, "Web element"),
    ("Any", THEME.text_secondary, "Wildcard type"),
]
```

**Recommendation**: Option 2 - Use THEME colors for consistency

---

### File 5: `src/casare_rpa/presentation/canvas/selectors/element_selector_dialog.py`

**Issue**: Uses `QColor(0,0,0,128)` for overlay

**Search**: Find the line with overlay color

**Replacement**:
```python
# Old
QColor(0, 0, 0, 128)

# New
QColor(THEME.bg_darkest).setAlpha(128)
# Or use get_selection_overlay_color() if applicable
```

---

## Phase 3: Verification

### Test Commands

```bash
# Find remaining hardcoded QColor with RGB
rg 'QColor\([0-9]{1,3},\s*[0-9]{1,3},\s*[0-9]{1,3}' src/casare_rpa/presentation/canvas/ --type py

# Find hardcoded hex colors in string positions that look like color params
rg '"#[0-9A-Fa-f]{6}"' src/casare_rpa/presentation/canvas/ --type py

# Verify THEME imports
rg 'from.*theme import THEME' src/casare_rpa/presentation/canvas/ --type py -l
```

### Visual Testing Checklist

- [ ] Frame colors render correctly with theme colors
- [ ] Selector dialog accent colors match status types
- [ ] Port legend colors match wire colors
- [ ] Selection badges use correct background colors
- [ ] No broken styling after refactor

---

## Appendix: Complete Token Reference

### CanvasThemeColors (theme_system/colors.py)

```python
# Backgrounds
bg_darkest, bg_dark, bg_medium, bg_light, bg_lighter
bg_panel, bg_header, bg_hover, bg_selected
bg_canvas, bg_node, bg_node_selected, bg_node_header

# Borders
border_dark, border, border_light, border_focus

# Text
text_primary, text_secondary, text_muted, text_disabled, text_header

# Status
status_success, status_warning, status_error, status_info
status_running, status_idle

# Node Status
node_idle, node_running, node_success, node_error, node_skipped, node_breakpoint

# Selection (NEW to add)
selection_success_bg, selection_error_bg, selection_warning_bg, selection_info_bg

# Brand (NEW to add)
brand_google, brand_google_hover, brand_gemini, brand_gemini_hover

# Overlays (NEW to add)
overlay_dark, overlay_light

# Accent
accent_primary, accent_secondary, accent_hover
accent_success, accent_warning, accent_error

# Wires
wire_exec, wire_data, wire_bool, wire_string, wire_number
wire_list, wire_dict, wire_table
```

### Helper Functions

```python
get_wire_color(data_type, theme=None) -> str
get_node_status_color(status, theme=None) -> str
get_status_color(status, theme=None) -> str
get_selection_overlay_color(status, theme=None) -> str  # NEW
```

---

## Implementation Order Summary

1. **Add tokens to colors.py** (30 min)
   - Selection overlay colors
   - Brand colors
   - Overlay colors
   - Helper function

2. **Fix style_manager.py** (45 min)
   - Delete unused FRAME_COLOR_PALETTE
   - Delete unused FRAME_COLORS
   - Replace DEFAULT_FRAME_COLOR
   - Replace DEFAULT_PORT_COLOR
   - Update get_frame_color()
   - Update CollapseButtonStyle

3. **Fix unified_selector_dialog.py** (30 min)
   - Replace 8 `accent_color` default values

4. **Fix panel_ux_helpers.py** (15 min)
   - Add documentation comment

5. **Fix port_legend_panel.py** (15 min)
   - Update LEGEND_ENTRIES with THEME colors

6. **Verification** (30 min)
   - Run test commands
   - Visual testing
   - Update documentation

**Total Time**: ~3 hours

---

## Notes

- All changes maintain backward compatibility
- THEME re-exports from theme_system for easy access
- Use `from casare_rpa.presentation.canvas.theme import THEME` for imports
- Wire colors in `CanvasThemeColors` match theme.py wire colors
