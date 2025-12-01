"""
Email automation nodes for CasareRPA.

Provides nodes for sending and receiving emails via SMTP and IMAP,
with support for attachments, HTML content, and email management.
"""

import asyncio
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Any, Optional, Dict
from pathlib import Path
import os

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    PortType,
    DataType,
    NodeStatus,
    ExecutionResult,
)
from casare_rpa.nodes.utils.type_converters import safe_int


def _decode_header_value(value: str) -> str:
    """Decode email header value."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _parse_email_message(msg: email.message.Message) -> Dict[str, Any]:
    """Parse an email message into a dictionary."""
    # Get basic headers
    subject = _decode_header_value(msg.get("Subject", ""))
    from_addr = _decode_header_value(msg.get("From", ""))
    to_addr = _decode_header_value(msg.get("To", ""))
    cc_addr = _decode_header_value(msg.get("Cc", ""))
    date_str = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    # Parse date
    date = None
    if date_str:
        try:
            date = parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            pass

    # Get body
    body_text = ""
    body_html = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition:
                # Attachment
                filename = part.get_filename()
                if filename:
                    filename = _decode_header_value(filename)
                    attachments.append(
                        {
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(part.get_payload(decode=True) or b""),
                        }
                    )
            elif content_type == "text/plain":
                try:
                    body_text = part.get_payload(decode=True).decode(
                        "utf-8", errors="replace"
                    )
                except (AttributeError, UnicodeDecodeError):
                    body_text = str(part.get_payload())
            elif content_type == "text/html":
                try:
                    body_html = part.get_payload(decode=True).decode(
                        "utf-8", errors="replace"
                    )
                except (AttributeError, UnicodeDecodeError):
                    body_html = str(part.get_payload())
    else:
        # Not multipart
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode("utf-8", errors="replace")
                if content_type == "text/html":
                    body_html = text
                else:
                    body_text = text
        except (AttributeError, UnicodeDecodeError):
            body_text = str(msg.get_payload())

    return {
        "message_id": message_id,
        "subject": subject,
        "from": from_addr,
        "to": to_addr,
        "cc": cc_addr,
        "date": date.isoformat() if date else "",
        "date_obj": date,
        "body_text": body_text,
        "body_html": body_html,
        "attachments": attachments,
        "has_attachments": len(attachments) > 0,
    }


@executable_node
@node_schema(
    PropertyDef(
        "smtp_server",
        PropertyType.STRING,
        default="smtp.gmail.com",
        label="SMTP Server",
        tooltip="SMTP server hostname",
    ),
    PropertyDef(
        "smtp_port",
        PropertyType.INTEGER,
        default=587,
        label="SMTP Port",
        tooltip="SMTP server port (587 for TLS, 465 for SSL)",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "from_email",
        PropertyType.STRING,
        default="",
        label="From Email",
        tooltip="Sender email address",
    ),
    PropertyDef(
        "to_email",
        PropertyType.STRING,
        default="",
        label="To Email",
        tooltip="Recipient email address(es), comma-separated",
    ),
    PropertyDef(
        "subject",
        PropertyType.STRING,
        default="",
        label="Subject",
        tooltip="Email subject line",
    ),
    PropertyDef(
        "body",
        PropertyType.STRING,
        default="",
        label="Body",
        tooltip="Email message body",
    ),
    PropertyDef(
        "cc",
        PropertyType.STRING,
        default="",
        label="CC",
        tooltip="CC recipients, comma-separated",
    ),
    PropertyDef(
        "bcc",
        PropertyType.STRING,
        default="",
        label="BCC",
        tooltip="BCC recipients, comma-separated",
    ),
    PropertyDef(
        "use_tls",
        PropertyType.BOOLEAN,
        default=True,
        label="Use TLS",
        tooltip="Use TLS encryption",
    ),
    PropertyDef(
        "use_ssl",
        PropertyType.BOOLEAN,
        default=False,
        label="Use SSL",
        tooltip="Use SSL encryption",
    ),
    PropertyDef(
        "is_html",
        PropertyType.BOOLEAN,
        default=False,
        label="HTML Body",
        tooltip="Body contains HTML content",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        label="Timeout (seconds)",
        tooltip="SMTP connection timeout",
    ),
    PropertyDef(
        "reply_to",
        PropertyType.STRING,
        default="",
        label="Reply-To",
        tooltip="Reply-To email address",
    ),
    PropertyDef(
        "priority",
        PropertyType.CHOICE,
        default="normal",
        choices=["high", "normal", "low"],
        label="Priority",
        tooltip="Email priority level",
    ),
    PropertyDef(
        "read_receipt",
        PropertyType.BOOLEAN,
        default=False,
        label="Request Read Receipt",
        tooltip="Request read receipt notification",
    ),
    PropertyDef(
        "sender_name",
        PropertyType.STRING,
        default="",
        label="Sender Name",
        tooltip="Display name for sender",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=2000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts in milliseconds",
    ),
)
@executable_node
class SendEmailNode(BaseNode):
    """
    Send an email via SMTP.

    Supports:
    - Plain text and HTML emails
    - Multiple recipients (To, CC, BCC)
    - File attachments
    - SSL/TLS encryption
    """

    def __init__(self, node_id: str, config: Optional[dict] = None, **kwargs) -> None:
        """Initialize SendEmail node."""
        config = config or kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = "Send Email"
        self.node_type = "SendEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("smtp_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("smtp_port", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("from_email", PortType.INPUT, DataType.STRING)
        self.add_input_port("to_email", PortType.INPUT, DataType.STRING)
        self.add_input_port("subject", PortType.INPUT, DataType.STRING)
        self.add_input_port("body", PortType.INPUT, DataType.STRING)
        self.add_input_port("cc", PortType.INPUT, DataType.STRING)
        self.add_input_port("bcc", PortType.INPUT, DataType.STRING)
        self.add_input_port(
            "attachments", PortType.INPUT, DataType.LIST, required=False
        )
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Send email via SMTP."""
        self.status = NodeStatus.RUNNING

        try:
            # Get connection settings
            smtp_server = self.get_parameter("smtp_server", "smtp.gmail.com")
            smtp_port = self.get_parameter("smtp_port", 587)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            use_tls = self.get_parameter("use_tls", True)
            use_ssl = self.get_parameter("use_ssl", False)
            timeout = self.get_parameter("timeout", 30)

            # Resolve {{variable}} patterns in connection parameters
            smtp_server = context.resolve_value(smtp_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)

            # Get retry options
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 2000)

            # Get email content
            from_email = self.get_parameter("from_email", username)
            to_email = self.get_parameter("to_email", "")
            subject = self.get_parameter("subject", "")
            body = self.get_parameter("body", "")
            cc = self.get_parameter("cc", "")
            bcc = self.get_parameter("bcc", "")

            # Resolve {{variable}} patterns in email content
            from_email = context.resolve_value(from_email)
            to_email = context.resolve_value(to_email)
            subject = context.resolve_value(subject)
            body = context.resolve_value(body)
            cc = context.resolve_value(cc)
            bcc = context.resolve_value(bcc)
            # Get attachments from port or config, resolve {{variables}}
            attachments = self.get_input_value("attachments")
            if attachments is None:
                attachments = self.get_parameter("attachments", "")
            # Resolve {{variable}} patterns in attachments
            if isinstance(attachments, str):
                attachments = context.resolve_value(attachments)
                # Handle comma-separated paths or single path
                if attachments:
                    attachments = [
                        p.strip() for p in attachments.split(",") if p.strip()
                    ]
                else:
                    attachments = []
            elif isinstance(attachments, list):
                # Resolve each item in case of {{variables}}
                attachments = [
                    context.resolve_value(p) if isinstance(p, str) else p
                    for p in attachments
                ]
            is_html = self.get_parameter("is_html", False)

            # Advanced options
            reply_to = self.get_parameter("reply_to", "")
            priority = self.get_parameter("priority", "normal")
            read_receipt = self.get_parameter("read_receipt", False)
            sender_name = self.get_parameter("sender_name", "")

            if not to_email:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No recipient email address provided",
                    "next_nodes": [],
                }

            # Create message
            msg = MIMEMultipart()

            # Set From with optional sender name
            if sender_name:
                msg["From"] = f"{sender_name} <{from_email}>"
            else:
                msg["From"] = from_email

            msg["To"] = to_email
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = cc
            if bcc:
                msg["Bcc"] = bcc

            # Reply-To header
            if reply_to:
                msg["Reply-To"] = reply_to

            # Priority header
            if priority == "high":
                msg["X-Priority"] = "1"
                msg["Importance"] = "High"
            elif priority == "low":
                msg["X-Priority"] = "5"
                msg["Importance"] = "Low"

            # Read receipt request
            if read_receipt and from_email:
                msg["Disposition-Notification-To"] = from_email

            # Add body
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

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

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            # Helper function to send email synchronously (runs in thread pool)
            def _send_email_sync() -> str:
                """Send email synchronously - called via run_in_executor."""
                server = None
                try:
                    if use_ssl:
                        server = smtplib.SMTP_SSL(
                            smtp_server, smtp_port, timeout=timeout
                        )
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

            loop = asyncio.get_running_loop()

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for send email"
                        )

                    # Run blocking SMTP operations in thread pool to avoid freezing UI
                    message_id = await loop.run_in_executor(None, _send_email_sync)
                    self.set_output_value("success", True)
                    self.set_output_value("message_id", message_id)

                    logger.info(
                        f"Email sent successfully to {to_email} (attempt {attempts})"
                    )
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {
                            "message_id": message_id,
                            "recipients": len(all_recipients),
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
                    }

                except smtplib.SMTPAuthenticationError:
                    raise  # Don't retry auth errors
                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Send email failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except smtplib.SMTPAuthenticationError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"SMTP authentication failed: {e}")
            return {
                "success": False,
                "error": f"Authentication failed: {e}",
                "next_nodes": [],
            }
        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to send email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port (usually 993 for SSL)",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder to read from",
    ),
    PropertyDef(
        "limit",
        PropertyType.INTEGER,
        default=10,
        min_value=0,
        label="Limit",
        tooltip="Maximum number of emails to retrieve",
    ),
    PropertyDef(
        "search_criteria",
        PropertyType.STRING,
        default="ALL",
        label="Search Criteria",
        tooltip="IMAP search criteria (e.g., ALL, UNSEEN, FROM 'sender@example.com')",
    ),
    PropertyDef(
        "use_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Use SSL",
        tooltip="Use SSL encryption",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        label="Timeout (seconds)",
        tooltip="IMAP connection timeout",
    ),
    PropertyDef(
        "mark_as_read",
        PropertyType.BOOLEAN,
        default=False,
        label="Mark as Read",
        tooltip="Mark emails as read after fetching",
    ),
    PropertyDef(
        "include_body",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Body",
        tooltip="Include email body content",
    ),
    PropertyDef(
        "newest_first",
        PropertyType.BOOLEAN,
        default=True,
        label="Newest First",
        tooltip="Return newest emails first",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=2000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts in milliseconds",
    ),
)
@executable_node
class ReadEmailsNode(BaseNode):
    """
    Read emails from an IMAP server.

    Supports:
    - Folder selection
    - Unread/All filter
    - Limit number of emails
    - Search criteria
    """

    def __init__(self, node_id: str, config: Optional[dict] = None, **kwargs) -> None:
        """Initialize ReadEmails node."""
        config = config or kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = "Read Emails"
        self.node_type = "ReadEmailsNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("imap_port", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("limit", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("search_criteria", PortType.INPUT, DataType.STRING)
        self.add_output_port("emails", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Read emails from IMAP server."""
        self.status = NodeStatus.RUNNING

        try:
            # Get connection settings
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            folder = self.get_parameter("folder", "INBOX")
            limit = self.get_parameter("limit", 10)
            search_criteria = self.get_parameter("search_criteria", "ALL")
            use_ssl = self.get_parameter("use_ssl", True)

            # Resolve {{variable}} patterns in connection parameters
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            folder = context.resolve_value(folder)
            search_criteria = context.resolve_value(search_criteria)

            # Get retry options
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 2000)

            if not username or not password:
                self.set_output_value("emails", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Username and password required",
                    "next_nodes": [],
                }

            logger.info(f"Reading emails from {imap_server}:{imap_port}/{folder}")

            # Helper function to read emails synchronously (runs in thread pool)
            def _read_emails_sync() -> list:
                """Read emails synchronously - called via run_in_executor."""
                mail = None
                try:
                    if use_ssl:
                        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    else:
                        mail = imaplib.IMAP4(imap_server, imap_port)

                    mail.login(username, password)
                    mail.select(folder)

                    # Search for emails
                    status, message_ids = mail.search(None, search_criteria)
                    if status != "OK":
                        raise Exception("Failed to search emails")

                    # Get message IDs (most recent first)
                    id_list = message_ids[0].split()
                    id_list = id_list[-limit:] if limit else id_list
                    id_list.reverse()  # Most recent first

                    emails_list = []
                    for msg_id in id_list:
                        status, msg_data = mail.fetch(msg_id, "(RFC822)")
                        if status == "OK":
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            parsed = _parse_email_message(msg)
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

            loop = asyncio.get_running_loop()
            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for read emails"
                        )

                    # Run blocking IMAP operations in thread pool to avoid freezing UI
                    emails = await loop.run_in_executor(None, _read_emails_sync)

                    self.set_output_value("emails", emails)
                    self.set_output_value("count", len(emails))

                    logger.info(
                        f"Read {len(emails)} emails from {folder} (attempt {attempts})"
                    )
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"count": len(emails), "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except imaplib.IMAP4.error as e:
                    if "authentication" in str(e).lower():
                        raise  # Don't retry auth errors
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Read emails failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break
                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Read emails failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except imaplib.IMAP4.error as e:
            self.set_output_value("emails", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"IMAP error: {e}")
            return {"success": False, "error": f"IMAP error: {e}", "next_nodes": []}
        except Exception as e:
            self.set_output_value("emails", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to read emails: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class GetEmailContentNode(BaseNode):
    """
    Extract content from an email object.

    Parses email data and extracts subject, body, sender, etc.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize GetEmailContent node."""
        super().__init__(node_id, config)
        self.name = "Get Email Content"
        self.node_type = "GetEmailContentNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("email", PortType.INPUT, DataType.DICT)
        self.add_output_port("subject", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("from", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("to", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("date", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("body_text", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("body_html", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("attachments", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Extract email content."""
        self.status = NodeStatus.RUNNING

        try:
            email_data = self.get_input_value("email")

            if not email_data or not isinstance(email_data, dict):
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email data provided",
                }

            # Extract fields
            self.set_output_value("subject", email_data.get("subject", ""))
            self.set_output_value("from", email_data.get("from", ""))
            self.set_output_value("to", email_data.get("to", ""))
            self.set_output_value("date", email_data.get("date", ""))
            self.set_output_value("body_text", email_data.get("body_text", ""))
            self.set_output_value("body_html", email_data.get("body_html", ""))
            self.set_output_value("attachments", email_data.get("attachments", []))

            logger.debug(
                f"Extracted email content: {email_data.get('subject', 'No subject')}"
            )
            self.status = NodeStatus.SUCCESS
            return {"success": True}

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to extract email content: {e}")
            return {"success": False, "error": str(e)}


