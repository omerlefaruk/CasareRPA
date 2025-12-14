"""
CasareRPA - Base Node Abstract Class

All automation nodes must inherit from this base class.
Implements the INode protocol defined in domain.interfaces.

Entry Points:
    - BaseNode: Abstract base class for all nodes
    - execute(): Core execution method (must be implemented)
    - validate(): Input/config validation
    - get_parameter(): Unified dual-source parameter access

Key Patterns:
    - Dual-source pattern: Values can come from ports OR config
    - Port-based data flow: Nodes communicate via typed ports
    - Status lifecycle: IDLE -> RUNNING -> SUCCESS/ERROR -> IDLE

Related:
    - See domain.interfaces.INode for the protocol definition
    - See domain.interfaces.IExecutionContext for context services
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

from casare_rpa.domain.value_objects import Port
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeConfig,
    NodeId,
    NodeStatus,
    PortType,
    SerializedNode,
)

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces import IExecutionContext


class BaseNode(ABC):
    """
    Abstract base class for all automation nodes.

    AI-HINT: This is the inheritance root for ALL 400+ automation nodes.
    AI-CONTEXT: Subclass this for any new node. Use @node decorator for registration.
    AI-WARNING: Changes here affect the entire node system. Test thoroughly.

    All nodes must implement:
    - execute(): Core execution logic
    - _define_ports(): Port definitions

    Key patterns:
    - Use add_exec_input()/add_exec_output() for execution ports
    - Use get_parameter() for dual-source config (port OR config)
    - Return ExecutionResult dict from execute(), don't raise exceptions
    """

    def __init__(self, node_id: NodeId, config: Optional[NodeConfig] = None) -> None:
        """
        Initialize base node.

        Args:
            node_id: Unique identifier for this node instance
            config: Node configuration dictionary
        """
        self.node_id = node_id
        self.config = config or {}
        self.status = NodeStatus.IDLE
        self.error_message: Optional[str] = None

        # Ports
        self.input_ports: Dict[str, Port] = {}
        self.output_ports: Dict[str, Port] = {}

        # Metadata
        self.node_type = self.__class__.__name__
        self.category = "General"
        self.description = self.__class__.__doc__ or "No description"

        # Debug support
        self.breakpoint_enabled: bool = False
        self.execution_count: int = 0
        self.last_execution_time: Optional[float] = None
        self.last_output: Optional[Dict[str, Any]] = None

        # Initialize ports
        self._define_ports()

    @abstractmethod
    def _define_ports(self) -> None:
        """
        Define the input and output ports for this node.
        Must be implemented by subclasses.

        Example:
            self.add_input_port("url", DataType.STRING, "URL to navigate")
            self.add_output_port("page", DataType.PAGE, "Loaded page")
        """
        pass

    @abstractmethod
    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """
        Execute the node's main logic.

        This is the core method that performs the node's automation task.
        Called by NodeExecutor after validation passes.

        Args:
            context: Execution context providing runtime services:
                - Variable access: context.get_variable(), context.set_variable()
                - Page access: context.get_active_page() for browser automation
                - Resource access: context.resources for shared resources
                - Flow control: context.stop_execution() to halt workflow

        Returns:
            ExecutionResult dict with structure:
                Success: {"success": True, "data": {"output_name": value, ...}}
                Error: {"success": False, "error": "message", "error_code": "CODE"}

            Special result keys (for flow control):
                - "route_to": NodeId - Override next node (for conditional nodes)
                - "loop_back_to": NodeId - Signal loop continuation
                - "parallel_branches": List[NodeId] - Fork execution

        Note:
            Should NOT raise exceptions for expected failures.
            Return error result instead. Exceptions indicate bugs.

        Related:
            See domain.interfaces.IExecutionContext for context methods
            See application.use_cases.node_executor for execution lifecycle
        """
        pass

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate node configuration and inputs.

        Checks both port values (runtime connections) and config values (design-time properties)
        for required parameters. This supports the dual-source pattern used by many nodes where
        values can come from either port connections OR the properties panel.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required input ports have values (from port OR config)
        for port in self.input_ports.values():
            # Skip EXEC ports - they control flow, not data
            # EXEC ports are identified by port_type or by name convention (exec_in, exec_out)
            if port.port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT):
                continue
            if port.name.startswith("exec_"):
                continue

            if port.required:
                # Check both sources: port.value (runtime) and config (design-time)
                port_value = port.value
                config_value = self.config.get(port.name)

                # Pass if value exists in EITHER source
                if port_value is None and config_value is None:
                    return False, f"Required input port '{port.name}' has no value"

        # Validate configuration
        validation_result = self._validate_config()
        if not validation_result[0]:
            return validation_result

        return True, None

    def _validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate node-specific configuration.
        Override in subclasses for custom validation.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None

    def add_input_port(
        self,
        name: str,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = True,
    ) -> None:
        """Add an input port to the node."""
        port = Port(name, PortType.INPUT, data_type, label, required)
        self.input_ports[name] = port

    def add_output_port(
        self,
        name: str,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = False,
    ) -> None:
        """Add an output port to the node."""
        port = Port(name, PortType.OUTPUT, data_type, label, required)
        self.output_ports[name] = port

    def add_exec_input(self, name: str = "exec_in") -> None:
        """Add an execution input port for flow control."""
        port = Port(name, PortType.EXEC_INPUT, DataType.EXEC, "Execute", required=False)
        self.input_ports[name] = port

    def add_exec_output(self, name: str = "exec_out") -> None:
        """Add an execution output port for flow control."""
        port = Port(name, PortType.EXEC_OUTPUT, DataType.EXEC, "Next", required=False)
        self.output_ports[name] = port

    def set_input_value(self, port_name: str, value: Any) -> None:
        """Set the value of an input port."""
        if port_name not in self.input_ports:
            raise ValueError(
                f"Input port '{port_name}' does not exist on {self.node_type}"
            )
        self.input_ports[port_name].set_value(value)

    def get_input_value(self, port_name: str, default: Any = None) -> Any:
        """Get the value of an input port."""
        if port_name not in self.input_ports:
            return default
        return self.input_ports[port_name].get_value()

    def set_output_value(self, port_name: str, value: Any) -> None:
        """Set the value of an output port."""
        if port_name not in self.output_ports:
            raise ValueError(
                f"Output port '{port_name}' does not exist on {self.node_type}"
            )
        self.output_ports[port_name].set_value(value)

    def get_output_value(self, port_name: str, default: Any = None) -> Any:
        """Get the value of an output port."""
        if port_name not in self.output_ports:
            return default
        return self.output_ports[port_name].get_value()

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get parameter value from port (runtime) or config (design-time).

        Unified accessor for the dual-source pattern used by many nodes.
        Prefers port value over config value to support runtime overrides.

        This is the recommended way to access node parameters that can come
        from either port connections OR the properties panel.

        Args:
            name: Parameter name (must match both port name and config key)
            default: Default value if parameter not found in either source

        Returns:
            Value from port if connected, otherwise from config, otherwise default

        Example:
            # Old pattern (fragile):
            file_path = self.config.get("file_path") or self.get_input_value("file_path")

            # New pattern (recommended):
            file_path = self.get_parameter("file_path")
        """
        # Check port first (runtime value from connection)
        port_value = self.get_input_value(name)
        if port_value is not None:
            return port_value

        # Fallback to config (design-time value from properties panel)
        return self.config.get(name, default)

    def serialize(self) -> SerializedNode:
        """
        Serialize node to dictionary for saving workflows.

        Returns:
            Dictionary containing node data
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "category": self.category,
            "config": self.config,
            "input_ports": {
                name: port.to_dict() for name, port in self.input_ports.items()
            },
            "output_ports": {
                name: port.to_dict() for name, port in self.output_ports.items()
            },
        }

    @classmethod
    def deserialize(cls, data: SerializedNode) -> "BaseNode":
        """
        Create a node instance from serialized data.

        Args:
            data: Serialized node dictionary

        Returns:
            Node instance
        """
        node_id = data["node_id"]
        config = data.get("config", {})
        return cls(node_id, config)

    def set_status(
        self, status: NodeStatus, error_message: Optional[str] = None
    ) -> None:
        """Update node status."""
        self.status = status
        self.error_message = error_message
        logger.debug(f"Node {self.node_id} ({self.node_type}) status: {status.name}")

    def get_status(self) -> NodeStatus:
        """Get current node status."""
        return self.status

    def reset(self) -> None:
        """Reset node to initial state."""
        self.status = NodeStatus.IDLE
        self.error_message = None
        for port in self.input_ports.values():
            port.value = None
        for port in self.output_ports.values():
            port.value = None
        self.execution_count = 0
        self.last_execution_time = None
        self.last_output = None

    def set_breakpoint(self, enabled: bool = True) -> None:
        """
        Enable or disable breakpoint on this node.

        Args:
            enabled: True to enable breakpoint, False to disable
        """
        self.breakpoint_enabled = enabled
        logger.debug(
            f"Breakpoint {'enabled' if enabled else 'disabled'} on node {self.node_id}"
        )

    def has_breakpoint(self) -> bool:
        """Check if this node has a breakpoint set."""
        return self.breakpoint_enabled

    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about this node.

        Returns:
            Dictionary containing debug information
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "status": self.status.name,
            "breakpoint_enabled": self.breakpoint_enabled,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time,
            "last_output": self.last_output,
            "input_values": {
                name: port.get_value() for name, port in self.input_ports.items()
            },
            "output_values": {
                name: port.get_value() for name, port in self.output_ports.items()
            },
        }

    def __repr__(self) -> str:
        """String representation of node."""
        return f"{self.node_type}(id={self.node_id}, status={self.status.name})"
