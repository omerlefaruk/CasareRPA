"""
Panel visibility and management controller.

Handles all panel-related operations:
- Bottom panel (Output, Log, Variables, Validation tabs)
- Execution timeline dock
- Minimap overlay
- Panel state persistence
"""

from typing import TYPE_CHECKING
from PySide6.QtCore import Signal
from loguru import logger

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class PanelController(BaseController):
    """
    Manages panel visibility and state.

    Single Responsibility: Panel lifecycle and visibility management.

    Signals:
        bottom_panel_toggled: Emitted when bottom panel visibility changes (bool: visible)
        minimap_toggled: Emitted when minimap visibility changes (bool: visible)
        panel_tab_changed: Emitted when active tab changes (str: tab_name)
    """

    # Signals
    bottom_panel_toggled = Signal(bool)  # visible
    minimap_toggled = Signal(bool)  # visible
    panel_tab_changed = Signal(str)  # tab_name

    def __init__(self, main_window: "MainWindow"):
        """Initialize panel controller."""
        super().__init__(main_window)

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("PanelController cleanup")

    def toggle_bottom_panel(self, visible: bool) -> None:
        """
        Toggle bottom panel visibility.

        Args:
            visible: True to show, False to hide
        """
        logger.debug(f"Toggling bottom panel: {visible}")

        dock = self.main_window.get_bottom_panel()
        if dock:
            dock.setVisible(visible)
            self.bottom_panel_toggled.emit(visible)

    def toggle_minimap(self, visible: bool) -> None:
        """
        Toggle minimap overlay visibility.

        Args:
            visible: True to show, False to hide
        """
        logger.debug(f"Toggling minimap: {visible}")

        minimap = self.main_window.get_minimap()
        if minimap:
            if visible:
                minimap.show()
            else:
                minimap.hide()
            self.minimap_toggled.emit(visible)

    def show_panel_tab(self, tab_name: str) -> None:
        """
        Switch to a specific tab in the bottom panel.

        Args:
            tab_name: Name of tab to show (e.g., "Output", "Log", "Variables", "Validation")
        """
        logger.debug(f"Showing panel tab: {tab_name}")

        panel = self.main_window.get_bottom_panel()
        if panel:
            # Make panel visible if hidden
            if not panel.isVisible():
                panel.setVisible(True)
                self.bottom_panel_toggled.emit(True)

            # Switch to requested tab
            if hasattr(panel, "show_output_tab") and tab_name == "Output":
                panel.show_output_tab()
            elif hasattr(panel, "show_log_tab") and tab_name == "Log":
                panel.show_log_tab()
            elif hasattr(panel, "show_variables_tab") and tab_name == "Variables":
                panel.show_variables_tab()
            elif hasattr(panel, "show_validation_tab") and tab_name == "Validation":
                panel.show_validation_tab()

            self.panel_tab_changed.emit(tab_name)

    def navigate_to_node(self, node_id: str) -> None:
        """
        Handle navigation to a node from a panel.

        Args:
            node_id: ID of node to navigate to
        """
        logger.debug(f"Panel navigation to node: {node_id}")

        # Get node controller from main window and delegate
        node_controller = self.main_window.get_node_controller()
        if node_controller:
            node_controller.navigate_to_node(node_id)

    def trigger_validation(self) -> None:
        """Trigger workflow validation and update validation panel."""
        logger.debug("Triggering workflow validation")

        panel = self.main_window.get_bottom_panel()
        if panel and hasattr(panel, "trigger_validation"):
            panel.trigger_validation()

    def get_validation_errors(self) -> list:
        """
        Get current validation errors.

        Returns:
            List of validation error messages
        """
        panel = self.main_window.get_bottom_panel()
        if panel and hasattr(panel, "get_validation_errors_blocking"):
            return panel.get_validation_errors_blocking()
        return []

    def show_validation_tab_if_errors(self) -> None:
        """Show validation tab if there are validation errors."""
        errors = self.get_validation_errors()
        if errors:
            self.show_panel_tab("Validation")
            logger.info(f"Showing validation tab: {len(errors)} errors found")

    def toggle_panel_tab(self, tab_name: str) -> None:
        """
        Toggle bottom panel to specific tab or hide if already on that tab.

        Args:
            tab_name: Tab name to toggle ('variables', 'output', 'log', 'validation', 'history')
        """
        panel = self.main_window.get_bottom_panel()
        if not panel:
            return

        tab_map = {
            "variables": 0,
            "output": 1,
            "log": 2,
            "validation": 3,
            "history": 4,
        }

        target_idx = tab_map.get(tab_name.lower(), 0)

        if panel.isVisible():
            # Switch to tab or hide if already on that tab
            if hasattr(panel, "_tab_widget"):
                current_idx = panel._tab_widget.currentIndex()
                if current_idx == target_idx:
                    panel.hide()
                    self.bottom_panel_toggled.emit(False)
                else:
                    panel._tab_widget.setCurrentIndex(target_idx)
                    self.panel_tab_changed.emit(tab_name)
        else:
            panel.show()
            if hasattr(panel, "_tab_widget"):
                panel._tab_widget.setCurrentIndex(target_idx)
            self.bottom_panel_toggled.emit(True)
            self.panel_tab_changed.emit(tab_name)

    def show_bottom_panel(self) -> None:
        """Show the bottom panel."""
        panel = self.main_window.get_bottom_panel()
        if panel:
            panel.show()
            self.bottom_panel_toggled.emit(True)

    def hide_bottom_panel(self) -> None:
        """Hide the bottom panel."""
        panel = self.main_window.get_bottom_panel()
        if panel:
            panel.hide()
            self.bottom_panel_toggled.emit(False)

    def show_minimap(self) -> None:
        """Show the minimap overlay."""
        minimap = self.main_window.get_minimap()
        if minimap:
            minimap.setVisible(True)
            self._position_minimap()
            self.minimap_toggled.emit(True)

    def hide_minimap(self) -> None:
        """Hide the minimap overlay."""
        minimap = self.main_window.get_minimap()
        if minimap:
            minimap.setVisible(False)
            self.minimap_toggled.emit(False)

    def _position_minimap(self) -> None:
        """Position minimap at bottom-left of central widget."""
        minimap = self.main_window.get_minimap()
        central_widget = getattr(self.main_window, "_central_widget", None)
        if minimap and central_widget:
            margin = 10
            x = margin
            y = central_widget.height() - minimap.height() - margin
            minimap.move(x, y)
            minimap.raise_()

    def update_status_bar_buttons(self) -> None:
        """Update status bar button states based on current panel visibility and tab."""
        panel = self.main_window.get_bottom_panel()
        if not panel:
            return

        visible = panel.isVisible()
        current_idx = -1
        if visible and hasattr(panel, "_tab_widget"):
            current_idx = panel._tab_widget.currentIndex()

        # Update button states if they exist
        if hasattr(self.main_window, "_btn_variables"):
            self.main_window._btn_variables.setChecked(visible and current_idx == 0)
        if hasattr(self.main_window, "_btn_output"):
            self.main_window._btn_output.setChecked(visible and current_idx == 1)
        if hasattr(self.main_window, "_btn_log"):
            self.main_window._btn_log.setChecked(visible and current_idx == 2)
        if hasattr(self.main_window, "_btn_validation"):
            self.main_window._btn_validation.setChecked(visible and current_idx == 3)
