"""
CasareRPA - Icon Provider (v2 consolidated).

This module has been migrated to exclusively use the v2 Lucide SVG icon system.
Legacy Qt standard icons and manual drawing code are removed.

Usage:
    from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon

    icon = get_toolbar_icon("run")  # Returns v2 'play' icon
"""

from typing import TYPE_CHECKING

from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon


def get_toolbar_icon(name: str) -> "QIcon":
    """
    Get an icon by action name using the v2 system.

    Args:
        name: Action name (e.g., "run", "stop", "save")

    Returns:
        QIcon from the v2 icon provider
    """
    return get_icon_v2(name, size=20, state="normal")


def get_icon_v2_or_legacy(name: str, size: int = 20) -> "QIcon":
    """
    Get v2 icon. Legacy fallback is removed as v2 is now mandatory.

    Args:
        name: Action name (e.g., "run", "stop", "save")
        size: Icon size in pixels (default: 20)

    Returns:
        QIcon from the v2 icon provider
    """
    return get_icon_v2(name, size=size, state="normal")
