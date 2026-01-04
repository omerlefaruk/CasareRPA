"""
CasareRPA Canvas Theme (v2-only).

Design System 2025 (Cursor/VS Code-like dark theme).

Most call sites should use:
    from casare_rpa.presentation.canvas.theme import THEME, TOKENS
or:
    from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
"""

from __future__ import annotations

# =============================================================================
# Core: v2 tokens + colors
# =============================================================================
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
    get_node_status_color,
    get_status_color,
    get_wire_color,
)

# Default exports used across the codebase
THEME = THEME_V2
TOKENS = TOKENS_V2

# =============================================================================
# Utilities
# =============================================================================

# =============================================================================
# Fonts (Epic 1.2)
# =============================================================================
from .font_loader import (
    GEIST_MONO_FAMILY,
    GEIST_SANS_FAMILY,
    ensure_font_registered,
    get_registered_fonts,
)

# =============================================================================
# Widget helpers
# =============================================================================
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

# =============================================================================
# Icons (Epic 2.1)
# =============================================================================
from .icons_v2 import IconProviderV2, IconSize, IconState, get_icon, get_pixmap, icon_v2

# =============================================================================
# Stylesheets (v2)
# =============================================================================
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
from .utils import alpha, blend, darken, hex_to_rgb, lighten, rgb_to_hex, saturate


def __getattr__(name: str):
    """Lazy import for galleries to avoid circular imports."""
    if name == "show_style_gallery_v2":
        from .style_gallery import show_style_gallery_v2

        return show_style_gallery_v2
    if name == "show_primitive_gallery_v2":
        from .primitive_gallery import show_primitive_gallery_v2

        return show_primitive_gallery_v2
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Defaults
    "THEME",
    "TOKENS",
    # v2 explicit
    "THEME_V2",
    "TOKENS_V2",
    "ThemeColorsV2",
    "DesignTokensV2",
    "NeutralRampV2",
    "AccentRampV2",
    "SemanticColorsV2",
    "TypographyV2",
    "SpacingV2",
    "MarginV2",
    "RadiusV2",
    "SizesV2",
    "BorderV2",
    "MotionV2",
    "ZIndexV2",
    # Color helpers
    "get_wire_color",
    "get_status_color",
    "get_node_status_color",
    # Utils
    "hex_to_rgb",
    "rgb_to_hex",
    "alpha",
    "blend",
    "darken",
    "lighten",
    "saturate",
    # Fonts
    "GEIST_SANS_FAMILY",
    "GEIST_MONO_FAMILY",
    "ensure_font_registered",
    "get_registered_fonts",
    # Icons
    "IconProviderV2",
    "IconSize",
    "IconState",
    "icon_v2",
    "get_icon",
    "get_pixmap",
    # Stylesheets v2
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
    # Widget helpers
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
    # Galleries
    "show_style_gallery_v2",
    "show_primitive_gallery_v2",
]
