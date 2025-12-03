"""
CasareRPA - WhatsApp Trigger Node

Trigger node that listens for incoming WhatsApp messages via Cloud API webhook.
Workflow starts when a message matching the filters is received.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import (
    BaseTriggerNode,
    trigger_node,
)
from casare_rpa.triggers.base import TriggerType


@node_schema(
    # Connection settings
    PropertyDef(
        "access_token",
        PropertyType.STRING,
        default="",
        label="Access Token",
        placeholder="EAAxxxxxxxx...",
        tooltip="WhatsApp Business API access token",
        tab="connection",
    ),
    PropertyDef(
        "phone_number_id",
        PropertyType.STRING,
        default="",
        label="Phone Number ID",
        placeholder="123456789012345",
        tooltip="WhatsApp Business phone number ID",
        tab="connection",
    ),
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="",
        label="Credential Name",
        placeholder="whatsapp",
        tooltip="Name of stored credential (alternative to access token)",
        tab="connection",
    ),
    # Webhook settings
    PropertyDef(
        "verify_token",
        PropertyType.STRING,
        default="",
        label="Verify Token",
        placeholder="my-secret-token",
        tooltip="Token for webhook verification (must match Meta app settings)",
    ),
    PropertyDef(
        "webhook_path",
        PropertyType.STRING,
        default="/whatsapp/webhook",
        label="Webhook Path",
        placeholder="/whatsapp/webhook",
        tooltip="Path for webhook endpoint",
    ),
    # Filters
    PropertyDef(
        "filter_phone_numbers",
        PropertyType.STRING,
        default="",
        label="Filter Phone Numbers",
        placeholder="+1234567890,+0987654321",
        tooltip="Comma-separated phone numbers to allow (empty = all)",
    ),
    PropertyDef(
        "message_types",
        PropertyType.STRING,
        default="text,image,document,audio,video,location",
        label="Message Types",
        placeholder="text,image,document",
        tooltip="Comma-separated message types to trigger on",
    ),
    PropertyDef(
        "include_status_updates",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Status Updates",
        tooltip="Also trigger on message status updates (sent, delivered, read)",
        tab="advanced",
    ),
)
@trigger_node
class WhatsAppTriggerNode(BaseTriggerNode):
    """
    WhatsApp trigger node that listens for incoming messages.

    Uses WhatsApp Cloud API webhook to receive messages.
    Requires a public HTTPS endpoint for webhook verification.

    Outputs:
    - message_id: WhatsApp message ID
    - from_number: Sender's phone number
    - to_number: Recipient phone number (your business number)
    - timestamp: Message timestamp
    - text: Message text (for text messages)
    - message_type: Type of message (text, image, document, etc.)
    - media_id: Media ID for media messages
    - media_url: Media URL (if available)
    - caption: Media caption (if any)
    - contact_name: Sender's WhatsApp profile name
    - raw_message: Full message object from webhook
    """

    trigger_display_name = "WhatsApp"
    trigger_description = "Trigger workflow when WhatsApp message is received"
    trigger_icon = "whatsapp"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "WhatsApp Trigger"
        self.node_type = "WhatsAppTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define WhatsApp-specific output ports."""
        self.add_output_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("from_number", DataType.STRING, "From Number")
        self.add_output_port("to_number", DataType.STRING, "To Number")
        self.add_output_port("timestamp", DataType.STRING, "Timestamp")
        self.add_output_port("text", DataType.STRING, "Message Text")
        self.add_output_port("message_type", DataType.STRING, "Message Type")
        self.add_output_port("media_id", DataType.STRING, "Media ID")
        self.add_output_port("media_url", DataType.STRING, "Media URL")
        self.add_output_port("caption", DataType.STRING, "Caption")
        self.add_output_port("contact_name", DataType.STRING, "Contact Name")
        self.add_output_port("raw_message", DataType.DICT, "Raw Message")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.WHATSAPP

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get WhatsApp-specific configuration."""
        # Parse comma-separated lists
        filter_phones_str = self.config.get("filter_phone_numbers", "")
        filter_phones = [p.strip() for p in filter_phones_str.split(",") if p.strip()]

        message_types_str = self.config.get(
            "message_types", "text,image,document,audio,video,location"
        )
        message_types = [t.strip() for t in message_types_str.split(",") if t.strip()]

        return {
            "access_token": self.config.get("access_token", ""),
            "phone_number_id": self.config.get("phone_number_id", ""),
            "credential_name": self.config.get("credential_name", ""),
            "verify_token": self.config.get("verify_token", ""),
            "webhook_path": self.config.get("webhook_path", "/whatsapp/webhook"),
            "filter_phone_numbers": filter_phones,
            "message_types": message_types,
            "include_status_updates": self.config.get("include_status_updates", False),
        }
