"""
Output Console Widget UI Component.

Provides console-style output display for workflow execution with improved UX:
- Empty state when no output
- Color-coded output levels
- Auto-scroll toggle
- Timestamp display
- Copy and clear functionality
"""

import tempfile
from datetime import datetime
from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
from casare_rpa.presentation.canvas.ui.base_widget import BaseWidget
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import EmptyState

_CHECK_TICK_PNG_PATH: str | None = None


class OutputConsoleWidget(BaseWidget):
    """
    Console widget for displaying execution output.

    Features:
    - Empty state when no output
    - Colored output (info, warning, error, success, debug)
    - Auto-scroll toggle
    - Timestamp display toggle
    - Copy to clipboard
    - Clear functionality
    - Maximum line limit
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize output console widget.

        Args:
            parent: Optional parent widget
        """
        self._auto_scroll = True
        self._show_timestamps = True
        self._max_lines = 1000
        self._line_count = 0

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("consoleToolbar")
        toolbar_widget.setProperty("panelToolbar", True)
        toolbar_widget.setMinimumHeight(TOKENS.sizes.input_lg)
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(
            TOKENS.spacing.xs,
            TOKENS.spacing.xxs,
            TOKENS.spacing.xs,
            TOKENS.spacing.xxs,
        )
        toolbar.setSpacing(TOKENS.spacing.xxs)

        # Line count label
        self._line_count_label = QLabel("0 lines")
        self._line_count_label.setProperty("muted", True)

        # Auto-scroll checkbox
        self._auto_scroll_cb = QCheckBox("Auto-scroll")
        self._auto_scroll_cb.setChecked(self._auto_scroll)
        self._auto_scroll_cb.toggled.connect(self._on_auto_scroll_toggled)
        self._auto_scroll_cb.setToolTip("Automatically scroll to latest output")
        self._apply_tick_checkbox_style(self._auto_scroll_cb)

        # Show timestamps checkbox
        self._timestamps_cb = QCheckBox("Timestamps")
        self._timestamps_cb.setChecked(self._show_timestamps)
        self._timestamps_cb.toggled.connect(self._on_timestamps_toggled)
        self._timestamps_cb.setToolTip("Show timestamps on each line")
        self._apply_tick_checkbox_style(self._timestamps_cb)

        # Copy button
        copy_btn = PushButton(text="Copy", variant="primary", size="sm")
        copy_btn.setToolTip("Copy all output to clipboard")
        copy_btn.clicked.connect(self._on_copy)

        # Clear button
        clear_btn = PushButton(text="Clear", variant="secondary", size="sm")
        clear_btn.setToolTip("Clear console output")
        clear_btn.clicked.connect(self.clear)

        toolbar.addWidget(self._line_count_label)
        toolbar.addStretch()
        toolbar.addWidget(self._auto_scroll_cb)
        toolbar.addWidget(self._timestamps_cb)
        toolbar.addWidget(copy_btn)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar_widget)

        # Content stack for empty state vs console
        self._content_stack = QStackedWidget()

        # Empty state (index 0)
        self._empty_state = EmptyState(
            icon="terminal",
            text="No Output",
            action_text="",
        )
        self._empty_state.set_text(
            "Console output will appear here when:\n"
            "- You run a workflow (F3)\n"
            "- Nodes produce output messages\n"
            "- Debug information is logged"
        )
        self._content_stack.addWidget(self._empty_state)

        # Console text area (index 1)
        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(8, 4, 8, 8)
        console_layout.setSpacing(0)

        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._console.setPlaceholderText("Waiting for output...")
        console_layout.addWidget(self._console)

        self._content_stack.addWidget(console_container)

        layout.addWidget(self._content_stack)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _get_check_tick_png_path(self) -> str:
        """Return a cached filesystem path for the themed tick icon PNG."""
        global _CHECK_TICK_PNG_PATH
        if _CHECK_TICK_PNG_PATH is not None and Path(_CHECK_TICK_PNG_PATH).exists():
            return _CHECK_TICK_PNG_PATH

        icon_size = max(12, TOKENS.sizes.checkbox_size - 4)
        base_pixmap = get_icon("check", size=TOKENS.sizes.icon_sm, state="accent").pixmap(
            icon_size, icon_size
        )
        pixmap = QPixmap(base_pixmap.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, base_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#ffffff"))
        painter.end()

        tmp_dir = Path(tempfile.gettempdir())
        file_name = f"casare_rpa_tick_white_{icon_size}.png"
        png_path = tmp_dir / file_name
        pixmap.save(str(png_path), "PNG")

        _CHECK_TICK_PNG_PATH = str(png_path)
        return _CHECK_TICK_PNG_PATH

    def _apply_tick_checkbox_style(self, checkbox: QCheckBox) -> None:
        """Use an icon tick for checked state (no full-fill indicator)."""
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        tick_path = self._get_check_tick_png_path().replace("\\", "/")
        size = TOKENS.sizes.checkbox_size
        radius = TOKENS.radius.xs

        checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                spacing: {TOKENS.spacing.xxs}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
                font-family: {TOKENS.typography.family};
            }}

            QCheckBox::indicator {{
                width: {size}px;
                height: {size}px;
                border: 1px solid {THEME.border_light};
                border-radius: {radius}px;
                background-color: {THEME.input_bg};
            }}

            QCheckBox::indicator:hover {{
                border-color: {THEME.primary};
            }}

            QCheckBox::indicator:checked {{
                background-color: {THEME.primary}20;
                border-color: {THEME.primary};
                image: url("{tick_path}");
            }}
            """
        )

    def apply_stylesheet(self) -> None:
        """Apply v2 theme styling for the console widget."""
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply v2 theme styling (keep local overrides minimal)."""
        self.setStyleSheet(f"""
            OutputConsoleWidget {{
                background-color: {THEME.bg_surface};
            }}
            QLabel {{
                background: transparent;
            }}
            #consoleToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTextEdit {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_primary};
                font-family: {TOKENS.typography.mono};
                font-size: {TOKENS.typography.body}px;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px;
            }}
        """)

    def _update_display(self) -> None:
        """Update empty state vs console display."""
        has_content = self._line_count > 0
        self._content_stack.setCurrentIndex(1 if has_content else 0)

        # Update line count
        self._line_count_label.setText(
            f"{self._line_count} line{'s' if self._line_count != 1 else ''}"
        )
        self._line_count_label.setProperty("muted", self._line_count == 0)
        self._line_count_label.style().unpolish(self._line_count_label)
        self._line_count_label.style().polish(self._line_count_label)

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
            level: Message level (info, warning, error, success, debug)
            timestamp: Whether to include timestamp
        """
        # Limit number of lines
        if self._console.document().lineCount() > self._max_lines:
            # Remove first line
            cursor = QTextCursor(self._console.document().firstBlock())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove newline
            self._line_count -= 1

        # Choose color based on level (using THEME colors)
        color_map = {
            "info": THEME.text_primary,
            "warning": THEME.warning,
            "error": THEME.error,
            "success": THEME.success,
            "debug": THEME.text_muted,
        }
        color = color_map.get(level.lower(), THEME.text_primary)

        # Format message
        if timestamp and self._show_timestamps:
            ts = datetime.now().strftime("%H:%M:%S")
            formatted = (
                f'<span style="color: {THEME.text_muted};">[{ts}]</span> '
                f'<span style="color: {color};">{text}</span>'
            )
        else:
            formatted = f'<span style="color: {color};">{text}</span>'

        # Append to console
        self._console.append(formatted)
        self._line_count += 1

        # Update display state
        self._update_display()

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
        self._line_count = 0
        self._update_display()
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

