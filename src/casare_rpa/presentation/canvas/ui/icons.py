"""
CasareRPA - Icon Provider for Toolbar Actions.

Uses Qt's built-in standard icons for consistent, theme-aware icons
that work on all platforms without external assets.

For custom icons, use ResourceCache.get_icon(path) from resources.py.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QStyle

# PERFORMANCE: Cache for colored icons to avoid recreation on every call
# Icons are immutable, so caching is safe and effective
_colored_icon_cache: dict[tuple[str, str, int], "QIcon"] = {}


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
        import math

        from PySide6.QtGui import QPainterPath

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

    elif shape == "brain":
        # Brain/AI icon - stylized brain with sparkle
        import math

        from PySide6.QtGui import QPainterPath

        center_x = size / 2
        center_y = size / 2
        radius = inner_size * 0.4

        # Draw brain outline (two hemispheres)
        path = QPainterPath()

        # Left hemisphere
        path.moveTo(center_x, margin + inner_size * 0.1)
        path.cubicTo(
            margin,
            margin + inner_size * 0.1,
            margin,
            size - margin - inner_size * 0.1,
            center_x,
            size - margin - inner_size * 0.1,
        )

        # Right hemisphere
        path.cubicTo(
            size - margin,
            size - margin - inner_size * 0.1,
            size - margin,
            margin + inner_size * 0.1,
            center_x,
            margin + inner_size * 0.1,
        )

        # Draw brain with fill
        painter.setBrush(QBrush(qcolor))
        pen = QPen(qcolor.darker(120), size * 0.06)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)

        # Draw center line (brain fold)
        painter.setPen(QPen(qcolor.darker(130), size * 0.04))
        painter.drawLine(
            QPointF(center_x, margin + inner_size * 0.2),
            QPointF(center_x, size - margin - inner_size * 0.2),
        )

        # Draw sparkle (AI indicator) - small star at top-right
        sparkle_x = size - margin - inner_size * 0.15
        sparkle_y = margin + inner_size * 0.15
        sparkle_size = size * 0.15

        sparkle_color = QColor("#FFD700")  # Gold sparkle
        painter.setBrush(QBrush(sparkle_color))
        painter.setPen(QPen(sparkle_color))

        # 4-point star
        sparkle_points = [
            QPointF(sparkle_x, sparkle_y - sparkle_size),
            QPointF(sparkle_x + sparkle_size * 0.3, sparkle_y - sparkle_size * 0.3),
            QPointF(sparkle_x + sparkle_size, sparkle_y),
            QPointF(sparkle_x + sparkle_size * 0.3, sparkle_y + sparkle_size * 0.3),
            QPointF(sparkle_x, sparkle_y + sparkle_size),
            QPointF(sparkle_x - sparkle_size * 0.3, sparkle_y + sparkle_size * 0.3),
            QPointF(sparkle_x - sparkle_size, sparkle_y),
            QPointF(sparkle_x - sparkle_size * 0.3, sparkle_y - sparkle_size * 0.3),
        ]
        painter.drawPolygon(QPolygonF(sparkle_points))

    elif shape == "key":
        # Key icon for credentials
        from PySide6.QtGui import QPainterPath

        # Key dimensions
        head_radius = inner_size * 0.25
        head_center_x = margin + head_radius + inner_size * 0.05
        head_center_y = margin + head_radius + inner_size * 0.05

        # Draw key head (circle with hole)
        painter.setBrush(QBrush(qcolor))
        pen = QPen(qcolor.darker(120), size * 0.06)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Outer circle
        painter.drawEllipse(
            QRectF(
                head_center_x - head_radius,
                head_center_y - head_radius,
                head_radius * 2,
                head_radius * 2,
            )
        )

        # Inner hole (draw with background color)
        hole_radius = head_radius * 0.4
        painter.setBrush(QBrush(QColor("#1e1e1e")))  # Dark background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QRectF(
                head_center_x - hole_radius,
                head_center_y - hole_radius,
                hole_radius * 2,
                hole_radius * 2,
            )
        )

        # Draw key shaft (diagonal line from head to bottom-right)
        shaft_start_x = head_center_x + head_radius * 0.7
        shaft_start_y = head_center_y + head_radius * 0.7
        shaft_end_x = size - margin - inner_size * 0.1
        shaft_end_y = size - margin - inner_size * 0.1

        pen = QPen(qcolor, size * 0.12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(shaft_start_x, shaft_start_y),
            QPointF(shaft_end_x, shaft_end_y),
        )

        # Draw key teeth (two small protrusions)
        teeth_pen = QPen(qcolor, size * 0.08)
        teeth_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(teeth_pen)

        # First tooth
        tooth1_x = shaft_start_x + (shaft_end_x - shaft_start_x) * 0.5
        tooth1_y = shaft_start_y + (shaft_end_y - shaft_start_y) * 0.5
        tooth_length = inner_size * 0.15
        painter.drawLine(
            QPointF(tooth1_x, tooth1_y),
            QPointF(tooth1_x + tooth_length, tooth1_y - tooth_length),
        )

        # Second tooth
        tooth2_x = shaft_start_x + (shaft_end_x - shaft_start_x) * 0.7
        tooth2_y = shaft_start_y + (shaft_end_y - shaft_start_y) * 0.7
        painter.drawLine(
            QPointF(tooth2_x, tooth2_y),
            QPointF(tooth2_x + tooth_length, tooth2_y - tooth_length),
        )

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
        "reload": "SP_BrowserReload",
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
        "ai_assistant": ("brain", "#9C27B0"),  # Purple - AI brain icon
        "ai": ("brain", "#9C27B0"),  # Purple - AI brain icon (alias)
        "credentials": ("key", "#FFB300"),  # Amber/Gold - Key icon for credentials
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
