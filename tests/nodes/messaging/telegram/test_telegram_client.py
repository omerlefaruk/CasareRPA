"""
Tests for TelegramClient API client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from casare_rpa.infrastructure.resources.telegram_client import (
    TelegramClient,
    TelegramConfig,
    TelegramMessage,
    TelegramAPIError,
)


class TestTelegramConfig:
    """Tests for TelegramConfig dataclass."""

    def test_api_url_construction(self):
        """Test API URL is correctly constructed from bot token."""
        config = TelegramConfig(bot_token="123456:ABC-DEF")
        assert config.api_url == "https://api.telegram.org/bot123456:ABC-DEF"

    def test_custom_base_url(self):
        """Test custom base URL is used when provided."""
        config = TelegramConfig(
            bot_token="123456:ABC-DEF", base_url="https://custom.telegram.api"
        )
        assert config.api_url == "https://custom.telegram.api/bot123456:ABC-DEF"

    def test_default_values(self):
        """Test default configuration values."""
        config = TelegramConfig(bot_token="test_token")
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0


class TestTelegramMessage:
    """Tests for TelegramMessage dataclass."""

    def test_from_response_basic(self):
        """Test creating TelegramMessage from API response."""
        data = {
            "message_id": 123,
            "chat": {"id": 456},
            "date": 1234567890,
            "text": "Hello World",
        }
        msg = TelegramMessage.from_response(data)

        assert msg.message_id == 123
        assert msg.chat_id == 456
        assert msg.date == 1234567890
        assert msg.text == "Hello World"

    def test_from_response_with_user(self):
        """Test creating TelegramMessage with user info."""
        data = {
            "message_id": 123,
            "chat": {"id": 456},
            "date": 1234567890,
            "from": {"id": 789, "first_name": "Test"},
        }
        msg = TelegramMessage.from_response(data)

        assert msg.from_user == {"id": 789, "first_name": "Test"}

    def test_from_response_missing_fields(self):
        """Test handling missing fields in response."""
        data = {}
        msg = TelegramMessage.from_response(data)

        assert msg.message_id == 0
        assert msg.chat_id == 0
        assert msg.text is None


class TestTelegramClient:
    """Tests for TelegramClient."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return TelegramConfig(bot_token="test_token_123")

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return TelegramClient(config)

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager opens and closes session."""
        with patch.object(
            client, "_ensure_session", new_callable=AsyncMock
        ) as mock_ensure:
            with patch.object(client, "close", new_callable=AsyncMock) as mock_close:
                async with client:
                    mock_ensure.assert_called_once()

                mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_success(self, client):
        """Test sending a text message successfully."""
        mock_response = {
            "ok": True,
            "result": {
                "message_id": 100,
                "chat": {"id": 123456},
                "date": 1234567890,
                "text": "Test message",
            },
        }

        with patch.object(
            client, "_ensure_session", new_callable=AsyncMock
        ) as mock_ensure:
            mock_session = MagicMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_session.post.return_value = mock_context
            mock_ensure.return_value = mock_session

            result = await client.send_message(chat_id=123456, text="Test message")

            assert result.message_id == 100
            assert result.chat_id == 123456
            mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_parse_mode(self, client):
        """Test sending message with parse mode."""
        mock_response = {
            "ok": True,
            "result": {
                "message_id": 101,
                "chat": {"id": 123456},
                "date": 1234567890,
            },
        }

        with patch.object(
            client, "_ensure_session", new_callable=AsyncMock
        ) as mock_ensure:
            mock_session = MagicMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_session.post.return_value = mock_context
            mock_ensure.return_value = mock_session

            await client.send_message(
                chat_id=123456, text="*Bold* text", parse_mode="Markdown"
            )

            # Verify post was called with parse_mode in data
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test handling API errors."""
        mock_response = {
            "ok": False,
            "error_code": 400,
            "description": "Bad Request: chat not found",
        }

        with patch.object(
            client, "_ensure_session", new_callable=AsyncMock
        ) as mock_ensure:
            mock_session = MagicMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_session.post.return_value = mock_context
            mock_ensure.return_value = mock_session

            with pytest.raises(TelegramAPIError) as exc_info:
                await client.send_message(chat_id=999999, text="Test")

            assert exc_info.value.error_code == 400
            assert "chat not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_me(self, client):
        """Test getting bot info."""
        mock_response = {
            "ok": True,
            "result": {
                "id": 123456789,
                "is_bot": True,
                "first_name": "Test Bot",
                "username": "test_bot",
            },
        }

        with patch.object(
            client, "_ensure_session", new_callable=AsyncMock
        ) as mock_ensure:
            mock_session = MagicMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_session.post.return_value = mock_context
            mock_ensure.return_value = mock_session

            result = await client.get_me()

            assert result["username"] == "test_bot"
            assert result["is_bot"] is True

    def test_guess_content_type(self, client):
        """Test content type guessing from file extension."""
        from pathlib import Path

        assert client._guess_content_type(Path("test.jpg")) == "image/jpeg"
        assert client._guess_content_type(Path("test.png")) == "image/png"
        assert client._guess_content_type(Path("test.pdf")) == "application/pdf"
        assert (
            client._guess_content_type(Path("test.unknown"))
            == "application/octet-stream"
        )
