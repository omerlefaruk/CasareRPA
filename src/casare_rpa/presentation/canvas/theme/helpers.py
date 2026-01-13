"""
Widget application helpers for UI tokens.

Design System 2025: Convenience functions for applying theme tokens to Qt widgets.

Usage:
    from casare_rpa.presentation.canvas.theme import TOKENS
    from casare_rpa.presentation.canvas.theme.helpers import (
        set_fixed_size,
        set_margins,
        set_spacing,
        set_font,
    )

    set_fixed_size(widget, 400, 500)
    set_margins(layout, TOKENS.margin.panel)
    set_spacing(layout, TOKENS.spacing.md)
"""

from __future__ import annotations

from PySide6.QtWidgets import QLayout, QWidget

from .design_tokens import TOKENS

# =============================================================================
# BASIC SIZE HELPERS
# =============================================================================


def set_fixed_size(widget: QWidget, width: int, height: int) -> None:
    """Apply fixed size to widget."""
    widget.setFixedSize(width, height)


def set_fixed_width(widget: QWidget, width: int) -> None:
    """Apply fixed width to widget."""
    widget.setFixedWidth(width)


def set_fixed_height(widget: QWidget, height: int) -> None:
    """Apply fixed height to widget."""
    widget.setFixedHeight(height)


def set_min_size(widget: QWidget, width: int, height: int) -> None:
    """Apply minimum size to widget."""
    widget.setMinimumSize(width, height)


def set_min_width(widget: QWidget, width: int) -> None:
    """Apply minimum width to widget."""
    widget.setMinimumWidth(width)


def set_min_height(widget: QWidget, height: int) -> None:
    """Apply minimum height to widget."""
    widget.setMinimumHeight(height)


def set_max_size(widget: QWidget, width: int, height: int) -> None:
    """Apply maximum size to widget."""
    widget.setMaximumSize(width, height)


def set_max_width(widget: QWidget, width: int) -> None:
    """Apply maximum width to widget."""
    widget.setMaximumWidth(width)


def set_max_height(widget: QWidget, height: int) -> None:
    """Apply maximum height to widget."""
    widget.setMaximumHeight(height)


# =============================================================================
# LAYOUT HELPERS
# =============================================================================


def set_margins(layout: QLayout, margins: tuple[int, int, int, int]) -> None:
    """
    Apply themed margins to layout.

    Args:
        layout: The layout to apply margins to.
        margins: Tuple of (left, top, right, bottom) in pixels.

    Usage:
        set_margins(layout, TOKENS.margin.panel)
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


# =============================================================================
# FONT HELPERS
# =============================================================================


def set_font(widget: QWidget, size: int, family: str | None = None) -> None:
    """
    Apply themed font to widget.

    Args:
        widget: The widget to apply font to.
        size: Font size in points.
        family: Optional font family string. Uses default UI font if None.

    Usage:
        set_font(label, TOKENS.typography.body, TOKENS.typography.sans)
    """
    font = widget.font()
    font.setPointSize(size)
    if family:
        font.setFamily(family)
    widget.setFont(font)


# =============================================================================
# MARGIN CONVENIENCE FUNCTIONS
# =============================================================================


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
    """Apply panel content margins (12px) to layout."""
    set_margins(layout, TOKENS.margin.panel)


def margin_dialog(layout: QLayout) -> None:
    """Apply dialog margins (24px) to layout."""
    set_margins(layout, TOKENS.margin.dialog)


def margin_toolbar(layout: QLayout) -> None:
    """Apply toolbar margins (tight, 4px) to layout."""
    set_margins(layout, TOKENS.margin.tight)


# =============================================================================
# COMPONENT SIZE HELPERS
# =============================================================================


def set_dialog_size(widget: QWidget, size: str = "md") -> None:
    """
    Set dialog size from preset.

    Args:
        widget: The dialog widget.
        size: Size preset - "sm", "md", "lg", or "xl".

    Raises:
        ValueError: If size preset is not recognized.
    """
    # Width x min-height presets
    sizes = {
        "sm": (TOKENS.sizes.dialog_sm_width, TOKENS.sizes.dialog_min_height),
        "md": (TOKENS.sizes.dialog_md_width, TOKENS.sizes.dialog_min_height * 2),
        "lg": (TOKENS.sizes.dialog_lg_width, TOKENS.sizes.dialog_min_height * 2),
        "xl": (TOKENS.sizes.dialog_lg_width, TOKENS.sizes.dialog_min_height * 3),
    }
    if size not in sizes:
        raise ValueError(f"Unknown dialog size: {size!r}. Use: sm, md, lg, xl")
    width, height = sizes[size]
    widget.setMinimumSize(width, height)


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
    height = heights[size]

    # Panel density: make buttons ~2x smaller inside docks.
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QDockWidget):
            # Avoid clipping descenders (p/y/g) when panel density is compact.
            height = max(16, int(round(height * 0.5)))
            break
        parent = parent.parentWidget()

    widget.setFixedHeight(height)


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
    # Size helpers
    "set_fixed_size",
    "set_fixed_width",
    "set_fixed_height",
    "set_min_size",
    "set_min_width",
    "set_min_height",
    "set_max_size",
    "set_max_width",
    "set_max_height",
    # Layout helpers
    "set_margins",
    "set_spacing",
    # Font helpers
    "set_font",
    # Margin presets
    "margin_none",
    "margin_compact",
    "margin_standard",
    "margin_comfortable",
    "margin_panel",
    "margin_dialog",
    "margin_toolbar",
    # Component size presets
    "set_dialog_size",
    "set_panel_width",
    "set_button_size",
    "set_input_size",
]
