"""
TooltipV2 - Minimal rich text tooltip popup.

V2 tooltip popup with HTML content support, auto-dismiss, and optional
follow-mouse mode. Extends PopupWindowBase but with minimal/no header.

Features:
- No header (optional minimal close button only)
- Rich text/HTML content (QLabel with limited HTML support)
- Auto-dismiss on timeout (default 5s, configurable)
- Auto-dismiss on mouse leave
- Optional follow-mouse mode
- Auto-position to avoid cursor
- Limited HTML: b, i, u, code, a, br, span

Signals:
    dismissed: Emitted when tooltip is dismissed (timeout or close)

Usage:
    tooltip = TooltipV2(parent=None)
    tooltip.set_html("Press <b>Ctrl+S</b> to save")
    tooltip.show_at_cursor()

    # With custom timeout
    tooltip = TooltipV2(duration_ms=3000)
    tooltip.set_text("Save successful")
    tooltip.show_at_position(pos)

    # Follow mouse mode
    tooltip = TooltipV2(follow_mouse=True)
    tooltip.set_html("Dragging: <i>hold to move</i>")
    tooltip.show_at_cursor()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QPoint, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2

from .popup_window_base import PopupWindowBase

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent


class TooltipV2(PopupWindowBase):
    """
    Minimal rich text tooltip popup with auto-dismiss.

    Simplified variant of PopupWindowBase with:
    - No header (or minimal close-only header)
    - Rich text/HTML content support
    - Auto-dismiss timeout
    - Optional follow-mouse mode
    - Mouse-leave dismissal

    Signals:
        dismissed: Emitted when tooltip is dismissed
    """

    dismissed = Signal()

    # Default dimensions
    DEFAULT_WIDTH = 250
    DEFAULT_HEIGHT = 80
    MIN_WIDTH = 100
    MIN_HEIGHT = 40

    # Default timeout (5 seconds)
    DEFAULT_DURATION_MS = 5000

    # Mouse offset for cursor positioning
    CURSOR_OFFSET = QPoint(16, 16)

    def __init__(
        self,
        parent: QWidget | None = None,
        duration_ms: int = DEFAULT_DURATION_MS,
        show_close: bool = False,
        follow_mouse: bool = False,
        dismiss_on_leave: bool = True,
    ) -> None:
        """
        Initialize tooltip.

        Args:
            parent: Parent widget
            duration_ms: Auto-dismiss timeout in ms (0 for no timeout)
            show_close: Show minimal close button (default: False)
            follow_mouse: Track mouse movement and update position
            dismiss_on_leave: Dismiss when mouse leaves tooltip area
        """
        # Initialize base with minimal settings (no title, no pin, optional close)
        super().__init__(
            title="",  # No title
            parent=parent,
            resizable=False,  # Not resizable
            pin_button=False,  # No pin
            close_button=show_close,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

        # Tooltip-specific settings
        self._duration_ms: int = duration_ms
        self._follow_mouse: bool = follow_mouse
        self._dismiss_on_leave: bool = dismiss_on_leave
        self._auto_dismiss_enabled: bool = True
        self._is_dismissing: bool = False  # Prevent double signal emission

        # Content label
        self._content_label: QLabel | None = None

        # Timer for auto-dismiss
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._on_timeout)

        # Follow-mouse timer (throttled position updates)
        self._mouse_timer = QTimer(self)
        self._mouse_timer.setInterval(50)  # 20fps updates
        self._mouse_timer.timeout.connect(self._update_mouse_position)

        # Track if tooltip is currently following mouse
        self._is_following: bool = False

        # Setup minimal UI
        self._setup_tooltip_ui()

        # Set default size
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def _setup_tooltip_ui(self) -> None:
        """Setup minimal tooltip content area."""
        # Hide header completely for tooltips (no title, no close by default)
        if self._header:
            self._header.hide()

        # Create content label
        self._content_label = QLabel()
        self._content_label.setObjectName("tooltipContent")
        self._content_label.setTextFormat(Qt.TextFormat.RichText)
        self._content_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        # Label styling
        self._content_label.setStyleSheet(f"""
            QLabel#tooltipContent {{
                background-color: transparent;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body_sm}px;
                padding: {TOKENS_V2.spacing.xs}px;
            }}
            QLabel#tooltipContent a {{
                color: {THEME_V2.primary};
                text-decoration: none;
            }}
            QLabel#tooltipContent a:hover {{
                color: {THEME_V2.primary_hover};
                text-decoration: underline;
            }}
        """)

        # Set as content widget
        content_frame = QFrame()
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._content_label)

        self.set_content_widget(content_frame)

        # Enable mouse tracking for leave detection
        self.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, True)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_html(self, html: str) -> None:
        """
        Set tooltip content as HTML.

        Supported HTML tags (subset):
        - b, strong: Bold
        - i, em: Italic
        - u: Underline
        - code: Inline code (styled)
        - a: Links
        - br: Line breaks
        - span: Custom styling

        Args:
            html: HTML content string
        """
        if self._content_label:
            self._content_label.setText(html)
            self._adjust_size_to_content()

    def set_text(self, text: str) -> None:
        """
        Set tooltip content as plain text.

        Args:
            text: Plain text content
        """
        if self._content_label:
            self._content_label.setText(text)
            self._adjust_size_to_content()

    def text(self) -> str:
        """Get current tooltip text."""
        if self._content_label:
            return self._content_label.text()
        return ""

    def set_duration(self, duration_ms: int) -> None:
        """
        Set auto-dismiss timeout.

        Args:
            duration_ms: Timeout in milliseconds (0 to disable)
        """
        self._duration_ms = duration_ms

    def set_follow_mouse(self, follow: bool) -> None:
        """
        Enable or disable follow-mouse mode.

        Args:
            follow: True to follow mouse cursor
        """
        self._follow_mouse = follow

        if follow and self._is_following:
            self._mouse_timer.start()
        elif not follow:
            self._mouse_timer.stop()
            self._is_following = False

    def show_at_cursor(self, offset: QPoint | None = None) -> None:
        """
        Show tooltip at cursor position with offset.

        Args:
            offset: Optional offset from cursor (default: CURSOR_OFFSET)
        """
        if offset is None:
            offset = self.CURSOR_OFFSET

        cursor_pos = QCursor.pos()
        target_pos = cursor_pos + offset
        self.show_at_position(target_pos)

        # Start timers
        self._start_dismiss_timer()
        if self._follow_mouse:
            self._is_following = True
            self._mouse_timer.start()

    def show_at_position(self, global_pos: QPoint) -> None:
        """
        Show tooltip at specific position.

        Args:
            global_pos: Global screen position
        """
        super().show_at_position(global_pos)

        # Start auto-dismiss timer
        self._start_dismiss_timer()

        # Start follow-mouse timer if enabled
        if self._follow_mouse:
            self._is_following = True
            self._mouse_timer.start()

    def show_at_anchor(
        self,
        widget: QWidget,
        position: type[PopupWindowBase.AnchorPosition] | None = None,
        offset: QPoint | None = None,
    ) -> None:
        """
        Show tooltip anchored to a widget.

        Args:
            widget: Anchor widget
            position: Position relative to anchor (default: BELOW)
            offset: Optional offset from anchor
        """
        if position is None:
            position = PopupWindowBase.AnchorPosition.BELOW

        super().show_at_anchor(widget, position, offset)

        # Start timers
        self._start_dismiss_timer()
        if self._follow_mouse:
            self._is_following = True
            self._mouse_timer.start()

    def dismiss(self) -> None:
        """Dismiss the tooltip programmatically."""
        if self._is_dismissing:
            return

        self._is_dismissing = True
        self._dismiss_timer.stop()
        self._mouse_timer.stop()
        self._is_following = False
        self.close()
        self.dismissed.emit()
        self._is_dismissing = False

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _adjust_size_to_content(self) -> None:
        """Adjust popup size to fit content with sensible limits."""
        if not self._content_label:
            return

        # Get content size hint
        content_size = self._content_label.sizeHint()

        # Calculate new window size (add padding)
        padding = TOKENS_V2.spacing.md * 2
        new_width = max(
            self.MIN_WIDTH,
            min(content_size.width() + padding, 400),  # Max width 400
        )
        new_height = max(
            self.MIN_HEIGHT,
            min(content_size.height() + padding, 200),  # Max height 200
        )

        self.resize(new_width, new_height)

    def _start_dismiss_timer(self) -> None:
        """Start auto-dismiss timer if duration is set."""
        self._dismiss_timer.stop()
        if self._duration_ms > 0 and self._auto_dismiss_enabled:
            self._dismiss_timer.start(self._duration_ms)

    def _update_mouse_position(self) -> None:
        """Update tooltip position to follow mouse cursor."""
        if not self._follow_mouse or not self._is_following:
            return

        # Only update if tooltip is visible
        if not self.isVisible():
            self._mouse_timer.stop()
            self._is_following = False
            return

        # Update position with offset
        cursor_pos = QCursor.pos()
        target_pos = cursor_pos + self.CURSOR_OFFSET

        # Use move directly to avoid re-clamping every frame
        # (clamp is done in show_at_position initially)
        self.move(target_pos)

    # =========================================================================
    # Qt Event Handlers
    # =========================================================================

    @Slot()
    def _on_timeout(self) -> None:
        """Handle auto-dismiss timeout."""
        logger.debug("Tooltip auto-dismissed after timeout")
        self.dismiss()

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        # Raise to top of z-order
        self.raise_()

    def hideEvent(self, event) -> None:
        """Handle hide event."""
        self._dismiss_timer.stop()
        self._mouse_timer.stop()
        self._is_following = False
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        """Handle close event."""
        self._dismiss_timer.stop()
        self._mouse_timer.stop()
        self._is_following = False
        # Only emit dismissed if not already emitted by dismiss()
        if not self._is_dismissing:
            self.dismissed.emit()
        super().closeEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave event for auto-dismiss."""
        if self._dismiss_on_leave and self._auto_dismiss_enabled:
            # Small delay to allow interactions (like clicking links)
            QTimer.singleShot(100, self.dismiss)
        super().leaveEvent(event)

    def enterEvent(self, event) -> None:
        """Handle mouse enter event - pause dismissal on hover."""
        if self._dismiss_on_leave:
            # Stop dismiss timer while hovering
            self._dismiss_timer.stop()
        super().enterEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Track mouse movement for follow-mouse mode."""
        if self._follow_mouse and self._is_following:
            # Position updates are handled by timer for throttling
            pass
        super().mouseMoveEvent(event)
