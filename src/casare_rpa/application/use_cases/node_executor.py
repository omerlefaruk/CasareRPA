"""
CasareRPA - Node Executor

Handles individual node execution including:
- Node validation and execution with timeout
- Status tracking and metrics recording
- Event emission for node lifecycle
- Bypass handling for disabled nodes

Extracted from ExecuteWorkflowUseCase for Single Responsibility.
"""

import asyncio
import time
from typing import Any, Dict, Optional, Tuple

from loguru import logger

from casare_rpa.domain.events import Event, EventBus
from casare_rpa.domain.value_objects.types import EventType, NodeStatus
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils.performance.performance_metrics import get_metrics


class NodeExecutionResult:
    """Result of a node execution."""

    def __init__(
        self,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        execution_time: float = 0.0,
        error_captured: bool = False,
    ) -> None:
        """
        Initialize node execution result.

        Args:
            success: Whether execution succeeded
            result: Result dictionary from node
            execution_time: Execution time in seconds
            error_captured: Whether error was captured by try-catch
        """
        self.success = success
        self.result = result
        self.execution_time = execution_time
        self.error_captured = error_captured


class NodeExecutor:
    """
    Executes individual nodes with proper lifecycle management.

    Responsibilities:
    - Execute nodes with timeout
    - Validate nodes before execution
    - Track execution metrics
    - Emit lifecycle events
    - Handle bypassed/disabled nodes
    """

    def __init__(
        self,
        context: ExecutionContext,
        event_bus: Optional[EventBus] = None,
        node_timeout: float = 120.0,
        progress_calculator: Optional[callable] = None,
    ) -> None:
        """
        Initialize node executor.

        Args:
            context: Execution context with resources and variables
            event_bus: Optional event bus for lifecycle events
            node_timeout: Timeout for individual node execution in seconds
            progress_calculator: Optional callable to calculate progress percentage
        """
        self.context = context
        self.event_bus = event_bus
        self.node_timeout = node_timeout
        self._calculate_progress = progress_calculator or (lambda: 0.0)

    def _emit_event(
        self, event_type: EventType, data: Dict[str, Any], node_id: Optional[str] = None
    ) -> None:
        """
        Emit an event to the event bus.

        Args:
            event_type: Type of event
            data: Event data payload
            node_id: Optional node ID associated with event
        """
        if self.event_bus:
            event = Event(
                event_type=event_type,
                data=data,
                node_id=node_id,
            )
            self.event_bus.publish(event)

    async def execute(self, node: Any) -> NodeExecutionResult:
        """
        Execute a single node with full lifecycle management.

        Args:
            node: The node instance to execute

        Returns:
            NodeExecutionResult with success status and result data
        """
        # Check if node is disabled (bypassed)
        if node.config.get("_disabled", False):
            return self._handle_bypassed_node(node)

        # Setup execution tracking
        node.status = NodeStatus.RUNNING
        self.context.set_current_node(node.node_id)

        self._emit_event(
            EventType.NODE_STARTED,
            {"node_id": node.node_id, "node_type": node.__class__.__name__},
            node.node_id,
        )

        start_time = time.time()
        node_type = node.__class__.__name__

        # Record metrics start
        get_metrics().record_node_start(node_type, node.node_id)

        try:
            # Validate node before execution
            validation_result = self._validate_node(node, start_time)
            if validation_result is not None:
                return validation_result

            # Execute the node
            result = await self._execute_with_timeout(node)
            execution_time = time.time() - start_time

            # Update debug info
            node.execution_count += 1
            node.last_execution_time = execution_time
            node.last_output = result

            # Handle result
            return self._process_result(node, result, execution_time)

        except Exception as e:
            return self._handle_exception(node, e, start_time)

    def _handle_bypassed_node(self, node: Any) -> NodeExecutionResult:
        """
        Handle execution of a bypassed/disabled node.

        Passes through input values to matching output ports so data flow
        continues through disabled nodes in a chain.

        Args:
            node: The bypassed node

        Returns:
            Success result with bypassed flag
        """
        logger.info(f"Node {node.node_id} is disabled - bypassing execution")
        node.status = NodeStatus.SUCCESS

        # Pass through input values to matching output ports
        # This ensures data flows through disabled nodes in a chain
        passthrough_count = 0
        if hasattr(node, "input_ports") and hasattr(node, "output_ports"):
            for port_name in node.input_ports:
                # Skip exec ports
                if port_name.startswith("exec"):
                    continue
                # Check if there's a matching output port (e.g., page -> page, fields_in -> fields_out)
                input_value = node.get_input_value(port_name)
                if input_value is not None:
                    # Direct match (page -> page)
                    if port_name in node.output_ports:
                        node.set_output_value(port_name, input_value)
                        passthrough_count += 1
                        logger.debug(f"Bypass passthrough: {port_name} -> {port_name}")
                    # fields_in -> fields_out pattern
                    elif port_name.endswith("_in"):
                        out_port = port_name.replace("_in", "_out")
                        if out_port in node.output_ports:
                            node.set_output_value(out_port, input_value)
                            passthrough_count += 1
                            logger.debug(
                                f"Bypass passthrough: {port_name} -> {out_port}"
                            )

        if passthrough_count > 0:
            logger.debug(
                f"Bypassed node {node.node_id}: passed through {passthrough_count} values"
            )

        self._emit_event(
            EventType.NODE_COMPLETED,
            {
                "node_id": node.node_id,
                "node_type": node.__class__.__name__,
                "bypassed": True,
                "execution_time": 0,
                "progress": self._calculate_progress(),
            },
            node.node_id,
        )

        return NodeExecutionResult(
            success=True,
            result={
                "success": True,
                "bypassed": True,
                "passthrough_count": passthrough_count,
            },
            execution_time=0.0,
        )

    def _validate_node(
        self, node: Any, start_time: float
    ) -> Optional[NodeExecutionResult]:
        """
        Validate node before execution.

        Args:
            node: The node to validate
            start_time: Execution start time

        Returns:
            NodeExecutionResult if validation fails, None if valid
        """
        # validate() returns tuple (is_valid: bool, error_message: Optional[str])
        is_valid, validation_error = node.validate()
        if not is_valid:
            error_msg = validation_error or "Validation failed"
            logger.error(f"Node validation failed: {node.node_id} - {error_msg}")
            node.status = NodeStatus.ERROR
            execution_time = time.time() - start_time

            self._emit_event(
                EventType.NODE_ERROR,
                {"node_id": node.node_id, "error": error_msg},
                node.node_id,
            )

            return NodeExecutionResult(
                success=False,
                result=None,
                execution_time=execution_time,
            )

        return None  # Validation passed

    async def _execute_with_timeout(self, node: Any) -> Dict[str, Any]:
        """
        Execute node with timeout.

        Args:
            node: The node to execute

        Returns:
            Execution result dictionary

        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        try:
            result = await asyncio.wait_for(
                node.execute(self.context), timeout=self.node_timeout
            )
            return result or {"success": False, "error": "No result returned"}
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f"Node {node.node_id} timed out after {self.node_timeout}s"
            )

    def _process_result(
        self, node: Any, result: Optional[Dict[str, Any]], execution_time: float
    ) -> NodeExecutionResult:
        """
        Process execution result and update node status.

        Args:
            node: The executed node
            result: Execution result dictionary
            execution_time: Execution time in seconds

        Returns:
            NodeExecutionResult
        """
        node_type = node.__class__.__name__

        # Handle None result explicitly
        if result is None:
            result = {
                "success": False,
                "error": f"Node {node.node_id} ({node_type}) returned None instead of result dict",
            }
            logger.error(result["error"])

        # Handle success
        if result.get("success", False):
            node.status = NodeStatus.SUCCESS

            self._emit_event(
                EventType.NODE_COMPLETED,
                {
                    "node_id": node.node_id,
                    "message": result.get("data", {}).get("message", "Completed"),
                    "progress": self._calculate_progress(),
                    "execution_time": execution_time,
                },
                node.node_id,
            )

            # Record successful execution in metrics
            get_metrics().record_node_complete(
                node_type, node.node_id, execution_time * 1000, success=True
            )

            return NodeExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
            )

        # Handle failure
        node.status = NodeStatus.ERROR
        error_msg = result.get("error", "Unknown error")

        self._emit_event(
            EventType.NODE_ERROR,
            {
                "node_id": node.node_id,
                "error": error_msg,
                "execution_time": execution_time,
            },
            node.node_id,
        )

        logger.error(f"Node execution failed: {node.node_id} - {error_msg}")

        # Record failed execution in metrics
        get_metrics().record_node_complete(
            node_type, node.node_id, execution_time * 1000, success=False
        )

        return NodeExecutionResult(
            success=False,
            result=result,
            execution_time=execution_time,
        )

    def _handle_exception(
        self, node: Any, exception: Exception, start_time: float
    ) -> NodeExecutionResult:
        """
        Handle exception during node execution.

        Args:
            node: The node that raised exception
            exception: The exception raised
            start_time: Execution start time

        Returns:
            NodeExecutionResult with error information
        """
        node.status = NodeStatus.ERROR
        error_msg = str(exception)
        execution_time = time.time() - start_time
        node_type = node.__class__.__name__

        self._emit_event(
            EventType.NODE_ERROR,
            {
                "node_id": node.node_id,
                "error": error_msg,
                "execution_time": execution_time,
            },
            node.node_id,
        )

        logger.exception(f"Exception during node execution: {node.node_id}")

        # Record exception in metrics
        get_metrics().record_node_complete(
            node_type, node.node_id, execution_time * 1000, success=False
        )

        return NodeExecutionResult(
            success=False,
            result={"success": False, "error": error_msg},
            execution_time=execution_time,
        )


class NodeExecutorWithTryCatch(NodeExecutor):
    """
    Extended NodeExecutor with try-catch block error capture.

    Handles error capture for nodes inside try-catch blocks,
    allowing errors to be routed to catch nodes instead of
    failing the workflow.
    """

    def __init__(
        self,
        context: ExecutionContext,
        event_bus: Optional[EventBus] = None,
        node_timeout: float = 120.0,
        progress_calculator: Optional[callable] = None,
        error_capturer: Optional[callable] = None,
    ) -> None:
        """
        Initialize node executor with try-catch support.

        Args:
            context: Execution context
            event_bus: Optional event bus for events
            node_timeout: Timeout for node execution
            progress_calculator: Optional callable for progress
            error_capturer: Callable to capture errors in try blocks
        """
        super().__init__(context, event_bus, node_timeout, progress_calculator)
        self._capture_error = error_capturer or (lambda *args: False)

    def _handle_exception(
        self, node: Any, exception: Exception, start_time: float
    ) -> NodeExecutionResult:
        """
        Handle exception with try-catch error capture.

        Args:
            node: The node that raised exception
            exception: The exception raised
            start_time: Execution start time

        Returns:
            NodeExecutionResult with error information
        """
        node.status = NodeStatus.ERROR
        error_msg = str(exception)
        execution_time = time.time() - start_time
        node_type = node.__class__.__name__

        # Check if we're inside a try block - capture error for catch
        error_captured = self._capture_error(
            error_msg, type(exception).__name__, exception
        )

        if not error_captured:
            self._emit_event(
                EventType.NODE_ERROR,
                {
                    "node_id": node.node_id,
                    "error": error_msg,
                    "execution_time": execution_time,
                },
                node.node_id,
            )
            logger.exception(f"Exception during node execution: {node.node_id}")
        else:
            logger.info(
                f"Exception captured by try block: {node.node_id} - {error_msg}"
            )

        # Record exception in metrics
        get_metrics().record_node_complete(
            node_type, node.node_id, execution_time * 1000, success=False
        )

        # If error was captured by try block, return success with special marker
        if error_captured:
            return NodeExecutionResult(
                success=True,
                result={"success": True, "error_captured": True},
                execution_time=execution_time,
                error_captured=True,
            )

        return NodeExecutionResult(
            success=False,
            result={"success": False, "error": error_msg},
            execution_time=execution_time,
        )
