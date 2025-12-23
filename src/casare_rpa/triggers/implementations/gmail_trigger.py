"""
CasareRPA - Gmail Trigger

Trigger that fires when new emails arrive in Gmail matching specified criteria.
Uses Gmail API with OAuth 2.0 authentication.
"""

import base64
import re
from datetime import UTC, datetime, timezone
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.triggers.implementations.google_trigger_base import GoogleTriggerBase
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class GmailTrigger(GoogleTriggerBase):
    """
    Trigger that monitors Gmail inbox for new messages.

    Configuration options:
        client_id: Google OAuth client ID
        client_secret_credential: Credential alias for client secret
        access_token_credential: Credential alias for access token
        refresh_token_credential: Credential alias for refresh token
        label_ids: Gmail labels to monitor (default: INBOX)
        query: Gmail search query (e.g., "from:user@example.com subject:invoice")
        from_filter: Filter by sender (regex pattern)
        subject_filter: Filter by subject (regex pattern)
        include_attachments: Include attachment info in payload
        mark_as_read: Mark messages as read after processing
        poll_interval: Polling interval in seconds (default: 60)

    Payload provided to workflow:
        message_id: Gmail message ID
        thread_id: Gmail thread ID
        from_address: Sender email address
        to_address: Recipient email address
        subject: Email subject
        body: Email body (plain text preferred, falls back to HTML)
        received_at: When the email was received
        labels: List of Gmail labels
        attachments: List of attachment info (if include_attachments is True)
        snippet: Email snippet/preview
    """

    trigger_type = TriggerType.GMAIL
    display_name = "Gmail"
    description = "Trigger when new emails arrive in Gmail"
    icon = "mail"
    category = "Google"

    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._seen_message_ids: set[str] = set()
        self._history_id: str | None = None

    def get_required_scopes(self) -> list[str]:
        """Return required Gmail API scopes."""
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        if self.config.config.get("mark_as_read", False):
            scopes.append("https://www.googleapis.com/auth/gmail.modify")
        return scopes

    async def start(self) -> bool:
        """Start the Gmail trigger."""
        result = await super().start()
        if result:
            # Initialize history ID for incremental sync
            try:
                await self._initialize_history()
            except Exception as e:
                logger.warning(f"Failed to initialize Gmail history: {e}")
        return result

    async def _initialize_history(self) -> None:
        """Initialize history ID for incremental message sync."""
        client = await self._get_google_client()
        profile = await client.get(f"{self.GMAIL_API_BASE}/users/me/profile")
        self._history_id = profile.get("historyId")
        logger.debug(f"Gmail history initialized with ID: {self._history_id}")

    async def _poll(self) -> None:
        """Poll Gmail for new messages."""
        config = self.config.config
        label_ids = config.get("label_ids", ["INBOX"])
        if isinstance(label_ids, str):
            label_ids = [label_ids]

        query = config.get("query", "")

        try:
            client = await self._get_google_client()

            # Try incremental sync if we have a history ID
            new_messages = []
            if self._history_id:
                new_messages = await self._get_new_messages_by_history(client, label_ids)
            else:
                new_messages = await self._get_new_messages_by_query(client, label_ids, query)

            # Process new messages
            for message_data in new_messages:
                message_id = message_data.get("id", "")
                if message_id in self._seen_message_ids:
                    continue

                # Fetch full message details
                full_message = await self._get_message_details(client, message_id)
                if full_message and self._should_process_message(full_message):
                    await self._process_message(full_message)
                    self._seen_message_ids.add(message_id)

                    # Mark as read if configured
                    if config.get("mark_as_read", False):
                        await self._mark_as_read(client, message_id)

        except Exception as e:
            logger.error(f"Gmail poll error: {e}")
            raise

    async def _get_new_messages_by_history(
        self, client, label_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Get new messages using Gmail history API for efficient incremental sync."""
        try:
            params = {
                "startHistoryId": self._history_id,
                "historyTypes": "messageAdded",
            }
            if label_ids:
                params["labelId"] = label_ids[0]

            response = await client.get(f"{self.GMAIL_API_BASE}/users/me/history", params=params)

            # Update history ID
            if "historyId" in response:
                self._history_id = response["historyId"]

            # Extract new message IDs
            new_messages = []
            for history in response.get("history", []):
                for added in history.get("messagesAdded", []):
                    message = added.get("message", {})
                    if message.get("id"):
                        new_messages.append(message)

            return new_messages

        except Exception as e:
            logger.warning(f"History sync failed, falling back to query: {e}")
            self._history_id = None
            return []

    async def _get_new_messages_by_query(
        self, client, label_ids: list[str], query: str
    ) -> list[dict[str, Any]]:
        """Get messages matching query (fallback method)."""
        params = {
            "maxResults": 10,
            "q": f"is:unread {query}".strip() if query else "is:unread",
        }
        if label_ids:
            params["labelIds"] = ",".join(label_ids)

        response = await client.get(f"{self.GMAIL_API_BASE}/users/me/messages", params=params)

        return response.get("messages", [])

    async def _get_message_details(self, client, message_id: str) -> dict[str, Any] | None:
        """Fetch full message details including body."""
        try:
            message = await client.get(
                f"{self.GMAIL_API_BASE}/users/me/messages/{message_id}",
                params={"format": "full"},
            )
            return message
        except Exception as e:
            logger.error(f"Failed to fetch message {message_id}: {e}")
            return None

    def _should_process_message(self, message: dict[str, Any]) -> bool:
        """Check if message matches configured filters."""
        config = self.config.config
        headers = self._extract_headers(message)

        # Check from filter
        from_filter = config.get("from_filter", "")
        if from_filter:
            from_addr = headers.get("from", "")
            if not re.search(from_filter, from_addr, re.IGNORECASE):
                return False

        # Check subject filter
        subject_filter = config.get("subject_filter", "")
        if subject_filter:
            subject = headers.get("subject", "")
            if not re.search(subject_filter, subject, re.IGNORECASE):
                return False

        return True

    def _extract_headers(self, message: dict[str, Any]) -> dict[str, str]:
        """Extract headers from Gmail message payload."""
        headers = {}
        payload = message.get("payload", {})
        for header in payload.get("headers", []):
            name = header.get("name", "").lower()
            value = header.get("value", "")
            headers[name] = value
        return headers

    def _extract_body(self, message: dict[str, Any]) -> str:
        """Extract email body from Gmail message payload."""
        payload = message.get("payload", {})
        mime_type = payload.get("mimeType", "")

        # Simple text/plain or text/html body
        if mime_type in ("text/plain", "text/html"):
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data)
                return decoded.decode("utf-8", errors="replace")

        # Multipart message - look for text/plain first, then text/html
        parts = payload.get("parts", [])
        plain_body = ""
        html_body = ""

        for part in self._flatten_parts(parts):
            part_mime = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data", "")
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                if part_mime == "text/plain":
                    plain_body = decoded
                elif part_mime == "text/html" and not html_body:
                    html_body = decoded

        return plain_body if plain_body else html_body

    def _flatten_parts(self, parts: list[dict]) -> list[dict]:
        """Recursively flatten nested MIME parts."""
        result = []
        for part in parts:
            result.append(part)
            nested = part.get("parts", [])
            if nested:
                result.extend(self._flatten_parts(nested))
        return result

    def _extract_attachments(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract attachment info from Gmail message."""
        attachments = []
        payload = message.get("payload", {})
        parts = payload.get("parts", [])

        for part in self._flatten_parts(parts):
            filename = part.get("filename", "")
            if filename:
                body = part.get("body", {})
                attachments.append(
                    {
                        "filename": filename,
                        "mime_type": part.get("mimeType", ""),
                        "size": body.get("size", 0),
                        "attachment_id": body.get("attachmentId", ""),
                    }
                )

        return attachments

    async def _process_message(self, message: dict[str, Any]) -> None:
        """Process a matching email and emit trigger."""
        config = self.config.config
        headers = self._extract_headers(message)
        body = self._extract_body(message)

        payload = {
            "message_id": message.get("id", ""),
            "thread_id": message.get("threadId", ""),
            "from_address": headers.get("from", ""),
            "to_address": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "body": body,
            "received_at": datetime.fromtimestamp(
                int(message.get("internalDate", 0)) / 1000, tz=UTC
            ).isoformat(),
            "labels": message.get("labelIds", []),
            "snippet": message.get("snippet", ""),
        }

        if config.get("include_attachments", False):
            payload["attachments"] = self._extract_attachments(message)

        metadata = {
            "source": "gmail",
            "thread_id": message.get("threadId", ""),
            "history_id": message.get("historyId", ""),
        }

        await self.emit(payload, metadata)

    async def _mark_as_read(self, client, message_id: str) -> None:
        """Mark message as read by removing UNREAD label."""
        try:
            await client.post(
                f"{self.GMAIL_API_BASE}/users/me/messages/{message_id}/modify",
                json_data={"removeLabelIds": ["UNREAD"]},
            )
            logger.debug(f"Marked message {message_id} as read")
        except Exception as e:
            logger.warning(f"Failed to mark message {message_id} as read: {e}")

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate Gmail trigger configuration."""
        valid, error = super().validate_config()
        if not valid:
            return valid, error

        config = self.config.config

        # Validate label IDs format
        label_ids = config.get("label_ids", ["INBOX"])
        if isinstance(label_ids, str):
            label_ids = [label_ids]
        if not label_ids:
            return False, "At least one label ID is required"

        # Validate regex patterns
        from_filter = config.get("from_filter", "")
        if from_filter:
            try:
                re.compile(from_filter)
            except re.error as e:
                return False, f"Invalid from_filter regex: {e}"

        subject_filter = config.get("subject_filter", "")
        if subject_filter:
            try:
                re.compile(subject_filter)
            except re.error as e:
                return False, f"Invalid subject_filter regex: {e}"

        return True, None

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get JSON schema for Gmail trigger configuration."""
        base_schema = super().get_config_schema()
        base_schema["properties"].update(
            {
                "label_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["INBOX"],
                    "description": "Gmail labels to monitor (e.g., INBOX, IMPORTANT)",
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'from:user@example.com')",
                },
                "from_filter": {
                    "type": "string",
                    "description": "Regex pattern to filter by sender",
                },
                "subject_filter": {
                    "type": "string",
                    "description": "Regex pattern to filter by subject",
                },
                "include_attachments": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include attachment information in payload",
                },
                "mark_as_read": {
                    "type": "boolean",
                    "default": False,
                    "description": "Mark messages as read after processing",
                },
            }
        )
        return base_schema


__all__ = ["GmailTrigger"]
