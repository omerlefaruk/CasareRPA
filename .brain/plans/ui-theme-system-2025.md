# Unified Theme System Architecture 2025

**Date**: 2025-12-26
**Status**: DESIGN PHASE
**Scope**: Single source of truth for ALL UI values (sizes, spacing, colors, radii, fonts, margins)

---

## Current State Analysis

### Hardcoded Values Discovered

| Category | Count | Examples |
|----------|-------|----------|
| **setFixedSize** | 150+ | `setFixedSize(200, 300)`, `setFixedSize(120, 28)` |
| **setMinimumSize** | 50+ | `setMinimumSize(300, 200)`, `setMinimumSize(100, 100)` |
| **resize** | 25+ | `resize(800, 600)`, `resize(400, 500)` |
| **setContentsMargins** | 200+ | `setContentsMargins(8, 8, 8, 8)`, `setContentsMargins(12, 0, 12, 0)` |
| **setSpacing** | 104+ | `setSpacing(8)`, `setSpacing(4)` |
| **Hardcoded colors** | 400+ | `"#1E1E1E"`, `QColor(30, 30, 30)`, `"white"` |

### UI Components Affected

- **630+** components across presentation layer
- **150+** dialog/window size definitions
- **200+** layout margin definitions
- **400+** hardcoded color values

---

## Architecture Overview

### Single Source of Truth

```
presentation/canvas/theme_system/
├── __init__.py              # Main entry point - re-exports
├── tokens.py                # NEW: All frozen dataclass tokens
├── colors.py                # Existing: Color definitions
├── styles.py                # Existing: QSS generators
├── constants.py             # Existing: Basic constants
├── utils.py                 # Existing: Color manipulation
├── helpers.py               # NEW: Helper functions for widgets
└── cache.py                 # NEW: Stylesheet cache manager
```

### Design Principles

1. **Frozen Dataclasses**: All tokens are immutable frozen dataclasses
2. **Type Safety**: Complete type hints on all properties
3. **Performance**: Stylesheet caching, lazy evaluation
4. **Modular**: Components can override base tokens
5. **Migration Path**: Gradual refactoring with backward compatibility

---

## Dataclass Definitions

### 1. UISizes - Widget Dimensions

```python
@dataclass(frozen=True)
class UISizes:
    """
    Standard widget sizes in pixels.

    All setFixedSize(), setMinimumSize(), resize() values
    should reference these constants.
    """

    # Button heights (width varies by content)
    button_height_sm: int = 24   # Compact toolbar buttons
    button_height_md: int = 28   # Standard buttons
    button_height_lg: int = 32   # Primary dialog actions
    button_min_width: int = 80   # Minimum button width
    button_padding_h: int = 16   # Horizontal padding

    # Input field sizes
    input_height_sm: int = 24    # Compact inputs
    input_height_md: int = 28    # Standard inputs
    input_height_lg: int = 36    # Large inputs
    input_min_width: int = 120   # Minimum input width
    input_max_width: int = 400   # Maximum input width

    # Icon sizes
    icon_xs: int = 12
    icon_sm: int = 16
    icon_md: int = 20
    icon_lg: int = 24
    icon_xl: int = 32

    # Dialog sizes
    dialog_width_sm: int = 400
    dialog_width_md: int = 600
    dialog_width_lg: int = 800
    dialog_width_xl: int = 1000
    dialog_height_sm: int = 300
    dialog_height_md: int = 500
    dialog_height_lg: int = 700

    # Panel sizes (dock widgets)
    panel_width_min: int = 200
    panel_width_default: int = 300
    panel_width_max: int = 600

    # Sidebar/Navigator sizes
    sidebar_width_min: int = 150
    sidebar_width_default: int = 250
    sidebar_width_max: int = 400

    # Node editor sizes
    node_width_min: int = 100
    node_width_default: int = 180
    node_port_spacing: int = 20
    node_header_height: int = 32

    # Status bar
    statusbar_height: int = 24

    # Toolbar
    toolbar_height: int = 40
    toolbar_icon_size: int = 24

    # Tab bar
    tab_min_width: int = 100
    tab_height: int = 36

    # Table/List row height
    row_height: int = 32
    row_height_compact: int = 24

    # Menus
    menu_item_height: int = 28
    menu_min_width: int = 200

    # Scrollbar
    scrollbar_width: int = 10
    scrollbar_min_handle: int = 40

    # Splitter handle
    splitter_handle: int = 4

    # Checkbox/Radio
    checkbox_size: int = 18
    radio_size: int = 18

    # Combo box
    combo_height: int = 28
    combo_dropdown_width: int = 24

    # Spinbox
    spinbox_height: int = 28
    spinbox_button_width: int = 20

    # Slider
    slider_height: int = 20
    slider_handle_size: int = 16

    # Progress bar
    progress_height: int = 18

    # Tooltip
    tooltip_max_width: int = 300

    # Badge
    badge_width: int = 16
    badge_height: int = 16

    # Specialized widget sizes
    variable_button_width: int = 24
    variable_button_height: int = 20

    expression_editor_height: int = 120
    property_panel_width: int = 320

    # Window sizes
    window_min_width: int = 800
    window_min_height: int = 600
    window_default_width: int = 1200
    window_default_height: int = 800
```

