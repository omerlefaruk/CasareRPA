"""
CasareRPA Theme System (Compatibility Layer).

This module re-exports the unified theme system components.
Prefer importing directly from `casare_rpa.presentation.canvas.theme_system`.
"""

from casare_rpa.presentation.canvas.theme_system import (
    THEME,
    TOKENS,
    CanvasThemeColors,
    DesignTokens,
    get_canvas_stylesheet,
    get_node_status_color,
    get_status_color,
    get_wire_color,
)

# Re-export key components
__all__ = [
    "THEME",
    "TOKENS",
    "CanvasThemeColors",
    "DesignTokens",
    "get_canvas_stylesheet",
    "get_node_status_color",
    "get_status_color",
    "get_wire_color",
]
