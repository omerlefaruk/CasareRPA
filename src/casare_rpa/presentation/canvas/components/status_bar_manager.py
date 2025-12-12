"""
Status bar manager for MainWindow.

Centralizes status bar creation, updates, and tab toggles.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QLabel, QPushButton, QStatusBar

from casare_rpa.presentation.canvas.ui.theme import Theme
from casare_rpa.presentation.canvas.ui.widgets.zoom_widget import ZoomWidget

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

    @staticmethod
    def _get_status_bar_style() -> str:
        """Generate theme-aware status bar stylesheet."""
        c = Theme.get_colors()
        return f"""
            QStatusBar {{
                background: {c.background_alt};
                color: {c.text_primary};
                border-top: 1px solid {c.border};
            }}
            QStatusBar::item {{
                border: none;
            }}
            QLabel {{
                color: {c.text_muted};
                padding: 0 8px;
            }}
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px 6px;
                color: {c.text_muted};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {c.surface};
                color: {c.text_primary};
            }}
            QPushButton:checked {{
                background: {c.selection};
                color: #ffffff;
            }}
        """

    @staticmethod
    def _get_status_colors() -> dict:
        """Get theme-aware status indicator colors."""
        c = Theme.get_colors()
        return {
            "ready": ("Ready", c.success),
            "running": ("Running", c.warning),
            "paused": ("Paused", c.info),
            "error": ("Error", c.error),
            "success": ("Complete", c.success),
        }

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize status bar manager.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

        # Status bar widgets
        self._zoom_widget: Optional[ZoomWidget] = None
        self._zoom_label: Optional[QLabel] = None  # Kept for backward compat
        self._node_count_label: Optional[QLabel] = None
        self._exec_status_label: Optional[QLabel] = None
        self._btn_variables: Optional[QPushButton] = None
        self._btn_output: Optional[QPushButton] = None
        self._btn_log: Optional[QPushButton] = None
        self._btn_validation: Optional[QPushButton] = None

    def create_status_bar(self) -> QStatusBar:
        """
        Create enhanced status bar with zoom, node count, and quick toggles.

        Returns:
            Created QStatusBar instance
        """
        mw = self._main_window
        status_bar = QStatusBar()
        mw.setStatusBar(status_bar)
        status_bar.setStyleSheet(self._get_status_bar_style())

        # Zoom widget with presets
        self._zoom_widget = ZoomWidget()
        self._zoom_widget.setToolTip("Zoom level - click for presets")
        self._zoom_widget.zoom_changed.connect(self._on_zoom_changed)
        self._zoom_widget.fit_to_window.connect(self._on_fit_to_window)
        self._zoom_widget.fit_to_selection.connect(self._on_fit_to_selection)
        self._zoom_widget.reset_zoom.connect(self._on_reset_zoom)
        status_bar.addPermanentWidget(self._zoom_widget)

        # Keep old label reference for backward compatibility
        self._zoom_label = QLabel("100%")
        self._zoom_label.hide()  # Hidden but available for legacy code

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
        c = Theme.get_colors()
        self._exec_status_label = QLabel("Ready")
        self._exec_status_label.setStyleSheet(f"color: {c.success};")
        self._exec_status_label.setToolTip("Workflow execution status")
        status_bar.addPermanentWidget(self._exec_status_label)

        status_bar.showMessage("Ready", 3000)

        # Store references on main window for compatibility
        mw._zoom_label = self._zoom_label
        mw._zoom_widget = self._zoom_widget
        mw._node_count_label = self._node_count_label
        mw._exec_status_label = self._exec_status_label
        mw._btn_variables = self._btn_variables
        mw._btn_output = self._btn_output
        mw._btn_log = self._btn_log
        mw._btn_validation = self._btn_validation

        return status_bar

    def _on_zoom_changed(self, zoom_factor: float) -> None:
        """Handle zoom change from widget."""
        mw = self._main_window
        if hasattr(mw, "_central_widget") and mw._central_widget:
            graph = getattr(mw._central_widget, "graph", None)
            if graph:
                try:
                    graph.set_zoom(zoom_factor)
                except Exception:
                    pass

    def _on_fit_to_window(self) -> None:
        """Handle fit to window request."""
        mw = self._main_window
        if hasattr(mw, "_central_widget") and mw._central_widget:
            graph = getattr(mw._central_widget, "graph", None)
            if graph and graph.all_nodes():
                try:
                    graph.fit_to_selection()
                    zoom = graph.get_zoom()
                    self._zoom_widget.set_zoom(zoom)
                except Exception:
                    pass

    def _on_fit_to_selection(self) -> None:
        """Handle fit to selection request."""
        mw = self._main_window
        if hasattr(mw, "_central_widget") and mw._central_widget:
            graph = getattr(mw._central_widget, "graph", None)
            if graph and graph.selected_nodes():
                try:
                    graph.fit_to_selection()
                    zoom = graph.get_zoom()
                    self._zoom_widget.set_zoom(zoom)
                except Exception:
                    pass

    def _on_reset_zoom(self) -> None:
        """Handle reset zoom to 100% request."""
        mw = self._main_window
        if hasattr(mw, "_central_widget") and mw._central_widget:
            graph = getattr(mw._central_widget, "graph", None)
            if graph:
                try:
                    graph.reset_zoom()
                    self._zoom_widget.set_zoom(1.0)
                except Exception:
                    pass

    def connect_to_graph(self, graph) -> None:
        """
        Connect zoom widget to a NodeGraph instance.

        Args:
            graph: NodeGraph instance
        """
        if self._zoom_widget:
            self._zoom_widget.set_graph(graph)

    def _add_separator(self, status_bar: QStatusBar) -> None:
        """Add a vertical separator to the status bar."""
        c = Theme.get_colors()
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {c.border_light};")
        status_bar.addPermanentWidget(sep)

    def _create_toggle_button(
        self, text: str, tooltip: str, tab_name: str
    ) -> QPushButton:
        """
        Create a toggle button for panel tabs.

        Args:
            text: Button text
            tooltip: Button tooltip
            tab_name: Tab name to toggle

        Returns:
            Created QPushButton
        """
        btn = QPushButton(text)
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
            zoom_percent: Current zoom percentage (e.g., 100 for 100%)
        """
        zoom_factor = zoom_percent / 100.0
        if self._zoom_widget:
            self._zoom_widget.set_zoom(zoom_factor)
        # Keep legacy label updated for backward compatibility
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

        c = Theme.get_colors()
        status_colors = self._get_status_colors()
        text, color = status_colors.get(status, ("Ready", c.success))
        self._exec_status_label.setText(text)
        self._exec_status_label.setStyleSheet(f"color: {color};")

    def update_button_states(self) -> None:
        """Update status bar button states based on panel visibility."""
        mw = self._main_window
        if mw._panel_controller:
            mw._panel_controller.update_status_bar_buttons()
