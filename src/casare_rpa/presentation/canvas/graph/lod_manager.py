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
    """LOD levels for rendering detail (Semantic Zoom)."""

    ULTRA_LOW = auto()  # < 25% zoom - just colored dots/blocks (structure only)
    LOW = auto()  # < 40% zoom - simplified rectangles
    MEDIUM = auto()  # < 60% zoom - reduced detail
    FULL = auto()  # 60%-100% zoom - full detail
    EXPANDED = auto()  # > 100% zoom - expanded with inline inputs


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
    # Supports semantic zoom: <50% shows structure, >100% shows expanded details
    LOD_THRESHOLDS = {
        0.25: LODLevel.ULTRA_LOW,  # < 25% zoom - dots/blocks
        0.40: LODLevel.LOW,  # < 40% zoom - rectangles
        0.60: LODLevel.MEDIUM,  # < 60% zoom - reduced
        1.0: LODLevel.FULL,  # 60%-100% zoom - normal
        # > 100% triggers EXPANDED level
    }

    # Threshold for expanded mode (zoom > 100%)
    EXPANDED_THRESHOLD = 1.0

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

        # Check for expanded mode (> 100% zoom)
        if zoom > self.EXPANDED_THRESHOLD:
            self._current_lod = LODLevel.EXPANDED
            return LODLevel.EXPANDED

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
            True at FULL, EXPANDED, or MEDIUM LOD
        """
        return self._current_lod in (LODLevel.FULL, LODLevel.MEDIUM, LODLevel.EXPANDED)

    # =========================================================================
    # SEMANTIC ZOOM HELPERS
    # =========================================================================

    def is_overview_mode(self) -> bool:
        """
        Check if in overview mode (zoomed out, showing structure).

        At < 50% zoom, nodes become simplified to show workflow structure.

        Returns:
            True if zoom < 50% (ULTRA_LOW, LOW, or MEDIUM)
        """
        return self._current_lod in (LODLevel.ULTRA_LOW, LODLevel.LOW, LODLevel.MEDIUM)

    def is_editing_mode(self) -> bool:
        """
        Check if in editing mode (normal zoom for editing).

        Between 50% and 100% zoom, full node details are shown.

        Returns:
            True if at FULL LOD (60%-100% zoom)
        """
        return self._current_lod == LODLevel.FULL

    def is_expanded_mode(self) -> bool:
        """
        Check if in expanded mode (zoomed in, showing extra details).

        At > 100% zoom, nodes expand to show inline input fields
        and extra configuration directly on the canvas.

        Returns:
            True if zoom > 100% (EXPANDED level)
        """
        return self._current_lod == LODLevel.EXPANDED

    def should_show_inline_inputs(self) -> bool:
        """
        Whether to show inline input fields directly on nodes.

        Only at EXPANDED zoom level (> 100%).

        Returns:
            True if should show inline input widgets
        """
        return self._current_lod == LODLevel.EXPANDED

    def should_show_node_as_dot(self) -> bool:
        """
        Whether to render nodes as simple colored dots/blocks.

        At ULTRA_LOW zoom (< 25%), nodes become dots showing structure.

        Returns:
            True if nodes should render as dots
        """
        return self._current_lod == LODLevel.ULTRA_LOW

    def get_node_simplification_level(self) -> int:
        """
        Get numeric simplification level (0=full, 4=dots).

        Returns:
            0 = EXPANDED (most detail)
            1 = FULL
            2 = MEDIUM
            3 = LOW
            4 = ULTRA_LOW (dots)
        """
        level_map = {
            LODLevel.EXPANDED: 0,
            LODLevel.FULL: 1,
            LODLevel.MEDIUM: 2,
            LODLevel.LOW: 3,
            LODLevel.ULTRA_LOW: 4,
        }
        return level_map.get(self._current_lod, 1)

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
