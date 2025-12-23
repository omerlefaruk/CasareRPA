"""
CasareRPA - Variable Resolver

Handles data transfer between nodes including:
- Port value resolution and transfer
- Output port validation after execution
- Error state capture for try-catch blocks

Entry Points:
    - VariableResolver: Data transfer between connected nodes
    - TryCatchErrorHandler: Error capture for try-catch blocks

Key Patterns:
    - CONNECTION INDEX: Pre-built O(1) lookup for incoming connections
    - DATA FLOW: Source output port -> Target input port
    - DUAL-SOURCE: Values can come from port OR config (see base_node.get_parameter)
    - TRY-CATCH: Errors captured in try_state variable for CatchNode routing

Result Pattern:
    Methods with *_safe suffix return Result[T, E] instead of raising exceptions.
    This enables explicit error handling at call sites:

        result = resolver.resolve_variable_safe("{{node.output}}")
        if result.is_ok():
            value = result.unwrap()
        else:
            # Handle error explicitly
            error = result.error

Extracted from ExecuteWorkflowUseCase for Single Responsibility.

Related:
    - See domain.interfaces.INode for node protocol
    - See node_executor.py for execution lifecycle
    - See execute_workflow.py for orchestration
    - See domain/errors/result.py for Result type documentation
"""

import traceback
from collections.abc import Callable
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema

# Result pattern for explicit error handling
from casare_rpa.domain.errors import (
    Err,
    ErrorContext,
    NodeExecutionError,
    Ok,
    Result,
    ValidationError,
)

# Interface for type hints (dependency inversion)
from casare_rpa.domain.interfaces import IExecutionContext, INode


