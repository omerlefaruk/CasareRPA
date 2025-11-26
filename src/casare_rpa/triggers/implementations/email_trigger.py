"""
CasareRPA - Email Trigger

Trigger that fires when new emails arrive matching specified criteria.
Supports IMAP, Microsoft Graph API, and Gmail API.
"""

import asyncio
import email as email_lib
import imaplib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from ..base import BaseTrigger, BaseTriggerConfig, TriggerStatus, TriggerType
from ..registry import register_trigger


@register_trigger
class EmailTrigger(BaseTrigger):
    """
    Trigger that monitors email inbox for new messages.

    Configuration options:
        provider: Email provider (imap, graph, gmail)
        server: IMAP server hostname
        port: Server port (default: 993 for IMAP SSL)
        username: Email username
        password_credential: Credential alias for password
        folder: Folder to monitor (default: INBOX)
        from_filter: Filter by sender (regex pattern)
        subject_filter: Filter by subject (regex pattern)
        poll_interval: Polling interval in seconds

    Payload provided to workflow:
        email_id: Unique email identifier
        from_address: Sender email address
        subject: Email subject
        body: Email body (text)
        received_at: When the email was received
    """

    trigger_type = TriggerType.EMAIL
    display_name = "Email"
    description = "Trigger when new emails arrive"
    icon = "mail"
    category = "External"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._poll_task: Optional[asyncio.Task] = None
        self._seen_ids: Set[str] = set()
        self._running = False

    async def start(self) -> bool:
        """Start the email trigger."""
        config = self.config.config
        provider = config.get('provider', 'imap')

        if provider == 'imap':
            # Validate IMAP settings
            if not config.get('server'):
                self._error_message = "IMAP server is required"
                self._status = TriggerStatus.ERROR
                return False

            if not config.get('username'):
                self._error_message = "Username is required"
                self._status = TriggerStatus.ERROR
                return False

        self._running = True
        self._status = TriggerStatus.ACTIVE

        # Start polling task
        self._poll_task = asyncio.create_task(self._poll_loop())

        logger.info(
            f"Email trigger started: {self.config.name} "
            f"(provider: {provider}, folder: {config.get('folder', 'INBOX')})"
        )
        return True

    async def stop(self) -> bool:
        """Stop the email trigger."""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        self._status = TriggerStatus.INACTIVE
        logger.info(f"Email trigger stopped: {self.config.name}")
        return True

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        config = self.config.config
        poll_interval = config.get('poll_interval', 60)
        provider = config.get('provider', 'imap')

        while self._running:
            try:
                if provider == 'imap':
                    new_emails = await self._check_imap()
                elif provider == 'graph':
                    new_emails = await self._check_graph()
                elif provider == 'gmail':
                    new_emails = await self._check_gmail()
                else:
                    logger.error(f"Unknown email provider: {provider}")
                    new_emails = []

                # Process new emails
                for email_data in new_emails:
                    if self._should_process_email(email_data):
                        await self._process_email(email_data)

            except Exception as e:
                logger.error(f"Email poll error: {e}")

            # Wait for next poll
            await asyncio.sleep(poll_interval)

    async def _check_imap(self) -> List[Dict[str, Any]]:
        """Check IMAP mailbox for new emails."""
        config = self.config.config
        server = config.get('server', '')
        port = config.get('port', 993)
        username = config.get('username', '')
        password = config.get('password', '')  # In production, use credential manager
        folder = config.get('folder', 'INBOX')

        new_emails = []

        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            mail.select(folder)

            # Search for unseen emails
            _, message_numbers = mail.search(None, 'UNSEEN')

            for num in message_numbers[0].split():
                email_id = num.decode() if isinstance(num, bytes) else str(num)

                if email_id in self._seen_ids:
                    continue

                # Fetch email
                _, msg_data = mail.fetch(num, '(RFC822)')
                raw_email = msg_data[0][1]

                if isinstance(raw_email, bytes):
                    msg = email_lib.message_from_bytes(raw_email)
                else:
                    msg = email_lib.message_from_string(raw_email)

                # Extract email data
                email_data = {
                    'id': email_id,
                    'from_address': msg.get('From', ''),
                    'to_address': msg.get('To', ''),
                    'subject': msg.get('Subject', ''),
                    'date': msg.get('Date', ''),
                    'body': self._get_email_body(msg),
                }

                new_emails.append(email_data)
                self._seen_ids.add(email_id)

            mail.logout()

        except Exception as e:
            logger.error(f"IMAP error: {e}")

        return new_emails

    async def _check_graph(self) -> List[Dict[str, Any]]:
        """Check Microsoft Graph API for new emails."""
        # Placeholder - requires Microsoft Graph SDK
        logger.warning("Microsoft Graph API not yet implemented")
        return []

    async def _check_gmail(self) -> List[Dict[str, Any]]:
        """Check Gmail API for new emails."""
        # Placeholder - requires Google API client
        logger.warning("Gmail API not yet implemented")
        return []

    def _get_email_body(self, msg) -> str:
        """Extract email body text."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except Exception:
                body = str(msg.get_payload())

        return body

    def _should_process_email(self, email_data: Dict[str, Any]) -> bool:
        """Check if email matches filters."""
        config = self.config.config

        # Check from filter
        from_filter = config.get('from_filter', '')
        if from_filter:
            from_addr = email_data.get('from_address', '')
            if not re.search(from_filter, from_addr, re.IGNORECASE):
                return False

        # Check subject filter
        subject_filter = config.get('subject_filter', '')
        if subject_filter:
            subject = email_data.get('subject', '')
            if not re.search(subject_filter, subject, re.IGNORECASE):
                return False

        return True

    async def _process_email(self, email_data: Dict[str, Any]) -> None:
        """Process a matching email and emit trigger."""
        payload = {
            "email_id": email_data.get('id', ''),
            "from_address": email_data.get('from_address', ''),
            "to_address": email_data.get('to_address', ''),
            "subject": email_data.get('subject', ''),
            "body": email_data.get('body', ''),
            "received_at": email_data.get('date', datetime.utcnow().isoformat()),
        }

        metadata = {
            "source": "email",
            "provider": self.config.config.get('provider', 'imap'),
            "folder": self.config.config.get('folder', 'INBOX'),
        }

        await self.emit(payload, metadata)

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate email trigger configuration."""
        config = self.config.config

        provider = config.get('provider', 'imap')
        valid_providers = ['imap', 'graph', 'gmail']
        if provider not in valid_providers:
            return False, f"Invalid provider. Must be one of: {valid_providers}"

        if provider == 'imap':
            if not config.get('server'):
                return False, "IMAP server is required"
            if not config.get('username'):
                return False, "Username is required"

        poll_interval = config.get('poll_interval', 60)
        if poll_interval < 10:
            return False, "poll_interval must be at least 10 seconds"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for email trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {"type": "integer", "minimum": 0, "maximum": 3, "default": 1},
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "provider": {
                    "type": "string",
                    "enum": ["imap", "graph", "gmail"],
                    "default": "imap",
                    "description": "Email provider",
                },
                "server": {
                    "type": "string",
                    "description": "IMAP server hostname",
                },
                "port": {
                    "type": "integer",
                    "default": 993,
                    "description": "Server port",
                },
                "username": {
                    "type": "string",
                    "description": "Email username",
                },
                "password_credential": {
                    "type": "string",
                    "description": "Credential alias for password",
                },
                "folder": {
                    "type": "string",
                    "default": "INBOX",
                    "description": "Folder to monitor",
                },
                "from_filter": {
                    "type": "string",
                    "description": "Regex pattern to filter by sender",
                },
                "subject_filter": {
                    "type": "string",
                    "description": "Regex pattern to filter by subject",
                },
                "poll_interval": {
                    "type": "integer",
                    "minimum": 10,
                    "default": 60,
                    "description": "Polling interval in seconds",
                },
            },
            "required": ["name"],
        }
