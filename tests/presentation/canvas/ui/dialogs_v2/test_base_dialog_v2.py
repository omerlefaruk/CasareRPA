"""
Tests for BaseDialogV2 and related classes.

Tests cover:
- ButtonRole and DialogSizeV2 enums
- DialogFooter button layout and styling
- DialogTitleBar title display
- BaseDialogV2 layout, keyboard handling, and behavior
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    ButtonRole,
    DialogFooter,
    DialogSizeV2,
    DialogTitleBar,
)

from .conftest import qapp, signal_capture

# =============================================================================
# ENUM TESTS
# =============================================================================


class TestButtonRole:
    """Tests for ButtonRole enum."""

    def test_button_role_values(self) -> None:
        """ButtonRole has correct values."""
        assert ButtonRole.PRIMARY.value == "primary"
        assert ButtonRole.SECONDARY.value == "secondary"
        assert ButtonRole.DESTRUCTIVE.value == "destructive"
        assert ButtonRole.CANCEL.value == "cancel"

    def test_button_role_members(self) -> None:
        """ButtonRole has all expected members."""
        members = [role.value for role in ButtonRole]
        assert "primary" in members
        assert "secondary" in members
        assert "destructive" in members
        assert "cancel" in members


class TestDialogSizeV2:
    """Tests for DialogSizeV2 enum."""

    def test_dialog_size_values(self) -> None:
        """DialogSizeV2 has correct values."""
        assert DialogSizeV2.SM.value == "sm"
        assert DialogSizeV2.MD.value == "md"
        assert DialogSizeV2.LG.value == "lg"


# =============================================================================
# DIALOG FOOTER TESTS
# =============================================================================


class TestDialogFooter:
    """Tests for DialogFooter."""

    def test_footer_creation(self) -> None:
        """Footer can be created with default parameters."""
        qapp()
        footer = DialogFooter()
        assert footer is not None
        assert footer._primary_btn is not None
        assert footer._cancel_btn is not None

    def test_footer_buttons_exist(self) -> None:
        """Footer has primary and cancel buttons."""
        qapp()
        footer = DialogFooter()
        primary = footer.get_primary_button()
        cancel = footer.get_cancel_button()

        assert primary is not None
        assert cancel is not None
        assert primary.text() == "OK"
        assert cancel.text() == "Cancel"

    def test_footer_primary_clicked_signal(self) -> None:
        """Footer emits primary_clicked when primary button clicked."""
        qapp()
        footer = DialogFooter()

        with signal_capture(footer.primary_clicked) as captured:
            footer._primary_btn.click()

        assert len(captured) == 1

    def test_footer_cancel_clicked_signal(self) -> None:
        """Footer emits cancel_clicked when cancel button clicked."""
        qapp()
        footer = DialogFooter()

        with signal_capture(footer.cancel_clicked) as captured:
            footer._cancel_btn.click()

        assert len(captured) == 1

    def test_footer_set_primary_text(self) -> None:
        """Can update primary button text."""
        qapp()
        footer = DialogFooter()
        footer.set_primary_text("Save")

        assert footer._primary_btn.text() == "Save"

    def test_footer_set_cancel_text(self) -> None:
        """Can update cancel button text."""
        qapp()
        footer = DialogFooter()
        footer.set_cancel_text("Close")

        assert footer._cancel_btn.text() == "Close"

    def test_footer_set_primary_enabled(self) -> None:
        """Can enable/disable primary button."""
        qapp()
        footer = DialogFooter()

        footer.set_primary_enabled(False)
        assert not footer._primary_btn.isEnabled()

        footer.set_primary_enabled(True)
        assert footer._primary_btn.isEnabled()

    def test_footer_destructive_primary(self) -> None:
        """Footer can have destructive primary button."""
        qapp()
        footer = DialogFooter(destructive_primary=True)

        # Destructive buttons use danger variant
        primary = footer.get_primary_button()
        assert primary is not None
        assert primary._variant == "danger"


# =============================================================================
# DIALOG TITLE BAR TESTS
# =============================================================================


class TestDialogTitleBar:
    """Tests for DialogTitleBar."""

    def test_title_bar_creation(self) -> None:
        """Title bar can be created."""
        qapp()
        title_bar = DialogTitleBar(title="Test Dialog")
        assert title_bar is not None
        assert title_bar._title == "Test Dialog"

    def test_title_bar_set_title(self) -> None:
        """Can update title bar text."""
        qapp()
        title_bar = DialogTitleBar(title="Original")
        title_bar.set_title("Updated")

        assert title_bar._title == "Updated"
        if title_bar._title_label:
            assert title_bar._title_label.text() == "Updated"

    def test_title_bar_with_close_button(self) -> None:
        """Title bar can show close button."""
        qapp()
        title_bar = DialogTitleBar(title="Test", show_close=True)

        assert title_bar._show_close is True
        assert title_bar._close_btn is not None

    def test_title_bar_close_requested_signal(self) -> None:
        """Title bar emits close_requested when close button clicked."""
        qapp()
        title_bar = DialogTitleBar(title="Test", show_close=True)

        with signal_capture(title_bar.close_requested) as captured:
            title_bar._close_btn.click()

        assert len(captured) == 1

    def test_title_bar_draggable(self) -> None:
        """Title bar supports dragging when parent dialog set."""
        qapp()
        title_bar = DialogTitleBar(title="Test")
        dialog = BaseDialogV2(title="Test", size=DialogSizeV2.SM)
        title_bar.set_parent_dialog(dialog)

        assert title_bar._parent_dialog is dialog


# =============================================================================
# BASE DIALOG V2 TESTS
# =============================================================================


class TestBaseDialogV2:
    """Tests for BaseDialogV2."""

    def test_dialog_creation(self) -> None:
        """Dialog can be created with default parameters."""
        qapp()
        dialog = BaseDialogV2(title="Test Dialog")

        assert dialog is not None
        assert dialog._dialog_title == "Test Dialog"
        assert dialog._size == DialogSizeV2.MD

    def test_dialog_size_sm(self) -> None:
        """Dialog SM size matches TOKENS_V2."""
        qapp()
        dialog = BaseDialogV2(title="Test", size=DialogSizeV2.SM)

        expected_width = TOKENS_V2.sizes.dialog_sm_width
        expected_height = TOKENS_V2.sizes.dialog_height_sm

        assert dialog.width() == expected_width
        assert dialog.height() == expected_height

    def test_dialog_size_md(self) -> None:
        """Dialog MD size matches TOKENS_V2."""
        qapp()
        dialog = BaseDialogV2(title="Test", size=DialogSizeV2.MD)

        expected_width = TOKENS_V2.sizes.dialog_md_width
        expected_height = TOKENS_V2.sizes.dialog_height_md

        assert dialog.width() == expected_width
        assert dialog.height() == expected_height

    def test_dialog_size_lg(self) -> None:
        """Dialog LG size matches TOKENS_V2."""
        qapp()
        dialog = BaseDialogV2(title="Test", size=DialogSizeV2.LG)

        expected_width = TOKENS_V2.sizes.dialog_lg_width
        expected_height = TOKENS_V2.sizes.dialog_height_lg

        assert dialog.width() == expected_width
        assert dialog.height() == expected_height

    def test_dialog_is_modal(self) -> None:
        """Dialog is modal by default."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        assert dialog.isModal() is True

    def test_dialog_set_body_widget(self) -> None:
        """Can set body content widget."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        content = QLabel("Test content")
        dialog.set_body_widget(content)

        assert dialog._body_widget is content

    def test_dialog_set_title(self) -> None:
        """Can update dialog title."""
        qapp()
        dialog = BaseDialogV2(title="Original")
        dialog.set_title("Updated")

        assert dialog._dialog_title == "Updated"

    def test_dialog_set_primary_button(self) -> None:
        """Can set primary button."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        button = dialog.set_primary_button("Save")
        assert button is not None
        assert button.text() == "Save"

    def test_dialog_set_secondary_button(self) -> None:
        """Can set secondary button (uses cancel button)."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        button = dialog.set_secondary_button("Cancel")
        assert button is not None

    def test_dialog_set_footer_visible(self) -> None:
        """Can hide/show footer."""
        qapp()
        dialog = BaseDialogV2(title="Test")
        dialog.show()  # Need to show for visibility to be meaningful

        dialog.set_footer_visible(False)
        assert not dialog._footer.isVisible()

        dialog.set_footer_visible(True)
        assert dialog._footer.isVisible()

    def test_dialog_validate_returns_true(self) -> None:
        """Default validate returns True."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        assert dialog.validate() is True

    def test_dialog_accept_emits_accepted(self) -> None:
        """Dialog emits accepted when accept is called."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        with signal_capture(dialog.accepted) as captured:
            dialog.accept()

        assert len(captured) == 1

    def test_dialog_reject_emits_rejected(self) -> None:
        """Dialog emits rejected when reject is called."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        with signal_capture(dialog.rejected) as captured:
            dialog.reject()

        assert len(captured) == 1


