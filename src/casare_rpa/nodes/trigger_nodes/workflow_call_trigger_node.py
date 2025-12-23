"""
CasareRPA - Workflow Call Trigger Node

Trigger node that fires when called from another workflow.
Enables sub-workflow patterns.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "call_alias",
        PropertyType.STRING,
        required=True,
        label="Call Alias",
        placeholder="process_invoice",
        tooltip="Unique alias to call this workflow",
    ),
    PropertyDef(
        "input_schema",
        PropertyType.JSON,
        default="{}",
        label="Input Schema",
        placeholder='{"invoice_id": "string", "amount": "number"}',
        tooltip="JSON schema for expected input parameters",
    ),
    PropertyDef(
        "output_schema",
        PropertyType.JSON,
        default="{}",
        label="Output Schema",
        placeholder='{"result": "string", "success": "boolean"}',
        tooltip="JSON schema for output parameters",
    ),
    PropertyDef(
        "wait_for_completion",
        PropertyType.BOOLEAN,
        default=True,
        label="Wait for Completion",
        tooltip="Caller waits for this workflow to complete",
    ),
    PropertyDef(
        "timeout_seconds",
        PropertyType.INTEGER,
        default=300,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for completion",
    ),
)
@node(category="triggers", exec_inputs=[])
class WorkflowCallTriggerNode(BaseTriggerNode):
    """
    Workflow call trigger node for sub-workflow invocation.

    Outputs:
    - params: Input parameters from caller
    - caller_workflow_id: ID of calling workflow
    - caller_node_id: ID of calling node
    - call_id: Unique ID for this call
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Workflow Call"
    trigger_description = "Trigger when called from another workflow"
    trigger_icon = "workflow"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        super().__init__(node_id, config)
        self.name = "Workflow Call Trigger"
        self.node_type = "WorkflowCallTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define workflow call-specific output ports."""
        self.add_output_port("params", DataType.DICT, "Input Parameters")
        self.add_output_port("caller_workflow_id", DataType.STRING, "Caller Workflow")
        self.add_output_port("caller_node_id", DataType.STRING, "Caller Node")
        self.add_output_port("call_id", DataType.STRING, "Call ID")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.WORKFLOW_CALL

    def get_trigger_config(self) -> dict[str, Any]:
        """Get workflow call-specific configuration."""
        return {
            "call_alias": self.get_parameter("call_alias", ""),
            "input_schema": self.get_parameter("input_schema", "{}"),
            "output_schema": self.get_parameter("output_schema", "{}"),
            "wait_for_completion": self.get_parameter("wait_for_completion", True),
            "timeout_seconds": self.get_parameter("timeout_seconds", 300),
        }
