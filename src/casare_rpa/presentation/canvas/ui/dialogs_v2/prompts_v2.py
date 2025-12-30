"""
PromptsV2 - Convenience API for Epic 7.3 migration.

Drop-in replacements for QMessageBox and QInputDialog usage.
All functions use v2 design system (THEME_V2/TOKENS_V2).

Usage:
    # Replace QMessageBox.* calls
    from casare_rpa.presentation.canvas.ui.dialogs_v2.prompts_v2 import (
        show_info, show_warning, show_error, show_question,
        get_text, show_confirm,
    )

    # Direct replacements for QMessageBox
    show_info(parent, "Title", "Message")           # QMessageBox.information
    show_warning(parent, "Title", "Message")        # QMessageBox.warning
    show_error(parent, "Title", "Message")          # QMessageBox.critical
    result = show_question(parent, "Title", "Message")  # QMessageBox.question

    # Direct replacement for QInputDialog.getText
    text, ok = get_text(parent, "Title", "Label:", current_text="value")
    if ok:
        process(text)

    # Destructive confirmations
    if show_confirm(parent, "Delete", "Are you sure?", "Delete"):
        delete_item()

Migration:
    Find/Replace in files:
    - QMessageBox.information → show_info
    - QMessageBox.warning → show_warning
    - QMessageBox.critical → show_error
    - QMessageBox.question → show_question
    - QInputDialog.getText → get_text
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from casare_rpa.presentation.canvas.ui.dialogs_v2.confirm_dialog_v2 import (
    ConfirmDialogV2,
)
from casare_rpa.presentation.canvas.ui.dialogs_v2.input_dialog_v2 import (
    InputDialogV2,
)
from casare_rpa.presentation.canvas.ui.dialogs_v2.message_box_v2 import (
    MessageBoxV2,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.toast_v2 import (
    ToastLevel,
    ToastV2,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.toast_v2 import (
    show_error as show_error_toast,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.toast_v2 import (
    show_info as show_info_toast,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.toast_v2 import (
    show_success as show_success_toast,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.toast_v2 import (
    show_warning as show_warning_toast,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


# =============================================================================
# MESSAGE BOX REPLACEMENTS (Modal blocking dialogs)
# =============================================================================


def show_info(parent: QWidget | None, title: str, message: str) -> None:
    """
    Show informational message dialog.

    Drop-in replacement for QMessageBox.information().

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text

    Example:
        # Before:
        # QMessageBox.information(parent, "Success", "File saved")

        # After:
        show_info(parent, "Success", "File saved")
    """
    MessageBoxV2.show_info(parent, title, message)


def show_warning(parent: QWidget | None, title: str, message: str) -> None:
    """
    Show warning message dialog.

    Drop-in replacement for QMessageBox.warning().

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text

    Example:
        # Before:
        # QMessageBox.warning(parent, "Warning", "Unsaved changes")

        # After:
        show_warning(parent, "Warning", "Unsaved changes")
    """
    MessageBoxV2.show_warning(parent, title, message)


def show_error(parent: QWidget | None, title: str, message: str) -> None:
    """
    Show error message dialog.

    Drop-in replacement for QMessageBox.critical().

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text

    Example:
        # Before:
        # QMessageBox.critical(parent, "Error", "Failed to save")

        # After:
        show_error(parent, "Error", "Failed to save")
    """
    MessageBoxV2.show_error(parent, title, message)


def show_question(parent: QWidget | None, title: str, message: str) -> bool:
    """
    Show yes/no question dialog.

    Drop-in replacement for QMessageBox.question().

    Args:
        parent: Parent widget
        title: Dialog title
        message: Question text

    Returns:
        True if user clicked Yes, False if No

    Example:
        # Before:
        # result = QMessageBox.question(
        #     parent, "Confirm", "Continue?",
        #     QMessageBox.Yes | QMessageBox.No
        # )
        # if result == QMessageBox.Yes:
        #     proceed()

        # After:
        if show_question(parent, "Confirm", "Continue?"):
            proceed()
    """
    return MessageBoxV2.show_question(parent, title, message)


def show_confirm(
    parent: QWidget | None,
    title: str,
    message: str,
    destructive_text: str = "Delete",
    detail: str = "",
) -> bool:
    """
    Show destructive action confirmation dialog.

    Enhanced replacement for QMessageBox.question() with destructive styling.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Confirmation message
        destructive_text: Text for destructive button (default: "Delete")
        detail: Optional additional detail text

    Returns:
        True if user confirmed, False if cancelled

    Example:
        # Before:
        # result = QMessageBox.question(
        #     parent, "Delete", "Are you sure?",
        #     QMessageBox.Yes | QMessageBox.No
        # )

        # After:
        if show_confirm(parent, "Delete", "Are you sure?", "Delete"):
            delete_item()
    """
    return ConfirmDialogV2.show_confirm(
        parent,
        title,
        message,
        destructive_text=destructive_text,
        detail=detail,
    )


# =============================================================================
# INPUT DIALOG REPLACEMENTS
# =============================================================================


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
    Show text input dialog.

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
        # Before:
        # text, ok = QInputDialog.getText(parent, "New Name", "Enter name:")
        # if ok:
        #     rename(text)

        # After:
        text, ok = get_text(parent, "New Name", "Enter name:")
        if ok:
            rename(text)

        # With default value:
        text, ok = get_text(
            parent, "Rename", "New name:", current_text="MyWorkflow"
        )
    """
    return InputDialogV2.get_text(
        parent=parent,
        title=title,
        label=label,
        current_text=current_text,
        placeholder=placeholder,
        password_mode=password_mode,
        required=required,
        min_length=min_length,
        max_length=max_length,
    )


