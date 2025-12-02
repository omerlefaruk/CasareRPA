"""
Tests for SheetsTriggerNode.

Tests:
- Trigger type and category
- Output port definitions
- Configuration parsing (spreadsheet_id, range, watch columns)
- Trigger config generation
- Payload population
- Edge cases (empty filters, column uppercase conversion)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.triggers.base import TriggerType


class TestSheetsTriggerNodeBasics:
    """Basic tests for SheetsTriggerNode structure."""

    def test_sheets_node_has_no_exec_in(self) -> None:
        """Trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        assert "exec_in" not in node.input_ports
        assert "exec_out" in node.output_ports

    def test_sheets_node_is_trigger_node(self) -> None:
        """SheetsTriggerNode has is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        assert SheetsTriggerNode.is_trigger_node is True

    def test_sheets_node_category(self) -> None:
        """SheetsTriggerNode is in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")
        assert node.category == "triggers"

    def test_sheets_returns_correct_trigger_type(self) -> None:
        """SheetsTriggerNode returns SHEETS trigger type."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        assert node.get_trigger_type() == TriggerType.SHEETS

    def test_sheets_trigger_display_name(self) -> None:
        """SheetsTriggerNode has correct display name."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        assert SheetsTriggerNode.trigger_display_name == "Google Sheets"


class TestSheetsTriggerNodeOutputPorts:
    """Tests for SheetsTriggerNode output port definitions."""

    def test_sheets_has_sheet_output_ports(self) -> None:
        """SheetsTriggerNode has all required output ports."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        expected_ports = [
            "spreadsheet_id",
            "sheet_name",
            "event_type",
            "row_number",
            "column",
            "old_value",
            "new_value",
            "row_data",
            "row_dict",
            "changed_cells",
            "timestamp",
            "raw_data",
            "exec_out",
        ]

        for port_name in expected_ports:
            assert port_name in node.output_ports, f"Missing port: {port_name}"

    def test_sheets_output_port_count(self) -> None:
        """SheetsTriggerNode has correct number of output ports."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        # 12 payload ports + 1 exec_out = 13 total
        assert len(node.output_ports) == 13


class TestSheetsTriggerNodeConfig:
    """Tests for SheetsTriggerNode configuration handling."""

    def test_sheets_config_with_defaults(self) -> None:
        """SheetsTriggerNode handles default configuration."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1", config={})

        config = node.get_trigger_config()

        assert config["credential_name"] == "google"
        assert config["spreadsheet_id"] == ""
        assert config["sheet_name"] == "Sheet1"
        assert config["range"] == ""
        assert config["polling_interval"] == 30
        assert config["trigger_on_new_row"] is True
        assert config["trigger_on_cell_change"] is True
        assert config["trigger_on_delete"] is False
        assert config["watch_columns"] == []
        assert config["ignore_empty_rows"] is True

    def test_sheets_config_with_custom_values(self) -> None:
        """SheetsTriggerNode parses custom configuration."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(
            node_id="sheets_1",
            config={
                "credential_name": "my_google",
                "spreadsheet_id": "1ABC123xyz",
                "sheet_name": "Data",
                "range": "A1:Z1000",
                "polling_interval": 60,
            },
        )

        config = node.get_trigger_config()

        assert config["credential_name"] == "my_google"
        assert config["spreadsheet_id"] == "1ABC123xyz"
        assert config["sheet_name"] == "Data"
        assert config["range"] == "A1:Z1000"
        assert config["polling_interval"] == 60

    def test_sheets_config_parses_watch_columns(self) -> None:
        """SheetsTriggerNode parses comma-separated columns and converts to uppercase."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(
            node_id="sheets_1",
            config={"watch_columns": "a, b, C, d"},  # Mixed case
        )

        config = node.get_trigger_config()

        # All columns should be uppercase
        assert config["watch_columns"] == ["A", "B", "C", "D"]

    def test_sheets_config_handles_empty_watch_columns(self) -> None:
        """SheetsTriggerNode handles empty watch_columns gracefully."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(
            node_id="sheets_1",
            config={"watch_columns": ""},
        )

        config = node.get_trigger_config()

        assert config["watch_columns"] == []

    def test_sheets_config_trigger_on_flags(self) -> None:
        """SheetsTriggerNode handles trigger_on flags configuration."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(
            node_id="sheets_1",
            config={
                "trigger_on_new_row": False,
                "trigger_on_cell_change": True,
                "trigger_on_delete": True,
            },
        )

        config = node.get_trigger_config()

        assert config["trigger_on_new_row"] is False
        assert config["trigger_on_cell_change"] is True
        assert config["trigger_on_delete"] is True

    def test_sheets_config_ignore_empty_rows(self) -> None:
        """SheetsTriggerNode handles ignore_empty_rows configuration."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(
            node_id="sheets_1",
            config={"ignore_empty_rows": False},
        )

        config = node.get_trigger_config()

        assert config["ignore_empty_rows"] is False


