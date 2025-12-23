"""
Email receive/read nodes for CasareRPA.

Provides nodes for reading, retrieving, and filtering emails via IMAP.
"""

import asyncio
import email as email_module
import imaplib

from loguru import logger

from casare_rpa.domain.credentials import (
    CREDENTIAL_NAME_PROP,
    IMAP_PORT_PROP,
    IMAP_SERVER_PROP,
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

from .email_base import EMAIL_PASSWORD_PROP, EMAIL_USERNAME_PROP, parse_email_message


@properties(
    CREDENTIAL_NAME_PROP,
    IMAP_SERVER_PROP,
    IMAP_PORT_PROP,
    EMAIL_USERNAME_PROP,
    EMAIL_PASSWORD_PROP,
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
@node(category="email")
class ReadEmailsNode(CredentialAwareMixin, BaseNode):
    """
    Read emails from an IMAP server.

    Supports:
    - Folder selection
    - Unread/All filter
    - Limit number of emails
    - Search criteria

    Credential Resolution (in order):
    1. Vault lookup (via credential_name parameter)
    2. Direct parameters (username, password)
    3. Environment variables (IMAP_USERNAME, IMAP_PASSWORD)
    """

    # @category: email
    # @requires: email
    # @ports: imap_server, imap_port, username, password, folder, limit, search_criteria -> emails, count

    def __init__(self, node_id: str, config: dict | None = None, **kwargs) -> None:
        """Initialize ReadEmails node."""
        config = config or kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = "Read Emails"
        self.node_type = "ReadEmailsNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", DataType.STRING)
        self.add_input_port("imap_port", DataType.INTEGER)
        self.add_input_port("username", DataType.STRING)
        self.add_input_port("password", DataType.STRING)
        self.add_input_port("folder", DataType.STRING)
        self.add_input_port("limit", DataType.INTEGER)
        self.add_input_port("search_criteria", DataType.STRING)
        self.add_output_port("emails", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Read emails from IMAP server."""
        self.status = NodeStatus.RUNNING

        try:
            # Get connection settings
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            folder = self.get_parameter("folder", "INBOX")
            limit = self.get_parameter("limit", 10)
            search_criteria = self.get_parameter("search_criteria", "ALL")
            use_ssl = self.get_parameter("use_ssl", True)

            # Resolve {{variable}} patterns in connection parameters

            # Resolve credentials using CredentialAwareMixin
            username, password = await self.resolve_username_password(
                context,
                credential_name_param="credential_name",
                username_param="username",
                password_param="password",
                env_prefix="IMAP",
                required=True,
            )

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
                    id_list.reverse()

                    emails_list = []
                    for msg_id in id_list:
                        status, msg_data = mail.fetch(msg_id, "(RFC822)")
                        if status == "OK":
                            raw_email = msg_data[0][1]
                            msg = email_module.message_from_bytes(raw_email)
                            parsed = parse_email_message(msg)
                            parsed["uid"] = (
                                msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
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
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for read emails")

                    emails = await loop.run_in_executor(None, _read_emails_sync)

                    self.set_output_value("emails", emails)
                    self.set_output_value("count", len(emails))

                    logger.info(f"Read {len(emails)} emails from {folder} (attempt {attempts})")
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"count": len(emails), "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except imaplib.IMAP4.error as e:
                    if "authentication" in str(e).lower():
                        raise
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


@properties(
    PropertyDef(
        "email",
        PropertyType.JSON,
        required=True,
        label="Email",
        tooltip="Email data object to extract content from",
    ),
)
@node(category="email")
class GetEmailContentNode(BaseNode):
    """
    Extract content from an email object.

    Parses email data and extracts subject, body, sender, etc.
    """

    # @category: email
    # @requires: email
    # @ports: email -> subject, from, to, date, body_text, body_html, attachments

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize GetEmailContent node."""
        super().__init__(node_id, config)
        self.name = "Get Email Content"
        self.node_type = "GetEmailContentNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("email", DataType.DICT)
        self.add_output_port("subject", DataType.STRING)
        self.add_output_port("from", DataType.STRING)
        self.add_output_port("to", DataType.STRING)
        self.add_output_port("date", DataType.STRING)
        self.add_output_port("body_text", DataType.STRING)
        self.add_output_port("body_html", DataType.STRING)
        self.add_output_port("attachments", DataType.LIST)

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

            logger.debug(f"Extracted email content: {email_data.get('subject', 'No subject')}")
            self.status = NodeStatus.SUCCESS
            return {"success": True}

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to extract email content: {e}")
            return {"success": False, "error": str(e)}


@properties(
    PropertyDef(
        "emails",
        PropertyType.LIST,
        required=True,
        label="Emails",
        tooltip="List of email objects to filter",
    ),
    PropertyDef(
        "subject_contains",
        PropertyType.STRING,
        label="Subject Contains",
        tooltip="Filter emails containing this text in subject",
    ),
    PropertyDef(
        "from_contains",
        PropertyType.STRING,
        label="From Contains",
        tooltip="Filter emails containing this text in sender",
    ),
    PropertyDef(
        "has_attachments",
        PropertyType.BOOLEAN,
        label="Has Attachments",
        tooltip="Filter emails that have attachments",
    ),
)
@node(category="email")
class FilterEmailsNode(BaseNode):
    """
    Filter a list of emails based on criteria.

    Supports filtering by subject, sender, date range, etc.
    """

    # @category: email
    # @requires: email
    # @ports: emails, subject_contains, from_contains, has_attachments -> filtered, count

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize FilterEmails node."""
        super().__init__(node_id, config)
        self.name = "Filter Emails"
        self.node_type = "FilterEmailsNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("emails", DataType.LIST)
        self.add_input_port("subject_contains", DataType.STRING)
        self.add_input_port("from_contains", DataType.STRING)
        self.add_input_port("has_attachments", DataType.BOOLEAN)
        self.add_output_port("filtered", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Filter emails based on criteria."""
        self.status = NodeStatus.RUNNING

        try:
            emails = self.get_input_value("emails") or []
            subject_contains = self.get_parameter("subject_contains", "")
            from_contains = self.get_parameter("from_contains", "")
            has_attachments = self.get_parameter("has_attachments", None)

            # Resolve {{variable}} patterns

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
