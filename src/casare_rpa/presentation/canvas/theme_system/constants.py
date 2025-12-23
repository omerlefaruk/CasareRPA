"""
Theme constants for CasareRPA Canvas.

Contains numeric values for spacing, sizes, borders, radii, and other
layout-related constants used throughout the UI.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpacingConstants:
    """Spacing values in pixels."""

    xs: int = 2
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16
    xxl: int = 20
    xxxl: int = 32


@dataclass(frozen=True)
class BorderConstants:
    """Border width values in pixels."""

    none: int = 0
    thin: int = 1
    medium: int = 2
    thick: int = 3


@dataclass(frozen=True)
class RadiusConstants:
    """Border radius values in pixels."""

    none: int = 0
    sm: int = 4
    md: int = 6
    lg: int = 8
    xl: int = 12
    full: int = 9999  # For pill shapes


@dataclass(frozen=True)
class FontSizeConstants:
    """Font size values in pixels."""

    xs: int = 10
    sm: int = 11
    md: int = 13
    lg: int = 14
    xl: int = 16
    xxl: int = 18
    header: int = 20


@dataclass(frozen=True)
class SizeConstants:
    """Component size values in pixels."""

    # Scrollbar
    scrollbar_width: int = 8
    scrollbar_min_handle: int = 40

    # Toolbar
    toolbar_padding: int = 8
    toolbar_spacing: int = 8
    toolbar_button_padding_h: int = 10
    toolbar_button_padding_v: int = 6
    toolbar_separator_width: int = 1
    toolbar_separator_margin: int = 8

    # Menu
    menu_padding: int = 6
    menu_item_padding_v: int = 8
    menu_item_padding_h: int = 12
    menu_item_padding_right: int = 32
    menu_separator_margin: int = 10

    # Tab
    tab_padding_v: int = 12
    tab_padding_h: int = 20
    tab_spacing: int = 4

    # Input
    input_padding_v: int = 8
    input_padding_h: int = 12
    input_min_height: int = 24

    # Button
    button_padding_v: int = 8
    button_padding_h: int = 16

    # Checkbox
    checkbox_size: int = 18
    checkbox_spacing: int = 8

    # Table/List
    table_item_padding_v: int = 8
    table_item_padding_h: int = 10

    # Header
    header_padding_v: int = 8
    header_padding_h: int = 12

    # Dock
    dock_title_padding_v: int = 10
    dock_title_padding_h: int = 16
    dock_button_padding: int = 4
    dock_button_icon_size: int = 14

    # Tooltip
    tooltip_padding_v: int = 6
    tooltip_padding_h: int = 12

    # Combo dropdown arrow
    combo_dropdown_width: int = 24
    combo_arrow_size: int = 5
    combo_arrow_margin: int = 8

    # Splitter
    splitter_handle_size: int = 4


@dataclass(frozen=True)
class FontConstants:
    """Font family definitions."""

    # Primary UI font stack
    ui: str = "'Segoe UI', 'Inter', 'Roboto', system-ui, sans-serif"

    # Monospace font stack for code/logs
    mono: str = "'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace"


# Global constant instances
SPACING = SpacingConstants()
BORDERS = BorderConstants()
RADIUS = RadiusConstants()
FONT_SIZES = FontSizeConstants()
SIZES = SizeConstants()
FONTS = FontConstants()


# Convenience dictionaries for programmatic access
SPACING_MAP: dict[str, int] = {
    "xs": SPACING.xs,
    "sm": SPACING.sm,
    "md": SPACING.md,
    "lg": SPACING.lg,
    "xl": SPACING.xl,
    "xxl": SPACING.xxl,
    "xxxl": SPACING.xxxl,
}

RADIUS_MAP: dict[str, int] = {
    "none": RADIUS.none,
    "sm": RADIUS.sm,
    "md": RADIUS.md,
    "lg": RADIUS.lg,
    "xl": RADIUS.xl,
    "full": RADIUS.full,
}

FONT_SIZE_MAP: dict[str, int] = {
    "xs": FONT_SIZES.xs,
    "sm": FONT_SIZES.sm,
    "md": FONT_SIZES.md,
    "lg": FONT_SIZES.lg,
    "xl": FONT_SIZES.xl,
    "xxl": FONT_SIZES.xxl,
    "header": FONT_SIZES.header,
}
