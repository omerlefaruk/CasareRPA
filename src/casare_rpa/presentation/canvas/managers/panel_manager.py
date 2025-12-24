"""
Panel Manager for MainWindow.

Extracts panel visibility, docking, and layout management from MainWindow.
Provides a unified interface for panel operations.

Usage:
    manager = PanelManager(main_window)
    manager.show_bottom_panel()
    manager.toggle_panel_tab("validation")
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from ..ui.panels import BottomPanelDock, SidePanelDock


class PanelManager:
    """
    Manages panel visibility and layout for MainWindow.

    Responsibilities:
    - Show/hide bottom panel (Variables, Output, Log, Validation, etc.)
    - Show/hide side panel (Debug, Process Mining, Robot Picker, Analytics)
    - Toggle specific tabs within panels
    - Access panel contents for external use
    - Coordinate with PanelController for state management

    Panel Structure:
    - Bottom Panel: Tabbed dock with Variables, Output, Log, Validation, History
    - Side Panel: Tabbed dock with Debug, Process Mining, Robot Picker, Analytics
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the panel manager.

        Args:
            main_window: Reference to parent MainWindow
        """
        self._mw = main_window

    # ==================== Bottom Panel ====================

    @property
    def bottom_panel(self) -> Optional["BottomPanelDock"]:
        """Get the bottom panel dock."""
        return self._mw._bottom_panel

    def get_bottom_panel(self) -> Optional["BottomPanelDock"]:
        """Get the bottom panel dock (getter method)."""
        return self._mw._bottom_panel

    def show_bottom_panel(self) -> None:
        """Show the bottom panel."""
        if self._mw._panel_controller:
            self._mw._panel_controller.show_bottom_panel()
        elif self._mw._bottom_panel:
            self._mw._bottom_panel.show()
            self._update_toggle_action("action_toggle_panel", True)

    def hide_bottom_panel(self) -> None:
        """Hide the bottom panel."""
        if self._mw._panel_controller:
            self._mw._panel_controller.hide_bottom_panel()
        elif self._mw._bottom_panel:
            self._mw._bottom_panel.hide()
            self._update_toggle_action("action_toggle_panel", False)

    def toggle_bottom_panel(self, checked: bool) -> None:
        """Toggle bottom panel visibility."""
        if checked:
            self.show_bottom_panel()
        else:
            self.hide_bottom_panel()

    def toggle_panel_tab(self, tab_name: str) -> None:
        """
        Toggle bottom panel to specific tab.

        Args:
            tab_name: Name of tab to show (variables, output, log, validation, history)
        """
        if self._mw._panel_controller:
            self._mw._panel_controller.toggle_panel_tab(tab_name)
            self._mw._status_bar_manager.update_button_states()
        elif self._mw._bottom_panel:
            tab_method = f"show_{tab_name}_tab"
            if hasattr(self._mw._bottom_panel, tab_method):
                getattr(self._mw._bottom_panel, tab_method)()
                self._mw._bottom_panel.show()

    # ==================== Side Panel ====================

    @property
    def side_panel(self) -> Optional["SidePanelDock"]:
        """Get the side panel dock."""
        return self._mw._side_panel

    def get_side_panel(self) -> Optional["SidePanelDock"]:
        """Get the side panel dock (getter method)."""
        return self._mw._side_panel

    def show_side_panel(self) -> None:
        """Show the side panel."""
        if self._mw._side_panel:
            self._mw._side_panel.show()
            self._update_toggle_action("action_toggle_side_panel", True)

    def hide_side_panel(self) -> None:
        """Hide the side panel."""
        if self._mw._side_panel:
            self._mw._side_panel.hide()
            self._update_toggle_action("action_toggle_side_panel", False)

    def toggle_side_panel(self, checked: bool) -> None:
        """Toggle side panel visibility."""
        if checked:
            self.show_side_panel()
        else:
            self.hide_side_panel()

    def show_debug_tab(self) -> None:
        """Show the side panel with Debug tab active."""
        if self._mw._side_panel:
            self._mw._side_panel.show_debug_tab()
            self._update_toggle_action("action_toggle_side_panel", True)

    def show_analytics_tab(self) -> None:
        """Show the side panel with Analytics tab active."""
        if self._mw._side_panel:
            self._mw._side_panel.show_analytics_tab()
            self._update_toggle_action("action_toggle_side_panel", True)

    def show_process_mining_tab(self) -> None:
        """Show the side panel with Process Mining tab active."""
        if self._mw._side_panel:
            self._mw._side_panel.show_process_mining_tab()
            self._update_toggle_action("action_toggle_side_panel", True)

    def show_profiling_tab(self) -> None:
        """Show the side panel with Profiling tab active."""
        if self._mw._side_panel:
            self._mw._side_panel.show_profiling_tab()
            self._update_toggle_action("action_toggle_side_panel", True)

    def show_credentials_tab(self) -> None:
        """Show the side panel with Credentials tab active."""
        if self._mw._side_panel:
            self._mw._side_panel.show_credentials_tab()
            self._update_toggle_action("action_toggle_side_panel", True)

    def show_robot_picker_tab(self) -> None:
        """Show the side panel with Robot Picker tab active."""
        if self._mw._side_panel:
            self._mw._side_panel.show_robot_picker_tab()
            self._update_toggle_action("action_toggle_side_panel", True)

    # ==================== Specific Panel Access ====================

    @property
    def validation_panel(self):
        """Get the validation tab from bottom panel."""
        return self._mw._bottom_panel.get_validation_tab() if self._mw._bottom_panel else None

    def get_validation_panel(self):
        """Get the validation tab (getter method)."""
        return self.validation_panel

    def show_validation_panel(self) -> None:
        """Show the validation tab in bottom panel."""
        if self._mw._bottom_panel:
            self._mw._bottom_panel.show_validation_tab()

    def hide_validation_panel(self) -> None:
        """Hide the validation panel (hides bottom panel)."""
        if self._mw._bottom_panel:
            self._mw._bottom_panel.hide()

    @property
    def log_viewer(self):
        """Get the log viewer tab from bottom panel."""
        return self._mw._bottom_panel.get_log_tab() if self._mw._bottom_panel else None

    def get_log_viewer(self):
        """Get the log viewer tab (getter method)."""
        return self.log_viewer

    def show_log_viewer(self) -> None:
        """Show the log viewer tab in bottom panel."""
        if self._mw._bottom_panel:
            self._mw._bottom_panel.show_log_tab()

    def hide_log_viewer(self) -> None:
        """Hide the log viewer (hides bottom panel)."""
        if self._mw._bottom_panel:
            self._mw._bottom_panel.hide()

    def show_execution_history(self) -> None:
        """Show the execution history tab in bottom panel."""
        if self._mw._bottom_panel:
            self._mw._bottom_panel.show_history_tab()

    def get_execution_history_viewer(self):
        """Get the execution history tab from bottom panel."""
        return self._mw._bottom_panel.get_history_tab() if self._mw._bottom_panel else None

    # ==================== Debug Panel ====================

    @property
    def debug_panel(self):
        """Get the debug panel reference."""
        return self._mw._debug_panel

    def get_debug_panel(self):
        """Get the debug panel (getter method)."""
        return self._mw._debug_panel

    @property
    def process_mining_panel(self):
        """Get the process mining panel reference."""
        return self._mw._process_mining_panel

    def get_process_mining_panel(self):
        """Get the process mining panel (getter method)."""
        return self._mw._process_mining_panel

    @property
    def robot_picker_panel(self):
        """Get the robot picker panel reference."""
        return self._mw._robot_picker_panel

    def get_robot_picker_panel(self):
        """Get the robot picker panel (getter method)."""
        return self._mw._robot_picker_panel

    @property
    def analytics_panel(self):
        """Get the analytics panel reference."""
        return self._mw._analytics_panel

    def get_analytics_panel(self):
        """Get the analytics panel (getter method)."""
        return self._mw._analytics_panel

    @property
    def credentials_panel(self):
        """Get the credentials panel reference."""
        return self._mw._side_panel.get_credentials_tab() if self._mw._side_panel else None

    def get_credentials_panel(self):
        """Get the credentials panel (getter method)."""
        return self.credentials_panel

    # ==================== Status Bar Button States ====================

    def update_status_bar_buttons(self) -> None:
        """Update status bar button states based on panel visibility."""
        self._mw._status_bar_manager.update_button_states()

    # ==================== Helper Methods ====================

    def _update_toggle_action(self, action_name: str, checked: bool) -> None:
        """
        Update a toggle action's checked state.

        Args:
            action_name: Name of the action attribute on MainWindow
            checked: Whether the action should be checked
        """
        if hasattr(self._mw, action_name):
            action = getattr(self._mw, action_name)
            if action:
                action.setChecked(checked)

    def is_bottom_panel_visible(self) -> bool:
        """Check if bottom panel is visible."""
        return self._mw._bottom_panel is not None and self._mw._bottom_panel.isVisible()

    def is_side_panel_visible(self) -> bool:
        """Check if side panel is visible."""
        return self._mw._side_panel is not None and self._mw._side_panel.isVisible()

    def get_active_bottom_tab(self) -> str | None:
        """Get the name of the currently active bottom panel tab."""
        if self._mw._bottom_panel:
            return self._mw._bottom_panel.current_tab_name()
        return None

    def get_active_side_tab(self) -> str | None:
        """Get the name of the currently active side panel tab."""
        if self._mw._side_panel:
            return self._mw._side_panel.current_tab_name()
        return None
