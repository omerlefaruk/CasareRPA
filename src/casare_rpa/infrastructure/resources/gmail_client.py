"""
Gmail API Client

Async client for interacting with the Gmail API v1.
Supports sending, reading, searching, and managing emails.
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass, field
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Union

import aiohttp
from loguru import logger


class GmailAPIError(Exception):
    """Exception raised for Gmail API errors."""

    def __init__(
        self,
        message: str,
        error_code: int | None = None,
        reason: str | None = None,
    ):
        self.error_code = error_code
        self.reason = reason
        super().__init__(message)


@dataclass
class GmailConfig:
    """Configuration for Gmail API client."""

    access_token: str
    user_id: str = "me"
    base_url: str = "https://gmail.googleapis.com/gmail/v1"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

    @property
    def users_url(self) -> str:
        """Get the users endpoint URL."""
        return f"{self.base_url}/users/{self.user_id}"


@dataclass
class GmailMessage:
    """Represents a Gmail message."""

    id: str
    thread_id: str
    label_ids: list[str] = field(default_factory=list)
    snippet: str = ""
    subject: str = ""
    from_address: str = ""
    to_addresses: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)
    date: str = ""
    body_plain: str = ""
    body_html: str = ""
    attachments: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> GmailMessage:
        """Create GmailMessage from API response."""
        message = cls(
            id=data.get("id", ""),
            thread_id=data.get("threadId", ""),
            label_ids=data.get("labelIds", []),
            snippet=data.get("snippet", ""),
            raw=data,
        )

        # Parse headers
        payload = data.get("payload", {})
        headers = payload.get("headers", [])
        header_map = {h["name"].lower(): h["value"] for h in headers}

        message.subject = header_map.get("subject", "")
        message.from_address = header_map.get("from", "")
        message.to_addresses = cls._parse_addresses(header_map.get("to", ""))
        message.cc_addresses = cls._parse_addresses(header_map.get("cc", ""))
        message.date = header_map.get("date", "")

        # Parse body and attachments
        message.body_plain, message.body_html, message.attachments = cls._parse_payload(payload)

        return message

    @staticmethod
    def _parse_addresses(addr_string: str) -> list[str]:
        """Parse comma-separated email addresses."""
        if not addr_string:
            return []
        return [addr.strip() for addr in addr_string.split(",")]

    @staticmethod
    def _parse_payload(payload: dict) -> tuple[str, str, list[dict]]:
        """Parse message payload for body and attachments."""
        body_plain = ""
        body_html = ""
        attachments = []

        mime_type = payload.get("mimeType", "")
        parts = payload.get("parts", [])

        if not parts:
            # Single-part message
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                if "html" in mime_type:
                    body_html = decoded
                else:
                    body_plain = decoded
        else:
            # Multi-part message
            for part in parts:
                part_mime = part.get("mimeType", "")
                part_body = part.get("body", {})

                if part_body.get("attachmentId"):
                    # Attachment
                    attachments.append(
                        {
                            "attachment_id": part_body.get("attachmentId"),
                            "filename": part.get("filename", "unknown"),
                            "mime_type": part_mime,
                            "size": part_body.get("size", 0),
                        }
                    )
                elif part_body.get("data"):
                    # Body part
                    decoded = base64.urlsafe_b64decode(part_body["data"]).decode(
                        "utf-8", errors="replace"
                    )
                    if "html" in part_mime:
                        body_html = decoded
                    elif "plain" in part_mime:
                        body_plain = decoded

                # Recurse into nested parts
                if part.get("parts"):
                    nested_plain, nested_html, nested_attachments = GmailMessage._parse_payload(
                        part
                    )
                    if not body_plain:
                        body_plain = nested_plain
                    if not body_html:
                        body_html = nested_html
                    attachments.extend(nested_attachments)

        return body_plain, body_html, attachments


@dataclass
class GmailThread:
    """Represents a Gmail thread."""

    id: str
    snippet: str = ""
    history_id: str = ""
    messages: list[GmailMessage] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> GmailThread:
        """Create GmailThread from API response."""
        messages = [GmailMessage.from_response(msg) for msg in data.get("messages", [])]
        return cls(
            id=data.get("id", ""),
            snippet=data.get("snippet", ""),
            history_id=data.get("historyId", ""),
            messages=messages,
            raw=data,
        )


@dataclass
class GmailDraft:
    """Represents a Gmail draft."""

    id: str
    message: GmailMessage | None = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> GmailDraft:
        """Create GmailDraft from API response."""
        message = None
        if "message" in data:
            message = GmailMessage.from_response(data["message"])
        return cls(
            id=data.get("id", ""),
            message=message,
            raw=data,
        )


class GmailClient:
    """
    Async client for Gmail API.

    Features:
    - OAuth 2.0 authentication via access token
    - Send plain text and HTML emails
    - Attachment support
    - Email search with Gmail query syntax
    - Thread management
    - Draft creation

    Usage:
        config = GmailConfig(access_token="ya29.xxx...")
        client = GmailClient(config)

        async with client:
            result = await client.send_message(
                to=["user@example.com"],
                subject="Hello",
                body="Test message"
            )
    """

    def __init__(self, config: GmailConfig):
        """Initialize the Gmail client.

        Args:
            config: GmailConfig with access token and settings
        """
        self.config = config
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> GmailClient:
        """Enter async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
        data: bytes | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        Make a request to the Gmail API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            data: Raw body data
            headers: Additional headers

        Returns:
            API response data

        Raises:
            GmailAPIError: If the API returns an error
        """
        session = await self._ensure_session()
        url = f"{self.config.users_url}/{endpoint}"

        request_headers = {}
        if headers:
            request_headers.update(headers)

        for attempt in range(self.config.max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=request_headers,
                ) as response:
                    if response.status == 204:
                        return {}

                    result = await response.json()

                    if response.status >= 400:
                        error = result.get("error", {})
                        error_code = error.get("code", response.status)
                        reason = error.get("message", "Unknown error")

                        # Rate limiting (429)
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", "5"))
                            logger.warning(f"Gmail rate limited. Waiting {retry_after}s...")
                            await asyncio.sleep(retry_after)
                            continue

                        # Auth error (401)
                        if response.status == 401:
                            raise GmailAPIError(
                                "Authentication failed. Access token may be expired.",
                                error_code=401,
                                reason="unauthorized",
                            )

                        raise GmailAPIError(
                            f"Gmail API error: {reason}",
                            error_code=error_code,
                            reason=reason,
                        )

                    return result

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Gmail request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise GmailAPIError(f"Network error: {e}") from e

        raise GmailAPIError("Max retries exceeded")

    # =========================================================================
    # Send Methods
    # =========================================================================

    async def send_message(
        self,
        to: list[str],
        subject: str,
        body: str,
        body_type: str = "plain",
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        from_address: str | None = None,
        reply_to: str | None = None,
        attachments: list[str | Path | dict] | None = None,
        thread_id: str | None = None,
    ) -> GmailMessage:
        """
        Send an email message.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: Body type ("plain" or "html")
            cc: List of CC recipients
            bcc: List of BCC recipients
            from_address: Sender address (default: authenticated user)
            reply_to: Reply-to address
            attachments: List of file paths or attachment dicts
            thread_id: Thread ID to add message to

        Returns:
            GmailMessage with sent message details
        """
        message = await self._create_message(
            to=to,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc,
            bcc=bcc,
            from_address=from_address,
            reply_to=reply_to,
            attachments=attachments,
        )

        send_data = {"raw": message}
        if thread_id:
            send_data["threadId"] = thread_id

        result = await self._request("POST", "messages/send", json_data=send_data)
        logger.info(f"Email sent: {result.get('id')}")
        return GmailMessage.from_response(result)

    async def reply_to_message(
        self,
        message_id: str,
        thread_id: str,
        body: str,
        body_type: str = "plain",
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[str | Path | dict] | None = None,
    ) -> GmailMessage:
        """
        Reply to an existing message.

        Args:
            message_id: ID of message to reply to
            thread_id: Thread ID of the conversation
            body: Reply body content
            body_type: Body type ("plain" or "html")
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of file paths or attachment dicts

        Returns:
            GmailMessage with sent reply details
        """
        # Get original message for reply headers
        original = await self.get_message(message_id, format_type="metadata")
        headers = {
            h["name"].lower(): h["value"]
            for h in original.raw.get("payload", {}).get("headers", [])
        }

        # Build reply addresses
        reply_to = headers.get("reply-to") or headers.get("from", "")
        to_addresses = [reply_to] if reply_to else []

        # Build reply subject
        subject = headers.get("subject", "")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # Get References and Message-ID for threading
        references = headers.get("references", "")
        original_message_id = headers.get("message-id", "")
        if original_message_id:
            if references:
                references = f"{references} {original_message_id}"
            else:
                references = original_message_id

        message = await self._create_message(
            to=to_addresses,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            in_reply_to=original_message_id,
            references=references,
        )

        send_data = {"raw": message, "threadId": thread_id}
        result = await self._request("POST", "messages/send", json_data=send_data)
        logger.info(f"Reply sent: {result.get('id')}")
        return GmailMessage.from_response(result)

    async def forward_message(
        self,
        message_id: str,
        to: list[str],
        body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> GmailMessage:
        """
        Forward an existing message.

        Args:
            message_id: ID of message to forward
            to: List of recipient addresses
            body: Optional additional body text
            cc: List of CC recipients
            bcc: List of BCC recipients

        Returns:
            GmailMessage with forwarded message details
        """
        # Get original message
        original = await self.get_message(message_id, format_type="full")
        headers = {
            h["name"].lower(): h["value"]
            for h in original.raw.get("payload", {}).get("headers", [])
        }

        # Build forward subject
        subject = headers.get("subject", "")
        if not subject.lower().startswith("fwd:"):
            subject = f"Fwd: {subject}"

        # Build forward body
        forward_header = (
            f"\n\n---------- Forwarded message ----------\n"
            f"From: {headers.get('from', '')}\n"
            f"Date: {headers.get('date', '')}\n"
            f"Subject: {headers.get('subject', '')}\n"
            f"To: {headers.get('to', '')}\n\n"
        )

        original_body = original.body_plain or original.body_html or ""
        full_body = (body or "") + forward_header + original_body

        # Get attachments from original
        attachments = []
        for att in original.attachments:
            att_data = await self.get_attachment(message_id, att["attachment_id"])
            attachments.append(
                {
                    "filename": att["filename"],
                    "mime_type": att["mime_type"],
                    "data": att_data,
                }
            )

        return await self.send_message(
            to=to,
            subject=subject,
            body=full_body,
            body_type="plain",
            cc=cc,
            bcc=bcc,
            attachments=attachments if attachments else None,
        )

    async def create_draft(
        self,
        to: list[str],
        subject: str,
        body: str,
        body_type: str = "plain",
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[str | Path | dict] | None = None,
    ) -> GmailDraft:
        """
        Create a draft email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: Body type ("plain" or "html")
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of file paths or attachment dicts

        Returns:
            GmailDraft with draft details
        """
        message = await self._create_message(
            to=to,
            subject=subject,
            body=body,
            body_type=body_type,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
        )

        draft_data = {"message": {"raw": message}}
        result = await self._request("POST", "drafts", json_data=draft_data)
        logger.info(f"Draft created: {result.get('id')}")
        return GmailDraft.from_response(result)

    async def _create_message(
        self,
        to: list[str],
        subject: str,
        body: str,
        body_type: str = "plain",
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        from_address: str | None = None,
        reply_to: str | None = None,
        attachments: list[str | Path | dict] | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> str:
        """Create base64-encoded email message."""
        if attachments:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, body_type, "utf-8"))

            for attachment in attachments:
                part = await self._create_attachment_part(attachment)
                if part:
                    msg.attach(part)
        else:
            msg = MIMEText(body, body_type, "utf-8")

        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        if from_address:
            msg["From"] = from_address
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)
        if reply_to:
            msg["Reply-To"] = reply_to
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = references

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        return raw

    async def _create_attachment_part(self, attachment: str | Path | dict) -> MIMEBase | None:
        """Create MIME attachment part."""
        if isinstance(attachment, dict):
            # Attachment dict with data
            filename = attachment.get("filename", "attachment")
            mime_type = attachment.get("mime_type", "application/octet-stream")
            data = attachment.get("data", b"")
        elif isinstance(attachment, (str, Path)):
            # File path
            path = Path(attachment)
            if not path.exists():
                logger.warning(f"Attachment not found: {path}")
                return None
            filename = path.name
            mime_type = self._guess_mime_type(path)
            data = path.read_bytes()
        else:
            return None

        main_type, sub_type = (
            mime_type.split("/", 1) if "/" in mime_type else ("application", "octet-stream")
        )
        part = MIMEBase(main_type, sub_type)
        part.set_payload(data)

        import email.encoders

        email.encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=filename)

        return part

    def _guess_mime_type(self, path: Path) -> str:
        """Guess MIME type from file extension."""
        suffix = path.suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".html": "text/html",
            ".htm": "text/html",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".zip": "application/zip",
            ".json": "application/json",
            ".xml": "application/xml",
            ".csv": "text/csv",
        }
        return mime_types.get(suffix, "application/octet-stream")

    # =========================================================================
    # Read Methods
    # =========================================================================

    async def get_message(
        self,
        message_id: str,
        format_type: str = "full",
    ) -> GmailMessage:
        """
        Get a message by ID.

        Args:
            message_id: Message ID
            format_type: Response format ("minimal", "metadata", "full", "raw")

        Returns:
            GmailMessage with message details
        """
        result = await self._request(
            "GET",
            f"messages/{message_id}",
            params={"format": format_type},
        )
        return GmailMessage.from_response(result)

    async def search_messages(
        self,
        query: str = "",
        max_results: int = 100,
        label_ids: list[str] | None = None,
        include_spam_trash: bool = False,
        page_token: str | None = None,
    ) -> tuple[list[GmailMessage], str | None]:
        """
        Search for messages.

        Args:
            query: Gmail search query (e.g., "from:user@example.com is:unread")
            max_results: Maximum number of results (default 100)
            label_ids: Filter by label IDs
            include_spam_trash: Include spam and trash
            page_token: Token for pagination

        Returns:
            Tuple of (list of GmailMessages, next page token)
        """
        params = {
            "maxResults": min(max_results, 500),
        }
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids
        if include_spam_trash:
            params["includeSpamTrash"] = "true"
        if page_token:
            params["pageToken"] = page_token

        result = await self._request("GET", "messages", params=params)
        messages = []
        for msg_info in result.get("messages", []):
            msg = await self.get_message(msg_info["id"], format_type="metadata")
            messages.append(msg)

        next_token = result.get("nextPageToken")
        return messages, next_token

    async def get_thread(
        self,
        thread_id: str,
        format_type: str = "full",
    ) -> GmailThread:
        """
        Get a thread by ID.

        Args:
            thread_id: Thread ID
            format_type: Response format ("minimal", "metadata", "full")

        Returns:
            GmailThread with thread details
        """
        result = await self._request(
            "GET",
            f"threads/{thread_id}",
            params={"format": format_type},
        )
        return GmailThread.from_response(result)

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        """
        Get an attachment by ID.

        Args:
            message_id: Message ID containing the attachment
            attachment_id: Attachment ID

        Returns:
            Attachment data as bytes
        """
        result = await self._request(
            "GET",
            f"messages/{message_id}/attachments/{attachment_id}",
        )
        data = result.get("data", "")
        return base64.urlsafe_b64decode(data)

    # =========================================================================
    # Management Methods
    # =========================================================================

    async def modify_labels(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> GmailMessage:
        """
        Modify message labels.

        Args:
            message_id: Message ID
            add_labels: Labels to add
            remove_labels: Labels to remove

        Returns:
            Updated GmailMessage
        """
        modify_data = {}
        if add_labels:
            modify_data["addLabelIds"] = add_labels
        if remove_labels:
            modify_data["removeLabelIds"] = remove_labels

        result = await self._request(
            "POST",
            f"messages/{message_id}/modify",
            json_data=modify_data,
        )
        return GmailMessage.from_response(result)

    async def trash_message(self, message_id: str) -> GmailMessage:
        """Move message to trash."""
        result = await self._request("POST", f"messages/{message_id}/trash")
        return GmailMessage.from_response(result)

    async def untrash_message(self, message_id: str) -> GmailMessage:
        """Remove message from trash."""
        result = await self._request("POST", f"messages/{message_id}/untrash")
        return GmailMessage.from_response(result)

    async def delete_message(self, message_id: str) -> None:
        """Permanently delete a message."""
        await self._request("DELETE", f"messages/{message_id}")
        logger.info(f"Message deleted: {message_id}")

    async def get_labels(self) -> list[dict]:
        """Get all labels."""
        result = await self._request("GET", "labels")
        return result.get("labels", [])


__all__ = [
    "GmailAPIError",
    "GmailClient",
    "GmailConfig",
    "GmailDraft",
    "GmailMessage",
    "GmailThread",
]
