"""
CasareRPA - Email Trigger Node

Trigger node that fires when new emails arrive.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "provider",
        PropertyType.CHOICE,
        default="imap",
        choices=["imap", "gmail", "outlook"],
        label="Email Provider",
        tooltip="Email service provider",
    ),
    # IMAP settings
    PropertyDef(
        "server",
        PropertyType.STRING,
        default="",
        label="IMAP Server",
        placeholder="imap.gmail.com",
        tooltip="IMAP server address",
    ),
    PropertyDef(
        "port",
        PropertyType.INTEGER,
        default=993,
        label="Port",
        tooltip="IMAP port (993 for SSL)",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username/Email",
        placeholder="user@example.com",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password/App Password",
        tooltip="Password or app-specific password",
    ),
    PropertyDef(
        "use_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Use SSL",
    ),
    # Folder and filters
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Email folder to monitor",
    ),
    PropertyDef(
        "filter_subject",
        PropertyType.STRING,
        default="",
        label="Subject Filter (regex)",
        placeholder=".*Invoice.*",
        tooltip="Regex pattern for subject",
    ),
    PropertyDef(
        "filter_from",
        PropertyType.STRING,
        default="",
        label="From Filter (regex)",
        placeholder=".*@company.com",
        tooltip="Regex pattern for sender",
    ),
    PropertyDef(
        "unread_only",
        PropertyType.BOOLEAN,
        default=True,
        label="Unread Only",
        tooltip="Only trigger on unread emails",
    ),
    PropertyDef(
        "mark_as_read",
        PropertyType.BOOLEAN,
        default=True,
        label="Mark as Read",
        tooltip="Mark email as read after triggering",
    ),
    # Polling
    PropertyDef(
        "poll_interval_seconds",
        PropertyType.INTEGER,
        default=60,
        label="Poll Interval (seconds)",
        tooltip="How often to check for new emails",
    ),
    PropertyDef(
        "download_attachments",
        PropertyType.BOOLEAN,
        default=False,
        label="Download Attachments",
        tooltip="Download email attachments",
    ),
    PropertyDef(
        "attachment_dir",
        PropertyType.DIRECTORY_PATH,
        default="",
        label="Attachment Directory",
        placeholder="C:\\Downloads\\Attachments",
    ),
)
@node(category="triggers", exec_inputs=[])
class EmailTriggerNode(BaseTriggerNode):
    """
    Email trigger node that fires when new emails arrive.

    Outputs:
    - email: Full email object
    - subject: Email subject
    - sender: Sender email address
    - body: Email body (text)
    - html_body: Email body (HTML)
    - attachments: List of attachment file paths
    - received_at: When the email was received
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Email"
    trigger_description = "Trigger on new email"
    trigger_icon = "email"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        super().__init__(node_id, config)
        self.name = "Email Trigger"
        self.node_type = "EmailTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define email-specific output ports."""
        self.add_output_port("email", DataType.DICT, "Email Object")
        self.add_output_port("subject", DataType.STRING, "Subject")
        self.add_output_port("sender", DataType.STRING, "Sender")
        self.add_output_port("body", DataType.STRING, "Body (Text)")
        self.add_output_port("html_body", DataType.STRING, "Body (HTML)")
        self.add_output_port("attachments", DataType.LIST, "Attachments")
        self.add_output_port("received_at", DataType.STRING, "Received At")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.EMAIL

    def get_trigger_config(self) -> dict[str, Any]:
        """Get email-specific configuration."""
        return {
            "provider": self.get_parameter("provider", "imap"),
            "server": self.get_parameter("server", ""),
            "port": self.get_parameter("port", 993),
            "username": self.get_parameter("username", ""),
            "password": self.get_parameter("password", ""),
            "use_ssl": self.get_parameter("use_ssl", True),
            "folder": self.get_parameter("folder", "INBOX"),
            "filter_subject": self.get_parameter("filter_subject", ""),
            "filter_from": self.get_parameter("filter_from", ""),
            "unread_only": self.get_parameter("unread_only", True),
            "mark_as_read": self.get_parameter("mark_as_read", True),
            "poll_interval_seconds": self.get_parameter("poll_interval_seconds", 60),
            "download_attachments": self.get_parameter("download_attachments", False),
            "attachment_dir": self.get_parameter("attachment_dir", ""),
        }