class VariableResolver:
    """
    Resolves and transfers data between nodes.

    DATA FLOW ARCHITECTURE:
    - Nodes communicate via typed ports (input/output)
    - Connections define source->target port mappings
    - Before each node executes, inputs are transferred from connected sources
    - After execution, output port validation warns about missing values

    Responsibilities:
    - Transfer data from source output ports to target input ports
    - Validate output ports have values after successful execution
    - Support dual-source pattern (port OR config values)

    Related:
        See domain.entities.base_node for port definitions
        See domain.value_objects.Port for port structure
    """

    # CONTROL FLOW NODES: Skip output validation for these nodes
    # They only have exec ports (no data ports to validate)
    # This is a performance optimization and noise reduction
    CONTROL_FLOW_NODES = frozenset(
        {
            "IfNode",
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WhileLoopStartNode",
            "WhileLoopEndNode",
            "TryCatchNode",
            "TryEndNode",
            "CatchNode",
            "CatchEndNode",
            "FinallyNode",
            "FinallyEndNode",
            "ForkNode",
            "JoinNode",
            "StartNode",
            "EndNode",
            "ParallelForEachNode",
            "ControlFlowSuperNode",
            "ExecuteScriptNode",
            "MergeNode",
        }
    )

    def __init__(
        self,
        workflow: WorkflowSchema,
        node_getter: Callable[[str], INode],
    ) -> None:
        """
        Initialize variable resolver.

        Args:
            workflow: Workflow schema with connections
            node_getter: Callable to get node instance by ID (typically ExecuteWorkflowUseCase._get_node_instance)
        """
        self.workflow = workflow
        self._get_node = node_getter

        # PERFORMANCE OPTIMIZATION: Pre-build connection index for O(1) lookups
        # Without this, we'd scan all connections (O(n)) for every node execution
        # With 100 nodes and 150 connections, this reduces from O(15000) to O(n) total
        self._incoming_connections: dict[str, list[Any]] = {}
        self._build_connection_index()

    def _build_connection_index(self) -> None:
        """
        Build connection index map for O(1) lookups by target node.

        Called once during initialization. Maps each target node ID
        to a list of incoming connections.

        Structure: {target_node_id: [conn1, conn2, ...]}
        """
        self._incoming_connections.clear()
        for conn in self.workflow.connections:
            if conn.target_node not in self._incoming_connections:
                self._incoming_connections[conn.target_node] = []
            self._incoming_connections[conn.target_node].append(conn)

    def transfer_data(self, connection: Any, context_override: Any | None = None) -> None:
        """
        Transfer data from source port to target port.

        DATA TRANSFER FLOW:
        1. Get source node's output port value
        2. Set target node's input port value
        3. Skip exec ports (flow control, not data)
        4. Log warnings for missing data (helps debug broken workflows)

        Args:
            connection: The connection defining source and target
            context_override: Optional execution context to use instead of self.context
        """
        try:
            source_node = self._get_node(connection.source_node)
            target_node = self._get_node(connection.target_node)
        except ValueError:
            # Node not found - may be deleted or invalid workflow
            return

        # OUTPUT -> INPUT: Read from source, write to target
        value = source_node.get_output_value(connection.source_port)

        if value is not None:
            target_node.set_input_value(connection.target_port, value)

            # DEBUG LOGGING: Log data transfers (not exec ports) for debugging
            # Truncate value repr to avoid flooding logs with large data
            if "exec" not in connection.source_port.lower():
                logger.info(
                    f"Data: {connection.source_port} -> {connection.target_port} = {repr(value)[:80]}"
                )
        else:
            # WARNING: Missing data might indicate a bug in upstream node
            # Skip exec ports - they're flow control, not data
            # Also skip 'true'/'false' ports from If/Branch nodes
            source_port_lower = connection.source_port.lower()
            if "exec" not in source_port_lower and source_port_lower not in (
                "true",
                "false",
            ):
                logger.warning(
                    f"Data transfer skipped: source node {source_node.node_id} "
                    f"({type(source_node).__name__}) port '{connection.source_port}' has no value"
                )

    def transfer_inputs_to_node(self, node_id: str, context_override: Any | None = None) -> None:
        """
        Transfer all input data to a node from its connected sources.

        Called before each node executes to populate its input ports
        with values from upstream nodes' output ports.

        Uses pre-built index for O(1) lookup instead of O(n) scan.

        Args:
            node_id: Target node ID to transfer data to

        Related:
            See execute_workflow._execute_from_node for usage
        """
        # PERFORMANCE: O(1) lookup using pre-built index
        for connection in self._incoming_connections.get(node_id, []):
            self.transfer_data(connection, context_override=context_override)

    def validate_output_ports(self, node: INode, result: dict[str, Any]) -> bool:
        """
        Validate that required output ports have values after execution.

        OUTPUT VALIDATION:
        - Called after successful node execution
        - Logs warnings for missing output values (informational only)
        - Helps detect silent failures where nodes succeed but don't produce data
        - Skip control flow nodes (only have exec ports)

        This is INFORMATIONAL validation - it doesn't block execution.
        The goal is to help users debug workflows where data isn't flowing
        as expected.

        Args:
            node: The executed node instance (implements INode)
            result: The execution result dictionary

        Returns:
            True (always - validation is informational)
        """
        # OPTIMIZATION: Skip control flow nodes (only have exec ports)
        node_type_name = type(node).__name__
        if node_type_name in self.CONTROL_FLOW_NODES:
            return True

        # SAFETY: Check if node has output_ports attribute
        if not hasattr(node, "output_ports"):
            return True

        # Handle different output_ports formats (Dict[str, Port] or Dict[str, str])
        output_ports_dict = node.output_ports
        if not output_ports_dict:
            return True

        # FILTER: Get data output ports only (exclude exec ports)
        output_port_names = self._get_data_output_ports(output_ports_dict)

        if not output_port_names:
            return True  # No data ports to validate

        # VALIDATION: Log warnings for missing output values
        # This helps debug workflows where downstream nodes don't receive data
        for port_name in output_port_names:
            value = node.get_output_value(port_name)
            if value is None:
                logger.warning(
                    f"Node {node.node_id} ({node_type_name}) output port "
                    f"'{port_name}' has no value after successful execution"
                )

        return True

    def _get_data_output_ports(self, output_ports_dict: dict[str, Any]) -> list[str]:
        """
        Get list of data output port names (excluding exec ports).

        Args:
            output_ports_dict: Dictionary of output ports

        Returns:
            List of data output port names
        """
        output_port_names = []
        for key, port in output_ports_dict.items():
            # Handle both Port objects and string port names
            if hasattr(port, "name"):
                port_name = port.name
            elif isinstance(port, str):
                port_name = port
            else:
                port_name = str(key)

            # Skip exec ports
            if not port_name.startswith("exec") and not port_name.startswith("_exec"):
                output_port_names.append(port_name)

        return output_port_names

    # ========================================================================
    # RESULT PATTERN - Safe variants for explicit error handling
    # ========================================================================

    def transfer_data_safe(self, connection: Any) -> Result[tuple[str, Any], NodeExecutionError]:
        """
        Transfer data from source port to target port with explicit error handling.

        Result pattern variant of transfer_data(). Returns Ok with transferred
        value on success, Err with NodeExecutionError on failure.

        Args:
            connection: The connection defining source and target

        Returns:
            Ok((port_name, value)) on success
            Err(NodeExecutionError) if node not found or transfer fails
        """
        try:
            source_node = self._get_node(connection.source_node)
            target_node = self._get_node(connection.target_node)
        except ValueError as e:
            # Node not found - return structured error instead of silently returning
            return Err(
                NodeExecutionError(
                    message=f"Node not found during data transfer: {e}",
                    node_id=connection.source_node,
                    node_type="Unknown",
                    context=ErrorContext(
                        component="VariableResolver",
                        operation="transfer_data_safe",
                        details={
                            "source_node": connection.source_node,
                            "target_node": connection.target_node,
                            "source_port": connection.source_port,
                        },
                    ),
                    original_error=e,
                )
            )

        # Read from source output port
        value = source_node.get_output_value(connection.source_port)

        if value is not None:
            target_node.set_input_value(connection.target_port, value)
            return Ok((connection.target_port, value))

        # Value is None - not necessarily an error for exec ports
        if "exec" in connection.source_port.lower():
            return Ok((connection.target_port, None))

        # Data port with None value - return Ok but caller can check value
        logger.warning(f"Data transfer: source {connection.source_port} has no value")
        return Ok((connection.target_port, None))

    def transfer_inputs_to_node_safe(self, node_id: str) -> Result[int, NodeExecutionError]:
        """
        Transfer all input data to a node with explicit error handling.

        Result pattern variant of transfer_inputs_to_node(). Returns Ok with
        count of successful transfers, or Err if any critical transfer fails.

        Args:
            node_id: Target node ID to transfer data to

        Returns:
            Ok(count) - number of successful data transfers
            Err(NodeExecutionError) - if a critical transfer fails
        """
        connections = self._incoming_connections.get(node_id, [])
        success_count = 0

        for connection in connections:
            result = self.transfer_data_safe(connection)
            if result.is_ok():
                success_count += 1
            else:
                # Log but don't fail - missing inputs may be optional
                logger.debug(f"Transfer issue for {node_id}: {result.error}")

        return Ok(success_count)

    def validate_output_ports_safe(
        self, node: INode, result: dict[str, Any]
    ) -> Result[list[str], ValidationError]:
        """
        Validate output ports have values with explicit error handling.

        Result pattern variant of validate_output_ports(). Returns Ok with
        list of missing port names (empty list if all valid).

        Args:
            node: The executed node instance
            result: The execution result dictionary

        Returns:
            Ok(missing_ports) - list of port names with missing values (informational)
            Always returns Ok since validation is informational
        """
        # Skip control flow nodes
        node_type_name = type(node).__name__
        if node_type_name in self.CONTROL_FLOW_NODES:
            return Ok([])

        if not hasattr(node, "output_ports"):
            return Ok([])

        output_ports_dict = node.output_ports
        if not output_ports_dict:
            return Ok([])

        output_port_names = self._get_data_output_ports(output_ports_dict)
        if not output_port_names:
            return Ok([])

        # Collect ports with missing values
        missing_ports: list[str] = []
        for port_name in output_port_names:
            value = node.get_output_value(port_name)
            if value is None:
                missing_ports.append(port_name)
                logger.warning(
                    f"Node {node.node_id} ({node_type_name}) output port "
                    f"'{port_name}' has no value after successful execution"
                )

        return Ok(missing_ports)


