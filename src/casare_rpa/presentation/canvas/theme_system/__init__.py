"""
Modular Theme System for CasareRPA Canvas.

This package provides a comprehensive theming system with:
- design_tokens.py: NEW unified design tokens (spacing, radius, sizes, typography, shadows)
- colors.py: Semantic color definitions and color lookup functions
- constants.py: LEGACY - Spacing, sizes, borders, radii constants (deprecated)
- styles.py: Widget-specific QSS generator functions
- utils.py: Color manipulation helpers (darken, lighten, alpha, etc.)
- tokens.py: LEGACY - Old UI tokens (being replaced by design_tokens.py)
- helpers.py: Widget application helpers for applying tokens
- cache.py: Stylesheet cache manager

Migration Guide (OLD -> NEW):
  TOKENS.sizes.button_sm -> TOKENS.sizes.button_sm
  TOKENS.spacing.xs -> TOKENS.spacing.xs (same)
  TOKENS.radius.sm -> TOKENS.radius.sm
  THEME.bg_darkest -> THEME.bg_canvas (semantic)
  THEME.accent_primary -> THEME.primary (semantic)

Usage:
    from casare_rpa.presentation.canvas.theme_system import (
        THEME,
        TOKENS,
        get_canvas_stylesheet,
        get_wire_color,
        get_node_status_color,
        get_status_color,
    )

    # Apply stylesheet
    app.setStyleSheet(get_canvas_stylesheet())

    # Get colors
    wire_color = get_wire_color("string")
    status_color = get_node_status_color("running")

    # Use tokens
    button_height = TOKENS.sizes.button_md
    panel_margin = TOKENS.margin.standard
"""

from .cache import (
    clear_cache as clear_stylesheet_cache,
)
from .cache import (
    get_cache_size,
    get_cached,
    has_cached,
)
from .colors import (
    NODE_STATUS_COLOR_MAP,
    STATUS_COLOR_MAP,
    WIRE_COLOR_MAP,
    CanvasThemeColors,
    get_node_status_color,
    get_status_color,
    get_wire_color,
)
from .constants import (
    BORDERS,
    FONT_SIZE_MAP,
    FONT_SIZES,
    FONTS,
    MONO_FONT,
    RADIUS,
    RADIUS_MAP,
    SIZES,
    SPACING,
    SPACING_MAP,
    UI_FONT,
    UI_FONT_CONDENSED,
    BorderConstants,
    FontConstants,
    FontSizeConstants,
    RadiusConstants,
    SizeConstants,
    SpacingConstants,
)

# NEW Unified Design Tokens (2025)
from .design_tokens import (
    TOKENS,
    DesignTokens,
    Margin,
    Radius,
    Shadows,
    Sizes,
    Spacing,
    Transitions,
    Typography,
    ZIndex,
)

# Helper imports
from .helpers import (
    TOKENS as _helpers_tokens,  # Avoid conflict, re-export main TOKENS
)
from .helpers import (
    margin_comfortable,
    margin_compact,
    margin_dialog,
    margin_none,
    margin_panel,
    margin_standard,
    margin_toolbar,
    set_button_size,
    set_dialog_size,
    set_fixed_size,
    set_font,
    set_input_size,
    set_margins,
    set_max_size,
    set_min_size,
    set_panel_width,
    set_spacing,
)
from .styles import (
    ASSETS_DIR,
    CHECKMARK_PATH,
    get_base_widget_styles,
    get_button_styles,
    get_canvas_stylesheet,
    get_checkbox_styles,
    get_combobox_styles,
    get_dialog_styles,
    get_dock_widget_styles,
    get_groupbox_styles,
    get_header_view_styles,
    get_input_styles,
    get_main_window_styles,
    get_menu_styles,
    get_scrollbar_styles,
    get_spinbox_styles,
    get_splitter_styles,
    get_statusbar_styles,
    get_tab_widget_styles,
    get_table_styles,
    get_textedit_styles,
    get_toolbar_styles,
    get_tooltip_styles,
)

# LEGACY Token system (being replaced)
from .tokens import (
    UIFonts,
    UIMargins,
    UIRadii,
    UISizes,
    UISpacing,
    UITokens,
    UITransition,
)
from .utils import (
    alpha,
    blend,
    contrast_color,
    darken,
    desaturate,
    hex_to_rgb,
    is_valid_hex,
    lighten,
    normalize_hex,
    rgb_to_hex,
    saturate,
)

# Global theme instance - default theme colors
THEME = CanvasThemeColors()


# Convenience wrapper that uses default THEME instance
def get_stylesheet() -> str:
    """
    Generate the main Canvas application stylesheet using default theme.

    Returns:
        Complete QSS stylesheet for the Canvas application.
    """
    return get_canvas_stylesheet(THEME)


__all__ = [
    # Main theme instance
    "THEME",
    # NEW Unified Token System (2025)
    "TOKENS",
    "DesignTokens",
    "Spacing",
    "Margin",
    "Radius",
    "Typography",
    "Sizes",
    "Shadows",
    "ZIndex",
    "Transitions",
    # Legacy Token System (deprecated, use TOKENS above)
    "UITokens",
    "UISizes",
    "UISpacing",
    "UIMargins",
    "UIRadii",
    "UIFonts",
    "UITransition",
    # Colors
    "CanvasThemeColors",
    "get_node_status_color",
    "get_wire_color",
    "get_status_color",
    "NODE_STATUS_COLOR_MAP",
    "STATUS_COLOR_MAP",
    "WIRE_COLOR_MAP",
    # Constants
    "SPACING",
    "BORDERS",
    "RADIUS",
    "FONT_SIZES",
    "SIZES",
    "FONTS",
    "SPACING_MAP",
    "RADIUS_MAP",
    "FONT_SIZE_MAP",
    "UI_FONT",
    "UI_FONT_CONDENSED",
    "MONO_FONT",
    "SpacingConstants",
    "BorderConstants",
    "RadiusConstants",
    "FontSizeConstants",
    "SizeConstants",
    "FontConstants",
    # Cache
    "get_cached",
    "clear_stylesheet_cache",
    "get_cache_size",
    "has_cached",
    # Styles
    "get_canvas_stylesheet",
    "get_stylesheet",
    "get_main_window_styles",
    "get_base_widget_styles",
    "get_menu_styles",
    "get_toolbar_styles",
    "get_statusbar_styles",
    "get_dock_widget_styles",
    "get_tab_widget_styles",
    "get_table_styles",
    "get_header_view_styles",
    "get_scrollbar_styles",
    "get_button_styles",
    "get_input_styles",
    "get_combobox_styles",
    "get_spinbox_styles",
    "get_checkbox_styles",
    "get_splitter_styles",
    "get_groupbox_styles",
    "get_tooltip_styles",
    "get_textedit_styles",
    "get_dialog_styles",
    "ASSETS_DIR",
    "CHECKMARK_PATH",
    # Utils
    "hex_to_rgb",
    "rgb_to_hex",
    "darken",
    "lighten",
    "alpha",
    "blend",
    "contrast_color",
    "is_valid_hex",
    "normalize_hex",
    "saturate",
    "desaturate",
    # Helpers
    "set_fixed_size",
    "set_min_size",
    "set_max_size",
    "set_margins",
    "set_spacing",
    "set_font",
    "margin_none",
    "margin_compact",
    "margin_standard",
    "margin_comfortable",
    "margin_panel",
    "margin_dialog",
    "margin_toolbar",
    "set_dialog_size",
    "set_panel_width",
    "set_button_size",
    "set_input_size",
]
