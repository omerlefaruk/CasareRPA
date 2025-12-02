"""
CasareRPA - Node Schema Validation Tests

Tests that all messaging nodes have proper @node_schema decorators
and that schemas are correctly configured.
"""

import pytest

from casare_rpa.domain.schemas import NodeSchema, PropertyDef, PropertyType

# Telegram nodes
from casare_rpa.nodes.messaging.telegram import (
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
    TelegramEditMessageNode,
    TelegramDeleteMessageNode,
    TelegramSendMediaGroupNode,
    TelegramAnswerCallbackNode,
    TelegramGetUpdatesNode,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    TELEGRAM_PARSE_MODE,
    TELEGRAM_DISABLE_NOTIFICATION,
)

# WhatsApp nodes
from casare_rpa.nodes.messaging.whatsapp import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendLocationNode,
    WhatsAppSendVideoNode,
    WhatsAppSendInteractiveNode,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_CREDENTIAL_NAME,
    WHATSAPP_TO,
)


class TestTelegramNodeSchemas:
    """Test Telegram node schema configuration."""

    @pytest.mark.parametrize(
        "node_class",
        [
            TelegramSendMessageNode,
            TelegramSendPhotoNode,
            TelegramSendDocumentNode,
            TelegramSendLocationNode,
            TelegramEditMessageNode,
            TelegramDeleteMessageNode,
            TelegramSendMediaGroupNode,
            TelegramAnswerCallbackNode,
            TelegramGetUpdatesNode,
        ],
    )
    def test_telegram_node_has_schema(self, node_class):
        """All Telegram nodes should have __node_schema__ attribute."""
        assert hasattr(node_class, "__node_schema__")
        assert isinstance(node_class.__node_schema__, NodeSchema)

    @pytest.mark.parametrize(
        "node_class",
        [
            TelegramSendMessageNode,
            TelegramSendPhotoNode,
            TelegramSendDocumentNode,
            TelegramSendLocationNode,
            TelegramEditMessageNode,
            TelegramDeleteMessageNode,
            TelegramSendMediaGroupNode,
            TelegramAnswerCallbackNode,
            TelegramGetUpdatesNode,
        ],
    )
    def test_telegram_node_has_connection_properties(self, node_class):
        """Telegram nodes should have bot_token and credential_name properties."""
        schema = node_class.__node_schema__
        prop_names = [p.name for p in schema.properties]
        assert "bot_token" in prop_names
        assert "credential_name" in prop_names

    @pytest.mark.parametrize(
        "node_class,expected_props",
        [
            (TelegramSendMessageNode, ["text", "parse_mode", "disable_notification"]),
            (TelegramSendPhotoNode, ["photo", "caption"]),
            (TelegramSendDocumentNode, ["document", "caption"]),
            (TelegramSendLocationNode, ["latitude", "longitude"]),
            (TelegramEditMessageNode, ["message_id", "text"]),
            (TelegramDeleteMessageNode, ["message_id"]),
            (TelegramSendMediaGroupNode, ["media_json"]),  # media stored as JSON string
            (TelegramAnswerCallbackNode, ["callback_query_id", "text"]),
            (TelegramGetUpdatesNode, ["offset", "limit", "timeout"]),
        ],
    )
    def test_telegram_node_specific_properties(self, node_class, expected_props):
        """Each Telegram node should have its specific properties."""
        schema = node_class.__node_schema__
        prop_names = [p.name for p in schema.properties]
        for prop in expected_props:
            assert prop in prop_names, f"{node_class.__name__} missing property: {prop}"


class TestWhatsAppNodeSchemas:
    """Test WhatsApp node schema configuration."""

    @pytest.mark.parametrize(
        "node_class",
        [
            WhatsAppSendMessageNode,
            WhatsAppSendTemplateNode,
            WhatsAppSendImageNode,
            WhatsAppSendDocumentNode,
            WhatsAppSendLocationNode,
            WhatsAppSendVideoNode,
            WhatsAppSendInteractiveNode,
        ],
    )
    def test_whatsapp_node_has_schema(self, node_class):
        """All WhatsApp nodes should have __node_schema__ attribute."""
        assert hasattr(node_class, "__node_schema__")
        assert isinstance(node_class.__node_schema__, NodeSchema)

    @pytest.mark.parametrize(
        "node_class",
        [
            WhatsAppSendMessageNode,
            WhatsAppSendTemplateNode,
            WhatsAppSendImageNode,
            WhatsAppSendDocumentNode,
            WhatsAppSendLocationNode,
            WhatsAppSendVideoNode,
            WhatsAppSendInteractiveNode,
        ],
    )
    def test_whatsapp_node_has_connection_properties(self, node_class):
        """WhatsApp nodes should have access_token and credential_name properties."""
        schema = node_class.__node_schema__
        prop_names = [p.name for p in schema.properties]
        assert "access_token" in prop_names
        assert "credential_name" in prop_names
        assert "phone_number_id" in prop_names

    @pytest.mark.parametrize(
        "node_class,expected_props",
        [
            (WhatsAppSendMessageNode, ["to", "text", "preview_url"]),
            (WhatsAppSendTemplateNode, ["to", "template_name", "language_code"]),
            (
                WhatsAppSendImageNode,
                ["to", "image", "caption"],
            ),  # property is 'image' not 'image_url'
            (
                WhatsAppSendDocumentNode,
                ["to", "document", "filename"],
            ),  # property is 'document'
            (WhatsAppSendLocationNode, ["to", "latitude", "longitude"]),
            (WhatsAppSendVideoNode, ["to", "video", "caption"]),  # property is 'video'
            (WhatsAppSendInteractiveNode, ["to", "interactive_type", "body_text"]),
        ],
    )
    def test_whatsapp_node_specific_properties(self, node_class, expected_props):
        """Each WhatsApp node should have its specific properties."""
        schema = node_class.__node_schema__
        prop_names = [p.name for p in schema.properties]
        for prop in expected_props:
            assert prop in prop_names, f"{node_class.__name__} missing property: {prop}"


