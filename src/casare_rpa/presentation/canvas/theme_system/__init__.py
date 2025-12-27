"""
CasareRPA Theme System - Design System 2025.

Unified design tokens and semantic colors for consistent UI styling.

Usage:
    from casare_rpa.presentation.canvas.theme_system import TOKENS, THEME

    # Spacing
    layout.setSpacing(TOKENS.spacing.md)

    # Colors
    widget.setStyleSheet(f"background: {THEME.bg_surface}; color: {THEME.text_primary};")

    # Typography
    font.setPointSize(TOKENS.typography.body)

    # Sizes
    widget.setFixedHeight(TOKENS.sizes.button_md)
"""

# =============================================================================
# CORE EXPORTS - Most commonly used
# =============================================================================

# Design tokens singleton
from .design_tokens import TOKENS

# Theme colors singleton
from .colors import THEME

# =============================================================================
# SECONDARY EXPORTS - For type hints and advanced usage
# =============================================================================

# Token classes (for type hints)
from .design_tokens import (
    DesignTokens,
    Margin,
    NodeTokens,
    Opacity,
    Radius,
    Shadows,
    Sizes,
    Spacing,
    Transitions,
    Typography,
    ZIndex,
)

# Theme class (for type hints)
from .colors import (
    CanvasThemeColors,
    TYPE_COLORS,
    get_canvas_stylesheet,
    get_node_status_color,
    get_status_color,
    get_wire_color,
)

# Widget helpers
from .helpers import (
    margin_compact,
    margin_comfortable,
    margin_dialog,
    margin_none,
    margin_panel,
    margin_standard,
    margin_toolbar,
    set_button_size,
    set_dialog_size,
    set_fixed_height,
    set_fixed_size,
    set_fixed_width,
    set_font,
    set_input_size,
    set_margins,
    set_max_height,
    set_max_size,
    set_max_width,
    set_min_height,
    set_min_size,
    set_min_width,
    set_panel_width,
    set_spacing,
)

# Style generators (for custom stylesheets)
from .styles import (
    ASSETS_DIR,
    CHECKMARK_PATH,
    get_base_widget_styles,
    get_button_styles,
    get_base_stylesheet,
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

# Color utilities
from .utils import (
    alpha,
    blend,
    darken,
    hex_to_rgb,
    lighten,
    rgb_to_hex,
    saturate,
)

__all__ = [
    # Core (most common)
    "TOKENS",
    "THEME",
    # Token classes
    "DesignTokens",
    "Spacing",
    "Margin",
    "Radius",
    "Typography",
    "Sizes",
    "Shadows",
    "ZIndex",
    "Transitions",
    "Opacity",
    "NodeTokens",
    # Theme
    "CanvasThemeColors",
    "TYPE_COLORS",
    "get_canvas_stylesheet",
    "get_node_status_color",
    "get_status_color",
    "get_wire_color",
    # Helpers
    "set_fixed_size",
    "set_fixed_width",
    "set_fixed_height",
    "set_min_size",
    "set_min_width",
    "set_min_height",
    "set_max_size",
    "set_max_width",
    "set_max_height",
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
    # Styles
    "ASSETS_DIR",
    "CHECKMARK_PATH",
    "get_base_widget_styles",
    "get_button_styles",
    "get_checkbox_styles",
    "get_combobox_styles",
    "get_dialog_styles",
    "get_dock_widget_styles",
    "get_groupbox_styles",
    "get_header_view_styles",
    "get_input_styles",
    "get_main_window_styles",
    "get_menu_styles",
    "get_scrollbar_styles",
    "get_spinbox_styles",
    "get_splitter_styles",
    "get_statusbar_styles",
    "get_tab_widget_styles",
    "get_table_styles",
    "get_textedit_styles",
    "get_toolbar_styles",
    "get_tooltip_styles",
    # Utils
    "alpha",
    "blend",
    "lighten",
    "darken",
    "saturate",
    "hex_to_rgb",
    "rgb_to_hex",
]
