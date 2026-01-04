"""
InputDialogV2 - Single-line text input dialog v2.

Replaces QInputDialog.getText() with v2 design system styling.
Features:
- THEME_V2/TOKENS_V2 styling
- Label + text input + optional placeholder
- Validation support (required, min/max length)
- Enter = accept, Esc = cancel
- Optional password mode

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs_v2 import InputDialogV2

    # Basic text input
    text, ok = InputDialogV2.get_text(parent, "New Name", "Enter name:")
    if ok:
        print(f"User entered: {text}")

    # With default value
    text, ok = InputDialogV2.get_text(
        parent,
        "Rename",
        "New name:",
        current_text="MyWorkflow",
    )

    # Password input
    password, ok = InputDialogV2.get_text(
        parent,
        "Password",
        "Enter password:",
        password_mode=True,
    )

    # With validation
    text, ok = InputDialogV2.get_text(
        parent,
        "New Project",
        "Project name:",
        required=True,
        min_length=3,
    )
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2.base_dialog_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import TextInput

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLineEdit


# =============================================================================
# INPUT DIALOG V2
# =============================================================================


class InputDialogV2(BaseDialogV2):
    """
    Single-line text input dialog with v2 styling.

    Replaces QInputDialog.getText() with consistent v2 design.

    Features:
    - Label + text input layout
    - Optional placeholder text
    - Password mode support
    - Validation (required, min/max length)
    - Enter to accept, Esc to cancel

    Example:
        dialog = InputDialogV2(
            title="New Workflow",
            label="Workflow name:",
            placeholder="My Awesome Workflow",
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_value()
            create_workflow(name)
    """

    def __init__(
        self,
        title: str,
        label: str,
        placeholder: str = "",
        current_text: str = "",
        password_mode: bool = False,
        required: bool = False,
        min_length: int = 0,
        max_length: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize input dialog.

        Args:
            title: Dialog title
            label: Label text shown above input
            placeholder: Placeholder text in input field
            current_text: Initial value for input
            password_mode: If True, input is password field (echo mode)
            required: If True, empty input is invalid
            min_length: Minimum length (0 = no minimum)
            max_length: Maximum length (0 = no maximum)
            parent: Optional parent widget
        """
        self._label_text = label
        self._placeholder = placeholder
        self._initial_text = current_text
        self._password_mode = password_mode
        self._required = required
        self._min_length = min_length
        self._max_length = max_length
        self._input_widget: TextInput | None = None

        super().__init__(
            title=title,
            parent=parent,
            size=DialogSizeV2.SM,
            resizable=False,
        )

        # Setup content (creates _input_widget)
        self._setup_content()

        # Set initial text after UI is built (redundant since TextInput takes value param)
        # This is here in case the value wasn't set during creation
        if self._input_widget and current_text and self._input_widget.get_value() != current_text:
            self._input_widget.set_value(current_text)

    def _setup_content(self) -> None:
        """Setup input dialog content."""
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Label
        label = QLabel(self._label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_primary};
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
            }}
        """)
        layout.addWidget(label)

        # Text input (TextInput is a QLineEdit subclass)
        self._input_widget = TextInput(
            placeholder=self._placeholder,
            value=self._initial_text,
            password=self._password_mode,
        )

        # Set max length if specified
        if self._max_length > 0:
            self._input_widget.setMaxLength(self._max_length)

        layout.addWidget(self._input_widget)

        layout.addStretch()

        self.set_body_widget(content)

        # Configure footer
        self._configure_footer()

        # Focus input on show
        self._input_widget.setFocus()

    def _configure_footer(self) -> None:
        """Configure footer for input dialog."""
        if self._footer:
            self._footer.set_primary_text("OK")
            self._footer.set_cancel_text("Cancel")
            # Hide cancel button for simple OK flow
            cancel_btn = self._footer.get_cancel_button()
            if cancel_btn:
                cancel_btn.setVisible(False)

    def validate(self) -> bool:
        """
        Validate input content.

        Returns:
            True if input is valid, False otherwise
        """
        text = self.get_value()

        # Required check
        if self._required and not text:
            self.set_validation_error("This field is required")
            return False

        # Min length check
        if self._min_length > 0 and len(text) < self._min_length:
            self.set_validation_error(f"Must be at least {self._min_length} characters")
            return False

        # Max length is enforced by QLineEdit, but double-check
        if self._max_length > 0 and len(text) > self._max_length:
            self.set_validation_error(f"Must be no more than {self._max_length} characters")
            return False

        return True

    # ========================================================================
    # Public API
    # ========================================================================

    def get_value(self) -> str:
        """
        Get current input value.

        Returns:
            Current text in input field
        """
        if self._input_widget:
            return self._input_widget.get_value()
        return ""

    def set_value(self, text: str) -> None:
        """
        Set input value.

        Args:
            text: Text to set in input field
        """
        if self._input_widget:
            self._input_widget.set_value(text)

    def get_input_widget(self) -> QLineEdit:
        """
        Get the underlying input widget.

        Returns:
            The TextInput widget (which is a QLineEdit subclass)
        """
        return self._input_widget  # type: ignore[return-value]

    # ========================================================================
    # Factory Functions
    # ========================================================================

    @staticmethod
    def get_text(
        parent: QWidget | None,
        title: str,
        label: str,
        current_text: str = "",
        placeholder: str = "",
        password_mode: bool = False,
        required: bool = False,
        min_length: int = 0,
        max_length: int = 0,
    ) -> tuple[str, bool]:
        """
        Show text input dialog and get user input.

        Drop-in replacement for QInputDialog.getText().

        Args:
            parent: Parent widget
            title: Dialog title
            label: Label text shown above input
            current_text: Initial value for input
            placeholder: Placeholder text in input field
            password_mode: If True, input is password field
            required: If True, empty input is invalid
            min_length: Minimum length (0 = no minimum)
            max_length: Maximum length (0 = no maximum)

        Returns:
            Tuple of (text, ok) where:
            - text: User-entered text (empty if cancelled)
            - ok: True if user clicked OK, False if cancelled

        Example:
            # Direct replacement for QInputDialog.getText()
            text, ok = InputDialogV2.get_text(
                parent,
                "New Name",
                "Enter name:",
                current_text="MyWorkflow",
            )
            if ok:
                rename_workflow(text)
        """
        from PySide6.QtWidgets import QDialog

        dialog = InputDialogV2(
            title=title,
            label=label,
            placeholder=placeholder,
            current_text=current_text,
            password_mode=password_mode,
            required=required,
            min_length=min_length,
            max_length=max_length,
            parent=parent,
        )

        if os.getenv("PYTEST_CURRENT_TEST"):
            QTimer.singleShot(0, dialog.reject)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            text = dialog.get_value()
            logger.debug(f"Input dialog accepted: {title} = {text}")
            return text, True

        logger.debug(f"Input dialog cancelled: {title}")
        return "", False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["InputDialogV2"]
