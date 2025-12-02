"""
Tests for WhatsAppClient API client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from casare_rpa.infrastructure.resources.whatsapp_client import (
    WhatsAppClient,
    WhatsAppConfig,
    WhatsAppMessage,
    WhatsAppTemplate,
    WhatsAppAPIError,
)


class TestWhatsAppConfig:
    """Tests for WhatsAppConfig dataclass."""

    def test_api_url_construction(self):
        """Test API URL is correctly constructed."""
        config = WhatsAppConfig(
            access_token="test_token",
            phone_number_id="123456789",
        )
        assert config.api_url == "https://graph.facebook.com/v18.0/123456789/messages"

    def test_media_url_construction(self):
        """Test media URL is correctly constructed."""
        config = WhatsAppConfig(
            access_token="test_token",
            phone_number_id="123456789",
        )
        assert config.media_url == "https://graph.facebook.com/v18.0/123456789/media"

    def test_custom_api_version(self):
        """Test custom API version is used."""
        config = WhatsAppConfig(
            access_token="test_token",
            phone_number_id="123456789",
            api_version="v19.0",
        )
        assert "v19.0" in config.api_url

    def test_default_values(self):
        """Test default configuration values."""
        config = WhatsAppConfig(
            access_token="test_token",
            phone_number_id="123456789",
        )
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0


class TestWhatsAppMessage:
    """Tests for WhatsAppMessage dataclass."""

    def test_from_response_basic(self):
        """Test creating WhatsAppMessage from API response."""
        data = {
            "messages": [{"id": "wamid.123456"}],
        }
        msg = WhatsAppMessage.from_response(data, "1234567890")

        assert msg.message_id == "wamid.123456"
        assert msg.phone_number == "1234567890"
        assert msg.status == "sent"

    def test_from_response_empty_messages(self):
        """Test handling empty messages array."""
        data = {"messages": []}
        msg = WhatsAppMessage.from_response(data, "1234567890")

        assert msg.message_id == ""
        assert msg.phone_number == "1234567890"


class TestWhatsAppTemplate:
    """Tests for WhatsAppTemplate dataclass."""

    def test_from_response(self):
        """Test creating WhatsAppTemplate from API response."""
        data = {
            "id": "template_123",
            "name": "hello_world",
            "language": "en_US",
            "category": "MARKETING",
            "status": "APPROVED",
            "components": [{"type": "BODY", "text": "Hello!"}],
        }
        template = WhatsAppTemplate.from_response(data)

        assert template.id == "template_123"
        assert template.name == "hello_world"
        assert template.language == "en_US"
        assert template.category == "MARKETING"
        assert template.status == "APPROVED"


class TestWhatsAppClient:
    """Tests for WhatsAppClient."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return WhatsAppConfig(
            access_token="test_access_token",
            phone_number_id="123456789",
        )

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return WhatsAppClient(config)

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
            "messages": [{"id": "wamid.test123"}],
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

            result = await client.send_message(to="+1234567890", text="Test message")

            assert result.message_id == "wamid.test123"
            assert result.phone_number == "1234567890"
            mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_normalizes_phone(self, client):
        """Test phone number normalization."""
        mock_response = {"messages": [{"id": "wamid.test123"}]}

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

            # Phone with various formats
            result = await client.send_message(to="+1 234-567-8900", text="Test")

            # Should normalize to just digits
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["to"] == "12345678900"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test handling API errors."""
        mock_response = {
            "error": {
                "code": 100,
                "message": "Invalid parameter",
                "type": "OAuthException",
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

            with pytest.raises(WhatsAppAPIError) as exc_info:
                await client.send_message(to="invalid", text="Test")

            assert exc_info.value.error_code == 100
            assert "Invalid parameter" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_template(self, client):
        """Test sending a template message."""
        mock_response = {"messages": [{"id": "wamid.template123"}]}

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

            result = await client.send_template(
                to="+1234567890",
                template_name="hello_world",
                language_code="en_US",
            )

            assert result.message_id == "wamid.template123"
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["type"] == "template"
            assert call_args[1]["json"]["template"]["name"] == "hello_world"

    @pytest.mark.asyncio
    async def test_send_image_url(self, client):
        """Test sending an image via URL."""
        mock_response = {"messages": [{"id": "wamid.image123"}]}

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

            result = await client.send_image(
                to="+1234567890",
                image="https://example.com/image.jpg",
                caption="Test image",
            )

            assert result.message_id == "wamid.image123"
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["type"] == "image"
            assert (
                call_args[1]["json"]["image"]["link"] == "https://example.com/image.jpg"
            )
            assert call_args[1]["json"]["image"]["caption"] == "Test image"

    @pytest.mark.asyncio
    async def test_send_location(self, client):
        """Test sending a location."""
        mock_response = {"messages": [{"id": "wamid.location123"}]}

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

            result = await client.send_location(
                to="+1234567890",
                latitude=51.5074,
                longitude=-0.1278,
                name="London",
                address="London, UK",
            )

            assert result.message_id == "wamid.location123"
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["type"] == "location"
            assert call_args[1]["json"]["location"]["latitude"] == 51.5074
            assert call_args[1]["json"]["location"]["name"] == "London"

    @pytest.mark.asyncio
    async def test_mark_as_read(self, client):
        """Test marking a message as read."""
        mock_response = {"success": True}

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

            result = await client.mark_as_read("wamid.test123")

            assert result is True
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["status"] == "read"
            assert call_args[1]["json"]["message_id"] == "wamid.test123"