class TestSheetsTriggerNodeTriggerConfig:
    """Tests for SheetsTriggerNode trigger config creation."""

    def test_sheets_creates_valid_trigger_config(self) -> None:
        """SheetsTriggerNode creates valid BaseTriggerConfig."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(
            node_id="sheets_1",
            config={
                "credential_name": "google",
                "spreadsheet_id": "spreadsheet123",
                "sheet_name": "Sheet1",
            },
        )

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", scenario_id="sc_1"
        )

        assert trigger_config.trigger_type == TriggerType.SHEETS
        assert trigger_config.workflow_id == "wf_1"
        assert trigger_config.scenario_id == "sc_1"
        assert trigger_config.config["spreadsheet_id"] == "spreadsheet123"
        assert trigger_config.config["sheet_name"] == "Sheet1"

    def test_sheets_trigger_config_id_generation(self) -> None:
        """SheetsTriggerNode generates trigger ID from node ID."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="my_sheets_trigger")

        trigger_config = node.create_trigger_config(workflow_id="wf_1")

        assert trigger_config.id == "trig_my_sheets_trigger"


class TestSheetsTriggerNodeExecution:
    """Tests for SheetsTriggerNode execution."""

    @pytest.mark.asyncio
    async def test_sheets_executes_as_passthrough(self, execution_context) -> None:
        """SheetsTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "data" in result


class TestSheetsTriggerNodePayload:
    """Tests for SheetsTriggerNode payload population."""

    def test_sheets_populate_from_trigger_event(self, sample_sheets_payload) -> None:
        """SheetsTriggerNode populates output ports from trigger payload."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")
        node.populate_from_trigger_event(sample_sheets_payload)

        assert node.output_ports["spreadsheet_id"].get_value() == "spreadsheet123"
        assert node.output_ports["sheet_name"].get_value() == "Sheet1"
        assert node.output_ports["event_type"].get_value() == "new_row"
        assert node.output_ports["row_number"].get_value() == 10
        assert node.output_ports["column"].get_value() == "A"
        assert node.output_ports["new_value"].get_value() == "New Data"
        assert len(node.output_ports["row_data"].get_value()) == 3
        assert len(node.output_ports["changed_cells"].get_value()) == 3

    def test_sheets_populate_ignores_unknown_fields(self) -> None:
        """SheetsTriggerNode ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        payload = {
            "sheet_name": "Test Sheet",
            "unknown_field": "should_be_ignored",
        }

        # Should not raise
        node.populate_from_trigger_event(payload)

        assert node.output_ports["sheet_name"].get_value() == "Test Sheet"

    def test_sheets_populate_cell_change_event(self) -> None:
        """SheetsTriggerNode handles cell change event payload."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        payload = {
            "spreadsheet_id": "spreadsheet456",
            "sheet_name": "Data",
            "event_type": "cell_change",
            "row_number": 5,
            "column": "B",
            "old_value": "Old Data",
            "new_value": "Updated Data",
            "changed_cells": ["B5"],
        }

        node.populate_from_trigger_event(payload)

        assert node.output_ports["event_type"].get_value() == "cell_change"
        assert node.output_ports["old_value"].get_value() == "Old Data"
        assert node.output_ports["new_value"].get_value() == "Updated Data"

    def test_sheets_populate_row_dict(self) -> None:
        """SheetsTriggerNode handles row_dict payload."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        payload = {
            "spreadsheet_id": "spreadsheet789",
            "row_dict": {
                "Name": "John",
                "Email": "john@example.com",
                "Status": "Active",
            },
        }

        node.populate_from_trigger_event(payload)

        row_dict = node.output_ports["row_dict"].get_value()
        assert row_dict["Name"] == "John"
        assert row_dict["Email"] == "john@example.com"


class TestSheetsTriggerNodeListeningState:
    """Tests for SheetsTriggerNode listening state."""

    def test_sheets_initially_not_listening(self) -> None:
        """SheetsTriggerNode starts in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        assert node.is_listening is False

    def test_sheets_set_listening_state(self) -> None:
        """SheetsTriggerNode listening state can be toggled."""
        from casare_rpa.nodes.trigger_nodes import SheetsTriggerNode

        node = SheetsTriggerNode(node_id="sheets_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
