"""
Tests for TelegramTrigger.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType, TriggerStatus
from casare_rpa.triggers.implementations.telegram_trigger import TelegramTrigger


@pytest.fixture
def trigger_config():
    """Create a test trigger configuration."""
    return BaseTriggerConfig(
        id="test_telegram_trigger_1",
        name="Test Telegram Trigger",
        trigger_type=TriggerType.TELEGRAM,
        scenario_id="test_scenario",
        workflow_id="test_workflow",
        config={
            "bot_token": "test_token_123",
            "mode": "polling",
            "polling_interval": 2,
        },
    )


@pytest.fixture
def trigger(trigger_config):
    """Create a test trigger instance."""
    callback = AsyncMock()
    return TelegramTrigger(trigger_config, event_callback=callback)


class TestTelegramTriggerConfig:
    """Tests for trigger configuration validation."""

    def test_validate_config_with_bot_token(self, trigger):
        """Test validation passes with bot token."""
        valid, error = trigger.validate_config()
        assert valid is True
        assert error is None

    def test_validate_config_without_token(self):
        """Test validation fails without any token source."""
        config = BaseTriggerConfig(
            id="test_trigger",
            name="Test",
            trigger_type=TriggerType.TELEGRAM,
            scenario_id="test_scenario",
            workflow_id="test_workflow",
            config={},  # No bot_token
        )
        trigger = TelegramTrigger(config)

        with patch.dict("os.environ", {}, clear=True):
            valid, error = trigger.validate_config()

        assert valid is False
        assert "token" in error.lower()

    def test_validate_config_invalid_mode(self, trigger_config):
        """Test validation fails with invalid mode."""
        trigger_config.config["mode"] = "invalid_mode"
        trigger = TelegramTrigger(trigger_config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "mode" in error.lower()

    def test_validate_config_invalid_polling_interval(self, trigger_config):
        """Test validation fails with too short polling interval."""
        trigger_config.config["polling_interval"] = 0.1  # Too short
        trigger = TelegramTrigger(trigger_config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "polling_interval" in error.lower()


class TestTelegramTriggerLifecycle:
    """Tests for trigger lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_polling_mode(self, trigger):
        """Test starting trigger in polling mode."""
        mock_client = AsyncMock()
        mock_client.get_me.return_value = {"username": "test_bot"}
        mock_client.delete_webhook = AsyncMock()
        mock_client.get_updates.return_value = []
        mock_client._ensure_session = AsyncMock()

        with patch.object(trigger, "_get_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_client

            # Start trigger (will spawn polling task)
            result = await trigger.start()

            assert result is True
            assert trigger.status == TriggerStatus.ACTIVE
            mock_client.get_me.assert_called_once()

            # Stop to cleanup
            await trigger.stop()

    @pytest.mark.asyncio
    async def test_stop_trigger(self, trigger):
        """Test stopping trigger cleans up properly."""
        trigger._status = TriggerStatus.ACTIVE
        trigger._polling_task = asyncio.create_task(asyncio.sleep(100))
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        trigger._client = mock_client

        result = await trigger.stop()

        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE
        # Client is set to None after close, so check the mock directly
        mock_client.close.assert_called_once()


class TestTelegramTriggerUpdateProcessing:
    """Tests for Telegram update processing."""

    @pytest.fixture
    def sample_update(self):
        """Create a sample Telegram update."""
        return {
            "update_id": 12345,
            "message": {
                "message_id": 100,
                "chat": {"id": 123456, "type": "private"},
                "from": {"id": 789, "first_name": "Test", "username": "testuser"},
                "date": 1234567890,
                "text": "Hello bot!",
            },
        }

    @pytest.mark.asyncio
    async def test_process_text_message(self, trigger, sample_update):
        """Test processing a text message."""
        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            await trigger._process_update(sample_update)

            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            payload = call_args[1]["payload"]

            assert payload["message_id"] == 100
            assert payload["chat_id"] == 123456
            assert payload["text"] == "Hello bot!"
            assert payload["username"] == "testuser"
            assert payload["is_command"] is False

    @pytest.mark.asyncio
    async def test_process_command_message(self, trigger):
        """Test processing a bot command."""
        update = {
            "update_id": 12346,
            "message": {
                "message_id": 101,
                "chat": {"id": 123456, "type": "private"},
                "from": {"id": 789, "first_name": "Test"},
                "date": 1234567890,
                "text": "/start hello world",
            },
        }

        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            await trigger._process_update(update)

            payload = mock_emit.call_args[1]["payload"]

            assert payload["is_command"] is True
            assert payload["command"] == "start"
            assert payload["command_args"] == "hello world"

    @pytest.mark.asyncio
    async def test_filter_by_chat_id(self, trigger_config):
        """Test filtering updates by chat ID."""
        trigger_config.config["filter_chat_ids"] = [123456]
        trigger = TelegramTrigger(trigger_config)

        # Message from allowed chat
        update1 = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "chat": {"id": 123456},
                "from": {"id": 1},
                "text": "Hello",
            },
        }

        # Message from blocked chat
        update2 = {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "chat": {"id": 999999},
                "from": {"id": 1},
                "text": "Hello",
            },
        }

        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            await trigger._process_update(update1)
            assert mock_emit.called

            mock_emit.reset_mock()

            await trigger._process_update(update2)
            assert not mock_emit.called

    @pytest.mark.asyncio
    async def test_commands_only_filter(self, trigger_config):
        """Test commands_only filter."""
        trigger_config.config["commands_only"] = True
        trigger = TelegramTrigger(trigger_config)

        # Regular message
        regular_update = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "chat": {"id": 123456},
                "from": {"id": 1},
                "text": "Hello",
            },
        }

        # Command message
        command_update = {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "chat": {"id": 123456},
                "from": {"id": 1},
                "text": "/help",
            },
        }

        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            await trigger._process_update(regular_update)
            assert not mock_emit.called

            await trigger._process_update(command_update)
            assert mock_emit.called

    def test_get_message_type(self, trigger):
        """Test message type detection."""
        assert trigger._get_message_type({"text": "hello"}) == "text"
        # Note: Empty lists/dicts are falsy, so use non-empty values
        assert trigger._get_message_type({"photo": [{"file_id": "abc"}]}) == "photo"
        assert trigger._get_message_type({"document": {"file_id": "abc"}}) == "document"
        assert (
            trigger._get_message_type({"location": {"latitude": 0, "longitude": 0}})
            == "location"
        )
        assert trigger._get_message_type({}) == "unknown"