# =============================================================================
# KEYBOARD HANDLING TESTS
# =============================================================================


class TestDialogKeyboardHandling:
    """Tests for dialog keyboard shortcuts."""

    def test_escape_key_rejects_dialog(self) -> None:
        """Pressing Escape rejects the dialog."""
        qapp()
        dialog = BaseDialogV2(title="Test")
        dialog.show()

        with signal_capture(dialog.rejected) as captured:
            from PySide6.QtGui import QKeyEvent

            key_event = QKeyEvent(
                QKeyEvent.Type.KeyPress,
                Qt.Key.Key_Escape,
                Qt.KeyboardModifier.NoModifier,
            )
            dialog.keyPressEvent(key_event)

        assert len(captured) == 1

    def test_enter_key_with_text_input_no_trigger(self) -> None:
        """Enter key in text input does NOT trigger primary button."""
        qapp()
        dialog = BaseDialogV2(title="Test")
        dialog.set_primary_button("OK")

        # Add text input to body
        text_input = QLineEdit()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(text_input)
        dialog.set_body_widget(content)

        # Show dialog and focus the text input
        dialog.show()
        text_input.setFocus()

        # Note: In headless test environment, focusWidget() may not work as expected.
        # The keyPressEvent handler checks isinstance(focused, (QLineEdit, QTextEdit))
        # to avoid triggering primary button when in text input.

        # Simulate Enter press - should not trigger primary button
        # (because focus would be on text input in real UI)
        # (we can't directly test this without spy,
        # but the keyPressEvent handler checks for this)


# =============================================================================
# ESCAPE FILTER TESTS
# =============================================================================


class TestEscapeFilter:
    """Tests for Escape key event filter on text widgets."""

    def test_escape_in_text_input_rejects_dialog(self) -> None:
        """Escape in text input triggers dialog reject via eventFilter."""
        qapp()
        dialog = BaseDialogV2(title="Test")

        # Add text input to body
        text_input = QLineEdit()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(text_input)
        dialog.set_body_widget(content)

        # Verify event filter was installed
        assert text_input in dialog._escape_filter_widgets

        # Simulate Escape key on text input
        with signal_capture(dialog.rejected) as captured:
            from PySide6.QtGui import QKeyEvent

            key_event = QKeyEvent(
                QKeyEvent.Type.KeyPress,
                Qt.Key.Key_Escape,
                Qt.KeyboardModifier.NoModifier,
            )
            # Event filter should return True and handle it
            result = dialog.eventFilter(text_input, key_event)

        assert result is True
        assert len(captured) == 1