### 2. UISpacing - Layout Spacing

```python
@dataclass(frozen=True)
class UISpacing:
    """
    Layout spacing values in pixels.

    All setSpacing(), layout spacing values
    should reference these constants.
    """

    # Spacing scale
    xs: int = 2     # Tight spacing
    sm: int = 4     # Compact spacing
    md: int = 8     # Default spacing
    lg: int = 12    # Relaxed spacing
    xl: int = 16    # Spacious spacing
    xxl: int = 24   # Extra spacious
    xxxl: int = 32  # Maximum spacing

    # Layout-specific spacing
    form_spacing: int = 12          # Form row spacing
    button_spacing: int = 8         # Button group spacing
    toolbar_spacing: int = 4        # Toolbar item spacing
    tab_spacing: int = 4            # Tab spacing
    menu_spacing: int = 0           # Menu item spacing
    table_spacing: int = 0          # Table cell spacing
    grid_spacing: int = 8           # Grid layout spacing
    splitter_spacing: int = 0       # Splitter spacing

    # Component internal spacing
    checkbox_label_spacing: int = 8
    radio_label_spacing: int = 8
    button_icon_text_spacing: int = 6
    menu_icon_text_spacing: int = 12
    table_header_spacing: int = 4
    panel_content_spacing: int = 12
```

### 3. UIMargins - Margin Presets

```python
@dataclass(frozen=True)
class UIMargins:
    """
    Margin presets in pixels.

    All setContentsMargins() values should use these presets.
    Returns tuple of (left, top, right, bottom).
    """

    # Preset margins
    none: tuple[int, int, int, int] = (0, 0, 0, 0)
    tight: tuple[int, int, int, int] = (4, 4, 4, 4)
    compact: tuple[int, int, int, int] = (8, 8, 8, 8)
    standard: tuple[int, int, int, int] = (12, 12, 12, 12)
    comfortable: tuple[int, int, int, int] = (16, 16, 16, 16)
    spacious: tuple[int, int, int, int] = (24, 24, 24, 24)

    # Component-specific margins
    panel_content: tuple[int, int, int, int] = (12, 12, 12, 12)
    panel_header: tuple[int, int, int, int] = (12, 8, 12, 8)
    toolbar: tuple[int, int, int, int] = (8, 4, 8, 4)
    dialog: tuple[int, int, int, int] = (16, 16, 16, 16)
    dialog_header: tuple[int, int, int, int] = (16, 12, 16, 8)
    dialog_footer: tuple[int, int, int, int] = (16, 12, 16, 12)
    form_row: tuple[int, int, int, int] = (0, 4, 0, 4)
    button_group: tuple[int, int, int, int] = (4, 4, 4, 4)
    menu_item: tuple[int, int, int, int] = (12, 6, 12, 6)
    table_cell: tuple[int, int, int, int] = (8, 4, 8, 4)
    table_header: tuple[int, int, int, int] = (10, 8, 10, 8)
    tab_content: tuple[int, int, int, int] = (12, 12, 12, 12)
    dock_widget: tuple[int, int, int, int] = (0, 0, 0, 0)
    statusbar: tuple[int, int, int, int] = (8, 2, 8, 2)
    sidebar: tuple[int, int, int, int] = (0, 8, 0, 8)
    property_item: tuple[int, int, int, int] = (4, 6, 4, 6)

    # Asymmetric margins for specific layouts
    input_horizontal: tuple[int, int, int, int] = (10, 6, 10, 6)
    button_horizontal: tuple[int, int, int, int] = (12, 6, 12, 6)
    header_bottom: tuple[int, int, int, int] = (0, 0, 0, 8)
    footer_top: tuple[int, int, int, int] = (0, 8, 0, 0)
```

