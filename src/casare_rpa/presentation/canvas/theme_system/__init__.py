"""
CasareRPA Theme System - Design System 2025.

Unified design tokens and semantic colors for consistent UI styling.
Includes font loader for Geist Sans/Mono bundling (Epic 1.2).

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

    # Font registration (call early in app.py before widget creation)
    from casare_rpa.presentation.canvas.theme_system import ensure_font_registered
    ensure_font_registered()
"""

# =============================================================================
# CORE EXPORTS - Most commonly used
# =============================================================================

# Design tokens singleton
# Theme colors singleton
# Theme class (for type hints)
from .colors import (
    THEME,
    TYPE_COLORS,
    CanvasThemeColors,
    Theme,
    get_canvas_stylesheet,
    get_node_status_color,
    get_status_color,
    get_wire_color,
)

# =============================================================================
# SECONDARY EXPORTS - For type hints and advanced usage
# =============================================================================
# Token classes (for type hints)
from .design_tokens import (
    TOKENS,
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

# Font loading and registration
from .font_loader import (
    GEIST_MONO_FAMILY,
    GEIST_SANS_FAMILY,
    ensure_font_registered,
    get_registered_fonts,
)

# Widget helpers (re-exported from theme.helpers via local helpers.py)
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

# Icon provider v2 (Epic 2.1)
from .icons_v2 import (
    IconProviderV2,
    IconSize,
    IconState,
    icon_v2,
)
from .icons_v2 import (
    get_icon as get_icon_v2,
)
from .icons_v2 import (
    get_pixmap as get_pixmap_v2,
)

# Style generators (for custom stylesheets)
from .styles import (
    ASSETS_DIR,
    CHECKMARK_PATH,
    get_base_stylesheet,
    get_base_widget_styles,
    get_button_styles,
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
from .styles_v2 import (
    get_base_widget_styles_v2,
    get_button_styles_v2,
    get_canvas_stylesheet_v2,
    get_checkbox_styles_v2,
    get_combobox_styles_v2,
    get_dialog_styles_v2,
    get_dock_widget_styles_v2,
    get_groupbox_styles_v2,
    get_header_view_styles_v2,
    get_input_styles_v2,
    get_main_window_styles_v2,
    get_menu_styles_v2,
    get_popup_styles_v2,
    get_scrollbar_styles_v2,
    get_spinbox_styles_v2,
    get_splitter_styles_v2,
    get_statusbar_styles_v2,
    get_tab_widget_styles_v2,
    get_table_styles_v2,
    get_textedit_styles_v2,
    get_toolbar_styles_v2,
    get_tooltip_styles_v2,
)


# Style gallery for Epic 1.3 verification (lazy import to avoid circular dependency)
# Primitive gallery for Epic 5.1 Component Library
def __getattr__(name: str):
    """Lazy import for galleries to avoid circular import."""
    if name == "show_style_gallery_v2":
        from .style_gallery import show_style_gallery_v2

        return show_style_gallery_v2
    if name == "show_primitive_gallery_v2":
        from .primitive_gallery import show_primitive_gallery_v2

        return show_primitive_gallery_v2
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# =============================================================================
# V2 EXPORTS - New design system (dark-only, compact)
# =============================================================================
# V2 tokens and theme (parallel to v1, used in new_main_window.py)
from .tokens_v2 import (
    THEME_V2,
    TOKENS_V2,
    AccentRampV2,
    BorderV2,
    DesignTokensV2,
    MarginV2,
    MotionV2,
    NeutralRampV2,
    RadiusV2,
    SemanticColorsV2,
    SizesV2,
    SpacingV2,
    ThemeColorsV2,
    TypographyV2,
    ZIndexV2,
)

# Color utilities (re-exported from theme.utils via local utils.py)
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
    "Theme",  # Legacy compatibility
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
    # Font loading
    "GEIST_SANS_FAMILY",
    "GEIST_MONO_FAMILY",
    "ensure_font_registered",
    "get_registered_fonts",
    # Icon provider v2 (Epic 2.1)
    "IconProviderV2",
    "icon_v2",
    "get_icon_v2",
    "get_pixmap_v2",
    "IconSize",
    "IconState",
    # === V2 EXPORTS ===
    # V2 Tokens
    "TOKENS_V2",
    "THEME_V2",
    "DesignTokensV2",
    "SpacingV2",
    "MarginV2",
    "RadiusV2",
    "TypographyV2",
    "SizesV2",
    "BorderV2",
    "MotionV2",
    "ZIndexV2",
    "NeutralRampV2",
    "AccentRampV2",
    "SemanticColorsV2",
    "ThemeColorsV2",
    # V2 Styles
    "get_canvas_stylesheet_v2",
    "get_main_window_styles_v2",
    "get_base_widget_styles_v2",
    "get_menu_styles_v2",
    "get_toolbar_styles_v2",
    "get_statusbar_styles_v2",
    "get_dock_widget_styles_v2",
    "get_tab_widget_styles_v2",
    "get_table_styles_v2",
    "get_header_view_styles_v2",
    "get_scrollbar_styles_v2",
    "get_button_styles_v2",
    "get_input_styles_v2",
    "get_combobox_styles_v2",
    "get_spinbox_styles_v2",
    "get_checkbox_styles_v2",
    "get_splitter_styles_v2",
    "get_groupbox_styles_v2",
    "get_tooltip_styles_v2",
    "get_textedit_styles_v2",
    "get_dialog_styles_v2",
    "get_popup_styles_v2",
    # Style gallery (Epic 1.3)
    "show_style_gallery_v2",
    # Primitive gallery (Epic 5.1)
    "show_primitive_gallery_v2",
]
