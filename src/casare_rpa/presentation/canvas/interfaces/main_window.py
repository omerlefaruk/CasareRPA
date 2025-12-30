"""Main window interface protocol (Epic 1.1).

This protocol defines the interface that MainWindow and NewMainWindow implement.
Controllers and other components depend on IMainWindow for loose coupling.
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from PySide6.QtCore import Signal

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from casare_rpa.presentation.canvas.controllers.ui_state_controller import (
        UIStateController,
    )


class IMainWindow(Protocol):
    """
    Protocol interface for MainWindow implementations.

    This protocol defines the contract that main window implementations
    must satisfy to work with controllers. Controllers use this interface
    instead of direct MainWindow dependency for loose coupling.

    Implementations:
        - MainWindow (main_window.py) - Legacy main window
        - NewMainWindow (new_main_window.py) - V2 dock-only workspace

    Note: This is a runtime-checkable Protocol, not an ABC.
    Implementations can provide additional methods beyond these.

    The protocol uses 'Any' for return types where the concrete types
    would create circular imports. Controllers access specific panel
    types via this interface without requiring the actual class imports.
    """

    # ==========================================================================
    # Signals (required attributes, not methods)
    # ==========================================================================

    # Workflow lifecycle signals
    workflow_new: Signal
    workflow_open: Signal  # str: file path
    workflow_save: Signal
    workflow_save_as: Signal  # str: file path
    workflow_import: Signal  # str: file path
    workflow_import_json: Signal  # str: file path
    workflow_export_selected: Signal  # str: file path

    # Execution control signals
    workflow_run: Signal
    workflow_run_all: Signal
    workflow_run_to_node: Signal  # str: node id
    workflow_run_single_node: Signal  # str: node id
    workflow_pause: Signal
    workflow_resume: Signal
    workflow_stop: Signal

    # Application signals
    preferences_saved: Signal
    trigger_workflow_requested: Signal

    # ==========================================================================
    # Graph Access
    # ==========================================================================

    def get_graph(self) -> Any:
        """
        Get the node graph widget.

        Returns:
            NodeGraphWidget or compatible graph instance.
        """

    def set_central_widget(self, widget: Any) -> None:
        """Set the node graph widget as central widget."""

    def get_current_file(self) -> Path | None:
        """
        Get the current workflow file path.

        Returns:
            Path to current workflow file, or None if no file loaded.
        """

    def set_current_file(self, file_path: Path | None) -> None:
        """
        Set the current workflow file path.

        Args:
            file_path: Path to workflow file, or None to clear.
        """

    def _get_workflow_data(self) -> dict | None:
        """
        Get workflow data as dict for serialization.

        Protected method accessed by controllers for workflow export
        and submission operations.

        Returns:
            Workflow dict with nodes, connections, and metadata.
        """

    def get_workflow_data(self) -> dict | None:
        """
        Get serialized workflow data for autosave.

        Returns:
            Workflow dict or None.
        """

    def set_modified(self, modified: bool) -> None:
        """
        Set the workflow modified state.

        Args:
            modified: True if workflow has unsaved changes.
        """

    def set_workflow_data_provider(self, provider: Callable) -> None:
        """
        Set the provider function for workflow data access.

        Args:
            provider: Callable that returns workflow dict.
        """

    # ==========================================================================
    # Status and Feedback
    # ==========================================================================

    def show_status(self, message: str, duration: int = 3000) -> None:
        """
        Show a status message in the status bar.

        Args:
            message: Status message to display.
            duration: Duration in milliseconds (0 for indefinite).
        """

    def set_execution_status(self, status: str) -> None:
        """
        Set the execution status display.

        Args:
            status: Status text to display.
        """

    def set_execution_state(
        self, is_running: bool, is_paused: bool = False
    ) -> None:
        """
        Update execution state (running/paused UI indicators).

        Args:
            is_running: True if workflow is executing.
            is_paused: True if execution is paused.
        """

    def set_browser_running(self, running: bool) -> None:
        """
        Update browser running state indicator.

        Args:
            running: True if browser automation is active.
        """

    def set_undo_enabled(self, enabled: bool) -> None:
        """Enable/disable undo action in UI."""

    def set_redo_enabled(self, enabled: bool) -> None:
        """Enable/disable redo action in UI."""

    def update_zoom(self, zoom_percent: float) -> None:
        """Update zoom display in status bar."""

    # ==========================================================================
    # Variables Access
    # ==========================================================================

    def get_variables(self) -> dict[str, Any]:
        """
        Get workflow variables from the variables panel.

        Returns:
            Dict mapping variable name to variable data.
        """

    def set_variables(self, variables: dict[str, Any]) -> None:
        """
        Set workflow variables in the variables panel.

        Args:
            variables: Dict of variables to set.
        """

    # ==========================================================================
    # Preferences Access
    # ==========================================================================

    def get_preferences(self) -> dict[str, Any]:
        """
        Get application preferences.

        Returns:
            Preferences dictionary.
        """

    # ==========================================================================
    # Panel Access
    # ==========================================================================

    def get_bottom_panel(self) -> "QWidget | None":
        """
        Get the bottom panel widget.

        Returns:
            Bottom panel containing logs, output, validation.
        """

    def get_side_panel(self) -> "QWidget | None":
        """
        Get the side panel widget.

        Returns:
            Left or right dock panel (project explorer/properties).
        """

    def get_log_viewer(self) -> Any:
        """
        Get the log viewer widget.

        Returns:
            Log viewer component for execution output.
        """

    def get_minimap(self) -> Any:
        """
        Get the minimap widget.

        Returns:
            Minimap component for graph navigation.
        """

    # ==========================================================================
    # Controller Access
    # ==========================================================================

    def get_project_controller(self) -> Any:
        """Get the project controller instance (may be None)."""

    def get_robot_controller(self) -> Any:
        """Get the robot controller instance (may be None)."""

    def get_node_controller(self) -> Any:
        """Get the node controller instance."""

    def get_viewport_controller(self) -> Any:
        """Get the viewport controller instance."""

    def get_ui_state_controller(self) -> "UIStateController | None":
        """Get the UI state controller instance."""

    def set_controllers(
        self,
        workflow_controller: Any,
        execution_controller: Any,
        node_controller: Any,
        selector_controller: Any | None = None,
    ) -> None:
        """
        Set controller instances for main window access.

        Args:
            workflow_controller: Workflow management controller.
            execution_controller: Execution management controller.
            node_controller: Node operations controller.
            selector_controller: Optional selector controller.
        """

    # ==========================================================================
    # Recent Files
    # ==========================================================================

    def add_to_recent_files(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to add to recent files.
        """

    # ==========================================================================
    # Validation
    # ==========================================================================

    def set_auto_validate(self, enabled: bool) -> None:
        """
        Enable/disable automatic workflow validation.

        Args:
            enabled: True to enable auto-validation.
        """

    def validate_current_workflow(
        self, show_panel: bool = True
    ) -> tuple[bool, list[str]]:
        """
        Validate the current workflow.

        Args:
            show_panel: If True, show validation panel.

        Returns:
            Tuple of (is_valid, error_messages).
        """

    # ==========================================================================
    # Panel Display Helpers
    # ==========================================================================

    def show_bottom_panel(self) -> None:
        """Show the bottom panel."""

    def show_side_panel(self) -> None:
        """Show the side panel."""

    def show_validation_panel(self) -> None:
        """Show the validation panel."""

    def show_log_viewer(self) -> None:
        """Show the log viewer panel."""

    def show_execution_history(self) -> None:
        """Show the execution history panel."""

    def show_debug_tab(self) -> None:
        """Show the debug tab in bottom panel."""

    def show_analytics_tab(self) -> None:
        """Show the analytics tab in bottom panel."""

    def show_minimap(self) -> None:
        """Show the graph minimap."""

    # ==========================================================================
    # Additional Getters (used by various controllers)
    # ==========================================================================

    def get_workflow_runner(self) -> Any:
        """Get the workflow runner instance."""

    def get_node_registry(self) -> dict:
        """Get the node registry."""

    def get_recent_files_menu(self) -> Any:
        """Get the recent files menu."""

    def get_ai_assistant_panel(self) -> Any:
        """Get the AI assistant panel."""

    def get_robot_picker_panel(self) -> Any:
        """Get the robot picker panel."""

    def get_process_mining_panel(self) -> Any:
        """Get the process mining panel."""

    def get_execution_history_viewer(self) -> Any:
        """Get the execution history viewer."""

    def get_quick_node_manager(self) -> Any:
        """Get the quick node manager."""

    # ==========================================================================
    # QMainWindow Methods (forwarded)
    # ==========================================================================

    def setWindowTitle(self, title: str) -> None:
        """Set the window title."""

    def centralWidget(self) -> "QWidget | None":
        """Get the central widget."""

    # ==========================================================================
    # Window State Persistence
    # ==========================================================================

    def saveGeometry(self) -> bytes:
        """Save window geometry."""

    def saveState(self) -> bytes:
        """Save window state."""

    def restoreGeometry(self, geometry: bytes) -> bool:
        """Restore window geometry."""

    def restoreState(self, state: bytes) -> bool:
        """Restore window state."""

    # ==========================================================================
    # Additional State Methods
    # ==========================================================================

    def is_modified(self) -> bool:
        """Check if the workflow has been modified."""

    def is_auto_connect_enabled(self) -> bool:
        """Check if auto-connect is enabled."""

    # ==========================================================================
    # Stub Action Properties
    # ==========================================================================
    # These are accessed by app.py for signal connections.
    # Using @property protocol for type checking without requiring actual properties.

    @property
    def action_undo(self) -> Any: ...

    @property
    def action_redo(self) -> Any: ...

    @property
    def action_delete(self) -> Any: ...

    @property
    def action_cut(self) -> Any: ...

    @property
    def action_copy(self) -> Any: ...

    @property
    def action_paste(self) -> Any: ...

    @property
    def action_duplicate(self) -> Any: ...

    @property
    def action_select_all(self) -> Any: ...

    @property
    def action_save(self) -> Any: ...

    @property
    def action_save_as(self) -> Any: ...

    @property
    def action_run(self) -> Any: ...

    @property
    def action_pause(self) -> Any: ...

    @property
    def action_stop(self) -> Any: ...
