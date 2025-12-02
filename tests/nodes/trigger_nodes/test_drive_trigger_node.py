"""
Tests for DriveTriggerNode.

Tests:
- Trigger type and category
- Output port definitions
- Configuration parsing (event types, file types, MIME types)
- Trigger config generation
- Payload population
- Edge cases (empty filters, name patterns)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.triggers.base import TriggerType


class TestDriveTriggerNodeBasics:
    """Basic tests for DriveTriggerNode structure."""

    def test_drive_node_has_no_exec_in(self) -> None:
        """Trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        assert "exec_in" not in node.input_ports
        assert "exec_out" in node.output_ports

    def test_drive_node_is_trigger_node(self) -> None:
        """DriveTriggerNode has is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        assert DriveTriggerNode.is_trigger_node is True

    def test_drive_node_category(self) -> None:
        """DriveTriggerNode is in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")
        assert node.category == "triggers"

    def test_drive_returns_correct_trigger_type(self) -> None:
        """DriveTriggerNode returns DRIVE trigger type."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        assert node.get_trigger_type() == TriggerType.DRIVE

    def test_drive_trigger_display_name(self) -> None:
        """DriveTriggerNode has correct display name."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        assert DriveTriggerNode.trigger_display_name == "Google Drive"


class TestDriveTriggerNodeOutputPorts:
    """Tests for DriveTriggerNode output port definitions."""

    def test_drive_has_file_output_ports(self) -> None:
        """DriveTriggerNode has all required output ports."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        expected_ports = [
            "file_id",
            "file_name",
            "mime_type",
            "event_type",
            "modified_time",
            "size",
            "parent_id",
            "parent_name",
            "web_view_link",
            "download_url",
            "changed_by",
            "raw_change",
            "exec_out",
        ]

        for port_name in expected_ports:
            assert port_name in node.output_ports, f"Missing port: {port_name}"

    def test_drive_output_port_count(self) -> None:
        """DriveTriggerNode has correct number of output ports."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        # 12 payload ports + 1 exec_out = 13 total
        assert len(node.output_ports) == 13


class TestDriveTriggerNodeConfig:
    """Tests for DriveTriggerNode configuration handling."""

    def test_drive_config_with_defaults(self) -> None:
        """DriveTriggerNode handles default configuration."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1", config={})

        config = node.get_trigger_config()

        assert config["credential_name"] == "google"
        assert config["polling_interval"] == 60
        assert config["folder_id"] == ""
        assert config["include_subfolders"] is True
        assert config["event_types"] == ["created", "modified"]
        assert config["file_types"] == []
        assert config["mime_types"] == []
        assert config["name_pattern"] == ""
        assert config["ignore_own_changes"] is True

    def test_drive_config_with_custom_values(self) -> None:
        """DriveTriggerNode parses custom configuration."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={
                "credential_name": "my_google",
                "polling_interval": 120,
                "folder_id": "folder123",
                "include_subfolders": False,
            },
        )

        config = node.get_trigger_config()

        assert config["credential_name"] == "my_google"
        assert config["polling_interval"] == 120
        assert config["folder_id"] == "folder123"
        assert config["include_subfolders"] is False

    def test_drive_config_parses_event_types(self) -> None:
        """DriveTriggerNode parses comma-separated event types."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={"event_types": "created, modified, deleted, moved"},
        )

        config = node.get_trigger_config()

        assert config["event_types"] == ["created", "modified", "deleted", "moved"]

    def test_drive_config_parses_file_types(self) -> None:
        """DriveTriggerNode parses comma-separated file extensions."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={"file_types": ".pdf, xlsx, .docx"},  # Mixed with/without dots
        )

        config = node.get_trigger_config()

        # Dots should be stripped
        assert config["file_types"] == ["pdf", "xlsx", "docx"]

    def test_drive_config_parses_mime_types(self) -> None:
        """DriveTriggerNode parses comma-separated MIME types."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={"mime_types": "application/pdf, image/*, text/plain"},
        )

        config = node.get_trigger_config()

        assert config["mime_types"] == ["application/pdf", "image/*", "text/plain"]

    def test_drive_config_handles_empty_file_and_mime_types(self) -> None:
        """DriveTriggerNode handles empty file_types and mime_types gracefully."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={
                "file_types": "  ",  # Whitespace only
                "mime_types": ",,,",  # Empty entries
            },
        )

        config = node.get_trigger_config()

        # event_types has default "created,modified" from @node_schema
        assert config["event_types"] == ["created", "modified"]
        assert config["file_types"] == []
        assert config["mime_types"] == []

    def test_drive_config_name_pattern(self) -> None:
        """DriveTriggerNode handles name pattern configuration."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={"name_pattern": "Invoice_*.pdf"},
        )

        config = node.get_trigger_config()

        assert config["name_pattern"] == "Invoice_*.pdf"

    def test_drive_config_ignore_own_changes(self) -> None:
        """DriveTriggerNode handles ignore_own_changes configuration."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={"ignore_own_changes": False},
        )

        config = node.get_trigger_config()

        assert config["ignore_own_changes"] is False


