"""
MessageBoxV2 - Standardized message box dialogs.

Provides factory functions for common message box types:
- show_info: Informational message
- show_warning: Warning message
- show_error: Error message
- show_question: Yes/No question (returns bool)

All use THEME_V2/TOKENS_V2 styling with appropriate icons and colors.

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs_v2 import MessageBoxV2

    # Simple message (blocking, modal)
    MessageBoxV2.show_info(parent, "Success", "Operation completed")
    MessageBoxV2.show_warning(parent, "Warning", "Check your inputs")
    MessageBoxV2.show_error(parent, "Error", "Something went wrong")

    # Question dialog (returns bool)
    if MessageBoxV2.show_question(parent, "Confirm", "Continue?"):
        print("User clicked Yes")
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2.base_dialog_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# ICON WIDGET
# =============================================================================


class IconWidget(QWidget):
    """
    Simple widget for rendering message box icons.

    Uses Unicode symbols with THEME_V2 color styling instead of images.
    """

    # Icon symbols mapped to THEME_V2 color attributes
    ICONS = {
        "info": {"symbol": "i", "color_attr": "info"},
        "warning": {"symbol": "!", "color_attr": "warning"},
        "error": {"symbol": "X", "color_attr": "error"},
        "question": {"symbol": "?", "color_attr": "primary"},
    }

    def __init__(self, icon_type: str, size: int = 48, parent: QWidget | None = None) -> None:
        """
        Initialize icon widget.

        Args:
            icon_type: Type of icon (info, warning, error, question)
            size: Icon size in pixels
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._icon_type = icon_type
        self._size = size

        icon_data = self.ICONS.get(icon_type, self.ICONS["info"])
        self._symbol = icon_data["symbol"]
        self._color_attr = icon_data["color_attr"]

        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        """Paint the icon."""
        from PySide6.QtGui import QFont, QPainter, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circle background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawEllipse(0, 0, self._size, self._size)

        # Draw symbol with THEME_V2 color
        color = getattr(THEME_V2, self._color_attr, THEME_V2.primary)
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)

        font = QFont()
        font.setPixelSize(int(self._size * 0.5))
        font.setBold(True)
        painter.setFont(font)

        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self._symbol,
        )


# =============================================================================
# MESSAGE BOX V2
# =============================================================================


class MessageBoxV2(BaseDialogV2):
    """
    Standardized message box dialog.

    Types:
        info: Informational message with blue icon
        warning: Warning message with amber icon
        error: Error message with red icon
        question: Yes/No question with blue icon (returns bool)

    Example:
        # Non-blocking usage
        msg_box = MessageBoxV2(
            title="Information",
            message="Operation completed successfully",
            msg_type="info",
            parent=self
        )
        msg_box.exec()

        # Factory functions (recommended)
        MessageBoxV2.show_info(parent, "Success", "Done!")
    """

    def __init__(
        self,
        title: str,
        message: str,
        msg_type: str = "info",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize message box.

        Args:
            title: Dialog title
            message: Message text to display
            msg_type: Type of message (info, warning, error, question)
            parent: Optional parent widget
        """
        self._message = message
        self._msg_type = msg_type

        # Size depends on message length
        size = DialogSizeV2.SM if len(message) < 100 else DialogSizeV2.MD

        # For question dialogs, show title bar
        show_title = msg_type == "question"

        super().__init__(
            title=title,
            parent=parent,
            size=size,
            resizable=False,
            show_title_bar=show_title,
        )

        self._setup_content()

    def _setup_content(self) -> None:
        """Setup message box content."""
        # Content widget
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.lg)

        # Icon
        icon = IconWidget(self._msg_type, size=40)
        layout.addWidget(icon)

        # Message label
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        message_label.setMinimumWidth(200)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_primary};
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
            }}
        """)
        layout.addWidget(message_label)

        layout.addStretch()

        self.set_body_widget(content)

        # Configure footer based on type
        self._configure_footer()

    def _configure_footer(self) -> None:
        """Configure footer buttons based on message type."""
        if self._msg_type == "question":
            # Question: Yes/No buttons
            if self._footer:
                self._footer.set_primary_text("Yes")
                self._footer.set_cancel_text("No")
        else:
            # Other types: OK button only
            if self._footer:
                self._footer.set_primary_text("OK")
                # Hide cancel button
                cancel_btn = self._footer.get_cancel_button()
                if cancel_btn:
                    cancel_btn.setVisible(False)

    # ========================================================================
    # FACTORY FUNCTIONS
    # ========================================================================

    @staticmethod
    def show_info(parent: QWidget | None, title: str, message: str) -> None:
        """
        Show informational message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message text

        Example:
            MessageBoxV2.show_info(parent, "Success", "File saved")
        """
        msg_box = MessageBoxV2(title, message, "info", parent)
        if os.getenv("PYTEST_CURRENT_TEST"):
            QTimer.singleShot(0, msg_box.accept)
        msg_box.exec()
        logger.debug(f"Info message shown: {title}")

    @staticmethod
    def show_warning(parent: QWidget | None, title: str, message: str) -> None:
        """
        Show warning message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message text

        Example:
            MessageBoxV2.show_warning(parent, "Warning", "Unsaved changes")
        """
        msg_box = MessageBoxV2(title, message, "warning", parent)
        if os.getenv("PYTEST_CURRENT_TEST"):
            QTimer.singleShot(0, msg_box.accept)
        msg_box.exec()
        logger.debug(f"Warning message shown: {title}")

    @staticmethod
    def show_error(parent: QWidget | None, title: str, message: str) -> None:
        """
        Show error message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message text

        Example:
            MessageBoxV2.show_error(parent, "Error", "Failed to save file")
        """
        msg_box = MessageBoxV2(title, message, "error", parent)
        if os.getenv("PYTEST_CURRENT_TEST"):
            QTimer.singleShot(0, msg_box.accept)
        msg_box.exec()
        logger.debug(f"Error message shown: {title}")

    @staticmethod
    def show_question(parent: QWidget | None, title: str, message: str) -> bool:
        """
        Show yes/no question dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Question text

        Returns:
            True if user clicked Yes, False if No

        Example:
            if MessageBoxV2.show_question(parent, "Confirm", "Delete file?"):
                print("User confirmed")
        """
        msg_box = MessageBoxV2(title, message, "question", parent)
        if os.getenv("PYTEST_CURRENT_TEST"):
            QTimer.singleShot(0, msg_box.reject)
        result = msg_box.exec()
        logger.debug(f"Question shown: {title}, result={result}")
        return result == QDialog.DialogCode.Accepted


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["MessageBoxV2"]