def get_password(
    parent: QWidget | None,
    title: str,
    label: str,
    required: bool = True,
) -> tuple[str, bool]:
    """
    Show password input dialog.

    Convenience wrapper for get_text() with password_mode=True.

    Args:
        parent: Parent widget
        title: Dialog title
        label: Label text shown above input
        required: If True, empty input is invalid (default: True)

    Returns:
        Tuple of (password, ok)

    Example:
        password, ok = get_password(parent, "Login", "Enter password:")
        if ok:
            authenticate(password)
    """
    return get_text(
        parent=parent,
        title=title,
        label=label,
        password_mode=True,
        required=required,
    )


# =============================================================================
# NON-BLOCKING TOAST NOTIFICATIONS
# =============================================================================


def toast_info(
    message: str,
    title: str = "",
    duration_ms: int = 3000,
    parent: QWidget | None = None,
) -> ToastV2:
    """
    Show non-blocking info toast notification.

    Use for non-modal feedback (e.g., "Saved successfully").

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms
        parent: Parent widget

    Returns:
        ToastV2 instance (for testing/signal connection)

    Example:
        # Non-blocking success feedback
        toast_info("Workflow saved successfully")

        # With title
        toast_info("File uploaded", "Upload Complete")
    """
    return show_info_toast(message=message, title=title, duration_ms=duration_ms, parent=parent)


def toast_success(
    message: str,
    title: str = "",
    duration_ms: int = 3000,
    parent: QWidget | None = None,
) -> ToastV2:
    """
    Show non-blocking success toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms
        parent: Parent widget

    Returns:
        ToastV2 instance

    Example:
        toast_success("Changes applied successfully")
    """
    return show_success_toast(message=message, title=title, duration_ms=duration_ms, parent=parent)


def toast_warning(
    message: str,
    title: str = "",
    duration_ms: int = 3000,
    parent: QWidget | None = None,
) -> ToastV2:
    """
    Show non-blocking warning toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms
        parent: Parent widget

    Returns:
        ToastV2 instance

    Example:
        toast_warning("3 nodes have validation errors")
    """
    return show_warning_toast(message=message, title=title, duration_ms=duration_ms, parent=parent)


def toast_error(
    message: str,
    title: str = "",
    duration_ms: int = 5000,
    parent: QWidget | None = None,
) -> ToastV2:
    """
    Show non-blocking error toast notification.

    Args:
        message: Main message text
        title: Optional title text
        duration_ms: Auto-dismiss duration in ms (default 5s for errors)
        parent: Parent widget

    Returns:
        ToastV2 instance

    Example:
        toast_error("Failed to save workflow")
    """
    return show_error_toast(message=message, title=title, duration_ms=duration_ms, parent=parent)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Modal dialogs (QMessageBox replacements)
    "show_info",
    "show_warning",
    "show_error",
    "show_question",
    "show_confirm",
    # Input dialogs (QInputDialog replacements)
    "get_text",
    "get_password",
    # Non-blocking toasts
    "toast_info",
    "toast_success",
    "toast_warning",
    "toast_error",
    "ToastLevel",
    "ToastV2",
]
