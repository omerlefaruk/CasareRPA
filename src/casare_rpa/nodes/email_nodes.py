"""
Email automation nodes for CasareRPA.

Provides nodes for sending and receiving emails via SMTP and IMAP,
with support for attachments, HTML content, and email management.
"""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Any, Optional, Dict, List
from pathlib import Path
from datetime import datetime
import os
import re

from loguru import logger

from ..core.base_node import BaseNode
from ..core.execution_context import ExecutionContext
from ..core.types import PortType, DataType, NodeStatus, ExecutionResult


def _decode_header_value(value: str) -> str:
    """Decode email header value."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or 'utf-8', errors='replace'))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode('utf-8', errors='replace'))
        else:
            result.append(part)
    return ''.join(result)


def _parse_email_message(msg: email.message.Message) -> Dict[str, Any]:
    """Parse an email message into a dictionary."""
    # Get basic headers
    subject = _decode_header_value(msg.get('Subject', ''))
    from_addr = _decode_header_value(msg.get('From', ''))
    to_addr = _decode_header_value(msg.get('To', ''))
    cc_addr = _decode_header_value(msg.get('Cc', ''))
    date_str = msg.get('Date', '')
    message_id = msg.get('Message-ID', '')

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
            content_disposition = str(part.get('Content-Disposition', ''))

            if 'attachment' in content_disposition:
                # Attachment
                filename = part.get_filename()
                if filename:
                    filename = _decode_header_value(filename)
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "size": len(part.get_payload(decode=True) or b''),
                    })
            elif content_type == 'text/plain':
                try:
                    body_text = part.get_payload(decode=True).decode('utf-8', errors='replace')
                except (AttributeError, UnicodeDecodeError):
                    body_text = str(part.get_payload())
            elif content_type == 'text/html':
                try:
                    body_html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                except (AttributeError, UnicodeDecodeError):
                    body_html = str(part.get_payload())
    else:
        # Not multipart
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode('utf-8', errors='replace')
                if content_type == 'text/html':
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


class SendEmailNode(BaseNode):
    """
    Send an email via SMTP.

    Supports:
    - Plain text and HTML emails
    - Multiple recipients (To, CC, BCC)
    - File attachments
    - SSL/TLS encryption
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize SendEmail node."""
        super().__init__(node_id, config)
        self.name = "Send Email"
        self.node_type = "SendEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
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
        self.add_input_port("attachments", PortType.INPUT, DataType.LIST)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message_id", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Send email via SMTP."""
        self.status = NodeStatus.RUNNING

        try:
            # Get connection settings
            smtp_server = self.get_input_value("smtp_server") or self.config.get("smtp_server", "smtp.gmail.com")
            smtp_port = self.get_input_value("smtp_port") or self.config.get("smtp_port", 587)
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            use_tls = self.config.get("use_tls", True)
            use_ssl = self.config.get("use_ssl", False)

            # Get email content
            from_email = self.get_input_value("from_email") or self.config.get("from_email", username)
            to_email = self.get_input_value("to_email") or self.config.get("to_email", "")
            subject = self.get_input_value("subject") or self.config.get("subject", "")
            body = self.get_input_value("body") or self.config.get("body", "")
            cc = self.get_input_value("cc") or self.config.get("cc", "")
            bcc = self.get_input_value("bcc") or self.config.get("bcc", "")
            attachments = self.get_input_value("attachments") or []
            is_html = self.config.get("is_html", False)

            if not to_email:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No recipient email address provided",
                    "next_nodes": []
                }

            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc

            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            for attachment_path in attachments:
                if attachment_path and os.path.exists(attachment_path):
                    filename = os.path.basename(attachment_path)
                    with open(attachment_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)

            # Build recipient list
            all_recipients = [addr.strip() for addr in to_email.split(',')]
            if cc:
                all_recipients.extend([addr.strip() for addr in cc.split(',')])
            if bcc:
                all_recipients.extend([addr.strip() for addr in bcc.split(',')])

            # Send email
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()

            if username and password:
                server.login(username, password)

            server.sendmail(from_email, all_recipients, msg.as_string())
            server.quit()

            message_id = msg.get('Message-ID', '')
            self.set_output_value("success", True)
            self.set_output_value("message_id", message_id)

            logger.info(f"Email sent successfully to {to_email}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"message_id": message_id, "recipients": len(all_recipients)},
                "next_nodes": ["exec_out"]
            }

        except smtplib.SMTPAuthenticationError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"SMTP authentication failed: {e}")
            return {
                "success": False,
                "error": f"Authentication failed: {e}",
                "next_nodes": []
            }
        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class ReadEmailsNode(BaseNode):
    """
    Read emails from an IMAP server.

    Supports:
    - Folder selection
    - Unread/All filter
    - Limit number of emails
    - Search criteria
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize ReadEmails node."""
        super().__init__(node_id, config)
        self.name = "Read Emails"
        self.node_type = "ReadEmailsNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("imap_port", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("limit", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("search_criteria", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("emails", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Read emails from IMAP server."""
        self.status = NodeStatus.RUNNING

        try:
            # Get connection settings
            imap_server = self.get_input_value("imap_server") or self.config.get("imap_server", "imap.gmail.com")
            imap_port = self.get_input_value("imap_port") or self.config.get("imap_port", 993)
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            folder = self.get_input_value("folder") or self.config.get("folder", "INBOX")
            limit = self.get_input_value("limit") or self.config.get("limit", 10)
            search_criteria = self.get_input_value("search_criteria") or self.config.get("search_criteria", "ALL")
            use_ssl = self.config.get("use_ssl", True)

            if not username or not password:
                self.set_output_value("emails", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Username and password required",
                    "next_nodes": []
                }

            # Connect to IMAP server
            if use_ssl:
                mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            else:
                mail = imaplib.IMAP4(imap_server, imap_port)

            mail.login(username, password)
            mail.select(folder)

            # Search for emails
            status, message_ids = mail.search(None, search_criteria)
            if status != 'OK':
                mail.logout()
                self.set_output_value("emails", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Failed to search emails",
                    "next_nodes": []
                }

            # Get message IDs (most recent first)
            id_list = message_ids[0].split()
            id_list = id_list[-limit:] if limit else id_list
            id_list.reverse()  # Most recent first

            emails = []
            for msg_id in id_list:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                if status == 'OK':
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    parsed = _parse_email_message(msg)
                    parsed['uid'] = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
                    emails.append(parsed)

            mail.logout()

            self.set_output_value("emails", emails)
            self.set_output_value("count", len(emails))

            logger.info(f"Read {len(emails)} emails from {folder}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"count": len(emails)},
                "next_nodes": ["exec_out"]
            }

        except imaplib.IMAP4.error as e:
            self.set_output_value("emails", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"IMAP error: {e}")
            return {
                "success": False,
                "error": f"IMAP error: {e}",
                "next_nodes": []
            }
        except Exception as e:
            self.set_output_value("emails", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to read emails: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("email", PortType.INPUT, DataType.DICT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
                    "next_nodes": []
                }

            # Extract fields
            self.set_output_value("subject", email_data.get("subject", ""))
            self.set_output_value("from", email_data.get("from", ""))
            self.set_output_value("to", email_data.get("to", ""))
            self.set_output_value("date", email_data.get("date", ""))
            self.set_output_value("body_text", email_data.get("body_text", ""))
            self.set_output_value("body_html", email_data.get("body_html", ""))
            self.set_output_value("attachments", email_data.get("attachments", []))

            logger.debug(f"Extracted email content: {email_data.get('subject', 'No subject')}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to extract email content: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("save_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("saved_files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Save email attachments."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_input_value("imap_server") or self.config.get("imap_server", "imap.gmail.com")
            imap_port = self.config.get("imap_port", 993)
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            email_uid = self.get_input_value("email_uid") or ""
            save_path = self.get_input_value("save_path") or self.config.get("save_path", ".")
            folder = self.get_input_value("folder") or self.config.get("folder", "INBOX")

            if not email_uid:
                self.set_output_value("saved_files", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": []
                }

            # Ensure save path exists
            Path(save_path).mkdir(parents=True, exist_ok=True)

            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
            mail.select(folder)

            # Fetch the email
            status, msg_data = mail.fetch(email_uid.encode(), '(RFC822)')
            if status != 'OK':
                mail.logout()
                self.set_output_value("saved_files", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Failed to fetch email",
                    "next_nodes": []
                }

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            saved_files = []
            for part in msg.walk():
                content_disposition = str(part.get('Content-Disposition', ''))
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = _decode_header_value(filename)
                        filepath = os.path.join(save_path, filename)

                        # Avoid overwriting
                        base, ext = os.path.splitext(filepath)
                        counter = 1
                        while os.path.exists(filepath):
                            filepath = f"{base}_{counter}{ext}"
                            counter += 1

                        payload = part.get_payload(decode=True)
                        if payload:
                            with open(filepath, 'wb') as f:
                                f.write(payload)
                            saved_files.append(filepath)

            mail.logout()

            self.set_output_value("saved_files", saved_files)
            self.set_output_value("count", len(saved_files))

            logger.info(f"Saved {len(saved_files)} attachments to {save_path}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"saved_files": saved_files},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("saved_files", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to save attachments: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("emails", PortType.INPUT, DataType.LIST)
        self.add_input_port("subject_contains", PortType.INPUT, DataType.STRING)
        self.add_input_port("from_contains", PortType.INPUT, DataType.STRING)
        self.add_input_port("has_attachments", PortType.INPUT, DataType.BOOLEAN)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("filtered", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to filter emails: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("mark_as", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Mark email with specified flag."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_input_value("imap_server") or self.config.get("imap_server", "imap.gmail.com")
            imap_port = self.config.get("imap_port", 993)
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            email_uid = self.get_input_value("email_uid") or ""
            folder = self.get_input_value("folder") or self.config.get("folder", "INBOX")
            mark_as = self.get_input_value("mark_as") or self.config.get("mark_as", "read")

            if not email_uid:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": []
                }

            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
            mail.select(folder)

            # Apply flag based on mark_as
            if mark_as == "read":
                mail.store(email_uid.encode(), '+FLAGS', '\\Seen')
            elif mark_as == "unread":
                mail.store(email_uid.encode(), '-FLAGS', '\\Seen')
            elif mark_as == "flagged":
                mail.store(email_uid.encode(), '+FLAGS', '\\Flagged')
            elif mark_as == "unflagged":
                mail.store(email_uid.encode(), '-FLAGS', '\\Flagged')

            mail.logout()

            self.set_output_value("success", True)
            logger.info(f"Marked email {email_uid} as {mark_as}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"marked_as": mark_as},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to mark email: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Delete email from mailbox."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_input_value("imap_server") or self.config.get("imap_server", "imap.gmail.com")
            imap_port = self.config.get("imap_port", 993)
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            email_uid = self.get_input_value("email_uid") or ""
            folder = self.get_input_value("folder") or self.config.get("folder", "INBOX")
            permanent = self.config.get("permanent", False)

            if not email_uid:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": []
                }

            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
            mail.select(folder)

            # Mark as deleted
            mail.store(email_uid.encode(), '+FLAGS', '\\Deleted')

            if permanent:
                mail.expunge()

            mail.logout()

            self.set_output_value("success", True)
            logger.info(f"Deleted email {email_uid}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to delete email: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("source_folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("target_folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Move email to different folder."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_input_value("imap_server") or self.config.get("imap_server", "imap.gmail.com")
            imap_port = self.config.get("imap_port", 993)
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            email_uid = self.get_input_value("email_uid") or ""
            source_folder = self.get_input_value("source_folder") or self.config.get("source_folder", "INBOX")
            target_folder = self.get_input_value("target_folder") or self.config.get("target_folder", "")

            if not email_uid or not target_folder:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Email UID and target folder required",
                    "next_nodes": []
                }

            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
            mail.select(source_folder)

            # Copy to target folder
            result = mail.copy(email_uid.encode(), target_folder)
            if result[0] == 'OK':
                # Mark original as deleted
                mail.store(email_uid.encode(), '+FLAGS', '\\Deleted')
                mail.expunge()

            mail.logout()

            self.set_output_value("success", True)
            logger.info(f"Moved email {email_uid} to {target_folder}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"target_folder": target_folder},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to move email: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
