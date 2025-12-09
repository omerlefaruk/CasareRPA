"""
CasareRPA - Gmail Read Nodes

Nodes for reading, searching, and retrieving emails via Gmail API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
# Reusable Property Definitions for Gmail Read Nodes
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

GMAIL_MESSAGE_ID = PropertyDef(
    "message_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="Message ID",
    placeholder="18a5b7c8d9e0f1g2",
    tooltip="Gmail message ID",
)

GMAIL_FORMAT = PropertyDef(
    "format",
    PropertyType.CHOICE,
    default="full",
    choices=["minimal", "metadata", "full", "raw"],
    label="Format",
    tooltip="Response format (minimal, metadata, full, or raw)",
)


# ============================================================================
# GmailGetEmailNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    GMAIL_MESSAGE_ID,
    GMAIL_FORMAT,
)
@executable_node
class GmailGetEmailNode(GmailBaseNode):
    """
    Get a single email by message ID.

    Inputs:
        - message_id: Gmail message ID
        - format: Response format ("minimal", "metadata", "full", "raw")

    Outputs:
        - message_id: Message ID
        - thread_id: Thread ID
        - subject: Email subject
        - from_address: Sender email address
        - to_addresses: Recipient addresses (JSON array)
        - date: Date header
        - snippet: Message snippet
        - body_plain: Plain text body
        - body_html: HTML body
        - label_ids: Label IDs (JSON array)
        - has_attachments: Whether message has attachments
        - attachment_count: Number of attachments
        - raw_message: Full raw message object (JSON)
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: message_id, format -> message_id, thread_id, subject, from_address, to_addresses, cc_addresses, date, snippet, body_plain, body_html, label_ids, has_attachments, attachment_count, attachments, raw_message

    NODE_TYPE = "gmail_get_email"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Get Email"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Get Email", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Get email-specific inputs
        self.add_input_port(
            "message_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("format", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("thread_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("subject", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("from_address", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("to_addresses", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("cc_addresses", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("date", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("snippet", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("body_plain", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("body_html", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("label_ids", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("has_attachments", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("attachment_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("attachments", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("raw_message", PortType.OUTPUT, DataType.OBJECT)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Get a single email by ID."""
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

        # Get format
        format_type = self.get_parameter("format") or "full"
        if hasattr(context, "resolve_value"):
            format_type = context.resolve_value(format_type)

        logger.debug(f"Getting Gmail message {message_id}")

        # Get message
        message = await client.get_message(message_id, format_type=format_type)

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("message_id", message.id)
        self.set_output_value("thread_id", message.thread_id)
        self.set_output_value("subject", message.subject)
        self.set_output_value("from_address", message.from_address)
        self.set_output_value("to_addresses", message.to_addresses)
        self.set_output_value("cc_addresses", message.cc_addresses)
        self.set_output_value("date", message.date)
        self.set_output_value("snippet", message.snippet)
        self.set_output_value("body_plain", message.body_plain)
        self.set_output_value("body_html", message.body_html)
        self.set_output_value("label_ids", message.label_ids)
        self.set_output_value("has_attachments", len(message.attachments) > 0)
        self.set_output_value("attachment_count", len(message.attachments))
        self.set_output_value("attachments", message.attachments)
        self.set_output_value("raw_message", message.raw)

        logger.info(f"Gmail message retrieved: {message.id}")

        return {
            "success": True,
            "message_id": message.id,
            "subject": message.subject,
            "next_nodes": [],
        }


# ============================================================================
# GmailSearchEmailsNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    PropertyDef(
        "query",
        PropertyType.STRING,
        default="",
        label="Search Query",
        placeholder="from:user@example.com is:unread",
        tooltip="Gmail search query (same syntax as Gmail search box)",
    ),
    PropertyDef(
        "max_results",
        PropertyType.INTEGER,
        default=10,
        min_value=1,
        max_value=500,
        label="Max Results",
        tooltip="Maximum number of messages to return (1-500)",
    ),
    PropertyDef(
        "label_ids",
        PropertyType.STRING,
        default="",
        label="Label IDs",
        placeholder="INBOX, UNREAD",
        tooltip="Filter by label IDs (comma-separated)",
    ),
    PropertyDef(
        "include_spam_trash",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Spam/Trash",
        tooltip="Include messages from spam and trash folders",
    ),
)
@executable_node
class GmailSearchEmailsNode(GmailBaseNode):
    """
    Search for emails using Gmail query syntax.

    Inputs:
        - query: Gmail search query (e.g., "from:user@example.com is:unread")
        - max_results: Maximum results to return (default 10)
        - label_ids: Filter by labels (comma-separated)
        - include_spam_trash: Include spam/trash messages

    Query Examples:
        - "is:unread" - Unread messages
        - "from:user@example.com" - From specific sender
        - "subject:meeting" - Subject contains "meeting"
        - "has:attachment" - Has attachments
        - "after:2024/01/01" - After date
        - "is:starred" - Starred messages

    Outputs:
        - messages: Array of message objects (id, thread_id, subject, from, snippet)
        - message_count: Number of messages found
        - message_ids: Array of message IDs
        - next_page_token: Token for pagination (empty if no more pages)
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: query, max_results, label_ids, include_spam_trash, page_token -> messages, message_count, message_ids, next_page_token

    NODE_TYPE = "gmail_search_emails"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Search Emails"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Search Emails", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Search-specific inputs
        self.add_input_port("query", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "max_results", PortType.INPUT, DataType.INTEGER, required=False
        )
        self.add_input_port(
            "label_ids", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "include_spam_trash", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port(
            "page_token", PortType.INPUT, DataType.STRING, required=False
        )

        # Outputs
        self.add_output_port("messages", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("message_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("message_ids", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("next_page_token", PortType.OUTPUT, DataType.STRING)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Search for emails."""
        # Get query parameters
        query = self.get_parameter("query") or ""
        max_results = self.get_parameter("max_results") or 10
        label_ids_str = self.get_parameter("label_ids") or ""
        include_spam_trash = self.get_parameter("include_spam_trash") or False
        page_token = self.get_parameter("page_token") or None

        if hasattr(context, "resolve_value"):
            query = context.resolve_value(query)
            max_results = context.resolve_value(max_results)
            label_ids_str = context.resolve_value(label_ids_str)
            include_spam_trash = context.resolve_value(include_spam_trash)
            if page_token:
                page_token = context.resolve_value(page_token)

        # Parse label IDs
        label_ids = None
        if label_ids_str:
            label_ids = [lid.strip() for lid in label_ids_str.split(",") if lid.strip()]

        # Ensure max_results is int
        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            max_results = 10
        max_results = max(1, min(max_results, 500))

        logger.debug(f"Searching Gmail with query: {query}")

        # Search messages
        messages, next_token = await client.search_messages(
            query=query,
            max_results=max_results,
            label_ids=label_ids,
            include_spam_trash=include_spam_trash,
            page_token=page_token,
        )

        # Build result arrays
        message_list = []
        message_ids = []
        for msg in messages:
            message_list.append(
                {
                    "id": msg.id,
                    "thread_id": msg.thread_id,
                    "subject": msg.subject,
                    "from": msg.from_address,
                    "date": msg.date,
                    "snippet": msg.snippet,
                    "label_ids": msg.label_ids,
                }
            )
            message_ids.append(msg.id)

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("messages", message_list)
        self.set_output_value("message_count", len(message_list))
        self.set_output_value("message_ids", message_ids)
        self.set_output_value("next_page_token", next_token or "")

        logger.info(f"Gmail search found {len(messages)} messages")

        return {
            "success": True,
            "message_count": len(message_list),
            "next_page_token": next_token,
            "next_nodes": [],
        }


# ============================================================================
# GmailGetThreadNode
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
        tooltip="Gmail thread ID",
    ),
    GMAIL_FORMAT,
)
@executable_node
class GmailGetThreadNode(GmailBaseNode):
    """
    Get a conversation thread with all messages.

    Inputs:
        - thread_id: Gmail thread ID
        - format: Response format ("minimal", "metadata", "full")

    Outputs:
        - thread_id: Thread ID
        - snippet: Thread snippet
        - messages: Array of message objects in the thread
        - message_count: Number of messages in thread
        - first_message: First message object
        - last_message: Last message object
        - participants: Unique email addresses in thread
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: thread_id, format -> thread_id, snippet, messages, message_count, first_message, last_message, participants

    NODE_TYPE = "gmail_get_thread"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Get Thread"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Get Thread", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Thread-specific inputs
        self.add_input_port("thread_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("format", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("thread_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("snippet", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("messages", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("message_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("first_message", PortType.OUTPUT, DataType.OBJECT)
        self.add_output_port("last_message", PortType.OUTPUT, DataType.OBJECT)
        self.add_output_port("participants", PortType.OUTPUT, DataType.ARRAY)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Get a conversation thread."""
        # Get thread ID
        thread_id = self.get_parameter("thread_id")
        if hasattr(context, "resolve_value"):
            thread_id = context.resolve_value(thread_id)

        if not thread_id:
            self._set_error_outputs("Thread ID is required")
            return {
                "success": False,
                "error": "Thread ID is required",
                "next_nodes": [],
            }

        # Get format
        format_type = self.get_parameter("format") or "full"
        if hasattr(context, "resolve_value"):
            format_type = context.resolve_value(format_type)

        logger.debug(f"Getting Gmail thread {thread_id}")

        # Get thread
        thread = await client.get_thread(thread_id, format_type=format_type)

        # Build message list and collect participants
        message_list = []
        participants = set()
        for msg in thread.messages:
            message_list.append(
                {
                    "id": msg.id,
                    "thread_id": msg.thread_id,
                    "subject": msg.subject,
                    "from": msg.from_address,
                    "to": msg.to_addresses,
                    "date": msg.date,
                    "snippet": msg.snippet,
                    "body_plain": msg.body_plain,
                    "label_ids": msg.label_ids,
                }
            )
            if msg.from_address:
                participants.add(msg.from_address)
            for addr in msg.to_addresses:
                if addr:
                    participants.add(addr)

        # Get first and last messages
        first_message = message_list[0] if message_list else {}
        last_message = message_list[-1] if message_list else {}

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("thread_id", thread.id)
        self.set_output_value("snippet", thread.snippet)
        self.set_output_value("messages", message_list)
        self.set_output_value("message_count", len(message_list))
        self.set_output_value("first_message", first_message)
        self.set_output_value("last_message", last_message)
        self.set_output_value("participants", list(participants))

        logger.info(
            f"Gmail thread retrieved: {thread.id} with {len(message_list)} messages"
        )

        return {
            "success": True,
            "thread_id": thread.id,
            "message_count": len(message_list),
            "next_nodes": [],
        }


# ============================================================================
# GmailGetAttachmentNode
# ============================================================================


@node_schema(
    GMAIL_ACCESS_TOKEN,
    GMAIL_CREDENTIAL_NAME,
    GMAIL_MESSAGE_ID,
    PropertyDef(
        "attachment_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Attachment ID",
        placeholder="ANGjdJ8...",
        tooltip="Attachment ID from message payload",
    ),
    PropertyDef(
        "save_path",
        PropertyType.FILE_PATH,
        default="",
        label="Save Path",
        placeholder="C:\\Downloads\\attachment.pdf",
        tooltip="File path to save the attachment (optional)",
    ),
    PropertyDef(
        "filename",
        PropertyType.STRING,
        default="",
        label="Filename",
        placeholder="document.pdf",
        tooltip="Filename for the attachment (used if no save path specified)",
    ),
)
@executable_node
class GmailGetAttachmentNode(GmailBaseNode):
    """
    Download an email attachment.

    Inputs:
        - message_id: Message ID containing the attachment
        - attachment_id: Attachment ID from message payload
        - save_path: File path to save attachment (optional)
        - filename: Filename for the attachment

    Outputs:
        - attachment_data: Raw attachment bytes (base64 if not saved)
        - save_path: Path where attachment was saved (if saved)
        - filename: Attachment filename
        - size: Attachment size in bytes
        - saved: Whether attachment was saved to disk
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: message_id, attachment_id, save_path, filename -> attachment_data, save_path, filename, size, saved

    NODE_TYPE = "gmail_get_attachment"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Gmail: Get Attachment"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Gmail Get Attachment", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Attachment-specific inputs
        self.add_input_port(
            "message_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "attachment_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "save_path", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("filename", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("attachment_data", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("save_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("filename", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("saved", PortType.OUTPUT, DataType.BOOLEAN)

    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """Download an attachment."""
        # Get message and attachment IDs
        message_id = self.get_parameter("message_id")
        attachment_id = self.get_parameter("attachment_id")
        if hasattr(context, "resolve_value"):
            message_id = context.resolve_value(message_id)
            attachment_id = context.resolve_value(attachment_id)

        if not message_id:
            self._set_error_outputs("Message ID is required")
            return {
                "success": False,
                "error": "Message ID is required",
                "next_nodes": [],
            }

        if not attachment_id:
            self._set_error_outputs("Attachment ID is required")
            return {
                "success": False,
                "error": "Attachment ID is required",
                "next_nodes": [],
            }

        # Get optional save path and filename
        save_path = self.get_parameter("save_path") or ""
        filename = self.get_parameter("filename") or "attachment"
        if hasattr(context, "resolve_value"):
            save_path = context.resolve_value(save_path)
            filename = context.resolve_value(filename)

        logger.debug(f"Getting attachment {attachment_id} from message {message_id}")

        # Get attachment data
        data = await client.get_attachment(message_id, attachment_id)
        size = len(data)

        # Save to file if path provided
        saved = False
        final_path = ""
        if save_path:
            try:
                path = Path(save_path)
                # Create parent directories if needed
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                saved = True
                final_path = str(path)
                logger.info(f"Attachment saved to {final_path}")
            except Exception as e:
                logger.error(f"Failed to save attachment: {e}")
                # Don't fail the node - attachment data is still available
        elif filename:
            # Use filename in current directory
            try:
                # Sanitize filename to prevent path traversal
                safe_filename = Path(filename).name
                path = Path(safe_filename)
                path.write_bytes(data)
                saved = True
                final_path = str(path.absolute())
                logger.info(f"Attachment saved to {final_path}")
            except Exception as e:
                logger.error(f"Failed to save attachment: {e}")

        # Set outputs
        self._set_success_outputs()
        import base64

        # Return base64 encoded data for port compatibility
        self.set_output_value("attachment_data", base64.b64encode(data).decode("utf-8"))
        self.set_output_value("save_path", final_path)
        self.set_output_value("filename", filename)
        self.set_output_value("size", size)
        self.set_output_value("saved", saved)

        logger.info(f"Attachment retrieved: {size} bytes")

        return {
            "success": True,
            "size": size,
            "saved": saved,
            "save_path": final_path,
            "next_nodes": [],
        }


__all__ = [
    "GmailGetEmailNode",
    "GmailSearchEmailsNode",
    "GmailGetThreadNode",
    "GmailGetAttachmentNode",
]