@executable_node
@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
    ),
    PropertyDef(
        "save_path",
        PropertyType.STRING,
        default=".",
        label="Save Path",
        tooltip="Directory path to save attachments",
    ),
)
@executable_node
class SaveAttachmentNode(BaseNode):
    """
    Save email attachments to disk.

    Downloads and saves attachments from an email.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize SaveAttachment node."""
        super().__init__(node_id, config)
        self.name = "Save Attachment"
        self.node_type = "SaveAttachmentNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("save_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("saved_files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Save email attachments."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            save_path = self.get_parameter("save_path", ".")
            folder = self.get_parameter("folder", "INBOX")

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            save_path = context.resolve_value(save_path)
            folder = context.resolve_value(folder)

            if not email_uid:
                self.set_output_value("saved_files", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": [],
                }

            # Ensure save path exists
            Path(save_path).mkdir(parents=True, exist_ok=True)

            # Helper function to save attachments synchronously (runs in thread pool)
            def _save_attachments_sync() -> list:
                """Save attachments synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(folder)

                    # Fetch the email
                    status, msg_data = mail.fetch(email_uid.encode(), "(RFC822)")
                    if status != "OK":
                        raise Exception("Failed to fetch email")

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    saved = []
                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition", ""))
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                filename = _decode_header_value(filename)
                                # SECURITY: Sanitize filename to prevent path traversal attacks
                                # Path(filename).name strips any directory components like ../../../
                                safe_filename = Path(filename).name
                                if not safe_filename:
                                    logger.warning(
                                        f"Skipping attachment with invalid filename: {filename}"
                                    )
                                    continue
                                filepath = os.path.join(save_path, safe_filename)

                                # Avoid overwriting
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

            # Run blocking IMAP operations in thread pool to avoid freezing UI
            loop = asyncio.get_running_loop()
            saved_files = await loop.run_in_executor(None, _save_attachments_sync)

            self.set_output_value("saved_files", saved_files)
            self.set_output_value("count", len(saved_files))

            logger.info(f"Saved {len(saved_files)} attachments to {save_path}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"saved_files": saved_files},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("saved_files", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to save attachments: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class FilterEmailsNode(BaseNode):
    """
    Filter a list of emails based on criteria.

    Supports filtering by subject, sender, date range, etc.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize FilterEmails node."""
        super().__init__(node_id, config)
        self.name = "Filter Emails"
        self.node_type = "FilterEmailsNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("emails", PortType.INPUT, DataType.LIST)
        self.add_input_port("subject_contains", PortType.INPUT, DataType.STRING)
        self.add_input_port("from_contains", PortType.INPUT, DataType.STRING)
        self.add_input_port("has_attachments", PortType.INPUT, DataType.BOOLEAN)
        self.add_output_port("filtered", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Filter emails based on criteria."""
        self.status = NodeStatus.RUNNING

        try:
            emails = self.get_input_value("emails") or []
            subject_contains = self.get_input_value("subject_contains") or ""
            from_contains = self.get_input_value("from_contains") or ""
            has_attachments = self.get_input_value("has_attachments")

            # Resolve {{variable}} patterns
            subject_contains = context.resolve_value(subject_contains)
            from_contains = context.resolve_value(from_contains)

            filtered = []
            for email_data in emails:
                if not isinstance(email_data, dict):
                    continue

                # Check subject filter
                if subject_contains:
                    subject = email_data.get("subject", "").lower()
                    if subject_contains.lower() not in subject:
                        continue

                # Check from filter
                if from_contains:
                    from_addr = email_data.get("from", "").lower()
                    if from_contains.lower() not in from_addr:
                        continue

                # Check attachments filter
                if has_attachments is not None:
                    email_has_attach = email_data.get("has_attachments", False)
                    if has_attachments and not email_has_attach:
                        continue
                    if not has_attachments and email_has_attach:
                        continue

                filtered.append(email_data)

            self.set_output_value("filtered", filtered)
            self.set_output_value("count", len(filtered))

            logger.info(f"Filtered {len(emails)} emails to {len(filtered)}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"count": len(filtered)},
            }

        except Exception as e:
            self.set_output_value("filtered", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to filter emails: {e}")
            return {"success": False, "error": str(e)}


@executable_node
@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
    ),
    PropertyDef(
        "mark_as",
        PropertyType.CHOICE,
        default="read",
        choices=["read", "unread", "flagged", "unflagged"],
        label="Mark As",
        tooltip="Flag to set on the email",
    ),
)
@executable_node
class MarkEmailNode(BaseNode):
    """
    Mark an email as read, unread, or flagged.

    Updates email flags on the IMAP server.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize MarkEmail node."""
        super().__init__(node_id, config)
        self.name = "Mark Email"
        self.node_type = "MarkEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("mark_as", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Mark email with specified flag."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            folder = self.get_parameter("folder", "INBOX")
            mark_as = self.get_parameter("mark_as", "read")

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            folder = context.resolve_value(folder)
            mark_as = context.resolve_value(mark_as)

            if not email_uid:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": [],
                }

            # Helper function to mark email synchronously (runs in thread pool)
            def _mark_email_sync() -> None:
                """Mark email synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(folder)

                    # Apply flag based on mark_as
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

            # Run blocking IMAP operations in thread pool to avoid freezing UI
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _mark_email_sync)

            self.set_output_value("success", True)
            logger.info(f"Marked email {email_uid} as {mark_as}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"marked_as": mark_as},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to mark email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
    ),
    PropertyDef(
        "permanent",
        PropertyType.BOOLEAN,
        default=False,
        label="Permanent Delete",
        tooltip="Permanently delete (expunge) instead of just marking deleted",
    ),
)
@executable_node
class DeleteEmailNode(BaseNode):
    """
    Delete an email from the mailbox.

    Moves email to trash or permanently deletes it.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize DeleteEmail node."""
        super().__init__(node_id, config)
        self.name = "Delete Email"
        self.node_type = "DeleteEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Delete email from mailbox."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            folder = self.get_parameter("folder", "INBOX")
            permanent = self.get_parameter("permanent", False)

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            folder = context.resolve_value(folder)

            if not email_uid:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": [],
                }

            # Helper function to delete email synchronously (runs in thread pool)
            def _delete_email_sync() -> None:
                """Delete email synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(folder)

                    # Mark as deleted
                    mail.store(email_uid.encode(), "+FLAGS", "\\Deleted")

                    if permanent:
                        mail.expunge()
                finally:
                    if mail:
                        try:
                            mail.logout()
                        except Exception:
                            pass

            # Run blocking IMAP operations in thread pool to avoid freezing UI
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _delete_email_sync)

            self.set_output_value("success", True)
            logger.info(f"Deleted email {email_uid}")
            self.status = NodeStatus.SUCCESS
            return {"success": True, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to delete email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "source_folder",
        PropertyType.STRING,
        default="INBOX",
        label="Source Folder",
        tooltip="Source mailbox folder",
    ),
    PropertyDef(
        "target_folder",
        PropertyType.STRING,
        default="",
        label="Target Folder",
        tooltip="Target mailbox folder",
    ),
)
@executable_node
class MoveEmailNode(BaseNode):
    """
    Move an email to a different folder.

    Copies email to target folder and marks original as deleted.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize MoveEmail node."""
        super().__init__(node_id, config)
        self.name = "Move Email"
        self.node_type = "MoveEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("source_folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("target_folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Move email to different folder."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            source_folder = self.get_parameter("source_folder", "INBOX")
            target_folder = self.get_parameter("target_folder", "")

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            source_folder = context.resolve_value(source_folder)
            target_folder = context.resolve_value(target_folder)

            if not email_uid or not target_folder:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Email UID and target folder required",
                    "next_nodes": [],
                }

            # Helper function to move email synchronously (runs in thread pool)
            def _move_email_sync() -> None:
                """Move email synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(source_folder)

                    # Copy to target folder
                    result = mail.copy(email_uid.encode(), target_folder)
                    if result[0] == "OK":
                        # Mark original as deleted
                        mail.store(email_uid.encode(), "+FLAGS", "\\Deleted")
                        mail.expunge()
                finally:
                    if mail:
                        try:
                            mail.logout()
                        except Exception:
                            pass

            # Run blocking IMAP operations in thread pool to avoid freezing UI
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _move_email_sync)

            self.set_output_value("success", True)
            logger.info(f"Moved email {email_uid} to {target_folder}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"target_folder": target_folder},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to move email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
