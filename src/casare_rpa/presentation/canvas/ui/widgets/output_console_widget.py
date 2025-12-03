"""
Output Console Widget UI Component.

Provides console-style output display for workflow execution.
"""

from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QCheckBox,
)
from PySide6.QtGui import QTextCursor

from loguru import logger

from casare_rpa.presentation.canvas.ui.base_widget import BaseWidget


class OutputConsoleWidget(BaseWidget):
    """
    Console widget for displaying execution output.

    Features:
    - Colored output (info, warning, error, success)
    - Auto-scroll
    - Clear functionality
    - Timestamp display
    - Copy to clipboard
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize output console widget.

        Args:
            parent: Optional parent widget
        """
        self._auto_scroll = True
        self._show_timestamps = True
        self._max_lines = 1000

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Auto-scroll checkbox
        self._auto_scroll_cb = QCheckBox("Auto-scroll")
        self._auto_scroll_cb.setChecked(self._auto_scroll)
        self._auto_scroll_cb.toggled.connect(self._on_auto_scroll_toggled)
        toolbar.addWidget(self._auto_scroll_cb)

        # Show timestamps checkbox
        self._timestamps_cb = QCheckBox("Timestamps")
        self._timestamps_cb.setChecked(self._show_timestamps)
        self._timestamps_cb.toggled.connect(self._on_timestamps_toggled)
        toolbar.addWidget(self._timestamps_cb)

        toolbar.addStretch()

        # Copy button
        copy_btn = QPushButton("Copy")
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(self._on_copy)
        toolbar.addWidget(copy_btn)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # Console text area
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._console)

    def append_line(
        self,
        text: str,
        level: str = "info",
        timestamp: bool = True,
    ) -> None:
        """
        Append a line to the console.

        Args:
            text: Text to append
            level: Message level (info, warning, error, success)
            timestamp: Whether to include timestamp
        """
        # Limit number of lines
        if self._console.document().lineCount() > self._max_lines:
            # Remove first line
            cursor = QTextCursor(self._console.document().firstBlock())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove newline

        # Choose color based on level
        color_map = {
            "info": "#d4d4d4",
            "warning": "#cca700",
            "error": "#f44747",
            "success": "#89d185",
            "debug": "#888888",
        }
        color = color_map.get(level.lower(), "#d4d4d4")

        # Format message
        if timestamp and self._show_timestamps:
            ts = datetime.now().strftime("%H:%M:%S")
            formatted = f'<span style="color: #888888;">[{ts}]</span> <span style="color: {color};">{text}</span>'
        else:
            formatted = f'<span style="color: {color};">{text}</span>'

        # Append to console
        self._console.append(formatted)

        # Auto-scroll
        if self._auto_scroll:
            cursor = self._console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self._console.setTextCursor(cursor)

        logger.debug(f"Console output ({level}): {text}")

    def append_info(self, text: str) -> None:
        """
        Append info message.

        Args:
            text: Message text
        """
        self.append_line(text, "info")

    def append_warning(self, text: str) -> None:
        """
        Append warning message.

        Args:
            text: Message text
        """
        self.append_line(text, "warning")

    def append_error(self, text: str) -> None:
        """
        Append error message.

        Args:
            text: Message text
        """
        self.append_line(text, "error")

    def append_success(self, text: str) -> None:
        """
        Append success message.

        Args:
            text: Message text
        """
        self.append_line(text, "success")

    def append_debug(self, text: str) -> None:
        """
        Append debug message.

        Args:
            text: Message text
        """
        self.append_line(text, "debug")

    def clear(self) -> None:
        """Clear console contents."""
        self._console.clear()
        logger.debug("Console cleared")

    def get_text(self) -> str:
        """
        Get all console text.

        Returns:
            Console text content
        """
        return self._console.toPlainText()

    def set_auto_scroll(self, enabled: bool) -> None:
        """
        Set auto-scroll enabled state.

        Args:
            enabled: Whether to enable auto-scroll
        """
        self._auto_scroll = enabled
        self._auto_scroll_cb.setChecked(enabled)

    def set_show_timestamps(self, enabled: bool) -> None:
        """
        Set timestamp display enabled state.

        Args:
            enabled: Whether to show timestamps
        """
        self._show_timestamps = enabled
        self._timestamps_cb.setChecked(enabled)

    def set_max_lines(self, max_lines: int) -> None:
        """
        Set maximum number of lines to keep.

        Args:
            max_lines: Maximum number of lines
        """
        self._max_lines = max_lines

    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        """
        Handle auto-scroll toggle.

        Args:
            checked: New checked state
        """
        self._auto_scroll = checked
        logger.debug(f"Auto-scroll: {checked}")

    def _on_timestamps_toggled(self, checked: bool) -> None:
        """
        Handle timestamps toggle.

        Args:
            checked: New checked state
        """
        self._show_timestamps = checked
        logger.debug(f"Show timestamps: {checked}")

    def _on_copy(self) -> None:
        """Handle copy button click."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self.get_text())
        logger.debug("Console text copied to clipboard")
