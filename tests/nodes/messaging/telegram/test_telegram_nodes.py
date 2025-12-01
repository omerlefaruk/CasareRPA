"""
Tests for Telegram send nodes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.nodes.messaging.telegram import (
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
)
from casare_rpa.infrastructure.resources.telegram_client import (
    TelegramClient,
    TelegramMessage,
    TelegramAPIError,
)


@pytest.fixture
def mock_execution_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.resources = {}
    context.variables = {}

    def resolve_value(val):
        if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
            var_name = val[2:-2].strip()
            return context.variables.get(var_name, val)
        return val

    context.resolve_value = resolve_value
    context.get_variable = lambda key: context.variables.get(key)
    return context


@pytest.fixture
def mock_telegram_client():
    """Create a mock Telegram client."""
    client = AsyncMock(spec=TelegramClient)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


class TestTelegramSendMessageNode:
    """Tests for TelegramSendMessageNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = TelegramSendMessageNode("test_node_1")

        assert node.NODE_TYPE == "telegram_send_message"
        assert node.NODE_CATEGORY == "messaging"
        assert "chat_id" in [p.name for p in node.input_ports.values()]
        assert "text" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test successful message sending."""
        node = TelegramSendMessageNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["text"] = "Hello, World!"
        node.config["bot_token"] = "test_token"

        # Mock the response
        mock_message = TelegramMessage(
            message_id=100, chat_id=123456, date=1234567890, text="Hello, World!"
        )
        mock_telegram_client.send_message.return_value = mock_message

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == 100
            mock_telegram_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_missing_text(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test error when text is missing."""
        node = TelegramSendMessageNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["text"] = ""  # Empty text
        node.config["bot_token"] = "test_token"

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is False
            assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_send_message_with_parse_mode(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test sending message with Markdown parse mode."""
        node = TelegramSendMessageNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["text"] = "*Bold* text"
        node.config["parse_mode"] = "Markdown"
        node.config["bot_token"] = "test_token"

        mock_message = TelegramMessage(message_id=101, chat_id=123456, date=1234567890)
        mock_telegram_client.send_message.return_value = mock_message

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            await node.execute(mock_execution_context)

            call_args = mock_telegram_client.send_message.call_args
            assert call_args[1]["parse_mode"] == "Markdown"


class TestTelegramSendPhotoNode:
    """Tests for TelegramSendPhotoNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = TelegramSendPhotoNode("test_node_1")

        assert node.NODE_TYPE == "telegram_send_photo"
        assert "photo" in [p.name for p in node.input_ports.values()]
        assert "caption" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_photo_success(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test successful photo sending."""
        node = TelegramSendPhotoNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["photo"] = "https://example.com/photo.jpg"
        node.config["bot_token"] = "test_token"

        mock_message = TelegramMessage(message_id=102, chat_id=123456, date=1234567890)
        mock_telegram_client.send_photo.return_value = mock_message

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == 102

    @pytest.mark.asyncio
    async def test_send_photo_with_caption(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test photo with caption."""
        node = TelegramSendPhotoNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["photo"] = "photo.jpg"
        node.config["caption"] = "Beautiful sunset!"
        node.config["bot_token"] = "test_token"

        mock_message = TelegramMessage(message_id=103, chat_id=123456, date=1234567890)
        mock_telegram_client.send_photo.return_value = mock_message

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            await node.execute(mock_execution_context)

            call_args = mock_telegram_client.send_photo.call_args
            assert call_args[1]["caption"] == "Beautiful sunset!"


class TestTelegramSendDocumentNode:
    """Tests for TelegramSendDocumentNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = TelegramSendDocumentNode("test_node_1")

        assert node.NODE_TYPE == "telegram_send_document"
        assert "document" in [p.name for p in node.input_ports.values()]
        assert "filename" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_document_success(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test successful document sending."""
        node = TelegramSendDocumentNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["document"] = "report.pdf"
        node.config["bot_token"] = "test_token"

        mock_message = TelegramMessage(message_id=104, chat_id=123456, date=1234567890)
        mock_telegram_client.send_document.return_value = mock_message

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == 104


class TestTelegramSendLocationNode:
    """Tests for TelegramSendLocationNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = TelegramSendLocationNode("test_node_1")

        assert node.NODE_TYPE == "telegram_send_location"
        assert "latitude" in [p.name for p in node.input_ports.values()]
        assert "longitude" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_location_success(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test successful location sending."""
        node = TelegramSendLocationNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["latitude"] = 51.5074
        node.config["longitude"] = -0.1278
        node.config["bot_token"] = "test_token"

        mock_message = TelegramMessage(message_id=105, chat_id=123456, date=1234567890)
        mock_telegram_client.send_location.return_value = mock_message

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == 105

    @pytest.mark.asyncio
    async def test_send_location_invalid_latitude(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test error with invalid latitude."""
        node = TelegramSendLocationNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["latitude"] = 100  # Invalid: > 90
        node.config["longitude"] = 0
        node.config["bot_token"] = "test_token"

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is False
            assert "latitude" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_send_location_invalid_longitude(
        self, mock_execution_context, mock_telegram_client
    ):
        """Test error with invalid longitude."""
        node = TelegramSendLocationNode("test_node_1")
        node.config["chat_id"] = "123456"
        node.config["latitude"] = 0
        node.config["longitude"] = 200  # Invalid: > 180
        node.config["bot_token"] = "test_token"

        with patch.object(
            node, "_get_telegram_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_telegram_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is False
            assert "longitude" in result["error"].lower()
