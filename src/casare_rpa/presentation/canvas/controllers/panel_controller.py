"""
Panel visibility and management controller.

Handles all panel-related operations:
- Bottom panel (Output, Log, Variables, Validation tabs)
- Properties panel (right dock)
- Variable inspector dock
- Execution timeline dock
- Minimap overlay
- Panel state persistence
"""

from typing import Optional
from PySide6.QtCore import Signal
from loguru import logger

from .base_controller import BaseController


class PanelController(BaseController):
    """
    Manages panel visibility and state.

    Single Responsibility: Panel lifecycle and visibility management.

    Signals:
        bottom_panel_toggled: Emitted when bottom panel visibility changes (bool: visible)
        properties_panel_toggled: Emitted when properties panel visibility changes (bool: visible)
        variable_inspector_toggled: Emitted when variable inspector visibility changes (bool: visible)
        minimap_toggled: Emitted when minimap visibility changes (bool: visible)
        panel_tab_changed: Emitted when active tab changes (str: tab_name)
    """

    # Signals
    bottom_panel_toggled = Signal(bool)  # visible
    properties_panel_toggled = Signal(bool)  # visible
    variable_inspector_toggled = Signal(bool)  # visible
    minimap_toggled = Signal(bool)  # visible
    panel_tab_changed = Signal(str)  # tab_name

    def __init__(self, main_window):
        """Initialize panel controller."""
        super().__init__(main_window)

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        logger.info("PanelController initialized")

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

        if hasattr(self.main_window, "_bottom_panel") and self.main_window._bottom_panel:
            dock = self.main_window._bottom_panel
            dock.setVisible(visible)
            self.bottom_panel_toggled.emit(visible)

    def toggle_properties_panel(self, visible: bool) -> None:
        """
        Toggle properties panel visibility.

        Args:
            visible: True to show, False to hide
        """
        logger.debug(f"Toggling properties panel: {visible}")

        if (
            hasattr(self.main_window, "_properties_panel")
            and self.main_window._properties_panel
        ):
            dock = self.main_window._properties_panel
            dock.setVisible(visible)
            self.properties_panel_toggled.emit(visible)

    def toggle_variable_inspector(self, visible: bool) -> None:
        """
        Toggle variable inspector visibility.

        Args:
            visible: True to show, False to hide
        """
        logger.debug(f"Toggling variable inspector: {visible}")

        if (
            hasattr(self.main_window, "_variable_inspector_dock")
            and self.main_window._variable_inspector_dock
        ):
            dock = self.main_window._variable_inspector_dock
            dock.setVisible(visible)
            self.variable_inspector_toggled.emit(visible)

    def toggle_minimap(self, visible: bool) -> None:
        """
        Toggle minimap overlay visibility.

        Args:
            visible: True to show, False to hide
        """
        logger.debug(f"Toggling minimap: {visible}")

        if hasattr(self.main_window, "_minimap") and self.main_window._minimap:
            minimap = self.main_window._minimap
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

        if hasattr(self.main_window, "_bottom_panel") and self.main_window._bottom_panel:
            panel = self.main_window._bottom_panel

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
        if hasattr(self.main_window, "_node_controller"):
            self.main_window._node_controller.navigate_to_node(node_id)

    def update_variables_panel(self, variables: dict) -> None:
        """
        Update the variables panel with new values.

        Args:
            variables: Dictionary of variable name -> value
        """
        logger.debug(f"Updating variables panel: {len(variables)} variables")

        if (
            hasattr(self.main_window, "_variable_inspector_dock")
            and self.main_window._variable_inspector_dock
        ):
            inspector = self.main_window._variable_inspector_dock
            if hasattr(inspector, "update_variables"):
                inspector.update_variables(variables)

    def trigger_validation(self) -> None:
        """Trigger workflow validation and update validation panel."""
        logger.debug("Triggering workflow validation")

        if hasattr(self.main_window, "_bottom_panel") and self.main_window._bottom_panel:
            panel = self.main_window._bottom_panel
            if hasattr(panel, "trigger_validation"):
                panel.trigger_validation()

    def get_validation_errors(self) -> list:
        """
        Get current validation errors.

        Returns:
            List of validation error messages
        """
        if hasattr(self.main_window, "_bottom_panel") and self.main_window._bottom_panel:
            panel = self.main_window._bottom_panel
            if hasattr(panel, "get_validation_errors_blocking"):
                return panel.get_validation_errors_blocking()
        return []

    def show_validation_tab_if_errors(self) -> None:
        """Show validation tab if there are validation errors."""
        errors = self.get_validation_errors()
        if errors:
            self.show_panel_tab("Validation")
            logger.info(f"Showing validation tab: {len(errors)} errors found")
