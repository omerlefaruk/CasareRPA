"""
Frame Style Manager

Centralized styling for NodeFrame components.
Consolidates color palettes, themes, and style application logic.

Following Single Responsibility Principle - this module handles ONLY visual styling.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS

# ============================================================================
# FRAME COLOR PALETTE (v2)
# ============================================================================
FRAME_COLORS: dict[str, QColor] = {
    "gray": QColor(THEME.text_muted),
    "blue": QColor(THEME.primary),
    "green": QColor(THEME.success),
    "yellow": QColor(THEME.warning),
    "orange": QColor(THEME.info),
    "red": QColor(THEME.error),
    "purple": QColor(THEME.secondary),
    "pink": QColor(THEME.category_control_flow),
    "cyan": QColor(THEME.category_database),
    "teal": QColor(THEME.wire_dict),
}

# ============================================================================
# DEFAULT COLORS
# ============================================================================
DEFAULT_FRAME_COLOR = FRAME_COLORS["blue"]
DEFAULT_PORT_COLOR = QColor(THEME.wire_data)


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
    def get_frame_color(color_name: str | None = None) -> QColor:
        """
        Get a frame color by name (or hex string).

        Args:
            color_name: Color name from FRAME_COLORS or a hex string.

        Returns:
            QColor for the frame
        """
        if not color_name:
            return DEFAULT_FRAME_COLOR

        if color_name in FRAME_COLORS:
            return FRAME_COLORS[color_name]

        if isinstance(color_name, str) and color_name.startswith("#"):
            color = QColor(color_name)
            if color.isValid():
                return color

        return DEFAULT_FRAME_COLOR

    @staticmethod
    def create_frame_brush(color: QColor) -> QBrush:
        """Create brush for frame fill."""
        fill = QColor(color)
        fill.setAlpha(28)
        return QBrush(fill)

    @staticmethod
    def create_frame_pen(
        color: QColor,
        width: int = 1,
        style: Qt.PenStyle = Qt.PenStyle.DashLine,
        darken_factor: int = 120,
    ) -> QPen:
        """
        Create pen for frame border.

        Args:
            color: Base color
            width: Line width
            style: Pen style (solid, dash, etc.)
            darken_factor: How much to darken the color (TOKENS.sizes.button_width_sm = no change)

        Returns:
            QPen for drawing frame border
        """
        stroke = QColor(color)
        stroke.setAlpha(200)
        pen = QPen(stroke.darker(darken_factor), width)
        pen.setStyle(style)
        return pen

    @staticmethod
    def get_selection_pen() -> QPen:
        """Get pen for selected frame highlight."""
        pen = QPen(QColor(THEME.node_selected), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        return pen

    @staticmethod
    def get_drop_target_pen() -> QPen:
        """Get pen for drop target highlight."""
        pen = QPen(QColor(THEME.success), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        return pen

    @staticmethod
    def get_drop_target_brush() -> QBrush:
        """Get brush for drop target fill."""
        color = QColor(THEME.success)
        color.setAlpha(40)
        return QBrush(color)

    @staticmethod
    def get_collapsed_pen(color: QColor) -> QPen:
        """Get pen for collapsed frame border."""
        pen = QPen(color.darker(130), 1)
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
                    from casare_rpa.application.services.port_type_service import (
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
        color = QColor(THEME.text_primary)
        color.setAlpha(180)  # Semi-transparent
        return color

    @staticmethod
    def get_node_count_color(frame_color: QColor) -> QColor:
        """Get color for collapsed node count text."""
        return frame_color.lighter(180)


class CollapseButtonStyle:
    """Style constants for collapse button."""

    SIZE = 16
    MARGIN = 4
    SYMBOL_SIZE = 8
    CORNER_RADIUS = TOKENS.radius.sm

    # Colors (from unified theme)
    BACKGROUND_NORMAL = QColor(THEME.bg_component)
    BACKGROUND_NORMAL.setAlpha(180)  # Semi-transparent
    BACKGROUND_HOVER = QColor(THEME.bg_hover)
    BORDER_COLOR = QColor(THEME.border)
    SYMBOL_COLOR = QColor(THEME.text_secondary)

    @classmethod
    def get_background_color(cls, is_hovered: bool) -> QColor:
        """Get background color based on hover state."""
        return cls.BACKGROUND_HOVER if is_hovered else cls.BACKGROUND_NORMAL


class ExposedPortStyle:
    """Style constants for exposed port indicators."""

    SIZE = 10
    BORDER_DARKEN = 130
    BORDER_WIDTH = 1
    MARGIN = 4
    SPACING = 8

