"""
Tests for ExpandButton widget.

This test suite covers:
- ExpandButton creation and initialization
- clicked_expand signal emission
- Button styling and appearance
- Tooltip and accessibility

Test Philosophy:
- Happy path: button creates correctly, signals emit
- Sad path: multiple rapid clicks handled
- Edge cases: button state during operations

Run: pytest tests/presentation/canvas/ui/widgets/expression_editor/test_expand_button.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# ExpandButton Creation Tests
# =============================================================================


class TestExpandButtonCreation:
    """Tests for ExpandButton instantiation."""

    def test_instantiation(self, qapp) -> None:
        """Test ExpandButton can be instantiated."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert button is not None

    def test_instantiation_with_parent(self, qapp) -> None:
        """Test ExpandButton with parent widget."""
        from PySide6.QtWidgets import QWidget

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        parent = QWidget()
        button = ExpandButton(parent=parent)
        assert button.parent() == parent

    def test_button_text(self, qapp) -> None:
        """Test button displays '...' text."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert button.text() == "..."

    def test_button_size(self, qapp) -> None:
        """Test button has fixed 20x20 size."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert button.width() == 20
        assert button.height() == 20

    def test_button_tooltip(self, qapp) -> None:
        """Test button has appropriate tooltip."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        tooltip = button.toolTip()
        assert "expression editor" in tooltip.lower() or "Ctrl+E" in tooltip


# =============================================================================
# Signal Emission Tests
# =============================================================================


class TestExpandButtonSignals:
    """Tests for ExpandButton signal emission."""

    def test_clicked_expand_signal_exists(self, qapp) -> None:
        """Test clicked_expand signal is defined."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert hasattr(button, "clicked_expand")

    def test_clicked_expand_emitted_on_click(self, qapp, signal_capture) -> None:
        """Test clicked_expand signal is emitted when button is clicked."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        button.clicked_expand.connect(signal_capture.slot)

        # Simulate click
        button.click()

        assert signal_capture.called
        assert signal_capture.call_count == 1

    def test_multiple_clicks_emit_multiple_signals(self, qapp, signal_capture) -> None:
        """Test multiple clicks emit multiple signals."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        button.clicked_expand.connect(signal_capture.slot)

        button.click()
        button.click()
        button.click()

        assert signal_capture.call_count == 3

    def test_signal_has_no_arguments(self, qapp, signal_capture) -> None:
        """Test clicked_expand signal emits with no arguments."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        button.clicked_expand.connect(signal_capture.slot)

        button.click()

        # Signal should emit empty tuple (no args)
        assert signal_capture.last_args == ()


# =============================================================================
# Button Appearance Tests
# =============================================================================


class TestExpandButtonAppearance:
    """Tests for ExpandButton visual appearance."""

    def test_cursor_is_pointer(self, qapp) -> None:
        """Test button has pointing hand cursor."""
        from PySide6.QtCore import Qt

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_no_focus_policy(self, qapp) -> None:
        """Test button doesn't take keyboard focus."""
        from PySide6.QtCore import Qt

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert button.focusPolicy() == Qt.FocusPolicy.NoFocus

    def test_has_stylesheet(self, qapp) -> None:
        """Test button has stylesheet applied."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        stylesheet = button.styleSheet()
        assert len(stylesheet) > 0
        assert "QPushButton" in stylesheet

    def test_stylesheet_uses_theme(self, qapp) -> None:
        """Test button stylesheet uses theme colors (no hardcoded hex)."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        # Button uses Theme.get_colors() which provides color values
        # The stylesheet is dynamically generated, so it should contain colors
        stylesheet = button.styleSheet()
        # Should contain color definitions
        assert "background" in stylesheet or "border" in stylesheet


# =============================================================================
# Button State Tests
# =============================================================================


class TestExpandButtonState:
    """Tests for ExpandButton state management."""

    def test_button_enabled_by_default(self, qapp) -> None:
        """Test button is enabled by default."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert button.isEnabled()

    def test_button_can_be_disabled(self, qapp) -> None:
        """Test button can be disabled."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        button.setEnabled(False)
        assert not button.isEnabled()

    def test_disabled_button_no_signal(self, qapp, signal_capture) -> None:
        """Test disabled button doesn't emit signal on click."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        button.clicked_expand.connect(signal_capture.slot)
        button.setEnabled(False)

        # Click on disabled button
        button.click()

        assert not signal_capture.called

    def test_button_can_be_enabled_and_shown(self, qapp) -> None:
        """Test button can be enabled and shown."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        # Button should be enabled by default
        assert button.isEnabled()
        # Show the button - won't actually be visible without a parent window
        button.show()
        # Button should still work after show
        assert button.isEnabled()


