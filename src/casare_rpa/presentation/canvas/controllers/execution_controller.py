"""
Workflow execution controller.

Handles all execution-related operations:
- Run/Pause/Resume/Stop
- Run to node (partial execution)
- Run single node (isolated execution)
- Debug mode controls
"""

from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox
from loguru import logger

from .base_controller import BaseController


class ExecutionController(BaseController):
    """
    Manages workflow execution lifecycle.

    Single Responsibility: Execution control and state management.

    Signals:
        execution_started: Emitted when workflow execution starts
        execution_paused: Emitted when workflow execution is paused
        execution_resumed: Emitted when workflow execution is resumed
        execution_stopped: Emitted when workflow execution is stopped
        execution_completed: Emitted when workflow execution completes
        execution_error: Emitted when workflow execution fails (str: error)
        run_to_node_requested: Emitted when user wants to run to a specific node (str: node_id)
        run_single_node_requested: Emitted when user wants to run only one node (str: node_id)
    """

    # Signals
    execution_started = Signal()
    execution_paused = Signal()
    execution_resumed = Signal()
    execution_stopped = Signal()
    execution_completed = Signal()
    execution_error = Signal(str)
    run_to_node_requested = Signal(str)  # node_id
    run_single_node_requested = Signal(str)  # node_id

    def __init__(self, main_window):
        """Initialize execution controller."""
        super().__init__(main_window)
        self._is_running = False
        self._is_paused = False

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        logger.info("ExecutionController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("ExecutionController cleanup")

    def run_workflow(self) -> None:
        """Run workflow from start to end (F3)."""
        logger.info("Running workflow")

        # Validate before running
        if not self._check_validation_before_run():
            return

        self._is_running = True
        self._is_paused = False
        self.execution_started.emit()

        # Update UI state
        self._update_execution_actions(running=True)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                "Workflow execution started...", 0
            )

    def run_to_node(self) -> None:
        """Run workflow up to the selected node (F4)."""
        logger.info("Running to selected node")

        # Get selected node from graph
        central_widget = self.main_window._central_widget
        if not central_widget or not hasattr(central_widget, "graph"):
            # Fallback to full run if no graph
            self.run_workflow()
            return

        graph = central_widget.graph
        selected_nodes = graph.selected_nodes()

        # If no node selected, fallback to full workflow run
        if not selected_nodes:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    "No node selected - running full workflow", 3000
                )
            self.run_workflow()
            return

        # Get first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    "Selected node has no ID - running full workflow", 3000
                )
            self.run_workflow()
            return

        # Validate before running
        if not self._check_validation_before_run():
            return

        # Get node name for display
        node_name = (
            target_node.name() if hasattr(target_node, "name") else target_node_id
        )

        self._is_running = True
        self._is_paused = False
        self.run_to_node_requested.emit(target_node_id)

        # Update UI state
        self._update_execution_actions(running=True)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                f"Running to node: {node_name}...", 0
            )

    def run_single_node(self) -> None:
        """Run only the selected node in isolation (F5)."""
        logger.info("Running single node")

        # Get selected node from graph
        central_widget = self.main_window._central_widget
        if not central_widget or not hasattr(central_widget, "graph"):
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage("No graph available", 3000)
            return

        graph = central_widget.graph
        selected_nodes = graph.selected_nodes()

        # If no node selected, show message
        if not selected_nodes:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    "No node selected - select a node to run", 3000
                )
            return

        # Get first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    "Selected node has no ID", 3000
                )
            return

        # Get node name for display
        node_name = (
            target_node.name() if hasattr(target_node, "name") else target_node_id
        )

        self.run_single_node_requested.emit(target_node_id)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(f"Running node: {node_name}...", 0)

    def pause_workflow(self) -> None:
        """Pause running workflow."""
        logger.info("Pausing workflow")

        if not self._is_running:
            logger.warning("Cannot pause - workflow not running")
            return

        self._is_paused = True
        self.execution_paused.emit()

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage("Workflow paused", 0)

    def resume_workflow(self) -> None:
        """Resume paused workflow."""
        logger.info("Resuming workflow")

        if not self._is_paused:
            logger.warning("Cannot resume - workflow not paused")
            return

        self._is_paused = False
        self.execution_resumed.emit()

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage("Workflow resumed...", 0)

    def toggle_pause(self, checked: bool) -> None:
        """
        Toggle pause/resume state.

        Args:
            checked: True to pause, False to resume
        """
        if checked:
            self.pause_workflow()
        else:
            self.resume_workflow()

    def stop_workflow(self) -> None:
        """Stop running workflow."""
        logger.info("Stopping workflow")

        if not self._is_running:
            logger.warning("Cannot stop - workflow not running")
            return

        self._is_running = False
        self._is_paused = False
        self.execution_stopped.emit()

        # Update UI state
        self._update_execution_actions(running=False)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                "Workflow execution stopped", 3000
            )

    def on_execution_completed(self) -> None:
        """Handle workflow execution completion."""
        logger.info("Workflow execution completed")

        self._is_running = False
        self._is_paused = False
        self.execution_completed.emit()

        # Update UI state
        self._update_execution_actions(running=False)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                "Workflow execution completed", 3000
            )

    def on_execution_error(self, error_message: str) -> None:
        """
        Handle workflow execution error.

        Args:
            error_message: Error description
        """
        logger.error(f"Workflow execution error: {error_message}")

        self._is_running = False
        self._is_paused = False
        self.execution_error.emit(error_message)

        # Update UI state
        self._update_execution_actions(running=False)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                "Workflow execution failed", 3000
            )

    @property
    def is_running(self) -> bool:
        """Check if workflow is currently executing."""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """Check if workflow is currently paused."""
        return self._is_paused

    def _check_validation_before_run(self) -> bool:
        """
        Check validation before running workflow.

        Returns:
            True if safe to run, False if validation errors block execution
        """
        # Get validation errors from bottom panel if available
        if (
            hasattr(self.main_window, "_bottom_panel")
            and self.main_window._bottom_panel
        ):
            validation_errors = (
                self.main_window._bottom_panel.get_validation_errors_blocking()
            )
            if validation_errors:
                QMessageBox.warning(
                    self.main_window,
                    "Validation Errors",
                    f"The workflow has {len(validation_errors)} validation error(s) "
                    "that must be fixed before running.\n\n"
                    "Please check the Validation tab for details.",
                )
                # Show validation tab
                self.main_window._bottom_panel.show_validation_tab()
                return False

        return True

    def _update_execution_actions(self, running: bool) -> None:
        """
        Update execution-related actions based on running state.

        Args:
            running: True if workflow is running, False otherwise
        """
        if not hasattr(self.main_window, "action_run"):
            return

        # When running: disable run actions, enable pause/stop
        # When stopped: enable run actions, disable pause/stop
        self.main_window.action_run.setEnabled(not running)
        self.main_window.action_run_to_node.setEnabled(not running)
        self.main_window.action_pause.setEnabled(running)
        self.main_window.action_stop.setEnabled(running)

        if not running:
            # Reset pause button state
            self.main_window.action_pause.setChecked(False)
