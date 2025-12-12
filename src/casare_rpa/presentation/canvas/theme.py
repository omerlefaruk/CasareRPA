"""
Unified Theme System for CasareRPA Canvas.

This module serves as a compatibility layer, re-exporting all theme components
from the modular theme package at presentation/canvas/theme/.

For new code, you can import directly from the theme package:
    from casare_rpa.presentation.canvas.theme import THEME, get_canvas_stylesheet

This module maintains backward compatibility with all existing imports.

Modular Theme Package Structure:
    presentation/canvas/theme_system/
    ├── __init__.py (re-exports for easy access)
    ├── colors.py (CanvasThemeColors dataclass, wire/status colors)
    ├── styles.py (widget QSS generator functions)
    ├── constants.py (spacing, sizes, borders, radii)
    └── utils.py (color manipulation: darken, lighten, alpha, etc.)
"""

from pathlib import Path

# Re-export colors module
from casare_rpa.presentation.canvas.theme_system.colors import (
    CanvasThemeColors,
    NODE_STATUS_COLOR_MAP,
    STATUS_COLOR_MAP,
    WIRE_COLOR_MAP,
    get_node_status_color as _get_node_status_color,
    get_status_color as _get_status_color,
    get_wire_color as _get_wire_color,
)

# Re-export constants module
from casare_rpa.presentation.canvas.theme_system.constants import (
    BORDERS,
    FONT_SIZE_MAP,
    FONT_SIZES,
    FONTS,
    RADIUS,
    RADIUS_MAP,
    SIZES,
    SPACING,
    SPACING_MAP,
    BorderConstants,
    FontConstants,
    FontSizeConstants,
    RadiusConstants,
    SizeConstants,
    SpacingConstants,
)

# Re-export styles module
from casare_rpa.presentation.canvas.theme_system.styles import (
    CHECKMARK_PATH,
    get_base_widget_styles,
    get_button_styles,
    get_canvas_stylesheet as _get_canvas_stylesheet,
    get_checkbox_styles,
    get_combobox_styles,
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

# Re-export utils module
from casare_rpa.presentation.canvas.theme_system.utils import (
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

# Get assets directory path (backward compatibility)
ASSETS_DIR = Path(__file__).parent / "assets"

# Global theme instance
THEME = CanvasThemeColors()


def get_canvas_stylesheet() -> str:
    """
    Generate the main Canvas application stylesheet.

    This wrapper maintains the original API signature (no arguments)
    by using the global THEME instance.

    Returns:
        Complete QSS stylesheet for the Canvas application.
    """
    return _get_canvas_stylesheet(THEME)


def get_node_status_color(status: str) -> str:
    """
    Get the color for a node execution status.

    Args:
        status: Node status string (idle, running, success, error, skipped)

    Returns:
        Hex color string for the status.
    """
    return _get_node_status_color(status, THEME)


def get_wire_color(data_type: str) -> str:
    """
    Get the color for a connection wire based on data type.

    Args:
        data_type: The data type of the connection.

    Returns:
        Hex color string for the wire.
    """
    return _get_wire_color(data_type, THEME)


def get_status_color(status: str) -> str:
    """
    Get color for a general status string.

    Args:
        status: Status string.

    Returns:
        Hex color string.
    """
    return _get_status_color(status, THEME)


__all__ = [
    # Main exports (original API)
    "THEME",
    "CanvasThemeColors",
    "get_canvas_stylesheet",
    "get_node_status_color",
    "get_wire_color",
    "get_status_color",
    # Assets
    "ASSETS_DIR",
    "CHECKMARK_PATH",
    # Color maps
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
    "SpacingConstants",
    "BorderConstants",
    "RadiusConstants",
    "FontSizeConstants",
    "SizeConstants",
    "FontConstants",
    # Style generators
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
]