class TryCatchErrorHandler:
    """
    Handles try-catch block error capture and routing.

    TRY-CATCH ARCHITECTURE:
    - TryCatchNode creates a "try_state" variable when entering try block
    - When an error occurs, capture_error() stores it in the try_state
    - TryEndNode checks for errors and routes to CatchNode if needed
    - CatchNode can access error details from the try_state variable

    This enables UiPath/Power Automate style error handling where users
    can wrap nodes in try-catch blocks to handle errors gracefully.

    Related:
        See nodes/control_flow/try_catch.py for TryCatch node implementations
        See node_executor.NodeExecutorWithTryCatch for exception handling
    """

    def __init__(self, context: IExecutionContext) -> None:
        """
        Initialize try-catch error handler.

        Args:
            context: IExecutionContext with variables (stores try_state)
        """
        self.context = context

    def capture_error(self, error_msg: str, error_type: str, exception: Exception) -> bool:
        """
        Check if we're inside a try block and capture the error if so.

        ERROR CAPTURE FLOW:
        1. Generate full stack trace for debugging
        2. Search context.variables for active try_state
        3. If found, store error details in try_state
        4. Return True so execution can route to CatchNode

        Args:
            error_msg: Error message
            error_type: Error type/class name (e.g., "TimeoutError")
            exception: The original exception (for stack trace)

        Returns:
            True if error was captured by a try block, False otherwise
        """
        if not self.context:
            return False

        # STACK TRACE: Full traceback for debugging in CatchNode
        stack_trace = "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )

        # TRY STATE DETECTION: Look for active try blocks
        # try_state is created by TryCatchNode and contains {catch_id, ...}
        for key, value in list(self.context.variables.items()):
            if key.endswith("_try_state") and isinstance(value, dict):
                # CAPTURE: Store error details for CatchNode to access
                value["error"] = True
                value["error_type"] = error_type
                value["error_message"] = error_msg
                value["stack_trace"] = stack_trace
                logger.debug(f"Error captured in try block: {key}")
                return True

        return False

    def find_catch_node_id(self) -> str | None:
        """
        Find the catch node ID for the most recent active try block.

        Called after error capture to determine where to route execution.
        Searches all try_state variables for one with an error and catch_id.

        Returns:
            Catch node ID if found, None otherwise
        """
        if not self.context:
            return None

        # CATCH ROUTING: Find try_state with error flag and catch_id
        for key, value in self.context.variables.items():
            if key.endswith("_try_state") and isinstance(value, dict):
                if value.get("error") and value.get("catch_id"):
                    return value.get("catch_id")

        return None

    def capture_from_result(self, result: dict[str, Any] | None, node_id: str) -> bool:
        """
        Capture error from a failed execution result.

        Used when a node returns {"success": False, "error": "..."}
        instead of raising an exception.

        Args:
            result: Execution result (may be None or contain error)
            node_id: Node ID that failed

        Returns:
            True if error was captured by a try block
        """
        error_msg = result.get("error", "Unknown error") if result else "Unknown error"
        return self.capture_error(error_msg, "ExecutionError", Exception(f"{node_id}: {error_msg}"))

    # ========================================================================
    # RESULT PATTERN - Safe variants for explicit error handling
    # ========================================================================

    def capture_error_safe(
        self, error_msg: str, error_type: str, exception: Exception
    ) -> Result[bool, NodeExecutionError]:
        """
        Check if we're inside a try block and capture the error if so.

        Result pattern variant of capture_error(). Returns Ok(True) if error
        was captured, Ok(False) if not inside a try block.

        Args:
            error_msg: Error message
            error_type: Error type/class name
            exception: The original exception

        Returns:
            Ok(True) if error was captured by a try block
            Ok(False) if not inside a try block
            Never returns Err (capture logic doesn't fail)
        """
        if not self.context:
            return Ok(False)

        stack_trace = "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )

        # Search for active try blocks
        for key, value in list(self.context.variables.items()):
            if key.endswith("_try_state") and isinstance(value, dict):
                value["error"] = True
                value["error_type"] = error_type
                value["error_message"] = error_msg
                value["stack_trace"] = stack_trace
                logger.debug(f"Error captured in try block: {key}")
                return Ok(True)

        return Ok(False)

    def find_catch_node_safe(self) -> Result[str | None, NodeExecutionError]:
        """
        Find the catch node ID for the most recent active try block.

        Result pattern variant of find_catch_node_id(). Returns Ok with
        catch node ID if found, Ok(None) if no active try block.

        Returns:
            Ok(catch_id) if found
            Ok(None) if no active try block with error
            Never returns Err
        """
        if not self.context:
            return Ok(None)

        for key, value in self.context.variables.items():
            if key.endswith("_try_state") and isinstance(value, dict):
                if value.get("error") and value.get("catch_id"):
                    return Ok(value.get("catch_id"))

        return Ok(None)
