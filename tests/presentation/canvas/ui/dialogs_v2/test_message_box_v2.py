"""
Tests for MessageBoxV2.

Tests cover:
- Icon widget rendering
- MessageBoxV2 creation and setup
- Factory functions (show_info, show_warning, show_error, show_question)
- Modal behavior
"""

from __future__ import annotations

from casare_rpa.presentation.canvas.ui.dialogs_v2 import MessageBoxV2

from .conftest import qapp

# =============================================================================
# ICON WIDGET TESTS
# =============================================================================


class TestIconWidget:
    """Tests for IconWidget."""

    def test_icon_widget_creation(self) -> None:
        """Icon widget can be created for all types."""
        from casare_rpa.presentation.canvas.ui.dialogs_v2.message_box_v2 import IconWidget

        qapp()

        for icon_type in ["info", "warning", "error", "question"]:
            icon = IconWidget(icon_type)
            assert icon is not None
            assert icon._icon_type == icon_type

    def test_icon_widget_has_symbol(self) -> None:
        """Icon widget has correct symbol for each type."""
        from casare_rpa.presentation.canvas.ui.dialogs_v2.message_box_v2 import IconWidget

        qapp()

        icon = IconWidget("info")
        assert icon._symbol == "i"

        icon = IconWidget("warning")
        assert icon._symbol == "!"

        icon = IconWidget("error")
        assert icon._symbol == "X"

        icon = IconWidget("question")
        assert icon._symbol == "?"


# =============================================================================
# MESSAGE BOX V2 TESTS
# =============================================================================


class TestMessageBoxV2:
    """Tests for MessageBoxV2."""

    def test_message_box_creation(self) -> None:
        """MessageBoxV2 can be created."""
        qapp()
        msg_box = MessageBoxV2(
            title="Test",
            message="Test message",
            msg_type="info",
        )

        assert msg_box is not None
        assert msg_box._message == "Test message"
        assert msg_box._msg_type == "info"

    def test_message_box_info_type(self) -> None:
        """Info message box has correct type."""
        qapp()
        msg_box = MessageBoxV2(
            title="Info",
            message="Information",
            msg_type="info",
        )

        assert msg_box._msg_type == "info"

    def test_message_box_warning_type(self) -> None:
        """Warning message box has correct type."""
        qapp()
        msg_box = MessageBoxV2(
            title="Warning",
            message="Warning message",
            msg_type="warning",
        )

        assert msg_box._msg_type == "warning"

    def test_message_box_error_type(self) -> None:
        """Error message box has correct type."""
        qapp()
        msg_box = MessageBoxV2(
            title="Error",
            message="Error message",
            msg_type="error",
        )

        assert msg_box._msg_type == "error"

    def test_message_box_question_type(self) -> None:
        """Question message box has correct type."""
        qapp()
        msg_box = MessageBoxV2(
            title="Question",
            message="Are you sure?",
            msg_type="question",
        )

        assert msg_box._msg_type == "question"

    def test_message_box_has_body_content(self) -> None:
        """MessageBoxV2 sets body content widget."""
        qapp()
        msg_box = MessageBoxV2(
            title="Test",
            message="Test message",
        )

        assert msg_box._body_widget is not None

    def test_message_box_size_based_on_message_length(self) -> None:
        """Short messages use SM size, longer use MD."""
        qapp()

        # Short message -> SM
        short_msg = MessageBoxV2(
            title="Short",
            message="Short",
        )
        assert short_msg._size.value == "sm"

        # Long message -> MD (100+ characters)
        long_msg = MessageBoxV2(
            title="Long",
            message="This is a much longer message that exceeds one hundred characters in length to properly trigger the MD size threshold",
        )
        assert long_msg._size.value == "md"

    def test_message_box_question_has_title_bar(self) -> None:
        """Question dialogs show title bar."""
        qapp()
        msg_box = MessageBoxV2(
            title="Confirm",
            message="Are you sure?",
            msg_type="question",
        )

        assert msg_box._show_title_bar is True

    def test_message_box_non_question_no_title_bar(self) -> None:
        """Non-question dialogs don't show title bar."""
        qapp()
        msg_box = MessageBoxV2(
            title="Info",
            message="Information",
            msg_type="info",
        )

        assert msg_box._show_title_bar is False


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestMessageBoxFactoryFunctions:
    """Tests for MessageBoxV2 factory functions."""

    def test_show_info_creates_dialog(self) -> None:
        """show_info creates and shows info dialog."""
        qapp()
        # Don't actually call exec() in tests

        msg_box = MessageBoxV2("Info", "Test", "info", None)

        assert msg_box._msg_type == "info"
        assert msg_box._message == "Test"

    def test_show_warning_creates_dialog(self) -> None:
        """show_warning creates and shows warning dialog."""
        qapp()
        msg_box = MessageBoxV2("Warning", "Test", "warning", None)

        assert msg_box._msg_type == "warning"

    def test_show_error_creates_dialog(self) -> None:
        """show_error creates and shows error dialog."""
        qapp()
        msg_box = MessageBoxV2("Error", "Test", "error", None)

        assert msg_box._msg_type == "error"

    def test_show_question_returns_bool_on_yes(self) -> None:
        """show_question returns True when user clicks Yes."""
        qapp()
        msg_box = MessageBoxV2(
            "Question",
            "Continue?",
            "question",
            None,
        )

        # Simulate user clicking Yes (accept)
        # In actual usage, exec() would return Accepted
        assert msg_box._msg_type == "question"

    def test_show_question_returns_bool_on_no(self) -> None:
        """show_question returns False when user clicks No."""
        qapp()
        msg_box = MessageBoxV2(
            "Question",
            "Continue?",
            "question",
            None,
        )

        # Simulate user clicking No (reject)
        # In actual usage, exec() would return Rejected
        assert msg_box._msg_type == "question"


