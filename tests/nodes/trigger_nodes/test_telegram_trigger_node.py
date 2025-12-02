"""
Tests for TelegramTriggerNode.

Tests:
- Trigger type and category
- Output port definitions
- Configuration parsing (comma-separated filters)
- Trigger config generation
- Payload population
- Edge cases (empty filters, negative chat IDs)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.triggers.base import TriggerType


class TestTelegramTriggerNodeBasics:
    """Basic tests for TelegramTriggerNode structure."""

    def test_telegram_node_has_no_exec_in(self) -> None:
        """Trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        assert "exec_in" not in node.input_ports
        assert "exec_out" in node.output_ports

    def test_telegram_node_is_trigger_node(self) -> None:
        """TelegramTriggerNode has is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        assert TelegramTriggerNode.is_trigger_node is True

    def test_telegram_node_category(self) -> None:
        """TelegramTriggerNode is in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")
        assert node.category == "triggers"

    def test_telegram_returns_correct_trigger_type(self) -> None:
        """TelegramTriggerNode returns TELEGRAM trigger type."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        assert node.get_trigger_type() == TriggerType.TELEGRAM

    def test_telegram_trigger_display_name(self) -> None:
        """TelegramTriggerNode has correct display name."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        assert TelegramTriggerNode.trigger_display_name == "Telegram"


class TestTelegramTriggerNodeOutputPorts:
    """Tests for TelegramTriggerNode output port definitions."""

    def test_telegram_has_message_output_ports(self) -> None:
        """TelegramTriggerNode has all required output ports."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        expected_ports = [
            "message_id",
            "chat_id",
            "user_id",
            "username",
            "first_name",
            "text",
            "is_command",
            "command",
            "command_args",
            "message_type",
            "raw_update",
            "exec_out",
        ]

        for port_name in expected_ports:
            assert port_name in node.output_ports, f"Missing port: {port_name}"

    def test_telegram_output_port_count(self) -> None:
        """TelegramTriggerNode has correct number of output ports."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        # 11 payload ports + 1 exec_out = 12 total
        assert len(node.output_ports) == 12


class TestTelegramTriggerNodeConfig:
    """Tests for TelegramTriggerNode configuration handling."""

    def test_telegram_config_with_defaults(self) -> None:
        """TelegramTriggerNode handles default configuration."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1", config={})

        config = node.get_trigger_config()

        assert config["bot_token"] == ""
        assert config["credential_name"] == ""
        assert config["mode"] == "auto"
        assert config["polling_interval"] == 2
        assert config["filter_chat_ids"] == []
        assert config["filter_user_ids"] == []
        assert config["commands_only"] is False
        assert config["filter_commands"] == []
        assert config["allowed_updates"] == ["message"]

    def test_telegram_config_with_bot_token(self) -> None:
        """TelegramTriggerNode parses bot token correctly."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={
                "bot_token": "123456:ABC-DEF",
                "mode": "webhook",
                "webhook_url": "https://example.com/webhook",
            },
        )

        config = node.get_trigger_config()

        assert config["bot_token"] == "123456:ABC-DEF"
        assert config["mode"] == "webhook"
        assert config["webhook_url"] == "https://example.com/webhook"

    def test_telegram_config_parses_chat_ids(self) -> None:
        """TelegramTriggerNode parses comma-separated chat IDs."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={"filter_chat_ids": "123456789, 987654321, -100123456789"},
        )

        config = node.get_trigger_config()

        assert config["filter_chat_ids"] == [123456789, 987654321, -100123456789]

    def test_telegram_config_parses_user_ids(self) -> None:
        """TelegramTriggerNode parses comma-separated user IDs."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={"filter_user_ids": "111, 222, 333"},
        )

        config = node.get_trigger_config()

        assert config["filter_user_ids"] == [111, 222, 333]

    def test_telegram_config_parses_commands(self) -> None:
        """TelegramTriggerNode parses comma-separated commands."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={
                "commands_only": True,
                "filter_commands": "/start, /help, run",  # Mixed with/without /
            },
        )

        config = node.get_trigger_config()

        assert config["commands_only"] is True
        assert config["filter_commands"] == ["start", "help", "run"]

    def test_telegram_config_parses_allowed_updates(self) -> None:
        """TelegramTriggerNode parses comma-separated allowed updates."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={"allowed_updates": "message, callback_query, inline_query"},
        )

        config = node.get_trigger_config()

        assert config["allowed_updates"] == [
            "message",
            "callback_query",
            "inline_query",
        ]

    def test_telegram_config_handles_empty_filters(self) -> None:
        """TelegramTriggerNode handles empty filter strings gracefully."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={
                "filter_chat_ids": "",
                "filter_user_ids": "  ",  # Whitespace only
                "filter_commands": ",,,",  # Empty entries
            },
        )

        config = node.get_trigger_config()

        assert config["filter_chat_ids"] == []
        assert config["filter_user_ids"] == []
        assert config["filter_commands"] == []

    def test_telegram_config_handles_invalid_chat_ids(self) -> None:
        """TelegramTriggerNode skips invalid chat ID entries."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={"filter_chat_ids": "123, abc, 456, not_a_number, 789"},
        )

        config = node.get_trigger_config()

        # Only valid numeric IDs should be included
        assert config["filter_chat_ids"] == [123, 456, 789]


