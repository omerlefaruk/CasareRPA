"""
Tests for WhatsApp send nodes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.nodes.messaging.whatsapp import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendLocationNode,
    WhatsAppSendInteractiveNode,
)
from casare_rpa.infrastructure.resources.whatsapp_client import (
    WhatsAppClient,
    WhatsAppMessage,
    WhatsAppAPIError,
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
def mock_whatsapp_client():
    """Create a mock WhatsApp client."""
    client = AsyncMock(spec=WhatsAppClient)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


class TestWhatsAppSendMessageNode:
    """Tests for WhatsAppSendMessageNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = WhatsAppSendMessageNode("test_node_1")

        assert node.NODE_TYPE == "whatsapp_send_message"
        assert node.NODE_CATEGORY == "messaging"
        assert "to" in [p.name for p in node.input_ports.values()]
        assert "text" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test successful message sending."""
        node = WhatsAppSendMessageNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["text"] = "Hello, World!"
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        # Mock the response
        mock_message = WhatsAppMessage(
            message_id="wamid.test123",
            phone_number="1234567890",
            status="sent",
        )
        mock_whatsapp_client.send_message.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == "wamid.test123"
            mock_whatsapp_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_missing_text(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test error when text is missing."""
        node = WhatsAppSendMessageNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["text"] = ""  # Empty text
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is False
            assert "required" in result["error"].lower()


class TestWhatsAppSendTemplateNode:
    """Tests for WhatsAppSendTemplateNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = WhatsAppSendTemplateNode("test_node_1")

        assert node.NODE_TYPE == "whatsapp_send_template"
        assert "template_name" in [p.name for p in node.input_ports.values()]
        assert "language_code" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_template_success(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test successful template sending."""
        node = WhatsAppSendTemplateNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["template_name"] = "hello_world"
        node.config["language_code"] = "en_US"
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        mock_message = WhatsAppMessage(
            message_id="wamid.template123",
            phone_number="1234567890",
        )
        mock_whatsapp_client.send_template.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == "wamid.template123"

    @pytest.mark.asyncio
    async def test_send_template_with_components(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test template with components JSON."""
        node = WhatsAppSendTemplateNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["template_name"] = "order_update"
        node.config["language_code"] = "en_US"
        node.config["components"] = (
            '[{"type": "body", "parameters": [{"type": "text", "text": "123"}]}]'
        )
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        mock_message = WhatsAppMessage(
            message_id="wamid.template456",
            phone_number="1234567890",
        )
        mock_whatsapp_client.send_template.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            call_args = mock_whatsapp_client.send_template.call_args
            assert call_args[1]["components"] is not None


class TestWhatsAppSendImageNode:
    """Tests for WhatsAppSendImageNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = WhatsAppSendImageNode("test_node_1")

        assert node.NODE_TYPE == "whatsapp_send_image"
        assert "image" in [p.name for p in node.input_ports.values()]
        assert "caption" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_image_success(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test successful image sending."""
        node = WhatsAppSendImageNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["image"] = "https://example.com/image.jpg"
        node.config["caption"] = "Test image"
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        mock_message = WhatsAppMessage(
            message_id="wamid.image123",
            phone_number="1234567890",
        )
        mock_whatsapp_client.send_image.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == "wamid.image123"


class TestWhatsAppSendDocumentNode:
    """Tests for WhatsAppSendDocumentNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = WhatsAppSendDocumentNode("test_node_1")

        assert node.NODE_TYPE == "whatsapp_send_document"
        assert "document" in [p.name for p in node.input_ports.values()]
        assert "filename" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_document_success(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test successful document sending."""
        node = WhatsAppSendDocumentNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["document"] = "https://example.com/report.pdf"
        node.config["filename"] = "report.pdf"
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        mock_message = WhatsAppMessage(
            message_id="wamid.doc123",
            phone_number="1234567890",
        )
        mock_whatsapp_client.send_document.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == "wamid.doc123"


class TestWhatsAppSendLocationNode:
    """Tests for WhatsAppSendLocationNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = WhatsAppSendLocationNode("test_node_1")

        assert node.NODE_TYPE == "whatsapp_send_location"
        assert "latitude" in [p.name for p in node.input_ports.values()]
        assert "longitude" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_location_success(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test successful location sending."""
        node = WhatsAppSendLocationNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["latitude"] = 51.5074
        node.config["longitude"] = -0.1278
        node.config["name"] = "London"
        node.config["address"] = "London, UK"
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        mock_message = WhatsAppMessage(
            message_id="wamid.loc123",
            phone_number="1234567890",
        )
        mock_whatsapp_client.send_location.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == "wamid.loc123"

    @pytest.mark.asyncio
    async def test_send_location_invalid_latitude(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test error with invalid latitude."""
        node = WhatsAppSendLocationNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["latitude"] = 100  # Invalid: > 90
        node.config["longitude"] = 0
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is False
            assert "latitude" in result["error"].lower()


class TestWhatsAppSendInteractiveNode:
    """Tests for WhatsAppSendInteractiveNode."""

    def test_node_initialization(self):
        """Test node initializes with correct properties."""
        node = WhatsAppSendInteractiveNode("test_node_1")

        assert node.NODE_TYPE == "whatsapp_send_interactive"
        assert "interactive_type" in [p.name for p in node.input_ports.values()]
        assert "body_text" in [p.name for p in node.input_ports.values()]
        assert "action_json" in [p.name for p in node.input_ports.values()]

    @pytest.mark.asyncio
    async def test_send_interactive_button_success(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test successful interactive button message."""
        node = WhatsAppSendInteractiveNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["interactive_type"] = "button"
        node.config["body_text"] = "Choose an option:"
        node.config["action_json"] = (
            '{"buttons": [{"type": "reply", "reply": {"id": "1", "title": "Yes"}}]}'
        )
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        mock_message = WhatsAppMessage(
            message_id="wamid.interactive123",
            phone_number="1234567890",
        )
        mock_whatsapp_client.send_interactive.return_value = mock_message

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is True
            assert result["message_id"] == "wamid.interactive123"

    @pytest.mark.asyncio
    async def test_send_interactive_invalid_type(
        self, mock_execution_context, mock_whatsapp_client
    ):
        """Test error with invalid interactive type."""
        node = WhatsAppSendInteractiveNode("test_node_1")
        node.config["to"] = "+1234567890"
        node.config["interactive_type"] = "invalid"
        node.config["body_text"] = "Test"
        node.config["action_json"] = "{}"
        node.config["access_token"] = "test_token"
        node.config["phone_number_id"] = "123456789"

        with patch.object(
            node, "_get_whatsapp_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_get_client.return_value = mock_whatsapp_client

            result = await node.execute(mock_execution_context)

            assert result["success"] is False
            assert (
                "button" in result["error"].lower() or "list" in result["error"].lower()
            )