### 4. UIRadii - Border Radius Values

```python
@dataclass(frozen=True)
class UIRadii:
    """
    Border radius values in pixels.

    All border-radius CSS values should use these constants.
    """

    none: int = 0        # No rounding
    sm: int = 4          # Small elements (buttons, inputs)
    md: int = 8          # Default radius (cards, panels)
    lg: int = 12         # Large radius (large cards)
    xl: int = 20         # Extra large radius
    two_xl: int = 28     # Dialog radius
    full: int = 999      # Pill shape (badges, tags)

    # Component-specific radii
    button: int = 4
    input: int = 4
    menu: int = 6
    menu_item: int = 4
    dialog: int = 8
    panel: int = 4
    tooltip: int = 4
    badge: int = 999
    tag: int = 4
    popover: int = 8
```

### 5. UIFonts - Font Sizes and Families

```python
@dataclass(frozen=True)
class UIFonts:
    """
    Font sizes and families.
    """

    # Font families
    ui: str = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    mono: str = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"

    # Font sizes (points)
    xs: int = 10      # Tiny labels, captions
    sm: int = 11      # Secondary text, metadata
    md: int = 12      # Default body text
    lg: int = 14      # Emphasized text, subheadings
    xl: int = 16      # Headings, titles
    xxl: int = 20     # Large headings
    xxxl: int = 24    # Display headings

    # Component-specific sizes
    button: int = 12
    input: int = 12
    menu: int = 13
    table: int = 12
    table_header: int = 11
    statusbar: int = 11
    tooltip: int = 11
    dialog_title: int = 16
    dialog_message: int = 12
    node_title: int = 12
    node_port: int = 11
    code: int = 11
    log: int = 10
```

### 6. UITransition - Animation Durations

```python
@dataclass(frozen=True)
class UITransition:
    """
    Animation durations in milliseconds.
    """

    instant: int = 50    # Button press, immediate feedback
    fast: int = 100      # Hover effects
    normal: int = 150    # Standard fade/slide
    medium: int = 200    # Panel transitions
    slow: int = 300      # Modal dialogs
    emphasis: int = 400  # Attention effects (shake, pulse)

    # Specific animations
    hover: int = 100
    focus: int = 150
    appear: int = 200
    disappear: int = 150
    slide: int = 200
    fade: int = 150
```

### 7. Combined UITokens Dataclass

```python
@dataclass(frozen=True)
class UITokens:
    """
    Unified UI tokens - single entry point for all theme values.

    Usage:
        from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

        # Access any token
        width = TOKENS.sizes.dialog_width_md
        margin = TOKENS.margins.panel_content
        spacing = TOKENS.spacing.md
    """

    sizes: UISizes = field(default_factory=UISizes)
    spacing: UISpacing = field(default_factory=UISpacing)
    margins: UIMargins = field(default_factory=UIMargins)
    radii: UIRadii = field(default_factory=UIRadii)
    fonts: UIFonts = field(default_factory=UIFonts)
    transitions: UITransition = field(default_factory=UITransition)


# Global singleton
TOKENS = UITokens()
```

---

## StyleSheet System

### Base StyleSheet Generators

