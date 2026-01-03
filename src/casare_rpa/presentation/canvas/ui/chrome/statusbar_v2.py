"""
StatusBarV2 - Status bar for NewMainWindow with THEME_V2 styling.

Epic 4.2: Chrome - Top Toolbar + Status Bar v2
- Minimal chrome: execution status, zoom display
- THEME_V2 colors for status indicators
- Future: connection status, robot status (placeholders)

See: docs/UX_REDESIGN_PLAN.md Phase 4 Epic 4.2
"""

from loguru import logger
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from casare_rpa.presentation.canvas.theme.tokens_v2 import THEME_V2, TOKENS_V2


class StatusBarV2(QStatusBar):
    """
    V2 status bar with THEME_V2 styling.

    Features:
    - Execution status indicator (Ready/Running/Paused/Error)
    - Zoom display (100%, 150%, etc.)
    - Theme-aware status colors (success/warning/error)
    - Minimal chrome for Epic 4.2

    Future additions (placeholders for later epics):
    - Connection status (robot connection)
    - Robot status
    - Cursor position
    """

    # Status text and color mappings
    _STATUS_MAP = {
        "ready": ("Ready", THEME_V2.success),
        "running": ("Running", THEME_V2.warning),
        "paused": ("Paused", THEME_V2.info),
        "error": ("Error", THEME_V2.error),
        "success": ("Complete", THEME_V2.success),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the status bar v2.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setObjectName("StatusBarV2")

        # Status bar widgets
        self._exec_status_label: QLabel | None = None
        self._zoom_label: QLabel | None = None

        self._create_widgets()

        logger.debug("StatusBarV2 initialized")

    def _create_widgets(self) -> None:
        """Create status bar widgets with minimal v2 chrome."""
        # Right-aligned permanent widgets (added in reverse order)

        # Execution status indicator
        self._exec_status_label = QLabel("Ready")
        self._exec_status_label.setObjectName("execStatusLabel")
        self._exec_status_label.setStyleSheet(
            f"color: {THEME_V2.success};font-size: {TOKENS_V2.typography.body_sm}px;"
        )
        self._exec_status_label.setToolTip("Workflow execution status")
        self.addPermanentWidget(self._exec_status_label)

        # Separator
        self._add_separator()

        # Zoom display
        self._zoom_label = QLabel("100%")
        self._zoom_label.setObjectName("zoomLabel")
        self._zoom_label.setStyleSheet(
            f"color: {THEME_V2.text_secondary};font-size: {TOKENS_V2.typography.body_sm}px;"
        )
        self._zoom_label.setToolTip("Zoom level")
        self.addPermanentWidget(self._zoom_label)

        # Initial status message
        self.showMessage("Ready", 3000)

    def _add_separator(self) -> None:
        """Add a vertical separator to the status bar."""
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {THEME_V2.border};font-size: {TOKENS_V2.typography.body_sm}px;")
        self.addPermanentWidget(sep)

    def set_execution_status(self, status: str) -> None:
        """
        Update execution status indicator.

        Args:
            status: One of 'ready', 'running', 'paused', 'error', 'success'
        """
        if self._exec_status_label is None:
            return

        text, color = self._STATUS_MAP.get(status, self._STATUS_MAP["ready"])
        self._exec_status_label.setText(text)
        self._exec_status_label.setStyleSheet(
            f"color: {color};font-size: {TOKENS_V2.typography.body_sm}px;"
        )

        logger.debug(f"StatusBarV2 execution status: {text} ({status})")

    def set_zoom(self, zoom_percent: float) -> None:
        """
        Update the zoom display.

        Args:
            zoom_percent: Current zoom percentage (e.g., 100.0 for 100%)
        """
        if self._zoom_label is None:
            return

        self._zoom_label.setText(f"{int(zoom_percent)}%")
        logger.debug(f"StatusBarV2 zoom: {zoom_percent}%")

    def show_message(self, message: str, duration: int = 3000) -> None:
        """
        Show a temporary message in the status bar.

        Args:
            message: Message text to display
            duration: Duration in milliseconds (0 for permanent)
        """
        super().showMessage(message, duration)
        logger.debug(f"StatusBarV2 message: {message}")

