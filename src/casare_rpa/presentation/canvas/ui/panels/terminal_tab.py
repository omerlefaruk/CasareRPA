"""
Terminal Tab for the Bottom Panel.

Provides raw stdout/stderr output display during workflow execution.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Slot
from loguru import logger

from ..widgets.output_console_widget import OutputConsoleWidget


class TerminalTab(QWidget):
    """
    Terminal tab widget for displaying raw output.

    Wraps OutputConsoleWidget to show stdout/stderr during workflow execution.
    Provides a VSCode-style terminal experience.

    Signals:
        output_received: Emitted when new output is received
    """

    output_received = Signal(str, str)  # text, level

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Terminal tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._apply_styles()

        logger.debug("TerminalTab initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        # Use OutputConsoleWidget for display
        self._console = OutputConsoleWidget()
        layout.addWidget(self._console)

        # Connect internal signal
        self.output_received.connect(self._on_output_received)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        from casare_rpa.presentation.canvas.theme import THEME

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_panel};
            }}
        """)

    @Slot(str, str)
    def _on_output_received(self, text: str, level: str) -> None:
        """Handle output received signal."""
        self._console.append_line(text, level)

    # ==================== Public API ====================

    def write(self, text: str, level: str = "info") -> None:
        """
        Write text to the terminal.

        Args:
            text: Text to write
            level: Output level (info, warning, error, success, debug)
        """
        # Strip trailing newline for cleaner display
        text = text.rstrip("\n")
        if text:
            self._console.append_line(text, level, timestamp=True)

    def write_stdout(self, text: str) -> None:
        """
        Write stdout text to the terminal.

        Args:
            text: Text from stdout
        """
        self.write(text, "info")

    def write_stderr(self, text: str) -> None:
        """
        Write stderr text to the terminal.

        Args:
            text: Text from stderr
        """
        self.write(text, "error")

    def append_info(self, text: str) -> None:
        """Append info message."""
        self._console.append_info(text)

    def append_warning(self, text: str) -> None:
        """Append warning message."""
        self._console.append_warning(text)

    def append_error(self, text: str) -> None:
        """Append error message."""
        self._console.append_error(text)

    def append_success(self, text: str) -> None:
        """Append success message."""
        self._console.append_success(text)

    def append_debug(self, text: str) -> None:
        """Append debug message."""
        self._console.append_debug(text)

    def clear(self) -> None:
        """Clear the terminal."""
        self._console.clear()

    def get_text(self) -> str:
        """Get all terminal text."""
        return self._console.get_text()

    def get_line_count(self) -> int:
        """Get the number of lines in the terminal."""
        text = self._console.get_text()
        return len(text.split("\n")) if text else 0
