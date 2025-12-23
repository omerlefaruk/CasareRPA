"""
CasareRPA - Error Handling Control Flow Nodes

Provides nodes for try/catch/finally error handling:
- TryNode: Start of error-protected execution block
- CatchNode: Error handler block
- FinallyNode: Cleanup block that always executes
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties()  # No config - paired with Catch/Finally
@node(category="control_flow", exec_outputs=["exec_out", "try_body"])
class TryNode(BaseNode):
    """
    Try block for error handling.

    Use with CatchNode and FinallyNode to create try/catch/finally blocks.
    When an error occurs in any node within the try body, execution routes
    to the CatchNode instead of failing the workflow.

    Layout: Try, Catch, Finally are placed side-by-side automatically.

    Outputs:
        - try_body: Execution flow for the try block (connect nodes here)
        - exec_out: Continues after try body completes (no error)
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in -> exec_out, try_body

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Try node."""
        super().__init__(node_id, config)
        self.name = "Try"
        self.node_type = "TryNode"
        # Paired nodes - set automatically when created together
        self.paired_catch_id: str = ""
        self.paired_finally_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")  # Main flow (top)
        self.add_exec_output("try_body")  # Try body (below)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute try - initializes error capture state."""
        self.status = NodeStatus.RUNNING

        try:
            # Initialize try state for error capture
            try_state_key = f"{self.node_id}_try_state"
            context.variables[try_state_key] = {
                "error": False,
                "error_type": None,
                "error_message": None,
                "stack_trace": None,
                "catch_id": self.paired_catch_id,
                "finally_id": self.paired_finally_id,
            }

            logger.debug(f"Try block started: {self.node_id}")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"try_state_key": try_state_key},
                "next_nodes": ["try_body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Try execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "paired_try_id",
        PropertyType.STRING,
        default="",
        label="Paired Try Node",
        tooltip="ID of the paired TryNode (set automatically)",
    ),
    PropertyDef(
        "error_types",
        PropertyType.STRING,
        default="",
        label="Error Types",
        tooltip="Comma-separated error types to catch (empty = catch all). E.g., 'ValueError,KeyError'",
    ),
)
@node(category="control_flow", exec_outputs=["catch_body"])
class CatchNode(BaseNode):
    """
    Catch block for handling errors from the Try block.

    Receives errors from the paired Try block and provides error details
    as output ports. Can filter by error type.

    Paired automatically with Try and Finally nodes when created together.

    Outputs:
        - catch_body: Execution flow for error handling
        - error_message: The error message string
        - error_type: The error type/class name
        - stack_trace: Full stack trace (if available)
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in -> catch_body, error_message, error_type, stack_trace

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Catch node."""
        super().__init__(node_id, config)
        self.name = "Catch"
        self.node_type = "CatchNode"
        # Paired automatically when created together - load from config
        self.paired_try_id: str = self.get_parameter("paired_try_id", "")
        self.paired_finally_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("catch_body")
        self.add_output_port("error_message", DataType.STRING)
        self.add_output_port("error_type", DataType.STRING)
        self.add_output_port("stack_trace", DataType.STRING)

    def set_paired_try(self, try_node_id: str) -> None:
        """Set the paired Try node ID (called automatically)."""
        self.paired_try_id = try_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute catch - provides error details and executes catch body."""
        self.status = NodeStatus.RUNNING

        try:
            try_id = self.paired_try_id or self.get_parameter("paired_try_id", "")
            try_state_key = f"{try_id}_try_state"
            try_state = context.variables.get(try_state_key, {})

            if not try_state.get("error"):
                # No error - skip catch body (shouldn't normally happen)
                logger.debug("Catch node reached but no error in try state - skipping")
                self.status = NodeStatus.SKIPPED

                return {
                    "success": True,
                    "data": {},
                    "next_nodes": [],  # Skip catch body
                }

            # Check error type filter
            error_types_str = self.get_parameter("error_types", "")
            if error_types_str:
                allowed_types = [t.strip() for t in error_types_str.split(",") if t.strip()]
                error_type = try_state.get("error_type", "")
                if allowed_types and error_type not in allowed_types:
                    # Error type not in filter - re-raise
                    logger.info(
                        f"Catch filter {allowed_types} doesn't match {error_type} - re-raising"
                    )
                    return {
                        "success": False,
                        "error": try_state.get("error_message", "Unhandled error"),
                        "next_nodes": [],
                    }

            # Set output values for error handling
            self.set_output_value("error_message", try_state.get("error_message", ""))
            self.set_output_value("error_type", try_state.get("error_type", ""))
            self.set_output_value("stack_trace", try_state.get("stack_trace", ""))

            logger.info(f"Catch block handling error: {try_state.get('error_type')}")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "error_message": try_state.get("error_message", ""),
                    "error_type": try_state.get("error_type", ""),
                },
                "next_nodes": ["catch_body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Catch execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "paired_try_id",
        PropertyType.STRING,
        default="",
        label="Paired Try Node",
        tooltip="ID of the paired TryNode (set automatically)",
    ),
)
@node(category="control_flow", exec_outputs=["finally_body"])
class FinallyNode(BaseNode):
    """
    Finally block - always executes after Try/Catch regardless of errors.

    Cleans up try state and provides a guaranteed execution path for cleanup code.
    Paired automatically with Try and Catch nodes when created together.

    Outputs:
        - finally_body: Execution flow for cleanup code
        - had_error: Boolean indicating if an error occurred in try block
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in -> finally_body, had_error

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Finally node."""
        super().__init__(node_id, config)
        self.name = "Finally"
        self.node_type = "FinallyNode"
        # Paired automatically when created together - load from config
        self.paired_try_id: str = self.get_parameter("paired_try_id", "")

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("finally_body")
        self.add_output_port("had_error", DataType.BOOLEAN)

    def set_paired_try(self, try_node_id: str) -> None:
        """Set the paired Try node ID (called automatically)."""
        self.paired_try_id = try_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute finally - always runs, cleans up try state."""
        self.status = NodeStatus.RUNNING

        try:
            try_id = self.paired_try_id or self.get_parameter("paired_try_id", "")
            try_state_key = f"{try_id}_try_state"
            try_state = context.variables.get(try_state_key, {})

            had_error = try_state.get("error", False)

            # Clean up try state
            if try_state_key in context.variables:
                del context.variables[try_state_key]

            # Set output
            self.set_output_value("had_error", had_error)

            logger.info(f"Finally block executing (had_error={had_error})")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"had_error": had_error},
                "next_nodes": ["finally_body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Finally execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "TryNode",
    "CatchNode",
    "FinallyNode",
]
