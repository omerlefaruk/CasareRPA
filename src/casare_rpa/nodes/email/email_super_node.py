"""
CasareRPA - Email Super Node

Consolidates all email operations into a single configurable node.
Supports SMTP sending and IMAP reading/management.
"""

from __future__ import annotations

import asyncio
import email as email_module
import imaplib
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.credentials import (
    CREDENTIAL_NAME_PROP,
    CredentialAwareMixin,
)
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext

from .email_base import decode_header_value, parse_email_message


class EmailAction(str, Enum):
    """Email operations."""

    SEND = "Send Email"
    READ = "Read Emails"
    MARK = "Mark Email"
    DELETE = "Delete Email"
    MOVE = "Move Email"
    SAVE_ATTACHMENT = "Save Attachment"


@node(category="email")
@properties(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=EmailAction.SEND.value,
        choices=[a.value for a in EmailAction],
        label="Action",
        tooltip="Email operation to perform",
        essential=True,
    ),
    # Credential
    CREDENTIAL_NAME_PROP,
    # Common connection properties
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
        tab="connection",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
        tab="connection",
    ),
    # SMTP properties (SEND action)
    PropertyDef(
        "smtp_server",
        PropertyType.STRING,
        default="smtp.gmail.com",
        label="SMTP Server",
        tooltip="SMTP server hostname",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "smtp_port",
        PropertyType.INTEGER,
        default=587,
        label="SMTP Port",
        tooltip="SMTP server port",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "from_email",
        PropertyType.STRING,
        default="",
        label="From Email",
        tooltip="Sender email address",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "to_email",
        PropertyType.STRING,
        default="",
        label="To Email",
        tooltip="Recipient email address(es), comma-separated",
        display_when={"action": EmailAction.SEND.value},
        essential=True,
    ),
    PropertyDef(
        "subject",
        PropertyType.STRING,
        default="",
        label="Subject",
        tooltip="Email subject line",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "body",
        PropertyType.TEXT,
        default="",
        label="Body",
        tooltip="Email message body",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "cc",
        PropertyType.STRING,
        default="",
        label="CC",
        tooltip="CC recipients, comma-separated",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "bcc",
        PropertyType.STRING,
        default="",
        label="BCC",
        tooltip="BCC recipients, comma-separated",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "is_html",
        PropertyType.BOOLEAN,
        default=False,
        label="HTML Body",
        tooltip="Body contains HTML content",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "use_tls",
        PropertyType.BOOLEAN,
        default=True,
        label="Use TLS",
        tooltip="Use TLS encryption (SMTP)",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "use_smtp_ssl",
        PropertyType.BOOLEAN,
        default=False,
        label="Use SSL",
        tooltip="Use SSL encryption (SMTP)",
        display_when={"action": EmailAction.SEND.value},
    ),
    PropertyDef(
        "priority",
        PropertyType.CHOICE,
        default="normal",
        choices=["high", "normal", "low"],
        label="Priority",
        tooltip="Email priority level",
        display_when={"action": EmailAction.SEND.value},
    ),
    # IMAP properties (READ, MARK, DELETE, MOVE, SAVE_ATTACHMENT actions)
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
        display_when={
            "action": [
                EmailAction.READ.value,
                EmailAction.MARK.value,
                EmailAction.DELETE.value,
                EmailAction.MOVE.value,
                EmailAction.SAVE_ATTACHMENT.value,
            ]
        },
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
        display_when={
            "action": [
                EmailAction.READ.value,
                EmailAction.MARK.value,
                EmailAction.DELETE.value,
                EmailAction.MOVE.value,
                EmailAction.SAVE_ATTACHMENT.value,
            ]
        },
    ),
    PropertyDef(
        "use_imap_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Use SSL",
        tooltip="Use SSL encryption (IMAP)",
        display_when={
            "action": [
                EmailAction.READ.value,
                EmailAction.MARK.value,
                EmailAction.DELETE.value,
                EmailAction.MOVE.value,
                EmailAction.SAVE_ATTACHMENT.value,
            ]
        },
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
        display_when={
            "action": [
                EmailAction.READ.value,
                EmailAction.MARK.value,
                EmailAction.DELETE.value,
                EmailAction.MOVE.value,
                EmailAction.SAVE_ATTACHMENT.value,
            ]
        },
    ),
    # READ-specific properties
    PropertyDef(
        "limit",
        PropertyType.INTEGER,
        default=10,
        min_value=0,
        label="Limit",
        tooltip="Maximum number of emails to retrieve",
        display_when={"action": EmailAction.READ.value},
    ),
    PropertyDef(
        "search_criteria",
        PropertyType.STRING,
        default="ALL",
        label="Search Criteria",
        tooltip="IMAP search criteria (e.g., ALL, UNSEEN, FROM 'sender@example.com')",
        display_when={"action": EmailAction.READ.value},
    ),
    PropertyDef(
        "newest_first",
        PropertyType.BOOLEAN,
        default=True,
        label="Newest First",
        tooltip="Return newest emails first",
        display_when={"action": EmailAction.READ.value},
    ),
    # MARK-specific properties
    PropertyDef(
        "mark_as",
        PropertyType.CHOICE,
        default="read",
        choices=["read", "unread", "flagged", "unflagged"],
        label="Mark As",
        tooltip="Flag to set on the email",
        display_when={"action": EmailAction.MARK.value},
    ),
    # DELETE-specific properties
    PropertyDef(
        "permanent_delete",
        PropertyType.BOOLEAN,
        default=False,
        label="Permanent Delete",
        tooltip="Permanently delete (expunge) instead of just marking deleted",
        display_when={"action": EmailAction.DELETE.value},
    ),
    # MOVE-specific properties
    PropertyDef(
        "target_folder",
        PropertyType.STRING,
        default="",
        label="Target Folder",
        tooltip="Target mailbox folder",
        display_when={"action": EmailAction.MOVE.value},
    ),
    # SAVE_ATTACHMENT-specific properties
    PropertyDef(
        "save_path",
        PropertyType.STRING,
        default=".",
        label="Save Path",
        tooltip="Directory path to save attachments",
        display_when={"action": EmailAction.SAVE_ATTACHMENT.value},
    ),
    # Common advanced properties
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        label="Timeout (seconds)",
        tooltip="Connection timeout",
        tab="advanced",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
        tab="advanced",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=2000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts",
        tab="advanced",
    ),
)
class EmailSuperNode(CredentialAwareMixin, BaseNode):
    """
    Unified email operations node.

    Consolidates all email operations:
    - SEND: Send email via SMTP
    - READ: Read emails from IMAP
    - MARK: Mark email as read/unread/flagged
    - DELETE: Delete email from mailbox
    - MOVE: Move email to different folder
    - SAVE_ATTACHMENT: Save email attachments to disk

    Features:
    - SMTP and IMAP support
    - SSL/TLS encryption
    - Credential resolution via vault
    - Retry logic with configurable intervals
    - Attachment handling
    """

    NODE_NAME = "Email"
    NODE_CATEGORY = "Communication"
    NODE_DESCRIPTION = "Unified email operations (Send, Read, Mark, Delete, Move)"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = self.NODE_NAME
        self.node_type = "EmailSuperNode"

    def _define_ports(self) -> None:
        """Define dynamic ports based on action."""
        # Execution ports
        self.add_exec_input_port("exec_in")
        self.add_exec_output_port("exec_out")
        self.add_exec_output_port("exec_error")

        # Common input
        self.add_input_port("action", DataType.STRING, required=False)

        # Connection inputs
        self.add_input_port("username", DataType.STRING, required=False)
        self.add_input_port("password", DataType.STRING, required=False)

        # SMTP inputs
        self.add_input_port("smtp_server", DataType.STRING, required=False)
        self.add_input_port("smtp_port", DataType.INTEGER, required=False)
        self.add_input_port("from_email", DataType.STRING, required=False)
        self.add_input_port("to_email", DataType.STRING, required=False)
        self.add_input_port("subject", DataType.STRING, required=False)
        self.add_input_port("body", DataType.STRING, required=False)
        self.add_input_port("cc", DataType.STRING, required=False)
        self.add_input_port("bcc", DataType.STRING, required=False)
        self.add_input_port("attachments", DataType.LIST, required=False)

        # IMAP inputs
        self.add_input_port("imap_server", DataType.STRING, required=False)
        self.add_input_port("imap_port", DataType.INTEGER, required=False)
        self.add_input_port("folder", DataType.STRING, required=False)
        self.add_input_port("email_uid", DataType.STRING, required=False)
        self.add_input_port("target_folder", DataType.STRING, required=False)
        self.add_input_port("save_path", DataType.STRING, required=False)

        # Outputs
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("message_id", DataType.STRING)
        self.add_output_port("emails", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)
        self.add_output_port("saved_files", DataType.LIST)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute the selected email action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", EmailAction.SEND.value)
        if hasattr(context, "resolve_value"):
            action = context.resolve_value(action)

        handlers = {
            EmailAction.SEND.value: self._execute_send,
            EmailAction.READ.value: self._execute_read,
            EmailAction.MARK.value: self._execute_mark,
            EmailAction.DELETE.value: self._execute_delete,
            EmailAction.MOVE.value: self._execute_move,
            EmailAction.SAVE_ATTACHMENT.value: self._execute_save_attachment,
        }

        handler = handlers.get(action)
        if not handler:
            return self._error_result(f"Unknown action: {action}")

        try:
            return await handler(context)
        except Exception as e:
            logger.error(f"Email {action} error: {e}")
            return self._error_result(str(e))

    async def _execute_send(self, context: "ExecutionContext") -> ExecutionResult:
        """Send email via SMTP."""
        smtp_server = self.get_parameter("smtp_server", "smtp.gmail.com")
        smtp_port = self.get_parameter("smtp_port", 587)
        use_tls = self.get_parameter("use_tls", True)
        use_ssl = self.get_parameter("use_smtp_ssl", False)
        timeout = self.get_parameter("timeout", 30)
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 2000)

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="SMTP",
            required=False,
        )

        # Get email content
        from_email = self.get_parameter("from_email", username or "")
        to_email = self.get_parameter("to_email", "")
        subject = self.get_parameter("subject", "")
        body = self.get_parameter("body", "")
        cc = self.get_parameter("cc", "")
        bcc = self.get_parameter("bcc", "")
        is_html = self.get_parameter("is_html", False)
        priority = self.get_parameter("priority", "normal")

        # Resolve variables
        if hasattr(context, "resolve_value"):
            smtp_server = context.resolve_value(smtp_server)
            from_email = context.resolve_value(from_email)
            to_email = context.resolve_value(to_email)
            subject = context.resolve_value(subject)
            body = context.resolve_value(body)
            cc = context.resolve_value(cc)
            bcc = context.resolve_value(bcc)

        if not to_email:
            return self._error_result("Recipient email address is required")

        # Get attachments
        attachments = self.get_input_value("attachments") or []
        if isinstance(attachments, str):
            attachments = [p.strip() for p in attachments.split(",") if p.strip()]

        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        # Priority
        if priority == "high":
            msg["X-Priority"] = "1"
            msg["Importance"] = "High"
        elif priority == "low":
            msg["X-Priority"] = "5"
            msg["Importance"] = "Low"

        # Add body
        msg.attach(MIMEText(body, "html" if is_html else "plain"))

        # Add attachments
        for attachment_path in attachments:
            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)

        # Build recipient list
        all_recipients = [addr.strip() for addr in to_email.split(",")]
        if cc:
            all_recipients.extend([addr.strip() for addr in cc.split(",")])
        if bcc:
            all_recipients.extend([addr.strip() for addr in bcc.split(",")])

        logger.info(f"Sending email to {to_email} via {smtp_server}:{smtp_port}")

        def _send_email_sync() -> str:
            """Send email synchronously."""
            server = None
            try:
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout)
                else:
                    server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
                    if use_tls:
                        server.starttls()

                if username and password:
                    server.login(username, password)

                server.sendmail(from_email, all_recipients, msg.as_bytes())
                return msg.get("Message-ID", "")
            finally:
                if server:
                    try:
                        server.quit()
                    except Exception:
                        pass

        return await self._retry_operation(
            _send_email_sync,
            retry_count,
            retry_interval,
            "send email",
            success_handler=lambda message_id: self._send_success(message_id, to_email),
        )

    def _send_success(self, message_id: str, to_email: str) -> ExecutionResult:
        """Handle successful send."""
        self.set_output_value("success", True)
        self.set_output_value("message_id", message_id)
        self.set_output_value("error", "")
        logger.info(f"Email sent successfully to {to_email}")
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {"message_id": message_id},
            "next_nodes": ["exec_out"],
        }

    async def _execute_read(self, context: "ExecutionContext") -> ExecutionResult:
        """Read emails from IMAP."""
        imap_server = self.get_parameter("imap_server", "imap.gmail.com")
        imap_port = self.get_parameter("imap_port", 993)
        use_ssl = self.get_parameter("use_imap_ssl", True)
        folder = self.get_parameter("folder", "INBOX")
        limit = self.get_parameter("limit", 10)
        search_criteria = self.get_parameter("search_criteria", "ALL")
        newest_first = self.get_parameter("newest_first", True)
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 2000)

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="IMAP",
            required=True,
        )

        # Resolve variables
        if hasattr(context, "resolve_value"):
            imap_server = context.resolve_value(imap_server)
            folder = context.resolve_value(folder)
            search_criteria = context.resolve_value(search_criteria)

        if not username or not password:
            return self._error_result("Username and password required")

        logger.info(f"Reading emails from {imap_server}:{imap_port}/{folder}")

        def _read_emails_sync() -> list:
            """Read emails synchronously."""
            mail = None
            try:
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                else:
                    mail = imaplib.IMAP4(imap_server, imap_port)

                mail.login(username, password)
                mail.select(folder)

                status, message_ids = mail.search(None, search_criteria)
                if status != "OK":
                    raise Exception("Failed to search emails")

                id_list = message_ids[0].split()
                id_list = id_list[-limit:] if limit else id_list
                if newest_first:
                    id_list.reverse()

                emails_list = []
                for msg_id in id_list:
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status == "OK":
                        raw_email = msg_data[0][1]
                        msg = email_module.message_from_bytes(raw_email)
                        parsed = parse_email_message(msg)
                        parsed["uid"] = (
                            msg_id.decode()
                            if isinstance(msg_id, bytes)
                            else str(msg_id)
                        )
                        emails_list.append(parsed)

                return emails_list
            finally:
                if mail:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        return await self._retry_operation(
            _read_emails_sync,
            retry_count,
            retry_interval,
            "read emails",
            success_handler=lambda emails: self._read_success(emails, folder),
        )

    def _read_success(self, emails: list, folder: str) -> ExecutionResult:
        """Handle successful read."""
        self.set_output_value("emails", emails)
        self.set_output_value("count", len(emails))
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        logger.info(f"Read {len(emails)} emails from {folder}")
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {"count": len(emails)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_mark(self, context: "ExecutionContext") -> ExecutionResult:
        """Mark email with flag."""
        imap_server = self.get_parameter("imap_server", "imap.gmail.com")
        imap_port = self.get_parameter("imap_port", 993)
        use_ssl = self.get_parameter("use_imap_ssl", True)
        folder = self.get_parameter("folder", "INBOX")
        email_uid = self.get_input_value("email_uid") or ""
        mark_as = self.get_parameter("mark_as", "read")

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="IMAP",
            required=True,
        )

        # Resolve variables
        if hasattr(context, "resolve_value"):
            imap_server = context.resolve_value(imap_server)
            folder = context.resolve_value(folder)
            email_uid = context.resolve_value(email_uid)

        if not email_uid:
            return self._error_result("Email UID is required")

        def _mark_email_sync() -> None:
            """Mark email synchronously."""
            mail = None
            try:
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                else:
                    mail = imaplib.IMAP4(imap_server, imap_port)

                mail.login(username, password)
                mail.select(folder)

                if mark_as == "read":
                    mail.store(email_uid.encode(), "+FLAGS", "\\Seen")
                elif mark_as == "unread":
                    mail.store(email_uid.encode(), "-FLAGS", "\\Seen")
                elif mark_as == "flagged":
                    mail.store(email_uid.encode(), "+FLAGS", "\\Flagged")
                elif mark_as == "unflagged":
                    mail.store(email_uid.encode(), "-FLAGS", "\\Flagged")
            finally:
                if mail:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _mark_email_sync)

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        logger.info(f"Marked email {email_uid} as {mark_as}")
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {"marked_as": mark_as},
            "next_nodes": ["exec_out"],
        }

    async def _execute_delete(self, context: "ExecutionContext") -> ExecutionResult:
        """Delete email from mailbox."""
        imap_server = self.get_parameter("imap_server", "imap.gmail.com")
        imap_port = self.get_parameter("imap_port", 993)
        use_ssl = self.get_parameter("use_imap_ssl", True)
        folder = self.get_parameter("folder", "INBOX")
        email_uid = self.get_input_value("email_uid") or ""
        permanent = self.get_parameter("permanent_delete", False)

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="IMAP",
            required=True,
        )

        # Resolve variables
        if hasattr(context, "resolve_value"):
            imap_server = context.resolve_value(imap_server)
            folder = context.resolve_value(folder)
            email_uid = context.resolve_value(email_uid)

        if not email_uid:
            return self._error_result("Email UID is required")

        def _delete_email_sync() -> None:
            """Delete email synchronously."""
            mail = None
            try:
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                else:
                    mail = imaplib.IMAP4(imap_server, imap_port)

                mail.login(username, password)
                mail.select(folder)

                mail.store(email_uid.encode(), "+FLAGS", "\\Deleted")
                if permanent:
                    mail.expunge()
            finally:
                if mail:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _delete_email_sync)

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        logger.info(f"Deleted email {email_uid}")
        self.status = NodeStatus.SUCCESS
        return {"success": True, "next_nodes": ["exec_out"]}

    async def _execute_move(self, context: "ExecutionContext") -> ExecutionResult:
        """Move email to different folder."""
        imap_server = self.get_parameter("imap_server", "imap.gmail.com")
        imap_port = self.get_parameter("imap_port", 993)
        use_ssl = self.get_parameter("use_imap_ssl", True)
        folder = self.get_parameter("folder", "INBOX")
        email_uid = self.get_input_value("email_uid") or ""
        target_folder = self.get_parameter("target_folder", "")

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="IMAP",
            required=True,
        )

        # Resolve variables
        if hasattr(context, "resolve_value"):
            imap_server = context.resolve_value(imap_server)
            folder = context.resolve_value(folder)
            email_uid = context.resolve_value(email_uid)
            target_folder = context.resolve_value(target_folder)

        if not email_uid or not target_folder:
            return self._error_result("Email UID and target folder are required")

        def _move_email_sync() -> None:
            """Move email synchronously."""
            mail = None
            try:
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                else:
                    mail = imaplib.IMAP4(imap_server, imap_port)

                mail.login(username, password)
                mail.select(folder)

                result = mail.copy(email_uid.encode(), target_folder)
                if result[0] == "OK":
                    mail.store(email_uid.encode(), "+FLAGS", "\\Deleted")
                    mail.expunge()
            finally:
                if mail:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _move_email_sync)

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        logger.info(f"Moved email {email_uid} to {target_folder}")
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {"target_folder": target_folder},
            "next_nodes": ["exec_out"],
        }

    async def _execute_save_attachment(
        self, context: "ExecutionContext"
    ) -> ExecutionResult:
        """Save email attachments to disk."""
        imap_server = self.get_parameter("imap_server", "imap.gmail.com")
        imap_port = self.get_parameter("imap_port", 993)
        use_ssl = self.get_parameter("use_imap_ssl", True)
        folder = self.get_parameter("folder", "INBOX")
        email_uid = self.get_input_value("email_uid") or ""
        save_path = self.get_parameter("save_path", ".")

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="IMAP",
            required=True,
        )

        # Resolve variables
        if hasattr(context, "resolve_value"):
            imap_server = context.resolve_value(imap_server)
            folder = context.resolve_value(folder)
            email_uid = context.resolve_value(email_uid)
            save_path = context.resolve_value(save_path)

        if not email_uid:
            return self._error_result("Email UID is required")

        Path(save_path).mkdir(parents=True, exist_ok=True)

        def _save_attachments_sync() -> list:
            """Save attachments synchronously."""
            mail = None
            try:
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                else:
                    mail = imaplib.IMAP4(imap_server, imap_port)

                mail.login(username, password)
                mail.select(folder)

                status, msg_data = mail.fetch(email_uid.encode(), "(RFC822)")
                if status != "OK":
                    raise Exception("Failed to fetch email")

                raw_email = msg_data[0][1]
                msg = email_module.message_from_bytes(raw_email)

                saved = []
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            filename = decode_header_value(filename)
                            safe_filename = Path(filename).name
                            if not safe_filename:
                                continue
                            filepath = os.path.join(save_path, safe_filename)

                            base, ext = os.path.splitext(filepath)
                            counter = 1
                            while os.path.exists(filepath):
                                filepath = f"{base}_{counter}{ext}"
                                counter += 1

                            payload = part.get_payload(decode=True)
                            if payload:
                                with open(filepath, "wb") as f:
                                    f.write(payload)
                                saved.append(filepath)

                return saved
            finally:
                if mail:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        loop = asyncio.get_running_loop()
        saved_files = await loop.run_in_executor(None, _save_attachments_sync)

        self.set_output_value("saved_files", saved_files)
        self.set_output_value("count", len(saved_files))
        self.set_output_value("success", True)
        self.set_output_value("error", "")

        logger.info(f"Saved {len(saved_files)} attachments to {save_path}")
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {"saved_files": saved_files},
            "next_nodes": ["exec_out"],
        }

    async def _retry_operation(
        self,
        sync_func,
        retry_count: int,
        retry_interval: int,
        operation_name: str,
        success_handler,
    ) -> ExecutionResult:
        """Execute operation with retry logic."""
        loop = asyncio.get_running_loop()
        last_error = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                if attempts > 1:
                    logger.info(
                        f"Retry attempt {attempts - 1}/{retry_count} for {operation_name}"
                    )

                result = await loop.run_in_executor(None, sync_func)
                return success_handler(result)

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    logger.warning(f"{operation_name} failed (attempt {attempts}): {e}")
                    await asyncio.sleep(retry_interval / 1000)
                else:
                    break

        raise last_error

    def _error_result(self, error_msg: str) -> ExecutionResult:
        """Create error result."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("emails", [])
        self.set_output_value("count", 0)
        self.set_output_value("saved_files", [])
        self.status = NodeStatus.ERROR
        return {"success": False, "error": error_msg, "next_nodes": ["exec_error"]}


__all__ = ["EmailSuperNode", "EmailAction"]
