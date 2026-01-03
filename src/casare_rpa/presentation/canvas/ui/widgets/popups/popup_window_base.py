"""
PopupWindowBase - V2 Popup Window Component.

Base class for all v2 popup windows in CasareRPA.
Provides consistent behavior: draggable, resizable, click-outside-to-close,
pin state, escape key handling, and screen-boundary clamping.

Features:
- Draggable header region (following NodeOutputPopup pattern)
- Optional corner resize grips
- Click-outside-to-close (via PopupManager)
- Pin state integration
- Close-on-escape behavior
- Positioning helpers (anchor-to-widget + screen-boundary clamp)
- THEME_V2 styling (no animations, no shadows, crisp borders)

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

    class MyPopup(PopupWindowBase):
        def __init__(self, parent=None):
            super().__init__(
                title="My Popup",
                parent=parent,
                resizable=True,
                pin_button=True,
            )
            # Add content widget
            content = QWidget()
            self.set_content_widget(content)

Signals:
    closed: Emitted when popup is closed
    pin_changed: Emitted when pin state changes (bool: pinned)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QPoint, QRect, Qt, Signal, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager
from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2

if TYPE_CHECKING:
    from PySide6.QtGui import QKeyEvent


class AnchorPosition(Enum):
    """Position relative to anchor widget."""

    BELOW = "below"
    ABOVE = "above"
    LEFT = "left"
    RIGHT = "right"


class DraggableHeader(QFrame):
    """Header that supports dragging to move the parent window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._parent_window: QWidget | None = None
        self._is_dragging: bool = False
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def set_parent_window(self, window: QWidget) -> None:
        """Set the window to be moved when dragging."""
        self._parent_window = window

    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self._is_dragging

    @Slot()
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start drag on left click."""
        if event.button() == Qt.MouseButton.LeftButton and self._parent_window:
            self._drag_pos = event.globalPos() - self._parent_window.pos()
            self._is_dragging = True
            event.accept()
        else:
            super().mousePressEvent(event)

    @Slot()
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move window while dragging."""
        if self._drag_pos is not None and self._parent_window:
            self._parent_window.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    @Slot()
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End drag."""
        self._drag_pos = None
        self._is_dragging = False
        super().mouseReleaseEvent(event)


class PopupWindowBase(QWidget):
    """
    Base class for v2 popup windows.

    Provides consistent popup behavior:
    - Draggable header
    - Optional corner resize
    - Click-outside-to-close (via PopupManager)
    - Pin state (ignore click-outside when pinned)
    - Escape key closes
    - Screen-boundary clamping
    - Anchor positioning helpers

    Signals:
        closed: Emitted when popup is closed
        pin_changed: Emitted when pin state changes (bool)
    """

    closed = Signal()
    pin_changed = Signal(bool)

    # Default dimensions
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 300
    MIN_WIDTH = 200
    MIN_HEIGHT = 150

    # Resize edge margin
    RESIZE_MARGIN = 8

    def __init__(
        self,
        title: str = "Popup",
        parent: QWidget | None = None,
        resizable: bool = True,
        pin_button: bool = True,
        close_button: bool = True,
        min_width: int = 300,
        min_height: int = 200,
    ) -> None:
        """
        Initialize popup window.

        Args:
            title: Header title text
            parent: Parent widget
            resizable: Enable corner resize grips
            pin_button: Show pin button in header
            close_button: Show close button in header
            min_width: Minimum width constraint
            min_height: Minimum height constraint
        """
        super().__init__(parent)

        self._title: str = title
        self._resizable: bool = resizable
        self._pin_button_enabled: bool = pin_button
        self._close_button_enabled: bool = close_button
        self._is_pinned: bool = False

        # Resize state
        self._resize_edge: str | None = None
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geometry: QRect | None = None

        # Content widget
        self._content_widget: QWidget | None = None

        # UI components
        self._header: DraggableHeader | None = None
        self._pin_btn: QPushButton | None = None
        self._close_btn: QPushButton | None = None
        self._title_label: QLabel | None = None

        # Setup
        self._setup_window()
        self._setup_ui(min_width, min_height)

        # Event filter for escape key (installed after content is set)
        self._escape_filter_widgets: list[QWidget] = []

    def _setup_window(self) -> None:
        """Setup window flags and attributes."""
        # Tool window for proper popup behavior
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Enable mouse tracking for cursor changes
        self.setMouseTracking(True)

    def _setup_ui(self, min_width: int, min_height: int) -> None:
        """Setup the UI layout."""
        self.setMinimumSize(min_width, min_height)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container for rounded corners
        container = QFrame()
        container.setObjectName("popupContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        self._header = self._create_header()
        self._header.set_parent_window(self)
        container_layout.addWidget(self._header)

        # Content area (placeholder, replaced by set_content_widget)
        self._content_area = QFrame()
        self._content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(self._content_area)
        content_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
        )
        container_layout.addWidget(self._content_area)

        main_layout.addWidget(container)

        self._apply_styles()

    def _create_header(self) -> DraggableHeader:
        """Create the draggable header."""
        header = DraggableHeader()
        header.setObjectName("header")
        header.setFixedHeight(32)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(
            TOKENS_V2.spacing.sm,  # left
            0,
            TOKENS_V2.spacing.xs,  # right
            0,
        )
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Title
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            color: {THEME_V2.text_primary};
            font-size: {TOKENS_V2.typography.body_sm}px;
            font-weight: {TOKENS_V2.typography.weight_medium};
        """)
        layout.addWidget(self._title_label)

        layout.addStretch()

        # Pin button
        if self._pin_button_enabled:
            self._pin_btn = QPushButton("○")
            self._pin_btn.setFixedSize(20, 20)
            self._pin_btn.setToolTip("Pin (keep open)")
            self._pin_btn.setCheckable(True)
            self._pin_btn.clicked.connect(self._on_pin_clicked)
            self._pin_btn.setStyleSheet(self._get_header_button_style())
            layout.addWidget(self._pin_btn)

        # Close button
        if self._close_button_enabled:
            self._close_btn = QPushButton("×")
            self._close_btn.setFixedSize(20, 20)
            self._close_btn.setToolTip("Close")
            self._close_btn.clicked.connect(self.close)
            self._close_btn.setStyleSheet(self._get_header_button_style())
            layout.addWidget(self._close_btn)

        return header

    def _get_header_button_style(self) -> str:
        """Get stylesheet for header buttons."""
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {TOKENS_V2.radius.xs}px;
                color: {THEME_V2.text_secondary};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME_V2.bg_hover};
                color: {THEME_V2.text_primary};
            }}
            QPushButton:checked {{
                color: {THEME_V2.primary};
            }}
        """

    def _apply_styles(self) -> None:
        """Apply v2 dark theme styling."""
        self.setStyleSheet(f"""
            PopupWindowBase {{
                background: transparent;
            }}
            QFrame#popupContainer {{
                background-color: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
            }}
            QFrame#header {{
                background-color: {THEME_V2.bg_component};
                border-top-left-radius: {TOKENS_V2.radius.md}px;
                border-top-right-radius: {TOKENS_V2.radius.md}px;
                border-bottom: 1px solid {THEME_V2.border};
            }}
            QFrame#contentArea {{
                background-color: {THEME_V2.bg_elevated};
                border-bottom-left-radius: {TOKENS_V2.radius.md}px;
                border-bottom-right-radius: {TOKENS_V2.radius.md}px;
            }}
        """)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_title(self, title: str) -> None:
        """
        Update header title.

        Args:
            title: New title text
        """
        self._title = title
        if self._title_label:
            self._title_label.setText(title)

    def set_content_widget(self, widget: QWidget | None) -> None:
        """
        Set the main content widget (replaces existing).

        Args:
            widget: Content widget to display, or None to clear
        """
        # Remove old content
        if self._content_widget:
            self._content_area.layout().removeWidget(self._content_widget)
            self._content_widget.deleteLater()

        # Add new content (if provided)
        self._content_widget = widget
        if widget:
            self._content_area.layout().addWidget(widget)
            # Install escape key filter on content
            self._install_escape_filter(widget)

    def set_pinned(self, pinned: bool) -> None:
        """
        Set pin state (pinned popups ignore click-outside).

        Args:
            pinned: True to pin, False to unpin
        """
        if self._is_pinned == pinned:
            return

        self._is_pinned = pinned

        # Update button state
        if self._pin_btn:
            self._pin_btn.setChecked(pinned)
            self._pin_btn.setText("●" if pinned else "○")

        # Update window flags for PopupManager
        current_pos = self.pos()
        if pinned:
            # Convert to regular window when pinned
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        else:
            # Back to Tool window
            self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.move(current_pos)
        if self.isVisible():
            self.show()

        # Re-register with PopupManager to update pinned state
        PopupManager.register(self, pinned=self._is_pinned)
        self.pin_changed.emit(pinned)

    def is_pinned(self) -> bool:
        """Check if popup is pinned."""
        return self._is_pinned

    def is_dragging(self) -> bool:
        """Check if popup is currently being dragged."""
        return self._header is not None and self._header.is_dragging()

    def show_at_anchor(
        self,
        widget: QWidget,
        position: AnchorPosition = AnchorPosition.BELOW,
        offset: QPoint | None = None,
    ) -> None:
        """
        Show popup anchored to a widget with boundary clamping.

        Args:
            widget: Anchor widget
            position: Position relative to anchor
            offset: Optional offset from anchor position
        """
        if offset is None:
            offset = QPoint(0, 0)

        # Get widget global geometry
        widget_rect = widget.geometry()
        widget_top_left = widget.mapToGlobal(widget_rect.topLeft())
        widget_bottom_left = widget.mapToGlobal(widget_rect.bottomLeft())
        widget_top_right = widget.mapToGlobal(widget_rect.topRight())

        # Calculate popup position based on anchor position
        match position:
            case AnchorPosition.BELOW:
                pos = widget_bottom_left + offset
            case AnchorPosition.ABOVE:
                pos = widget_top_left - QPoint(0, self.height()) + offset
            case AnchorPosition.LEFT:
                pos = widget_top_left - QPoint(self.width(), 0) + offset
            case AnchorPosition.RIGHT:
                pos = widget_top_right + offset
            case _:
                pos = widget_bottom_left + offset

        self.show_at_position(pos)

    def show_at_position(self, global_pos: QPoint) -> None:
        """
        Show popup at global position with screen-boundary clamping.

        Args:
            global_pos: Global screen position
        """
        # Clamp to screen bounds
        clamped_pos = self._clamp_to_screen(global_pos)
        self.move(clamped_pos)
        self.show()

    # =========================================================================
    # Qt Event Handlers
    # =========================================================================

    @Slot()
    def showEvent(self, event) -> None:
        """Handle show event - register with PopupManager."""
        super().showEvent(event)
        PopupManager.register(self, pinned=self._is_pinned)
        self.activateWindow()
        self.raise_()

    @Slot()
    def closeEvent(self, event) -> None:
        """Handle close event - cleanup and emit signal."""
        PopupManager.unregister(self)

        # Remove event filters
        for widget in self._escape_filter_widgets:
            try:
                widget.removeEventFilter(self)
                if hasattr(widget, "viewport"):
                    widget.viewport().removeEventFilter(self)
            except RuntimeError as e:
                logger.debug(f"Widget already deleted during cleanup: {e}")
        self._escape_filter_widgets.clear()

        self.closed.emit()
        super().closeEvent(event)

    @Slot()
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events - Escape closes popup."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event) -> bool:
        """
        Event filter to catch Escape key from child widgets.

        Args:
            obj: The object receiving the event
            event: The event

        Returns:
            False to let event propagate, True to consume
        """
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
        return False

    def _install_escape_filter(self, widget: QWidget) -> None:
        """Install event filter on widget for Escape key handling."""
        if widget in self._escape_filter_widgets:
            return

        widget.installEventFilter(self)
        self._escape_filter_widgets.append(widget)

        # Also install on viewport for scroll-based widgets
        if hasattr(widget, "viewport"):
            widget.viewport().installEventFilter(self)

        # Recursively install on children
        for child in widget.findChildren(QWidget):
            if child not in self._escape_filter_widgets:
                child.installEventFilter(self)
                self._escape_filter_widgets.append(child)
                if hasattr(child, "viewport"):
                    child.viewport().installEventFilter(self)

    @Slot()
    def _on_pin_clicked(self) -> None:
        """Handle pin button click."""
        if self._pin_btn:
            self.set_pinned(self._pin_btn.isChecked())

    # =========================================================================
    # Resize Handling
    # =========================================================================

    def _get_resize_edge(self, pos: QPoint) -> str | None:
        """Determine which corner the mouse is near for resizing (corners only)."""
        if not self._resizable:
            return None

        m = self.RESIZE_MARGIN
        rect = self.rect()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()

        left = x < m
        right = x > w - m
        top = y < m
        bottom = y > h - m

        # Only allow corner resizing (not edges)
        if top and left:
            return "top-left"
        elif top and right:
            return "top-right"
        elif bottom and left:
            return "bottom-left"
        elif bottom and right:
            return "bottom-right"
        return None

    def _update_cursor_for_edge(self, edge: str | None) -> None:
        """Update cursor based on resize corner."""
        if edge is None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif edge in ("top-left", "bottom-right"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ("top-right", "bottom-left"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    @Slot()
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start resize on edge click."""
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    @Slot()
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle resize drag or update cursor."""
        if self._resize_edge and self._resize_start_pos and self._resizable:
            # Resizing in progress
            delta = event.globalPos() - self._resize_start_pos
            geo = self._resize_start_geometry

            new_x, new_y = geo.x(), geo.y()
            new_w, new_h = geo.width(), geo.height()

            edge = self._resize_edge
            if "left" in edge:
                new_x = geo.x() + delta.x()
                new_w = geo.width() - delta.x()
            if "right" in edge:
                new_w = geo.width() + delta.x()
            if "top" in edge:
                new_y = geo.y() + delta.y()
                new_h = geo.height() - delta.y()
            if "bottom" in edge:
                new_h = geo.height() + delta.y()

            # Enforce minimum size
            min_w = self.minimumWidth()
            min_h = self.minimumHeight()

            if new_w < min_w:
                if "left" in edge:
                    new_x = geo.x() + geo.width() - min_w
                new_w = min_w
            if new_h < min_h:
                if "top" in edge:
                    new_y = geo.y() + geo.height() - min_h
                new_h = min_h

            # Clamp to screen bounds
            screen = QApplication.primaryScreen().availableGeometry()
            if new_x < screen.left():
                new_x = screen.left()
            if new_y < screen.top():
                new_y = screen.top()
            if new_x + new_w > screen.right():
                new_w = screen.right() - new_x
            if new_y + new_h > screen.bottom():
                new_h = screen.bottom() - new_y

            self.setGeometry(new_x, new_y, new_w, new_h)
            event.accept()
        else:
            # Update cursor based on position
            edge = self._get_resize_edge(event.pos())
            self._update_cursor_for_edge(edge)
            super().mouseMoveEvent(event)

    @Slot()
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End resize."""
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        super().mouseReleaseEvent(event)

    # =========================================================================
    # Positioning Helpers
    # =========================================================================

    def _clamp_to_screen(self, pos: QPoint) -> QPoint:
        """
        Clamp position to screen boundaries.

        Args:
            pos: Desired position

        Returns:
            Clamped position that stays on screen
        """
        screen = QApplication.primaryScreen().availableGeometry()

        x = pos.x()
        y = pos.y()

        # Clamp right and bottom
        if x + self.width() > screen.right():
            x = screen.right() - self.width() - TOKENS_V2.spacing.xs
        if y + self.height() > screen.bottom():
            y = screen.bottom() - self.height() - TOKENS_V2.spacing.xs

        # Clamp left and top
        if x < screen.left():
            x = screen.left() + TOKENS_V2.spacing.xs
        if y < screen.top():
            y = screen.top() + TOKENS_V2.spacing.xs

        return QPoint(x, y)

