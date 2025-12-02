"""
Tests for WhatsAppTriggerNode.

Tests:
- Trigger type and category
- Output port definitions
- Configuration parsing (phone number filters, message types)
- Trigger config generation
- Payload population
- Edge cases (empty filters, status updates)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.triggers.base import TriggerType


class TestWhatsAppTriggerNodeBasics:
    """Basic tests for WhatsAppTriggerNode structure."""

    def test_whatsapp_node_has_no_exec_in(self) -> None:
        """Trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        assert "exec_in" not in node.input_ports
        assert "exec_out" in node.output_ports

    def test_whatsapp_node_is_trigger_node(self) -> None:
        """WhatsAppTriggerNode has is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        assert WhatsAppTriggerNode.is_trigger_node is True

    def test_whatsapp_node_category(self) -> None:
        """WhatsAppTriggerNode is in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")
        assert node.category == "triggers"

    def test_whatsapp_returns_correct_trigger_type(self) -> None:
        """WhatsAppTriggerNode returns WHATSAPP trigger type."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        assert node.get_trigger_type() == TriggerType.WHATSAPP

    def test_whatsapp_trigger_display_name(self) -> None:
        """WhatsAppTriggerNode has correct display name."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        assert WhatsAppTriggerNode.trigger_display_name == "WhatsApp"


class TestWhatsAppTriggerNodeOutputPorts:
    """Tests for WhatsAppTriggerNode output port definitions."""

    def test_whatsapp_has_message_output_ports(self) -> None:
        """WhatsAppTriggerNode has all required output ports."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        expected_ports = [
            "message_id",
            "from_number",
            "to_number",
            "timestamp",
            "text",
            "message_type",
            "media_id",
            "media_url",
            "caption",
            "contact_name",
            "raw_message",
            "exec_out",
        ]

        for port_name in expected_ports:
            assert port_name in node.output_ports, f"Missing port: {port_name}"

    def test_whatsapp_output_port_count(self) -> None:
        """WhatsAppTriggerNode has correct number of output ports."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        # 11 payload ports + 1 exec_out = 12 total
        assert len(node.output_ports) == 12


class TestWhatsAppTriggerNodeConfig:
    """Tests for WhatsAppTriggerNode configuration handling."""

    def test_whatsapp_config_with_defaults(self) -> None:
        """WhatsAppTriggerNode handles default configuration."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1", config={})

        config = node.get_trigger_config()

        assert config["access_token"] == ""
        assert config["phone_number_id"] == ""
        assert config["credential_name"] == ""
        assert config["verify_token"] == ""
        assert config["webhook_path"] == "/whatsapp/webhook"
        assert config["filter_phone_numbers"] == []
        assert config["message_types"] == [
            "text",
            "image",
            "document",
            "audio",
            "video",
            "location",
        ]
        assert config["include_status_updates"] is False

    def test_whatsapp_config_with_credentials(self) -> None:
        """WhatsAppTriggerNode parses credentials correctly."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(
            node_id="whatsapp_1",
            config={
                "access_token": "EAAxxxxxxxx",
                "phone_number_id": "123456789012345",
                "verify_token": "my_secret_token",
            },
        )

        config = node.get_trigger_config()

        assert config["access_token"] == "EAAxxxxxxxx"
        assert config["phone_number_id"] == "123456789012345"
        assert config["verify_token"] == "my_secret_token"

    def test_whatsapp_config_parses_phone_numbers(self) -> None:
        """WhatsAppTriggerNode parses comma-separated phone numbers."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(
            node_id="whatsapp_1",
            config={"filter_phone_numbers": "+1234567890, +0987654321, +5551234567"},
        )

        config = node.get_trigger_config()

        assert config["filter_phone_numbers"] == [
            "+1234567890",
            "+0987654321",
            "+5551234567",
        ]

    def test_whatsapp_config_parses_message_types(self) -> None:
        """WhatsAppTriggerNode parses comma-separated message types."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(
            node_id="whatsapp_1",
            config={"message_types": "text, image, document"},
        )

        config = node.get_trigger_config()

        assert config["message_types"] == ["text", "image", "document"]

    def test_whatsapp_config_handles_empty_phone_filter(self) -> None:
        """WhatsAppTriggerNode handles empty phone filter gracefully."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(
            node_id="whatsapp_1",
            config={"filter_phone_numbers": ""},
        )

        config = node.get_trigger_config()

        assert config["filter_phone_numbers"] == []
        # message_types has @node_schema default
        assert config["message_types"] == [
            "text",
            "image",
            "document",
            "audio",
            "video",
            "location",
        ]

    def test_whatsapp_config_include_status_updates(self) -> None:
        """WhatsAppTriggerNode handles status updates flag."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(
            node_id="whatsapp_1",
            config={"include_status_updates": True},
        )

        config = node.get_trigger_config()

        assert config["include_status_updates"] is True


