"""
Base Tab Widget for Fleet Dashboard.

Provides common functionality for all fleet dashboard tabs:
- Refresh button management
- Timer-based auto-refresh
- Status label
- Common styling
"""

from abc import abstractmethod

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    REFRESH_INTERVALS,
    TAB_WIDGET_BASE_STYLE,
)


class BaseTabWidget(QWidget):
    """
    Base class for fleet dashboard tab widgets.

    Provides:
    - Automatic refresh timer
    - Refresh button state management
    - Status label updates
    - Common styling

    Subclasses must implement:
    - _setup_content(): Create tab-specific UI
    - _apply_additional_styles(): Add tab-specific styles
    """

    refresh_requested = Signal()

    def __init__(
        self,
        tab_name: str,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize base tab widget.

        Args:
            tab_name: Name for refresh interval lookup (robots, jobs, etc.)
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._tab_name = tab_name
        self._refresh_interval = REFRESH_INTERVALS.get(tab_name, 60000)

        # Setup timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._request_refresh)
        self._refresh_timer.start(self._refresh_interval)

        # Setup base UI
        self._setup_base_ui()

        # Apply styles
        self._apply_base_styles()

    def _setup_base_ui(self) -> None:
        """Set up base UI structure."""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(8, 8, 8, 8)
        self._main_layout.setSpacing(8)

        # Toolbar (to be populated by subclass)
        self._toolbar = QHBoxLayout()
        self._main_layout.addLayout(self._toolbar)

        # Content area (to be filled by subclass)
        self._setup_content()

        # Footer with status and refresh
        self._footer = QHBoxLayout()

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"color: {THEME.text_secondary};")
        self._footer.addWidget(self._status_label)

        self._footer.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._request_refresh)
        self._footer.addWidget(self._refresh_btn)

        self._main_layout.addLayout(self._footer)

    @abstractmethod
    def _setup_content(self) -> None:
        """
        Set up tab-specific content.

        Subclasses must implement this to add their specific UI elements.
        """
        pass

    def _apply_base_styles(self) -> None:
        """Apply base stylesheet."""
        self.setStyleSheet(TAB_WIDGET_BASE_STYLE)
        self._apply_additional_styles()

    def _apply_additional_styles(self) -> None:
        """
        Apply tab-specific styles.

        Subclasses can override to add additional styling.
        """
        pass

    def _request_refresh(self) -> None:
        """Request data refresh."""
        self.refresh_requested.emit()

    def set_refreshing(self, refreshing: bool) -> None:
        """
        Set refresh button state.

        Args:
            refreshing: True if refresh in progress
        """
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")

    def set_status(self, message: str) -> None:
        """
        Set status label message.

        Args:
            message: Status message to display
        """
        self._status_label.setText(message)

    def pause_auto_refresh(self) -> None:
        """Pause automatic refresh timer."""
        self._refresh_timer.stop()

    def resume_auto_refresh(self) -> None:
        """Resume automatic refresh timer."""
        self._refresh_timer.start(self._refresh_interval)

    def set_refresh_interval(self, interval_ms: int) -> None:
        """
        Set refresh interval.

        Args:
            interval_ms: Interval in milliseconds
        """
        self._refresh_interval = interval_ms
        if self._refresh_timer.isActive():
            self._refresh_timer.start(interval_ms)


__all__ = ["BaseTabWidget"]
