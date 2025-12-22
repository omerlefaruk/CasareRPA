"""
Qt Domain Event Bridge for Typed Domain Events.

Bridges typed domain events (DDD events) to Qt signals for UI updates.
This allows Qt widgets to receive strongly-typed execution events through
signal/slot connections while maintaining clean architecture separation.

Unlike DomainEventBridge (which bridges EventType enum to presentation EventBus),
this bridge works with typed dataclass events and emits Qt signals with
specific signatures.

Usage:
    from casare_rpa.presentation.canvas.coordinators import QtDomainEventBridge
    from casare_rpa.domain.events import get_event_bus

    # Create bridge at application startup
    bridge = QtDomainEventBridge(get_event_bus())

    # Connect Qt slots to typed signals
    bridge.node_started.connect(on_node_started)
    bridge.workflow_completed.connect(on_workflow_completed)

    def on_node_started(node_id: str, node_type: str) -> None:
        print(f"Node {node_id} ({node_type}) started")

Thread Safety:
    Events may be published from async code. Qt signals handle cross-thread
    delivery automatically via Qt's queued connection mechanism.
"""

from typing import Any, Callable, Optional, Type

from PySide6.QtCore import QObject, Signal

from loguru import logger


class QtDomainEventBridge(QObject):
    """
    Bridge typed domain events to Qt signals for UI updates.

    This bridge subscribes to typed domain events (frozen dataclasses) and
    emits Qt signals with specific signatures. This allows Qt widgets to
    receive execution state changes through signal/slot connections.

    Signals:
        Node Events:
            node_started(node_id, node_type, workflow_id)
            node_completed(node_id, node_type, execution_time_ms)
            node_failed(node_id, node_type, error_message, is_retryable)
            node_skipped(node_id, node_type, reason)

        Workflow Events:
            workflow_started(workflow_id, workflow_name, total_nodes)
            workflow_completed(workflow_id, execution_time_ms, nodes_executed)
            workflow_failed(workflow_id, error_message, failed_node_id)
            workflow_progress(workflow_id, percentage, completed_nodes, total_nodes)
            workflow_paused(workflow_id, paused_at_node_id)
            workflow_resumed(workflow_id, resume_from_node_id)
            workflow_stopped(workflow_id, stopped_at_node_id)

        System Events:
            variable_set(variable_name, value)
            log_message(level, message, source)
            browser_page_ready(page_id, url, title)
            debug_breakpoint_hit(node_id, workflow_id)

    Example:
        class ExecutionPanel(QWidget):
            def __init__(self, event_bridge: QtDomainEventBridge):
                super().__init__()

                # Connect to typed signals
                event_bridge.node_started.connect(self._on_node_started)
                event_bridge.node_completed.connect(self._on_node_completed)
                event_bridge.node_failed.connect(self._on_node_failed)
                event_bridge.workflow_progress.connect(self._on_progress)

            def _on_node_started(
                self, node_id: str, node_type: str, workflow_id: str
            ) -> None:
                self.highlight_node(node_id, "running")

            def _on_node_completed(
                self, node_id: str, node_type: str, execution_time_ms: float
            ) -> None:
                self.highlight_node(node_id, "completed")
                self.update_timing(node_id, execution_time_ms)

            def _on_node_failed(
                self, node_id: str, node_type: str, error_msg: str, retryable: bool
            ) -> None:
                self.highlight_node(node_id, "error")
                self.show_error(node_id, error_msg)

            def _on_progress(
                self, workflow_id: str, pct: float, completed: int, total: int
            ) -> None:
                self.progress_bar.setValue(int(pct))
    """

    # Node signals - specific signatures for type safety
    node_started = Signal(str, str, str)  # node_id, node_type, workflow_id
    node_completed = Signal(str, str, float)  # node_id, node_type, execution_time_ms
    node_failed = Signal(str, str, str, bool)  # node_id, node_type, error_msg, retryable
    node_skipped = Signal(str, str, str)  # node_id, node_type, reason

    # Workflow signals
    workflow_started = Signal(str, str, int)  # workflow_id, workflow_name, total_nodes
    workflow_completed = Signal(str, float, int)  # workflow_id, exec_time_ms, nodes_executed
    workflow_failed = Signal(str, str, str)  # workflow_id, error_message, failed_node_id
    workflow_progress = Signal(str, float, int, int)  # workflow_id, pct, completed, total
    workflow_paused = Signal(str, str)  # workflow_id, paused_at_node_id
    workflow_resumed = Signal(str, str)  # workflow_id, resume_from_node_id
    workflow_stopped = Signal(str, str)  # workflow_id, stopped_at_node_id

    # System signals
    variable_set = Signal(str, object)  # variable_name, value
    log_message = Signal(str, str, str)  # level, message, source
    browser_page_ready = Signal(str, str, str)  # page_id, url, title
    debug_breakpoint_hit = Signal(str, str)  # node_id, workflow_id

    # Generic signal for all events (event_type_name, event_dict)
    domain_event = Signal(str, dict)

    def __init__(self, event_bus: Any, parent: Optional[QObject] = None) -> None:
        """
        Initialize the Qt domain event bridge.

        Args:
            event_bus: EventBus instance that supports subscribe(EventType, handler)
            parent: Optional parent QObject for Qt ownership
        """
        super().__init__(parent)
        self._event_bus = event_bus
        self._subscriptions: list[tuple[Type, Callable]] = []
        self._running = False

        logger.debug("QtDomainEventBridge created")

    def start(self) -> None:
        """
        Start bridging domain events to Qt signals.

        Subscribes to all typed domain events. Call this at application startup
        after the event bus is ready.
        """
        if self._running:
            logger.warning("QtDomainEventBridge already running")
            return

        self._subscribe_to_events()
        self._running = True
        logger.info(f"QtDomainEventBridge started with {len(self._subscriptions)} subscriptions")

    def stop(self) -> None:
        """
        Stop bridging domain events.

        Unsubscribes from all event types. Call this when closing the application.
        """
        if not self._running:
            return

        self._unsubscribe_all()
        self._running = False
        logger.info("QtDomainEventBridge stopped")

    def _subscribe_to_events(self) -> None:
        """Subscribe to all typed domain events."""
        try:
            from casare_rpa.domain.events import (
                BrowserPageReady,
                DebugBreakpointHit,
                LogMessage,
                NodeCompleted,
                NodeFailed,
                NodeSkipped,
                NodeStarted,
                VariableSet,
                WorkflowCompleted,
                WorkflowFailed,
                WorkflowPaused,
                WorkflowProgress,
                WorkflowResumed,
                WorkflowStarted,
                WorkflowStopped,
            )

            # Node events
            self._subscribe(NodeStarted, self._on_node_started)
            self._subscribe(NodeCompleted, self._on_node_completed)
            self._subscribe(NodeFailed, self._on_node_failed)
            self._subscribe(NodeSkipped, self._on_node_skipped)

            # Workflow events
            self._subscribe(WorkflowStarted, self._on_workflow_started)
            self._subscribe(WorkflowCompleted, self._on_workflow_completed)
            self._subscribe(WorkflowFailed, self._on_workflow_failed)
            self._subscribe(WorkflowProgress, self._on_workflow_progress)
            self._subscribe(WorkflowPaused, self._on_workflow_paused)
            self._subscribe(WorkflowResumed, self._on_workflow_resumed)
            self._subscribe(WorkflowStopped, self._on_workflow_stopped)

            # System events
            self._subscribe(VariableSet, self._on_variable_set)
            self._subscribe(LogMessage, self._on_log_message)
            self._subscribe(BrowserPageReady, self._on_browser_page_ready)
            self._subscribe(DebugBreakpointHit, self._on_debug_breakpoint_hit)

        except ImportError as e:
            logger.error(f"Failed to import domain events: {e}")
            raise

    def _subscribe(self, event_type: Type, handler: Callable) -> None:
        """
        Subscribe to a typed event.

        Args:
            event_type: The DomainEvent subclass to subscribe to
            handler: Handler method to call when event occurs
        """
        try:
            self._event_bus.subscribe(event_type, handler)
            self._subscriptions.append((event_type, handler))
        except Exception as e:
            logger.warning(f"Failed to subscribe to {event_type.__name__}: {e}")

    def _unsubscribe_all(self) -> None:
        """Unsubscribe from all events."""
        for event_type, handler in self._subscriptions:
            try:
                self._event_bus.unsubscribe(event_type, handler)
            except Exception as e:
                logger.debug(f"Failed to unsubscribe from {event_type.__name__}: {e}")
        self._subscriptions.clear()

    # ==================== Node Event Handlers ====================

    def _on_node_started(self, event: Any) -> None:
        """Handle NodeStarted event."""
        try:
            self.node_started.emit(
                event.node_id,
                event.node_type,
                event.workflow_id,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling NodeStarted: {e}")

    def _on_node_completed(self, event: Any) -> None:
        """Handle NodeCompleted event."""
        try:
            self.node_completed.emit(
                event.node_id,
                event.node_type,
                event.execution_time_ms,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling NodeCompleted: {e}")

    def _on_node_failed(self, event: Any) -> None:
        """Handle NodeFailed event."""
        try:
            self.node_failed.emit(
                event.node_id,
                event.node_type,
                event.error_message,
                event.is_retryable,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling NodeFailed: {e}")

    def _on_node_skipped(self, event: Any) -> None:
        """Handle NodeSkipped event."""
        try:
            self.node_skipped.emit(
                event.node_id,
                event.node_type,
                event.reason,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling NodeSkipped: {e}")

    # ==================== Workflow Event Handlers ====================

    def _on_workflow_started(self, event: Any) -> None:
        """Handle WorkflowStarted event."""
        try:
            self.workflow_started.emit(
                event.workflow_id,
                event.workflow_name,
                event.total_nodes,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowStarted: {e}")

    def _on_workflow_completed(self, event: Any) -> None:
        """Handle WorkflowCompleted event."""
        try:
            self.workflow_completed.emit(
                event.workflow_id,
                event.execution_time_ms,
                event.nodes_executed,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowCompleted: {e}")

    def _on_workflow_failed(self, event: Any) -> None:
        """Handle WorkflowFailed event."""
        try:
            failed_node_id = event.failed_node_id or ""
            self.workflow_failed.emit(
                event.workflow_id,
                event.error_message,
                failed_node_id,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowFailed: {e}")

    def _on_workflow_progress(self, event: Any) -> None:
        """Handle WorkflowProgress event."""
        try:
            self.workflow_progress.emit(
                event.workflow_id,
                event.percentage,
                event.completed_nodes,
                event.total_nodes,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowProgress: {e}")

    def _on_workflow_paused(self, event: Any) -> None:
        """Handle WorkflowPaused event."""
        try:
            self.workflow_paused.emit(
                event.workflow_id,
                event.paused_at_node_id,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowPaused: {e}")

    def _on_workflow_resumed(self, event: Any) -> None:
        """Handle WorkflowResumed event."""
        try:
            self.workflow_resumed.emit(
                event.workflow_id,
                event.resume_from_node_id,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowResumed: {e}")

    def _on_workflow_stopped(self, event: Any) -> None:
        """Handle WorkflowStopped event."""
        try:
            stopped_at = event.stopped_at_node_id or ""
            self.workflow_stopped.emit(
                event.workflow_id,
                stopped_at,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling WorkflowStopped: {e}")

    # ==================== System Event Handlers ====================

    def _on_variable_set(self, event: Any) -> None:
        """Handle VariableSet event."""
        try:
            self.variable_set.emit(
                event.variable_name,
                event.variable_value,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling VariableSet: {e}")

    def _on_log_message(self, event: Any) -> None:
        """Handle LogMessage event."""
        try:
            level_str = event.level.value if hasattr(event.level, "value") else str(event.level)
            source = event.source or ""
            self.log_message.emit(
                level_str,
                event.message,
                source,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling LogMessage: {e}")

    def _on_browser_page_ready(self, event: Any) -> None:
        """Handle BrowserPageReady event."""
        try:
            self.browser_page_ready.emit(
                event.page_id,
                event.url,
                event.title,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling BrowserPageReady: {e}")

    def _on_debug_breakpoint_hit(self, event: Any) -> None:
        """Handle DebugBreakpointHit event."""
        try:
            self.debug_breakpoint_hit.emit(
                event.node_id,
                event.workflow_id,
            )
            self._emit_generic(event)
        except Exception as e:
            logger.error(f"Error handling DebugBreakpointHit: {e}")

    # ==================== Utility Methods ====================

    def _emit_generic(self, event: Any) -> None:
        """
        Emit the generic domain_event signal.

        Args:
            event: Any domain event with to_dict() method
        """
        try:
            event_type_name = event.__class__.__name__
            event_dict = event.to_dict() if hasattr(event, "to_dict") else {}
            self.domain_event.emit(event_type_name, event_dict)
        except Exception as e:
            logger.debug(f"Failed to emit generic event: {e}")

    @property
    def is_running(self) -> bool:
        """Check if bridge is currently running."""
        return self._running

    def cleanup(self) -> None:
        """
        Cleanup the bridge.

        Stops the bridge and clears subscriptions. Call before destroying.
        """
        self.stop()
        logger.debug("QtDomainEventBridge cleaned up")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"QtDomainEventBridge("
            f"running={self._running}, "
            f"subscriptions={len(self._subscriptions)}"
            f")"
        )


# Singleton instance for convenience
_bridge_instance: Optional[QtDomainEventBridge] = None


def get_qt_domain_event_bridge(
    event_bus: Optional[Any] = None, parent: Optional[QObject] = None
) -> QtDomainEventBridge:
    """
    Get or create the Qt domain event bridge singleton.

    Args:
        event_bus: EventBus instance (required on first call)
        parent: Optional parent QObject

    Returns:
        QtDomainEventBridge singleton instance

    Raises:
        ValueError: If event_bus not provided on first call
    """
    global _bridge_instance

    if _bridge_instance is None:
        if event_bus is None:
            raise ValueError("event_bus required on first call to get_qt_domain_event_bridge")
        _bridge_instance = QtDomainEventBridge(event_bus, parent)

    return _bridge_instance


def reset_qt_domain_event_bridge() -> None:
    """
    Reset the singleton instance (for testing).

    Stops and clears the existing bridge.
    """
    global _bridge_instance

    if _bridge_instance is not None:
        _bridge_instance.cleanup()
        _bridge_instance = None
    logger.debug("QtDomainEventBridge singleton reset")
