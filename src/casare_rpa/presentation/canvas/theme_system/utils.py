"""
Color utilities - re-exported from theme.utils for backward compatibility.

This module re-exports all color utilities from theme.utils to maintain
compatibility with existing imports from theme_system.utils.
"""

from ..theme.utils import (
    alpha,
    blend,
    darken,
    hex_to_rgb,
    lighten,
    rgb_to_hex,
    saturate,
)

__all__ = [
    "alpha",
    "blend",
    "lighten",
    "darken",
    "saturate",
    "hex_to_rgb",
    "rgb_to_hex",
]