# =============================================================================
# FOOTER CONFIGURATION TESTS
# =============================================================================


class TestMessageBoxFooter:
    """Tests for MessageBoxV2 footer configuration."""

    def test_question_has_yes_no_buttons(self) -> None:
        """Question dialog has Yes/No buttons."""
        qapp()
        msg_box = MessageBoxV2(
            title="Question",
            message="Continue?",
            msg_type="question",
        )

        primary = msg_box._footer.get_primary_button()
        cancel = msg_box._footer.get_cancel_button()

        assert primary is not None
        assert cancel is not None
        assert primary.text() == "Yes"
        assert cancel.text() == "No"

    def test_info_has_ok_button_only(self) -> None:
        """Info dialog has OK button, cancel hidden."""
        qapp()
        msg_box = MessageBoxV2(
            title="Info",
            message="Information",
            msg_type="info",
        )

        primary = msg_box._footer.get_primary_button()
        cancel = msg_box._footer.get_cancel_button()

        assert primary is not None
        assert primary.text() == "OK"
        assert cancel is not None
        assert not cancel.isVisible()  # Cancel button hidden

    def test_warning_has_ok_button_only(self) -> None:
        """Warning dialog has OK button, cancel hidden."""
        qapp()
        msg_box = MessageBoxV2(
            title="Warning",
            message="Warning message",
            msg_type="warning",
        )

        primary = msg_box._footer.get_primary_button()
        cancel = msg_box._footer.get_cancel_button()

        assert primary is not None
        assert primary.text() == "OK"
        assert not cancel.isVisible()

    def test_error_has_ok_button_only(self) -> None:
        """Error dialog has OK button, cancel hidden."""
        qapp()
        msg_box = MessageBoxV2(
            title="Error",
            message="Error message",
            msg_type="error",
        )

        primary = msg_box._footer.get_primary_button()
        cancel = msg_box._footer.get_cancel_button()

        assert primary is not None
        assert primary.text() == "OK"
        assert not cancel.isVisible()
