"""
CasareRPA - Telegram Send Nodes

Nodes for sending messages, photos, documents, and locations via Telegram Bot API.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.telegram_client import TelegramClient
from casare_rpa.nodes.messaging.telegram.telegram_base import TelegramBaseNode


# ============================================================================
# Reusable Property Definitions for Telegram Nodes
# ============================================================================

# Connection properties (shared across all Telegram nodes)
TELEGRAM_BOT_TOKEN = PropertyDef(
    "bot_token",
    PropertyType.STRING,
    default="",
    label="Bot Token",
    placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    tooltip="Telegram Bot token from @BotFather",
    tab="connection",
)

TELEGRAM_CREDENTIAL_NAME = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="telegram",
    tooltip="Name of stored Telegram credential (alternative to bot token)",
    tab="connection",
)

TELEGRAM_CHAT_ID = PropertyDef(
    "chat_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="Chat ID",
    placeholder="123456789 or @username",
    tooltip="Target chat ID or @username",
)

TELEGRAM_PARSE_MODE = PropertyDef(
    "parse_mode",
    PropertyType.CHOICE,
    default="",
    choices=["", "Markdown", "MarkdownV2", "HTML"],
    label="Parse Mode",
    tooltip="Text formatting mode",
)

TELEGRAM_DISABLE_NOTIFICATION = PropertyDef(
    "disable_notification",
    PropertyType.BOOLEAN,
    default=False,
    label="Silent",
    tooltip="Send message silently (no notification sound)",
)


@properties(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        required=True,
        label="Message Text",
        placeholder="Hello from CasareRPA!",
        tooltip="Message content (1-4096 characters)",
    ),
    TELEGRAM_PARSE_MODE,
    TELEGRAM_DISABLE_NOTIFICATION,
    PropertyDef(
        "reply_to_message_id",
        PropertyType.INTEGER,
        default=0,
        label="Reply To",
        tooltip="Message ID to reply to (0 for no reply)",
    ),
)
@node(category="messaging")
class TelegramSendMessageNode(TelegramBaseNode):
    """
    Send a text message via Telegram.

    Inputs:
        - chat_id: Target chat ID or @username
        - text: Message text (1-4096 characters)
        - parse_mode: Optional "Markdown", "MarkdownV2", or "HTML"
        - disable_notification: Send silently (default: False)

    Outputs:
        - message_id: Sent message ID
        - chat_id: Target chat ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: text, parse_mode, disable_notification, reply_to_message_id -> text

    NODE_TYPE = "telegram_send_message"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Send Message"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Send Message", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Common ports
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Message-specific ports
        self.add_input_port("text", DataType.STRING, required=True)
        self.add_input_port("parse_mode", DataType.STRING, required=False)
        self.add_input_port("disable_notification", DataType.BOOLEAN, required=False)
        self.add_input_port("reply_to_message_id", DataType.INTEGER, required=False)

        # Additional output
        self.add_output_port("text", DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Send a text message."""
        chat_id = self._get_chat_id(context)

        # Get text
        text = self.get_parameter("text")

        if not text:
            self._set_error_outputs("Text message is required")
            return {
                "success": False,
                "error": "Text message is required",
                "next_nodes": [],
            }

        # Get optional params
        parse_mode = self.get_parameter("parse_mode")

        disable_notification = self.get_parameter("disable_notification") or False
        reply_to = self.get_parameter("reply_to_message_id")

        logger.debug(f"Sending Telegram message to {chat_id}")

        # Send message
        result = await client.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.chat_id)
        self.set_output_value("text", text)

        logger.info(f"Telegram message sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "chat_id": result.chat_id,
            "next_nodes": [],
        }


@properties(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "photo",
        PropertyType.STRING,
        default="",
        required=True,
        label="Photo",
        placeholder="https://example.com/photo.jpg or file path",
        tooltip="Photo URL, file path, or Telegram file_id",
    ),
    PropertyDef(
        "caption",
        PropertyType.TEXT,
        default="",
        label="Caption",
        placeholder="Photo caption...",
        tooltip="Optional photo caption (0-1024 characters)",
    ),
    TELEGRAM_PARSE_MODE,
    TELEGRAM_DISABLE_NOTIFICATION,
)
@node(category="messaging")
class TelegramSendPhotoNode(TelegramBaseNode):
    """
    Send a photo via Telegram.

    Inputs:
        - chat_id: Target chat ID or @username
        - photo: File path, URL, or file_id
        - caption: Optional caption (0-1024 characters)
        - parse_mode: Optional "Markdown", "MarkdownV2", or "HTML"

    Outputs:
        - message_id: Sent message ID
        - chat_id: Target chat ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: photo, caption, parse_mode, disable_notification -> photo_path

    NODE_TYPE = "telegram_send_photo"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Send Photo"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Send Photo", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Photo-specific ports
        self.add_input_port("photo", DataType.STRING, required=True)
        self.add_input_port("caption", DataType.STRING, required=False)
        self.add_input_port("parse_mode", DataType.STRING, required=False)
        self.add_input_port("disable_notification", DataType.BOOLEAN, required=False)

        # Additional output
        self.add_output_port("photo_path", DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Send a photo."""
        chat_id = self._get_chat_id(context)

        # Get photo
        photo = self.get_parameter("photo")

        if not photo:
            self._set_error_outputs("Photo is required")
            return {"success": False, "error": "Photo is required", "next_nodes": []}

        # Get optional params
        caption = self.get_parameter("caption")

        parse_mode = self.get_parameter("parse_mode")

        disable_notification = self.get_parameter("disable_notification") or False

        logger.debug(f"Sending Telegram photo to {chat_id}")

        # Send photo
        result = await client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.chat_id)
        self.set_output_value("photo_path", str(photo))

        logger.info(f"Telegram photo sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "chat_id": result.chat_id,
            "next_nodes": [],
        }


@properties(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "document",
        PropertyType.STRING,
        default="",
        required=True,
        label="Document",
        placeholder="https://example.com/file.pdf or file path",
        tooltip="Document URL, file path, or Telegram file_id",
    ),
    PropertyDef(
        "filename",
        PropertyType.STRING,
        default="",
        label="Filename",
        placeholder="report.pdf",
        tooltip="Custom display filename",
    ),
    PropertyDef(
        "caption",
        PropertyType.TEXT,
        default="",
        label="Caption",
        placeholder="Document description...",
        tooltip="Optional document caption",
    ),
    TELEGRAM_PARSE_MODE,
    TELEGRAM_DISABLE_NOTIFICATION,
)
@node(category="messaging")
class TelegramSendDocumentNode(TelegramBaseNode):
    """
    Send a document/file via Telegram.

    Inputs:
        - chat_id: Target chat ID or @username
        - document: File path, URL, or file_id
        - filename: Optional custom filename
        - caption: Optional caption

    Outputs:
        - message_id: Sent message ID
        - chat_id: Target chat ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: document, filename, caption, parse_mode, disable_notification -> document_path

    NODE_TYPE = "telegram_send_document"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Send Document"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Send Document", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Document-specific ports
        self.add_input_port("document", DataType.STRING, required=True)
        self.add_input_port("filename", DataType.STRING, required=False)
        self.add_input_port("caption", DataType.STRING, required=False)
        self.add_input_port("parse_mode", DataType.STRING, required=False)
        self.add_input_port("disable_notification", DataType.BOOLEAN, required=False)

        # Additional output
        self.add_output_port("document_path", DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Send a document."""
        chat_id = self._get_chat_id(context)

        # Get document
        document = self.get_parameter("document")

        if not document:
            self._set_error_outputs("Document is required")
            return {"success": False, "error": "Document is required", "next_nodes": []}

        # Get optional params
        filename = self.get_parameter("filename")

        caption = self.get_parameter("caption")

        parse_mode = self.get_parameter("parse_mode")

        disable_notification = self.get_parameter("disable_notification") or False

        logger.debug(f"Sending Telegram document to {chat_id}")

        # Send document
        result = await client.send_document(
            chat_id=chat_id,
            document=document,
            filename=filename,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.chat_id)
        self.set_output_value("document_path", str(document))

        logger.info(f"Telegram document sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "chat_id": result.chat_id,
            "next_nodes": [],
        }


@properties(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "latitude",
        PropertyType.FLOAT,
        default=0.0,
        required=True,
        label="Latitude",
        placeholder="37.7749",
        tooltip="Location latitude (-90 to 90)",
        min_value=-90.0,
        max_value=90.0,
    ),
    PropertyDef(
        "longitude",
        PropertyType.FLOAT,
        default=0.0,
        required=True,
        label="Longitude",
        placeholder="-122.4194",
        tooltip="Location longitude (-180 to 180)",
        min_value=-180.0,
        max_value=180.0,
    ),
    TELEGRAM_DISABLE_NOTIFICATION,
)
@node(category="messaging")
class TelegramSendLocationNode(TelegramBaseNode):
    """
    Send a location via Telegram.

    Inputs:
        - chat_id: Target chat ID or @username
        - latitude: Latitude (-90 to 90)
        - longitude: Longitude (-180 to 180)

    Outputs:
        - message_id: Sent message ID
        - chat_id: Target chat ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: latitude, longitude, disable_notification -> latitude, longitude

    NODE_TYPE = "telegram_send_location"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Send Location"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Send Location", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Location-specific ports
        self.add_input_port("latitude", DataType.FLOAT, required=True)
        self.add_input_port("longitude", DataType.FLOAT, required=True)
        self.add_input_port("disable_notification", DataType.BOOLEAN, required=False)

        # Additional outputs
        self.add_output_port("latitude", DataType.FLOAT)
        self.add_output_port("longitude", DataType.FLOAT)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Send a location."""
        chat_id = self._get_chat_id(context)

        # Get coordinates
        latitude = self.get_parameter("latitude")
        longitude = self.get_parameter("longitude")

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            self._set_error_outputs("Invalid latitude or longitude")
            return {
                "success": False,
                "error": "Invalid latitude or longitude",
                "next_nodes": [],
            }

        # Validate range
        if not (-90 <= latitude <= 90):
            self._set_error_outputs("Latitude must be between -90 and 90")
            return {
                "success": False,
                "error": "Latitude must be between -90 and 90",
                "next_nodes": [],
            }

        if not (-180 <= longitude <= 180):
            self._set_error_outputs("Longitude must be between -180 and 180")
            return {
                "success": False,
                "error": "Longitude must be between -180 and 180",
                "next_nodes": [],
            }

        disable_notification = self.get_parameter("disable_notification") or False

        logger.debug(f"Sending Telegram location to {chat_id}")

        # Send location
        result = await client.send_location(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            disable_notification=disable_notification,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.chat_id)
        self.set_output_value("latitude", latitude)
        self.set_output_value("longitude", longitude)

        logger.info(f"Telegram location sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "chat_id": result.chat_id,
            "next_nodes": [],
        }


__all__ = [
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
]
