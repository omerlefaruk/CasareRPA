"""
Level-of-Detail Manager for viewport rendering.

Determines LOD level once per frame instead of per-item.
This significantly reduces CPU overhead when many nodes/pipes need
to determine their rendering detail level.

Performance benefit: Instead of each of N nodes calculating zoom level
in paint(), a single calculation is done per frame and all items query
the cached result.
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsView


class LODLevel(Enum):
    """LOD levels for rendering detail."""

    ULTRA_LOW = auto()  # < 15% zoom - just colored rectangles
    LOW = auto()  # < 30% zoom - simplified (current LOD)
    MEDIUM = auto()  # < 50% zoom - reduced detail
    FULL = auto()  # >= 50% zoom - full detail


class ViewportLODManager:
    """
    Singleton manager for viewport LOD level.

    Determines LOD once per frame, all items query this instead of
    calculating zoom level individually in paint().

    Usage:
        # In viewport update timer (once per frame):
        lod_manager = get_lod_manager()
        lod_manager.update_from_view(viewer)

        # In item paint():
        lod = get_lod_manager().current_lod
        if lod == LODLevel.ULTRA_LOW:
            self._paint_ultra_simple(painter)
            return
    """

    _instance: Optional["ViewportLODManager"] = None

    # LOD thresholds - zoom level where each LOD kicks in
    # More aggressive thresholds for better performance at common zoom levels (40-60%)
    LOD_THRESHOLDS = {
        0.25: LODLevel.ULTRA_LOW,  # < 25% zoom (was 15%)
        0.40: LODLevel.LOW,  # < 40% zoom (was 30%)
        0.60: LODLevel.MEDIUM,  # < 60% zoom (was 50%)
    }

    def __new__(cls) -> "ViewportLODManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_lod = LODLevel.FULL
            cls._instance._last_zoom = 1.0
            cls._instance._zoom_hysteresis = 0.02  # Prevent flickering at boundaries
        return cls._instance

    @property
    def current_lod(self) -> LODLevel:
        """Get the current LOD level."""
        return self._current_lod

    @property
    def last_zoom(self) -> float:
        """Get the last computed zoom level."""
        return self._last_zoom

    def update_from_view(self, view: "QGraphicsView") -> LODLevel:
        """
        Update LOD based on current view transform. Call once per frame.

        Args:
            view: The QGraphicsView to get zoom from

        Returns:
            The new LOD level
        """
        if view is None:
            return self._current_lod

        try:
            zoom = view.transform().m11()
        except (RuntimeError, AttributeError):
            # View may be destroyed or invalid
            return self._current_lod

        # Hysteresis to prevent LOD flickering at boundaries
        # Only update if zoom changed significantly
        if abs(zoom - self._last_zoom) < self._zoom_hysteresis:
            return self._current_lod

        self._last_zoom = zoom

        # Find appropriate LOD level based on thresholds
        for threshold, level in sorted(self.LOD_THRESHOLDS.items()):
            if zoom < threshold:
                self._current_lod = level
                return level

        self._current_lod = LODLevel.FULL
        return LODLevel.FULL

    def force_lod(self, level: LODLevel) -> None:
        """
        Force a specific LOD level (for high performance mode).

        Args:
            level: The LOD level to force
        """
        self._current_lod = level

    def should_render_widgets(self) -> bool:
        """
        Whether to render node widgets (inputs, dropdowns, etc).

        Returns:
            True if at FULL or MEDIUM LOD
        """
        return self._current_lod in (LODLevel.FULL, LODLevel.MEDIUM)

    def should_render_icons(self) -> bool:
        """
        Whether to render node icons.

        Returns:
            True if not at ULTRA_LOW LOD
        """
        return self._current_lod != LODLevel.ULTRA_LOW

    def should_render_ports(self) -> bool:
        """
        Whether to render port details (connection points).

        Returns:
            True only at FULL LOD
        """
        return self._current_lod == LODLevel.FULL

    def should_render_labels(self) -> bool:
        """
        Whether to render text labels on nodes/pipes.

        Returns:
            True only at FULL LOD
        """
        return self._current_lod == LODLevel.FULL

    def should_use_antialiasing(self) -> bool:
        """
        Whether to use antialiasing for rendering.

        Returns:
            True at FULL or MEDIUM LOD
        """
        return self._current_lod in (LODLevel.FULL, LODLevel.MEDIUM)

    def get_stats(self) -> dict:
        """
        Get LOD manager statistics.

        Returns:
            Dict with current state info
        """
        return {
            "current_lod": self._current_lod.name,
            "last_zoom": self._last_zoom,
            "hysteresis": self._zoom_hysteresis,
        }


def get_lod_manager() -> ViewportLODManager:
    """
    Get the singleton LOD manager instance.

    Returns:
        The ViewportLODManager singleton
    """
    return ViewportLODManager()
