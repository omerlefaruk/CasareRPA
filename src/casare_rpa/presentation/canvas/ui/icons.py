"""
CasareRPA - Icon Provider for Toolbar Actions.

Uses Qt's built-in standard icons for consistent, theme-aware icons
that work on all platforms without external assets.

For custom icons, use ResourceCache.get_icon(path) from resources.py.
"""

from typing import TYPE_CHECKING, Optional, Dict, Tuple

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QStyle

# PERFORMANCE: Cache for colored icons to avoid recreation on every call
# Icons are immutable, so caching is safe and effective
_colored_icon_cache: Dict[Tuple[str, str, int], "QIcon"] = {}


def _create_colored_icon(shape: str, color: str, size: int = 16) -> "QIcon":
    """
    Create a colored icon with specified shape.

    PERFORMANCE: Uses caching to avoid recreating icons on every call.
    Icons are immutable so caching is safe.

    Args:
        shape: "play", "pause", or "stop"
        color: Hex color string (e.g., "#4CAF50")
        size: Icon size in pixels

    Returns:
        QIcon with the colored shape
    """
    # PERFORMANCE: Check cache first
    cache_key = (shape, color, size)
    if cache_key in _colored_icon_cache:
        return _colored_icon_cache[cache_key]

    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    qcolor = QColor(color)
    painter.setBrush(QBrush(qcolor))
    painter.setPen(QPen(qcolor.darker(110), 1))

    margin = size * 0.15
    inner_size = size - 2 * margin

    if shape == "play":
        # Triangle pointing right
        points = [
            QPointF(margin, margin),
            QPointF(size - margin, size / 2),
            QPointF(margin, size - margin),
        ]
        painter.drawPolygon(QPolygonF(points))
    elif shape == "pause":
        # Two vertical bars
        bar_width = inner_size * 0.3
        gap = inner_size * 0.2
        left_x = margin + (inner_size - 2 * bar_width - gap) / 2
        painter.drawRoundedRect(QRectF(left_x, margin, bar_width, inner_size), 2, 2)
        painter.drawRoundedRect(
            QRectF(left_x + bar_width + gap, margin, bar_width, inner_size), 2, 2
        )
    elif shape == "stop":
        # Square
        painter.drawRoundedRect(QRectF(margin, margin, inner_size, inner_size), 3, 3)
    elif shape == "restart":
        # Circular arrow (restart symbol)
        from PySide6.QtGui import QPainterPath
        import math

        center_x = size / 2
        center_y = size / 2
        radius = inner_size * 0.4

        # Draw circular arc (about 270 degrees)
        path = QPainterPath()
        start_angle = -45  # degrees
        span_angle = 270  # degrees

        # Arc rect
        arc_rect = QRectF(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2,
        )
        path.arcMoveTo(arc_rect, start_angle)
        path.arcTo(arc_rect, start_angle, span_angle)

        # Draw arc with thicker pen
        pen = QPen(qcolor, size * 0.12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Draw arrowhead at the end of the arc
        end_angle = math.radians(start_angle + span_angle)
        end_x = center_x + radius * math.cos(end_angle)
        end_y = center_y - radius * math.sin(end_angle)

        # Arrowhead pointing in direction of arc
        arrow_size = size * 0.25
        arrow_angle = end_angle - math.pi / 2  # Perpendicular to end of arc

        arrow_points = [
            QPointF(end_x, end_y),
            QPointF(
                end_x - arrow_size * math.cos(arrow_angle - 0.5),
                end_y + arrow_size * math.sin(arrow_angle - 0.5),
            ),
            QPointF(
                end_x - arrow_size * math.cos(arrow_angle + 0.5),
                end_y + arrow_size * math.sin(arrow_angle + 0.5),
            ),
        ]
        painter.setBrush(QBrush(qcolor))
        painter.setPen(QPen(qcolor))
        painter.drawPolygon(QPolygonF(arrow_points))

    painter.end()

    # Cache and return
    icon = QIcon(pixmap)
    _colored_icon_cache[cache_key] = icon
    return icon


class ToolbarIcons:
    """
    Provides icons for toolbar actions using Qt standard icons.

    Qt standard icons are:
    - Always available (no external files needed)
    - Theme-aware (respect system theme on all platforms)
    - Properly scaled for different DPI settings

    Usage:
        icon = ToolbarIcons.get_icon("run")
        action.setIcon(icon)
    """

    # Maps action names to Qt StandardPixmap enum values
    # See: https://doc.qt.io/qt-6/qstyle.html#StandardPixmap-enum
    _ICON_MAP = {
        # File operations
        "new": "SP_FileIcon",
        "open": "SP_DirOpenIcon",
        "save": "SP_DialogSaveButton",
        "save_as": "SP_DialogSaveButton",
        # Edit operations
        "undo": "SP_ArrowBack",
        "redo": "SP_ArrowForward",
        "cut": "SP_FileIcon",  # No standard cut icon
        "copy": "SP_FileDialogContentsView",
        "paste": "SP_FileDialogDetailedView",
        "delete": "SP_TrashIcon",
        "find": "SP_FileDialogContentsView",
        # Execution operations
        "run": "SP_MediaPlay",
        "pause": "SP_MediaPause",
        "resume": "SP_MediaPlay",
        "stop": "SP_MediaStop",
        "restart": "SP_BrowserReload",
        "step": "SP_MediaSeekForward",
        "continue": "SP_MediaSkipForward",
        # Debug operations
        "debug": "SP_FileDialogInfoView",
        "breakpoint": "SP_DialogCancelButton",
        "clear_breakpoints": "SP_DialogResetButton",
        # View operations
        "zoom_in": "SP_ArrowUp",
        "zoom_out": "SP_ArrowDown",
        "zoom_reset": "SP_BrowserReload",
        "fit_view": "SP_DesktopIcon",
        "save_layout": "SP_DialogApplyButton",
        # Tools
        "record": "SP_DialogApplyButton",
        "pick_selector": "SP_DialogHelpButton",
        "preferences": "SP_FileDialogDetailedView",
        "help": "SP_DialogHelpButton",
        "about": "SP_MessageBoxInformation",
        # Status indicators
        "info": "SP_MessageBoxInformation",
        "warning": "SP_MessageBoxWarning",
        "error": "SP_MessageBoxCritical",
        "success": "SP_DialogApplyButton",
        # Performance/Monitoring
        "performance": "SP_ComputerIcon",
        "dashboard": "SP_ComputerIcon",
        "metrics": "SP_DriveHDIcon",
        # Project/Settings
        "project": "SP_DirIcon",
        "fleet": "SP_DriveNetIcon",
        "layout": "SP_DialogSaveButton",
        # Trigger controls
        "listen": "SP_MediaPlay",
        "stop_listen": "SP_MediaStop",
    }

    _style: Optional["QStyle"] = None

    @classmethod
    def _get_style(cls) -> "QStyle":
        """Get the application style (cached)."""
        if cls._style is None:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                cls._style = app.style()
            else:
                # Fallback: create style without app
                from PySide6.QtWidgets import QStyleFactory

                cls._style = QStyleFactory.create("Fusion")
        return cls._style

    # Colored icons for execution controls (shape, color)
    _COLORED_ICONS = {
        "run": ("play", "#4CAF50"),  # Green
        "pause": ("pause", "#FF9800"),  # Orange
        "stop": ("stop", "#F44336"),  # Red
        "restart": ("restart", "#2196F3"),  # Blue
        "resume": ("play", "#4CAF50"),  # Green
    }

    @classmethod
    def get_icon(cls, name: str) -> "QIcon":
        """
        Get a toolbar icon by action name.

        Args:
            name: Action name (e.g., "run", "stop", "save")

        Returns:
            QIcon for the action, or empty QIcon if not found
        """
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QStyle

        # Check for colored icons first
        if name in cls._COLORED_ICONS:
            shape, color = cls._COLORED_ICONS[name]
            return _create_colored_icon(shape, color)

        pixmap_name = cls._ICON_MAP.get(name)
        if not pixmap_name:
            return QIcon()

        style = cls._get_style()
        if not style:
            return QIcon()

        # Get the StandardPixmap enum value
        try:
            pixmap_enum = getattr(QStyle.StandardPixmap, pixmap_name, None)
            if pixmap_enum is None:
                return QIcon()
            return style.standardIcon(pixmap_enum)
        except (AttributeError, TypeError):
            return QIcon()

    @classmethod
    def get_all_icons(cls) -> dict:
        """
        Get all available toolbar icons.

        Returns:
            Dictionary mapping action names to QIcon instances
        """
        return {name: cls.get_icon(name) for name in cls._ICON_MAP.keys()}


def get_toolbar_icon(name: str) -> "QIcon":
    """
    Convenience function to get a toolbar icon.

    Args:
        name: Action name

    Returns:
        QIcon for the action
    """
    return ToolbarIcons.get_icon(name)
