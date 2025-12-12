"""
CasareRPA - Form Trigger Node

Trigger node that fires when a form is submitted.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import (
    BaseTriggerNode,
    trigger_node,
)
from casare_rpa.triggers.base import TriggerType


@trigger_node
@properties(
    PropertyDef(
        "form_title",
        PropertyType.STRING,
        default="Submit Data",
        label="Form Title",
        placeholder="Submit Invoice",
    ),
    PropertyDef(
        "form_description",
        PropertyType.STRING,
        default="",
        label="Form Description",
        placeholder="Enter invoice details",
    ),
    PropertyDef(
        "form_fields",
        PropertyType.JSON,
        default='[{"name": "data", "type": "text", "label": "Data", "required": true}]',
        label="Form Fields",
        tooltip="JSON array of field definitions",
    ),
    PropertyDef(
        "submit_button_text",
        PropertyType.STRING,
        default="Submit",
        label="Submit Button Text",
    ),
    PropertyDef(
        "success_message",
        PropertyType.STRING,
        default="Form submitted successfully",
        label="Success Message",
    ),
    PropertyDef(
        "require_auth",
        PropertyType.BOOLEAN,
        default=False,
        label="Require Authentication",
        tooltip="Require user to be logged in",
    ),
)
class FormTriggerNode(BaseTriggerNode):
    """
    Form trigger node that fires when a form is submitted.

    Outputs:
    - form_data: Submitted form data as dictionary
    - submitted_at: When the form was submitted
    - user_id: ID of user who submitted (if authenticated)
    - ip_address: IP address of submitter
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Form"
    trigger_description = "Trigger on form submission"
    trigger_icon = "form"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Form Trigger"
        self.node_type = "FormTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define form-specific output ports."""
        self.add_output_port("form_data", DataType.DICT, "Form Data")
        self.add_output_port("submitted_at", DataType.STRING, "Submitted At")
        self.add_output_port("user_id", DataType.STRING, "User ID")
        self.add_output_port("ip_address", DataType.STRING, "IP Address")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.FORM

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get form-specific configuration."""
        return {
            "form_title": self.config.get("form_title", "Submit Data"),
            "form_description": self.config.get("form_description", ""),
            "form_fields": self.config.get("form_fields", "[]"),
            "submit_button_text": self.config.get("submit_button_text", "Submit"),
            "success_message": self.config.get(
                "success_message", "Form submitted successfully"
            ),
            "require_auth": self.config.get("require_auth", False),
        }
