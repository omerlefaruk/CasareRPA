"""
ToastV2 - Non-modal notification popup.

Features:
- No animations (0ms fade - instant show/hide)
- Timer-based auto-dismiss (QTimer.singleShot, NOT QPropertyAnimation)
- Close button
- Level-based left border accent color
- Stacked toasts (top-right corner via ToastManager)
- Icon per level (INFO, SUCCESS, WARNING, ERROR)

Usage:
    toast = ToastV2(
        level=ToastLevel.SUCCESS,
        title="Success",
        message="Operation completed",
        duration_ms=3000,
        parent=None
    )
    toast.show()

Signals:
    dismissed: Signal() - Emitted when toast is dismissed (timer, close, or escape)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

from .popup_utils import ToastManager
from .popup_window_base import PopupWindowBase

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent, QShowEvent


class ToastLevel(Enum):
    """Toast notification levels."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ToastV2(PopupWindowBase):
    """
    Non-modal toast notification popup.

    Features:
    - No animations (instant show/hide)
    - Auto-dismiss timer
    - Level-based styling (border accent color + icon)
    - Stacked positioning via ToastManager
    - Minimal header (close button only, no title/pin)
    - Escape key closes

    Signals:
        dismissed: Emitted when toast closes (timer, close, or escape)
    """

    dismissed = Signal()

    # Default dimensions
    DEFAULT_WIDTH = 320
    DEFAULT_HEIGHT = 80
    MIN_WIDTH = 280
    MIN_HEIGHT = 60

    # Default duration (3 seconds)
    DEFAULT_DURATION_MS = 3000

    # Level configurations (border color, icon name)
    _LEVEL_CONFIG = {
        ToastLevel.INFO: {
            "color": THEME_V2.info,
            "icon": "info",
        },
        ToastLevel.SUCCESS: {
            "color": THEME_V2.success,
            "icon": "check",
        },
        ToastLevel.WARNING: {
            "color": THEME_V2.warning,
            "icon": "warning",
        },
        ToastLevel.ERROR: {
            "color": THEME_V2.error,
            "icon": "alert",
        },
    }

    def __init__(
        self,
        level: ToastLevel = ToastLevel.INFO,
        title: str = "",
        message: str = "",
        duration_ms: int = DEFAULT_DURATION_MS,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize toast notification.

        Args:
            level: Toast level (INFO, SUCCESS, WARNING, ERROR)
            title: Optional title text (bold, above message)
            message: Main message text (required)
            duration_ms: Auto-dismiss duration in ms (0 for no auto-dismiss)
            parent: Parent widget
        """
        # Store toast-specific config before base init
        self._toast_level = level
        self._toast_title = title
        self._toast_message = message
        self._duration_ms = duration_ms

        # Initialize base with minimal config
        # No pin button, no resize, minimal header
        super().__init__(
            title="",  # No title in header
            parent=parent,
            resizable=False,
            pin_button=False,
            close_button=True,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

        # Override window flags for non-modal behavior
        # Tool window + stay-on-top for visibility
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Set fixed size (toasts don't resize)
        self.setFixedSize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Auto-dismiss timer (QTimer, NOT QPropertyAnimation)
        self._dismiss_timer: QTimer | None = None

        # Build custom toast UI
        self._setup_toast_ui()

    def _setup_toast_ui(self) -> None:
        """Setup custom toast UI (override base header/content)."""
        # Clear base layout and rebuild
        layout = self.layout()
        if layout:
            # Remove the default container
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # Get level config
        config = self._LEVEL_CONFIG[self._toast_level]
        accent_color = config["color"]
        icon_name = config["icon"]

        # Main container with rounded corners
        container = QFrame()
        container.setObjectName("toastContainer")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Left border accent (4px wide)
        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(f"background-color: {accent_color};")
        container_layout.addWidget(accent_bar)

        # Content area
        content = QFrame()
        content.setObjectName("toastContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(
            TOKENS_V2.spacing.md,  # left
            TOKENS_V2.spacing.sm,  # top
            TOKENS_V2.spacing.md,  # right
            TOKENS_V2.spacing.sm,  # bottom
        )
        content_layout.setSpacing(TOKENS_V2.spacing.xs)
        container_layout.addWidget(content)

        # Header row (icon + title + close button)
        header_row = QHBoxLayout()
        header_row.setSpacing(TOKENS_V2.spacing.sm)

        # Icon (left side)
        icon_label = QLabel()
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = get_icon(icon_name, size=20, state="normal")
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(20, 20))
        header_row.addWidget(icon_label)

        # Title (bold, if provided)
        if self._toast_title:
            title_label = QLabel(self._toast_title)
            title_label.setObjectName("toastTitle")
            title_font = QFont()
            title_font.setPointSize(TOKENS_V2.typography.body)
            title_font.setWeight(QFont.Weight(TOKENS_V2.typography.weight_semibold))
            title_label.setFont(title_font)
            title_label.setStyleSheet(f"color: {THEME_V2.text_primary};")
            header_row.addWidget(title_label)

        header_row.addStretch()

        # Close button (small, top-right)
        close_btn = QPushButton("×")
        close_btn.setObjectName("toastCloseBtn")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(self._get_close_button_style())
        header_row.addWidget(close_btn)

        content_layout.addLayout(header_row)

        # Message (main content)
        message_label = QLabel(self._toast_message)
        message_label.setObjectName("toastMessage")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        message_label.setStyleSheet(f"""
            color: {THEME_V2.text_secondary};
            font-size: {TOKENS_V2.typography.body_sm}px;
        """)
        content_layout.addWidget(message_label)

        # Add container to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(container)

        # Apply styles
        self._apply_toast_styles()

    def _get_close_button_style(self) -> str:
        """Get stylesheet for close button."""
        return f"""
            QPushButton#toastCloseBtn {{
                background: transparent;
                border: none;
                border-radius: {TOKENS_V2.radius.xs}px;
                color: {THEME_V2.text_secondary};
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton#toastCloseBtn:hover {{
                background-color: {THEME_V2.bg_hover};
                color: {THEME_V2.text_primary};
            }}
        """

    def _apply_toast_styles(self) -> None:
        """Apply v2 dark theme styling for toast."""
        self.setStyleSheet(f"""
            ToastV2 {{
                background: transparent;
            }}
            QFrame#toastContainer {{
                background-color: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
            }}
            QFrame#toastContent {{
                background-color: {THEME_V2.bg_elevated};
                border-top-left-radius: {TOKENS_V2.radius.md}px;
                border-top-right-radius: {TOKENS_V2.radius.md}px;
                border-bottom-left-radius: {TOKENS_V2.radius.md}px;
                border-bottom-right-radius: {TOKENS_V2.radius.md}px;
            }}
        """)

    # ========================================================================
    # Public API
    # ========================================================================

    def set_duration(self, duration_ms: int) -> None:
        """
        Set auto-dismiss duration.

        Args:
            duration_ms: Duration in ms (0 for no auto-dismiss)
        """
        self._duration_ms = duration_ms

    def show(self) -> None:
        """
        Show toast with auto-dismiss timer.

        Overrides base to:
        1. Calculate stacked position via ToastManager
        2. Start auto-dismiss timer
        """
        # Calculate stacked position (top-right corner)
        toast_manager = ToastManager.instance()
        pos = toast_manager.register_toast(self, self.height())
        self.move(pos)

        # Call base show
        super().show()

        # Start auto-dismiss timer (if duration > 0)
        if self._duration_ms > 0:
            self._start_dismiss_timer()

    def close(self) -> bool:
        """
        Close toast and cleanup.

        Returns:
            True if toast was closed
        """
        # Stop timer if running
        self._stop_dismiss_timer()

        # Unregister from ToastManager
        toast_manager = ToastManager.instance()
        toast_manager.unregister_toast(self)

        # Reposition remaining toasts
        toast_manager.reposition_toasts()

        # Call base close
        return super().close()

    # ========================================================================
    # Timer Management (QTimer.singleShot, NOT QPropertyAnimation)
    # ========================================================================

    def _start_dismiss_timer(self) -> None:
        """Start auto-dismiss timer using QTimer.singleShot."""
        # Stop any existing timer
        self._stop_dismiss_timer()

        # Use QTimer.singleShot for one-shot auto-dismiss
        QTimer.singleShot(self._duration_ms, self._on_timer_expired)

    def _stop_dismiss_timer(self) -> None:
        """Stop the dismiss timer (cleanup only - singleShot auto-stops)."""
        # No persistent timer to stop (singleShot is fire-and-forget)
        # This method exists for API completeness and future extensibility
        pass

    @Slot()
    def _on_timer_expired(self) -> None:
        """Handle timer expiration - close toast."""
        if self.isVisible():
            logger.debug(f"Toast auto-dismiss: {self._toast_level} - {self._toast_message}")
            self.close()

    # ========================================================================
    # Qt Event Handlers
    # ========================================================================

    def showEvent(self, event: QShowEvent) -> None:
        """Handle show event - ensure stacking is updated."""
        super().showEvent(event)

        # Ensure z-order for stacking
        self.raise_()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle close event - emit dismissed signal."""
        # Unregister from ToastManager
        toast_manager = ToastManager.instance()
        toast_manager.unregister_toast(self)

        # Emit dismissed signal
        self.dismissed.emit()

        # Reposition remaining toasts
        toast_manager.reposition_toasts()

        # Call base close
        super().closeEvent(event)

    def keyPressEvent(self, event) -> None:
        """Handle key press events - Escape closes toast."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)


# =============================================================================
# Convenience Factory Functions
# =============================================================================


def show_info(
    message: str, title: str = "", duration_ms: int = 3000, parent: QWidget | None = None
) -> ToastV2:
    """
    Show info toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms
        parent: Parent widget

    Returns:
        ToastV2 instance (for testing/signal connection)
    """
    toast = ToastV2(
        level=ToastLevel.INFO,
        title=title,
        message=message,
        duration_ms=duration_ms,
        parent=parent,
    )
    toast.show()
    return toast


def show_success(
    message: str, title: str = "", duration_ms: int = 3000, parent: QWidget | None = None
) -> ToastV2:
    """
    Show success toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms
        parent: Parent widget

    Returns:
        ToastV2 instance (for testing/signal connection)
    """
    toast = ToastV2(
        level=ToastLevel.SUCCESS,
        title=title,
        message=message,
        duration_ms=duration_ms,
        parent=parent,
    )
    toast.show()
    return toast


def show_warning(
    message: str, title: str = "", duration_ms: int = 3000, parent: QWidget | None = None
) -> ToastV2:
    """
    Show warning toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms
        parent: Parent widget

    Returns:
        ToastV2 instance (for testing/signal connection)
    """
    toast = ToastV2(
        level=ToastLevel.WARNING,
        title=title,
        message=message,
        duration_ms=duration_ms,
        parent=parent,
    )
    toast.show()
    return toast


def show_error(
    message: str, title: str = "", duration_ms: int = 5000, parent: QWidget | None = None
) -> ToastV2:
    """
    Show error toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms (default 5s for errors)
        parent: Parent widget

    Returns:
        ToastV2 instance (for testing/signal connection)
    """
    toast = ToastV2(
        level=ToastLevel.ERROR,
        title=title,
        message=message,
        duration_ms=duration_ms,
        parent=parent,
    )
    toast.show()
    return toast


__all__ = [
    "ToastLevel",
    "ToastV2",
    "show_error",
    "show_info",
    "show_success",
    "show_warning",
]
