"""
Gmail nodes for CasareRPA.

Provides nodes for interacting with Gmail API:
- Sending emails and drafts
- Reading and searching emails
- Managing labels, stars, and archive
- Batch operations
"""

import base64
import mimetypes
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


async def _get_gmail_service(context: ExecutionContext, credential_name: str) -> Any:
    """Get authenticated Gmail service from context."""
    google_client = context.resources.get("google_client")
    if not google_client:
        raise RuntimeError("Google client not initialized. Use 'Google: Authenticate' node first.")
    return await google_client.get_service("gmail", "v1", credential_name)


def _create_message(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    body_type: str = "text",
    reply_to: str = "",
) -> dict[str, str]:
    """Create a message for an email."""
    if body_type == "html":
        msg = MIMEText(body, "html")
    else:
        msg = MIMEText(body, "plain")

    msg["to"] = to
    msg["subject"] = subject

    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    if reply_to:
        msg["In-Reply-To"] = reply_to
        msg["References"] = reply_to

    return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}


def _create_message_with_attachment(
    to: str,
    subject: str,
    body: str,
    attachment_paths: list[str],
    cc: str = "",
    bcc: str = "",
    body_type: str = "text",
) -> dict[str, str]:
    """Create a message with attachments."""
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject

    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc

    if body_type == "html":
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "plain"))

    for file_path in attachment_paths:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Attachment not found: {file_path}")
            continue

        content_type, _ = mimetypes.guess_type(str(path))
        if content_type is None:
            content_type = "application/octet-stream"

        main_type, sub_type = content_type.split("/", 1)
        with open(path, "rb") as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())

        from email import encoders

        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=path.name)
        msg.attach(attachment)

    return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}


