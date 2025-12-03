"""
Frame Style Manager

Centralized styling for NodeFrame components.
Consolidates color palettes, themes, and style application logic.

Following Single Responsibility Principle - this module handles ONLY visual styling.
"""

from typing import Dict, Optional, Tuple
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtCore import Qt


# ============================================================================
# FRAME COLOR PALETTES
# ============================================================================

# Predefined colors for frame grouping (semi-transparent for background)
# Higher alpha (80-100) for better visibility
FRAME_COLOR_PALETTE: Dict[str, QColor] = {
    "Gray": QColor(100, 100, 100, 80),
    "Blue": QColor(60, 120, 180, 100),
    "Green": QColor(60, 160, 80, 100),
    "Yellow": QColor(180, 160, 60, 100),
    "Orange": QColor(200, 120, 60, 100),
    "Red": QColor(180, 70, 70, 100),
    "Purple": QColor(140, 80, 160, 100),
    "Teal": QColor(60, 150, 150, 100),
    "Pink": QColor(180, 100, 140, 100),
}

# Lower alpha (60) themes for lighter appearance
FRAME_COLORS: Dict[str, QColor] = {
    "blue": QColor(100, 181, 246, 60),
    "purple": QColor(156, 39, 176, 60),
    "green": QColor(102, 187, 106, 60),
    "orange": QColor(255, 167, 38, 60),
    "red": QColor(239, 83, 80, 60),
    "yellow": QColor(255, 202, 40, 60),
    "teal": QColor(77, 182, 172, 60),
    "pink": QColor(236, 64, 122, 60),
    "gray": QColor(120, 120, 120, 60),
}

# Default colors
DEFAULT_FRAME_COLOR = QColor(100, 100, 100, 80)
DEFAULT_PORT_COLOR = QColor(100, 181, 246)  # Light blue


class FrameStyleManager:
    """
    Manages visual styling for NodeFrame components.

    Responsibilities:
    - Color palette management
    - Brush and pen creation
    - Port type color resolution
    - Theme application
    """

    @staticmethod
    def get_frame_color(color_name: str) -> QColor:
        """
        Get frame color by name.

        Args:
            color_name: Color name (case-insensitive)

        Returns:
            QColor for the frame
        """
        # Check both palettes (case-insensitive)
        lower_name = color_name.lower()

        if lower_name in FRAME_COLORS:
            return FRAME_COLORS[lower_name]

        # Check FRAME_COLOR_PALETTE (title case)
        title_name = color_name.title()
        if title_name in FRAME_COLOR_PALETTE:
            return FRAME_COLOR_PALETTE[title_name]

        return DEFAULT_FRAME_COLOR

    @staticmethod
    def create_frame_brush(color: QColor) -> QBrush:
        """Create brush for frame fill."""
        return QBrush(color)

    @staticmethod
    def create_frame_pen(
        color: QColor,
        width: int = 2,
        style: Qt.PenStyle = Qt.PenStyle.DashLine,
        darken_factor: int = 120,
    ) -> QPen:
        """
        Create pen for frame border.

        Args:
            color: Base color
            width: Line width
            style: Pen style (solid, dash, etc.)
            darken_factor: How much to darken the color (100 = no change)

        Returns:
            QPen for drawing frame border
        """
        pen = QPen(color.darker(darken_factor), width)
        pen.setStyle(style)
        return pen

    @staticmethod
    def get_selection_pen() -> QPen:
        """Get pen for selected frame highlight."""
        pen = QPen(QColor(255, 215, 0), 3)  # Bright yellow
        pen.setStyle(Qt.PenStyle.SolidLine)
        return pen

    @staticmethod
    def get_drop_target_pen() -> QPen:
        """Get pen for drop target highlight."""
        pen = QPen(QColor(76, 175, 80), 3)  # Green
        pen.setStyle(Qt.PenStyle.SolidLine)
        return pen

    @staticmethod
    def get_drop_target_brush() -> QBrush:
        """Get brush for drop target fill."""
        return QBrush(QColor(76, 175, 80, 40))  # Semi-transparent green

    @staticmethod
    def get_collapsed_pen(color: QColor) -> QPen:
        """Get pen for collapsed frame border."""
        pen = QPen(color.darker(150), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        return pen

    @staticmethod
    def get_collapsed_brush(color: QColor) -> QBrush:
        """Get brush for collapsed frame fill."""
        return QBrush(color.darker(110))

    @staticmethod
    def get_port_color(port) -> QColor:
        """
        Get color for a port based on its type.

        Args:
            port: Port object with node() method

        Returns:
            QColor for the port
        """
        try:
            node = port.node()
            if hasattr(node, "get_port_type"):
                data_type = node.get_port_type(port.name())
                if data_type:
                    from casare_rpa.domain.port_type_system import (
                        get_port_type_registry,
                    )

                    registry = get_port_type_registry()
                    color_tuple = registry.get_type_color(data_type)
                    return QColor(*color_tuple)
        except Exception:
            pass

        return DEFAULT_PORT_COLOR

    @staticmethod
    def get_title_color() -> QColor:
        """Get color for frame title text."""
        return QColor(255, 255, 255, 200)  # Semi-transparent white

    @staticmethod
    def get_node_count_color(frame_color: QColor) -> QColor:
        """Get color for collapsed node count text."""
        return frame_color.lighter(180)


class CollapseButtonStyle:
    """Style constants for collapse button."""

    SIZE = 18
    MARGIN = 8
    SYMBOL_SIZE = 6
    CORNER_RADIUS = 4

    # Colors
    BACKGROUND_NORMAL = QColor(60, 60, 60, 180)
    BACKGROUND_HOVER = QColor(80, 80, 80, 200)
    BORDER_COLOR = QColor(100, 100, 100)
    SYMBOL_COLOR = QColor(220, 220, 220)

    @classmethod
    def get_background_color(cls, is_hovered: bool) -> QColor:
        """Get background color based on hover state."""
        return cls.BACKGROUND_HOVER if is_hovered else cls.BACKGROUND_NORMAL


class ExposedPortStyle:
    """Style constants for exposed port indicators."""

    SIZE = 10
    BORDER_DARKEN = 130
    BORDER_WIDTH = 1.5
    MARGIN = 12
    SPACING = 14