class TestTelegramTriggerNodeTriggerConfig:
    """Tests for TelegramTriggerNode trigger config creation."""

    def test_telegram_creates_valid_trigger_config(self) -> None:
        """TelegramTriggerNode creates valid BaseTriggerConfig."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(
            node_id="telegram_1",
            config={
                "bot_token": "test_token",
                "mode": "polling",
                "polling_interval": 5,
            },
        )

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", scenario_id="sc_1"
        )

        assert trigger_config.trigger_type == TriggerType.TELEGRAM
        assert trigger_config.workflow_id == "wf_1"
        assert trigger_config.scenario_id == "sc_1"
        assert trigger_config.config["bot_token"] == "test_token"
        assert trigger_config.config["mode"] == "polling"
        assert trigger_config.config["polling_interval"] == 5

    def test_telegram_trigger_config_id_generation(self) -> None:
        """TelegramTriggerNode generates trigger ID from node ID."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="my_telegram_trigger")

        trigger_config = node.create_trigger_config(workflow_id="wf_1")

        assert trigger_config.id == "trig_my_telegram_trigger"

    def test_telegram_trigger_config_custom_id(self) -> None:
        """TelegramTriggerNode accepts custom trigger ID."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", trigger_id="custom_trigger_id"
        )

        assert trigger_config.id == "custom_trigger_id"


class TestTelegramTriggerNodeExecution:
    """Tests for TelegramTriggerNode execution."""

    @pytest.mark.asyncio
    async def test_telegram_executes_as_passthrough(self, execution_context) -> None:
        """TelegramTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "data" in result


class TestTelegramTriggerNodePayload:
    """Tests for TelegramTriggerNode payload population."""

    def test_telegram_populate_from_trigger_event(
        self, sample_telegram_payload
    ) -> None:
        """TelegramTriggerNode populates output ports from trigger payload."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")
        node.populate_from_trigger_event(sample_telegram_payload)

        assert node.output_ports["message_id"].get_value() == 12345
        assert node.output_ports["chat_id"].get_value() == 987654321
        assert node.output_ports["user_id"].get_value() == 111222333
        assert node.output_ports["username"].get_value() == "testuser"
        assert node.output_ports["text"].get_value() == "Hello bot!"
        assert node.output_ports["is_command"].get_value() is False
        assert node.output_ports["message_type"].get_value() == "text"

    def test_telegram_populate_ignores_unknown_fields(self) -> None:
        """TelegramTriggerNode ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        payload = {
            "text": "Hello",
            "unknown_field": "should_be_ignored",
            "another_unknown": 123,
        }

        # Should not raise
        node.populate_from_trigger_event(payload)

        assert node.output_ports["text"].get_value() == "Hello"

    def test_telegram_populate_partial_payload(self) -> None:
        """TelegramTriggerNode handles partial payload."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        # Only provide some fields
        payload = {
            "message_id": 999,
            "text": "Partial message",
        }

        node.populate_from_trigger_event(payload)

        assert node.output_ports["message_id"].get_value() == 999
        assert node.output_ports["text"].get_value() == "Partial message"


class TestTelegramTriggerNodeListeningState:
    """Tests for TelegramTriggerNode listening state."""

    def test_telegram_initially_not_listening(self) -> None:
        """TelegramTriggerNode starts in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        assert node.is_listening is False

    def test_telegram_set_listening_state(self) -> None:
        """TelegramTriggerNode listening state can be toggled."""
        from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode

        node = TelegramTriggerNode(node_id="telegram_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
