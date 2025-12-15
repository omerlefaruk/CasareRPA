"""
CasareRPA - Telegram Trigger Node

Trigger node that listens for incoming Telegram messages.
Workflow starts when a message matching the filters is received.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    # Connection settings
    PropertyDef(
        "bot_token",
        PropertyType.STRING,
        default="",
        label="Bot Token",
        placeholder="123456:ABC-DEF...",
        tooltip="Telegram bot token from @BotFather",
        tab="connection",
    ),
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="",
        label="Credential Name",
        placeholder="telegram",
        tooltip="Name of stored credential (alternative to bot token)",
        tab="connection",
    ),
    # Mode settings
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="auto",
        choices=["auto", "webhook", "polling"],
        label="Mode",
        tooltip="How to receive updates: webhook (public URL required), polling, or auto",
    ),
    PropertyDef(
        "webhook_url",
        PropertyType.STRING,
        default="",
        label="Webhook URL",
        placeholder="https://your-domain.com/webhook",
        tooltip="Public URL for webhook mode (auto-detected from CASARE_WEBHOOK_URL if empty)",
    ),
    PropertyDef(
        "polling_interval",
        PropertyType.INTEGER,
        default=2,
        label="Polling Interval (sec)",
        tooltip="Seconds between polls in polling mode",
        tab="advanced",
    ),
    # Filters
    PropertyDef(
        "filter_chat_ids",
        PropertyType.STRING,
        default="",
        label="Filter Chat IDs",
        placeholder="123456789,-987654321",
        tooltip="Comma-separated chat IDs to allow (empty = all)",
    ),
    PropertyDef(
        "filter_user_ids",
        PropertyType.STRING,
        default="",
        label="Filter User IDs",
        placeholder="111222333,444555666",
        tooltip="Comma-separated user IDs to allow (empty = all)",
    ),
    PropertyDef(
        "commands_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Commands Only",
        tooltip="Only trigger on bot commands (e.g., /start, /help)",
    ),
    PropertyDef(
        "filter_commands",
        PropertyType.STRING,
        default="",
        label="Filter Commands",
        placeholder="start,help,run",
        tooltip="Comma-separated commands to trigger on (empty = all commands)",
    ),
    # Update types
    PropertyDef(
        "allowed_updates",
        PropertyType.STRING,
        default="message",
        label="Allowed Update Types",
        placeholder="message,callback_query,inline_query",
        tooltip="Comma-separated update types to receive",
        tab="advanced",
    ),
)
@node(category="triggers", exec_inputs=[])
class TelegramTriggerNode(BaseTriggerNode):
    """
    Telegram trigger node that listens for incoming messages.

    Outputs:
    - message_id: ID of the received message
    - chat_id: ID of the chat
    - user_id: ID of the user who sent the message
    - username: Username of the sender
    - first_name: First name of the sender
    - text: Message text content
    - is_command: Whether message is a bot command
    - command: Command name if is_command (without /)
    - command_args: Command arguments if is_command
    - message_type: Type of message (text, photo, document, etc.)
    - raw_update: Full update object from Telegram
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Telegram"
    trigger_description = "Trigger workflow when Telegram message is received"
    trigger_icon = "telegram"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Telegram Trigger"
        self.node_type = "TelegramTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define Telegram-specific output ports."""
        self.add_output_port("message_id", DataType.INTEGER, "Message ID")
        self.add_output_port("chat_id", DataType.INTEGER, "Chat ID")
        self.add_output_port("user_id", DataType.INTEGER, "User ID")
        self.add_output_port("username", DataType.STRING, "Username")
        self.add_output_port("first_name", DataType.STRING, "First Name")
        self.add_output_port("text", DataType.STRING, "Message Text")
        self.add_output_port("is_command", DataType.BOOLEAN, "Is Command")
        self.add_output_port("command", DataType.STRING, "Command Name")
        self.add_output_port("command_args", DataType.STRING, "Command Args")
        self.add_output_port("message_type", DataType.STRING, "Message Type")
        self.add_output_port("raw_update", DataType.DICT, "Raw Update")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.TELEGRAM

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get Telegram-specific configuration."""
        # Parse comma-separated lists
        filter_chat_ids_str = self.config.get("filter_chat_ids", "")
        filter_chat_ids = [
            int(cid.strip())
            for cid in filter_chat_ids_str.split(",")
            if cid.strip() and cid.strip().lstrip("-").isdigit()
        ]

        filter_user_ids_str = self.config.get("filter_user_ids", "")
        filter_user_ids = [
            int(uid.strip())
            for uid in filter_user_ids_str.split(",")
            if uid.strip() and uid.strip().isdigit()
        ]

        filter_commands_str = self.config.get("filter_commands", "")
        filter_commands = [
            cmd.strip().lstrip("/")
            for cmd in filter_commands_str.split(",")
            if cmd.strip()
        ]

        allowed_updates_str = self.config.get("allowed_updates", "message")
        allowed_updates = [
            u.strip() for u in allowed_updates_str.split(",") if u.strip()
        ]

        return {
            "bot_token": self.config.get("bot_token", ""),
            "credential_name": self.config.get("credential_name", ""),
            "mode": self.config.get("mode", "auto"),
            "webhook_url": self.config.get("webhook_url", ""),
            "polling_interval": self.config.get("polling_interval", 2),
            "filter_chat_ids": filter_chat_ids,
            "filter_user_ids": filter_user_ids,
            "commands_only": self.config.get("commands_only", False),
            "filter_commands": filter_commands,
            "allowed_updates": allowed_updates,
        }
