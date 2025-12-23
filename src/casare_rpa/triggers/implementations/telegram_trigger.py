"""
CasareRPA - Telegram Trigger

Trigger that fires when a Telegram message is received.
Supports both webhook mode and polling mode (auto-fallback).
Uses vault-integrated credential resolution.
"""

import asyncio
import os
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.resources.telegram_client import (
    TelegramAPIError,
    TelegramClient,
    TelegramConfig,
)
from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerStatus,
    TriggerType,
)
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class TelegramTrigger(BaseTrigger):
    """
    Trigger that responds to Telegram messages.

    Supports two modes:
    1. Webhook mode: Receives updates via Telegram webhook (requires public URL)
    2. Polling mode: Polls getUpdates API (fallback when webhook unavailable)

    Configuration options:
        bot_token: Telegram bot token from @BotFather
        credential_name: Name of stored credential (alternative to bot_token)
        mode: "webhook", "polling", or "auto" (default: auto)
        webhook_url: Public URL for webhook (auto-detected from CASARE_WEBHOOK_URL)
        polling_interval: Seconds between polls (default: 2)
        allowed_updates: List of update types to receive
        filter_chat_ids: Only trigger for specific chat IDs (optional)
        filter_user_ids: Only trigger for specific user IDs (optional)
        commands_only: Only trigger for bot commands (default: False)

    Payload variables:
        message_id: ID of the received message
        chat_id: ID of the chat
        user_id: ID of the user who sent the message
        username: Username of the sender
        first_name: First name of the sender
        text: Message text content
        is_command: Whether message is a bot command
        command: Command name if is_command (without /)
        command_args: Command arguments if is_command
        message_type: Type of message (text, photo, document, etc.)
        raw_update: Full update object from Telegram
    """

    trigger_type = TriggerType.TELEGRAM
    display_name = "Telegram"
    description = "Trigger workflow when Telegram message is received"
    icon = "telegram"
    category = "Messaging"

    def __init__(
        self,
        config: BaseTriggerConfig,
        event_callback=None,
    ) -> None:
        super().__init__(config, event_callback)
        self._client: TelegramClient | None = None
        self._polling_task: asyncio.Task | None = None
        self._last_update_id: int = 0
        self._webhook_active: bool = False

    async def _get_client(self) -> TelegramClient:
        """Get or create Telegram client."""
        if self._client:
            return self._client

        # Get bot token
        bot_token = await self._get_bot_token()
        if not bot_token:
            raise TelegramAPIError("No Telegram bot token configured")

        config = TelegramConfig(bot_token=bot_token)
        self._client = TelegramClient(config)
        return self._client

    async def _get_bot_token(self) -> str | None:
        """
        Get bot token using unified credential resolution.

        Resolution order:
        1. Direct config (bot_token)
        2. Vault credential lookup (via credential_name)
        3. Legacy credential manager (for backwards compatibility)
        4. Environment variable (TELEGRAM_BOT_TOKEN)

        Returns:
            Bot token string or None
        """
        # Try direct config first
        token = self.config.config.get("bot_token")
        if token:
            return token

        # Try vault credential provider
        cred_name = self.config.config.get("credential_name")
        if cred_name:
            try:
                from casare_rpa.infrastructure.security.credential_provider import (
                    VaultCredentialProvider,
                )

                provider = VaultCredentialProvider()
                await provider.initialize()
                try:
                    cred = await provider.get_credential(cred_name)
                    if cred:
                        # Try bot_token field or api_key field
                        bot_token = getattr(cred, "bot_token", None)
                        if bot_token:
                            logger.debug(f"Using vault credential: {cred_name}")
                            return bot_token
                        # Try data dict
                        if hasattr(cred, "data") and cred.data:
                            bot_token = cred.data.get("bot_token")
                            if bot_token:
                                logger.debug(f"Using vault credential data: {cred_name}")
                                return bot_token
                finally:
                    await provider.shutdown()
            except ImportError:
                logger.debug("Vault credential provider not available")
            except Exception as e:
                logger.debug(f"Vault credential lookup failed: {e}")

        # Try legacy credential manager for backwards compatibility
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            if cred_name:
                cred = credential_manager.get_telegram_credential(cred_name)
                if cred and cred.bot_token:
                    logger.debug(f"Using legacy credential: {cred_name}")
                    return cred.bot_token

            # Try default names in legacy system
            for name in ["telegram", "telegram_bot", "default_telegram"]:
                cred = credential_manager.get_telegram_credential(name)
                if cred and cred.bot_token:
                    logger.debug(f"Using legacy default credential: {name}")
                    return cred.bot_token
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Legacy credential lookup failed: {e}")

        # Try environment
        return os.environ.get("TELEGRAM_BOT_TOKEN")

    async def start(self) -> bool:
        """Start the Telegram trigger."""
        self._status = TriggerStatus.STARTING

        try:
            client = await self._get_client()
            await client._ensure_session()

            # Verify bot token
            bot_info = await client.get_me()
            logger.info(f"Telegram trigger connecting as @{bot_info.get('username', 'unknown')}")

            # Determine mode
            mode = self.config.config.get("mode", "auto")

            if mode == "webhook" or (mode == "auto" and self._can_use_webhook()):
                success = await self._setup_webhook(client)
                if success:
                    self._webhook_active = True
                    self._status = TriggerStatus.ACTIVE
                    logger.info(f"Telegram trigger started in webhook mode: {self.config.name}")
                    return True
                elif mode == "webhook":
                    # Webhook mode explicitly requested but failed
                    raise TelegramAPIError("Failed to set up webhook")

            # Fallback to polling
            await self._start_polling(client)
            self._status = TriggerStatus.ACTIVE
            logger.info(f"Telegram trigger started in polling mode: {self.config.name}")
            return True

        except Exception as e:
            self._status = TriggerStatus.ERROR
            self._error_message = str(e)
            logger.error(f"Failed to start Telegram trigger: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the Telegram trigger."""
        self._status = TriggerStatus.STOPPING

        try:
            # Stop polling if active
            if self._polling_task and not self._polling_task.done():
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass
                self._polling_task = None

            # Delete webhook if active
            if self._webhook_active and self._client:
                try:
                    await self._client.delete_webhook()
                except Exception as e:
                    logger.warning(f"Failed to delete webhook: {e}")
                self._webhook_active = False

            # Close client
            if self._client:
                await self._client.close()
                self._client = None

            self._status = TriggerStatus.INACTIVE
            logger.info(f"Telegram trigger stopped: {self.config.name}")
            return True

        except Exception as e:
            self._error_message = str(e)
            logger.error(f"Error stopping Telegram trigger: {e}")
            return False

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate Telegram trigger configuration."""
        config = self.config.config

        # Check for bot token source
        has_token = bool(config.get("bot_token"))
        has_credential = bool(config.get("credential_name"))
        has_env = bool(os.environ.get("TELEGRAM_BOT_TOKEN"))

        if not (has_token or has_credential or has_env):
            return (
                False,
                "Bot token required: provide bot_token, credential_name, or TELEGRAM_BOT_TOKEN env",
            )

        # Validate mode
        mode = config.get("mode", "auto")
        if mode not in ["auto", "webhook", "polling"]:
            return False, "mode must be 'auto', 'webhook', or 'polling'"

        # Validate polling interval
        interval = config.get("polling_interval", 2)
        if not isinstance(interval, int | float) or interval < 0.5:
            return False, "polling_interval must be >= 0.5 seconds"

        # Validate filter arrays
        for key in ["filter_chat_ids", "filter_user_ids", "allowed_updates"]:
            value = config.get(key)
            if value is not None and not isinstance(value, list):
                return False, f"{key} must be a list"

        return True, None

    def _can_use_webhook(self) -> bool:
        """Check if webhook mode is available."""
        # Check for configured webhook URL
        webhook_url = self.config.config.get("webhook_url")
        if webhook_url:
            return True

        # Check environment for tunnel URL
        env_url = os.environ.get("CASARE_WEBHOOK_URL")
        if env_url:
            return True

        return False

    def _get_webhook_url(self) -> str:
        """Get the webhook URL for this trigger."""
        # Use configured URL
        webhook_url = self.config.config.get("webhook_url")
        if webhook_url:
            return f"{webhook_url}/telegram/{self.config.id}"

        # Use environment URL
        env_url = os.environ.get("CASARE_WEBHOOK_URL")
        if env_url:
            return f"{env_url}/telegram/{self.config.id}"

        raise TelegramAPIError("No webhook URL available")

    async def _setup_webhook(self, client: TelegramClient) -> bool:
        """Set up Telegram webhook."""
        try:
            webhook_url = self._get_webhook_url()
            allowed_updates = self.config.config.get("allowed_updates", ["message"])

            await client.set_webhook(
                url=webhook_url,
                allowed_updates=allowed_updates,
                drop_pending_updates=True,
            )

            logger.info(f"Telegram webhook set to: {webhook_url}")
            return True

        except Exception as e:
            logger.warning(f"Failed to set webhook: {e}")
            return False

    async def _start_polling(self, client: TelegramClient) -> None:
        """Start long polling for updates."""
        # Delete any existing webhook first
        try:
            await client.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass

        # Start polling task
        self._polling_task = asyncio.create_task(self._poll_updates(client))

    async def _poll_updates(self, client: TelegramClient) -> None:
        """Poll for Telegram updates."""
        interval = self.config.config.get("polling_interval", 2)
        allowed_updates = self.config.config.get("allowed_updates", ["message"])
        timeout = 30  # Long polling timeout

        logger.debug(f"Starting Telegram polling with {interval}s interval")

        while self._status == TriggerStatus.ACTIVE:
            try:
                updates = await client.get_updates(
                    offset=self._last_update_id + 1 if self._last_update_id else None,
                    timeout=timeout,
                    allowed_updates=allowed_updates,
                )

                for update in updates:
                    update_id = update.get("update_id", 0)
                    if update_id > self._last_update_id:
                        self._last_update_id = update_id
                        await self._process_update(update)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(interval * 2)  # Back off on error

            await asyncio.sleep(interval)

    async def handle_webhook_update(self, update: dict[str, Any]) -> bool:
        """
        Handle an update received via webhook.

        Called by TriggerManager when webhook request is received.

        Args:
            update: Telegram update object

        Returns:
            True if processed successfully
        """
        try:
            await self._process_update(update)
            return True
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            return False

    async def _process_update(self, update: dict[str, Any]) -> None:
        """Process a Telegram update and emit trigger event if matching."""
        message = update.get("message", {})
        if not message:
            # Could be edited_message, channel_post, etc.
            message = (
                update.get("edited_message")
                or update.get("channel_post")
                or update.get("edited_channel_post")
                or {}
            )

        if not message:
            logger.debug(f"Update has no message: {update.get('update_id')}")
            return

        # Extract message info
        chat_id = message.get("chat", {}).get("id")
        user = message.get("from", {})
        user_id = user.get("id")
        text = message.get("text", "")

        # Apply filters
        if not self._passes_filters(chat_id, user_id, text):
            logger.debug(f"Update filtered out: chat={chat_id}, user={user_id}")
            return

        # Build payload
        payload = self._build_payload(update, message, user, text)

        # Emit trigger event
        await self.emit(
            payload=payload,
            metadata={
                "update_id": update.get("update_id"),
                "message_type": self._get_message_type(message),
            },
        )

    def _passes_filters(self, chat_id: int | None, user_id: int | None, text: str) -> bool:
        """Check if message passes configured filters."""
        config = self.config.config

        # Filter by chat ID
        filter_chats = config.get("filter_chat_ids")
        if filter_chats and chat_id not in filter_chats:
            return False

        # Filter by user ID
        filter_users = config.get("filter_user_ids")
        if filter_users and user_id not in filter_users:
            return False

        # Commands only filter
        if config.get("commands_only", False):
            if not text or not text.startswith("/"):
                return False

        return True

    def _build_payload(
        self,
        update: dict[str, Any],
        message: dict[str, Any],
        user: dict[str, Any],
        text: str,
    ) -> dict[str, Any]:
        """Build payload from Telegram message."""
        chat = message.get("chat", {})

        # Parse command if present
        is_command = text.startswith("/") if text else False
        command = ""
        command_args = ""
        if is_command:
            parts = text[1:].split(maxsplit=1)
            command = parts[0].split("@")[0]  # Remove @botname suffix
            command_args = parts[1] if len(parts) > 1 else ""

        return {
            "message_id": message.get("message_id"),
            "chat_id": chat.get("id"),
            "chat_type": chat.get("type"),
            "chat_title": chat.get("title", chat.get("first_name", "")),
            "user_id": user.get("id"),
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "text": text,
            "is_command": is_command,
            "command": command,
            "command_args": command_args,
            "message_type": self._get_message_type(message),
            "date": message.get("date"),
            "raw_update": update,
        }

    def _get_message_type(self, message: dict[str, Any]) -> str:
        """Determine message type."""
        if message.get("text"):
            return "text"
        elif message.get("photo"):
            return "photo"
        elif message.get("document"):
            return "document"
        elif message.get("video"):
            return "video"
        elif message.get("audio"):
            return "audio"
        elif message.get("voice"):
            return "voice"
        elif message.get("video_note"):
            return "video_note"
        elif message.get("sticker"):
            return "sticker"
        elif message.get("location"):
            return "location"
        elif message.get("contact"):
            return "contact"
        elif message.get("poll"):
            return "poll"
        else:
            return "unknown"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get JSON schema for Telegram trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "bot_token": {
                    "type": "string",
                    "description": "Telegram bot token from @BotFather",
                },
                "credential_name": {
                    "type": "string",
                    "description": "Name of stored Telegram credential",
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "webhook", "polling"],
                    "default": "auto",
                    "description": "Update receiving mode",
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Public URL for webhook (auto-detected if not set)",
                },
                "polling_interval": {
                    "type": "number",
                    "minimum": 0.5,
                    "default": 2,
                    "description": "Seconds between polls in polling mode",
                },
                "allowed_updates": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["message"],
                    "description": "Types of updates to receive",
                },
                "filter_chat_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Only trigger for these chat IDs",
                },
                "filter_user_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Only trigger for these user IDs",
                },
                "commands_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only trigger for bot commands (messages starting with /)",
                },
            },
            "required": ["name"],
        }


__all__ = ["TelegramTrigger"]
