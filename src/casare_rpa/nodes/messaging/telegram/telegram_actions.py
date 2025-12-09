"""
CasareRPA - Telegram Action Nodes (P2)

Nodes for editing, deleting, and managing Telegram messages.
"""

from __future__ import annotations

from typing import Any
import json

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.telegram_client import TelegramClient
from casare_rpa.nodes.messaging.telegram.telegram_base import TelegramBaseNode

# Import reusable definitions from telegram_send
from casare_rpa.nodes.messaging.telegram.telegram_send import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    TELEGRAM_PARSE_MODE,
    TELEGRAM_DISABLE_NOTIFICATION,
)


@node_schema(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "message_id",
        PropertyType.INTEGER,
        default=0,
        required=True,
        label="Message ID",
        placeholder="12345",
        tooltip="ID of the message to edit",
    ),
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        required=True,
        label="New Text",
        placeholder="Updated message content...",
        tooltip="New message text content",
    ),
    TELEGRAM_PARSE_MODE,
)
@executable_node
class TelegramEditMessageNode(TelegramBaseNode):
    """
    Edit a sent text message via Telegram.

    Inputs:
        - chat_id: Target chat ID
        - message_id: ID of message to edit
        - text: New message text
        - parse_mode: Optional "Markdown", "MarkdownV2", or "HTML"

    Outputs:
        - message_id: Edited message ID
        - chat_id: Target chat ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: message_id, text, parse_mode -> none

    NODE_TYPE = "telegram_edit_message"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Edit Message"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Edit Message", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Edit-specific ports
        self.add_input_port(
            "message_id", PortType.INPUT, DataType.INTEGER, required=True
        )
        self.add_input_port("text", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "parse_mode", PortType.INPUT, DataType.STRING, required=False
        )

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Edit a message."""
        chat_id = self._get_chat_id(context)

        # Get message ID
        message_id = self.get_parameter("message_id")
        if hasattr(context, "resolve_value"):
            message_id = context.resolve_value(message_id)

        try:
            message_id = int(message_id)
        except (TypeError, ValueError):
            self._set_error_outputs("Invalid message_id")
            return {"success": False, "error": "Invalid message_id", "next_nodes": []}

        # Get new text
        text = self.get_parameter("text")
        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self._set_error_outputs("Text is required")
            return {"success": False, "error": "Text is required", "next_nodes": []}

        # Get optional params
        parse_mode = self.get_parameter("parse_mode")
        if parse_mode and hasattr(context, "resolve_value"):
            parse_mode = context.resolve_value(parse_mode)

        logger.debug(f"Editing Telegram message {message_id} in {chat_id}")

        # Edit message
        result = await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=parse_mode,
        )

        self._set_success_outputs(result.message_id, result.chat_id)

        logger.info(f"Telegram message edited: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "chat_id": result.chat_id,
            "next_nodes": [],
        }


@node_schema(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "message_id",
        PropertyType.INTEGER,
        default=0,
        required=True,
        label="Message ID",
        placeholder="12345",
        tooltip="ID of the message to delete",
    ),
)
@executable_node
class TelegramDeleteMessageNode(TelegramBaseNode):
    """
    Delete a message via Telegram.

    Inputs:
        - chat_id: Target chat ID
        - message_id: ID of message to delete

    Outputs:
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: message_id -> success, error

    NODE_TYPE = "telegram_delete_message"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Delete Message"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Delete Message", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()

        # Delete-specific ports
        self.add_input_port(
            "message_id", PortType.INPUT, DataType.INTEGER, required=True
        )

        # Output ports
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Delete a message."""
        chat_id = self._get_chat_id(context)

        # Get message ID
        message_id = self.get_parameter("message_id")
        if hasattr(context, "resolve_value"):
            message_id = context.resolve_value(message_id)

        try:
            message_id = int(message_id)
        except (TypeError, ValueError):
            self.set_output_value("success", False)
            self.set_output_value("error", "Invalid message_id")
            return {"success": False, "error": "Invalid message_id", "next_nodes": []}

        logger.debug(f"Deleting Telegram message {message_id} in {chat_id}")

        # Delete message
        await client.delete_message(chat_id=chat_id, message_id=message_id)

        self.set_output_value("success", True)
        self.set_output_value("error", "")

        logger.info(f"Telegram message deleted: {message_id}")

        return {
            "success": True,
            "message_id": message_id,
            "next_nodes": [],
        }