class TestWhatsAppTriggerNodeTriggerConfig:
    """Tests for WhatsAppTriggerNode trigger config creation."""

    def test_whatsapp_creates_valid_trigger_config(self) -> None:
        """WhatsAppTriggerNode creates valid BaseTriggerConfig."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(
            node_id="whatsapp_1",
            config={
                "access_token": "test_token",
                "phone_number_id": "123456",
                "verify_token": "verify_me",
            },
        )

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", scenario_id="sc_1"
        )

        assert trigger_config.trigger_type == TriggerType.WHATSAPP
        assert trigger_config.workflow_id == "wf_1"
        assert trigger_config.scenario_id == "sc_1"
        assert trigger_config.config["access_token"] == "test_token"
        assert trigger_config.config["phone_number_id"] == "123456"
        assert trigger_config.config["verify_token"] == "verify_me"

    def test_whatsapp_trigger_config_id_generation(self) -> None:
        """WhatsAppTriggerNode generates trigger ID from node ID."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="my_whatsapp_trigger")

        trigger_config = node.create_trigger_config(workflow_id="wf_1")

        assert trigger_config.id == "trig_my_whatsapp_trigger"


class TestWhatsAppTriggerNodeExecution:
    """Tests for WhatsAppTriggerNode execution."""

    @pytest.mark.asyncio
    async def test_whatsapp_executes_as_passthrough(self, execution_context) -> None:
        """WhatsAppTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "data" in result


class TestWhatsAppTriggerNodePayload:
    """Tests for WhatsAppTriggerNode payload population."""

    def test_whatsapp_populate_from_trigger_event(
        self, sample_whatsapp_payload
    ) -> None:
        """WhatsAppTriggerNode populates output ports from trigger payload."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")
        node.populate_from_trigger_event(sample_whatsapp_payload)

        assert node.output_ports["message_id"].get_value() == "wamid.test123"
        assert node.output_ports["from_number"].get_value() == "+15551234567"
        assert node.output_ports["to_number"].get_value() == "+15557654321"
        assert node.output_ports["text"].get_value() == "Hello from WhatsApp!"
        assert node.output_ports["message_type"].get_value() == "text"
        assert node.output_ports["contact_name"].get_value() == "Test User"

    def test_whatsapp_populate_ignores_unknown_fields(self) -> None:
        """WhatsAppTriggerNode ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        payload = {
            "text": "Hello",
            "unknown_field": "should_be_ignored",
        }

        # Should not raise
        node.populate_from_trigger_event(payload)

        assert node.output_ports["text"].get_value() == "Hello"

    def test_whatsapp_populate_media_message(self) -> None:
        """WhatsAppTriggerNode handles media message payload."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        payload = {
            "message_id": "wamid.media123",
            "from_number": "+15551234567",
            "message_type": "image",
            "media_id": "media_id_123",
            "media_url": "https://example.com/image.jpg",
            "caption": "Check out this image!",
        }

        node.populate_from_trigger_event(payload)

        assert node.output_ports["message_type"].get_value() == "image"
        assert node.output_ports["media_id"].get_value() == "media_id_123"
        assert node.output_ports["caption"].get_value() == "Check out this image!"


class TestWhatsAppTriggerNodeListeningState:
    """Tests for WhatsAppTriggerNode listening state."""

    def test_whatsapp_initially_not_listening(self) -> None:
        """WhatsAppTriggerNode starts in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        assert node.is_listening is False

    def test_whatsapp_set_listening_state(self) -> None:
        """WhatsAppTriggerNode listening state can be toggled."""
        from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode

        node = WhatsAppTriggerNode(node_id="whatsapp_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
