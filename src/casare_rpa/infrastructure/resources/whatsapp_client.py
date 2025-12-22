"""
WhatsApp Business Cloud API Client

Async HTTP client for interacting with the WhatsApp Business Cloud API (Meta Graph API).
Supports sending messages, templates, media, and handling webhooks.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union
import aiohttp
from loguru import logger


class WhatsAppAPIError(Exception):
    """Exception raised for WhatsApp API errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        error_subcode: Optional[int] = None,
        error_type: Optional[str] = None,
    ):
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.error_type = error_type
        super().__init__(message)


@dataclass
class WhatsAppConfig:
    """Configuration for WhatsApp Business Cloud API client."""

    access_token: str
    phone_number_id: str
    business_account_id: Optional[str] = None
    api_version: str = "v18.0"
    base_url: str = "https://graph.facebook.com"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

    @property
    def api_url(self) -> str:
        """Get the full API URL for messages."""
        return f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"

    @property
    def media_url(self) -> str:
        """Get the full API URL for media uploads."""
        return f"{self.base_url}/{self.api_version}/{self.phone_number_id}/media"

    @property
    def templates_url(self) -> str:
        """Get the full API URL for templates."""
        if not self.business_account_id:
            raise WhatsAppAPIError("business_account_id required for templates")
        return f"{self.base_url}/{self.api_version}/{self.business_account_id}/message_templates"


@dataclass
class WhatsAppMessage:
    """Represents a WhatsApp message response."""

    message_id: str
    phone_number: str
    status: str = "sent"
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict, phone_number: str) -> "WhatsAppMessage":
        """Create WhatsAppMessage from API response."""
        messages = data.get("messages", [])
        message_id = messages[0].get("id", "") if messages else ""
        return cls(
            message_id=message_id,
            phone_number=phone_number,
            status="sent",
            raw=data,
        )


