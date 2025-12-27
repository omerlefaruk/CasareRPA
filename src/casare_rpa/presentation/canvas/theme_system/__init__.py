"""
Modular Theme System for CasareRPA Canvas.

This package provides a comprehensive theming system with:
- colors.py: Color definitions and color lookup functions
- constants.py: Spacing, sizes, borders, radii constants
- styles.py: Widget-specific QSS generator functions
- utils.py: Color manipulation helpers (darken, lighten, alpha, etc.)
- tokens.py: UI design tokens (sizes, spacing, margins, radii, fonts, transitions)
- helpers.py: Widget application helpers for applying tokens
- stylesheet_cache.py: Disk-based stylesheet cache

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
    dialog_width = TOKENS.sizes.dialog_width_md
    panel_margin = TOKENS.margins.panel_content
"""

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

# Token system imports
from .tokens import (
    TOKENS,
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
    # Token system
    "TOKENS",
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