# =============================================================================
# Send Operations
# =============================================================================


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "to",
        PropertyType.STRING,
        required=True,
        label="To",
        tooltip="Recipient email address",
    ),
    PropertyDef(
        "subject",
        PropertyType.STRING,
        required=True,
        label="Subject",
        tooltip="Email subject",
    ),
    PropertyDef(
        "body",
        PropertyType.TEXT,
        required=True,
        label="Body",
        tooltip="Email body content",
    ),
    PropertyDef(
        "cc",
        PropertyType.STRING,
        label="CC",
        tooltip="CC recipients (comma-separated)",
    ),
    PropertyDef(
        "bcc",
        PropertyType.STRING,
        label="BCC",
        tooltip="BCC recipients (comma-separated)",
    ),
)
@node(category="google")
class GmailSendEmailNode(BaseNode):
    """Send an email via Gmail."""

    # @category: google
    # @requires: email
    # @ports: to, subject, body, cc, bcc -> message_id, thread_id, success, error

    NODE_NAME = "Gmail: Send Email"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("to", DataType.STRING, "Recipient email")
        self.add_input_port("subject", DataType.STRING, "Email subject")
        self.add_input_port("body", DataType.STRING, "Email body")
        self.add_input_port("cc", DataType.STRING, "CC recipients")
        self.add_input_port("bcc", DataType.STRING, "BCC recipients")
        self.add_output_port("message_id", DataType.STRING, "Sent message ID")
        self.add_output_port("thread_id", DataType.STRING, "Thread ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            to = self.get_input_value("to") or self.get_parameter("to", "")
            subject = self.get_input_value("subject") or self.get_parameter("subject", "")
            body = self.get_input_value("body") or self.get_parameter("body", "")
            cc = self.get_input_value("cc") or self.get_parameter("cc", "")
            bcc = self.get_input_value("bcc") or self.get_parameter("bcc", "")
            body_type = self.get_parameter("body_type", "text")

            if not to:
                raise ValueError("Recipient (to) is required")
            if not subject:
                raise ValueError("Subject is required")

            service = await _get_gmail_service(context, credential_name)
            message = _create_message(to, subject, body, cc, bcc, body_type)

            result = service.users().messages().send(userId="me", body=message).execute()

            self.set_output_value("message_id", result.get("id", ""))
            self.set_output_value("thread_id", result.get("threadId", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": result.get("id")}

        except Exception as e:
            logger.error(f"Gmail send error: {e}")
            self.set_output_value("message_id", "")
            self.set_output_value("thread_id", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "to",
        PropertyType.STRING,
        required=True,
        label="To",
        tooltip="Recipient email address",
    ),
    PropertyDef(
        "subject",
        PropertyType.STRING,
        required=True,
        label="Subject",
        tooltip="Email subject",
    ),
    PropertyDef(
        "body",
        PropertyType.TEXT,
        required=True,
        label="Body",
        tooltip="Email body content",
    ),
    PropertyDef(
        "attachments",
        PropertyType.LIST,
        required=True,
        label="Attachments",
        tooltip="List of file paths to attach",
    ),
    PropertyDef(
        "cc",
        PropertyType.STRING,
        label="CC",
        tooltip="CC recipients (comma-separated)",
    ),
    PropertyDef(
        "bcc",
        PropertyType.STRING,
        label="BCC",
        tooltip="BCC recipients (comma-separated)",
    ),
    PropertyDef(
        "body_type",
        PropertyType.CHOICE,
        default="text",
        choices=["text", "html"],
        label="Body Type",
        tooltip="Type of email body (text or html)",
    ),
)
@node(category="google")
class GmailSendWithAttachmentNode(BaseNode):
    """Send an email with attachments via Gmail."""

    # @category: google
    # @requires: email
    # @ports: to, subject, body, attachments, cc, bcc -> message_id, thread_id, success, error

    NODE_NAME = "Gmail: Send With Attachment"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("to", DataType.STRING, "Recipient email")
        self.add_input_port("subject", DataType.STRING, "Email subject")
        self.add_input_port("body", DataType.STRING, "Email body")
        self.add_input_port("attachments", DataType.LIST, "File paths to attach")
        self.add_input_port("cc", DataType.STRING, "CC recipients")
        self.add_input_port("bcc", DataType.STRING, "BCC recipients")
        self.add_output_port("message_id", DataType.STRING, "Sent message ID")
        self.add_output_port("thread_id", DataType.STRING, "Thread ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            to = self.get_input_value("to") or self.get_parameter("to", "")
            subject = self.get_input_value("subject") or self.get_parameter("subject", "")
            body = self.get_input_value("body") or self.get_parameter("body", "")
            attachments = self.get_input_value("attachments") or []
            cc = self.get_input_value("cc") or self.get_parameter("cc", "")
            bcc = self.get_input_value("bcc") or self.get_parameter("bcc", "")
            body_type = self.get_parameter("body_type", "text")

            if not to:
                raise ValueError("Recipient (to) is required")
            if not subject:
                raise ValueError("Subject is required")

            service = await _get_gmail_service(context, credential_name)
            message = _create_message_with_attachment(
                to, subject, body, attachments, cc, bcc, body_type
            )

            result = service.users().messages().send(userId="me", body=message).execute()

            self.set_output_value("message_id", result.get("id", ""))
            self.set_output_value("thread_id", result.get("threadId", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": result.get("id")}

        except Exception as e:
            logger.error(f"Gmail send with attachment error: {e}")
            self.set_output_value("message_id", "")
            self.set_output_value("thread_id", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "to",
        PropertyType.STRING,
        required=True,
        label="To",
        tooltip="Recipient email address",
    ),
    PropertyDef(
        "subject",
        PropertyType.STRING,
        required=True,
        label="Subject",
        tooltip="Email subject",
    ),
    PropertyDef(
        "body",
        PropertyType.TEXT,
        required=True,
        label="Body",
        tooltip="Email body content",
    ),
    PropertyDef(
        "cc",
        PropertyType.STRING,
        label="CC",
        tooltip="CC recipients (comma-separated)",
    ),
    PropertyDef(
        "bcc",
        PropertyType.STRING,
        label="BCC",
        tooltip="BCC recipients (comma-separated)",
    ),
    PropertyDef(
        "body_type",
        PropertyType.CHOICE,
        default="text",
        choices=["text", "html"],
        label="Body Type",
        tooltip="Type of email body (text or html)",
    ),
)
@node(category="google")
class GmailCreateDraftNode(BaseNode):
    """Create a draft email in Gmail."""

    # @category: google
    # @requires: email
    # @ports: to, subject, body, cc, bcc -> draft_id, message_id, success, error

    NODE_NAME = "Gmail: Create Draft"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("to", DataType.STRING, "Recipient email")
        self.add_input_port("subject", DataType.STRING, "Email subject")
        self.add_input_port("body", DataType.STRING, "Email body")
        self.add_input_port("cc", DataType.STRING, "CC recipients")
        self.add_input_port("bcc", DataType.STRING, "BCC recipients")
        self.add_output_port("draft_id", DataType.STRING, "Draft ID")
        self.add_output_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            to = self.get_input_value("to") or self.get_parameter("to", "")
            subject = self.get_input_value("subject") or self.get_parameter("subject", "")
            body = self.get_input_value("body") or self.get_parameter("body", "")
            cc = self.get_input_value("cc") or self.get_parameter("cc", "")
            bcc = self.get_input_value("bcc") or self.get_parameter("bcc", "")
            body_type = self.get_parameter("body_type", "text")

            service = await _get_gmail_service(context, credential_name)
            message = _create_message(to, subject, body, cc, bcc, body_type)

            result = (
                service.users().drafts().create(userId="me", body={"message": message}).execute()
            )

            self.set_output_value("draft_id", result.get("id", ""))
            self.set_output_value("message_id", result.get("message", {}).get("id", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "draft_id": result.get("id")}

        except Exception as e:
            logger.error(f"Gmail create draft error: {e}")
            self.set_output_value("draft_id", "")
            self.set_output_value("message_id", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "draft_id",
        PropertyType.STRING,
        required=True,
        label="Draft ID",
        tooltip="ID of the draft to send",
    ),
)
@node(category="google")
class GmailSendDraftNode(BaseNode):
    """Send an existing draft from Gmail."""

    # @category: google
    # @requires: email
    # @ports: draft_id -> message_id, thread_id, success, error

    NODE_NAME = "Gmail: Send Draft"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("draft_id", DataType.STRING, "Draft ID to send")
        self.add_output_port("message_id", DataType.STRING, "Sent message ID")
        self.add_output_port("thread_id", DataType.STRING, "Thread ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            draft_id = self.get_input_value("draft_id") or self.get_parameter("draft_id", "")

            if not draft_id:
                raise ValueError("Draft ID is required")

            service = await _get_gmail_service(context, credential_name)

            result = service.users().drafts().send(userId="me", body={"id": draft_id}).execute()

            self.set_output_value("message_id", result.get("id", ""))
            self.set_output_value("thread_id", result.get("threadId", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": result.get("id")}

        except Exception as e:
            logger.error(f"Gmail send draft error: {e}")
            self.set_output_value("message_id", "")
            self.set_output_value("thread_id", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Read Operations
# =============================================================================


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to retrieve",
    ),
    PropertyDef(
        "format",
        PropertyType.CHOICE,
        default="full",
        choices=["full", "metadata", "minimal", "raw"],
        label="Format",
        tooltip="Format of the returned message",
    ),
)
@node(category="google")
class GmailGetEmailNode(BaseNode):
    """Get a specific email by ID from Gmail."""

    # @category: google
    # @requires: email
    # @ports: message_id -> subject, from, to, date, body, snippet, labels, attachments, success, error

    NODE_NAME = "Gmail: Get Email"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("subject", DataType.STRING, "Email subject")
        self.add_output_port("from", DataType.STRING, "Sender email")
        self.add_output_port("to", DataType.STRING, "Recipient email")
        self.add_output_port("date", DataType.STRING, "Date received")
        self.add_output_port("body", DataType.STRING, "Email body")
        self.add_output_port("snippet", DataType.STRING, "Email snippet")
        self.add_output_port("labels", DataType.LIST, "Label IDs")
        self.add_output_port("attachments", DataType.LIST, "Attachment info")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")
            format_type = self.get_parameter("format", "full")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            result = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format=format_type)
                .execute()
            )

            headers = {h["name"]: h["value"] for h in result.get("payload", {}).get("headers", [])}

            body = ""
            payload = result.get("payload", {})
            if "body" in payload and payload["body"].get("data"):
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode()
            elif "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode()
                        break

            attachments = []
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("filename"):
                        attachments.append(
                            {
                                "filename": part["filename"],
                                "mimeType": part.get("mimeType", ""),
                                "size": part.get("body", {}).get("size", 0),
                                "attachmentId": part.get("body", {}).get("attachmentId", ""),
                            }
                        )

            self.set_output_value("subject", headers.get("Subject", ""))
            self.set_output_value("from", headers.get("From", ""))
            self.set_output_value("to", headers.get("To", ""))
            self.set_output_value("date", headers.get("Date", ""))
            self.set_output_value("body", body)
            self.set_output_value("snippet", result.get("snippet", ""))
            self.set_output_value("labels", result.get("labelIds", []))
            self.set_output_value("attachments", attachments)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail get email error: {e}")
            self.set_output_value("subject", "")
            self.set_output_value("from", "")
            self.set_output_value("to", "")
            self.set_output_value("date", "")
            self.set_output_value("body", "")
            self.set_output_value("snippet", "")
            self.set_output_value("labels", [])
            self.set_output_value("attachments", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "max_results",
        PropertyType.INTEGER,
        default=10,
        min_value=1,
        max_value=500,
        label="Max Results",
        tooltip="Maximum number of messages to return",
    ),
    PropertyDef(
        "label_ids",
        PropertyType.LIST,
        default=["INBOX"],
        label="Label IDs",
        tooltip="List of label IDs to filter by (e.g., ['INBOX', 'UNREAD'])",
    ),
    PropertyDef(
        "page_token",
        PropertyType.STRING,
        label="Page Token",
        tooltip="Token for the next page of results",
    ),
)
@node(category="google")
class GmailListEmailsNode(BaseNode):
    """List emails from Gmail inbox."""

    # @category: google
    # @requires: email
    # @ports: max_results, label_ids -> messages, count, next_page_token, success, error

    NODE_NAME = "Gmail: List Emails"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("max_results", DataType.INTEGER, "Maximum results")
        self.add_input_port("label_ids", DataType.LIST, "Label IDs to filter")
        self.add_output_port("messages", DataType.LIST, "List of message objects")
        self.add_output_port("count", DataType.INTEGER, "Number of messages")
        self.add_output_port("next_page_token", DataType.STRING, "Next page token")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            max_results = self.get_input_value("max_results") or self.get_parameter(
                "max_results", 10
            )
            label_ids = self.get_input_value("label_ids") or self.get_parameter(
                "label_ids", ["INBOX"]
            )
            page_token = self.get_parameter("page_token", "")

            service = await _get_gmail_service(context, credential_name)

            params = {"userId": "me", "maxResults": max_results, "labelIds": label_ids}
            if page_token:
                params["pageToken"] = page_token

            result = service.users().messages().list(**params).execute()

            messages = result.get("messages", [])

            self.set_output_value("messages", messages)
            self.set_output_value("count", len(messages))
            self.set_output_value("next_page_token", result.get("nextPageToken", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "count": len(messages)}

        except Exception as e:
            logger.error(f"Gmail list emails error: {e}")
            self.set_output_value("messages", [])
            self.set_output_value("count", 0)
            self.set_output_value("next_page_token", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "query",
        PropertyType.STRING,
        required=True,
        label="Search Query",
        tooltip="Gmail search query (e.g., 'from:someone@example.com')",
    ),
    PropertyDef(
        "max_results",
        PropertyType.INTEGER,
        default=10,
        min_value=1,
        max_value=500,
        label="Max Results",
        tooltip="Maximum number of messages to return",
    ),
    PropertyDef(
        "page_token",
        PropertyType.STRING,
        label="Page Token",
        tooltip="Token for the next page of results",
    ),
)
@node(category="google")
class GmailSearchEmailsNode(BaseNode):
    """Search emails in Gmail using query."""

    # @category: google
    # @requires: email
    # @ports: query, max_results -> messages, count, next_page_token, success, error

    NODE_NAME = "Gmail: Search Emails"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("query", DataType.STRING, "Search query")
        self.add_input_port("max_results", DataType.INTEGER, "Maximum results")
        self.add_output_port("messages", DataType.LIST, "List of message objects")
        self.add_output_port("count", DataType.INTEGER, "Number of messages")
        self.add_output_port("next_page_token", DataType.STRING, "Next page token")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            query = self.get_input_value("query") or self.get_parameter("query", "")
            max_results = self.get_input_value("max_results") or self.get_parameter(
                "max_results", 10
            )
            page_token = self.get_parameter("page_token", "")

            if not query:
                raise ValueError("Search query is required")

            service = await _get_gmail_service(context, credential_name)

            params = {"userId": "me", "q": query, "maxResults": max_results}
            if page_token:
                params["pageToken"] = page_token

            result = service.users().messages().list(**params).execute()

            messages = result.get("messages", [])

            self.set_output_value("messages", messages)
            self.set_output_value("count", len(messages))
            self.set_output_value("next_page_token", result.get("nextPageToken", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "count": len(messages)}

        except Exception as e:
            logger.error(f"Gmail search emails error: {e}")
            self.set_output_value("messages", [])
            self.set_output_value("count", 0)
            self.set_output_value("next_page_token", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "thread_id",
        PropertyType.STRING,
        required=True,
        label="Thread ID",
        tooltip="ID of the thread to retrieve",
    ),
)
@node(category="google")
class GmailGetThreadNode(BaseNode):
    """Get a complete email thread from Gmail."""

    # @category: google
    # @requires: email
    # @ports: thread_id -> messages, count, snippet, success, error

    NODE_NAME = "Gmail: Get Thread"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("thread_id", DataType.STRING, "Thread ID")
        self.add_output_port("messages", DataType.LIST, "Thread messages")
        self.add_output_port("count", DataType.INTEGER, "Number of messages in thread")
        self.add_output_port("snippet", DataType.STRING, "Thread snippet")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            thread_id = self.get_input_value("thread_id") or self.get_parameter("thread_id", "")

            if not thread_id:
                raise ValueError("Thread ID is required")

            service = await _get_gmail_service(context, credential_name)

            result = (
                service.users().threads().get(userId="me", id=thread_id, format="full").execute()
            )

            messages = result.get("messages", [])

            self.set_output_value("messages", messages)
            self.set_output_value("count", len(messages))
            self.set_output_value("snippet", result.get("snippet", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "thread_id": thread_id, "count": len(messages)}

        except Exception as e:
            logger.error(f"Gmail get thread error: {e}")
            self.set_output_value("messages", [])
            self.set_output_value("count", 0)
            self.set_output_value("snippet", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Management Operations
# =============================================================================


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to modify",
    ),
    PropertyDef(
        "add_labels",
        PropertyType.LIST,
        label="Add Labels",
        tooltip="List of label IDs to add",
    ),
    PropertyDef(
        "remove_labels",
        PropertyType.LIST,
        label="Remove Labels",
        tooltip="List of label IDs to remove",
    ),
)
@node(category="google")
class GmailModifyLabelsNode(BaseNode):
    """Modify labels on a Gmail message."""

    # @category: google
    # @requires: email
    # @ports: message_id, add_labels, remove_labels -> labels, success, error

    NODE_NAME = "Gmail: Modify Labels"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_input_port("add_labels", DataType.LIST, "Labels to add")
        self.add_input_port("remove_labels", DataType.LIST, "Labels to remove")
        self.add_output_port("labels", DataType.LIST, "Updated labels")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")
            add_labels = self.get_input_value("add_labels") or []
            remove_labels = self.get_input_value("remove_labels") or []

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            body = {}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels

            result = (
                service.users().messages().modify(userId="me", id=message_id, body=body).execute()
            )

            self.set_output_value("labels", result.get("labelIds", []))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail modify labels error: {e}")
            self.set_output_value("labels", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to move to trash",
    ),
)
@node(category="google")
class GmailMoveToTrashNode(BaseNode):
    """Move a Gmail message to trash."""

    # @category: google
    # @requires: email
    # @ports: message_id -> success, error

    NODE_NAME = "Gmail: Move to Trash"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().trash(userId="me", id=message_id).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail move to trash error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to mark as read",
    ),
)
@node(category="google")
class GmailMarkAsReadNode(BaseNode):
    """Mark a Gmail message as read."""

    # @category: google
    # @requires: email
    # @ports: message_id -> success, error

    NODE_NAME = "Gmail: Mark as Read"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail mark as read error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to mark as unread",
    ),
)
@node(category="google")
class GmailMarkAsUnreadNode(BaseNode):
    """Mark a Gmail message as unread."""

    # @category: google
    # @requires: email
    # @ports: message_id -> success, error

    NODE_NAME = "Gmail: Mark as Unread"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().modify(
                userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail mark as unread error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to star/unstar",
    ),
    PropertyDef(
        "star",
        PropertyType.BOOLEAN,
        default=True,
        label="Star",
        tooltip="Whether to star (True) or unstar (False) the message",
    ),
)
@node(category="google")
class GmailStarEmailNode(BaseNode):
    """Star or unstar a Gmail message."""

    # @category: google
    # @requires: email
    # @ports: message_id, star -> success, error

    NODE_NAME = "Gmail: Star Email"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_input_port("star", DataType.BOOLEAN, "Star (True) or Unstar (False)")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")
            star = self.get_input_value("star")
            if star is None:
                star = self.get_parameter("star", True)

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            if star:
                body = {"addLabelIds": ["STARRED"]}
            else:
                body = {"removeLabelIds": ["STARRED"]}

            service.users().messages().modify(userId="me", id=message_id, body=body).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail star email error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to archive",
    ),
)
@node(category="google")
class GmailArchiveEmailNode(BaseNode):
    """Archive a Gmail message (remove from inbox)."""

    # @category: google
    # @requires: email
    # @ports: message_id -> success, error

    NODE_NAME = "Gmail: Archive Email"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail archive email error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to permanently delete",
    ),
)
@node(category="google")
class GmailDeleteEmailNode(BaseNode):
    """Permanently delete a Gmail message."""

    # @category: google
    # @requires: email
    # @ports: message_id -> success, error

    NODE_NAME = "Gmail: Delete Email"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().delete(userId="me", id=message_id).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail delete email error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Batch Operations