```python
class StyleSheetBuilder:
    """
    Helper class for building styled widgets with theme tokens.

    Caches generated stylesheets for performance.
    """

    _cache: dict[str, str] = {}

    @classmethod
    def button(cls, variant: str = "default", size: str = "md") -> str:
        """
        Generate button stylesheet.

        Args:
            variant: "default", "primary", "danger", "ghost"
            size: "sm", "md", "lg"
        """

    @classmethod
    def input(cls, size: str = "md") -> str:
        """Generate input stylesheet."""

    @classmethod
    def panel(cls) -> str:
        """Generate panel/card stylesheet."""

    @classmethod
    def dialog(cls) -> str:
        """Generate dialog stylesheet."""

    @classmethod
    def menu(cls) -> str:
        """Generate context menu stylesheet."""

    @classmethod
    def table(cls) -> str:
        """Generate table stylesheet."""

    @classmethod
    def tooltip(cls) -> str:
        """Generate tooltip stylesheet."""

    @classmethod
    def clear_cache(cls) -> None:
        """Clear stylesheet cache."""
```

### Override Pattern

```python
class ComponentTokens:
    """
    Base class for component-specific token overrides.

    Components can extend base tokens by subclassing:
    """

    def __init__(self, base: UITokens = TOKENS):
        self._base = base

    @property
    def sizes(self) -> UISizes:
        return self._base.sizes

    def override_sizes(self, **overrides) -> UISizes:
        """Create new UISizes with overridden values."""
        return dataclasses.replace(self.sizes, **overrides)


# Example: Custom dialog with larger size
class MyDialogTokens(ComponentTokens):
    """Custom tokens for MyDialog."""

    @property
    def sizes(self) -> UISizes:
        # Override dialog width
        base = self._base.sizes
        return dataclasses.replace(
            base,
            dialog_width_md=800,  # Wider than default (600)
        )
```

---

## Helper Functions

### Widget Application Helpers

```python
# tokens.py helpers

def apply_size(widget: QWidget, width: int, height: int | None = None) -> None:
    """
    Apply themed size to widget.

    Usage:
        apply_size(button, TOKENS.sizes.button_width_md, TOKENS.sizes.button_height_md)
        # Or simpler:
        set_size(button, TOKENS.sizes.button_height_md)  # width auto
    """

def set_fixed_size(widget: QWidget, width: int, height: int) -> None:
    """Wrapper for setFixedSize with theme tokens."""

def set_min_size(widget: QWidget, width: int, height: int) -> None:
    """Wrapper for setMinimumSize with theme tokens."""

def set_max_size(widget: QWidget, width: int, height: int) -> None:
    """Wrapper for setMaximumSize with theme tokens."""

def set_margins(layout: QLayout, margins: tuple[int, int, int, int]) -> None:
    """Apply themed margins to layout.

    Usage:
        set_margins(layout, TOKENS.margins.panel_content)
        # Or:
        layout.setContentsMargins(*TOKENS.margins.panel_content)
    """

def set_spacing(layout: QLayout, spacing: int) -> None:
    """Apply themed spacing to layout.

    Usage:
        set_spacing(layout, TOKENS.spacing.md)
        # Or:
        layout.setSpacing(TOKENS.spacing.md)
    """

def set_font(widget: QWidget, size: int, family: str | None = None) -> None:
    """Apply themed font to widget.

    Usage:
        set_font(label, TOKENS.fonts.lg, TOKENS.fonts.ui)
    """

def style_widget(widget: QWidget, stylesheet: str) -> None:
    """Apply stylesheet with color token substitution.

    Usage:
        style_widget(button, get_button_style())
    """
```

### Convenience Functions

```python
# Quick size setters
def set_dialog_size(dialog: QDialog, size: str = "md") -> None:
    """Set dialog size from preset."""

def set_panel_size(panel: QDockWidget, width: int | None = None) -> None:
    """Set panel width from theme."""

def set_button_size(button: QPushButton, size: str = "md") -> None:
    """Set button height from preset."""

def set_input_size(input: QLineEdit, size: str = "md") -> None:
    """Set input height from preset."""

# Quick margin setters
def margin_none(layout: QLayout) -> None:
    """layout.setContentsMargins(0, 0, 0, 0)"""

def margin_compact(layout: QLayout) -> None:
    """layout.setContentsMargins(8, 8, 8, 8)"""

def margin_standard(layout: QLayout) -> None:
    """layout.setContentsMargins(12, 12, 12, 12)"""

def margin_panel(layout: QLayout) -> None:
    """layout.setContentsMargins(*TOKENS.margins.panel_content)"""
```

