"""
Port Shape Drawing Functions for CasareRPA Canvas.

Provides shape rendering for different data types to ensure accessibility
for color-blind users. Each DataType has a distinct shape in addition to color.

References:
- "The Design of Everyday Things" by Don Norman - Accessibility & Affordances
- WCAG 2.1 - Don't rely on color alone to convey information
"""

import math
from typing import Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF

from casare_rpa.application.services.port_type_service import get_port_type_registry
from casare_rpa.domain.port_type_system import PortShape
from casare_rpa.domain.value_objects.types import DataType

# ============================================================================
# SHAPE DRAWING FUNCTIONS
# ============================================================================


def draw_circle(
    painter: QPainter,
    center: QPointF,
    radius: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
) -> None:
    """
    Draw a filled circle (default shape for most types).

    Args:
        painter: QPainter to draw with
        center: Center point of the circle
        radius: Radius of the circle
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
    """
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawEllipse(center, radius, radius)


def draw_hollow_circle(
    painter: QPainter,
    center: QPointF,
    radius: float,
    border_color: QColor,
    border_width: float = 2.0,
) -> None:
    """
    Draw a hollow circle (for ANY/wildcard type).

    Args:
        painter: QPainter to draw with
        center: Center point of the circle
        radius: Radius of the circle
        border_color: Border color
        border_width: Border line width
    """
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(center, radius, radius)


def draw_diamond(
    painter: QPainter,
    center: QPointF,
    size: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
) -> None:
    """
    Draw a diamond shape (for BOOLEAN type).

    Args:
        painter: QPainter to draw with
        center: Center point
        size: Size (distance from center to vertex)
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
    """
    half = size
    points = [
        QPointF(center.x(), center.y() - half),  # Top
        QPointF(center.x() + half, center.y()),  # Right
        QPointF(center.x(), center.y() + half),  # Bottom
        QPointF(center.x() - half, center.y()),  # Left
    ]

    polygon = QPolygonF(points)
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawPolygon(polygon)


def draw_square(
    painter: QPainter,
    center: QPointF,
    size: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
) -> None:
    """
    Draw a square (for LIST type).

    Args:
        painter: QPainter to draw with
        center: Center point
        size: Half-width of the square
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
    """
    rect = QRectF(
        center.x() - size,
        center.y() - size,
        size * 2,
        size * 2,
    )

    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawRect(rect)


def draw_rounded_square(
    painter: QPainter,
    center: QPointF,
    size: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
    corner_radius: float = 3.0,
) -> None:
    """
    Draw a rounded square (for PAGE type).

    Args:
        painter: QPainter to draw with
        center: Center point
        size: Half-width of the square
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
        corner_radius: Radius of rounded corners
    """
    rect = QRectF(
        center.x() - size,
        center.y() - size,
        size * 2,
        size * 2,
    )

    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawRoundedRect(rect, corner_radius, corner_radius)


def draw_hexagon(
    painter: QPainter,
    center: QPointF,
    size: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
) -> None:
    """
    Draw a hexagon (for DICT type).

    Args:
        painter: QPainter to draw with
        center: Center point
        size: Radius (center to vertex)
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
    """
    points = []
    for i in range(6):
        angle = math.pi / 6 + i * math.pi / 3  # Start at 30 degrees
        x = center.x() + size * math.cos(angle)
        y = center.y() + size * math.sin(angle)
        points.append(QPointF(x, y))

    polygon = QPolygonF(points)
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawPolygon(polygon)


def draw_pentagon(
    painter: QPainter,
    center: QPointF,
    size: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
) -> None:
    """
    Draw a pentagon (for ELEMENT type).

    Args:
        painter: QPainter to draw with
        center: Center point
        size: Radius (center to vertex)
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
    """
    points = []
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5  # Start at top
        x = center.x() + size * math.cos(angle)
        y = center.y() + size * math.sin(angle)
        points.append(QPointF(x, y))

    polygon = QPolygonF(points)
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawPolygon(polygon)


def draw_triangle(
    painter: QPainter,
    center: QPointF,
    size: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
    pointing_right: bool = True,
) -> None:
    """
    Draw a triangle (for EXEC ports - execution flow).

    Args:
        painter: QPainter to draw with
        center: Center point
        size: Size of the triangle
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
        pointing_right: If True, points right; if False, points left
    """
    if pointing_right:
        # Right-pointing triangle (for output exec ports)
        points = [
            QPointF(center.x() - size * 0.6, center.y() - size),
            QPointF(center.x() + size, center.y()),
            QPointF(center.x() - size * 0.6, center.y() + size),
        ]
    else:
        # Left-pointing triangle (for input exec ports)
        points = [
            QPointF(center.x() + size * 0.6, center.y() - size),
            QPointF(center.x() - size, center.y()),
            QPointF(center.x() + size * 0.6, center.y() + size),
        ]

    polygon = QPolygonF(points)
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawPolygon(polygon)