# =============================================================================


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "emails",
        PropertyType.LIST,
        required=True,
        label="Emails",
        tooltip="List of email objects to send (each with to, subject, body)",
    ),
)
@node(category="google")
class GmailBatchSendNode(BaseNode):
    """Send multiple emails in batch."""

    # @category: google
    # @requires: email
    # @ports: emails -> results, sent_count, failed_count, success, error

    NODE_NAME = "Gmail: Batch Send"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("emails", DataType.LIST, "Array of email objects")
        self.add_output_port("results", DataType.LIST, "Send results")
        self.add_output_port("sent_count", DataType.INTEGER, "Number sent")
        self.add_output_port("failed_count", DataType.INTEGER, "Number failed")
        self.add_output_port("success", DataType.BOOLEAN, "Overall success")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            emails = self.get_input_value("emails") or []

            if not emails:
                raise ValueError("Emails array is required")

            service = await _get_gmail_service(context, credential_name)

            results = []
            sent_count = 0
            failed_count = 0

            for email in emails:
                try:
                    to = email.get("to", "")
                    subject = email.get("subject", "")
                    body = email.get("body", "")
                    cc = email.get("cc", "")
                    bcc = email.get("bcc", "")
                    body_type = email.get("body_type", "text")

                    message = _create_message(to, subject, body, cc, bcc, body_type)
                    result = service.users().messages().send(userId="me", body=message).execute()

                    results.append(
                        {
                            "to": to,
                            "message_id": result.get("id"),
                            "success": True,
                        }
                    )
                    sent_count += 1

                except Exception as e:
                    results.append(
                        {
                            "to": email.get("to", ""),
                            "success": False,
                            "error": str(e),
                        }
                    )
                    failed_count += 1

            self.set_output_value("results", results)
            self.set_output_value("sent_count", sent_count)
            self.set_output_value("failed_count", failed_count)
            self.set_output_value("success", failed_count == 0)
            self.set_output_value(
                "error", "" if failed_count == 0 else f"{failed_count} emails failed"
            )

            return {
                "success": failed_count == 0,
                "sent_count": sent_count,
                "failed_count": failed_count,
            }

        except Exception as e:
            logger.error(f"Gmail batch send error: {e}")
            self.set_output_value("results", [])
            self.set_output_value("sent_count", 0)
            self.set_output_value("failed_count", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_ids",
        PropertyType.LIST,
        required=True,
        label="Message IDs",
        tooltip="List of message IDs to modify",
    ),
    PropertyDef(
        "add_labels",
        PropertyType.LIST,
        label="Add Labels",
        tooltip="List of label IDs to add to all messages",
    ),
    PropertyDef(
        "remove_labels",
        PropertyType.LIST,
        label="Remove Labels",
        tooltip="List of label IDs to remove from all messages",
    ),
)
@node(category="google")
class GmailBatchModifyNode(BaseNode):
    """Modify multiple Gmail messages in batch."""

    # @category: google
    # @requires: email
    # @ports: message_ids, add_labels, remove_labels -> modified_count, success, error

    NODE_NAME = "Gmail: Batch Modify"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_ids", DataType.LIST, "Array of message IDs")
        self.add_input_port("add_labels", DataType.LIST, "Labels to add")
        self.add_input_port("remove_labels", DataType.LIST, "Labels to remove")
        self.add_output_port("modified_count", DataType.INTEGER, "Number modified")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_ids = self.get_input_value("message_ids") or []
            add_labels = self.get_input_value("add_labels") or []
            remove_labels = self.get_input_value("remove_labels") or []

            if not message_ids:
                raise ValueError("Message IDs array is required")

            service = await _get_gmail_service(context, credential_name)

            body = {"ids": message_ids}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels

            service.users().messages().batchModify(userId="me", body=body).execute()

            self.set_output_value("modified_count", len(message_ids))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "modified_count": len(message_ids)}

        except Exception as e:
            logger.error(f"Gmail batch modify error: {e}")
            self.set_output_value("modified_count", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_ids",
        PropertyType.LIST,
        required=True,
        label="Message IDs",
        tooltip="List of message IDs to permanently delete",
    ),
)
@node(category="google")
class GmailBatchDeleteNode(BaseNode):
    """Delete multiple Gmail messages in batch."""

    # @category: google
    # @requires: email
    # @ports: message_ids -> deleted_count, success, error

    NODE_NAME = "Gmail: Batch Delete"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_ids", DataType.LIST, "Array of message IDs")
        self.add_output_port("deleted_count", DataType.INTEGER, "Number deleted")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_ids = self.get_input_value("message_ids") or []

            if not message_ids:
                raise ValueError("Message IDs array is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().batchDelete(userId="me", body={"ids": message_ids}).execute()

            self.set_output_value("deleted_count", len(message_ids))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "deleted_count": len(message_ids)}

        except Exception as e:
            logger.error(f"Gmail batch delete error: {e}")
            self.set_output_value("deleted_count", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Additional Management Operations
# =============================================================================


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to add labels to",
    ),
    PropertyDef(
        "label_ids",
        PropertyType.LIST,
        required=True,
        label="Label IDs",
        tooltip="List of label IDs to add",
    ),
)
@node(category="google")
class GmailAddLabelNode(BaseNode):
    """Add label(s) to a Gmail message."""

    # @category: google
    # @requires: email
    # @ports: message_id, label_ids -> labels, success, error

    NODE_NAME = "Gmail: Add Label"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_input_port("label_ids", DataType.LIST, "Label IDs to add")
        self.add_output_port("labels", DataType.LIST, "Updated labels")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")
            label_ids = self.get_input_value("label_ids") or self.get_parameter("label_ids", [])

            if not message_id:
                raise ValueError("Message ID is required")
            if not label_ids:
                raise ValueError("Label IDs are required")

            # Ensure label_ids is a list
            if isinstance(label_ids, str):
                label_ids = [label_ids]

            service = await _get_gmail_service(context, credential_name)

            result = (
                service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": label_ids})
                .execute()
            )

            self.set_output_value("labels", result.get("labelIds", []))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Added labels {label_ids} to message {message_id}")
            return {
                "success": True,
                "message_id": message_id,
                "labels_added": label_ids,
            }

        except Exception as e:
            logger.error(f"Gmail add label error: {e}")
            self.set_output_value("labels", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to remove labels from",
    ),
    PropertyDef(
        "label_ids",
        PropertyType.LIST,
        required=True,
        label="Label IDs",
        tooltip="List of label IDs to remove",
    ),
)
@node(category="google")
class GmailRemoveLabelNode(BaseNode):
    """Remove label(s) from a Gmail message."""

    # @category: google
    # @requires: email
    # @ports: message_id, label_ids -> labels, success, error

    NODE_NAME = "Gmail: Remove Label"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID")
        self.add_input_port("label_ids", DataType.LIST, "Label IDs to remove")
        self.add_output_port("labels", DataType.LIST, "Updated labels")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")
            label_ids = self.get_input_value("label_ids") or self.get_parameter("label_ids", [])

            if not message_id:
                raise ValueError("Message ID is required")
            if not label_ids:
                raise ValueError("Label IDs are required")

            # Ensure label_ids is a list
            if isinstance(label_ids, str):
                label_ids = [label_ids]

            service = await _get_gmail_service(context, credential_name)

            result = (
                service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"removeLabelIds": label_ids})
                .execute()
            )

            self.set_output_value("labels", result.get("labelIds", []))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Removed labels {label_ids} from message {message_id}")
            return {
                "success": True,
                "message_id": message_id,
                "labels_removed": label_ids,
            }

        except Exception as e:
            logger.error(f"Gmail remove label error: {e}")
            self.set_output_value("labels", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties()
@node(category="google")
class GmailGetLabelsNode(BaseNode):
    """Get all labels from Gmail account."""

    # @category: google
    # @requires: email
    # @ports: none -> labels, count, success, error

    NODE_NAME = "Gmail: Get Labels"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_output_port("labels", DataType.LIST, "List of label objects")
        self.add_output_port("count", DataType.INTEGER, "Number of labels")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")

            service = await _get_gmail_service(context, credential_name)

            result = service.users().labels().list(userId="me").execute()

            labels = result.get("labels", [])

            # Format labels for easier use
            formatted_labels = []
            for label in labels:
                formatted_labels.append(
                    {
                        "id": label.get("id", ""),
                        "name": label.get("name", ""),
                        "type": label.get("type", ""),
                        "messageListVisibility": label.get("messageListVisibility", ""),
                        "labelListVisibility": label.get("labelListVisibility", ""),
                        "messagesTotal": label.get("messagesTotal", 0),
                        "messagesUnread": label.get("messagesUnread", 0),
                        "threadsTotal": label.get("threadsTotal", 0),
                        "threadsUnread": label.get("threadsUnread", 0),
                    }
                )

            self.set_output_value("labels", formatted_labels)
            self.set_output_value("count", len(formatted_labels))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "count": len(formatted_labels)}

        except Exception as e:
            logger.error(f"Gmail get labels error: {e}")
            self.set_output_value("labels", [])
            self.set_output_value("count", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        tooltip="Name of the Google credential to use",
    ),
    PropertyDef(
        "message_id",
        PropertyType.STRING,
        required=True,
        label="Message ID",
        tooltip="ID of the message to trash",
    ),
)
@node(category="google")
class GmailTrashEmailNode(BaseNode):
    """Move a Gmail message to trash (alias for MoveToTrash with clearer name)."""

    # @category: google
    # @requires: email
    # @ports: message_id -> success, error

    NODE_NAME = "Gmail: Trash Email"
    CATEGORY = "google/gmail"

    def _define_ports(self) -> None:
        self.add_input_port("message_id", DataType.STRING, "Message ID to trash")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            message_id = self.get_input_value("message_id") or self.get_parameter("message_id", "")

            if not message_id:
                raise ValueError("Message ID is required")

            service = await _get_gmail_service(context, credential_name)

            service.users().messages().trash(userId="me", id=message_id).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Trashed message {message_id}")
            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error(f"Gmail trash email error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}
