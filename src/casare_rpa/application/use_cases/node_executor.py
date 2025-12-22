"""
CasareRPA - Node Executor

Handles individual node execution including:
- Node validation and execution with timeout
- Status tracking and metrics recording
- Event emission for node lifecycle
- Bypass handling for disabled nodes

Entry Points:
    - NodeExecutor: Basic node execution with lifecycle management
    - NodeExecutorWithTryCatch: Extended with try-catch error capture
    - NodeExecutionResult: Typed result wrapper

Key Patterns:
    - NODE LIFECYCLE: IDLE -> RUNNING -> SUCCESS/ERROR -> (reset to IDLE for loops)
    - BYPASS PATTERN: Disabled nodes pass-through inputs to matching outputs
    - ERROR CAPTURE: Try-catch blocks intercept errors for routing to CatchNode

Result Pattern:
    Methods with *_safe suffix return Result[T, E] instead of raising exceptions.
    This enables explicit error handling at call sites:

        result = await executor.execute_safe(node)
        if result.is_ok():
            exec_result = result.unwrap()
        else:
            error = result.error  # NodeExecutionError with context

Extracted from ExecuteWorkflowUseCase for Single Responsibility.

Related:
    - See domain.interfaces.INode for node protocol
    - See domain.interfaces.IExecutionContext for context services
    - See execute_workflow.py for orchestration logic
    - See domain/errors/result.py for Result type documentation
"""

import asyncio
import re
import time
from typing import Any, Callable, Dict, Optional

from loguru import logger

from casare_rpa.domain.events import (
    EventBus,
    NodeStarted,
    NodeCompleted,
    NodeFailed,
)
from casare_rpa.domain.value_objects.types import DataType, NodeStatus

# Interface for type hints (dependency inversion)
from casare_rpa.domain.interfaces import IExecutionContext, INode
from casare_rpa.utils.performance.performance_metrics import get_metrics

