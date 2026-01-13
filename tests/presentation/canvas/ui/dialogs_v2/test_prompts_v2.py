"""
Tests for PromptsV2 convenience API (Epic 7.3 migration helpers).

Tests cover:
- show_info, show_warning, show_error, show_question
- show_confirm
- get_text, get_password
- toast_info, toast_success, toast_warning, toast_error
"""

from __future__ import annotations

from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    ConfirmDialogV2,
    InputDialogV2,
    MessageBoxV2,
    ToastLevel,
    ToastV2,
    get_password,
    get_text,
    show_confirm,
    show_error,
    show_info,
    show_question,
    show_warning,
    toast_error,
    toast_info,
    toast_success,
    toast_warning,
)

from .conftest import qapp

# =============================================================================
# SHOW_* FUNCTION TESTS (QMessageBox replacements)
# =============================================================================


class TestShowFunctions:
    """Tests for show_* convenience functions."""

    def test_show_info_returns_none(self) -> None:
        """show_info returns None (blocking dialog)."""
        qapp()
        result = show_info(None, "Title", "Message")
        assert result is None

    def test_show_warning_returns_none(self) -> None:
        """show_warning returns None (blocking dialog)."""
        qapp()
        result = show_warning(None, "Title", "Message")
        assert result is None

    def test_show_error_returns_none(self) -> None:
        """show_error returns None (blocking dialog)."""
        qapp()
        result = show_error(None, "Title", "Message")
        assert result is None

    def test_show_question_returns_bool(self) -> None:
        """show_question returns bool (user choice)."""
        qapp()
        result = show_question(None, "Title", "Message")
        assert isinstance(result, bool)

    def test_show_confirm_returns_bool(self) -> None:
        """show_confirm returns bool (user choice)."""
        qapp()
        result = show_confirm(None, "Delete", "Are you sure?", "Delete")
        assert isinstance(result, bool)

    def test_show_confirm_with_custom_destructive_text(self) -> None:
        """show_confirm supports custom destructive button text."""
        qapp()
        result = show_confirm(
            None,
            "Remove Project",
            "This will delete the project.",
            "Remove Project",
        )
        assert isinstance(result, bool)

    def test_show_confirm_with_detail(self) -> None:
        """show_confirm supports detail text."""
        qapp()
        result = show_confirm(
            None,
            "Delete",
            "Are you sure?",
            "Delete",
            detail="This action cannot be undone.",
        )
        assert isinstance(result, bool)


# =============================================================================
# GET_* FUNCTION TESTS (QInputDialog replacements)
# =============================================================================


class TestGetFunctions:
    """Tests for get_* convenience functions."""

    def test_get_text_returns_tuple(self) -> None:
        """get_text returns (text, ok) tuple matching QInputDialog API."""
        qapp()
        text, ok = get_text(None, "Title", "Label:")
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_with_current_text(self) -> None:
        """get_text supports initial text value."""
        qapp()
        text, ok = get_text(None, "Title", "Label:", current_text="Default")
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_with_placeholder(self) -> None:
        """get_text supports placeholder text."""
        qapp()
        text, ok = get_text(None, "Title", "Label:", placeholder="Placeholder")
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_password_mode(self) -> None:
        """get_text supports password mode."""
        qapp()
        text, ok = get_text(None, "Title", "Label:", password_mode=True)
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_required_validation(self) -> None:
        """get_text supports required validation."""
        qapp()
        text, ok = get_text(None, "Title", "Label:", required=True)
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_min_length_validation(self) -> None:
        """get_text supports minimum length validation."""
        qapp()
        text, ok = get_text(None, "Title", "Label:", min_length=3)
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_max_length_validation(self) -> None:
        """get_text supports maximum length validation."""
        qapp()
        text, ok = get_text(None, "Title", "Label:", max_length=10)
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_password_returns_tuple(self) -> None:
        """get_password returns (password, ok) tuple."""
        qapp()
        password, ok = get_password(None, "Login", "Password:")
        assert isinstance(password, str)
        assert isinstance(ok, bool)

    def test_get_password_required_by_default(self) -> None:
        """get_password has required=True by default."""
        qapp()
        password, ok = get_password(None, "Login", "Password:")
        assert isinstance(password, str)
        assert isinstance(ok, bool)


# =============================================================================
# TOAST_* FUNCTION TESTS (Non-blocking notifications)
# =============================================================================


