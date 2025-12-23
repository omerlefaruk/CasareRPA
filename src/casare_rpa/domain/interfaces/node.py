"""
CasareRPA - INode Protocol

Protocol interface defining the contract for all automation nodes.
Used for type hints in application layer without coupling to concrete implementations.

Usage:
    from casare_rpa.domain.interfaces import INode, IExecutionContext

    async def execute_node(node: INode, context: IExecutionContext) -> ExecutionResult:
        if not node.validate()[0]:
            return {"success": False, "error": "Validation failed"}
        return await node.execute(context)

Design Pattern: Dependency Inversion
- Application layer depends on INode protocol
- Node implementations satisfy the protocol
- Enables testing with mock nodes
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol

from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeConfig,
    NodeId,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces.execution_context import IExecutionContext
    from casare_rpa.domain.value_objects import Port


class INode(Protocol):
    """
    Protocol defining the node interface for execution.

    All automation nodes must satisfy this protocol.
    Enables type-safe node handling in application layer.

    Required Attributes:
        node_id: Unique identifier for this node instance
        node_type: Class name of the node (e.g., "ClickElementNode")
        config: Node configuration from properties panel
        status: Current execution status
        category: Node category for UI grouping
        input_ports: Dictionary of input port definitions
        output_ports: Dictionary of output port definitions

    Required Methods:
        execute(): Core execution logic
        validate(): Input/config validation
        get_input_value(): Read input port value
        set_output_value(): Write output port value
        get_parameter(): Unified port/config value access
    """

    # ========================================================================
    # Required Attributes
    # ========================================================================

    node_id: NodeId
    node_type: str
    config: NodeConfig
    status: NodeStatus
    category: str
    description: str

    input_ports: dict[str, "Port"]
    output_ports: dict[str, "Port"]

    # Debug support
    breakpoint_enabled: bool
    execution_count: int
    last_execution_time: float | None
    last_output: dict[str, Any] | None

    # ========================================================================
    # Core Execution Methods
    # ========================================================================

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """
        Execute the node's main logic.

        This is the core method that performs the node's automation task.
        Called by the execution engine after validation passes.

        Args:
            context: Execution context providing runtime services:
                - Variable access (get_variable, set_variable)
                - Page/browser access for web automation
                - Credential resolution
                - Logging and events

        Returns:
            ExecutionResult dict with structure:
                {"success": True, "data": {...}}  # On success
                {"success": False, "error": "...", "error_code": "..."}  # On failure

        Raises:
            Should NOT raise exceptions - return error result instead.
            Exceptions indicate bugs, not expected failures.

        Example Implementation:
            async def execute(self, context: IExecutionContext) -> ExecutionResult:
                try:
                    url = self.get_parameter("url")
                    page = context.get_variable("page")
                    await page.goto(url)
                    return {"success": True, "data": {"navigated": True}}
                except Exception as e:
                    return {"success": False, "error": str(e), "error_code": "NAV_FAILED"}
        """
        ...

    def validate(self) -> tuple[bool, str | None]:
        """
        Validate node configuration and inputs before execution.

        Called before execute() to ensure all required data is present.
        Checks both port values (runtime) and config (design-time).

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if validation passes
            - (False, "error description") if validation fails

        Note:
            This supports the dual-source pattern where values can come
            from either port connections OR the properties panel.
        """
        ...

    # ========================================================================
    # Port Access Methods
    # ========================================================================

    def get_input_value(self, port_name: str, default: Any = None) -> Any:
        """
        Get value from an input port.

        Retrieves the runtime value passed via port connection.

        Args:
            port_name: Name of the input port
            default: Value to return if port has no value

        Returns:
            The port value or default
        """
        ...

    def set_input_value(self, port_name: str, value: Any) -> None:
        """
        Set value on an input port.

        Used by execution engine to transfer data from upstream nodes.

        Args:
            port_name: Name of the input port
            value: Value to set

        Raises:
            ValueError: If port doesn't exist
        """
        ...

    def get_output_value(self, port_name: str, default: Any = None) -> Any:
        """
        Get value from an output port.

        Retrieves the value set by execute() for downstream nodes.

        Args:
            port_name: Name of the output port
            default: Value to return if port has no value

        Returns:
            The port value or default
        """
        ...

    def set_output_value(self, port_name: str, value: Any) -> None:
        """
        Set value on an output port.

        Called during execute() to expose results to downstream nodes.

        Args:
            port_name: Name of the output port
            value: Value to set

        Raises:
            ValueError: If port doesn't exist
        """
        ...

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get parameter from port OR config (dual-source pattern).

        Unified accessor that checks port value first (runtime),
        then falls back to config (design-time).

        This is the RECOMMENDED way to access node parameters.

        Args:
            name: Parameter name (matches both port name and config key)
            default: Value to return if not found in either source

        Returns:
            Value from port if connected, else config, else default

        Example:
            # Instead of:
            file_path = self.config.get("file_path") or self.get_input_value("file_path")

            # Use:
            file_path = self.get_parameter("file_path")
        """
        ...

    # ========================================================================
    # Port Definition Methods
    # ========================================================================

    def add_input_port(
        self,
        name: str,
        data_type: DataType,
        label: str | None = None,
        required: bool = True,
    ) -> None:
        """Add an input port definition."""
        ...

    def add_output_port(
        self,
        name: str,
        data_type: DataType,
        label: str | None = None,
        required: bool = False,
    ) -> None:
        """Add an output port definition."""
        ...

    # ========================================================================
    # Status Management
    # ========================================================================

    def set_status(self, status: NodeStatus, error_message: str | None = None) -> None:
        """Update node execution status."""
        ...

    def get_status(self) -> NodeStatus:
        """Get current node status."""
        ...

    def reset(self) -> None:
        """Reset node to initial IDLE state."""
        ...

    # ========================================================================
    # Debug Support
    # ========================================================================

    def set_breakpoint(self, enabled: bool = True) -> None:
        """Enable or disable breakpoint on this node."""
        ...

    def has_breakpoint(self) -> bool:
        """Check if this node has a breakpoint set."""
        ...

    def get_debug_info(self) -> dict[str, Any]:
        """Get debug information about this node."""
        ...

    # ========================================================================
    # Serialization
    # ========================================================================

    def serialize(self) -> dict[str, Any]:
        """Serialize node to dictionary for persistence."""
        ...
