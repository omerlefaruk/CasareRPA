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
from casare_rpa.application.services import ExecutionLifecycleManager

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
    # Trigger listening signals
    trigger_listening_started = Signal()
    trigger_listening_stopped = Signal()
    trigger_fired = Signal(int)  # run count

    def __init__(self, main_window: "MainWindow"):
        """Initialize execution controller."""
        super().__init__(main_window)
        self._is_running = False
        self._is_paused = False
        self._is_listening = False
        self._use_case: Optional = None
        self._workflow_task: Optional[asyncio.Task] = None
        self._event_bus = None
        self._workflow_runner: Optional["CanvasWorkflowRunner"] = None
        self._node_index: dict[str, object] = {}  # O(1) node lookup by node_id

        # Execution lifecycle manager for state machine and cleanup
        self._lifecycle_manager = ExecutionLifecycleManager()
        logger.debug("ExecutionLifecycleManager initialized")

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

    def set_workflow_runner(self, runner: "CanvasWorkflowRunner") -> None:
        """
        Set the workflow runner instance.

        Called by CasareRPAApp after initialization.

        Args:
            runner: CanvasWorkflowRunner instance
        """
        self._workflow_runner = runner
        logger.debug("Workflow runner configured in ExecutionController")

    def cleanup(self) -> None:
        """
        Clean up resources.

        Note: BaseController.cleanup() is synchronous by design (called during Qt
        widget destruction). We cannot await task cancellation here. The task's
        CancelledError will be handled in _run_workflow_async() which logs and
        exits gracefully. For truly clean shutdown, call cleanup_async() if an
        event loop is available.
        """
        # Request cancellation of running workflow task
        if self._workflow_task and not self._workflow_task.done():
            self._workflow_task.cancel()
            # Task cancellation is asynchronous - the task will handle CancelledError
            # in _run_workflow_async() and clean up properly
            logger.debug("Workflow task cancellation requested")
            self._workflow_task = None
        self._use_case = None
        self._node_index.clear()  # Clear node index
        super().cleanup()
        logger.info("ExecutionController cleanup")

    async def cleanup_async(self) -> None:
        """
        Async cleanup that properly awaits task cancellation.

        Use this method when an event loop is available for proper async cleanup.
        Falls back to sync cleanup for non-async resources.
        """
        if self._workflow_task and not self._workflow_task.done():
            self._workflow_task.cancel()
            try:
                await self._workflow_task
            except asyncio.CancelledError:
                logger.debug("Workflow task cancelled successfully")
            self._workflow_task = None
        self._use_case = None
        self._node_index.clear()
        # Call sync cleanup for base class and remaining resources
        super().cleanup()
        logger.info("ExecutionController async cleanup completed")

    def _on_node_started(self, event) -> None:
        """
        Handle NODE_STARTED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'running'.
        """
        # Extract data from Event object
        event_data = event.data if hasattr(event, "data") else event
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("running")
                logger.debug(f"Node {node_id} visual status: running")

    def _on_node_completed(self, event) -> None:
        """
        Handle NODE_COMPLETED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'success' (shows green checkmark).
        """
        # Extract data from Event object
        event_data = event.data if hasattr(event, "data") else event
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("success")
                # Update execution time if available
                duration_ms = (
                    event_data.get("duration_ms")
                    if isinstance(event_data, dict)
                    else None
                )
                if duration_ms is not None and hasattr(
                    visual_node, "update_execution_time"
                ):
                    visual_node.update_execution_time(duration_ms / 1000.0)
                logger.debug(f"Node {node_id} visual status: success")

    def _on_node_error(self, event) -> None:
        """
        Handle NODE_ERROR event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'error' (shows red X icon).
        """
        # Extract data from Event object
        event_data = event.data if hasattr(event, "data") else event
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None
        error = (
            event_data.get("error", "Unknown error")
            if isinstance(event_data, dict)
            else "Unknown error"
        )
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("error")
                logger.error(f"Node {node_id} error: {error}")

    def _on_workflow_completed(self, event) -> None:
        """
        Handle WORKFLOW_COMPLETED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        logger.info("Workflow execution completed (EventBus)")
        self.on_execution_completed()

    def _on_workflow_error(self, event) -> None:
        """
        Handle WORKFLOW_ERROR event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        # Extract data from Event object
        event_data = event.data if hasattr(event, "data") else event
        error = (
            event_data.get("error", "Unknown error")
            if isinstance(event_data, dict)
            else "Unknown error"
        )
        logger.error(f"Workflow error (EventBus): {error}")
        self.on_execution_error(str(error))

    def _on_workflow_stopped(self, event) -> None:
        """
        Handle WORKFLOW_STOPPED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        logger.info("Workflow stopped (EventBus)")
        self._is_running = False
        self._is_paused = False
        self._update_execution_actions(running=False)

    def _build_node_index(self) -> None:
        """
        Build node index dictionary for O(1) lookups during execution.

        Must be called before workflow execution starts to ensure
        the index is current with the graph state.
        """
        graph = self.main_window.get_graph()
        if not graph:
            self._node_index = {}
            return

        self._node_index = {
            node.get_property("node_id"): node
            for node in graph.all_nodes()
            if node.get_property("node_id")
        }
        logger.debug(f"Built node index with {len(self._node_index)} entries")

    def _find_visual_node(self, node_id: str):
        """
        Find visual node by node_id using index for O(1) lookup.

        Args:
            node_id: Node ID to find

        Returns:
            Visual node or None
        """
        return self._node_index.get(node_id)

    def _reset_all_node_visuals(self) -> None:
        """Reset all node visual states to idle (clears animations and status icons)."""
        graph = self.main_window.get_graph()
        if not graph:
            return

        for visual_node in graph.all_nodes():
            if hasattr(visual_node, "update_status"):
                visual_node.update_status("idle")
            # Also clear execution time
            if hasattr(visual_node, "update_execution_time"):
                visual_node.update_execution_time(None)

    def run_workflow(self) -> None:
        """Run workflow from start to end (F3)."""
        logger.info("Running workflow")

        # Atomic check-and-set to prevent race condition on rapid F3 presses
        if self._is_running:
            logger.warning("Workflow already running")
            self.main_window.show_status("Workflow is already running", 3000)
            return

        # Set flag immediately to block concurrent calls
        self._is_running = True

        try:
            # Validate before running
            if not self._check_validation_before_run():
                self._is_running = False
                return

            # Check if runner is configured
            if not self._workflow_runner:
                logger.error("WorkflowRunner not configured")
                QMessageBox.critical(
                    self.main_window,
                    "Execution Error",
                    "Workflow runner not initialized. Please restart the application.",
                )
                self._is_running = False
                return

            # Reset all node visuals before starting
            self._reset_all_node_visuals()

            # Build node index for O(1) lookups during execution events
            self._build_node_index()

            self._is_paused = False
            self.execution_started.emit()

            # Emit MainWindow signal for backward compatibility
            self.main_window.workflow_run.emit()

            # Update UI state
            self._update_execution_actions(running=True)

            self.main_window.show_status("Workflow execution started...", 0)

            # Create async task using lifecycle manager for proper cleanup
            self._workflow_task = asyncio.create_task(
                self._lifecycle_manager.start_workflow(
                    self._workflow_runner,
                    force_cleanup=True,  # Always cleanup before new run
                )
            )

        except Exception as e:
            # Ensure flag is reset on any unexpected error during setup
            logger.exception("Unexpected error during workflow startup")
            self._is_running = False
            self._update_execution_actions(running=False)
            raise

    async def _run_workflow_async(self) -> None:
        """Execute workflow asynchronously."""
        try:
            success = await self._workflow_runner.run_workflow()
            # Note: completion is handled via EventBus events
            # (WORKFLOW_COMPLETED or WORKFLOW_ERROR events trigger
            #  on_execution_completed or on_execution_error)
            logger.debug(f"Workflow execution completed: success={success}")
        except asyncio.CancelledError:
            logger.info("Workflow execution was cancelled")
        except Exception as e:
            logger.exception("Unexpected error during workflow execution")
            self.on_execution_error(str(e))

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

        # Atomic check-and-set to prevent race condition
        if self._is_running:
            logger.warning("Workflow already running")
            self.main_window.show_status("Workflow is already running", 3000)
            return

        # Set flag immediately to block concurrent calls
        self._is_running = True

        try:
            # Validate before running
            if not self._check_validation_before_run():
                self._is_running = False
                return

            # Check if runner is configured
            if not self._workflow_runner:
                logger.error("WorkflowRunner not configured")
                QMessageBox.critical(
                    self.main_window,
                    "Execution Error",
                    "Workflow runner not initialized. Please restart the application.",
                )
                self._is_running = False
                return

            # Get node name for display
            node_name = (
                target_node.name() if hasattr(target_node, "name") else target_node_id
            )

            # Reset all node visuals before starting
            self._reset_all_node_visuals()

            # Build node index for O(1) lookups during execution events
            self._build_node_index()

            self._is_paused = False
            self.run_to_node_requested.emit(target_node_id)
            self.execution_started.emit()

            # Update UI state
            self._update_execution_actions(running=True)

            self.main_window.show_status(f"Running to node: {node_name}...", 0)

            # Create async task using lifecycle manager with target_node_id
            self._workflow_task = asyncio.create_task(
                self._lifecycle_manager.start_workflow(
                    self._workflow_runner,
                    force_cleanup=True,
                    target_node_id=target_node_id,
                    single_node=False,
                )
            )

        except Exception as e:
            # Ensure flag is reset on any unexpected error during setup
            logger.exception("Unexpected error during run_to_node startup")
            self._is_running = False
            self._update_execution_actions(running=False)
            raise

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

        # Atomic check-and-set to prevent race condition
        if self._is_running:
            logger.warning("Workflow already running")
            self.main_window.show_status("Workflow is already running", 3000)
            return

        # Set flag immediately to block concurrent calls
        self._is_running = True

        try:
            # Check if runner is configured
            if not self._workflow_runner:
                logger.error("WorkflowRunner not configured")
                QMessageBox.critical(
                    self.main_window,
                    "Execution Error",
                    "Workflow runner not initialized. Please restart the application.",
                )
                self._is_running = False
                return

            # Get node name for display
            node_name = (
                target_node.name() if hasattr(target_node, "name") else target_node_id
            )

            # Reset only target node visual before starting
            if hasattr(target_node, "update_status"):
                target_node.update_status("idle")
            if hasattr(target_node, "update_execution_time"):
                target_node.update_execution_time(None)

            # Build node index for O(1) lookups during execution events
            self._build_node_index()

            self._is_paused = False
            self.run_single_node_requested.emit(target_node_id)
            self.execution_started.emit()

            # Update UI state
            self._update_execution_actions(running=True)

            self.main_window.show_status(f"Running node: {node_name}...", 0)

            # Create async task using lifecycle manager with single_node=True
            self._workflow_task = asyncio.create_task(
                self._lifecycle_manager.start_workflow(
                    self._workflow_runner,
                    force_cleanup=True,
                    target_node_id=target_node_id,
                    single_node=True,
                )
            )

        except Exception as e:
            # Ensure flag is reset on any unexpected error during setup
            logger.exception("Unexpected error during run_single_node startup")
            self._is_running = False
            self._update_execution_actions(running=False)
            raise

    def pause_workflow(self) -> None:
        """Pause running workflow."""
        logger.info("Pausing workflow")

        if not self._is_running:
            logger.warning("Cannot pause - workflow not running")
            return

        # Delegate to lifecycle manager
        asyncio.create_task(self._pause_workflow_async())

    async def _pause_workflow_async(self) -> None:
        """Async pause workflow via lifecycle manager."""
        success = await self._lifecycle_manager.pause_workflow()
        if success:
            self._is_paused = True
            self.execution_paused.emit()

            # Emit MainWindow signal for backward compatibility
            self.main_window.workflow_pause.emit()

            self.main_window.show_status("Workflow paused", 0)
        else:
            logger.warning("Failed to pause workflow via lifecycle manager")

    def resume_workflow(self) -> None:
        """Resume paused workflow."""
        logger.info("Resuming workflow")

        if not self._is_paused:
            logger.warning("Cannot resume - workflow not paused")
            return

        # Delegate to lifecycle manager
        asyncio.create_task(self._resume_workflow_async())

    async def _resume_workflow_async(self) -> None:
        """Async resume workflow via lifecycle manager."""
        success = await self._lifecycle_manager.resume_workflow()
        if success:
            self._is_paused = False
            self.execution_resumed.emit()

            # Emit MainWindow signal for backward compatibility
            self.main_window.workflow_resume.emit()

            self.main_window.show_status("Workflow resumed...", 0)
        else:
            logger.warning("Failed to resume workflow via lifecycle manager")

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

        # Delegate to lifecycle manager
        asyncio.create_task(self._stop_workflow_async())

    async def _stop_workflow_async(self) -> None:
        """Async stop workflow via lifecycle manager."""
        success = await self._lifecycle_manager.stop_workflow(force=False)
        if success:
            self._is_running = False
            self._is_paused = False
            self.execution_stopped.emit()

            # Emit MainWindow signal for backward compatibility
            self.main_window.workflow_stop.emit()

            # Update UI state
            self._update_execution_actions(running=False)

            self.main_window.show_status("Workflow execution stopped", 3000)
        else:
            logger.warning("Failed to stop workflow via lifecycle manager")

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

    @property
    def is_listening(self) -> bool:
        """Check if trigger is actively listening."""
        return self._is_listening

    # ─────────────────────────────────────────────────────────────────────────
    # Trigger Listening Methods (F9/F10)
    # ─────────────────────────────────────────────────────────────────────────

    def start_trigger_listening(self) -> None:
        """
        Start listening for trigger events (F9).

        For workflows with a trigger node, this activates background listening.
        When the trigger fires (e.g., schedule interval), the workflow executes.
        """
        logger.info("Starting trigger listening mode")

        if self._is_listening:
            logger.warning("Already listening for triggers")
            self.main_window.show_status("Already listening for triggers", 3000)
            return

        if self._is_running:
            logger.warning("Cannot start listening while workflow is running")
            self.main_window.show_status("Stop workflow first", 3000)
            return

        if not self._workflow_runner:
            logger.error("WorkflowRunner not configured")
            QMessageBox.critical(
                self.main_window,
                "Error",
                "Workflow runner not initialized.",
            )
            return

        # Validate before starting
        if not self._check_validation_before_run():
            return

        # Start listening asynchronously
        asyncio.create_task(self._start_listening_async())

    async def _start_listening_async(self) -> None:
        """Start trigger listening asynchronously."""
        success = await self._workflow_runner.start_listening()

        if success:
            self._is_listening = True
            self.trigger_listening_started.emit()
            self.main_window.show_status(
                "Trigger listening started - waiting for events...", 0
            )
            logger.success("Trigger listening started")

            # Update trigger node visual to show listening state
            self._update_trigger_node_visual(listening=True)
        else:
            QMessageBox.warning(
                self.main_window,
                "Trigger Error",
                "Failed to start trigger listening.\n\n"
                "Make sure your workflow has a trigger node (e.g., Schedule, Webhook).",
            )

    def stop_trigger_listening(self) -> None:
        """
        Stop listening for trigger events (F10 or Esc).

        Stops the active trigger and returns to idle state.
        """
        logger.info("Stopping trigger listening mode")

        if not self._is_listening:
            logger.debug("Not currently listening")
            return

        # Stop listening asynchronously
        asyncio.create_task(self._stop_listening_async())

    async def _stop_listening_async(self) -> None:
        """Stop trigger listening asynchronously."""
        if not self._workflow_runner:
            return

        success = await self._workflow_runner.stop_listening()

        if success:
            run_count = self._workflow_runner.trigger_run_count
            self._is_listening = False
            self.trigger_listening_stopped.emit()
            self.main_window.show_status(
                f"Trigger listening stopped (fired {run_count} times)", 3000
            )
            logger.info(f"Trigger listening stopped (fired {run_count} times)")

            # Update trigger node visual
            self._update_trigger_node_visual(listening=False)

    def toggle_trigger_listening(self) -> None:
        """Toggle trigger listening on/off."""
        if self._is_listening:
            self.stop_trigger_listening()
        else:
            self.start_trigger_listening()

    def _update_trigger_node_visual(self, listening: bool) -> None:
        """
        Update trigger node visual state.

        Args:
            listening: Whether trigger is actively listening
        """
        graph = self.main_window.get_graph()
        if not graph:
            return

        for visual_node in graph.all_nodes():
            # Check if this is a trigger node
            node_type = getattr(visual_node, "type_", "")
            if "Trigger" in node_type:
                if hasattr(visual_node, "set_listening"):
                    visual_node.set_listening(listening)
                # Also update status indicator
                if hasattr(visual_node, "update_status"):
                    visual_node.update_status("listening" if listening else "idle")

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
        self.main_window.action_pause.setEnabled(running)
        self.main_window.action_stop.setEnabled(running)

        if not running:
            # Reset pause button state
            self.main_window.action_pause.setChecked(False)