@node_schema(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    PropertyDef(
        "media_json",
        PropertyType.JSON,
        default=[],
        required=True,
        label="Media (JSON)",
        placeholder='[{"type":"photo","media":"url"}]',
        tooltip="JSON array of InputMediaPhoto/InputMediaVideo objects (2-10 items)",
    ),
    TELEGRAM_DISABLE_NOTIFICATION,
)
@executable_node
class TelegramSendMediaGroupNode(TelegramBaseNode):
    """
    Send a media group (album) via Telegram.

    Inputs:
        - chat_id: Target chat ID
        - media_json: JSON array of media objects (InputMediaPhoto/InputMediaVideo)

    Outputs:
        - message_ids: Comma-separated IDs of sent messages
        - count: Number of messages in the group
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: media_json, disable_notification -> message_ids, count, success, error

    NODE_TYPE = "telegram_send_media_group"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Send Media Group"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Send Media Group", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()

        # Media group-specific ports
        self.add_input_port(
            "media_json", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "disable_notification", PortType.INPUT, DataType.BOOLEAN, required=False
        )

        # Output ports
        self.add_output_port("message_ids", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Send a media group."""
        chat_id = self._get_chat_id(context)

        # Get media JSON
        media_json = self.get_parameter("media_json")
        if hasattr(context, "resolve_value"):
            media_json = context.resolve_value(media_json)

        if not media_json:
            self.set_output_value("success", False)
            self.set_output_value("error", "media_json is required")
            return {
                "success": False,
                "error": "media_json is required",
                "next_nodes": [],
            }

        try:
            media = json.loads(media_json)
        except json.JSONDecodeError as e:
            self.set_output_value("success", False)
            self.set_output_value("error", f"Invalid media JSON: {e}")
            return {
                "success": False,
                "error": f"Invalid media JSON: {e}",
                "next_nodes": [],
            }

        if not isinstance(media, list) or len(media) < 2:
            self.set_output_value("success", False)
            self.set_output_value("error", "media_json must be array with 2-10 items")
            return {
                "success": False,
                "error": "media_json must be array with 2-10 items",
                "next_nodes": [],
            }

        disable_notification = self.get_parameter("disable_notification") or False

        logger.debug(f"Sending Telegram media group to {chat_id}")

        # Send media group
        results = await client.send_media_group(
            chat_id=chat_id,
            media=media,
            disable_notification=disable_notification,
        )

        message_ids = ",".join(str(r.message_id) for r in results)

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("message_ids", message_ids)
        self.set_output_value("count", len(results))

        logger.info(f"Telegram media group sent: {message_ids}")

        return {
            "success": True,
            "message_ids": message_ids,
            "count": len(results),
            "next_nodes": [],
        }


@node_schema(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    PropertyDef(
        "callback_query_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Callback Query ID",
        placeholder="From trigger payload",
        tooltip="ID of the callback query to answer",
    ),
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        label="Response Text",
        placeholder="Notification text...",
        tooltip="Optional notification text to show user",
    ),
    PropertyDef(
        "show_alert",
        PropertyType.BOOLEAN,
        default=False,
        label="Show Alert",
        tooltip="Show as alert popup instead of toast notification",
    ),
    PropertyDef(
        "url",
        PropertyType.STRING,
        default="",
        label="URL",
        placeholder="https://example.com",
        tooltip="URL to open (for game bots)",
        tab="advanced",
    ),
)
@executable_node
class TelegramAnswerCallbackNode(TelegramBaseNode):
    """
    Answer a callback query from an inline keyboard.

    Inputs:
        - callback_query_id: ID of callback query to answer
        - text: Optional text to show as notification
        - show_alert: Show as alert instead of toast
        - url: URL to open (for games)

    Outputs:
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: bot_token, credential_name, callback_query_id, text, show_alert, url -> success, error

    NODE_TYPE = "telegram_answer_callback"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Answer Callback"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Answer Callback", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Callback-specific input ports (no common ports needed)
        self.add_input_port(
            "bot_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "callback_query_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("text", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "show_alert", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port("url", PortType.INPUT, DataType.STRING, required=False)

        # Output ports
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Answer a callback query."""
        # Get callback query ID
        callback_query_id = self.get_parameter("callback_query_id")
        if hasattr(context, "resolve_value"):
            callback_query_id = context.resolve_value(callback_query_id)

        if not callback_query_id:
            self.set_output_value("success", False)
            self.set_output_value("error", "callback_query_id is required")
            return {
                "success": False,
                "error": "callback_query_id is required",
                "next_nodes": [],
            }

        # Get optional params
        text = self.get_parameter("text")
        if text and hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        show_alert = self.get_parameter("show_alert") or False

        url = self.get_parameter("url")
        if url and hasattr(context, "resolve_value"):
            url = context.resolve_value(url)

        logger.debug(f"Answering Telegram callback: {callback_query_id}")

        # Answer callback
        await client.answer_callback_query(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            url=url,
        )

        self.set_output_value("success", True)
        self.set_output_value("error", "")

        logger.info(f"Telegram callback answered: {callback_query_id}")

        return {
            "success": True,
            "callback_query_id": callback_query_id,
            "next_nodes": [],
        }