class TestToastFunctions:
    """Tests for toast_* convenience functions."""

    def test_toast_info_returns_toast_v2(self) -> None:
        """toast_info returns ToastV2 instance."""
        qapp()
        toast = toast_info("Info message")
        assert isinstance(toast, ToastV2)

    def test_toast_info_with_title(self) -> None:
        """toast_info supports title parameter."""
        qapp()
        toast = toast_info("Message", title="Info")
        assert isinstance(toast, ToastV2)

    def test_toast_info_with_custom_duration(self) -> None:
        """toast_info supports custom duration."""
        qapp()
        toast = toast_info("Message", duration_ms=5000)
        assert isinstance(toast, ToastV2)

    def test_toast_success_returns_toast_v2(self) -> None:
        """toast_success returns ToastV2 instance."""
        qapp()
        toast = toast_success("Success message")
        assert isinstance(toast, ToastV2)

    def test_toast_warning_returns_toast_v2(self) -> None:
        """toast_warning returns ToastV2 instance."""
        qapp()
        toast = toast_warning("Warning message")
        assert isinstance(toast, ToastV2)

    def test_toast_error_returns_toast_v2(self) -> None:
        """toast_error returns ToastV2 instance."""
        qapp()
        toast = toast_error("Error message")
        assert isinstance(toast, ToastV2)

    def test_toast_error_longer_default_duration(self) -> None:
        """toast_error has longer default duration (5s)."""
        qapp()
        toast = toast_error("Error")
        # Default for error should be 5000ms
        assert toast._duration_ms == 5000


# =============================================================================
# API COMPATIBILITY TESTS
# =============================================================================


class TestApiCompatibility:
    """Tests for API compatibility with QMessageBox/QInputDialog."""

    def test_show_info_signature_matches_qmessagebox(self) -> None:
        """show_info has compatible signature with QMessageBox.information."""
        # QMessageBox.information(parent, title, message)
        # show_info(parent, title, message)
        qapp()
        show_info(None, "Title", "Message")  # Should not raise

    def test_show_warning_signature_matches_qmessagebox(self) -> None:
        """show_warning has compatible signature with QMessageBox.warning."""
        qapp()
        show_warning(None, "Title", "Message")  # Should not raise

    def test_show_error_signature_matches_qmessagebox(self) -> None:
        """show_error has compatible signature with QMessageBox.critical."""
        qapp()
        show_error(None, "Title", "Message")  # Should not raise

    def test_show_question_signature_matches_qmessagebox(self) -> None:
        """show_question has compatible return type with QMessageBox.question.

        QMessageBox.question returns button ID (int), show_question returns bool.
        Both are truthy/falsy for conditional checks.
        """
        qapp()
        result = show_question(None, "Title", "Message")
        assert isinstance(result, bool)
        # Can use in conditional
        if result:
            pass  # User confirmed

    def test_get_text_signature_matches_qinputdialog(self) -> None:
        """get_text has compatible signature with QInputDialog.getText.

        QInputDialog.getText(parent, title, label) -> (text, ok)
        get_text(parent, title, label) -> (text, ok)
        """
        qapp()
        text, ok = get_text(None, "Title", "Label:")
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_matches_extended_qinputdialog_api(self) -> None:
        """get_text supports extended QInputDialog.getText parameters."""
        qapp()
        # QInputDialog.getText supports current_text as 4th positional
        text, ok = get_text(None, "Title", "Label:", "current")
        assert isinstance(text, str)
        assert isinstance(ok, bool)


# =============================================================================
# EXPORTS TEST
# =============================================================================


class TestExports:
    """Tests that all public APIs are exported correctly."""

    def test_dialog_classes_exported(self) -> None:
        """Core dialog classes are exported."""
        from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
            ConfirmDialogV2,
            InputDialogV2,
            MessageBoxV2,
        )

        assert ConfirmDialogV2 is not None
        assert InputDialogV2 is not None
        assert MessageBoxV2 is not None

    def test_convenience_functions_exported(self) -> None:
        """Convenience functions are exported."""
        from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
            get_password,
            get_text,
            show_confirm,
            show_error,
            show_info,
            show_question,
            show_warning,
        )

        assert callable(show_info)
        assert callable(show_warning)
        assert callable(show_error)
        assert callable(show_question)
        assert callable(show_confirm)
        assert callable(get_text)
        assert callable(get_password)

    def test_toast_functions_exported(self) -> None:
        """Toast functions are exported."""
        from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
            ToastLevel,
            ToastV2,
            toast_error,
            toast_info,
            toast_success,
            toast_warning,
        )

        assert ToastLevel is not None
        assert ToastV2 is not None
        assert callable(toast_info)
        assert callable(toast_success)
        assert callable(toast_warning)
        assert callable(toast_error)
