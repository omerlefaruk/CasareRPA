"""
Widget helpers - re-exported from theme.helpers for backward compatibility.

This module re-exports all helpers from theme.helpers to maintain
compatibility with existing imports from theme_system.helpers.
"""

from ..theme.helpers import (
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

__all__ = [
    "margin_none",
    "margin_compact",
    "margin_standard",
    "margin_comfortable",
    "margin_panel",
    "margin_dialog",
    "margin_toolbar",
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
    "set_dialog_size",
    "set_panel_width",
    "set_button_size",
    "set_input_size",
]