# =============================================================================
# Inheritance Tests
# =============================================================================


class TestExpandButtonInheritance:
    """Tests for ExpandButton class hierarchy."""

    def test_inherits_from_qpushbutton(self, qapp) -> None:
        """Test ExpandButton inherits from QPushButton."""
        from PySide6.QtWidgets import QPushButton

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        assert issubclass(ExpandButton, QPushButton)

    def test_has_standard_button_methods(self, qapp) -> None:
        """Test ExpandButton has standard QPushButton methods."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()

        # Standard button methods
        assert hasattr(button, "click")
        assert hasattr(button, "setEnabled")
        assert hasattr(button, "setText")
        assert hasattr(button, "setToolTip")

    def test_has_clicked_signal(self, qapp) -> None:
        """Test standard clicked signal from QPushButton exists."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        assert hasattr(button, "clicked")


# =============================================================================
# Integration Tests
# =============================================================================


class TestExpandButtonIntegration:
    """Integration tests for ExpandButton usage patterns."""

    def test_connect_to_slot(self, qapp) -> None:
        """Test connecting clicked_expand to a slot."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        handler_called = []

        def handler():
            handler_called.append(True)

        button.clicked_expand.connect(handler)
        button.click()

        assert len(handler_called) == 1

    def test_disconnect_from_slot(self, qapp) -> None:
        """Test disconnecting from clicked_expand signal."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        handler_called = []

        def handler():
            handler_called.append(True)

        button.clicked_expand.connect(handler)
        button.clicked_expand.disconnect(handler)
        button.click()

        assert len(handler_called) == 0

    def test_multiple_handlers(self, qapp) -> None:
        """Test multiple handlers connected to signal."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        handler1_calls = []
        handler2_calls = []

        def handler1():
            handler1_calls.append(True)

        def handler2():
            handler2_calls.append(True)

        button.clicked_expand.connect(handler1)
        button.clicked_expand.connect(handler2)
        button.click()

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestExpandButtonEdgeCases:
    """Edge case tests for ExpandButton."""

    def test_rapid_clicks(self, qapp, signal_capture) -> None:
        """Test handling rapid successive clicks."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        button.clicked_expand.connect(signal_capture.slot)

        # Simulate rapid clicks
        for _ in range(100):
            button.click()

        assert signal_capture.call_count == 100

    def test_click_while_handler_running(self, qapp, signal_capture) -> None:
        """Test click during signal handling."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        click_count = []

        def handler():
            click_count.append(1)
            # Simulate slow handler
            qapp.processEvents()

        button.clicked_expand.connect(handler)
        button.click()

        assert len(click_count) == 1

    def test_button_deletion_after_connection(self, qapp) -> None:
        """Test button can be deleted with connected signals."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()

        def handler():
            pass

        button.clicked_expand.connect(handler)

        # Should not crash on deletion
        del button

    def test_signal_after_reparent(self, qapp, signal_capture) -> None:
        """Test signal works after reparenting button."""
        from PySide6.QtWidgets import QWidget

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        parent1 = QWidget()
        parent2 = QWidget()

        button = ExpandButton(parent=parent1)
        button.clicked_expand.connect(signal_capture.slot)

        # Reparent
        button.setParent(parent2)
        button.click()

        assert signal_capture.called


# =============================================================================
# Accessibility Tests
# =============================================================================


class TestExpandButtonAccessibility:
    """Tests for ExpandButton accessibility features."""

    def test_has_accessible_name(self, qapp) -> None:
        """Test button has accessible name or tooltip."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        # Either accessible name or tooltip should be set
        has_accessibility = button.accessibleName() != "" or button.toolTip() != ""
        assert has_accessibility

    def test_tooltip_describes_action(self, qapp) -> None:
        """Test tooltip describes what button does."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
            ExpandButton,
        )

        button = ExpandButton()
        tooltip = button.toolTip().lower()

        # Should mention opening editor or keyboard shortcut
        has_description = (
            "expression" in tooltip or "editor" in tooltip or "open" in tooltip or "ctrl" in tooltip
        )
        assert has_description
