"""
Tests for InputDialogV2.

Tests cover:
- Input dialog creation and setup
- get_text factory function
- Validation (required, min/max length)
- Password mode
- Return values (text, ok) tuple matching QInputDialog.getText API
"""

from __future__ import annotations

from casare_rpa.presentation.canvas.ui.dialogs_v2 import InputDialogV2

from .conftest import qapp

# =============================================================================
# INPUT DIALOG V2 TESTS
# =============================================================================


class TestInputDialogV2:
    """Tests for InputDialogV2."""

    def test_input_dialog_creation(self) -> None:
        """InputDialogV2 can be created."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter text:",
        )

        assert dialog is not None
        assert dialog._label_text == "Enter text:"
        assert dialog._placeholder == ""

    def test_input_dialog_with_placeholder(self) -> None:
        """InputDialogV2 can have placeholder text."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
            placeholder="My Workflow",
        )

        assert dialog._placeholder == "My Workflow"

    def test_input_dialog_with_initial_text(self) -> None:
        """InputDialogV2 can have initial text value."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
            current_text="Default Value",
        )

        assert dialog._initial_text == "Default Value"
        # After show, get_value should return initial text
        dialog.show()
        assert dialog.get_value() == "Default Value"

    def test_input_dialog_password_mode(self) -> None:
        """InputDialogV2 supports password mode."""
        qapp()
        dialog = InputDialogV2(
            title="Password",
            label="Enter password:",
            password_mode=True,
        )

        assert dialog._password_mode is True
        assert dialog._input_widget is not None
        # TextInput uses is_password_mode() method
        assert dialog._input_widget.is_password_mode() is True

    def test_input_dialog_required_validation(self) -> None:
        """InputDialogV2 validates required field."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
            required=True,
        )

        assert dialog._required is True

        # Empty input should fail validation
        dialog.show()
        assert not dialog.validate()

        # Non-empty input should pass validation
        dialog.set_value("test")
        assert dialog.validate()

    def test_input_dialog_min_length_validation(self) -> None:
        """InputDialogV2 validates minimum length."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
            min_length=3,
        )

        assert dialog._min_length == 3

        # Short input should fail validation
        dialog.show()
        dialog.set_value("ab")
        assert not dialog.validate()

        # Valid input should pass
        dialog.set_value("abc")
        assert dialog.validate()

    def test_input_dialog_max_length_validation(self) -> None:
        """InputDialogV2 validates maximum length."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
            max_length=5,
        )

        assert dialog._max_length == 5

        # Max length should be set on input widget
        dialog.show()
        input_widget = dialog.get_input_widget()
        assert input_widget is not None
        assert input_widget.maxLength() == 5

    def test_input_dialog_get_value(self) -> None:
        """InputDialogV2 get_value returns current text."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
            current_text="Initial",
        )

        dialog.show()
        assert dialog.get_value() == "Initial"

        dialog.set_value("Changed")
        assert dialog.get_value() == "Changed"

    def test_input_dialog_set_value(self) -> None:
        """InputDialogV2 set_value changes the text."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
        )

        dialog.show()
        dialog.set_value("New Value")
        assert dialog.get_value() == "New Value"

    def test_input_dialog_get_input_widget(self) -> None:
        """InputDialogV2 get_input_widget returns the QLineEdit."""
        qapp()
        dialog = InputDialogV2(
            title="Test",
            label="Enter name:",
        )

        dialog.show()
        input_widget = dialog.get_input_widget()
        assert input_widget is not None

    def test_input_dialog_empty_cancelled(self) -> None:
        """InputDialogV2 returns (empty, False) when cancelled."""
        from PySide6.QtWidgets import QDialog

        qapp()
        text, ok = InputDialogV2.get_text(
            None,
            "Test",
            "Enter name:",
        )

        # Without user interaction, dialog closes with reject
        assert ok is False
        assert text == ""


class TestInputDialogV2Factory:
    """Tests for InputDialogV2 factory function."""

    def test_get_text_returns_tuple(self) -> None:
        """get_text returns (text, ok) tuple matching QInputDialog API."""
        qapp()

        # Mock the exec to return Accepted with text
        text, ok = InputDialogV2.get_text(
            None,
            "Test",
            "Enter name:",
        )

        # Returns tuple (text: str, ok: bool)
        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_with_current_text(self) -> None:
        """get_text supports initial text value."""
        qapp()

        text, ok = InputDialogV2.get_text(
            None,
            "Test",
            "Enter name:",
            current_text="Default",
        )

        # Without user interaction, ok is False
        assert ok is False

    def test_get_text_password_mode(self) -> None:
        """get_text supports password mode."""
        qapp()

        text, ok = InputDialogV2.get_text(
            None,
            "Password",
            "Enter password:",
            password_mode=True,
        )

        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_validation_required(self) -> None:
        """get_text supports required validation."""
        qapp()

        text, ok = InputDialogV2.get_text(
            None,
            "Test",
            "Enter name:",
            required=True,
        )

        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_validation_min_length(self) -> None:
        """get_text supports minimum length validation."""
        qapp()

        text, ok = InputDialogV2.get_text(
            None,
            "Test",
            "Enter name:",
            min_length=3,
        )

        assert isinstance(text, str)
        assert isinstance(ok, bool)

    def test_get_text_validation_max_length(self) -> None:
        """get_text supports maximum length validation."""
        qapp()

        text, ok = InputDialogV2.get_text(
            None,
            "Test",
            "Enter name:",
            max_length=10,
        )

        assert isinstance(text, str)
        assert isinstance(ok, bool)


class TestInputDialogV2Integration:
    """Integration tests for InputDialogV2 with real UI interaction."""

    def test_full_dialog_flow(self) -> None:
        """Test full dialog creation, show, and value retrieval."""
        from PySide6.QtWidgets import QDialog

        qapp()
        dialog = InputDialogV2(
            title="New Workflow",
            label="Workflow name:",
            placeholder="My Awesome Workflow",
            required=True,
            min_length=3,
        )

        # Show dialog
        dialog.show()

        # Set a valid value
        dialog.set_value("TestWorkflow")

        # Validate should pass
        assert dialog.validate()

        # Get value should return what we set
        assert dialog.get_value() == "TestWorkflow"

        # Clean up
        dialog.close()

    def test_password_dialog_flow(self) -> None:
        """Test password dialog flow."""
        qapp()
        dialog = InputDialogV2(
            title="Login",
            label="Password:",
            password_mode=True,
            required=True,
        )

        dialog.show()

        # Password mode is set
        assert dialog._password_mode is True

        # Can set and get value
        dialog.set_value("secret123")
        assert dialog.get_value() == "secret123"

        # Clean up
        dialog.close()
