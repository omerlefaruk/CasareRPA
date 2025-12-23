"""
CasareRPA - Gmail Trigger Node

Trigger node that listens for new Gmail emails matching filters.
Workflow starts when a matching email arrives.
"""

from typing import Any

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    # Connection settings
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        placeholder="google",
        tooltip="Name of stored Google OAuth credential",
        tab="connection",
    ),
    # Polling settings
    PropertyDef(
        "polling_interval",
        PropertyType.INTEGER,
        default=60,
        label="Polling Interval (sec)",
        tooltip="Seconds between checks for new emails",
    ),
    # Filters
    PropertyDef(
        "label_ids",
        PropertyType.STRING,
        default="INBOX",
        label="Label IDs",
        placeholder="INBOX,IMPORTANT",
        tooltip="Comma-separated Gmail label IDs to monitor",
    ),
    PropertyDef(
        "query",
        PropertyType.STRING,
        default="is:unread",
        label="Search Query",
        placeholder="is:unread from:example@gmail.com",
        tooltip="Gmail search query to filter emails",
    ),
    PropertyDef(
        "from_filter",
        PropertyType.STRING,
        default="",
        label="From Filter",
        placeholder="sender@example.com",
        tooltip="Only trigger for emails from this address",
    ),
    PropertyDef(
        "subject_contains",
        PropertyType.STRING,
        default="",
        label="Subject Contains",
        placeholder="Invoice",
        tooltip="Only trigger if subject contains this text",
    ),
    PropertyDef(
        "mark_as_read",
        PropertyType.BOOLEAN,
        default=True,
        label="Mark as Read",
        tooltip="Mark email as read after triggering",
        tab="advanced",
    ),
    PropertyDef(
        "include_attachments",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Attachments",
        tooltip="Include attachment metadata in payload",
        tab="advanced",
    ),
    PropertyDef(
        "max_results",
        PropertyType.INTEGER,
        default=10,
        label="Max Results",
        tooltip="Maximum emails to process per poll",
        tab="advanced",
    ),
)
@node(category="triggers", exec_inputs=[])
class GmailTriggerNode(BaseTriggerNode):
    """
    Gmail trigger node that monitors for new emails.

    Polls Gmail API for new emails matching the specified filters.
    Requires Google OAuth credentials with Gmail scope.

    Outputs:
    - message_id: Gmail message ID
    - thread_id: Gmail thread ID
    - subject: Email subject
    - from_email: Sender email address
    - from_name: Sender name
    - to_email: Recipient email address
    - date: Email date/time
    - snippet: Email preview snippet
    - body_text: Plain text body
    - body_html: HTML body (if available)
    - labels: List of Gmail labels
    - has_attachments: Whether email has attachments
    - attachments: List of attachment metadata
    - raw_message: Full message object
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Gmail"
    trigger_description = "Trigger workflow when new Gmail email arrives"
    trigger_icon = "gmail"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        super().__init__(node_id, config)
        self.name = "Gmail Trigger"
        self.node_type = "GmailTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define Gmail-specific output ports."""
        self.add_output_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("thread_id", DataType.STRING, "Thread ID")
        self.add_output_port("subject", DataType.STRING, "Subject")
        self.add_output_port("from_email", DataType.STRING, "From Email")
        self.add_output_port("from_name", DataType.STRING, "From Name")
        self.add_output_port("to_email", DataType.STRING, "To Email")
        self.add_output_port("date", DataType.STRING, "Date")
        self.add_output_port("snippet", DataType.STRING, "Snippet")
        self.add_output_port("body_text", DataType.STRING, "Body (Text)")
        self.add_output_port("body_html", DataType.STRING, "Body (HTML)")
        self.add_output_port("labels", DataType.LIST, "Labels")
        self.add_output_port("has_attachments", DataType.BOOLEAN, "Has Attachments")
        self.add_output_port("attachments", DataType.LIST, "Attachments")
        self.add_output_port("raw_message", DataType.DICT, "Raw Message")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.GMAIL

    def get_trigger_config(self) -> dict[str, Any]:
        """Get Gmail-specific configuration."""
        # Parse comma-separated label IDs
        label_ids_str = self.get_parameter("label_ids", "INBOX")
        label_ids = [lid.strip() for lid in label_ids_str.split(",") if lid.strip()]

        return {
            "credential_name": self.get_parameter("credential_name", "google"),
            "polling_interval": self.get_parameter("polling_interval", 60),
            "label_ids": label_ids,
            "query": self.get_parameter("query", "is:unread"),
            "from_filter": self.get_parameter("from_filter", ""),
            "subject_contains": self.get_parameter("subject_contains", ""),
            "mark_as_read": self.get_parameter("mark_as_read", True),
            "include_attachments": self.get_parameter("include_attachments", True),
            "max_results": self.get_parameter("max_results", 10),
        }
