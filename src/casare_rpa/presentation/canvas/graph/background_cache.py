"""
Pre-rendered node background cache.

Renders node body backgrounds to pixmaps once, reuses for identical node types/sizes.
This eliminates repeated QPainterPath creation and fill operations during paint().

Performance benefit: Node backgrounds are rendered once and cached as QPixmap,
subsequent paint() calls just draw the cached pixmap (GPU-accelerated blit).
"""

from typing import Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPixmap

from casare_rpa.presentation.canvas.ui.theme import Theme


class NodeBackgroundCache:
    """
    Cache pre-rendered node backgrounds by type and size.

    Key: (node_type, width, height, header_color_hex)
    Value: QPixmap with rendered background

    The cache uses a simple LRU eviction strategy with a maximum size
    to prevent unbounded memory growth.

    Usage:
        cache = get_background_cache()
        pixmap = cache.get_background(
            node_type="ClickNode",
            width=200,
            height=150,
            header_color=QColor(85, 45, 50),
            body_color=QColor(45, 45, 45),
        )
        painter.drawPixmap(rect.toRect(), pixmap)
    """

    _instance: Optional["NodeBackgroundCache"] = None
    _cache: dict[tuple[str, int, int, str], QPixmap]
    _max_cache_size: int = 200  # Limit memory usage

    def __new__(cls) -> "NodeBackgroundCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance

    def get_background(
        self,
        node_type: str,
        width: int,
        height: int,
        header_color: QColor,
        body_color: QColor,
        corner_radius: float = 8.0,
        header_height: int = 26,
    ) -> QPixmap:
        """
        Get cached background pixmap, rendering if needed.

        Args:
            node_type: Node type identifier for cache key
            width: Node width in pixels
            height: Node height in pixels
            header_color: Header bar color
            body_color: Body background color
            corner_radius: Corner rounding radius
            header_height: Height of header bar

        Returns:
            Pre-rendered QPixmap of node background
        """
        key = (node_type, width, height, header_color.name())

        if key not in self._cache:
            # Evict oldest if at capacity (simple FIFO eviction)
            if len(self._cache) >= self._max_cache_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            self._cache[key] = self._render_background(
                width, height, header_color, body_color, corner_radius, header_height
            )

        return self._cache[key]

    def _render_background(
        self,
        width: int,
        height: int,
        header_color: QColor,
        body_color: QColor,
        corner_radius: float,
        header_height: int,
    ) -> QPixmap:
        """
        Render node background to pixmap.

        Args:
            width: Node width
            height: Node height
            header_color: Color for header gradient
            body_color: Color for body background
            corner_radius: Corner rounding
            header_height: Height of header area

        Returns:
            Rendered QPixmap
        """
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, width, height)

        # Create rounded rect path for main body
        body_path = QPainterPath()
        body_path.addRoundedRect(rect, corner_radius, corner_radius)

        # Fill body background
        painter.fillPath(body_path, QBrush(body_color))

        # Draw header bar (top portion with rounded corners)
        QRectF(0, 0, width, header_height)
        header_path = QPainterPath()

        # Create header path with only top corners rounded
        header_path.moveTo(corner_radius, 0)
        header_path.lineTo(width - corner_radius, 0)
        header_path.arcTo(
            width - corner_radius * 2, 0, corner_radius * 2, corner_radius * 2, 90, -90
        )
        header_path.lineTo(width, header_height)
        header_path.lineTo(0, header_height)
        header_path.lineTo(0, corner_radius)
        header_path.arcTo(0, 0, corner_radius * 2, corner_radius * 2, 180, -90)
        header_path.closeSubpath()

        # Clip header path to body shape
        header_path = header_path.intersected(body_path)

        # Apply header color with alpha
        header_brush_color = QColor(header_color)
        header_brush_color.setAlpha(100)  # 40% opacity
        painter.fillPath(header_path, QBrush(header_brush_color))

        # Draw separator line below header
        sep_color = QColor(header_color)
        sep_color.setAlpha(150)
        painter.setPen(QPen(sep_color, 1))
        painter.drawLine(0, header_height, width, header_height)

        # Draw border
        canvas_colors = Theme.get_canvas_colors()
        border_color = QColor(canvas_colors.node_border_normal)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(body_path)

        painter.end()
        return pixmap

    def get_background_with_state(
        self,
        node_type: str,
        width: int,
        height: int,
        header_color: QColor,
        body_color: QColor,
        border_color: QColor,
        border_width: float = 1.0,
        corner_radius: float = 8.0,
        header_height: int = 26,
    ) -> QPixmap:
        """
        Get background with custom border (for selected/running states).

        This variant allows custom border styling but is not cached
        because state-dependent styling changes frequently.

        Args:
            node_type: Node type identifier
            width: Node width
            height: Node height
            header_color: Header bar color
            body_color: Body background color
            border_color: Border color
            border_width: Border thickness
            corner_radius: Corner rounding
            header_height: Header area height

        Returns:
            Rendered QPixmap (not cached)
        """
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, width, height)

        # Create rounded rect path
        body_path = QPainterPath()
        body_path.addRoundedRect(rect, corner_radius, corner_radius)

        # Fill body
        painter.fillPath(body_path, QBrush(body_color))

        # Draw header (same as above)
        QRectF(0, 0, width, header_height)
        header_path = QPainterPath()
        header_path.moveTo(corner_radius, 0)
        header_path.lineTo(width - corner_radius, 0)
        header_path.arcTo(
            width - corner_radius * 2, 0, corner_radius * 2, corner_radius * 2, 90, -90
        )
        header_path.lineTo(width, header_height)
        header_path.lineTo(0, header_height)
        header_path.lineTo(0, corner_radius)
        header_path.arcTo(0, 0, corner_radius * 2, corner_radius * 2, 180, -90)
        header_path.closeSubpath()
        header_path = header_path.intersected(body_path)

        header_brush_color = QColor(header_color)
        header_brush_color.setAlpha(100)
        painter.fillPath(header_path, QBrush(header_brush_color))

        # Separator
        sep_color = QColor(header_color)
        sep_color.setAlpha(150)
        painter.setPen(QPen(sep_color, 1))
        painter.drawLine(0, header_height, width, header_height)

        # Custom border
        painter.setPen(QPen(border_color, border_width))
        painter.drawPath(body_path)

        painter.end()
        return pixmap

    def clear(self) -> None:
        """Clear cache (call on theme change or cleanup)."""
        self._cache.clear()

    def invalidate(self, node_type: str) -> None:
        """
        Invalidate cache entries for a specific node type.

        Args:
            node_type: The node type to invalidate
        """
        keys_to_remove = [k for k in self._cache if k[0] == node_type]
        for key in keys_to_remove:
            del self._cache[key]

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache info
        """
        return {
            "cached_backgrounds": len(self._cache),
            "max_size": self._max_cache_size,
        }


def get_background_cache() -> NodeBackgroundCache:
    """
    Get singleton background cache instance.

    Returns:
        The NodeBackgroundCache singleton
    """
    return NodeBackgroundCache()
