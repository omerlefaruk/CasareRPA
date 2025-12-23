"""
Port Shape Legend Panel for CasareRPA Canvas.

Provides a visual reference for port shapes and colors to help users
understand connection types at a glance.

Features:
- Auto-hide overlay that appears in canvas corner (top-right)
- Shows on: F1 key, hover on "?" button, or first-time user
- Auto-hides after 5 seconds idle (reset on hover)
- Pin button to keep visible permanently
- Draggable to any position when pinned
- First-time users: auto-show for 10s with "Pin to keep visible" hint
"""

from loguru import logger
from PySide6.QtCore import QPoint, QSettings, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.application.services.port_type_service import get_port_type_registry
from casare_rpa.domain.ports.port_type_interfaces import PortShape
from casare_rpa.domain.value_objects.types import DataType

# ============================================================================
# LEGEND DATA
# ============================================================================

# Legend entries: (shape_char, label, color_hex, description)
# Based on port_shapes.py and port_type_service.py
LEGEND_ENTRIES: list[tuple[str, str, str, str]] = [
    ("", "Execution", "#FFFFFF", "Control flow between nodes"),
    ("", "String", "#FFC107", "Text data"),
    ("", "Integer", "#4CAF50", "Whole numbers"),
    ("", "Float", "#8BC34A", "Decimal numbers"),
    ("", "Boolean", "#9C27B0", "True/False values"),
    ("", "List", "#FF9800", "Array of values"),
    ("", "Dict", "#FF5722", "Key-value mapping"),
    ("", "Page", "#2196F3", "Browser page"),
    ("", "Element", "#00BCD4", "Web element"),
    ("", "Any", "#969696", "Wildcard type"),
]


# ============================================================================
# PORT SHAPE ICONS
# ============================================================================


