"""
CasareRPA - Base Trigger Node

Abstract base class for all trigger nodes. Trigger nodes are workflow entry points
that have NO exec_in port (they START workflows) and output trigger payload data.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional, Type

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    ExecutionResult,
    NodeConfig,
    NodeId,
    PortType,
)
from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerType,
)


class BaseTriggerNode(BaseNode):
    """
    Abstract base class for all trigger nodes.

    Trigger nodes differ from regular nodes:
    - NO exec_in port (triggers START workflows)
    - Only exec_out port for flow continuation
    - Output ports for trigger payload data
    - Can create a BaseTrigger instance for background listening

    Subclasses must implement:
    - get_trigger_type(): Return the TriggerType enum
    - get_trigger_config(): Return trigger-specific config dict
    - _define_payload_ports(): Define output ports for trigger data
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> exec_out

    # Class attribute to identify trigger nodes
    is_trigger_node: bool = True

    # Trigger metadata (override in subclasses)
    trigger_display_name: str = "Trigger"
    trigger_description: str = "Base trigger node"
    trigger_icon: str = "trigger"
    trigger_category: str = "triggers"

    def __init__(self, node_id: NodeId, config: Optional[NodeConfig] = None) -> None:
        """Initialize trigger node."""
        super().__init__(node_id, config)
        self.category = "triggers"

        # Trigger state
        self._is_listening: bool = False
        self._trigger_instance: Optional[BaseTrigger] = None

    def _define_ports(self) -> None:
        """
        Define ports for trigger node.

        Trigger nodes have:
        - NO exec_in (they start workflows)
        - exec_out for flow continuation
        - Payload output ports defined by subclass
        """
        # Only exec_out, no exec_in!
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        # Let subclass define payload ports
        self._define_payload_ports()

    @abstractmethod
    def _define_payload_ports(self) -> None:
        """
        Define output ports for trigger payload data.

        Override in subclasses to add trigger-specific output ports.

        Example:
            self.add_output_port("payload", DataType.DICT)
            self.add_output_port("headers", DataType.DICT)
        """
        pass

    @abstractmethod
    def get_trigger_type(self) -> TriggerType:
        """
        Get the trigger type for this node.

        Returns:
            TriggerType enum value
        """
        pass

    @abstractmethod
    def get_trigger_config(self) -> Dict[str, Any]:
        """
        Get trigger-specific configuration from node properties.

        Returns:
            Dictionary of trigger configuration
        """
        pass

    async def execute(self, context: Any) -> ExecutionResult:
        """
        Execute the trigger node.

        In canvas execution mode, this acts as a pass-through (like StartNode).
        The trigger payload is already populated in output ports by the trigger system.

        Args:
            context: Execution context

        Returns:
            ExecutionResult indicating success
        """
        # Trigger nodes act as pass-through during execution
        # The payload data is already set in output ports by the trigger system
        return {
            "success": True,
            "data": {
                port_name: port.get_value()
                for port_name, port in self.output_ports.items()
                if port_name != "exec_out"
            },
        }

    def populate_from_trigger_event(self, payload: Dict[str, Any]) -> None:
        """
        Populate output ports from trigger event payload.

        Called by the trigger system when the trigger fires.

        Args:
            payload: Trigger event payload data
        """
        for port_name, port in self.output_ports.items():
            if port_name == "exec_out":
                continue
            if port_name in payload:
                port.set_value(payload[port_name])

    def create_trigger_config(
        self,
        workflow_id: str,
        scenario_id: str = "",
        trigger_id: Optional[str] = None,
    ) -> BaseTriggerConfig:
        """
        Create a BaseTriggerConfig from this node's configuration.

        Args:
            workflow_id: ID of the workflow this trigger belongs to
            scenario_id: ID of the scenario (optional)
            trigger_id: Custom trigger ID (auto-generated if not provided)

        Returns:
            BaseTriggerConfig instance
        """
        return BaseTriggerConfig(
            id=trigger_id or f"trig_{self.node_id}",
            name=self.config.get("name", self.trigger_display_name),
            trigger_type=self.get_trigger_type(),
            scenario_id=scenario_id,
            workflow_id=workflow_id,
            enabled=self.config.get("enabled", True),
            priority=self.config.get("priority", 1),
            cooldown_seconds=self.config.get("cooldown_seconds", 0),
            description=self.config.get("description", ""),
            config=self.get_trigger_config(),
        )

    def create_trigger_instance(
        self,
        workflow_id: str,
        scenario_id: str = "",
        event_callback: Optional[Any] = None,
    ) -> Optional[BaseTrigger]:
        """
        Create a BaseTrigger instance for background listening.

        Args:
            workflow_id: ID of the workflow
            scenario_id: ID of the scenario
            event_callback: Callback when trigger fires

        Returns:
            BaseTrigger instance or None if trigger class not available
        """
        from casare_rpa.triggers.registry import TriggerRegistry

        trigger_config = self.create_trigger_config(workflow_id, scenario_id)
        trigger_class = TriggerRegistry().get(self.get_trigger_type())

        if trigger_class:
            self._trigger_instance = trigger_class(trigger_config, event_callback)
            return self._trigger_instance
        return None

    @property
    def is_listening(self) -> bool:
        """Check if this trigger is currently listening."""
        return self._is_listening

    def set_listening(self, listening: bool) -> None:
        """Set the listening state."""
        self._is_listening = listening

    def get_trigger_instance(self) -> Optional[BaseTrigger]:
        """Get the trigger instance if created."""
        return self._trigger_instance


def trigger_node(cls: Type) -> Type:
    """
    Decorator to mark a class as a trigger node.

    Unlike @executable_node, this only adds exec_out (no exec_in).
    Trigger nodes start workflows, they don't receive execution flow.

    Usage:
        @trigger_node
        class WebhookTriggerNode(BaseTriggerNode):
            def _define_payload_ports(self) -> None:
                self.add_output_port("payload", DataType.DICT)
    """
    # Mark class as trigger node
    cls.is_trigger_node = True

    # Ensure _define_ports adds exec_out (already handled in BaseTriggerNode)
    # This decorator mainly serves as documentation/validation

    return cls
