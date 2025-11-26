"""
CasareRPA - Chat Message Trigger

Trigger that fires when a chat message is received.
Provides a generic webhook interface for chat platforms (Slack, Teams, Discord, etc.).
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from ..base import BaseTrigger, BaseTriggerConfig, TriggerStatus, TriggerType
from ..registry import register_trigger


@register_trigger
class ChatTrigger(BaseTrigger):
    """
    Trigger that responds to chat messages.

    This trigger provides a webhook endpoint for receiving messages
    from chat platforms. It's platform-agnostic and can be configured
    to work with Slack, Microsoft Teams, Discord, or custom chat systems.

    Configuration options:
        platform: Chat platform hint (slack, teams, discord, custom)
        message_pattern: Regex pattern to match messages
        channel_filter: List of channels/rooms to monitor
        user_filter: List of users to monitor (empty = all)
        bot_filter: Ignore bot messages (default: true)
        mention_required: Only trigger when bot is mentioned

    Payload provided to workflow:
        message_text: The message content
        sender_id: ID of the message sender
        sender_name: Name of the sender
        channel_id: ID of the channel/room
        channel_name: Name of the channel
        timestamp: When the message was sent
        platform: The chat platform
        raw_payload: Full original payload for platform-specific data
    """

    trigger_type = TriggerType.CHAT
    display_name = "Chat Message"
    description = "Trigger when a chat message is received"
    icon = "message-square"
    category = "External"

    async def start(self) -> bool:
        """
        Start the chat message trigger.

        The webhook endpoint is handled by TriggerManager's HTTP server.
        """
        self._status = TriggerStatus.ACTIVE
        platform = self.config.config.get('platform', 'custom')
        logger.info(
            f"Chat trigger started: {self.config.name} (platform: {platform})"
        )
        return True

    async def stop(self) -> bool:
        """Stop the chat message trigger."""
        self._status = TriggerStatus.INACTIVE
        logger.info(f"Chat trigger stopped: {self.config.name}")
        return True

    async def process_message(
        self,
        raw_payload: Dict[str, Any],
        platform: Optional[str] = None
    ) -> bool:
        """
        Process a chat message.

        Called by TriggerManager when a chat webhook is received.

        Args:
            raw_payload: The raw webhook payload from the chat platform
            platform: The chat platform (overrides config if provided)

        Returns:
            True if message was processed, False if filtered out
        """
        config = self.config.config
        platform = platform or config.get('platform', 'custom')

        # Extract message data based on platform
        message_data = self._extract_message_data(raw_payload, platform)

        if not message_data:
            logger.debug("Could not extract message data from payload")
            return False

        # Apply filters
        if not self._should_process_message(message_data):
            return False

        # Build payload
        payload = {
            "message_text": message_data.get('text', ''),
            "sender_id": message_data.get('sender_id', ''),
            "sender_name": message_data.get('sender_name', ''),
            "channel_id": message_data.get('channel_id', ''),
            "channel_name": message_data.get('channel_name', ''),
            "timestamp": message_data.get('timestamp', datetime.utcnow().isoformat()),
            "platform": platform,
            "is_mention": message_data.get('is_mention', False),
            "raw_payload": raw_payload,
        }

        metadata = {
            "source": "chat",
            "platform": platform,
        }

        return await self.emit(payload, metadata)

    def _extract_message_data(
        self,
        payload: Dict[str, Any],
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """Extract standardized message data from platform-specific payload."""

        if platform == 'slack':
            # Slack event payload structure
            event = payload.get('event', payload)
            return {
                'text': event.get('text', ''),
                'sender_id': event.get('user', ''),
                'sender_name': event.get('username', event.get('user', '')),
                'channel_id': event.get('channel', ''),
                'channel_name': event.get('channel_name', ''),
                'timestamp': event.get('ts', ''),
                'is_bot': event.get('bot_id') is not None,
                'is_mention': '<@' in event.get('text', ''),
            }

        elif platform == 'teams':
            # Microsoft Teams payload structure
            return {
                'text': payload.get('text', ''),
                'sender_id': payload.get('from', {}).get('id', ''),
                'sender_name': payload.get('from', {}).get('name', ''),
                'channel_id': payload.get('channelId', ''),
                'channel_name': payload.get('channelData', {}).get('channel', {}).get('name', ''),
                'timestamp': payload.get('timestamp', ''),
                'is_bot': payload.get('from', {}).get('isBot', False),
                'is_mention': payload.get('mentioned', []) != [],
            }

        elif platform == 'discord':
            # Discord webhook payload structure
            return {
                'text': payload.get('content', ''),
                'sender_id': payload.get('author', {}).get('id', ''),
                'sender_name': payload.get('author', {}).get('username', ''),
                'channel_id': payload.get('channel_id', ''),
                'channel_name': '',  # Discord doesn't include channel name in webhook
                'timestamp': payload.get('timestamp', ''),
                'is_bot': payload.get('author', {}).get('bot', False),
                'is_mention': payload.get('mentions', []) != [] or payload.get('mention_everyone', False),
            }

        else:
            # Custom/generic format
            return {
                'text': payload.get('message', payload.get('text', payload.get('content', ''))),
                'sender_id': payload.get('sender_id', payload.get('user_id', payload.get('from', ''))),
                'sender_name': payload.get('sender_name', payload.get('username', '')),
                'channel_id': payload.get('channel_id', payload.get('room_id', '')),
                'channel_name': payload.get('channel_name', payload.get('room_name', '')),
                'timestamp': payload.get('timestamp', datetime.utcnow().isoformat()),
                'is_bot': payload.get('is_bot', False),
                'is_mention': payload.get('is_mention', False),
            }

    def _should_process_message(self, message_data: Dict[str, Any]) -> bool:
        """Check if message should be processed based on filters."""
        config = self.config.config

        # Bot filter
        if config.get('bot_filter', True) and message_data.get('is_bot', False):
            return False

        # Mention required
        if config.get('mention_required', False) and not message_data.get('is_mention', False):
            return False

        # Channel filter
        channel_filter = config.get('channel_filter', [])
        if channel_filter:
            channel_id = message_data.get('channel_id', '')
            channel_name = message_data.get('channel_name', '')
            if channel_id not in channel_filter and channel_name not in channel_filter:
                return False

        # User filter
        user_filter = config.get('user_filter', [])
        if user_filter:
            sender_id = message_data.get('sender_id', '')
            sender_name = message_data.get('sender_name', '')
            if sender_id not in user_filter and sender_name not in user_filter:
                return False

        # Message pattern
        message_pattern = config.get('message_pattern', '')
        if message_pattern:
            text = message_data.get('text', '')
            if not re.search(message_pattern, text, re.IGNORECASE):
                return False

        return True

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate chat trigger configuration."""
        config = self.config.config

        platform = config.get('platform', 'custom')
        valid_platforms = ['slack', 'teams', 'discord', 'custom']
        if platform not in valid_platforms:
            return False, f"Invalid platform. Must be one of: {valid_platforms}"

        # Validate message pattern if provided
        message_pattern = config.get('message_pattern', '')
        if message_pattern:
            try:
                re.compile(message_pattern)
            except re.error as e:
                return False, f"Invalid message_pattern regex: {e}"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for chat trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {"type": "integer", "minimum": 0, "maximum": 3, "default": 1},
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "platform": {
                    "type": "string",
                    "enum": ["slack", "teams", "discord", "custom"],
                    "default": "custom",
                    "description": "Chat platform",
                },
                "message_pattern": {
                    "type": "string",
                    "description": "Regex pattern to match messages",
                },
                "channel_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Channels/rooms to monitor (empty = all)",
                },
                "user_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Users to monitor (empty = all)",
                },
                "bot_filter": {
                    "type": "boolean",
                    "default": True,
                    "description": "Ignore messages from bots",
                },
                "mention_required": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only trigger when bot is mentioned",
                },
            },
            "required": ["name"],
        }
