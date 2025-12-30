"""
Icon Provider v2 - Lucide SVG icons with THEME_V2 colors.

Epic 2.1: Icon System v2
- Loads SVG icons from resources/icons/
- Applies THEME_V2 colors (neutral + accent blue)
- Supports sizes: 16/20/24 (from TOKENS_V2.sizes)
- Supports states: normal, disabled, accent
- Caches rendered icons for performance

Usage:
    from casare_rpa.presentation.canvas.theme_system.icons_v2 import icon_v2

    # Get themed icon
    icon = icon_v2.get_icon("file", size=20, state="normal")
    action.setIcon(icon)

    # Get pixmap for custom painting
    pixmap = icon_v2.get_pixmap("play", size=24, state="accent")

See: docs/UX_REDESIGN_PLAN.md Phase 2 Epic 2.1
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from loguru import logger

from .tokens_v2 import THEME_V2

# =============================================================================
# ICON STATE TYPES
# =============================================================================

IconState = Literal["normal", "disabled", "accent"]
IconSize = Literal[16, 20, 24]

# =============================================================================
# ICON DIRECTORY RESOLUTION
# =============================================================================


def _get_icons_dir() -> Path:
    """
    Get the path to the icons directory.

    Handles both development and PyInstaller frozen modes.

    Returns:
        Path to the icons directory
    """
    # Try PyInstaller frozen mode first
    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)  # type: ignore
    else:
        # Development mode: use project root
        base_path = Path(__file__).parent.parent.parent.parent / "resources"

    icons_dir = base_path / "icons"
    if not icons_dir.exists():
        # Fallback to src path for development
        icons_dir = Path(__file__).parent.parent.parent.parent.parent / "src" / "casare_rpa" / "resources" / "icons"

    return icons_dir


# =============================================================================
# ICON PROVIDER V2
# =============================================================================


class IconProviderV2:
    """
    Icon provider for v2 UI using Lucide SVG icons.

    Features:
    - Loads SVG icons from resources/icons/
    - Applies THEME_V2 colors dynamically
    - Supports normal/disabled/accent states
    - Caches rendered icons for performance
    - Zero-asset (SVGs bundled with PyInstaller)

    Icon source: [Lucide Icons](https://lucide.dev/)
    License: ISC (free for commercial use)
    """

    # Color mappings for states
    _STATE_COLORS = {
        "normal": THEME_V2.text_primary,      # "#a0a0a0"
        "disabled": THEME_V2.text_disabled,   # "#404040"
        "accent": THEME_V2.primary,           # "#0066ff"
    }

    _icons_dir: Path | None = None
    _icon_cache: dict[tuple[str, int, IconState], QIcon] = {}

    @classmethod
    def _get_icons_directory(cls) -> Path:
        """Get cached icons directory path."""
        if cls._icons_dir is None:
            cls._icons_dir = _get_icons_dir()
            logger.debug(f"IconProviderV2: icons directory = {cls._icons_dir}")
        return cls._icons_dir

    @classmethod
    def _get_state_color(cls, state: IconState) -> str:
        """Get theme color for the given state."""
        return cls._STATE_COLORS.get(state, cls._STATE_COLORS["normal"])

    @classmethod
    def _load_svg_content(cls, name: str) -> str | None:
        """
        Load SVG file content.

        Args:
            name: Icon name (without .svg extension)

        Returns:
            SVG content as string, or None if not found
        """
        icons_dir = cls._get_icons_directory()
        svg_path = icons_dir / f"{name}.svg"

        if not svg_path.exists():
            logger.debug(f"Icon not found: {name}.svg")
            return None

        try:
            return svg_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read icon {name}.svg: {e}")
            return None

    @classmethod
    def _render_svg(
        cls,
        svg_content: str,
        size: int,
        color: str
    ) -> QPixmap:
        """
        Render SVG content to QPixmap with applied color.

        Args:
            svg_content: SVG XML string
            size: Icon size in pixels
            color: Hex color to apply (replaces currentColor)

        Returns:
            QPixmap containing the rendered icon
        """
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPainter, QPixmap

        # Replace currentColor with theme color
        svg_colored = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')

        # Create pixmap with transparent background
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        # Render SVG to pixmap
        from PySide6.QtSvg import QSvgRenderer

        renderer = QSvgRenderer(svg_colored.encode("utf-8"))

        if not renderer.isValid():
            logger.warning("Invalid SVG content")
            return pixmap

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()

        return pixmap

    @classmethod
    def get_icon(
        cls,
        name: str,
        size: IconSize = 20,
        state: IconState = "normal"
    ) -> QIcon:
        """
        Get a themed icon by name.

        Args:
            name: Icon name (e.g., "file", "play", "settings")
            size: Icon size: 16, 20, or 24 (default: 20)
            state: Icon state: "normal", "disabled", or "accent" (default: "normal")

        Returns:
            QIcon with the themed icon (may be empty if icon not found)
        """
        from PySide6.QtGui import QIcon

        cache_key = (name, size, state)

        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]

        # Load SVG content
        svg_content = cls._load_svg_content(name)
        if svg_content is None:
            return QIcon()

        # Get color for state
        color = cls._get_state_color(state)

        # Render to pixmap
        pixmap = cls._render_svg(svg_content, size, color)

        # Create and cache icon
        icon = QIcon(pixmap)
        cls._icon_cache[cache_key] = icon

        return icon

    @classmethod
    def get_pixmap(
        cls,
        name: str,
        size: IconSize = 20,
        state: IconState = "normal"
    ) -> QPixmap | None:
        """
        Get a themed pixmap by name.

        Args:
            name: Icon name (e.g., "file", "play", "settings")
            size: Icon size: 16, 20, or 24 (default: 20)
            state: Icon state: "normal", "disabled", or "accent" (default: "normal")

        Returns:
            QPixmap containing the icon, or None if not found
        """

        icon = cls.get_icon(name, size, state)
        if icon.isNull():
            return None

        return icon.pixmap(size, size)

    @classmethod
    def get_available_icons(cls) -> list[str]:
        """
        Get list of available icon names.

        Returns:
            List of icon names (without .svg extension)
        """
        icons_dir = cls._get_icons_directory()
        if not icons_dir.exists():
            return []

        return [
            f.stem for f in icons_dir.glob("*.svg")
            if f.is_file()
        ]

    @classmethod
    def has_icon(cls, name: str) -> bool:
        """Check if an icon exists."""
        return f"{name}.svg" in [f.name for f in cls._get_icons_directory().glob("*.svg")]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the icon cache (useful for theme changes)."""
        cls._icon_cache.clear()
        logger.debug("IconProviderV2 cache cleared")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

icon_v2 = IconProviderV2()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_icon(name: str, size: IconSize = 20, state: IconState = "normal") -> QIcon:
    """
    Convenience function to get a themed icon.

    Args:
        name: Icon name (e.g., "file", "play", "settings")
        size: Icon size: 16, 20, or 24 (default: 20)
        state: Icon state: "normal", "disabled", or "accent" (default: "normal")

    Returns:
        QIcon with the themed icon

    Example:
        from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon

        icon = get_icon("play", size=24, state="accent")
        play_action.setIcon(icon)
    """
    return icon_v2.get_icon(name, size, state)


def get_pixmap(name: str, size: IconSize = 20, state: IconState = "normal") -> QPixmap | None:
    """
    Convenience function to get a themed pixmap.

    Args:
        name: Icon name (e.g., "file", "play", "settings")
        size: Icon size: 16, 20, or 24 (default: 20)
        state: Icon state: "normal", "disabled", or "accent" (default: "normal")

    Returns:
        QPixmap containing the icon, or None if not found

    Example:
        from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_pixmap

        pixmap = get_pixmap("check", size=16, state="accent")
        painter.drawPixmap(x, y, pixmap)
    """
    return icon_v2.get_pixmap(name, size, state)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "IconProviderV2",
    "icon_v2",
    "get_icon",
    "get_pixmap",
    "IconState",
    "IconSize",
]
