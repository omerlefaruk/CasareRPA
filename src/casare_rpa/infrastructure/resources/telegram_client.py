"""
Telegram Bot API Client

Async HTTP client for interacting with the Telegram Bot API.
Supports sending messages, media, and handling updates.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union
import aiohttp
from loguru import logger


class TelegramAPIError(Exception):
    """Exception raised for Telegram API errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        description: Optional[str] = None,
    ):
        self.error_code = error_code
        self.description = description
        super().__init__(message)


@dataclass
class TelegramConfig:
    """Configuration for Telegram Bot API client."""

    bot_token: str
    base_url: str = "https://api.telegram.org"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

    @property
    def api_url(self) -> str:
        """Get the full API URL with bot token."""
        return f"{self.base_url}/bot{self.bot_token}"


@dataclass
class TelegramMessage:
    """Represents a Telegram message response."""

    message_id: int
    chat_id: int
    date: int
    text: Optional[str] = None
    from_user: Optional[dict] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> "TelegramMessage":
        """Create TelegramMessage from API response."""
        return cls(
            message_id=data.get("message_id", 0),
            chat_id=data.get("chat", {}).get("id", 0),
            date=data.get("date", 0),
            text=data.get("text"),
            from_user=data.get("from"),
            raw=data,
        )


class TelegramClient:
    """
    Async client for Telegram Bot API.

    Features:
    - Automatic retry on transient errors
    - File upload support (photos, documents, etc.)
    - Rate limiting awareness
    - Proper error handling

    Usage:
        config = TelegramConfig(bot_token="123456:ABC-DEF...")
        client = TelegramClient(config)

        async with client:
            result = await client.send_message(chat_id=123, text="Hello!")
    """

    def __init__(self, config: TelegramConfig):
        """Initialize the Telegram client.

        Args:
            config: TelegramConfig with bot token and settings
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "TelegramClient":
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
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        data: Optional[dict] = None,
        files: Optional[dict[str, tuple]] = None,
    ) -> dict:
        """
        Make a request to the Telegram Bot API.

        Args:
            method: API method name (e.g., "sendMessage")
            data: Request parameters
            files: Files to upload as {field_name: (filename, file_content, content_type)}

        Returns:
            API response data

        Raises:
            TelegramAPIError: If the API returns an error
        """
        session = await self._ensure_session()
        url = f"{self.config.api_url}/{method}"

        for attempt in range(self.config.max_retries):
            try:
                if files:
                    # Multipart form data for file uploads
                    form_data = aiohttp.FormData()
                    if data:
                        for key, value in data.items():
                            if value is not None:
                                form_data.add_field(key, str(value))
                    for field_name, (filename, content, content_type) in files.items():
                        form_data.add_field(
                            field_name,
                            content,
                            filename=filename,
                            content_type=content_type,
                        )
                    async with session.post(url, data=form_data) as response:
                        result = await response.json()
                else:
                    # JSON request
                    async with session.post(url, json=data or {}) as response:
                        result = await response.json()

                if not result.get("ok"):
                    error_code = result.get("error_code")
                    description = result.get("description", "Unknown error")

                    # Check for rate limiting (error code 429)
                    if error_code == 429:
                        retry_after = result.get("parameters", {}).get("retry_after", 5)
                        logger.warning(f"Telegram rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue

                    raise TelegramAPIError(
                        f"Telegram API error: {description}",
                        error_code=error_code,
                        description=description,
                    )

                return result.get("result", {})

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Telegram request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise TelegramAPIError(f"Network error: {e}") from e

        raise TelegramAPIError("Max retries exceeded")

    # =========================================================================
    # Message Methods
    # =========================================================================

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[dict] = None,
    ) -> TelegramMessage:
        """
        Send a text message.

        Args:
            chat_id: Target chat ID or @username
            text: Message text (1-4096 characters)
            parse_mode: "Markdown", "MarkdownV2", or "HTML"
            disable_notification: Send silently
            reply_to_message_id: Message to reply to
            reply_markup: Inline keyboard or reply keyboard

        Returns:
            TelegramMessage with message details
        """
        data = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            data["parse_mode"] = parse_mode
        if disable_notification:
            data["disable_notification"] = True
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            import json

            data["reply_markup"] = json.dumps(reply_markup)

        result = await self._request("sendMessage", data)
        return TelegramMessage.from_response(result)

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[str, Path, bytes],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> TelegramMessage:
        """
        Send a photo.

        Args:
            chat_id: Target chat ID
            photo: File path, URL, or bytes
            caption: Photo caption (0-1024 characters)
            parse_mode: Caption parse mode
            disable_notification: Send silently
            reply_to_message_id: Message to reply to

        Returns:
            TelegramMessage with message details
        """
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        if parse_mode:
            data["parse_mode"] = parse_mode
        if disable_notification:
            data["disable_notification"] = True
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        files = None
        if isinstance(photo, (str, Path)):
            photo_path = Path(photo)
            if photo_path.exists():
                # Local file
                content = photo_path.read_bytes()
                content_type = self._guess_content_type(photo_path)
                files = {"photo": (photo_path.name, content, content_type)}
            else:
                # URL or file_id
                data["photo"] = str(photo)
        elif isinstance(photo, bytes):
            files = {"photo": ("photo.jpg", photo, "image/jpeg")}

        result = await self._request("sendPhoto", data, files)
        return TelegramMessage.from_response(result)

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[str, Path, bytes],
        filename: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> TelegramMessage:
        """
        Send a document/file.

        Args:
            chat_id: Target chat ID
            document: File path, URL, or bytes
            filename: Custom filename (for bytes)
            caption: Document caption
            parse_mode: Caption parse mode
            disable_notification: Send silently
            reply_to_message_id: Message to reply to

        Returns:
            TelegramMessage with message details
        """
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        if parse_mode:
            data["parse_mode"] = parse_mode
        if disable_notification:
            data["disable_notification"] = True
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        files = None
        if isinstance(document, (str, Path)):
            doc_path = Path(document)
            if doc_path.exists():
                content = doc_path.read_bytes()
                content_type = self._guess_content_type(doc_path)
                files = {"document": (doc_path.name, content, content_type)}
            else:
                data["document"] = str(document)
        elif isinstance(document, bytes):
            fname = filename or "document"
            files = {"document": (fname, document, "application/octet-stream")}

        result = await self._request("sendDocument", data, files)
        return TelegramMessage.from_response(result)

    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> TelegramMessage:
        """
        Send a location.

        Args:
            chat_id: Target chat ID
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            disable_notification: Send silently
            reply_to_message_id: Message to reply to

        Returns:
            TelegramMessage with message details
        """
        data = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
        }
        if disable_notification:
            data["disable_notification"] = True
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        result = await self._request("sendLocation", data)
        return TelegramMessage.from_response(result)

    # =========================================================================
    # Webhook Methods
    # =========================================================================

    async def set_webhook(
        self,
        url: str,
        allowed_updates: Optional[list[str]] = None,
        drop_pending_updates: bool = False,
    ) -> bool:
        """
        Set webhook URL for receiving updates.

        Args:
            url: HTTPS URL for webhook
            allowed_updates: List of update types to receive
            drop_pending_updates: Drop pending updates

        Returns:
            True if successful
        """
        data = {"url": url}
        if allowed_updates:
            import json

            data["allowed_updates"] = json.dumps(allowed_updates)
        if drop_pending_updates:
            data["drop_pending_updates"] = True

        await self._request("setWebhook", data)
        logger.info(f"Telegram webhook set to: {url}")
        return True

    async def delete_webhook(self, drop_pending_updates: bool = False) -> bool:
        """
        Delete webhook and switch to getUpdates.

        Args:
            drop_pending_updates: Drop pending updates

        Returns:
            True if successful
        """
        data = {}
        if drop_pending_updates:
            data["drop_pending_updates"] = True

        await self._request("deleteWebhook", data)
        logger.info("Telegram webhook deleted")
        return True

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Get updates via long polling.

        Args:
            offset: Offset to acknowledge processed updates
            limit: Max number of updates (1-100)
            timeout: Timeout in seconds for long polling
            allowed_updates: List of update types to receive

        Returns:
            List of update objects
        """
        data = {
            "limit": min(limit, 100),
            "timeout": timeout,
        }
        if offset is not None:
            data["offset"] = offset
        if allowed_updates:
            import json

            data["allowed_updates"] = json.dumps(allowed_updates)

        return await self._request("getUpdates", data)

    async def get_me(self) -> dict:
        """Get bot info."""
        return await self._request("getMe")

    # =========================================================================
    # Edit/Delete Methods
    # =========================================================================

    async def edit_message_text(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> TelegramMessage:
        """
        Edit a message text.

        Args:
            chat_id: Target chat ID
            message_id: ID of message to edit
            text: New text content
            parse_mode: Text parse mode
            reply_markup: New inline keyboard

        Returns:
            Edited TelegramMessage
        """
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            import json

            data["reply_markup"] = json.dumps(reply_markup)

        result = await self._request("editMessageText", data)
        return TelegramMessage.from_response(result)

    async def edit_message_caption(
        self,
        chat_id: Union[int, str],
        message_id: int,
        caption: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> TelegramMessage:
        """
        Edit a message caption.

        Args:
            chat_id: Target chat ID
            message_id: ID of message to edit
            caption: New caption
            parse_mode: Caption parse mode
            reply_markup: New inline keyboard

        Returns:
            Edited TelegramMessage
        """
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption,
        }
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            import json

            data["reply_markup"] = json.dumps(reply_markup)

        result = await self._request("editMessageCaption", data)
        return TelegramMessage.from_response(result)

    async def delete_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
    ) -> bool:
        """
        Delete a message.

        Args:
            chat_id: Target chat ID
            message_id: ID of message to delete

        Returns:
            True if successful
        """
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        await self._request("deleteMessage", data)
        return True

    # =========================================================================
    # Media Group Methods
    # =========================================================================

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: list[dict],
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> list[TelegramMessage]:
        """
        Send a group of photos or videos as an album.

        Args:
            chat_id: Target chat ID
            media: Array of InputMediaPhoto/InputMediaVideo
            disable_notification: Send silently
            reply_to_message_id: Message to reply to

        Returns:
            List of TelegramMessage
        """
        import json

        data = {
            "chat_id": chat_id,
            "media": json.dumps(media),
        }
        if disable_notification:
            data["disable_notification"] = True
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        results = await self._request("sendMediaGroup", data)
        return [TelegramMessage.from_response(r) for r in results]

    # =========================================================================
    # Callback Query Methods
    # =========================================================================

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: int = 0,
    ) -> bool:
        """
        Answer a callback query from inline keyboard.

        Args:
            callback_query_id: ID of callback query to answer
            text: Text to show (toast or alert)
            show_alert: Show as alert instead of toast
            url: URL to open (game URL)
            cache_time: Cache time in seconds

        Returns:
            True if successful
        """
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
        if show_alert:
            data["show_alert"] = True
        if url:
            data["url"] = url
        if cache_time > 0:
            data["cache_time"] = cache_time

        await self._request("answerCallbackQuery", data)
        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _guess_content_type(self, path: Path) -> str:
        """Guess content type from file extension."""
        suffix = path.suffix.lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".mp4": "video/mp4",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".txt": "text/plain",
            ".json": "application/json",
        }
        return content_types.get(suffix, "application/octet-stream")
