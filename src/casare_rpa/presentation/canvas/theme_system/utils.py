"""
Theme utility functions for CasareRPA Canvas.

Contains color manipulation helpers like darken, lighten, alpha,
and other utility functions for working with colors.
"""

import re
from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert a hex color string to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#ff0000" or "ff0000")

    Returns:
        Tuple of (red, green, blue) values (0-255)
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color string.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Hex color string with # prefix
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def darken(hex_color: str, percent: float) -> str:
    """
    Darken a hex color by a percentage.

    Args:
        hex_color: Hex color string (e.g., "#ff0000")
        percent: Percentage to darken (0-100)

    Returns:
        Darkened hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    factor = 1 - (percent / 100)
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))
    return rgb_to_hex(r, g, b)


def lighten(hex_color: str, percent: float) -> str:
    """
    Lighten a hex color by a percentage.

    Args:
        hex_color: Hex color string (e.g., "#ff0000")
        percent: Percentage to lighten (0-100)

    Returns:
        Lightened hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    factor = percent / 100
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)


def alpha(hex_color: str, opacity: float) -> str:
    """
    Convert a hex color to rgba string with specified opacity.

    Args:
        hex_color: Hex color string (e.g., "#ff0000")
        opacity: Opacity value (0.0-1.0)

    Returns:
        RGBA color string for use in QSS
    """
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {opacity})"


def blend(color1: str, color2: str, ratio: float = 0.5) -> str:
    """
    Blend two hex colors together.

    Args:
        color1: First hex color
        color2: Second hex color
        ratio: Blend ratio (0.0 = all color1, 1.0 = all color2)

    Returns:
        Blended hex color string
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    return rgb_to_hex(r, g, b)


def contrast_color(hex_color: str) -> str:
    """
    Get a contrasting color (black or white) for text on the given background.

    Uses relative luminance calculation to determine contrast.

    Args:
        hex_color: Background hex color

    Returns:
        "#ffffff" for dark backgrounds, "#000000" for light backgrounds
    """
    r, g, b = hex_to_rgb(hex_color)
    # Calculate relative luminance using sRGB formula
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if luminance < 0.5 else "#000000"


def is_valid_hex(color: str) -> bool:
    """
    Check if a string is a valid hex color.

    Args:
        color: String to validate

    Returns:
        True if valid hex color, False otherwise
    """
    pattern = r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"
    return bool(re.match(pattern, color))


def normalize_hex(color: str) -> str:
    """
    Normalize a hex color to 6-digit format with # prefix.

    Args:
        color: Hex color string (3 or 6 digits, with or without #)

    Returns:
        Normalized 6-digit hex color with # prefix
    """
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return f"#{color.lower()}"


def saturate(hex_color: str, percent: float) -> str:
    """
    Increase saturation of a hex color.

    Args:
        hex_color: Hex color string
        percent: Percentage to increase saturation (0-100)

    Returns:
        Saturated hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    factor = 1 + (percent / 100)
    r = min(255, max(0, int(gray + (r - gray) * factor)))
    g = min(255, max(0, int(gray + (g - gray) * factor)))
    b = min(255, max(0, int(gray + (b - gray) * factor)))
    return rgb_to_hex(r, g, b)


def desaturate(hex_color: str, percent: float) -> str:
    """
    Decrease saturation of a hex color.

    Args:
        hex_color: Hex color string
        percent: Percentage to decrease saturation (0-100)

    Returns:
        Desaturated hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    factor = 1 - (percent / 100)
    r = int(gray + (r - gray) * factor)
    g = int(gray + (g - gray) * factor)
    b = int(gray + (b - gray) * factor)
    return rgb_to_hex(r, g, b)