# Result pattern for explicit error handling
from casare_rpa.domain.errors import (
    Result,
    Ok,
    Err,
    NodeExecutionError,
    NodeTimeoutError,
    NodeValidationError,
    ErrorContext,
)
from casare_rpa.infrastructure.cache.manager import TieredCacheManager
from casare_rpa.infrastructure.cache.keys import CacheKeyGenerator


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
        context: IExecutionContext,
        event_bus: Optional[EventBus] = None,
        node_timeout: float = 120.0,
        progress_calculator: Optional[Callable[[], float]] = None,
        cache_manager: Optional[TieredCacheManager] = None,
    ) -> None:
        """
        Initialize node executor.

        Args:
            context: IExecutionContext with resources and variables
            event_bus: Optional event bus for lifecycle events
            node_timeout: Timeout for individual node execution in seconds
            progress_calculator: Optional callable to calculate progress percentage

        Related:
            See domain.interfaces.IExecutionContext for context protocol
        """
        self.context = context
        self.event_bus = event_bus
        self.node_timeout = node_timeout
        self._calculate_progress = progress_calculator or (lambda: 0.0)
        self.cache_manager = cache_manager

        # PERFORMANCE: Cache metrics instance to avoid singleton lookup on every call
        # Related: See utils.performance.performance_metrics for metrics tracking
        self._metrics = get_metrics()

    def _publish_node_started(self, node: INode, node_type: str) -> None:
        """Publish NodeStarted event to the event bus."""
        if self.event_bus:
            self.event_bus.publish(
                NodeStarted(
                    node_id=node.node_id,
                    node_type=node_type,
                    workflow_id=getattr(self.context, "workflow_id", ""),
                )
            )

    def _publish_node_completed(
        self,
        node: INode,
        node_type: str,
        execution_time: float,
        outputs: Dict[str, Any],
    ) -> None:
        """Publish NodeCompleted event to the event bus."""
        if self.event_bus:
            self.event_bus.publish(
                NodeCompleted(
                    node_id=node.node_id,
                    node_type=node_type,
                    workflow_id=getattr(self.context, "workflow_id", ""),
                    execution_time_ms=execution_time * 1000,
                    output_data=outputs,
                )
            )

    def _publish_node_failed(self, node: INode, node_type: str, error_msg: str) -> None:
        """Publish NodeFailed event to the event bus."""
        if self.event_bus:
            self.event_bus.publish(
                NodeFailed(
                    node_id=node.node_id,
                    node_type=node_type,
                    workflow_id=getattr(self.context, "workflow_id", ""),
                    error_message=error_msg,
                )
            )

    def _get_node_display_name(self, node: INode) -> str:
        """
        Get a human-readable display name for a node.

        Priority:
            1. config["label"] - User-defined label in properties
            2. config["name"] - Alternative name field
            3. Cleaned node_type - Remove "Node" suffix and add spaces
        """
        # Check config for user-defined label/name
        label = node.config.get("label") or node.config.get("name")
        if label:
            return str(label)

        # Fall back to cleaned node type name
        node_type = node.__class__.__name__
        # Remove "Node" suffix and add spaces before capitals
        if node_type.endswith("Node"):
            node_type = node_type[:-4]
        # Add spaces before capital letters (e.g., "ClickElement" -> "Click Element")
        return re.sub(r"(?<!^)(?=[A-Z])", " ", node_type)

    def _get_node_cache_key(self, node: INode) -> str:
        """Generate a cache key for the node based on its inputs and config."""
        inputs = {}
        if hasattr(node, "input_ports"):
            for name in node.input_ports:
                if not name.startswith("exec"):
                    inputs[name] = node.get_input_value(name)

        cache_data = {
            "node_type": node.__class__.__name__,
            "inputs": inputs,
            "config": {k: v for k, v in node.config.items() if not k.startswith("_")},
        }
        workflow_id = getattr(self.context, "workflow_id", "unknown")
        return CacheKeyGenerator.generate(f"node:{workflow_id}", cache_data)

    async def execute(self, node: INode) -> NodeExecutionResult:
        """
        Execute a single node with full lifecycle management.

        EXECUTION LIFECYCLE:
        1. Check if node is disabled (bypass mode)
        2. Set status to RUNNING, emit NODE_STARTED event
        3. Validate node inputs/config
        4. Execute with timeout
        5. Process result, update status to SUCCESS or ERROR
        6. Emit NODE_COMPLETED or NODE_ERROR event
        7. Record metrics for performance dashboard

        Args:
            node: The node instance to execute (implements INode protocol)

        Returns:
            NodeExecutionResult with success status and result data

        Related:
            See domain.interfaces.INode for node protocol
            See execute_workflow._execute_from_node for orchestration
        """
        # BYPASS PATTERN: Disabled nodes pass-through inputs to matching outputs
        # This allows disabling nodes during debugging without breaking data flow
        if node.config.get("_disabled", False):
            return self._handle_bypassed_node(node)

        # Check cache if node is cacheable (via code or user toggle)
        cache_key = None
        is_cacheable = getattr(node, "cacheable", False) or node.config.get("_cache_enabled", False)
        if self.cache_manager and is_cacheable:
            cache_key = self._get_node_cache_key(node)
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for node {node.node_id} ({node.__class__.__name__})")
                node.status = NodeStatus.SUCCESS
                node.last_output = cached_result
                # Set outputs from cache
                for port_name, value in cached_result.items():
                    if port_name in node.output_ports:
                        node.set_output_value(port_name, value)
                return NodeExecutionResult(success=True, result=cached_result)

        # Setup execution tracking
        node.status = NodeStatus.RUNNING
        self.context.set_current_node(node.node_id)

        node_type = node.__class__.__name__
        self._get_node_display_name(node)

        self._publish_node_started(node, node_type)

        start_time = time.time()

        # Record metrics start (using cached instance)
        self._metrics.record_node_start(node_type, node.node_id)

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

            # Store in cache if cacheable
            if cache_key and self.cache_manager and result:
                await self.cache_manager.set(
                    cache_key, result, ttl=getattr(node, "cache_ttl", 3600)
                )

            # Handle result
            return self._process_result(node, result, execution_time)

        except Exception as e:
            return self._handle_exception(node, e, start_time)

    def _handle_bypassed_node(self, node: INode) -> NodeExecutionResult:
        """
        Handle execution of a bypassed/disabled node.

        BYPASS LOGIC:
        1. Mark node as SUCCESS (so it doesn't block the workflow)
        2. Pass-through input values to matching output ports
        3. Support two naming patterns:
           - Direct match: page -> page
           - Suffix pattern: fields_in -> fields_out

        This ensures data flows through disabled nodes in a chain,
        enabling users to disable nodes during debugging without
        breaking the data flow to downstream nodes.

        Args:
            node: The bypassed node (implements INode)

        Returns:
            Success result with bypassed flag and passthrough count
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
                            logger.debug(f"Bypass passthrough: {port_name} -> {out_port}")

        if passthrough_count > 0:
            logger.debug(f"Bypassed node {node.node_id}: passed through {passthrough_count} values")

        self._publish_node_completed(
            node,
            node.__class__.__name__,
            0.0,
            {"bypassed": True, "passthrough_count": passthrough_count},
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

    def _validate_node(self, node: INode, start_time: float) -> Optional[NodeExecutionResult]:
        """
        Validate node before execution.

        VALIDATION CHECKS:
        - Required input ports have values (from port OR config - dual-source pattern)
        - Node-specific config validation via _validate_config()

        Args:
            node: The node to validate (implements INode)
            start_time: Execution start time (for timing metrics)

        Returns:
            NodeExecutionResult if validation fails, None if valid

        Related:
            See domain.entities.base_node.validate() for validation logic
        """
        # DUAL-SOURCE PATTERN: validate() checks both port values AND config
        # This supports values coming from either port connections or properties panel
        is_valid, validation_error = node.validate()
        if not is_valid:
            error_msg = validation_error or "Validation failed"
            logger.error(f"Node validation failed: {node.node_id} - {error_msg}")
            node.status = NodeStatus.ERROR
            execution_time = time.time() - start_time

            self._publish_node_failed(node, node.__class__.__name__, error_msg)

            return NodeExecutionResult(
                success=False,
                result=None,
                execution_time=execution_time,
            )

        return None  # Validation passed

    async def _execute_with_timeout(self, node: INode) -> Dict[str, Any]:
        """
        Execute node with timeout.

        TIMEOUT BEHAVIOR:
        - Wraps node.execute() in asyncio.wait_for()
        - Default timeout is 120 seconds (configurable via settings)
        - Timeout raises asyncio.TimeoutError which is caught by _handle_exception

        Args:
            node: The node to execute (implements INode)

        Returns:
            Execution result dictionary from node.execute()

        Raises:
            asyncio.TimeoutError: If execution exceeds timeout

        Related:
            See domain.entities.base_node.execute() for expected result format
        """
        try:
            # NODE CONTRACT: execute() must return ExecutionResult dict
            # Expected: {"success": True/False, "data": {...}, "error": "..."}
            logger.debug(
                f"NodeExecutor: executing {node.__class__.__name__} ({node.node_id}) "
                f"with context_id={id(self.context)}"
            )

            # Inject execution context for auto-resolution in get_parameter()
            # This enables nodes to use get_parameter() without manual resolve_value calls
            if hasattr(node, "set_execution_context"):
                node.set_execution_context(self.context)

            try:
                result = await asyncio.wait_for(
                    node.execute(self.context), timeout=self.node_timeout
                )
            finally:
                # Clear context to prevent memory leaks and stale references
                if hasattr(node, "set_execution_context"):
                    node.set_execution_context(None)

            # EDGE CASE: Some nodes may return None instead of proper dict
            # Treat as failure to enforce the contract
            return result or {"success": False, "error": "No result returned"}
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Node {node.node_id} timed out after {self.node_timeout}s")

    def _process_result(
        self, node: INode, result: Optional[Dict[str, Any]], execution_time: float
    ) -> NodeExecutionResult:
        """
        Process execution result and update node status.

        RESULT PROCESSING:
        1. Handle None result (treat as error)
        2. Check success flag in result dict
        3. Update node status (SUCCESS or ERROR)
        4. Collect output port values for UI inspector
        5. Emit appropriate lifecycle event
        6. Record metrics for performance dashboard

        Args:
            node: The executed node (implements INode)
            result: Execution result dictionary
            execution_time: Execution time in seconds

        Returns:
            NodeExecutionResult wrapping the raw result with metadata
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

            # Collect output port values for output inspector
            outputs = {}
            if hasattr(node, "output_ports"):
                for port_name, port in node.output_ports.items():
                    # Skip EXEC ports - they're flow control, not data
                    if port.data_type != DataType.EXEC:
                        outputs[port_name] = port.value

            self._publish_node_completed(node, node_type, execution_time, outputs)

            # Record successful execution in metrics
            self._metrics.record_node_complete(
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

        self._publish_node_failed(node, node_type, error_msg)

        logger.error(f"Node execution failed: {node.node_id} - {error_msg}")

        # Record failed execution in metrics
        self._metrics.record_node_complete(
            node_type, node.node_id, execution_time * 1000, success=False
        )

        return NodeExecutionResult(
            success=False,
            result=result,
            execution_time=execution_time,
        )

    def _handle_exception(
        self, node: INode, exception: Exception, start_time: float
    ) -> NodeExecutionResult:
        """
        Handle exception during node execution.

        EXCEPTION HANDLING:
        - Exceptions from execute() indicate bugs, not expected failures
        - Nodes should return error results for expected failures
        - This catches TimeoutError, Playwright errors, system errors, etc.

        Args:
            node: The node that raised exception (implements INode)
            exception: The exception raised
            start_time: Execution start time (for timing metrics)

        Returns:
            NodeExecutionResult with error information

        Note:
            Subclass NodeExecutorWithTryCatch overrides this to support
            try-catch block error capture.
        """
        node.status = NodeStatus.ERROR
        error_msg = str(exception)
        execution_time = time.time() - start_time
        node_type = node.__class__.__name__

        self._publish_node_failed(node, node_type, error_msg)

        logger.exception(f"Exception during node execution: {node.node_id}")

        # Record exception in metrics
        self._metrics.record_node_complete(
            node_type, node.node_id, execution_time * 1000, success=False
        )

        return NodeExecutionResult(
            success=False,
            result={"success": False, "error": error_msg},
            execution_time=execution_time,
        )

    # ========================================================================
    # RESULT PATTERN - Safe variants for explicit error handling
    # ========================================================================

    async def execute_safe(self, node: INode) -> Result[NodeExecutionResult, NodeExecutionError]:
        """
        Execute a single node with Result-based error handling.

        Result pattern variant of execute(). Returns Ok with NodeExecutionResult
        on successful execution (even if node result indicates failure), or
        Err with NodeExecutionError on infrastructure/unexpected failures.

        The distinction is:
        - Ok(NodeExecutionResult(success=False)) - Node executed but failed logically
        - Err(NodeExecutionError) - Node couldn't execute (timeout, infrastructure error)

        Args:
            node: The node instance to execute

        Returns:
            Ok(NodeExecutionResult) on successful execution (check .success for logic status)
            Err(NodeExecutionError) on infrastructure/unexpected failure
        """
        try:
            result = await self.execute(node)
            return Ok(result)
        except asyncio.TimeoutError as e:
            # Timeout is a distinct error type for retry decisions
            return Err(
                NodeTimeoutError(
                    message=f"Node execution timed out after {self.node_timeout}s",
                    node_id=node.node_id,
                    node_type=node.__class__.__name__,
                    timeout_ms=int(self.node_timeout * 1000),
                    context=ErrorContext(
                        component="NodeExecutor",
                        operation="execute_safe",
                        details={"timeout_s": self.node_timeout},
                    ),
                    original_error=e,
                )
            )
        except Exception as e:
            return Err(
                NodeExecutionError(
                    message=f"Unexpected error during node execution: {e}",
                    node_id=node.node_id,
                    node_type=node.__class__.__name__,
                    context=ErrorContext(
                        component="NodeExecutor",
                        operation="execute_safe",
                        details={"error_type": type(e).__name__},
                    ),
                    original_error=e,
                )
            )

    def validate_node_safe(self, node: INode) -> Result[None, NodeValidationError]:
        """
        Validate node before execution with explicit error handling.

        Result pattern variant of _validate_node(). Returns Ok(None) if
        validation passes, Err(NodeValidationError) if validation fails.

        Args:
            node: The node to validate

        Returns:
            Ok(None) if validation passes
            Err(NodeValidationError) if validation fails
        """
        is_valid, validation_error = node.validate()
        if is_valid:
            return Ok(None)

        return Err(
            NodeValidationError(
                message=validation_error or "Validation failed",
                node_id=node.node_id,
                node_type=node.__class__.__name__,
                context=ErrorContext(
                    component="NodeExecutor",
                    operation="validate_node_safe",
                    details={"node_name": getattr(node, "name", node.node_id)},
                ),
            )
        )

    async def execute_with_timeout_safe(
        self, node: INode
    ) -> Result[Dict[str, Any], NodeExecutionError]:
        """
        Execute node with timeout and explicit error handling.

        Result pattern variant of _execute_with_timeout(). Returns Ok with
        result dict on success, Err on timeout or other failure.

        Args:
            node: The node to execute

        Returns:
            Ok(result_dict) on success
            Err(NodeTimeoutError) on timeout
            Err(NodeExecutionError) on other failures
        """
        try:
            # Inject execution context for auto-resolution in get_parameter()
            if hasattr(node, "set_execution_context"):
                node.set_execution_context(self.context)

            try:
                result = await asyncio.wait_for(
                    node.execute(self.context), timeout=self.node_timeout
                )
            finally:
                # Clear context to prevent memory leaks
                if hasattr(node, "set_execution_context"):
                    node.set_execution_context(None)

            # Handle None result explicitly
            if result is None:
                return Err(
                    NodeExecutionError(
                        message="Node returned None instead of result dict",
                        node_id=node.node_id,
                        node_type=node.__class__.__name__,
                        error_code="NULL_RESULT",
                        context=ErrorContext(
                            component="NodeExecutor",
                            operation="execute_with_timeout_safe",
                            details={},
                        ),
                    )
                )
            return Ok(result)
        except asyncio.TimeoutError as e:
            return Err(
                NodeTimeoutError(
                    message=f"Node timed out after {self.node_timeout}s",
                    node_id=node.node_id,
                    node_type=node.__class__.__name__,
                    timeout_ms=int(self.node_timeout * 1000),
                    context=ErrorContext(
                        component="NodeExecutor",
                        operation="execute_with_timeout_safe",
                        details={"timeout_s": self.node_timeout},
                    ),
                    original_error=e,
                )
            )
        except Exception as e:
            return Err(
                NodeExecutionError(
                    message=str(e),
                    node_id=node.node_id,
                    node_type=node.__class__.__name__,
                    context=ErrorContext(
                        component="NodeExecutor",
                        operation="execute_with_timeout_safe",
                        details={"error_type": type(e).__name__},
                    ),
                    original_error=e,
                )
            )


class NodeExecutorWithTryCatch(NodeExecutor):
    """
    Extended NodeExecutor with try-catch block error capture.

    TRY-CATCH PATTERN:
    - When a node is inside a try block, errors are captured instead of failing
    - The error is stored in try_state variable for the CatchNode to access
    - Execution routes to the CatchNode instead of stopping the workflow
    - This enables UiPath/Power Automate style error handling

    Handles error capture for nodes inside try-catch blocks,
    allowing errors to be routed to catch nodes instead of
    failing the workflow.

    Related:
        See variable_resolver.TryCatchErrorHandler for error capture logic
        See nodes/control_flow/try_catch.py for TryCatch nodes
    """

    def __init__(
        self,
        context: IExecutionContext,
        event_bus: Optional[EventBus] = None,
        node_timeout: float = 120.0,
        progress_calculator: Optional[Callable[[], float]] = None,
        error_capturer: Optional[Callable[..., bool]] = None,
    ) -> None:
        """
        Initialize node executor with try-catch support.

        Args:
            context: IExecutionContext instance
            event_bus: Optional event bus for events
            node_timeout: Timeout for node execution
            progress_calculator: Optional callable for progress
            error_capturer: Callable to capture errors in try blocks
                           Returns True if error was captured, False otherwise
        """
        super().__init__(context, event_bus, node_timeout, progress_calculator)
        # ERROR CAPTURE: This callable checks if we're in a try block
        # and stores the error in the try_state variable if so
        self._capture_error = error_capturer or (lambda *args: False)

    def _handle_exception(
        self, node: INode, exception: Exception, start_time: float
    ) -> NodeExecutionResult:
        """
        Handle exception with try-catch error capture.

        TRY-CATCH EXCEPTION FLOW:
        1. Check if we're inside a try block (via _capture_error callback)
        2. If captured: store error in try_state, return success with error_captured=True
        3. If not captured: emit error event, return failure

        When error is captured, the orchestrator will route to the CatchNode
        based on the error_captured flag in the result.

        Args:
            node: The node that raised exception (implements INode)
            exception: The exception raised
            start_time: Execution start time

        Returns:
            NodeExecutionResult - success if error captured, failure otherwise

        Related:
            See execute_workflow._handle_special_results for routing logic
        """
        node.status = NodeStatus.ERROR
        error_msg = str(exception)
        execution_time = time.time() - start_time
        node_type = node.__class__.__name__

        # Check if we're inside a try block - capture error for catch
        error_captured = self._capture_error(error_msg, type(exception).__name__, exception)

        if not error_captured:
            self._publish_node_failed(node, node_type, error_msg)
            logger.exception(f"Exception during node execution: {node.node_id}")
        else:
            logger.info(f"Exception captured by try block: {node.node_id} - {error_msg}")

        # Record exception in metrics
        self._metrics.record_node_complete(
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