class TestTelegramTriggerWebhook:
    """Tests for webhook handling."""

    @pytest.mark.asyncio
    async def test_handle_webhook_update(self, trigger):
        """Test handling webhook update."""
        update = {
            "update_id": 12345,
            "message": {
                "message_id": 100,
                "chat": {"id": 123456},
                "from": {"id": 789},
                "text": "Webhook test",
            },
        }

        with patch.object(
            trigger, "_process_update", new_callable=AsyncMock
        ) as mock_process:
            result = await trigger.handle_webhook_update(update)

            assert result is True
            mock_process.assert_called_once_with(update)

    @pytest.mark.asyncio
    async def test_handle_webhook_error(self, trigger):
        """Test handling webhook update with error."""
        update = {"update_id": 12345}

        with patch.object(
            trigger, "_process_update", new_callable=AsyncMock
        ) as mock_process:
            mock_process.side_effect = Exception("Processing error")

            result = await trigger.handle_webhook_update(update)

            assert result is False


class TestTelegramTriggerConfigSchema:
    """Tests for configuration schema."""

    def test_get_config_schema(self):
        """Test getting config schema."""
        schema = TelegramTrigger.get_config_schema()

        assert "properties" in schema
        assert "bot_token" in schema["properties"]
        assert "mode" in schema["properties"]
        assert "polling_interval" in schema["properties"]
        assert "filter_chat_ids" in schema["properties"]
        assert "commands_only" in schema["properties"]

    def test_display_info(self):
        """Test getting display info."""
        info = TelegramTrigger.get_display_info()

        assert info["type"] == "telegram"
        assert info["display_name"] == "Telegram"
        assert info["category"] == "Messaging"
