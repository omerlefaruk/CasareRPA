"""
Widget application helpers for UI tokens.

This module provides convenience functions for applying theme tokens
to Qt widgets and layouts.

Usage:
    from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS
    from casare_rpa.presentation.canvas.theme_system.helpers import (
        set_fixed_size,
        set_margins,
        set_spacing,
        set_font,
    )

    set_fixed_size(widget, 400, 500)
    set_margins(layout, TOKENS.margin.panel_content)
    set_spacing(layout, TOKENS.spacing.md)
"""

from __future__ import annotations

from PySide6.QtWidgets import QLayout, QWidget

from .tokens import TOKENS


def set_fixed_size(widget: QWidget, width: int, height: int) -> None:
    """
    Apply fixed size to widget.

    Args:
        widget: The widget to size.
        width: Width in pixels.
        height: Height in pixels.
    """
    widget.setFixedSize(width, height)


def set_fixed_width(widget: QWidget, width: int) -> None:
    """
    Apply fixed width to widget.

    Args:
        widget: The widget to constrain.
        width: Width in pixels.
    """
    widget.setFixedWidth(width)


def set_fixed_height(widget: QWidget, height: int) -> None:
    """
    Apply fixed height to widget.

    Args:
        widget: The widget to constrain.
        height: Height in pixels.
    """
    widget.setFixedHeight(height)


def set_min_size(widget: QWidget, width: int, height: int) -> None:
    """
    Apply minimum size to widget.

    Args:
        widget: The widget to constrain.
        width: Minimum width in pixels.
        height: Minimum height in pixels.
    """
    widget.setMinimumSize(width, height)


def set_min_width(widget: QWidget, width: int) -> None:
    """
    Apply minimum width to widget.

    Args:
        widget: The widget to constrain.
        width: Minimum width in pixels.
    """
    widget.setMinimumWidth(width)


def set_min_height(widget: QWidget, height: int) -> None:
    """
    Apply minimum height to widget.

    Args:
        widget: The widget to constrain.
        height: Minimum height in pixels.
    """
    widget.setMinimumHeight(height)


def set_max_size(widget: QWidget, width: int, height: int) -> None:
    """
    Apply maximum size to widget.

    Args:
        widget: The widget to constrain.
        width: Maximum width in pixels.
        height: Maximum height in pixels.
    """
    widget.setMaximumSize(width, height)


def set_max_width(widget: QWidget, width: int) -> None:
    """
    Apply maximum width to widget.

    Args:
        widget: The widget to constrain.
        width: Maximum width in pixels.
    """
    widget.setMaximumWidth(width)


def set_max_height(widget: QWidget, height: int) -> None:
    """
    Apply maximum height to widget.

    Args:
        widget: The widget to constrain.
        height: Maximum height in pixels.
    """
    widget.setMaximumHeight(height)


def set_margins(layout: QLayout, margins: tuple[int, int, int, int]) -> None:
    """
    Apply themed margins to layout.

    Args:
        layout: The layout to apply margins to.
        margins: Tuple of (left, top, right, bottom) in pixels.

    Usage:
        set_margins(layout, TOKENS.margin.panel_content)
    """
    layout.setContentsMargins(*margins)


def set_spacing(layout: QLayout, spacing: int) -> None:
    """
    Apply themed spacing to layout.

    Args:
        layout: The layout to apply spacing to.
        spacing: Spacing in pixels.

    Usage:
        set_spacing(layout, TOKENS.spacing.md)
    """
    layout.setSpacing(spacing)


def set_font(widget: QWidget, size: int, family: str | None = None) -> None:
    """
    Apply themed font to widget.

    Args:
        widget: The widget to apply font to.
        size: Font size in points.
        family: Optional font family string. Uses default UI font if None.

    Usage:
        set_font(label, TOKENS.typography.display_m, TOKENS.typography.ui)
    """
    font = widget.font()
    font.setPointSize(size)
    if family:
        font.setFamily(family)
    widget.setFont(font)


# Convenience functions for common patterns


def margin_none(layout: QLayout) -> None:
    """Apply zero margins to layout."""
    set_margins(layout, TOKENS.margin.none)


def margin_compact(layout: QLayout) -> None:
    """Apply compact margins (8px) to layout."""
    set_margins(layout, TOKENS.margin.compact)


def margin_standard(layout: QLayout) -> None:
    """Apply standard margins (12px) to layout."""
    set_margins(layout, TOKENS.margin.standard)


def margin_comfortable(layout: QLayout) -> None:
    """Apply comfortable margins (16px) to layout."""
    set_margins(layout, TOKENS.margin.comfortable)


def margin_panel(layout: QLayout) -> None:
    """Apply panel content margins to layout."""
    set_margins(layout, TOKENS.margin.panel_content)


def margin_dialog(layout: QLayout) -> None:
    """Apply dialog margins to layout."""
    set_margins(layout, TOKENS.margin.dialog)


def margin_toolbar(layout: QLayout) -> None:
    """Apply toolbar margins to layout."""
    set_margins(layout, TOKENS.margin.toolbar)


def set_dialog_size(widget: QWidget, size: str = "md") -> None:
    """
    Set dialog size from preset.

    Args:
        widget: The dialog widget.
        size: Size preset - "sm", "md", "lg", or "xl".

    Raises:
        ValueError: If size preset is not recognized.
    """
    sizes = {
        "sm": (TOKENS.sizes.dialog_sm_width, TOKENS.sizes.dialog_height_sm),
        "md": (TOKENS.sizes.dialog_md_width, TOKENS.sizes.dialog_height_md),
        "lg": (TOKENS.sizes.dialog_lg_width, TOKENS.sizes.dialog_height_lg),
        "xl": (TOKENS.sizes.dialog_lg_width, TOKENS.sizes.dialog_height_lg),
    }
    if size not in sizes:
        raise ValueError(f"Unknown dialog size: {size!r}. Use: sm, md, lg, xl")
    width, height = sizes[size]
    widget.setFixedSize(width, height)


def set_panel_width(widget: QWidget, width: int | None = None) -> None:
    """
    Set panel width from theme.

    Args:
        widget: The panel widget.
        width: Width in pixels, or None for default.
    """
    if width is None:
        width = TOKENS.sizes.panel_default_width
    widget.setFixedWidth(width)


def set_button_size(widget: QWidget, size: str = "md") -> None:
    """
    Set button height from preset.

    Args:
        widget: The button widget.
        size: Size preset - "sm", "md", or "lg".

    Raises:
        ValueError: If size preset is not recognized.
    """
    heights = {
        "sm": TOKENS.sizes.button_sm,
        "md": TOKENS.sizes.button_md,
        "lg": TOKENS.sizes.button_lg,
    }
    if size not in heights:
        raise ValueError(f"Unknown button size: {size!r}. Use: sm, md, lg")
    widget.setFixedHeight(heights[size])


def set_input_size(widget: QWidget, size: str = "md") -> None:
    """
    Set input height from preset.

    Args:
        widget: The input widget.
        size: Size preset - "sm", "md", or "lg".

    Raises:
        ValueError: If size preset is not recognized.
    """
    heights = {
        "sm": TOKENS.sizes.input_sm,
        "md": TOKENS.sizes.input_md,
        "lg": TOKENS.sizes.input_lg,
    }
    if size not in heights:
        raise ValueError(f"Unknown input size: {size!r}. Use: sm, md, lg")
    widget.setFixedHeight(heights[size])


__all__ = [
    "TOKENS",
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
]
