"""
ConfirmDialogV2 - Destructive action confirmation dialogs.

Specialized dialog for confirming destructive actions (delete, remove, etc.).
Features:
- Warning icon and colors
- Destructive button highlighted with error color
- Cancel as default safe option
- Optional detail text

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs_v2 import ConfirmDialogV2

    # Basic confirmation
    if ConfirmDialogV2.show_confirm(parent, "Delete", "Are you sure?"):
        print("User confirmed deletion")

    # With custom button text
    if ConfirmDialogV2.show_confirm(
        parent,
        "Remove Project",
        "This will permanently delete the project and all its data.",
        destructive_text="Delete Project",
    ):
        print("User confirmed project deletion")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2.base_dialog_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)
from casare_rpa.presentation.canvas.ui.dialogs_v2.message_box_v2 import IconWidget

if TYPE_CHECKING:
    pass


# =============================================================================
# CONFIRM DIALOG V2
# =============================================================================


class ConfirmDialogV2(BaseDialogV2):
    """
    Confirmation dialog for destructive actions.

    Features:
    - Warning icon (amber)
    - Primary message and optional detail text
    - Destructive button with error color styling
    - Cancel button as safe default

    Signals:
        accepted: User confirmed the destructive action
        rejected: User cancelled

    Example:
        confirm = ConfirmDialogV2(
            title="Delete Project",
            message="This will permanently delete the project.",
            detail="This action cannot be undone.",
            destructive_text="Delete",
            parent=self
        )
        if confirm.exec() == QDialog.DialogCode.Accepted:
            delete_project()
    """

    def __init__(
        self,
        title: str,
        message: str,
        detail: str = "",
        destructive_text: str = "Delete",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize confirmation dialog.

        Args:
            title: Dialog title
            message: Main confirmation message
            detail: Optional additional detail text
            destructive_text: Text for destructive button (default: "Delete")
            parent: Optional parent widget
        """
        self._message = message
        self._detail = detail
        self._destructive_text = destructive_text

        super().__init__(
            title=title,
            parent=parent,
            size=DialogSizeV2.SM,
            resizable=False,
        )

        self._setup_content()

    def _setup_content(self) -> None:
        """Setup confirmation dialog content."""
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Icon + message row
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(TOKENS_V2.spacing.lg)

        # Warning icon
        icon = IconWidget("warning", size=36)
        row_layout.addWidget(icon)

        # Message column
        message_column = QWidget()
        message_layout = QVBoxLayout(message_column)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(TOKENS_V2.spacing.xs)

        # Main message
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_primary};
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
            }}
        """)
        message_layout.addWidget(message_label)

        # Detail text (if provided)
        if self._detail:
            detail_label = QLabel(self._detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME_V2.text_secondary};
                    font-family: {TOKENS_V2.typography.family};
                    font-size: {TOKENS_V2.typography.body_sm}px;
                }}
            """)
            message_layout.addWidget(detail_label)

        row_layout.addWidget(message_column)
        row_layout.addStretch()

        layout.addWidget(row)
        layout.addStretch()

        self.set_body_widget(content)

        # Configure footer with destructive primary button
        self._configure_footer()

    def _configure_footer(self) -> None:
        """Configure footer for destructive confirmation."""
        if self._footer:
            # Update to destructive button
            self._footer.set_primary_text(self._destructive_text)
            self._footer.set_cancel_text("Cancel")

            # Apply destructive styling to primary button
            primary_btn = self._footer.get_primary_button()
            if primary_btn:
                primary_btn.set_variant("danger")

    # ========================================================================
    # FACTORY FUNCTION
    # ========================================================================

    @staticmethod
    def show_confirm(
        parent: QWidget | None,
        title: str,
        message: str,
        destructive_text: str = "Delete",
        detail: str = "",
    ) -> bool:
        """
        Show destructive action confirmation dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Confirmation message
            destructive_text: Text for destructive button (default: "Delete")
            detail: Optional additional detail text

        Returns:
            True if user confirmed, False if cancelled

        Example:
            if ConfirmDialogV2.show_confirm(
                parent,
                "Delete File",
                "Are you sure you want to delete this file?",
                "Delete"
            ):
                delete_file()
        """
        dialog = ConfirmDialogV2(
            title=title,
            message=message,
            detail=detail,
            destructive_text=destructive_text,
            parent=parent,
        )
        result = dialog.exec()
        logger.debug(f"Confirm dialog shown: {title}, result={result}")
        return result == QDialog.DialogCode.Accepted


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["ConfirmDialogV2"]
