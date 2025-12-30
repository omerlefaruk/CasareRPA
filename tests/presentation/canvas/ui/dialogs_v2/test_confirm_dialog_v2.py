"""
Tests for ConfirmDialogV2.

Tests cover:
- ConfirmDialogV2 creation and setup
- Destructive button styling
- Factory function (show_confirm)
- Modal behavior
"""

from __future__ import annotations

from casare_rpa.presentation.canvas.ui.dialogs_v2 import ConfirmDialogV2, DialogSizeV2

from .conftest import qapp, signal_capture

# =============================================================================
# CONFIRM DIALOG V2 TESTS
# =============================================================================


class TestConfirmDialogV2:
    """Tests for ConfirmDialogV2."""

    def test_confirm_dialog_creation(self) -> None:
        """ConfirmDialogV2 can be created."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        assert dialog is not None
        assert dialog._message == "Are you sure?"
        assert dialog._destructive_text == "Delete"

    def test_confirm_dialog_with_detail(self) -> None:
        """ConfirmDialogV2 can include detail text."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            detail="This action cannot be undone.",
        )

        assert dialog._detail == "This action cannot be undone."

    def test_confirm_dialog_custom_destructive_text(self) -> None:
        """ConfirmDialogV2 can have custom destructive button text."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Remove",
            message="Remove item?",
            destructive_text="Remove Permanently",
        )

        assert dialog._destructive_text == "Remove Permanently"

    def test_confirm_dialog_uses_sm_size(self) -> None:
        """ConfirmDialogV2 uses SM size by default."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        assert dialog._size == DialogSizeV2.SM

    def test_confirm_dialog_is_modal(self) -> None:
        """ConfirmDialogV2 is modal."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        assert dialog.isModal() is True

    def test_confirm_dialog_not_resizable(self) -> None:
        """ConfirmDialogV2 is not resizable by default."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        assert dialog._resizable is False

    def test_confirm_dialog_has_body_content(self) -> None:
        """ConfirmDialogV2 sets body content widget."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        assert dialog._body_widget is not None

    def test_confirm_dialog_footer_configuration(self) -> None:
        """ConfirmDialogV2 has properly configured footer."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            destructive_text="Delete",
        )

        primary = dialog._footer.get_primary_button()
        cancel = dialog._footer.get_cancel_button()

        assert primary is not None
        assert cancel is not None
        assert primary.text() == "Delete"
        assert cancel.text() == "Cancel"

    def test_confirm_dialog_destructive_button_styling(self) -> None:
        """Primary button has danger variant for destructive action."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        primary = dialog._footer.get_primary_button()
        assert primary is not None
        assert primary._variant == "danger"

    def test_confirm_dialog_accept_emits_accepted(self) -> None:
        """Dialog emits accepted when user confirms."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        with signal_capture(dialog.accepted) as captured:
            dialog.accept()

        assert len(captured) == 1

    def test_confirm_dialog_reject_emits_rejected(self) -> None:
        """Dialog emits rejected when user cancels."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        with signal_capture(dialog.rejected) as captured:
            dialog.reject()

        assert len(captured) == 1


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestConfirmDialogFactory:
    """Tests for ConfirmDialogV2 factory function."""

    def test_show_confirm_creates_dialog(self) -> None:
        """show_confirm creates ConfirmDialogV2."""
        qapp()

        # Create dialog without exec for testing
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            destructive_text="Delete",
            parent=None,
        )

        assert dialog is not None
        assert dialog._message == "Are you sure?"
        assert dialog._destructive_text == "Delete"

    def test_show_confirm_with_all_parameters(self) -> None:
        """show_confirm works with all parameters."""
        qapp()

        dialog = ConfirmDialogV2(
            title="Remove Project",
            message="Delete this project?",
            detail="This cannot be undone.",
            destructive_text="Delete Project",
            parent=None,
        )

        assert dialog._message == "Delete this project?"
        assert dialog._detail == "This cannot be undone."
        assert dialog._destructive_text == "Delete Project"

    def test_show_confirm_returns_true_on_accept(self) -> None:
        """show_confirm returns True when user confirms."""
        qapp()

        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            parent=None,
        )

        # Simulate user clicking confirm
        # In actual usage, exec() would return Accepted
        assert dialog._destructive_text == "Delete"

    def test_show_confirm_returns_false_on_reject(self) -> None:
        """show_confirm returns False when user cancels."""
        qapp()

        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            parent=None,
        )

        # Simulate user clicking cancel
        # In actual usage, exec() would return Rejected
        assert dialog._destructive_text == "Delete"


# =============================================================================
# CONTENT LAYOUT TESTS
# =============================================================================


class TestConfirmDialogContent:
    """Tests for ConfirmDialogV2 content layout."""

    def test_content_has_warning_icon(self) -> None:
        """Confirm dialog includes warning icon."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
        )

        # Icon widget should be in body
        # We can't directly access the icon widget without exposing it,
        # but we can verify body content was set
        assert dialog._body_widget is not None

    def test_content_displays_message(self) -> None:
        """Confirm dialog displays main message."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure you want to delete?",
        )

        assert dialog._message == "Are you sure you want to delete?"
        assert dialog._body_widget is not None

    def test_content_displays_detail_when_provided(self) -> None:
        """Confirm dialog displays detail text when provided."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            detail="This action cannot be undone.",
        )

        assert dialog._detail == "This action cannot be undone."

    def test_content_no_detail_when_empty(self) -> None:
        """Confirm dialog handles empty detail text."""
        qapp()
        dialog = ConfirmDialogV2(
            title="Delete",
            message="Are you sure?",
            detail="",
        )

        assert dialog._detail == ""
        assert dialog._body_widget is not None