def draw_circle_with_dot(
    painter: QPainter,
    center: QPointF,
    radius: float,
    fill_color: QColor,
    border_color: QColor,
    border_width: float = 1.5,
) -> None:
    """
    Draw a circle with a center dot (for BROWSER type).

    Args:
        painter: QPainter to draw with
        center: Center point
        radius: Outer radius
        fill_color: Fill color
        border_color: Border color
        border_width: Border line width
    """
    # Draw outer circle
    painter.setPen(QPen(border_color, border_width))
    painter.setBrush(QBrush(fill_color))
    painter.drawEllipse(center, radius, radius)

    # Draw center dot
    dot_radius = radius * 0.35
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(border_color))
    painter.drawEllipse(center, dot_radius, dot_radius)


# ============================================================================
# MAIN DISPATCH FUNCTION
# ============================================================================


def draw_port_shape(
    painter: QPainter,
    center: QPointF,
    size: float,
    data_type: DataType | None,
    fill_color: tuple[int, int, int, int],
    border_color: tuple[int, int, int, int] | None = None,
    is_exec: bool = False,
    is_output: bool = False,
) -> None:
    """
    Draw the appropriate port shape based on data type.

    Args:
        painter: QPainter to draw with
        center: Center point of the port
        size: Size/radius of the port
        data_type: The DataType (None for exec ports)
        fill_color: RGBA tuple for fill color
        border_color: RGBA tuple for border (darker fill if None)
        is_exec: True if this is an execution flow port
        is_output: True if this is an output port (affects triangle direction)
    """
    # Convert color tuples to QColor
    fill_qcolor = QColor(*fill_color)

    if border_color:
        border_qcolor = QColor(*border_color)
    else:
        # Default: darker version of fill color
        border_qcolor = QColor(
            max(0, fill_color[0] - 40),
            max(0, fill_color[1] - 40),
            max(0, fill_color[2] - 40),
            fill_color[3],
        )

    # Enable antialiasing for smooth shapes
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Exec ports always use triangle
    if is_exec or data_type is None:
        draw_triangle(painter, center, size, fill_qcolor, border_qcolor, pointing_right=is_output)
        return

    # Get shape for data type
    registry = get_port_type_registry()
    shape = registry.get_type_shape(data_type)

    # Dispatch to appropriate drawing function
    if shape == PortShape.DIAMOND:
        draw_diamond(painter, center, size, fill_qcolor, border_qcolor)
    elif shape == PortShape.SQUARE:
        draw_square(painter, center, size, fill_qcolor, border_qcolor)
    elif shape == PortShape.HEXAGON:
        draw_hexagon(painter, center, size, fill_qcolor, border_qcolor)
    elif shape == PortShape.HOLLOW_CIRCLE:
        draw_hollow_circle(painter, center, size, border_qcolor)
    elif shape == PortShape.ROUNDED_SQUARE:
        draw_rounded_square(painter, center, size, fill_qcolor, border_qcolor)
    elif shape == PortShape.CIRCLE_DOT:
        draw_circle_with_dot(painter, center, size, fill_qcolor, border_qcolor)
    elif shape == PortShape.PENTAGON:
        draw_pentagon(painter, center, size, fill_qcolor, border_qcolor)
    elif shape == PortShape.TRIANGLE:
        draw_triangle(painter, center, size, fill_qcolor, border_qcolor, pointing_right=is_output)
    else:
        # Default: circle
        draw_circle(painter, center, size, fill_qcolor, border_qcolor)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_shape_for_type(data_type: DataType | None) -> str:
    """
    Get the shape name for a data type.

    Args:
        data_type: The DataType (None for exec)

    Returns:
        Shape name string
    """
    if data_type is None:
        return "triangle"

    registry = get_port_type_registry()
    shape = registry.get_type_shape(data_type)
    return shape.name.lower()


def get_shape_description(data_type: DataType | None) -> str:
    """
    Get a human-readable description of the shape for a type.

    Useful for tooltips and accessibility.

    Args:
        data_type: The DataType (None for exec)

    Returns:
        Description string
    """
    if data_type is None:
        return "Triangle (execution flow)"

    registry = get_port_type_registry()
    shape = registry.get_type_shape(data_type)
    info = registry.get_type_info(data_type)

    shape_descriptions = {
        PortShape.CIRCLE: "Circle",
        PortShape.DIAMOND: "Diamond",
        PortShape.SQUARE: "Square",
        PortShape.HEXAGON: "Hexagon",
        PortShape.HOLLOW_CIRCLE: "Hollow circle",
        PortShape.ROUNDED_SQUARE: "Rounded square",
        PortShape.CIRCLE_DOT: "Circle with dot",
        PortShape.PENTAGON: "Pentagon",
        PortShape.TRIANGLE: "Triangle",
    }

    shape_name = shape_descriptions.get(shape, "Circle")
    return f"{shape_name} ({info.display_name})"
