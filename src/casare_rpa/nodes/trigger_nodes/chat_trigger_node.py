"""
CasareRPA - Chat Trigger Node

Trigger node that fires when a chat message is received.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import (
    BaseTriggerNode,
    trigger_node,
)
from casare_rpa.triggers.base import TriggerType


@trigger_node
@properties(
    PropertyDef(
        "welcome_message",
        PropertyType.STRING,
        default="Hello! How can I help you?",
        label="Welcome Message",
        placeholder="Hello! How can I help you?",
    ),
    PropertyDef(
        "input_placeholder",
        PropertyType.STRING,
        default="Type your message...",
        label="Input Placeholder",
    ),
    PropertyDef(
        "platform",
        PropertyType.CHOICE,
        default="web",
        choices=["web", "slack", "teams", "discord", "telegram"],
        label="Platform",
        tooltip="Chat platform to receive messages from",
    ),
    PropertyDef(
        "channel_id",
        PropertyType.STRING,
        default="",
        label="Channel ID",
        placeholder="C1234567890",
        tooltip="Channel/room ID for platform-specific triggers",
    ),
    PropertyDef(
        "bot_token",
        PropertyType.STRING,
        default="",
        label="Bot Token",
        tooltip="Bot token for platform authentication",
    ),
    PropertyDef(
        "message_pattern",
        PropertyType.STRING,
        default="",
        label="Message Pattern",
        placeholder="^/start.*",
        tooltip="Regex pattern to filter messages",
    ),
    PropertyDef(
        "allow_dm",
        PropertyType.BOOLEAN,
        default=True,
        label="Allow Direct Messages",
    ),
    PropertyDef(
        "allow_mentions",
        PropertyType.BOOLEAN,
        default=True,
        label="Respond to Mentions",
    ),
)
class ChatTriggerNode(BaseTriggerNode):
    """
    Chat trigger node that fires when a chat message is received.

    Outputs:
    - message: The message content
    - user_id: ID of the user who sent the message
    - user_name: Name of the user
    - channel_id: ID of the channel/room
    - platform: Chat platform
    - timestamp: When the message was sent
    - reply_to: Message ID this is replying to (if any)
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Chat"
    trigger_description = "Trigger on chat message"
    trigger_icon = "chat"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Chat Trigger"
        self.node_type = "ChatTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define chat-specific output ports."""
        self.add_output_port("message", DataType.STRING, "Message")
        self.add_output_port("user_id", DataType.STRING, "User ID")
        self.add_output_port("user_name", DataType.STRING, "User Name")
        self.add_output_port("channel_id", DataType.STRING, "Channel ID")
        self.add_output_port("platform", DataType.STRING, "Platform")
        self.add_output_port("timestamp", DataType.STRING, "Timestamp")
        self.add_output_port("reply_to", DataType.STRING, "Reply To")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.CHAT

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get chat-specific configuration."""
        return {
            "welcome_message": self.config.get(
                "welcome_message", "Hello! How can I help you?"
            ),
            "input_placeholder": self.config.get(
                "input_placeholder", "Type your message..."
            ),
            "platform": self.config.get("platform", "web"),
            "channel_id": self.config.get("channel_id", ""),
            "bot_token": self.config.get("bot_token", ""),
            "message_pattern": self.config.get("message_pattern", ""),
            "allow_dm": self.config.get("allow_dm", True),
            "allow_mentions": self.config.get("allow_mentions", True),
        }