@node_schema(
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    PropertyDef(
        "offset",
        PropertyType.INTEGER,
        default=0,
        label="Offset",
        placeholder="0",
        tooltip="Starting update ID (0 for first available)",
    ),
    PropertyDef(
        "limit",
        PropertyType.INTEGER,
        default=100,
        label="Limit",
        tooltip="Max updates to retrieve (1-100)",
        min_value=1,
        max_value=100,
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        label="Timeout (seconds)",
        tooltip="Long polling timeout in seconds",
        min_value=0,
        max_value=120,
    ),
)
@executable_node
class TelegramGetUpdatesNode(TelegramBaseNode):
    """
    Get updates via Telegram's getUpdates API.

    Useful for manual polling or debugging.

    Inputs:
        - offset: Starting update ID
        - limit: Max updates to retrieve (1-100)
        - timeout: Long polling timeout

    Outputs:
        - updates_json: JSON array of updates
        - count: Number of updates retrieved
        - last_update_id: ID of last update
        - success: Boolean
        - error: Error message if failed
    """

    # @category: integration
    # @requires: none
    # @ports: bot_token, credential_name, offset, limit, timeout -> updates_json, count, last_update_id, success, error

    NODE_TYPE = "telegram_get_updates"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "Telegram: Get Updates"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Telegram Get Updates", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Input ports (no chat_id needed)
        self.add_input_port(
            "bot_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("offset", PortType.INPUT, DataType.INTEGER, required=False)
        self.add_input_port("limit", PortType.INPUT, DataType.INTEGER, required=False)
        self.add_input_port("timeout", PortType.INPUT, DataType.INTEGER, required=False)

        # Output ports
        self.add_output_port("updates_json", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("last_update_id", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """Get updates."""
        # Get optional params
        offset = self.get_parameter("offset")
        if offset and hasattr(context, "resolve_value"):
            offset = context.resolve_value(offset)
            try:
                offset = int(offset)
            except (TypeError, ValueError):
                offset = None

        limit = self.get_parameter("limit") or 100
        if hasattr(context, "resolve_value"):
            limit = context.resolve_value(limit)
        try:
            limit = min(int(limit), 100)
        except (TypeError, ValueError):
            limit = 100

        timeout = self.get_parameter("timeout") or 30
        if hasattr(context, "resolve_value"):
            timeout = context.resolve_value(timeout)
        try:
            timeout = int(timeout)
        except (TypeError, ValueError):
            timeout = 30

        logger.debug(f"Getting Telegram updates (offset={offset}, limit={limit})")

        # Get updates
        updates = await client.get_updates(
            offset=offset,
            limit=limit,
            timeout=timeout,
        )

        updates_json = json.dumps(updates)
        count = len(updates)
        last_update_id = updates[-1].get("update_id", 0) if updates else 0

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("updates_json", updates_json)
        self.set_output_value("count", count)
        self.set_output_value("last_update_id", last_update_id)

        logger.info(f"Got {count} Telegram updates")

        return {
            "success": True,
            "updates_json": updates_json,
            "count": count,
            "last_update_id": last_update_id,
            "next_nodes": [],
        }


__all__ = [
    "TelegramEditMessageNode",
    "TelegramDeleteMessageNode",
    "TelegramSendMediaGroupNode",
    "TelegramAnswerCallbackNode",
    "TelegramGetUpdatesNode",
]
