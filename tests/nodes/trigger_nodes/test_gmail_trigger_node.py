"""
Tests for GmailTriggerNode.

Tests:
- Trigger type and category
- Output port definitions
- Configuration parsing (label IDs, query, filters)
- Trigger config generation
- Payload population
- Edge cases (empty filters, attachments)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.triggers.base import TriggerType


class TestGmailTriggerNodeBasics:
    """Basic tests for GmailTriggerNode structure."""

    def test_gmail_node_has_no_exec_in(self) -> None:
        """Trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        assert "exec_in" not in node.input_ports
        assert "exec_out" in node.output_ports

    def test_gmail_node_is_trigger_node(self) -> None:
        """GmailTriggerNode has is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        assert GmailTriggerNode.is_trigger_node is True

    def test_gmail_node_category(self) -> None:
        """GmailTriggerNode is in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")
        assert node.category == "triggers"

    def test_gmail_returns_correct_trigger_type(self) -> None:
        """GmailTriggerNode returns GMAIL trigger type."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        assert node.get_trigger_type() == TriggerType.GMAIL

    def test_gmail_trigger_display_name(self) -> None:
        """GmailTriggerNode has correct display name."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        assert GmailTriggerNode.trigger_display_name == "Gmail"


class TestGmailTriggerNodeOutputPorts:
    """Tests for GmailTriggerNode output port definitions."""

    def test_gmail_has_email_output_ports(self) -> None:
        """GmailTriggerNode has all required output ports."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        expected_ports = [
            "message_id",
            "thread_id",
            "subject",
            "from_email",
            "from_name",
            "to_email",
            "date",
            "snippet",
            "body_text",
            "body_html",
            "labels",
            "has_attachments",
            "attachments",
            "raw_message",
            "exec_out",
        ]

        for port_name in expected_ports:
            assert port_name in node.output_ports, f"Missing port: {port_name}"

    def test_gmail_output_port_count(self) -> None:
        """GmailTriggerNode has correct number of output ports."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        # 14 payload ports + 1 exec_out = 15 total
        assert len(node.output_ports) == 15


class TestGmailTriggerNodeConfig:
    """Tests for GmailTriggerNode configuration handling."""

    def test_gmail_config_with_defaults(self) -> None:
        """GmailTriggerNode handles default configuration."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1", config={})

        config = node.get_trigger_config()

        assert config["credential_name"] == "google"
        assert config["polling_interval"] == 60
        assert config["label_ids"] == ["INBOX"]
        assert config["query"] == "is:unread"
        assert config["from_filter"] == ""
        assert config["subject_contains"] == ""
        assert config["mark_as_read"] is True
        assert config["include_attachments"] is True
        assert config["max_results"] == 10

    def test_gmail_config_with_custom_values(self) -> None:
        """GmailTriggerNode parses custom configuration."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(
            node_id="gmail_1",
            config={
                "credential_name": "my_google",
                "polling_interval": 120,
                "query": "is:unread from:important@example.com",
                "from_filter": "boss@company.com",
                "subject_contains": "URGENT",
            },
        )

        config = node.get_trigger_config()

        assert config["credential_name"] == "my_google"
        assert config["polling_interval"] == 120
        assert config["query"] == "is:unread from:important@example.com"
        assert config["from_filter"] == "boss@company.com"
        assert config["subject_contains"] == "URGENT"

    def test_gmail_config_parses_label_ids(self) -> None:
        """GmailTriggerNode parses comma-separated label IDs."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(
            node_id="gmail_1",
            config={"label_ids": "INBOX, IMPORTANT, STARRED"},
        )

        config = node.get_trigger_config()

        assert config["label_ids"] == ["INBOX", "IMPORTANT", "STARRED"]

    def test_gmail_config_default_label_ids(self) -> None:
        """GmailTriggerNode defaults to INBOX label."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1", config={})

        config = node.get_trigger_config()

        # @node_schema default is "INBOX"
        assert config["label_ids"] == ["INBOX"]

    def test_gmail_config_attachment_settings(self) -> None:
        """GmailTriggerNode handles attachment settings."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(
            node_id="gmail_1",
            config={
                "include_attachments": False,
                "mark_as_read": False,
            },
        )

        config = node.get_trigger_config()

        assert config["include_attachments"] is False
        assert config["mark_as_read"] is False

    def test_gmail_config_max_results(self) -> None:
        """GmailTriggerNode handles max_results configuration."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(
            node_id="gmail_1",
            config={"max_results": 50},
        )

        config = node.get_trigger_config()

        assert config["max_results"] == 50