class TestPropertyDefConstants:
    """Test reusable PropertyDef constants are correctly configured."""

    def test_telegram_constants_are_property_defs(self):
        """Telegram constants should be PropertyDef instances."""
        assert isinstance(TELEGRAM_BOT_TOKEN, PropertyDef)
        assert isinstance(TELEGRAM_CREDENTIAL_NAME, PropertyDef)
        assert isinstance(TELEGRAM_CHAT_ID, PropertyDef)
        assert isinstance(TELEGRAM_PARSE_MODE, PropertyDef)
        assert isinstance(TELEGRAM_DISABLE_NOTIFICATION, PropertyDef)

    def test_whatsapp_constants_are_property_defs(self):
        """WhatsApp constants should be PropertyDef instances."""
        assert isinstance(WHATSAPP_ACCESS_TOKEN, PropertyDef)
        assert isinstance(WHATSAPP_PHONE_NUMBER_ID, PropertyDef)
        assert isinstance(WHATSAPP_CREDENTIAL_NAME, PropertyDef)
        assert isinstance(WHATSAPP_TO, PropertyDef)

    def test_telegram_constants_tab_placement(self):
        """Connection-related constants should be in 'connection' tab."""
        assert TELEGRAM_BOT_TOKEN.tab == "connection"
        assert TELEGRAM_CREDENTIAL_NAME.tab == "connection"

    def test_whatsapp_constants_tab_placement(self):
        """Connection-related constants should be in 'connection' tab."""
        assert WHATSAPP_ACCESS_TOKEN.tab == "connection"
        assert WHATSAPP_CREDENTIAL_NAME.tab == "connection"
        assert WHATSAPP_PHONE_NUMBER_ID.tab == "connection"

    def test_chat_id_is_required(self):
        """Chat ID should be required."""
        assert TELEGRAM_CHAT_ID.required is True

    def test_to_is_required(self):
        """WhatsApp 'to' field should be required."""
        assert WHATSAPP_TO.required is True


class TestSchemaDefaultConfig:
    """Test schema generates correct default configurations."""

    def test_telegram_send_message_defaults(self):
        """TelegramSendMessageNode should have correct defaults."""
        schema = TelegramSendMessageNode.__node_schema__
        defaults = schema.get_default_config()

        assert defaults["bot_token"] == ""
        assert defaults["credential_name"] == ""
        assert defaults["chat_id"] == ""
        assert defaults["text"] == ""
        assert defaults["parse_mode"] == ""
        assert defaults["disable_notification"] is False

    def test_whatsapp_send_message_defaults(self):
        """WhatsAppSendMessageNode should have correct defaults."""
        schema = WhatsAppSendMessageNode.__node_schema__
        defaults = schema.get_default_config()

        assert defaults["access_token"] == ""
        assert defaults["phone_number_id"] == ""
        assert defaults["credential_name"] == ""
        assert defaults["to"] == ""
        assert defaults["text"] == ""
        assert defaults["preview_url"] is False


class TestSchemaValidation:
    """Test schema validation logic."""

    def test_valid_telegram_config(self):
        """Valid Telegram config should pass validation."""
        schema = TelegramSendMessageNode.__node_schema__
        config = {
            "bot_token": "123456:ABC",
            "chat_id": "123456789",
            "text": "Hello World",
        }
        valid, error = schema.validate_config(config)
        assert valid is True
        # error is empty string on success, not None
        assert error == "" or error is None

    def test_valid_whatsapp_config(self):
        """Valid WhatsApp config should pass validation."""
        schema = WhatsAppSendMessageNode.__node_schema__
        config = {
            "access_token": "token123",
            "phone_number_id": "12345",
            "to": "+1234567890",
            "text": "Hello World",
        }
        valid, error = schema.validate_config(config)
        assert valid is True
        # error is empty string on success, not None
        assert error == "" or error is None

    def test_missing_required_field_fails(self):
        """Missing required field should fail validation."""
        schema = TelegramSendMessageNode.__node_schema__
        config = {
            "bot_token": "123456:ABC",
            # Missing chat_id (required)
            "text": "Hello",
        }
        valid, error = schema.validate_config(config)
        assert valid is False
        # Error message contains label "Chat ID" not field name
        assert "Chat ID" in error or "chat_id" in error

    def test_invalid_choice_fails(self):
        """Invalid choice value should fail validation."""
        schema = TelegramSendMessageNode.__node_schema__
        config = {
            "chat_id": "123",
            "text": "Hello",
            "parse_mode": "InvalidMode",  # Not in choices
        }
        valid, error = schema.validate_config(config)
        assert valid is False
        # Error mentions "Parse Mode" (label) or "parse_mode" or the value options
        assert "Parse Mode" in error or "parse_mode" in error or "InvalidMode" in error


class TestExecPorts:
    """Test nodes have execution ports via @executable_node decorator."""

    @pytest.mark.parametrize(
        "node_class",
        [
            TelegramSendMessageNode,
            TelegramSendPhotoNode,
            WhatsAppSendMessageNode,
            WhatsAppSendImageNode,
        ],
    )
    def test_node_has_exec_ports(self, node_class):
        """Nodes should have exec_in and exec_out ports."""
        node = node_class(node_id="test_node")
        # input_ports and output_ports are dicts, get keys
        input_port_names = list(node.input_ports.keys())
        output_port_names = list(node.output_ports.keys())
        all_port_names = input_port_names + output_port_names
        assert "exec_in" in all_port_names
        assert "exec_out" in all_port_names
