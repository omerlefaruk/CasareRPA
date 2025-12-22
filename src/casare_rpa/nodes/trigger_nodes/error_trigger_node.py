"""
CasareRPA - Error Trigger Node

Trigger node that fires when errors occur in other workflows.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "error_types",
        PropertyType.STRING,
        default="*",
        label="Error Types",
        placeholder="NodeExecutionError,TimeoutError",
        tooltip="Comma-separated error types to catch (* for all)",
    ),
    PropertyDef(
        "workflow_filter",
        PropertyType.STRING,
        default="",
        label="Workflow Filter",
        placeholder="workflow_id_1,workflow_id_2",
        tooltip="Comma-separated workflow IDs to monitor (empty = all)",
    ),
    PropertyDef(
        "severity",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "critical", "error", "warning"],
        label="Minimum Severity",
        tooltip="Minimum error severity to trigger",
    ),
    PropertyDef(
        "error_pattern",
        PropertyType.STRING,
        default="",
        label="Error Message Pattern",
        placeholder=".*timeout.*",
        tooltip="Regex pattern to match error messages",
    ),
    PropertyDef(
        "include_warnings",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Warnings",
        tooltip="Also trigger on warning-level events",
    ),
)
@node(category="triggers", exec_inputs=[])
class ErrorTriggerNode(BaseTriggerNode):
    """
    Error trigger node that fires when errors occur.

    Outputs:
    - error: Full error object
    - error_type: Type/class of error
    - error_message: Error message
    - workflow_id: ID of workflow that errored
    - node_id: ID of node that errored
    - stack_trace: Stack trace (if available)
    - timestamp: When the error occurred
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Error"
    trigger_description = "Trigger on workflow errors"
    trigger_icon = "error"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Error Trigger"
        self.node_type = "ErrorTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define error-specific output ports."""
        self.add_output_port("error", DataType.DICT, "Error Object")
        self.add_output_port("error_type", DataType.STRING, "Error Type")
        self.add_output_port("error_message", DataType.STRING, "Error Message")
        self.add_output_port("workflow_id", DataType.STRING, "Workflow ID")
        self.add_output_port("node_id", DataType.STRING, "Node ID")
        self.add_output_port("stack_trace", DataType.STRING, "Stack Trace")
        self.add_output_port("timestamp", DataType.STRING, "Timestamp")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.ERROR

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get error-specific configuration."""
        error_types_str = self.get_parameter("error_types", "*")
        if error_types_str == "*":
            error_types = ["*"]
        else:
            error_types = [e.strip() for e in error_types_str.split(",") if e.strip()]

        workflow_filter_str = self.get_parameter("workflow_filter", "")
        workflow_filter = [w.strip() for w in workflow_filter_str.split(",") if w.strip()]

        return {
            "error_types": error_types,
            "workflow_filter": workflow_filter,
            "severity": self.get_parameter("severity", "all"),
            "error_pattern": self.get_parameter("error_pattern", ""),
            "include_warnings": self.get_parameter("include_warnings", False),
        }