@dataclass
class WhatsAppTemplate:
    """Represents a WhatsApp message template."""

    name: str
    language: str
    category: str
    status: str
    id: str = ""
    components: list = field(default_factory=list)

    @classmethod
    def from_response(cls, data: dict) -> "WhatsAppTemplate":
        """Create WhatsAppTemplate from API response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            language=data.get("language", ""),
            category=data.get("category", ""),
            status=data.get("status", ""),
            components=data.get("components", []),
        )


class WhatsAppClient:
    """
    Async client for WhatsApp Business Cloud API.

    Features:
    - Send text, template, media, and location messages
    - Template management and listing
    - Media upload support
    - Automatic retry on transient errors
    - Proper error handling

    Usage:
        config = WhatsAppConfig(
            access_token="EAABx...",
            phone_number_id="123456789",
        )
        client = WhatsAppClient(config)

        async with client:
            result = await client.send_message(to="+1234567890", text="Hello!")
    """

    def __init__(self, config: WhatsAppConfig):
        """Initialize the WhatsApp client.

        Args:
            config: WhatsAppConfig with access token and phone number ID
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "WhatsAppClient":
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
        url: str,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> dict:
        """
        Make a request to the WhatsApp Cloud API.

        Args:
            method: HTTP method (GET, POST)
            url: Full API URL
            data: Request body
            files: Files to upload

        Returns:
            API response data

        Raises:
            WhatsAppAPIError: If the API returns an error
        """
        session = await self._ensure_session()

        for attempt in range(self.config.max_retries):
            try:
                if method.upper() == "GET":
                    async with session.get(url) as response:
                        result = await response.json()
                elif files:
                    # Multipart form data for file uploads
                    form_data = aiohttp.FormData()
                    for field_name, (filename, content, content_type) in files.items():
                        form_data.add_field(
                            field_name,
                            content,
                            filename=filename,
                            content_type=content_type,
                        )
                    # Remove Content-Type header for multipart
                    headers = {"Authorization": f"Bearer {self.config.access_token}"}
                    async with session.post(url, data=form_data, headers=headers) as response:
                        result = await response.json()
                else:
                    async with session.post(url, json=data) as response:
                        result = await response.json()

                # Check for errors
                if "error" in result:
                    error = result["error"]
                    error_code = error.get("code")
                    error_msg = error.get("message", "Unknown error")

                    # Check for rate limiting
                    if error_code in [4, 17, 341]:  # Rate limit codes
                        retry_after = 5
                        logger.warning(f"WhatsApp rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue

                    raise WhatsAppAPIError(
                        f"WhatsApp API error: {error_msg}",
                        error_code=error_code,
                        error_subcode=error.get("error_subcode"),
                        error_type=error.get("type"),
                    )

                return result

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"WhatsApp request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise WhatsAppAPIError(f"Network error: {e}") from e

        raise WhatsAppAPIError("Max retries exceeded")

    # =========================================================================
    # Message Methods
    # =========================================================================

    async def send_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False,
    ) -> WhatsAppMessage:
        """
        Send a text message.

        Args:
            to: Recipient phone number (with country code, e.g., +1234567890)
            text: Message text
            preview_url: Enable URL preview in message

        Returns:
            WhatsAppMessage with message details
        """
        # Normalize phone number (remove + and spaces)
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text,
            },
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list] = None,
    ) -> WhatsAppMessage:
        """
        Send a template message.

        Args:
            to: Recipient phone number
            template_name: Name of the approved template
            language_code: Template language (e.g., "en_US", "es_ES")
            components: Template components (header, body, button variables)

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        template_data = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template_data["components"] = components

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_image(
        self,
        to: str,
        image: Union[str, Path],
        caption: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Send an image message.

        Args:
            to: Recipient phone number
            image: Image URL or media ID
            caption: Optional image caption

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        image_data = {}
        image_str = str(image)

        if image_str.startswith("http"):
            image_data["link"] = image_str
        else:
            # Assume it's a media ID
            image_data["id"] = image_str

        if caption:
            image_data["caption"] = caption

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": image_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_document(
        self,
        to: str,
        document: Union[str, Path],
        filename: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Send a document message.

        Args:
            to: Recipient phone number
            document: Document URL or media ID
            filename: Display filename
            caption: Optional caption

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        doc_data = {}
        doc_str = str(document)

        if doc_str.startswith("http"):
            doc_data["link"] = doc_str
        else:
            doc_data["id"] = doc_str

        if filename:
            doc_data["filename"] = filename
        if caption:
            doc_data["caption"] = caption

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": doc_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_audio(
        self,
        to: str,
        audio: Union[str, Path],
    ) -> WhatsAppMessage:
        """
        Send an audio message.

        Args:
            to: Recipient phone number
            audio: Audio URL or media ID

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        audio_data = {}
        audio_str = str(audio)

        if audio_str.startswith("http"):
            audio_data["link"] = audio_str
        else:
            audio_data["id"] = audio_str

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": audio_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_video(
        self,
        to: str,
        video: Union[str, Path],
        caption: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Send a video message.

        Args:
            to: Recipient phone number
            video: Video URL or media ID
            caption: Optional caption

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        video_data = {}
        video_str = str(video)

        if video_str.startswith("http"):
            video_data["link"] = video_str
        else:
            video_data["id"] = video_str

        if caption:
            video_data["caption"] = caption

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "video",
            "video": video_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_location(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Send a location message.

        Args:
            to: Recipient phone number
            latitude: Location latitude
            longitude: Location longitude
            name: Location name
            address: Location address

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        location_data = {
            "latitude": latitude,
            "longitude": longitude,
        }
        if name:
            location_data["name"] = name
        if address:
            location_data["address"] = address

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "location",
            "location": location_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_contacts(
        self,
        to: str,
        contacts: list[dict],
    ) -> WhatsAppMessage:
        """
        Send contact cards.

        Args:
            to: Recipient phone number
            contacts: List of contact objects

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "contacts",
            "contacts": contacts,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def send_interactive(
        self,
        to: str,
        interactive_type: str,
        body_text: str,
        action: dict,
        header: Optional[dict] = None,
        footer_text: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Send an interactive message (buttons, lists).

        Args:
            to: Recipient phone number
            interactive_type: "button" or "list"
            body_text: Message body
            action: Action object (buttons or sections)
            header: Optional header object
            footer_text: Optional footer text

        Returns:
            WhatsAppMessage with message details
        """
        to = to.replace("+", "").replace(" ", "").replace("-", "")

        interactive_data = {
            "type": interactive_type,
            "body": {"text": body_text},
            "action": action,
        }
        if header:
            interactive_data["header"] = header
        if footer_text:
            interactive_data["footer"] = {"text": footer_text}

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_data,
        }

        result = await self._request("POST", self.config.api_url, data)
        return WhatsAppMessage.from_response(result, to)

    async def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read.

        Args:
            message_id: ID of the message to mark as read

        Returns:
            True if successful
        """
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        await self._request("POST", self.config.api_url, data)
        return True

    # =========================================================================
    # Template Methods
    # =========================================================================

    async def list_templates(
        self,
        limit: int = 100,
    ) -> list[WhatsAppTemplate]:
        """
        List message templates.

        Args:
            limit: Maximum templates to return

        Returns:
            List of WhatsAppTemplate objects
        """
        url = f"{self.config.templates_url}?limit={limit}"
        result = await self._request("GET", url)

        templates = []
        for t in result.get("data", []):
            templates.append(WhatsAppTemplate.from_response(t))

        return templates

    # =========================================================================
    # Media Methods
    # =========================================================================

    async def upload_media(
        self,
        file_path: Path,
        content_type: str,
    ) -> str:
        """
        Upload media to WhatsApp.

        Args:
            file_path: Path to file to upload
            content_type: MIME type of file

        Returns:
            Media ID
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise WhatsAppAPIError(f"File not found: {file_path}")

        content = file_path.read_bytes()

        # Need to add messaging_product to form data
        session = await self._ensure_session()
        form_data = aiohttp.FormData()
        form_data.add_field("messaging_product", "whatsapp")
        form_data.add_field(
            "file",
            content,
            filename=file_path.name,
            content_type=content_type,
        )

        headers = {"Authorization": f"Bearer {self.config.access_token}"}
        async with session.post(self.config.media_url, data=form_data, headers=headers) as response:
            result = await response.json()

        if "error" in result:
            raise WhatsAppAPIError(result["error"].get("message", "Upload failed"))

        return result.get("id", "")

    async def get_media_url(self, media_id: str) -> str:
        """
        Get download URL for media.

        Args:
            media_id: Media ID from webhook

        Returns:
            Download URL
        """
        url = f"{self.config.base_url}/{self.config.api_version}/{media_id}"
        result = await self._request("GET", url)
        return result.get("url", "")


__all__ = [
    "WhatsAppClient",
    "WhatsAppConfig",
    "WhatsAppMessage",
    "WhatsAppTemplate",
    "WhatsAppAPIError",
]
