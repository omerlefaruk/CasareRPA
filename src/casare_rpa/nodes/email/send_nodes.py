"""
Email send nodes for CasareRPA.

Provides nodes for sending emails via SMTP with support for
attachments, HTML content, and various delivery options.
"""

import asyncio
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from loguru import logger

from casare_rpa.domain.credentials import (
    CREDENTIAL_NAME_PROP,
    SMTP_PORT_PROP,
    SMTP_SERVER_PROP,
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
from casare_rpa.infrastructure.execution import ExecutionContext

from .email_base import EMAIL_PASSWORD_PROP, EMAIL_USERNAME_PROP


@properties(
    CREDENTIAL_NAME_PROP,
    SMTP_SERVER_PROP,
    SMTP_PORT_PROP,
    EMAIL_USERNAME_PROP,
    EMAIL_PASSWORD_PROP,
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
@node(category="email")
class SendEmailNode(CredentialAwareMixin, BaseNode):
    """
    Send an email via SMTP.

    Supports:
    - Plain text and HTML emails
    - Multiple recipients (To, CC, BCC)
    - File attachments
    - SSL/TLS encryption

    Credential Resolution (in order):
    1. Vault lookup (via credential_name parameter)
    2. Direct parameters (username, password)
    3. Environment variables (SMTP_USERNAME, SMTP_PASSWORD)
    """

    # @category: email
    # @requires: email
    # @ports: smtp_server, smtp_port, username, password, from_email, to_email, subject, body, cc, bcc, attachments -> success, message_id

    def __init__(self, node_id: str, config: Optional[dict] = None, **kwargs) -> None:
        """Initialize SendEmail node."""
        config = config or kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = "Send Email"
        self.node_type = "SendEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("smtp_server", DataType.STRING)
        self.add_input_port("smtp_port", DataType.INTEGER)
        self.add_input_port("username", DataType.STRING)
        self.add_input_port("password", DataType.STRING)
        self.add_input_port("from_email", DataType.STRING)
        self.add_input_port("to_email", DataType.STRING)
        self.add_input_port("subject", DataType.STRING)
        self.add_input_port("body", DataType.STRING)
        self.add_input_port("cc", DataType.STRING)
        self.add_input_port("bcc", DataType.STRING)
        self.add_input_port("attachments", DataType.LIST, required=False)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("message_id", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Send email via SMTP."""
        self.status = NodeStatus.RUNNING

        try:
            # Get connection settings
            smtp_server = self.get_parameter("smtp_server", "smtp.gmail.com")
            smtp_port = self.get_parameter("smtp_port", 587)
            use_tls = self.get_parameter("use_tls", True)
            use_ssl = self.get_parameter("use_ssl", False)
            timeout = self.get_parameter("timeout", 30)

            # Resolve {{variable}} patterns in connection parameters

            # Resolve credentials using CredentialAwareMixin
            username, password = await self.resolve_username_password(
                context,
                credential_name_param="credential_name",
                username_param="username",
                password_param="password",
                env_prefix="SMTP",
                required=False,
            )

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

            # Get attachments from port or config, resolve {{variables}}
            attachments = self.get_input_value("attachments")
            if attachments is None:
                attachments = self.get_parameter("attachments", "")

            # Resolve {{variable}} patterns in attachments
            if isinstance(attachments, str):
                if attachments:
                    attachments = [p.strip() for p in attachments.split(",") if p.strip()]
                else:
                    attachments = []
            elif isinstance(attachments, list):
                attachments = [
                    context.resolve_value(p) if isinstance(p, str) else p for p in attachments
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

            def _send_email_sync() -> str:
                """Send email synchronously - called via run_in_executor."""
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

            loop = asyncio.get_running_loop()

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for send email")

                    message_id = await loop.run_in_executor(None, _send_email_sync)
                    self.set_output_value("success", True)
                    self.set_output_value("message_id", message_id)

                    logger.info(f"Email sent successfully to {to_email} (attempt {attempts})")
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
                    raise
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
