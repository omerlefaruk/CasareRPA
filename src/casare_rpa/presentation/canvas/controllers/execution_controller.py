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
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from casare_rpa.application.services import ExecutionLifecycleManager
from casare_rpa.presentation.canvas.ui.theme import THEME

from .base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.workflow_runner import CanvasWorkflowRunner

    from ..main_window import MainWindow


class _ThreadSafeLogBridge(QObject):
    """
    Thread-safe bridge for Loguru → Log Tab.

    Qt signals are thread-safe and automatically marshal calls to the
    main thread when emitted from background threads.
    """

    log_received = Signal(str, str, str, str)  # level, message, module, timestamp

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

    def emit_log(self, level: str, message: str, module: str, timestamp: str) -> None:
        """Emit log signal (thread-safe)."""
        self.log_received.emit(level, message, module, timestamp)


class _ThreadSafeTerminalBridge(QObject):
    """
    Thread-safe bridge for stdout/stderr → Terminal Tab.

    Qt signals are thread-safe and automatically marshal calls to the
    main thread when emitted from background threads.
    """

    stdout_received = Signal(str)
    stderr_received = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

    def emit_stdout(self, text: str) -> None:
        """Emit stdout signal (thread-safe)."""
        self.stdout_received.emit(text)

    def emit_stderr(self, text: str) -> None:
        """Emit stderr signal (thread-safe)."""
        self.stderr_received.emit(text)


