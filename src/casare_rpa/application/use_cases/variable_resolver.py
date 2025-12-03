"""
CasareRPA - Variable Resolver

Handles data transfer between nodes including:
- Port value resolution and transfer
- Output port validation after execution
- Error state capture for try-catch blocks

Extracted from ExecuteWorkflowUseCase for Single Responsibility.
"""

import traceback
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.infrastructure.execution import ExecutionContext


class VariableResolver:
    """
    Resolves and transfers data between nodes.

    Responsibilities:
    - Transfer data from source output ports to target input ports
    - Validate output ports have values after successful execution
    - Capture errors in try-catch block state
    """

    # Control flow nodes that only have exec ports (skip validation)
    CONTROL_FLOW_NODES = frozenset(
        {
            "IfNode",
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WhileLoopNode",
            "WhileEndNode",
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
        }
    )

    def __init__(
        self,
        workflow: WorkflowSchema,
        node_getter: callable,
    ) -> None:
        """
        Initialize variable resolver.

        Args:
            workflow: Workflow schema with connections
            node_getter: Callable to get node instance by ID
        """
        self.workflow = workflow
        self._get_node = node_getter

    def transfer_data(self, connection: Any) -> None:
        """
        Transfer data from source port to target port.

        Args:
            connection: The connection defining source and target
        """
        try:
            source_node = self._get_node(connection.source_node)
            target_node = self._get_node(connection.target_node)
        except ValueError:
            return

        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)

        # Set value to target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)

            # Log data transfers (non-exec) for debugging
            if "exec" not in connection.source_port.lower():
                logger.info(
                    f"Data: {connection.source_port} -> {connection.target_port} = {repr(value)[:80]}"
                )
        else:
            # Log warning when data transfer fails due to missing output value
            if "exec" not in connection.source_port.lower():
                logger.warning(
                    f"Data transfer skipped: source node {source_node.node_id} "
                    f"({type(source_node).__name__}) port '{connection.source_port}' has no value"
                )

    def transfer_inputs_to_node(self, node_id: str) -> None:
        """
        Transfer all input data to a node from its connected sources.

        Args:
            node_id: Target node ID to transfer data to
        """
        for connection in self.workflow.connections:
            if connection.target_node == node_id:
                self.transfer_data(connection)

    def validate_output_ports(self, node: Any, result: Dict[str, Any]) -> bool:
        """
        Validate that required output ports have values after execution.

        Logs warnings for output ports that have no value after successful execution.
        This helps detect silent failures where nodes succeed but don't produce expected data.

        Args:
            node: The executed node instance
            result: The execution result dictionary

        Returns:
            True (validation is informational, doesn't block execution)
        """
        # Skip validation for control flow nodes (only have exec ports)
        node_type_name = type(node).__name__
        if node_type_name in self.CONTROL_FLOW_NODES:
            return True

        # Check if node has output_ports attribute
        if not hasattr(node, "output_ports"):
            return True

        # Handle different output_ports formats (Dict[str, Port] or Dict[str, str])
        output_ports_dict = node.output_ports
        if not output_ports_dict:
            return True

        # Filter to data output ports (exclude exec ports)
        output_port_names = self._get_data_output_ports(output_ports_dict)

        if not output_port_names:
            return True  # No data ports to validate

        # Validate each output port has a value
        for port_name in output_port_names:
            value = node.get_output_value(port_name)
            if value is None:
                logger.warning(
                    f"Node {node.node_id} ({node_type_name}) output port "
                    f"'{port_name}' has no value after successful execution"
                )

        return True

    def _get_data_output_ports(self, output_ports_dict: Dict[str, Any]) -> List[str]:
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


class TryCatchErrorHandler:
    """
    Handles try-catch block error capture and routing.

    Extracted to separate error handling logic from execution flow.
    """

    def __init__(self, context: ExecutionContext) -> None:
        """
        Initialize try-catch error handler.

        Args:
            context: Execution context with variables
        """
        self.context = context

    def capture_error(
        self, error_msg: str, error_type: str, exception: Exception
    ) -> bool:
        """
        Check if we're inside a try block and capture the error if so.

        Args:
            error_msg: Error message
            error_type: Error type/class name
            exception: The original exception

        Returns:
            True if error was captured by a try block, False otherwise
        """
        if not self.context:
            return False

        # Generate stack trace
        stack_trace = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )

        # Find active try state(s) in context variables
        for key, value in list(self.context.variables.items()):
            if key.endswith("_try_state") and isinstance(value, dict):
                # Found an active try block - capture the error
                value["error"] = True
                value["error_type"] = error_type
                value["error_message"] = error_msg
                value["stack_trace"] = stack_trace
                logger.debug(f"Error captured in try block: {key}")
                return True

        return False

    def find_catch_node_id(self) -> Optional[str]:
        """
        Find the catch node ID for the most recent active try block.

        Returns:
            Catch node ID if found, None otherwise
        """
        if not self.context:
            return None

        for key, value in self.context.variables.items():
            if key.endswith("_try_state") and isinstance(value, dict):
                if value.get("error") and value.get("catch_id"):
                    return value.get("catch_id")

        return None

    def capture_from_result(
        self, result: Optional[Dict[str, Any]], node_id: str
    ) -> bool:
        """
        Capture error from a failed execution result.

        Args:
            result: Execution result (may be None or contain error)
            node_id: Node ID that failed

        Returns:
            True if error was captured by a try block
        """
        error_msg = result.get("error", "Unknown error") if result else "Unknown error"
        return self.capture_error(
            error_msg, "ExecutionError", Exception(f"{node_id}: {error_msg}")
        )