class TestGmailTriggerNodeTriggerConfig:
    """Tests for GmailTriggerNode trigger config creation."""

    def test_gmail_creates_valid_trigger_config(self) -> None:
        """GmailTriggerNode creates valid BaseTriggerConfig."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(
            node_id="gmail_1",
            config={
                "credential_name": "google",
                "polling_interval": 30,
                "query": "is:unread",
            },
        )

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", scenario_id="sc_1"
        )

        assert trigger_config.trigger_type == TriggerType.GMAIL
        assert trigger_config.workflow_id == "wf_1"
        assert trigger_config.scenario_id == "sc_1"
        assert trigger_config.config["credential_name"] == "google"
        assert trigger_config.config["polling_interval"] == 30

    def test_gmail_trigger_config_id_generation(self) -> None:
        """GmailTriggerNode generates trigger ID from node ID."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="my_gmail_trigger")

        trigger_config = node.create_trigger_config(workflow_id="wf_1")

        assert trigger_config.id == "trig_my_gmail_trigger"


class TestGmailTriggerNodeExecution:
    """Tests for GmailTriggerNode execution."""

    @pytest.mark.asyncio
    async def test_gmail_executes_as_passthrough(self, execution_context) -> None:
        """GmailTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "data" in result


class TestGmailTriggerNodePayload:
    """Tests for GmailTriggerNode payload population."""

    def test_gmail_populate_from_trigger_event(self, sample_gmail_payload) -> None:
        """GmailTriggerNode populates output ports from trigger payload."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")
        node.populate_from_trigger_event(sample_gmail_payload)

        assert node.output_ports["message_id"].get_value() == "msg123abc"
        assert node.output_ports["thread_id"].get_value() == "thread456def"
        assert node.output_ports["subject"].get_value() == "Test Email Subject"
        assert node.output_ports["from_email"].get_value() == "sender@example.com"
        assert node.output_ports["from_name"].get_value() == "Test Sender"
        assert node.output_ports["body_text"].get_value() == "Full email body text"
        assert node.output_ports["has_attachments"].get_value() is True
        assert len(node.output_ports["attachments"].get_value()) == 1

    def test_gmail_populate_ignores_unknown_fields(self) -> None:
        """GmailTriggerNode ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        payload = {
            "subject": "Test Subject",
            "unknown_field": "should_be_ignored",
        }

        # Should not raise
        node.populate_from_trigger_event(payload)

        assert node.output_ports["subject"].get_value() == "Test Subject"

    def test_gmail_populate_email_without_attachments(self) -> None:
        """GmailTriggerNode handles email without attachments."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        payload = {
            "message_id": "msg456",
            "subject": "Simple Email",
            "from_email": "sender@example.com",
            "body_text": "Just text content",
            "has_attachments": False,
            "attachments": [],
        }

        node.populate_from_trigger_event(payload)

        assert node.output_ports["has_attachments"].get_value() is False
        assert node.output_ports["attachments"].get_value() == []


class TestGmailTriggerNodeListeningState:
    """Tests for GmailTriggerNode listening state."""

    def test_gmail_initially_not_listening(self) -> None:
        """GmailTriggerNode starts in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        assert node.is_listening is False

    def test_gmail_set_listening_state(self) -> None:
        """GmailTriggerNode listening state can be toggled."""
        from casare_rpa.nodes.trigger_nodes import GmailTriggerNode

        node = GmailTriggerNode(node_id="gmail_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