class _ThreadSafeEventBusBridge(QObject):
    """
    Thread-safe bridge for EventBus events → UI updates.

    EventBus callbacks are invoked from background threads during workflow
    execution. This bridge marshals those calls to the main Qt thread using
    signals with QueuedConnection.
    """

    node_started = Signal(object)
    node_completed = Signal(object)
    node_error = Signal(object)
    workflow_completed = Signal(object)
    workflow_error = Signal(object)
    workflow_stopped = Signal(object)
    browser_page_ready = Signal(object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)


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
        self._workflow_task: asyncio.Task | None = None
        self._event_bus = None
        self._workflow_runner: CanvasWorkflowRunner | None = None
        self._node_index: dict[str, object] = {}  # O(1) node lookup by node_id

        # Thread-safe bridges for cross-thread Qt calls
        self._log_bridge: _ThreadSafeLogBridge | None = None
        self._terminal_bridge: _ThreadSafeTerminalBridge | None = None
        self._event_bus_bridge: _ThreadSafeEventBusBridge | None = None

        # Execution lifecycle manager for state machine and cleanup
        self._lifecycle_manager = ExecutionLifecycleManager()
        logger.debug("ExecutionLifecycleManager initialized")

    def _emit_to_bridge(self, signal, event) -> None:
        """
        Helper method to emit events to bridge signals.

        Used with functools.partial to avoid lambdas in EventBus subscriptions.

        Args:
            signal: Qt Signal to emit to
            event: Event object to emit
        """
        signal.emit(event)

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        # Setup EventBus integration for visual node feedback
        self._setup_event_bus()
        # Setup Loguru → Log Tab bridge
        self._setup_log_tab_bridge()
        # Setup stdout/stderr → Terminal tab bridge
        self._setup_terminal_bridge()

    def _show_styled_message(
        self,
        title: str,
        text: str,
        info: str = "",
        icon: QMessageBox.Icon = QMessageBox.Icon.Critical,
    ) -> None:
        """Show a styled QMessageBox matching UI Explorer theme."""
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle(title)
        msg.setText(text)
        if info:
            msg.setInformativeText(info)
        msg.setIcon(icon)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {THEME.bg_darkest}; }}
            QMessageBox QLabel {{ color: {THEME.text_primary}; font-size: 12px; }}
            QPushButton {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 16px;
                color: {THEME.text_primary};
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }}
            QPushButton:hover {{ background: {THEME.bg_medium}; border-color: {THEME.accent_primary}; color: white; }}
            QPushButton:default {{ background: {THEME.accent_primary}; border-color: {THEME.accent_primary}; color: white; }}
        """)
        msg.exec()

    def _setup_event_bus(self) -> None:
        """
        Setup EventBus integration for workflow execution events.

        Extracted from: canvas/components/execution_component.py
        Subscribes to domain events for visual node feedback.

        Uses a thread-safe bridge with QueuedConnection to ensure UI updates
        happen on the main Qt thread, since EventBus callbacks are invoked
        from background workflow execution threads.
        """
        try:
            from ....domain.events import (
                BrowserPageReady,
                NodeCompleted,
                NodeFailed,
                NodeStarted,
                WorkflowCompleted,
                WorkflowFailed,
                WorkflowStopped,
                get_event_bus,
            )

            self._event_bus = get_event_bus()

            # Create thread-safe bridge for cross-thread event handling
            self._event_bus_bridge = _ThreadSafeEventBusBridge(self.main_window)

            # Connect bridge signals to handler slots with QueuedConnection
            # This ensures UI updates happen on the main thread
            self._event_bus_bridge.node_started.connect(
                self._on_node_started, Qt.ConnectionType.QueuedConnection
            )
            self._event_bus_bridge.node_completed.connect(
                self._on_node_completed, Qt.ConnectionType.QueuedConnection
            )
            self._event_bus_bridge.node_error.connect(
                self._on_node_error, Qt.ConnectionType.QueuedConnection
            )
            self._event_bus_bridge.workflow_completed.connect(
                self._on_workflow_completed, Qt.ConnectionType.QueuedConnection
            )
            self._event_bus_bridge.workflow_error.connect(
                self._on_workflow_error, Qt.ConnectionType.QueuedConnection
            )
            self._event_bus_bridge.workflow_stopped.connect(
                self._on_workflow_stopped, Qt.ConnectionType.QueuedConnection
            )
            self._event_bus_bridge.browser_page_ready.connect(
                self._on_browser_page_ready, Qt.ConnectionType.QueuedConnection
            )

            # Subscribe to EventBus - callbacks emit to bridge signals (thread-safe)
            # Using typed event classes (DDD pattern) instead of string enums
            # Using functools.partial instead of lambdas per signal-slot-rules.md
            self._event_bus.subscribe(
                NodeStarted,
                partial(self._emit_to_bridge, self._event_bus_bridge.node_started),
            )
            self._event_bus.subscribe(
                NodeCompleted,
                partial(self._emit_to_bridge, self._event_bus_bridge.node_completed),
            )
            self._event_bus.subscribe(
                NodeFailed,
                partial(self._emit_to_bridge, self._event_bus_bridge.node_error),
            )
            self._event_bus.subscribe(
                WorkflowCompleted,
                partial(self._emit_to_bridge, self._event_bus_bridge.workflow_completed),
            )
            self._event_bus.subscribe(
                WorkflowFailed,
                partial(self._emit_to_bridge, self._event_bus_bridge.workflow_error),
            )
            self._event_bus.subscribe(
                WorkflowStopped,
                partial(self._emit_to_bridge, self._event_bus_bridge.workflow_stopped),
            )
            self._event_bus.subscribe(
                BrowserPageReady,
                partial(self._emit_to_bridge, self._event_bus_bridge.browser_page_ready),
            )

            # Subscribe all events to log viewer if available
            # PERFORMANCE: Use subscribe_all() for O(1) instead of 100+ subscriptions
            log_viewer = self.main_window.get_log_viewer()
            if log_viewer and hasattr(log_viewer, "log_event"):
                self._event_bus.subscribe_all(log_viewer.log_event)

            logger.debug("EventBus bridge setup with QueuedConnection for thread safety")
        except ImportError as e:
            logger.warning(f"EventBus not available: {e}")
            self._event_bus = None
            self._event_bus_bridge = None

    def _setup_log_tab_bridge(self) -> None:
        """
        Setup Loguru → Log Tab bridge.

        Forwards all Loguru logs to the bottom panel's Log Tab for UI display.
        Uses thread-safe Qt signals to marshal calls from background threads.
        """
        try:
            from casare_rpa.infrastructure.observability.logging import (
                set_ui_log_callback,
            )

            # Create thread-safe bridge (must be parented to Qt object for thread affinity)
            self._log_bridge = _ThreadSafeLogBridge(self.main_window)

            # Connect signal to slot (runs in main thread)
            @Slot(str, str, str, str)
            def on_log_received(level: str, message: str, module: str, timestamp: str) -> None:
                """Handle log in main thread."""
                bottom_panel = self.main_window.get_bottom_panel()
                if bottom_panel:
                    # Map level to Log Tab format (lowercase)
                    level_map = {
                        "DEBUG": "debug",
                        "INFO": "info",
                        "SUCCESS": "success",
                        "WARNING": "warning",
                        "ERROR": "error",
                        "CRITICAL": "error",
                    }
                    log_level = level_map.get(level, "info")
                    # Include module in message for context
                    full_message = f"[{module}] {message}"
                    bottom_panel.log_message(full_message, log_level)

            self._log_bridge.log_received.connect(
                on_log_received, Qt.ConnectionType.QueuedConnection
            )

            # Register callback that emits signal (thread-safe)
            def log_callback(level: str, message: str, module: str, timestamp: str) -> None:
                """Forward log via thread-safe signal."""
                if self._log_bridge:
                    self._log_bridge.emit_log(level, message, module, timestamp)

            # Register callback with INFO level for better performance
            # DEBUG logging has significant overhead during execution
            set_ui_log_callback(log_callback, min_level="INFO")

        except ImportError as e:
            logger.warning(f"Failed to setup Log Tab bridge: {e}")

    def _setup_terminal_bridge(self) -> None:
        """
        Setup stdout/stderr → Terminal tab bridge.

        Captures print() statements and subprocess output during workflow
        execution and displays them in the Terminal tab.
        Uses thread-safe Qt signals to marshal calls from background threads.
        """
        try:
            from casare_rpa.infrastructure.observability.stdout_capture import (
                set_output_callbacks,
            )

            # Create thread-safe bridge (must be parented to Qt object for thread affinity)
            self._terminal_bridge = _ThreadSafeTerminalBridge(self.main_window)

            # Connect signals to slots (runs in main thread)
            @Slot(str)
            def on_stdout_received(text: str) -> None:
                """Handle stdout in main thread."""
                bottom_panel = self.main_window.get_bottom_panel()
                if bottom_panel:
                    bottom_panel.terminal_write_stdout(text)
                else:
                    logger.warning(f"Terminal: bottom_panel is None, dropping stdout: {text[:50]}")

            @Slot(str)
            def on_stderr_received(text: str) -> None:
                """Handle stderr in main thread."""
                bottom_panel = self.main_window.get_bottom_panel()
                if bottom_panel:
                    bottom_panel.terminal_write_stderr(text)
                else:
                    logger.warning(f"Terminal: bottom_panel is None, dropping stderr: {text[:50]}")

            self._terminal_bridge.stdout_received.connect(
                on_stdout_received, Qt.ConnectionType.QueuedConnection
            )
            self._terminal_bridge.stderr_received.connect(
                on_stderr_received, Qt.ConnectionType.QueuedConnection
            )

            # Register callbacks that emit signals (thread-safe)
            def stdout_callback(text: str) -> None:
                """Forward stdout via thread-safe signal."""
                if self._terminal_bridge:
                    self._terminal_bridge.emit_stdout(text)
                else:
                    # Log to original stderr to avoid recursion
                    import sys

                    sys.__stderr__.write(f"[TERMINAL] Bridge is None, stdout lost: {text}\n")

            def stderr_callback(text: str) -> None:
                """Forward stderr via thread-safe signal."""
                if self._terminal_bridge:
                    self._terminal_bridge.emit_stderr(text)
                else:
                    import sys

                    sys.__stderr__.write(f"[TERMINAL] Bridge is None, stderr lost: {text}\n")

            # Register callbacks
            set_output_callbacks(stdout_callback, stderr_callback)
            logger.debug("Terminal bridge setup complete - stdout/stderr capture active")

        except ImportError as e:
            logger.warning(f"Failed to setup Terminal bridge: {e}")

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

        # Remove Log Tab bridge
        try:
            from casare_rpa.infrastructure.observability.logging import (
                remove_ui_log_callback,
            )

            remove_ui_log_callback()
        except ImportError:
            pass

        # Clean up log bridge
        if self._log_bridge:
            self._log_bridge.deleteLater()
            self._log_bridge = None

        # Remove Terminal bridge
        try:
            from casare_rpa.infrastructure.observability.stdout_capture import (
                remove_output_callbacks,
            )

            remove_output_callbacks()
        except ImportError:
            pass

        # Clean up terminal bridge
        if self._terminal_bridge:
            self._terminal_bridge.deleteLater()
            self._terminal_bridge = None

        # Clean up event bus bridge
        if self._event_bus_bridge:
            self._event_bus_bridge.deleteLater()
            self._event_bus_bridge = None

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

    @Slot(object)
    def _on_node_started(self, event) -> None:
        """
        Handle NODE_STARTED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'running' and starts pipe flow animation.
        """
        # Extract data from Event object
        # Support both: typed DomainEvent (has to_dict) and legacy dict events
        if hasattr(event, "to_dict") and callable(event.to_dict):
            event_data = event.to_dict()
        elif hasattr(event, "data"):
            event_data = event.data
        else:
            event_data = event if isinstance(event, dict) else {}
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("running")
                logger.debug(f"Node {node_id} visual status: running")

                # Start flow animation on outgoing pipes
                self._start_pipe_animations(visual_node)

    @Slot(object)
    def _on_node_completed(self, event) -> None:
        """
        Handle NODE_COMPLETED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'success' (shows green checkmark).
        Also stops pipe animation with success glow, stores output for
        output inspector popup, and forwards node output to Output Tab
        and History Tab.
        """
        # Extract data from Event object
        # Support both: typed DomainEvent (has to_dict) and legacy dict events
        if hasattr(event, "to_dict") and callable(event.to_dict):
            event_data = event.to_dict()
        elif hasattr(event, "data"):
            event_data = event.data
        else:
            event_data = event if isinstance(event, dict) else {}
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None
        if node_id:
            visual_node = self._find_visual_node(node_id)

            # Extract execution time early (before visual_node check)
            # Support 'execution_time_ms' (from NodeCompleted event),
            # 'execution_time' (seconds), and 'duration_ms' (milliseconds)
            execution_time_sec = None
            if isinstance(event_data, dict):
                if "execution_time_ms" in event_data:
                    # execution_time_ms is in milliseconds (from NodeCompleted event)
                    execution_time_ms = event_data.get("execution_time_ms")
                    if execution_time_ms is not None:
                        execution_time_sec = execution_time_ms / 1000.0
                elif "execution_time" in event_data:
                    # execution_time is in seconds
                    execution_time_sec = event_data.get("execution_time")
                elif "duration_ms" in event_data:
                    # duration_ms is in milliseconds, convert to seconds
                    duration_ms = event_data.get("duration_ms")
                    if duration_ms is not None:
                        execution_time_sec = duration_ms / 1000.0

            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("success")
                if execution_time_sec is not None and hasattr(visual_node, "update_execution_time"):
                    visual_node.update_execution_time(execution_time_sec)
                logger.debug(f"Node {node_id} visual status: success")

                # Stop flow animation with success glow
                self._stop_pipe_animations(visual_node, success=True)

                # Store output data for output inspector popup (middle-click)
                # Get output port values from event_data (set by node_executor)
                # Key is 'output_data' from NodeCompleted event's to_dict()
                if hasattr(visual_node, "set_last_output"):
                    output_data = (
                        event_data.get("output_data", {}) if isinstance(event_data, dict) else {}
                    )
                    if output_data:
                        visual_node.set_last_output(output_data)
                        logger.debug(
                            f"Stored output for node {node_id}: {list(output_data.keys())}"
                        )

                        # Update phantom values on output pipes
                        self._update_phantom_values(visual_node, output_data)

            # Forward output to Output Tab and History Tab
            bottom_panel = self.main_window.get_bottom_panel()
            if bottom_panel and isinstance(event_data, dict):
                # Get node name for output display
                node_type = event_data.get("node_type", "Node")
                node_name = event_data.get("node_name", node_id)

                # Check for output value in event data
                output_value = event_data.get("result") or event_data.get("output")
                if output_value is not None:
                    bottom_panel.add_output(node_name, output_value)

                # Add to history
                history_entry = {
                    "timestamp": event_data.get(
                        "timestamp",
                        datetime.now().isoformat(),
                    ),
                    "node_id": node_id,
                    "node_type": node_type,
                    "execution_time": execution_time_sec or 0,
                    "status": "success",
                }
                bottom_panel.append_history_entry(history_entry)

    @Slot(object)
    def _on_node_error(self, event) -> None:
        """
        Handle NODE_ERROR event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Updates visual node status to 'error' (shows red X icon).
        Also stops pipe animation and adds failed entry to History Tab.
        """
        # Extract data from Event object
        # Support both: typed DomainEvent (has to_dict) and legacy dict events
        if hasattr(event, "to_dict") and callable(event.to_dict):
            event_data = event.to_dict()
        elif hasattr(event, "data"):
            event_data = event.data
        else:
            event_data = event if isinstance(event, dict) else {}
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None
        error = event_data.get("error_message") or event_data.get("error") or "Unknown error"
        if node_id:
            visual_node = self._find_visual_node(node_id)
            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("error")
                logger.error(f"Node {node_id} error: {error}")

                # Stop flow animation without success glow
                self._stop_pipe_animations(visual_node, success=False)

            # Add to history
            bottom_panel = self.main_window.get_bottom_panel()
            if bottom_panel and isinstance(event_data, dict):
                node_type = event_data.get("node_type", "Node")
                history_entry = {
                    "timestamp": event_data.get(
                        "timestamp",
                        datetime.now().isoformat(),
                    ),
                    "node_id": node_id,
                    "node_type": node_type,
                    "execution_time": 0,
                    "status": "failed",
                    "error": str(error),
                }
                bottom_panel.append_history_entry(history_entry)

    @Slot(object)
    def _on_workflow_completed(self, event) -> None:
        """
        Handle WORKFLOW_COMPLETED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Also sets workflow result and exports variables to Output Tab.
        """
        logger.info("Workflow execution completed (EventBus)")

        # Set workflow result in Output Tab
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            event_data = event.data if hasattr(event, "data") else event
            message = "Workflow completed successfully"
            if isinstance(event_data, dict):
                message = event_data.get("message", message)
                # Include execution stats if available
                # ExecuteWorkflowUseCase emits: executed_nodes, total_nodes, duration
                node_count = event_data.get("executed_nodes", 0)
                duration = event_data.get("duration", 0)
                if node_count or duration:
                    message = f"{message} ({node_count} nodes in {duration:.2f}s)"

                # Export final variables to Output Tab
                variables = event_data.get("variables", {})
                if variables:
                    for var_name, var_value in variables.items():
                        bottom_panel.add_output(var_name, var_value)
                    logger.debug(f"Exported {len(variables)} variables to Output tab")

            bottom_panel.set_workflow_result(True, message)

        self.on_execution_completed()

    @Slot(object)
    def _on_workflow_error(self, event) -> None:
        """
        Handle WORKFLOW_ERROR event from EventBus.

        Extracted from: canvas/components/execution_component.py
        Also sets workflow result in Output Tab.
        """
        # Extract data from Event object
        event_data = event.data if hasattr(event, "data") else event
        error = (
            event_data.get("error", "Unknown error")
            if isinstance(event_data, dict)
            else "Unknown error"
        )
        logger.error(f"Workflow error (EventBus): {error}")

        # Set workflow result in Output Tab
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            # Include node info if available for better error context
            node_id = event_data.get("node_id", "") if isinstance(event_data, dict) else ""
            if node_id:
                error_msg = f"Failed at node {node_id}: {error}"
            else:
                error_msg = str(error)
            bottom_panel.set_workflow_result(False, error_msg)

        self.on_execution_error(str(error))

    @Slot(object)
    def _on_workflow_stopped(self, event) -> None:
        """
        Handle WORKFLOW_STOPPED event from EventBus.

        Extracted from: canvas/components/execution_component.py
        """
        logger.info("Workflow stopped (EventBus)")
        self._is_running = False
        self._is_paused = False
        self._update_execution_actions(running=False)
        # Disable browser picker/recorder when workflow stops
        self.main_window.set_browser_running(False)

    @Slot(object)
    def _on_browser_page_ready(self, event) -> None:
        """
        Handle BROWSER_PAGE_READY event from EventBus.

        Enables picker and recorder actions when browser is launched.
        Also initializes the selector controller with the page.

        Note: This may be called from a background thread, so we use
        QTimer.singleShot to ensure UI updates happen on the main thread.
        """
        from PySide6.QtCore import QTimer

        logger.info("Browser page ready event received - scheduling UI update")

        # Extract page from event data
        event_data = event.data if hasattr(event, "data") else {}
        page = event_data.get("page") if isinstance(event_data, dict) else None

        # Schedule UI update on main thread
        def enable_browser_actions():
            logger.info("Enabling picker/recorder on main thread")
            self.main_window.set_browser_running(True)

            # Initialize selector controller with the page (sync version for reliability)
            if page and hasattr(self.main_window, "_selector_controller"):
                selector_ctrl = self.main_window._selector_controller
                if selector_ctrl:
                    # Use sync version - async version can fail silently on Qt main thread
                    selector_ctrl.set_browser_page(page)
                    logger.info("Browser page set on selector controller")

        QTimer.singleShot(0, enable_browser_actions)

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

    def _iter_connected_pipes(self, port_view):
        """Yield connected pipe items from a PortItem (supports list or callable API)."""
        connected = getattr(port_view, "connected_pipes", None)
        if connected is None:
            return []
        try:
            if callable(connected):
                connected = connected()
        except Exception:
            return []
        if not connected:
            return []
        try:
            return list(connected)
        except Exception:
            return []

    def _start_pipe_animations(self, visual_node) -> None:
        """
        Start flow animation on all outgoing pipes from a node.

        Called when a node starts executing to show data flowing along wires.

        Args:
            visual_node: The visual node whose output pipes should animate
        """
        try:
            # Get outgoing pipes from output ports
            for output_port in visual_node.output_ports():
                # output_port.view gives access to the NodeGraphQt port item
                port_view = getattr(output_port, "view", None)
                if port_view is None:
                    continue

                for pipe in self._iter_connected_pipes(port_view):
                    if hasattr(pipe, "start_flow_animation"):
                        pipe.start_flow_animation()
        except Exception:
            # Don't let animation errors affect execution
            pass

    def _stop_pipe_animations(self, visual_node, success: bool = True) -> None:
        """
        Stop flow animation on all outgoing pipes from a node.

        Called when a node finishes executing.

        Args:
            visual_node: The visual node whose output pipes should stop animating
            success: Whether execution was successful (shows green glow if True)
        """
        try:
            # Get outgoing pipes from output ports
            for output_port in visual_node.output_ports():
                # output_port.view gives access to the NodeGraphQt port item
                port_view = getattr(output_port, "view", None)
                if port_view is None:
                    continue

                for pipe in self._iter_connected_pipes(port_view):
                    if hasattr(pipe, "stop_flow_animation"):
                        pipe.stop_flow_animation(show_completion_glow=success)
        except Exception:
            # Don't let animation errors affect execution
            pass

    def _update_phantom_values(self, visual_node, output_data: dict) -> None:
        """
        Update phantom values on output pipes to show execution results.

        Displays the last execution value as semi-transparent text on each output wire.

        Args:
            visual_node: The visual node whose output pipes should show phantom values
            output_data: Dictionary of port_name -> value from node execution
        """
        try:
            for output_port in visual_node.output_ports():
                port_name = output_port.name()
                value = output_data.get(port_name)

                if value is None:
                    continue

                port_view = getattr(output_port, "view", None)
                if port_view is None:
                    continue

                for pipe in self._iter_connected_pipes(port_view):
                    if hasattr(pipe, "set_phantom_value"):
                        pipe.set_phantom_value(value)
        except Exception as e:
            logger.debug(f"Error updating phantom values: {e}")

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

    def _sync_all_widget_values(self) -> None:
        """
        Force sync all widget values to casare_node.config before execution.

        CRITICAL: Widgets only sync their values when editingFinished fires (on Enter
        or focus loss). If user types a value and clicks Run without pressing Enter,
        the value is never synced. This method forces all widgets to sync.
        """
        graph = self.main_window.get_graph()
        if not graph:
            return

        for visual_node in graph.all_nodes():
            # Force each widget to emit its current value
            if hasattr(visual_node, "widgets"):
                for _widget_name, widget in visual_node.widgets().items():
                    try:
                        if hasattr(widget, "on_value_changed"):
                            widget.on_value_changed()
                    except Exception:
                        pass  # Widget might not support this

    def run_workflow(self) -> None:
        """
        Run workflow from start to end (F3).

        Auto-detects trigger nodes: if workflow has a trigger, starts listening mode
        instead of one-shot execution.
        """
        logger.info("Running workflow")

        # Check if already listening - stop first
        if self._is_listening:
            logger.info("Stopping active trigger before re-run")
            self.stop_trigger_listening()

        # Atomic check-and-set to prevent race condition on rapid F3 presses
        if self._is_running:
            logger.warning("Workflow already running")
            self.main_window.show_status("Workflow is already running", 3000)
            return

        # Validate before running
        if not self._check_validation_before_run():
            return

        # Check if runner is configured
        if not self._workflow_runner:
            logger.error("WorkflowRunner not configured")
            self._show_styled_message(
                "Execution Error",
                "Workflow runner not initialized.",
                "Please restart the application.",
            )
            return

        # Auto-detect trigger nodes - if present, start listening mode instead
        if self._has_trigger_node():
            logger.info("Trigger node detected - starting listening mode")
            self.start_trigger_listening()
            return

        # Set flag immediately to block concurrent calls (only for non-trigger runs)
        self._is_running = True

        try:
            # CRITICAL: Sync all widget values before execution
            # Widgets only sync on Enter/focus-loss - this forces sync for any unsaved values
            self._sync_all_widget_values()

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

        except Exception:
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
            self.main_window.show_status("No node selected - running full workflow", 3000)
            self.run_workflow()
            return

        # Get first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            self.main_window.show_status("Selected node has no ID - running full workflow", 3000)
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
                self._show_styled_message(
                    "Execution Error",
                    "Workflow runner not initialized.",
                    "Please restart the application.",
                )
                self._is_running = False
                return

            # Get node name for display
            node_name = target_node.name() if hasattr(target_node, "name") else target_node_id

            # CRITICAL: Sync all widget values before execution
            self._sync_all_widget_values()

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

        except Exception:
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
            self.main_window.show_status("No node selected - select a node to run", 3000)
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
                self._show_styled_message(
                    "Execution Error",
                    "Workflow runner not initialized.",
                    "Please restart the application.",
                )
                self._is_running = False
                return

            # Get node name for display
            node_name = target_node.name() if hasattr(target_node, "name") else target_node_id

            # CRITICAL: Sync all widget values before execution
            self._sync_all_widget_values()

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

        except Exception:
            # Ensure flag is reset on any unexpected error during setup
            logger.exception("Unexpected error during run_single_node startup")
            self._is_running = False
            self._update_execution_actions(running=False)
            raise

    def run_all_workflows(self) -> None:
        """
        Run all workflows on canvas concurrently (Shift+F3).

        When the canvas contains multiple independent workflows (each with its
        own StartNode), this executes them all in parallel. Each workflow gets
        SHARED variables but SEPARATE browser instances.
        """
        logger.info("Running all workflows concurrently")

        # Atomic check-and-set to prevent race condition
        if self._is_running:
            logger.warning("Workflow already running")
            self.main_window.show_status("Workflow is already running", 3000)
            return

        # Validate before running
        if not self._check_validation_before_run():
            return

        # Check if runner is configured
        if not self._workflow_runner:
            logger.error("WorkflowRunner not configured")
            self._show_styled_message(
                "Execution Error",
                "Workflow runner not initialized.",
                "Please restart the application.",
            )
            return

        # Set flag immediately to block concurrent calls
        self._is_running = True

        try:
            # CRITICAL: Sync all widget values before execution
            self._sync_all_widget_values()

            # Reset all node visuals before starting
            self._reset_all_node_visuals()

            # Build node index for O(1) lookups during execution events
            self._build_node_index()

            self._is_paused = False
            self.execution_started.emit()

            # Emit MainWindow signal for parallel workflow execution
            self.main_window.workflow_run_all.emit()

            # Update UI state
            self._update_execution_actions(running=True)

            self.main_window.show_status("Running all workflows concurrently...", 0)

            # Create async task using lifecycle manager for run_all mode
            self._workflow_task = asyncio.create_task(
                self._lifecycle_manager.start_workflow_run_all(
                    self._workflow_runner,
                    force_cleanup=True,
                )
            )

        except Exception:
            # Ensure flag is reset on any unexpected error during setup
            logger.exception("Unexpected error during run_all_workflows startup")
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

    @Slot(bool)
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
        # Use force=True for immediate cancellation
        # Graceful stop (force=False) only checks flag between nodes,
        # which can take 120s+ if a node is running a long browser operation
        success = await self._lifecycle_manager.stop_workflow(force=True)

        # Always reset state and emit events, regardless of success
        # This ensures UI stays in sync even if cleanup had issues
        self._is_running = False
        self._is_paused = False
        self.execution_stopped.emit()

        # Emit MainWindow signal for backward compatibility
        self.main_window.workflow_stop.emit()

        # Update UI state
        self._update_execution_actions(running=False)

        if success:
            self.main_window.show_status("Workflow execution stopped", 3000)
        else:
            logger.warning("Workflow stop completed with issues")
            self.main_window.show_status("Workflow stopped (cleanup may be incomplete)", 3000)

    def restart_workflow(self) -> None:
        """
        Restart workflow - force stop, reset all state, and run fresh.

        This ensures a clean restart as if the workflow was never run before:
        1. Force stop any running execution
        2. Reset all node visual states
        3. Clear execution context and variables
        4. Start fresh execution
        """
        logger.info("Restarting workflow")

        # Create async task to handle the restart
        asyncio.create_task(self._restart_workflow_async())

    async def _restart_workflow_async(self) -> None:
        """Async implementation of restart workflow."""
        # Step 1: Force stop if running
        if self._is_running:
            logger.info("Stopping current execution before restart")
            await self._lifecycle_manager.stop_workflow(force=True)

            # Reset state
            self._is_running = False
            self._is_paused = False

        # Step 2: Reset all node visuals
        self._reset_all_node_visuals()

        # Step 3: Clear execution context via lifecycle manager
        # (This is handled by force_cleanup in stop_workflow)

        # Step 4: Small delay to ensure cleanup completes
        await asyncio.sleep(0.1)

        # Step 5: Start fresh execution
        logger.info("Starting fresh workflow execution")
        self.run_workflow()

        self.main_window.show_status("Workflow restarted", 3000)

    @Slot()
    def on_execution_completed(self) -> None:
        """Handle workflow execution completion."""
        logger.info("Workflow execution completed")

        self._is_running = False
        self._is_paused = False
        self.execution_completed.emit()

        # Update UI state
        self._update_execution_actions(running=False)

        self.main_window.show_status("Workflow execution completed", 3000)

    @Slot(str)
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
            self._show_styled_message(
                "Error",
                "Workflow runner not initialized.",
            )
            return

        # Validate before starting
        if not self._check_validation_before_run():
            return

        # CRITICAL: Sync all widget values before execution
        self._sync_all_widget_values()

        # Start listening asynchronously
        asyncio.create_task(self._start_listening_async())

    async def _start_listening_async(self) -> None:
        """Start trigger listening asynchronously."""
        success = await self._workflow_runner.start_listening()

        if success:
            self._is_listening = True
            self.trigger_listening_started.emit()
            self.main_window.show_status("Trigger listening started - waiting for events...", 0)
            logger.success("Trigger listening started")

            # Update trigger node visual to show listening state
            self._update_trigger_node_visual(listening=True)
        else:
            self._show_styled_message(
                "Trigger Error",
                "Failed to start trigger listening.",
                "Make sure your workflow has a trigger node (e.g., Schedule, Webhook).",
                QMessageBox.Icon.Warning,
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

    def _has_trigger_node(self) -> bool:
        """
        Check if workflow contains a trigger node.

        Returns:
            True if any trigger node is present in the graph
        """
        graph = self.main_window.get_graph()
        if not graph:
            return False

        for visual_node in graph.all_nodes():
            node_type = getattr(visual_node, "type_", "")
            # Check for trigger node types
            if "Trigger" in node_type and "Node" in node_type:
                logger.debug(f"Found trigger node: {node_type}")
                return True

        return False

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
                self._show_styled_message(
                    "Validation Errors",
                    f"The workflow has {len(validation_errors)} validation error(s) that must be fixed before running.",
                    "Please check the Validation tab for details.",
                    QMessageBox.Icon.Warning,
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
