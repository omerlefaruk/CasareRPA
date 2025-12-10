"""
Status bar manager for MainWindow.

Centralizes status bar creation, updates, and tab toggles.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QStatusBar, QLabel

from casare_rpa.presentation.canvas.ui.widgets import AnimatedButton

if TYPE_CHECKING:
    from ..main_window import MainWindow


class StatusBarManager:
    """
    Manages the status bar for MainWindow.

    Responsibilities:
    - Create enhanced status bar with zoom, node count, toggles
    - Handle tab toggle buttons (Vars, Out, Log, Valid)
    - Update execution status indicator
    """

    # Status bar stylesheet
    STATUS_BAR_STYLE = """
        QStatusBar {
            background: #2b2b2b;
            color: #e0e0e0;
            border-top: 1px solid #3d3d3d;
        }
        QStatusBar::item {
            border: none;
        }
        QLabel {
            color: #a0a0a0;
            padding: 0 8px;
        }
        QPushButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 2px 6px;
            color: #a0a0a0;
            font-size: 11px;
        }
        QPushButton:hover {
            background: #3d3d3d;
            color: #e0e0e0;
        }
        QPushButton:checked {
            background: #4a6a8a;
            color: #ffffff;
        }
    """

    # Status indicator colors
    STATUS_COLORS = {
        "ready": ("Ready", "#4CAF50"),  # Green
        "running": ("Running", "#FFA500"),  # Orange
        "paused": ("Paused", "#2196F3"),  # Blue
        "error": ("Error", "#f44336"),  # Red
        "success": ("Complete", "#4CAF50"),  # Green
    }

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize status bar manager.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

        # Status bar widgets
        self._zoom_label: Optional[QLabel] = None
        self._node_count_label: Optional[QLabel] = None
        self._exec_status_label: Optional[QLabel] = None
        self._btn_variables: Optional[AnimatedButton] = None
        self._btn_output: Optional[AnimatedButton] = None
        self._btn_log: Optional[AnimatedButton] = None
        self._btn_validation: Optional[AnimatedButton] = None

    def create_status_bar(self) -> QStatusBar:
        """
        Create enhanced status bar with zoom, node count, and quick toggles.

        Returns:
            Created QStatusBar instance
        """
        mw = self._main_window
        status_bar = QStatusBar()
        mw.setStatusBar(status_bar)
        status_bar.setStyleSheet(self.STATUS_BAR_STYLE)

        # Zoom indicator
        self._zoom_label = QLabel("100%")
        self._zoom_label.setToolTip("Current zoom level")
        status_bar.addPermanentWidget(self._zoom_label)

        self._add_separator(status_bar)

        # Node count
        self._node_count_label = QLabel("Nodes: 0")
        self._node_count_label.setToolTip("Number of nodes in workflow")
        status_bar.addPermanentWidget(self._node_count_label)

        self._add_separator(status_bar)

        # Quick tab toggles
        self._btn_variables = self._create_toggle_button(
            "Vars", "Toggle Variables tab", "variables"
        )
        status_bar.addPermanentWidget(self._btn_variables)

        self._btn_output = self._create_toggle_button(
            "Out", "Toggle Output tab", "output"
        )
        status_bar.addPermanentWidget(self._btn_output)

        self._btn_log = self._create_toggle_button("Log", "Toggle Log tab", "log")
        status_bar.addPermanentWidget(self._btn_log)

        self._btn_validation = self._create_toggle_button(
            "Valid", "Toggle Validation tab", "validation"
        )
        status_bar.addPermanentWidget(self._btn_validation)

        self._add_separator(status_bar)

        # Execution status indicator
        self._exec_status_label = QLabel("Ready")
        self._exec_status_label.setStyleSheet("color: #4CAF50;")
        self._exec_status_label.setToolTip("Workflow execution status")
        status_bar.addPermanentWidget(self._exec_status_label)

        status_bar.showMessage("Ready", 3000)

        # Store references on main window for compatibility
        mw._zoom_label = self._zoom_label
        mw._node_count_label = self._node_count_label
        mw._exec_status_label = self._exec_status_label
        mw._btn_variables = self._btn_variables
        mw._btn_output = self._btn_output
        mw._btn_log = self._btn_log
        mw._btn_validation = self._btn_validation

        return status_bar

    def _add_separator(self, status_bar: QStatusBar) -> None:
        """Add a vertical separator to the status bar."""
        sep = QLabel("|")
        sep.setStyleSheet("color: #4a4a4a;")
        status_bar.addPermanentWidget(sep)

    def _create_toggle_button(
        self, text: str, tooltip: str, tab_name: str
    ) -> AnimatedButton:
        """
        Create a toggle button for panel tabs.

        Args:
            text: Button text
            tooltip: Button tooltip
            tab_name: Tab name to toggle

        Returns:
            Created AnimatedButton
        """
        btn = AnimatedButton(text)
        btn.setCheckable(True)
        btn.setToolTip(tooltip)
        btn.clicked.connect(lambda: self._toggle_panel_tab(tab_name))
        return btn

    def _toggle_panel_tab(self, tab_name: str) -> None:
        """Toggle bottom panel to specific tab."""
        mw = self._main_window
        if mw._panel_controller:
            mw._panel_controller.toggle_panel_tab(tab_name)
            self.update_button_states()

    def update_zoom_display(self, zoom_percent: float) -> None:
        """
        Update the zoom level display.

        Args:
            zoom_percent: Current zoom percentage
        """
        if self._zoom_label:
            self._zoom_label.setText(f"{int(zoom_percent)}%")

    def update_node_count(self, count: int) -> None:
        """
        Update the node count display.

        Args:
            count: Number of nodes
        """
        if self._node_count_label:
            self._node_count_label.setText(f"Nodes: {count}")

    def set_execution_status(self, status: str) -> None:
        """
        Update execution status indicator.

        Args:
            status: One of 'ready', 'running', 'paused', 'error', 'success'
        """
        if not self._exec_status_label:
            return

        text, color = self.STATUS_COLORS.get(status, ("Ready", "#4CAF50"))
        self._exec_status_label.setText(text)
        self._exec_status_label.setStyleSheet(f"color: {color};")

    def update_button_states(self) -> None:
        """Update status bar button states based on panel visibility."""
        mw = self._main_window
        if mw._panel_controller:
            mw._panel_controller.update_status_bar_buttons()