class TestDriveTriggerNodeTriggerConfig:
    """Tests for DriveTriggerNode trigger config creation."""

    def test_drive_creates_valid_trigger_config(self) -> None:
        """DriveTriggerNode creates valid BaseTriggerConfig."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(
            node_id="drive_1",
            config={
                "credential_name": "google",
                "folder_id": "folder123",
                "event_types": "created,modified",
            },
        )

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", scenario_id="sc_1"
        )

        assert trigger_config.trigger_type == TriggerType.DRIVE
        assert trigger_config.workflow_id == "wf_1"
        assert trigger_config.scenario_id == "sc_1"
        assert trigger_config.config["folder_id"] == "folder123"
        assert trigger_config.config["event_types"] == ["created", "modified"]

    def test_drive_trigger_config_id_generation(self) -> None:
        """DriveTriggerNode generates trigger ID from node ID."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="my_drive_trigger")

        trigger_config = node.create_trigger_config(workflow_id="wf_1")

        assert trigger_config.id == "trig_my_drive_trigger"


class TestDriveTriggerNodeExecution:
    """Tests for DriveTriggerNode execution."""

    @pytest.mark.asyncio
    async def test_drive_executes_as_passthrough(self, execution_context) -> None:
        """DriveTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "data" in result


class TestDriveTriggerNodePayload:
    """Tests for DriveTriggerNode payload population."""

    def test_drive_populate_from_trigger_event(self, sample_drive_payload) -> None:
        """DriveTriggerNode populates output ports from trigger payload."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")
        node.populate_from_trigger_event(sample_drive_payload)

        assert node.output_ports["file_id"].get_value() == "file123abc"
        assert node.output_ports["file_name"].get_value() == "document.pdf"
        assert node.output_ports["mime_type"].get_value() == "application/pdf"
        assert node.output_ports["event_type"].get_value() == "created"
        assert node.output_ports["size"].get_value() == 102400
        assert node.output_ports["parent_id"].get_value() == "folder789"
        assert node.output_ports["changed_by"].get_value() == "user@example.com"

    def test_drive_populate_ignores_unknown_fields(self) -> None:
        """DriveTriggerNode ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        payload = {
            "file_name": "test.txt",
            "unknown_field": "should_be_ignored",
        }

        # Should not raise
        node.populate_from_trigger_event(payload)

        assert node.output_ports["file_name"].get_value() == "test.txt"

    def test_drive_populate_deleted_file(self) -> None:
        """DriveTriggerNode handles deleted file payload."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        payload = {
            "file_id": "deleted_file",
            "file_name": "old_document.pdf",
            "event_type": "deleted",
            "changed_by": "admin@example.com",
        }

        node.populate_from_trigger_event(payload)

        assert node.output_ports["event_type"].get_value() == "deleted"
        assert node.output_ports["changed_by"].get_value() == "admin@example.com"


class TestDriveTriggerNodeListeningState:
    """Tests for DriveTriggerNode listening state."""

    def test_drive_initially_not_listening(self) -> None:
        """DriveTriggerNode starts in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        assert node.is_listening is False

    def test_drive_set_listening_state(self) -> None:
        """DriveTriggerNode listening state can be toggled."""
        from casare_rpa.nodes.trigger_nodes import DriveTriggerNode

        node = DriveTriggerNode(node_id="drive_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