---

## File Structure

### New Files to Create

```
presentation/canvas/theme_system/
├── tokens.py              # NEW: All size/spacing/margin dataclasses
├── helpers.py             # NEW: Widget application helpers
├── cache.py               # NEW: Stylesheet cache manager
└── styles/                # NEW: Component style modules
    ├── __init__.py
    ├── button.py
    ├── input.py
    ├── dialog.py
    ├── table.py
    └── ...
```

### Updated Files

```
presentation/canvas/theme_system/
├── __init__.py            # UPDATE: Re-export TOKENS, helpers
├── colors.py              # KEEP: As-is (already unified)
├── styles.py              # KEEP: As-is (already refactored)
├── constants.py           # MERGE: Into tokens.py
└── utils.py               # KEEP: As-is (color manipulation)
```

---

## Example Before/After Code

### Before: Hardcoded Values

```python
class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(600, 500)  # Hardcoded!
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #1E1E1E;
                border: 1px solid #3E3E42;
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)  # Hardcoded!
        layout.setSpacing(12)  # Hardcoded!

        button = QPushButton("Save")
        button.setFixedSize(80, 32)  # Hardcoded!
```

### After: Themed Values

```python
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_size, set_margins, set_spacing, set_button_size
)
from casare_rpa.presentation.canvas.theme import THEME

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        set_fixed_size(self, TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_md)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.dialog}px;
            }}
        """)

        layout = QVBoxLayout()
        set_margins(layout, TOKENS.margins.dialog)
        set_spacing(layout, TOKENS.spacing.form)

        button = QPushButton("Save")
        set_button_size(button, "lg")  # Uses theme height
```

### Alternative: Fluent API

```python
from casare_rpa.presentation.canvas.theme_system import apply_theme

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        # Fluent API applies all theme values at once
        apply_theme.dialog(self, size="md")
        apply_theme.margins(self.layout(), "dialog")
        apply_theme.spacing(self.layout(), "form")

        button = QPushButton("Save")
        apply_theme.button_size(button, "lg")
```

---

## Migration Strategy

### Phase 1: Core Infrastructure (Week 1)

1. Create `tokens.py` with all dataclass definitions
2. Create `helpers.py` with helper functions
3. Create `cache.py` for stylesheet caching
4. Update `theme_system/__init__.py` to re-exports
5. Write unit tests for all dataclasses

### Phase 2: High-Impact Components (Week 2-3)

Priority order by impact:

1. **Dialogs** (~50 files)
   - `ui/dialogs/*.py`
   - Replace setFixedSize, setContentsMargins
   - Examples: `BaseDialog`, `ConfirmDialog`, `InputDialog`

2. **Panels** (~30 files)
   - `panels/*.py`
   - Replace panel widths, margins
   - Examples: `PropertiesPanel`, `NavigatorPanel`, `LogPanel`

3. **Buttons/Inputs** (~100 files)
   - Replace button heights, input sizes
   - Common across all widgets

4. **Tables/Lists** (~40 files)
   - Replace row heights, cell margins
   - Examples: `NodeTable`, `VariableTable`

5. **Nodes** (~200 files)
   - Replace node widths, port spacing
   - Examples: `BaseVisualNode`, node widgets

### Phase 3: Remaining Components (Week 4)

6. **Menus/Context Menus** (~20 files)
7. **Toolbars** (~15 files)
8. **Status Bar** (~5 files)
9. **Specialized Widgets** (~170 files)

### Phase 4: Validation & Cleanup (Week 5)

1. Run full visual regression test
2. Search for remaining hardcoded values
3. Update documentation
4. Remove deprecated constants from `constants.py`

---

## Search Patterns for Migration

### Finding Hardcoded Sizes

