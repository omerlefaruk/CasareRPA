"""
Workflow execution controller.

Handles all execution-related operations:
- Run/Pause/Resume/Stop
- Run to node (partial execution)
- Run single node (isolated execution)
- Debug mode controls
- EventBus integration for node visual feedback
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox
from loguru import logger

from .base_controller import BaseController

if TYPE_CHECKING:
    from ..main_window import MainWindow


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

    def __init__(self, main_window: "MainWindow"):
        """Initialize execution controller."""
        super().__init__(main_window)
        self._is_running = False
        self._is_paused = False
        self._use_case: Optional = None
        self._workflow_task: Optional[asyncio.Task] = None
        self._event_bus = None

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        # Setup EventBus integration for visual node feedback
        self._setup_event_bus()
        logger.info("ExecutionController initialized")

    def _setup_event_bus(self) -> None:
        """
        Setup EventBus integration for workflow execution events.

        Extracted from: canvas/components/execution_component.py
        Subscribes to domain events for visual node feedback.
        """
        try:
            from ....domain.events import EventType, get_event_bus

            self._event_bus = get_event_bus()

            # Subscribe to execution events for visual feedback
            self._event_bus.subscribe(EventType.NODE_STARTED, self._on_node_started)
            self._event_bus.subscribe(EventType.NODE_COMPLETED, self._on_node_completed)
            self._event_bus.subscribe(EventType.NODE_ERROR, self._on_node_error)
            self._event_bus.subscribe(
                EventType.WORKFLOW_COMPLETED, self._on_workflow_completed
            )
            self._event_bus.subscribe(EventType.WORKFLOW_ERROR, self._on_workflow_error)
            self._event_bus.subscribe(
                EventType.WORKFLOW_STOPPED, self._on_workflow_stopped
            )

            # Subscribe all events to log viewer if available
            log_viewer = self.main_window.get_log_viewer()
            if log_viewer and hasattr(log_viewer, "log_event"):
                for event_type in EventType:
                    self._event_bus.subscribe(event_type, log_viewer.log_event)

            logger.info("EventBus integration configured for execution feedback")
        except ImportError as e:
            logger.warning(f"EventBus not available: {e}")
            self._event_bus = None

    def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel running workflow task
        if self._workflow_task and not self._workflow_task.done():
            self._workflow_task.cancel()
            self._workflow_task = None
        self._use_case = None
        super().cleanup()
        logger.info("ExecutionController cleanup")

    def _on_node_started(self, event_data: dict) -> None:
        """
        Handle NODE_STARTED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'running'.
        """
        node_id = event_data.get("node_id")
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "set_property"):
                visual_node.set_property("status", "running")
                logger.debug(f"Node {node_id} visual status: running")

    def _on_node_completed(self, event_data: dict) -> None:
        """
        Handle NODE_COMPLETED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'completed'.
        """
        node_id = event_data.get("node_id")
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "set_property"):
                visual_node.set_property("status", "completed")
                logger.debug(f"Node {node_id} visual status: completed")

    def _on_node_error(self, event_data: dict) -> None:
        """
        Handle NODE_ERROR event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'error'.
        """
        node_id = event_data.get("node_id")
        error = event_data.get("error", "Unknown error")
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "set_property"):
                visual_node.set_property("status", "error")
                logger.error(f"Node {node_id} error: {error}")

    def _on_workflow_completed(self, event_data: dict) -> None:
        """
        Handle WORKFLOW_COMPLETED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        logger.info("Workflow execution completed (EventBus)")
        self.on_execution_completed()

    def _on_workflow_error(self, event_data: dict) -> None:
        """
        Handle WORKFLOW_ERROR event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        error = event_data.get("error", "Unknown error")
        logger.error(f"Workflow error (EventBus): {error}")
        self.on_execution_error(str(error))

    def _on_workflow_stopped(self, event_data: dict) -> None:
        """
        Handle WORKFLOW_STOPPED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        logger.info("Workflow stopped (EventBus)")
        self._is_running = False
        self._is_paused = False
        self._update_execution_actions(running=False)

    def _find_visual_node(self, node_id: str):
        """
        Find visual node by node_id in the graph.

        Args:
            node_id: Node ID to find

        Returns:
            Visual node or None
        """
        graph = self.main_window.get_graph()
        if not graph:
            return None

        for visual_node in graph.all_nodes():
            if visual_node.get_property("node_id") == node_id:
                return visual_node
        return None

    def _reset_all_node_visuals(self) -> None:
        """Reset all node visual states to idle."""
        graph = self.main_window.get_graph()
        if not graph:
            return

        for visual_node in graph.all_nodes():
            if hasattr(visual_node, "set_property"):
                visual_node.set_property("status", "idle")

    def run_workflow(self) -> None:
        """Run workflow from start to end (F3)."""
        logger.info("Running workflow")

        # Validate before running
        if not self._check_validation_before_run():
            return

        # Reset all node visuals before starting
        self._reset_all_node_visuals()

        self._is_running = True
        self._is_paused = False
        self.execution_started.emit()

        # Emit MainWindow signal for backward compatibility
        self.main_window.workflow_run.emit()

        # Update UI state
        self._update_execution_actions(running=True)

        self.main_window.show_status("Workflow execution started...", 0)

    def run_to_node(self) -> None:
        """Run workflow up to the selected node (F4)."""
        logger.info("Running to selected node")

        # Get selected node from graph
        graph = self.main_window.get_graph()
        if not graph:
            # Fallback to full run if no graph
            self.run_workflow()
            return

        selected_nodes = graph.selected_nodes()

        # If no node selected, fallback to full workflow run
        if not selected_nodes:
            self.main_window.show_status(
                "No node selected - running full workflow", 3000
            )
            self.run_workflow()
            return

        # Get first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            self.main_window.show_status(
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

        self.main_window.show_status(f"Running to node: {node_name}...", 0)

    def run_single_node(self) -> None:
        """Run only the selected node in isolation (F5)."""
        logger.info("Running single node")

        # Get selected node from graph
        graph = self.main_window.get_graph()
        if not graph:
            self.main_window.show_status("No graph available", 3000)
            return

        selected_nodes = graph.selected_nodes()

        # If no node selected, show message
        if not selected_nodes:
            self.main_window.show_status(
                "No node selected - select a node to run", 3000
            )
            return

        # Get first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            self.main_window.show_status("Selected node has no ID", 3000)
            return

        # Get node name for display
        node_name = (
            target_node.name() if hasattr(target_node, "name") else target_node_id
        )

        self.run_single_node_requested.emit(target_node_id)

        self.main_window.show_status(f"Running node: {node_name}...", 0)

    def pause_workflow(self) -> None:
        """Pause running workflow."""
        logger.info("Pausing workflow")

        if not self._is_running:
            logger.warning("Cannot pause - workflow not running")
            return

        self._is_paused = True
        self.execution_paused.emit()

        # Emit MainWindow signal for backward compatibility
        self.main_window.workflow_pause.emit()

        self.main_window.show_status("Workflow paused", 0)

    def resume_workflow(self) -> None:
        """Resume paused workflow."""
        logger.info("Resuming workflow")

        if not self._is_paused:
            logger.warning("Cannot resume - workflow not paused")
            return

        self._is_paused = False
        self.execution_resumed.emit()

        # Emit MainWindow signal for backward compatibility
        self.main_window.workflow_resume.emit()

        self.main_window.show_status("Workflow resumed...", 0)

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

        # Emit MainWindow signal for backward compatibility
        self.main_window.workflow_stop.emit()

        # Update UI state
        self._update_execution_actions(running=False)

        self.main_window.show_status("Workflow execution stopped", 3000)

    def on_execution_completed(self) -> None:
        """Handle workflow execution completion."""
        logger.info("Workflow execution completed")

        self._is_running = False
        self._is_paused = False
        self.execution_completed.emit()

        # Update UI state
        self._update_execution_actions(running=False)

        self.main_window.show_status("Workflow execution completed", 3000)

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

        self.main_window.show_status("Workflow execution failed", 3000)

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
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            validation_errors = bottom_panel.get_validation_errors_blocking()
            if validation_errors:
                QMessageBox.warning(
                    self.main_window,
                    "Validation Errors",
                    f"The workflow has {len(validation_errors)} validation error(s) "
                    "that must be fixed before running.\n\n"
                    "Please check the Validation tab for details.",
                )
                # Show validation tab
                bottom_panel.show_validation_tab()
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