class PortShapeIcon(QWidget):
    """Widget that renders a port shape with its type color."""

    def __init__(
        self,
        shape: PortShape,
        color: QColor,
        size: int = 16,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize port shape icon.

        Args:
            shape: The PortShape enum value
            color: QColor for fill
            size: Icon size in pixels
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._shape = shape
        self._color = color
        self._size = size
        self.setFixedSize(size + 4, size + 4)

    def paintEvent(self, event) -> None:
        """Paint the port shape."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center coordinates
        cx = self.width() / 2
        cy = self.height() / 2
        half = self._size / 2 - 1

        # Set colors
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)

        if self._shape == PortShape.TRIANGLE:
            # Right-pointing triangle for exec ports
            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPolygonF

            points = [
                QPointF(cx - half * 0.6, cy - half),
                QPointF(cx + half, cy),
                QPointF(cx - half * 0.6, cy + half),
            ]
            painter.drawPolygon(QPolygonF(points))

        elif self._shape == PortShape.CIRCLE:
            painter.drawEllipse(int(cx - half), int(cy - half), int(half * 2), int(half * 2))

        elif self._shape == PortShape.DIAMOND:
            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPolygonF

            points = [
                QPointF(cx, cy - half),
                QPointF(cx + half, cy),
                QPointF(cx, cy + half),
                QPointF(cx - half, cy),
            ]
            painter.drawPolygon(QPolygonF(points))

        elif self._shape == PortShape.SQUARE:
            painter.drawRect(int(cx - half), int(cy - half), int(half * 2), int(half * 2))

        elif self._shape == PortShape.HEXAGON:
            import math

            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPolygonF

            points = []
            for i in range(6):
                angle = math.pi / 6 + i * math.pi / 3
                x = cx + half * math.cos(angle)
                y = cy + half * math.sin(angle)
                points.append(QPointF(x, y))
            painter.drawPolygon(QPolygonF(points))

        elif self._shape == PortShape.HOLLOW_CIRCLE:
            # Draw border only
            painter.setBrush(Qt.BrushStyle.NoBrush)
            from PySide6.QtGui import QPen

            painter.setPen(QPen(self._color, 2))
            painter.drawEllipse(int(cx - half), int(cy - half), int(half * 2), int(half * 2))

        elif self._shape == PortShape.ROUNDED_SQUARE:
            from PySide6.QtCore import QRectF

            rect = QRectF(cx - half, cy - half, half * 2, half * 2)
            painter.drawRoundedRect(rect, 3, 3)

        elif self._shape == PortShape.PENTAGON:
            import math

            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPolygonF

            points = []
            for i in range(5):
                angle = -math.pi / 2 + i * 2 * math.pi / 5
                x = cx + half * math.cos(angle)
                y = cy + half * math.sin(angle)
                points.append(QPointF(x, y))
            painter.drawPolygon(QPolygonF(points))

        elif self._shape == PortShape.CIRCLE_DOT:
            # Outer circle
            painter.drawEllipse(int(cx - half), int(cy - half), int(half * 2), int(half * 2))
            # Inner dot
            from PySide6.QtGui import QPen

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#252526"))
            dot_size = half * 0.4
            painter.drawEllipse(
                int(cx - dot_size),
                int(cy - dot_size),
                int(dot_size * 2),
                int(dot_size * 2),
            )

        painter.end()


# ============================================================================
# LEGEND ROW WIDGET
# ============================================================================


class LegendRow(QWidget):
    """Single row in the legend showing shape, type name, and description."""

    def __init__(
        self,
        data_type: DataType | None,
        is_exec: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize legend row.

        Args:
            data_type: DataType for this row (None for exec)
            is_exec: True if this is the execution flow row
            parent: Optional parent widget
        """
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        registry = get_port_type_registry()

        # Get shape and color
        if is_exec:
            shape = PortShape.TRIANGLE
            rgba = registry.get_exec_color()
            type_name = "Execution"
            description = "Control flow"
        else:
            shape = registry.get_type_shape(data_type)
            rgba = registry.get_type_color(data_type)
            info = registry.get_type_info(data_type)
            type_name = info.display_name
            description = info.description

        color = QColor(rgba[0], rgba[1], rgba[2], rgba[3])

        # Shape icon
        icon = PortShapeIcon(shape, color, size=14)
        layout.addWidget(icon)

        # Type name label
        name_label = QLabel(type_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {color.name()};
                font-weight: 600;
                font-size: 11px;
                min-width: 70px;
            }}
        """)
        layout.addWidget(name_label)

        # Description (optional, truncated)
        if description:
            desc_label = QLabel(description[:30])
            desc_label.setStyleSheet("""
                QLabel {
                    color: #808080;
                    font-size: 10px;
                }
            """)
            layout.addWidget(desc_label, 1)
        else:
            layout.addStretch(1)


# ============================================================================
# PORT LEGEND PANEL
# ============================================================================


class PortLegendPanel(QFrame):
    """
    Port Shape Legend overlay panel.

    Features:
    - Auto-hide after 5 seconds idle
    - Pin button to keep visible
    - Draggable when pinned
    - Position/pin state saved to QSettings
    """

    # Signal emitted when panel visibility changes
    visibility_changed = Signal(bool)

    # Settings keys
    SETTINGS_KEY_PINNED = "port_legend/pinned"
    SETTINGS_KEY_POS_X = "port_legend/pos_x"
    SETTINGS_KEY_POS_Y = "port_legend/pos_y"
    SETTINGS_KEY_FIRST_TIME = "port_legend/first_time_shown"

    # Timing constants
    AUTO_HIDE_MS = 5000  # 5 seconds
    FIRST_TIME_SHOW_MS = 10000  # 10 seconds for first-time users

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize port legend panel.

        Args:
            parent: Optional parent widget (usually the canvas)
        """
        super().__init__(parent)

        # State
        self._is_pinned = False
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self._mouse_inside = False
        self._is_first_time = False

        # Auto-hide timer
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._on_auto_hide)

        # Setup UI
        self._setup_ui()
        self._apply_styles()
        self._add_shadow()

        # Load saved state
        self._load_settings()

        # Start hidden
        self.hide()

        logger.debug("PortLegendPanel initialized")

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container frame (for styling)
        self._container = QFrame(self)
        main_layout.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header with title and pin button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 8, 4)
        header_layout.setSpacing(4)

        title = QLabel("PORT LEGEND")
        title.setStyleSheet("""
            QLabel {
                color: #D4D4D4;
                font-weight: 600;
                font-size: 11px;
                letter-spacing: 1px;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Pin button
        self._pin_button = QPushButton()
        self._pin_button.setFixedSize(24, 24)
        self._pin_button.setCheckable(True)
        self._pin_button.setToolTip("Pin to keep visible")
        self._pin_button.clicked.connect(self._on_pin_toggled)
        self._update_pin_button()
        header_layout.addWidget(self._pin_button)

        container_layout.addWidget(header)

        # First-time hint (hidden by default)
        self._hint_label = QLabel("Press F1 or click here to show")
        self._hint_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 10px;
                font-style: italic;
                padding: 0 12px;
            }
        """)
        self._hint_label.hide()
        container_layout.addWidget(self._hint_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #3E3E42;")
        separator.setFixedHeight(1)
        container_layout.addWidget(separator)

        # Legend content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 8)
        content_layout.setSpacing(0)

        # Add execution row first
        exec_row = LegendRow(None, is_exec=True)
        content_layout.addWidget(exec_row)

        # Add data type rows
        data_types = [
            DataType.STRING,
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.BOOLEAN,
            DataType.LIST,
            DataType.DICT,
            DataType.PAGE,
            DataType.ELEMENT,
            DataType.ANY,
        ]

        for dt in data_types:
            row = LegendRow(dt)
            content_layout.addWidget(row)

        container_layout.addWidget(content)

        # Set fixed size based on content
        self.setFixedWidth(220)
        self.adjustSize()

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ styling."""
        self._container.setStyleSheet("""
            QFrame {
                background: rgba(37, 37, 38, 0.95);
                border: 1px solid #3E3E42;
                border-radius: 6px;
            }
        """)

        self._pin_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2A2D2E;
            }
            QPushButton:checked {
                background: #007ACC;
            }
        """)

    def _add_shadow(self) -> None:
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self._container.setGraphicsEffect(shadow)

    def _update_pin_button(self) -> None:
        """Update pin button text based on state."""
        # Use text instead of emoji for better cross-platform compatibility
        if self._is_pinned:
            self._pin_button.setText("X")
            self._pin_button.setToolTip("Unpin (legend will auto-hide)")
        else:
            self._pin_button.setText("o")
            self._pin_button.setToolTip("Pin to keep visible")
        self._pin_button.setChecked(self._is_pinned)

    def _load_settings(self) -> None:
        """Load saved position and pin state from QSettings."""
        settings = QSettings("CasareRPA", "Canvas")

        self._is_pinned = settings.value(self.SETTINGS_KEY_PINNED, False, type=bool)
        self._update_pin_button()

        # Check if first time
        first_time_shown = settings.value(self.SETTINGS_KEY_FIRST_TIME, False, type=bool)
        self._is_first_time = not first_time_shown

        # Load position if saved
        pos_x = settings.value(self.SETTINGS_KEY_POS_X, -1, type=int)
        pos_y = settings.value(self.SETTINGS_KEY_POS_Y, -1, type=int)

        if pos_x >= 0 and pos_y >= 0:
            self.move(pos_x, pos_y)

    def _save_settings(self) -> None:
        """Save current position and pin state to QSettings."""
        settings = QSettings("CasareRPA", "Canvas")

        settings.setValue(self.SETTINGS_KEY_PINNED, self._is_pinned)
        settings.setValue(self.SETTINGS_KEY_POS_X, self.x())
        settings.setValue(self.SETTINGS_KEY_POS_Y, self.y())
        settings.setValue(self.SETTINGS_KEY_FIRST_TIME, True)

    def _position_default(self) -> None:
        """Position panel in top-right corner of parent."""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = 60  # Below toolbar area
            self.move(max(0, x), y)

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def show_legend(self, is_first_time: bool = False) -> None:
        """
        Show the legend panel.

        Args:
            is_first_time: If True, shows for longer with hint text
        """
        # Position if not already positioned
        if self.x() <= 0 or self.y() <= 0:
            self._position_default()

        # Show hint for first-time users
        if is_first_time and self._is_first_time:
            self._hint_label.setText("Pin to keep visible")
            self._hint_label.show()
            self._is_first_time = False
            self._save_settings()  # Mark as shown
        else:
            self._hint_label.hide()

        self.show()
        self.raise_()
        self.visibility_changed.emit(True)

        # Start auto-hide timer if not pinned
        if not self._is_pinned:
            timeout = self.FIRST_TIME_SHOW_MS if is_first_time else self.AUTO_HIDE_MS
            self._auto_hide_timer.start(timeout)

        logger.debug(f"Legend shown (pinned={self._is_pinned})")

    def hide_legend(self) -> None:
        """Hide the legend panel."""
        self._auto_hide_timer.stop()
        self.hide()
        self.visibility_changed.emit(False)
        logger.debug("Legend hidden")

    def toggle_legend(self) -> None:
        """Toggle legend visibility."""
        if self.isVisible():
            self.hide_legend()
        else:
            self.show_legend()

    def is_pinned(self) -> bool:
        """Check if legend is pinned."""
        return self._is_pinned

    def set_pinned(self, pinned: bool) -> None:
        """
        Set pinned state.

        Args:
            pinned: True to pin, False to unpin
        """
        self._is_pinned = pinned
        self._update_pin_button()
        self._save_settings()

        if pinned:
            self._auto_hide_timer.stop()
        elif self.isVisible():
            self._auto_hide_timer.start(self.AUTO_HIDE_MS)

    def show_first_time_hint(self) -> None:
        """Show legend for first-time users with extended visibility."""
        if self._is_first_time:
            self.show_legend(is_first_time=True)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def _on_pin_toggled(self) -> None:
        """Handle pin button click."""
        self._is_pinned = self._pin_button.isChecked()
        self._update_pin_button()
        self._save_settings()

        if self._is_pinned:
            self._auto_hide_timer.stop()
            self._hint_label.hide()
            logger.debug("Legend pinned")
        else:
            self._auto_hide_timer.start(self.AUTO_HIDE_MS)
            logger.debug("Legend unpinned")

    def _on_auto_hide(self) -> None:
        """Handle auto-hide timer timeout."""
        if not self._is_pinned and not self._mouse_inside:
            self.hide_legend()

    def enterEvent(self, event) -> None:
        """Handle mouse enter - pause auto-hide."""
        self._mouse_inside = True
        self._auto_hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave - restart auto-hide if not pinned."""
        self._mouse_inside = False
        if not self._is_pinned and self.isVisible():
            self._auto_hide_timer.start(self.AUTO_HIDE_MS)
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_pinned:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for dragging."""
        if self._is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            # Constrain to parent bounds
            if self.parent():
                parent_rect = self.parent().rect()
                new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - self.height())))
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - save position."""
        if self._is_dragging:
            self._is_dragging = False
            self._save_settings()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        # Start auto-hide if not pinned
        if not self._is_pinned:
            self._auto_hide_timer.start(self.AUTO_HIDE_MS)

    def hideEvent(self, event) -> None:
        """Handle hide event."""
        self._auto_hide_timer.stop()
        super().hideEvent(event)
