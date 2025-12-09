"""
CasareRPA - Gmail Send Nodes

Nodes for sending emails, replies, forwards, and drafts via Gmail API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.gmail_client import GmailClient
from casare_rpa.nodes.google.google_base import GmailBaseNode


# ============================================================================
# Reusable Property Definitions for Gmail Nodes
# ============================================================================

GMAIL_ACCESS_TOKEN = PropertyDef(
    "access_token",
    PropertyType.STRING,
    default="",
    label="Access Token",
    placeholder="ya29.a0...",
    tooltip="OAuth 2.0 access token for Gmail API",
    tab="connection",
)

GMAIL_CREDENTIAL_NAME = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="gmail",
    tooltip="Name of stored OAuth credential (alternative to access token)",
    tab="connection",
)

GMAIL_TO = PropertyDef(
    "to",
    PropertyType.STRING,
    default="",
    required=True,
    label="To",
    placeholder="recipient@example.com, another@example.com",
    tooltip="Recipient email addresses (comma-separated)",
)

GMAIL_CC = PropertyDef(
    "cc",
    PropertyType.STRING,
    default="",
    label="CC",
    placeholder="cc@example.com",
    tooltip="CC recipients (comma-separated)",
)

GMAIL_BCC = PropertyDef(
    "bcc",
    PropertyType.STRING,
    default="",
    label="BCC",
    placeholder="bcc@example.com",
    tooltip="BCC recipients (comma-separated)",
)

GMAIL_SUBJECT = PropertyDef(
    "subject",
    PropertyType.STRING,
    default="",
    required=True,
    label="Subject",
    placeholder="Email subject",
    tooltip="Email subject line",
)

GMAIL_BODY = PropertyDef(
    "body",
    PropertyType.TEXT,
    default="",
    required=True,
    label="Body",
    placeholder="Email body content...",
    tooltip="Email body (plain text or HTML)",
)

GMAIL_BODY_TYPE = PropertyDef(
    "body_type",
    PropertyType.CHOICE,
    default="plain",
    choices=["plain", "html"],
    label="Body Type",
    tooltip="Email body format (plain text or HTML)",
)


def _parse_email_list(email_string: str) -> list[str]:
    """Parse comma-separated email addresses into a list."""
    if not email_string:
        return []
    return [addr.strip() for addr in email_string.split(",") if addr.strip()]


# ============================================================================
# GmailSendEmailNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    GMAIL_TO,
    GMAIL_CC,
    GMAIL_BCC,
    GMAIL_SUBJECT,
    GMAIL_BODY,
    GMAIL_BODY_TYPE,
)
@executable_node
class GmailSendEmailNode(GmailBaseNode):
    """
    Send a plain text or HTML email via Gmail.

    Inputs:
        - to: Recipient email addresses (comma-separated)
        - cc: CC recipients (optional)
        - bcc: BCC recipients (optional)
        - subject: Email subject
        - body: Email body content
        - body_type: "plain" or "html"

    Outputs:
        - message_id: Sent message ID
        - thread_id: Thread ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: to, cc, bcc, subject, body, body_type -> message_id, thread_id

    NODE_TYPE = "gmail_send_email"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Send Email"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Send Email", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Email-specific ports
        self.add_input_port("to", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("cc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("bcc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("subject", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("body", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "body_type", PortType.INPUT, DataType.STRING, required=False
        )

        # Additional outputs
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("thread_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Send a plain/HTML email."""
        # Get recipients
        to_str = self.get_parameter("to")
        if hasattr(context, "resolve_value"):
            to_str = context.resolve_value(to_str)

        to_list = _parse_email_list(to_str)
        if not to_list:
            self._set_error_outputs("At least one recipient is required")
            return {
                "success": False,
                "error": "At least one recipient is required",
                "next_nodes": [],
            }

        # Get optional CC/BCC
        cc_str = self.get_parameter("cc") or ""
        bcc_str = self.get_parameter("bcc") or ""
        if hasattr(context, "resolve_value"):
            cc_str = context.resolve_value(cc_str)
            bcc_str = context.resolve_value(bcc_str)
        cc_list = _parse_email_list(cc_str)
        bcc_list = _parse_email_list(bcc_str)

        # Get subject and body
        subject = self.get_parameter("subject")
        body = self.get_parameter("body")
        if hasattr(context, "resolve_value"):
            subject = context.resolve_value(subject)
            body = context.resolve_value(body)

        if not subject:
            self._set_error_outputs("Subject is required")
            return {"success": False, "error": "Subject is required", "next_nodes": []}

        if not body:
            self._set_error_outputs("Body is required")
            return {"success": False, "error": "Body is required", "next_nodes": []}

        # Get body type
        body_type = self.get_parameter("body_type") or "plain"
        if hasattr(context, "resolve_value"):
            body_type = context.resolve_value(body_type)

        logger.debug(f"Sending Gmail to {to_list}")

        # Send message
        result = await client.send_message(
            to=to_list,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc_list if cc_list else None,
            bcc=bcc_list if bcc_list else None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("message_id", result.id)
        self.set_output_value("thread_id", result.thread_id)

        logger.info(f"Gmail sent: {result.id}")

        return {
            "success": True,
            "message_id": result.id,
            "thread_id": result.thread_id,
            "next_nodes": [],
        }


# ============================================================================
# GmailSendWithAttachmentNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    GMAIL_TO,
    GMAIL_CC,
    GMAIL_BCC,
    GMAIL_SUBJECT,
    GMAIL_BODY,
    GMAIL_BODY_TYPE,
    PropertyDef(
        "attachments",
        PropertyType.STRING,
        default="",
        label="Attachments",
        placeholder="C:\\files\\doc.pdf, C:\\files\\image.png",
        tooltip="File paths to attach (comma-separated)",
    ),
)
@executable_node
class GmailSendWithAttachmentNode(GmailBaseNode):
    """
    Send an email with file attachments via Gmail.

    Inputs:
        - to: Recipient email addresses (comma-separated)
        - cc: CC recipients (optional)
        - bcc: BCC recipients (optional)
        - subject: Email subject
        - body: Email body content
        - body_type: "plain" or "html"
        - attachments: File paths (comma-separated)

    Outputs:
        - message_id: Sent message ID
        - thread_id: Thread ID
        - attachment_count: Number of attachments sent
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: to, cc, bcc, subject, body, body_type, attachments, attachment_list -> message_id, thread_id, attachment_count

    NODE_TYPE = "gmail_send_with_attachment"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Send with Attachment"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Send with Attachment", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Email-specific ports
        self.add_input_port("to", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("cc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("bcc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("subject", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("body", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "body_type", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "attachments", PortType.INPUT, DataType.STRING, required=False
        )
        # Also accept attachments as array from port connection
        self.add_input_port(
            "attachment_list", PortType.INPUT, DataType.ARRAY, required=False
        )

        # Additional outputs
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("thread_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("attachment_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Send an email with attachments."""
        # Get recipients
        to_str = self.get_parameter("to")
        if hasattr(context, "resolve_value"):
            to_str = context.resolve_value(to_str)

        to_list = _parse_email_list(to_str)
        if not to_list:
            self._set_error_outputs("At least one recipient is required")
            return {
                "success": False,
                "error": "At least one recipient is required",
                "next_nodes": [],
            }

        # Get optional CC/BCC
        cc_str = self.get_parameter("cc") or ""
        bcc_str = self.get_parameter("bcc") or ""
        if hasattr(context, "resolve_value"):
            cc_str = context.resolve_value(cc_str)
            bcc_str = context.resolve_value(bcc_str)
        cc_list = _parse_email_list(cc_str)
        bcc_list = _parse_email_list(bcc_str)

        # Get subject and body
        subject = self.get_parameter("subject")
        body = self.get_parameter("body")
        if hasattr(context, "resolve_value"):
            subject = context.resolve_value(subject)
            body = context.resolve_value(body)

        if not subject:
            self._set_error_outputs("Subject is required")
            return {"success": False, "error": "Subject is required", "next_nodes": []}

        if not body:
            self._set_error_outputs("Body is required")
            return {"success": False, "error": "Body is required", "next_nodes": []}

        # Get body type
        body_type = self.get_parameter("body_type") or "plain"
        if hasattr(context, "resolve_value"):
            body_type = context.resolve_value(body_type)

        # Get attachments - from string or list
        attachments_str = self.get_parameter("attachments") or ""
        attachment_list = self.get_parameter("attachment_list") or []
        if hasattr(context, "resolve_value"):
            attachments_str = context.resolve_value(attachments_str)
            attachment_list = context.resolve_value(attachment_list)

        # Parse attachment paths
        attachment_paths: list[Union[str, Path]] = []
        if attachments_str:
            for path_str in attachments_str.split(","):
                path = path_str.strip()
                if path:
                    attachment_paths.append(path)
        if attachment_list:
            attachment_paths.extend(attachment_list)

        # Validate attachments exist
        valid_attachments = []
        for att_path in attachment_paths:
            path = Path(att_path)
            if path.exists():
                valid_attachments.append(path)
            else:
                logger.warning(f"Attachment not found: {att_path}")

        logger.debug(
            f"Sending Gmail with {len(valid_attachments)} attachments to {to_list}"
        )

        # Send message
        result = await client.send_message(
            to=to_list,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc_list if cc_list else None,
            bcc=bcc_list if bcc_list else None,
            attachments=valid_attachments if valid_attachments else None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("message_id", result.id)
        self.set_output_value("thread_id", result.thread_id)
        self.set_output_value("attachment_count", len(valid_attachments))

        logger.info(
            f"Gmail sent with {len(valid_attachments)} attachments: {result.id}"
        )

        return {
            "success": True,
            "message_id": result.id,
            "thread_id": result.thread_id,
            "attachment_count": len(valid_attachments),
            "next_nodes": [],
        }


# ============================================================================
# GmailReplyToEmailNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    PropertyDef(
        "thread_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Thread ID",
        placeholder="18a5b7c8d9e0f1g2",
        tooltip="Thread ID of the conversation to reply to",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Message ID",
        placeholder="18a5b7c8d9e0f1g2",
        tooltip="Message ID to reply to",
    ),
    PropertyDef(
        "body",
        PropertyType.TEXT,
        default="",
        required=True,
        label="Reply Body",
        placeholder="Your reply content...",
        tooltip="Reply body content",
    ),
    GMAIL_BODY_TYPE,
    GMAIL_CC,
    GMAIL_BCC,
)
@executable_node
class GmailReplyToEmailNode(GmailBaseNode):
    """
    Reply to an existing email thread.

    Inputs:
        - thread_id: Thread ID of the conversation
        - message_id: Message ID to reply to
        - body: Reply body content
        - body_type: "plain" or "html"
        - cc: CC recipients (optional)
        - bcc: BCC recipients (optional)

    Outputs:
        - message_id: Sent reply message ID
        - thread_id: Thread ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: thread_id, message_id, body, body_type, cc, bcc -> message_id, thread_id

    NODE_TYPE = "gmail_reply_to_email"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Reply to Email"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Reply to Email", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Reply-specific ports
        self.add_input_port("thread_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "message_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("body", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "body_type", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("cc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("bcc", PortType.INPUT, DataType.STRING, required=False)

        # Additional outputs
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("thread_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Reply to an email thread."""
        # Get thread and message IDs
        thread_id = self.get_parameter("thread_id")
        message_id = self.get_parameter("message_id")
        if hasattr(context, "resolve_value"):
            thread_id = context.resolve_value(thread_id)
            message_id = context.resolve_value(message_id)

        if not thread_id:
            self._set_error_outputs("Thread ID is required")
            return {
                "success": False,
                "error": "Thread ID is required",
                "next_nodes": [],
            }

        if not message_id:
            self._set_error_outputs("Message ID is required")
            return {
                "success": False,
                "error": "Message ID is required",
                "next_nodes": [],
            }

        # Get body
        body = self.get_parameter("body")
        if hasattr(context, "resolve_value"):
            body = context.resolve_value(body)

        if not body:
            self._set_error_outputs("Reply body is required")
            return {
                "success": False,
                "error": "Reply body is required",
                "next_nodes": [],
            }

        # Get body type
        body_type = self.get_parameter("body_type") or "plain"
        if hasattr(context, "resolve_value"):
            body_type = context.resolve_value(body_type)

        # Get optional CC/BCC
        cc_str = self.get_parameter("cc") or ""
        bcc_str = self.get_parameter("bcc") or ""
        if hasattr(context, "resolve_value"):
            cc_str = context.resolve_value(cc_str)
            bcc_str = context.resolve_value(bcc_str)
        cc_list = _parse_email_list(cc_str)
        bcc_list = _parse_email_list(bcc_str)

        logger.debug(f"Sending reply to thread {thread_id}")

        # Send reply
        result = await client.reply_to_message(
            message_id=message_id,
            thread_id=thread_id,
            body=body,
            body_type=body_type,
            cc=cc_list if cc_list else None,
            bcc=bcc_list if bcc_list else None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("message_id", result.id)
        self.set_output_value("thread_id", result.thread_id)

        logger.info(f"Gmail reply sent: {result.id}")

        return {
            "success": True,
            "message_id": result.id,
            "thread_id": result.thread_id,
            "next_nodes": [],
        }


# ============================================================================
# GmailForwardEmailNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Message ID",
        placeholder="18a5b7c8d9e0f1g2",
        tooltip="Message ID to forward",
    ),
    GMAIL_TO,
    GMAIL_CC,
    GMAIL_BCC,
    PropertyDef(
        "additional_body",
        PropertyType.TEXT,
        default="",
        label="Additional Text",
        placeholder="Adding my comments...",
        tooltip="Optional text to add before the forwarded message",
    ),
)
@executable_node
class GmailForwardEmailNode(GmailBaseNode):
    """
    Forward an existing email to new recipients.

    Inputs:
        - message_id: Message ID to forward
        - to: Recipient email addresses (comma-separated)
        - cc: CC recipients (optional)
        - bcc: BCC recipients (optional)
        - additional_body: Optional text to prepend

    Outputs:
        - message_id: Sent forward message ID
        - thread_id: Thread ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: message_id, to, cc, bcc, additional_body -> message_id, thread_id

    NODE_TYPE = "gmail_forward_email"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Forward Email"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Forward Email", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Forward-specific ports
        self.add_input_port(
            "message_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("to", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("cc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("bcc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "additional_body", PortType.INPUT, DataType.STRING, required=False
        )

        # Additional outputs
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("thread_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Forward an email."""
        # Get message ID
        message_id = self.get_parameter("message_id")
        if hasattr(context, "resolve_value"):
            message_id = context.resolve_value(message_id)

        if not message_id:
            self._set_error_outputs("Message ID is required")
            return {
                "success": False,
                "error": "Message ID is required",
                "next_nodes": [],
            }

        # Get recipients
        to_str = self.get_parameter("to")
        if hasattr(context, "resolve_value"):
            to_str = context.resolve_value(to_str)

        to_list = _parse_email_list(to_str)
        if not to_list:
            self._set_error_outputs("At least one recipient is required")
            return {
                "success": False,
                "error": "At least one recipient is required",
                "next_nodes": [],
            }

        # Get optional CC/BCC
        cc_str = self.get_parameter("cc") or ""
        bcc_str = self.get_parameter("bcc") or ""
        if hasattr(context, "resolve_value"):
            cc_str = context.resolve_value(cc_str)
            bcc_str = context.resolve_value(bcc_str)
        cc_list = _parse_email_list(cc_str)
        bcc_list = _parse_email_list(bcc_str)

        # Get additional body
        additional_body = self.get_parameter("additional_body") or ""
        if hasattr(context, "resolve_value"):
            additional_body = context.resolve_value(additional_body)

        logger.debug(f"Forwarding message {message_id} to {to_list}")

        # Forward message
        result = await client.forward_message(
            message_id=message_id,
            to=to_list,
            body=additional_body if additional_body else None,
            cc=cc_list if cc_list else None,
            bcc=bcc_list if bcc_list else None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("message_id", result.id)
        self.set_output_value("thread_id", result.thread_id)

        logger.info(f"Gmail forwarded: {result.id}")

        return {
            "success": True,
            "message_id": result.id,
            "thread_id": result.thread_id,
            "next_nodes": [],
        }


# ============================================================================
# GmailCreateDraftNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    GMAIL_TO,
    GMAIL_CC,
    GMAIL_BCC,
    GMAIL_SUBJECT,
    GMAIL_BODY,
    GMAIL_BODY_TYPE,
    PropertyDef(
        "attachments",
        PropertyType.STRING,
        default="",
        label="Attachments",
        placeholder="C:\\files\\doc.pdf, C:\\files\\image.png",
        tooltip="File paths to attach (comma-separated)",
    ),
)
@executable_node
class GmailCreateDraftNode(GmailBaseNode):
    """
    Create a draft email (save without sending).

    Inputs:
        - to: Recipient email addresses (comma-separated)
        - cc: CC recipients (optional)
        - bcc: BCC recipients (optional)
        - subject: Email subject
        - body: Email body content
        - body_type: "plain" or "html"
        - attachments: File paths (comma-separated, optional)

    Outputs:
        - draft_id: Created draft ID
        - message_id: Draft message ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: to, cc, bcc, subject, body, body_type, attachments -> draft_id, message_id

    NODE_TYPE = "gmail_create_draft"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Create Draft"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Create Draft", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Draft-specific ports
        self.add_input_port("to", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("cc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("bcc", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("subject", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("body", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "body_type", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "attachments", PortType.INPUT, DataType.STRING, required=False
        )

        # Additional outputs
        self.add_output_port("draft_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Create a draft email."""
        # Get recipients
        to_str = self.get_parameter("to")
        if hasattr(context, "resolve_value"):
            to_str = context.resolve_value(to_str)

        to_list = _parse_email_list(to_str)
        if not to_list:
            self._set_error_outputs("At least one recipient is required")
            return {
                "success": False,
                "error": "At least one recipient is required",
                "next_nodes": [],
            }

        # Get optional CC/BCC
        cc_str = self.get_parameter("cc") or ""
        bcc_str = self.get_parameter("bcc") or ""
        if hasattr(context, "resolve_value"):
            cc_str = context.resolve_value(cc_str)
            bcc_str = context.resolve_value(bcc_str)
        cc_list = _parse_email_list(cc_str)
        bcc_list = _parse_email_list(bcc_str)

        # Get subject and body
        subject = self.get_parameter("subject")
        body = self.get_parameter("body")
        if hasattr(context, "resolve_value"):
            subject = context.resolve_value(subject)
            body = context.resolve_value(body)

        if not subject:
            self._set_error_outputs("Subject is required")
            return {"success": False, "error": "Subject is required", "next_nodes": []}

        if not body:
            self._set_error_outputs("Body is required")
            return {"success": False, "error": "Body is required", "next_nodes": []}

        # Get body type
        body_type = self.get_parameter("body_type") or "plain"
        if hasattr(context, "resolve_value"):
            body_type = context.resolve_value(body_type)

        # Get attachments
        attachments_str = self.get_parameter("attachments") or ""
        if hasattr(context, "resolve_value"):
            attachments_str = context.resolve_value(attachments_str)

        attachment_paths = []
        if attachments_str:
            for path_str in attachments_str.split(","):
                path = Path(path_str.strip())
                if path.exists():
                    attachment_paths.append(path)
                else:
                    logger.warning(f"Attachment not found: {path_str}")

        logger.debug(f"Creating Gmail draft for {to_list}")

        # Create draft
        result = await client.create_draft(
            to=to_list,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc_list if cc_list else None,
            bcc=bcc_list if bcc_list else None,
            attachments=attachment_paths if attachment_paths else None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("draft_id", result.id)
        message_id = result.message.id if result.message else ""
        self.set_output_value("message_id", message_id)

        logger.info(f"Gmail draft created: {result.id}")

        return {
            "success": True,
            "draft_id": result.id,
            "message_id": message_id,
            "next_nodes": [],
        }


__all__ = [
    "GmailSendEmailNode",
    "GmailSendWithAttachmentNode",
    "GmailReplyToEmailNode",
    "GmailForwardEmailNode",
    "GmailCreateDraftNode",
]