```bash
# Find all setFixedSize calls
rg "setFixedSize\(" src/casare_rpa/presentation/

# Find all setMinimumSize calls
rg "setMinimumSize\(" src/casare_rpa/presentation/

# Find all resize calls
rg "\.resize\(" src/casare_rpa/presentation/

# Find specific size patterns
rg "\b(600|500|400|300|200|100|800|1000|1200)\b" src/casare_rpa/presentation/
```

### Finding Hardcoded Margins

```bash
# Find setContentsMargins
rg "setContentsMargins\(" src/casare_rpa/presentation/

# Find setSpacing
rg "setSpacing\(" src/casare_rpa/presentation/
```

### Finding Hardcoded Colors

```bash
# Find hex colors
rg "#[0-9A-Fa-f]{6}" src/casare_rpa/presentation/

# Find QColor construction
rg "QColor\(" src/casare_rpa/presentation/

# Find color names
rg "(white|black|red|blue|green)" src/casare_rpa/presentation/
```

---

## Validation Checklist

### Pre-Migration

- [ ] All dataclasses have frozen=True
- [ ] All properties have type hints
- [ ] All default values are documented
- [ ] Unit tests for helper functions
- [ ] Documentation complete

### Post-Migration (Per File)

- [ ] No hardcoded sizes remain
- [ ] No hardcoded margins remain
- [ ] No hardcoded colors remain (use THEME)
- [ ] Widget renders correctly
- [ ] Widget is responsive to theme changes

### Integration Testing

- [ ] Canvas loads without errors
- [ ] All dialogs open at correct sizes
- [ ] All panels have correct margins
- [ ] All buttons have correct heights
- [ ] All tables have correct row heights
- [ ] Resizing behavior works correctly
- [ ] Visual regression tests pass

---

## Performance Considerations

### Caching Strategy

1. **StyleSheet Cache**: Module-level cache for generated stylesheets
2. **QColor Cache**: Already implemented in `colors.py`
3. **Lazy Evaluation**: Tokens only created when accessed

### Memory Impact

- Frozen dataclasses are lightweight (~200 bytes per instance)
- Global singleton `TOKENS` = one instance
- StyleSheet cache = ~50KB typical

---

## Documentation Updates

### Files to Update

1. `.brain/docs/ui-standards.md` - Add token usage examples
2. `.claude/rules/ui/theme-rules.md` - Update to reference TOKENS
3. `src/casare_rpa/presentation/canvas/_index.md` - Add tokens section
4. `CLAUDE.md` - Add migration guide

### New Documentation

1. `.brain/docs/ui-tokens.md` - Complete token reference
2. `.brain/docs/ui-migration.md` - Step-by-step migration guide

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Hardcoded sizes | 150+ | 0 | 100% |
| Hardcoded margins | 200+ | 0 | 100% |
| Hardcoded colors | 400+ | 0 | 100% |
| Token coverage | 0% | 95% | >90% |
| Files migrated | 0 | 630 | 100% |

---

## Open Questions

1. **Should we support light theme?**
   - Current design assumes dark only
   - Could extend `UITokens` with `light_mode: UITokens | None`

2. **Should tokens be runtime configurable?**
   - Frozen dataclasses prevent modification
   - Could use `dataclasses.replace()` for overrides

3. **Should we create a fluent API?**
   - Alternative: `apply_theme.dialog(widget, size="md")`
   - Trade-off: More code vs better readability

4. **How to handle dynamic sizing?**
   - Some widgets need computed sizes
   - Could add helper functions for common patterns

---

## Next Steps

1. **Review this plan** - Approve design before implementation
2. **Create worktree** - `python scripts/create_worktree.py "ui-theme-system"`
3. **Implement Phase 1** - Core infrastructure
4. **Test Phase 1** - Unit tests pass
5. **Implement Phase 2** - Migrate high-impact components
6. **Test Phase 2** - Visual regression
7. **Complete remaining phases**
8. **Final validation**
9. **Update documentation**

---

*Generated: 2025-12-26*
*Status: DRAFT - Awaiting Approval*
*Estimated Effort: 4-5 weeks*
*Files Modified: ~630*
*Lines Added: ~2000*
*Lines Removed: ~500 (hardcoded values)*
