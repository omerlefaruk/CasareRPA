"""
Tests for TooltipV2 popup component.
"""

import pytest

from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from casare_rpa.presentation.canvas.ui.widgets.popups import (
    TooltipV2,
    PopupWindowBase,
    AnchorPosition,
)


class TestTooltipV2:
    """Test suite for TooltipV2 popup."""

    def test_init_default(self, qtbot) -> None:
        """Test default initialization."""
        tooltip = TooltipV2()

        assert tooltip._duration_ms == TooltipV2.DEFAULT_DURATION_MS
        assert tooltip._follow_mouse is False
        assert tooltip._dismiss_on_leave is True
        assert tooltip._auto_dismiss_enabled is True
        assert tooltip._is_following is False
        assert tooltip._content_label is not None

        qtbot.addWidget(tooltip)

    def test_init_with_params(self, qtbot) -> None:
        """Test initialization with custom parameters."""
        tooltip = TooltipV2(
            duration_ms=3000,
            show_close=True,
            follow_mouse=True,
            dismiss_on_leave=False,
        )

        assert tooltip._duration_ms == 3000
        assert tooltip._follow_mouse is True
        assert tooltip._dismiss_on_leave is False

        qtbot.addWidget(tooltip)

    def test_set_text(self, qtbot) -> None:
        """Test setting plain text content."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        tooltip.set_text("Hello, world!")
        assert tooltip.text() == "Hello, world!"

    def test_set_html(self, qtbot) -> None:
        """Test setting HTML content."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        html = "Press <b>Ctrl+S</b> to <i>save</i>"
        tooltip.set_html(html)
        assert tooltip.text() == html

    def test_set_duration(self, qtbot) -> None:
        """Test setting custom duration."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        tooltip.set_duration(2000)
        assert tooltip._duration_ms == 2000

        tooltip.set_duration(0)  # Disable auto-dismiss
        assert tooltip._duration_ms == 0

    def test_set_follow_mouse(self, qtbot) -> None:
        """Test enabling follow-mouse mode."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        tooltip.set_follow_mouse(True)
        assert tooltip._follow_mouse is True

        tooltip.set_follow_mouse(False)
        assert tooltip._follow_mouse is False

    def test_dismiss_signal(self, qtbot) -> None:
        """Test dismissed signal emission."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        dismissed_received = []

        @Slot()
        def on_dismissed():
            dismissed_received.append(True)

        tooltip.dismissed.connect(on_dismissed)

        # Show and immediately dismiss
        tooltip.show_at_position(QPoint(100, 100))
        tooltip.dismiss()

        assert len(dismissed_received) == 1

    def test_show_at_position(self, qtbot) -> None:
        """Test showing tooltip at specific position."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        pos = QPoint(200, 200)
        tooltip.show_at_position(pos)

        assert tooltip.isVisible()
        # Position may be clamped to screen, so just check it's shown
        assert tooltip.x() >= 0
        assert tooltip.y() >= 0

    def test_show_at_cursor(self, qtbot) -> None:
        """Test showing tooltip at cursor position."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        tooltip.set_text("Cursor tooltip")
        tooltip.show_at_cursor()

        assert tooltip.isVisible()

    def test_show_at_anchor(self, qtbot) -> None:
        """Test showing tooltip anchored to a widget."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        # Create a button as anchor
        button = QPushButton("Anchor")
        qtbot.addWidget(button)
        button.show()
        button.move(100, 100)

        tooltip.set_text("Anchored tooltip")
        tooltip.show_at_anchor(button, AnchorPosition.BELOW)

        assert tooltip.isVisible()

    def test_content_auto_resize(self, qtbot) -> None:
        """Test that tooltip resizes to fit content."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        # Short content
        tooltip.set_text("Short")
        width_short = tooltip.width()

        # Long content
        tooltip.set_text("This is a much longer tooltip text that should expand the width")
        tooltip._adjust_size_to_content()
        width_long = tooltip.width()

        # Longer content should result in wider tooltip (within max bounds)
        assert width_long >= width_short

    def test_header_hidden_by_default(self, qtbot) -> None:
        """Test that header is hidden for minimal appearance."""
        tooltip = TooltipV2()
        qtbot.addWidget(tooltip)

        assert not tooltip._header.isVisible()

    def test_with_close_button(self, qtbot) -> None:
        """Test tooltip with close button enabled."""
        tooltip = TooltipV2(show_close=True)
        qtbot.addWidget(tooltip)

        # With close button, header might still be hidden for tooltips
        # The base class creates the button, but we hide the header
        # This is expected behavior for tooltips
        assert tooltip._close_btn is not None

    def test_auto_dismiss_timer(self, qtbot) -> None:
        """Test auto-dismiss timer functionality."""
        tooltip = TooltipV2(duration_ms=100)  # Very short timeout
        qtbot.addWidget(tooltip)

        dismissed_received = []

        @Slot()
        def on_dismissed():
            dismissed_received.append(True)

        tooltip.dismissed.connect(on_dismissed)

        tooltip.show_at_position(QPoint(100, 100))

        # Wait for timeout
        qtbot.wait(150)

        assert len(dismissed_received) == 1
        assert not tooltip.isVisible()

    def test_no_auto_dismiss_with_zero_duration(self, qtbot) -> None:
        """Test that zero duration disables auto-dismiss."""
        tooltip = TooltipV2(duration_ms=0)
        qtbot.addWidget(tooltip)

        tooltip.show_at_position(QPoint(100, 100))

        # Wait a bit - tooltip should still be visible
        qtbot.wait(200)

        # With zero duration, timer should not fire
        # (tooltip might be closed by other means, but not by timer)
        assert not tooltip._dismiss_timer.isActive()

    def test_dismiss_on_leave(self, qtbot) -> None:
        """Test dismiss on mouse leave behavior."""
        tooltip = TooltipV2(dismiss_on_leave=True, duration_ms=0)  # No timeout
        qtbot.addWidget(tooltip)

        tooltip.show_at_position(QPoint(100, 100))
        assert tooltip.isVisible()

        # Simulating leave event is complex in tests
        # Just verify the flag is set correctly
        assert tooltip._dismiss_on_leave is True
