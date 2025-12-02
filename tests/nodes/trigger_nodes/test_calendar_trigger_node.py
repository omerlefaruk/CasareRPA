"""
Tests for CalendarTriggerNode.

Tests:
- Trigger type and category
- Output port definitions
- Configuration parsing (trigger_on, minutes_before, filters)
- Trigger config generation
- Payload population
- Edge cases (all-day events, minimum polling interval)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.triggers.base import TriggerType


class TestCalendarTriggerNodeBasics:
    """Basic tests for CalendarTriggerNode structure."""

    def test_calendar_node_has_no_exec_in(self) -> None:
        """Trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        assert "exec_in" not in node.input_ports
        assert "exec_out" in node.output_ports

    def test_calendar_node_is_trigger_node(self) -> None:
        """CalendarTriggerNode has is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        assert CalendarTriggerNode.is_trigger_node is True

    def test_calendar_node_category(self) -> None:
        """CalendarTriggerNode is in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")
        assert node.category == "triggers"

    def test_calendar_returns_correct_trigger_type(self) -> None:
        """CalendarTriggerNode returns CALENDAR trigger type."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        assert node.get_trigger_type() == TriggerType.CALENDAR

    def test_calendar_trigger_display_name(self) -> None:
        """CalendarTriggerNode has correct display name."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        assert CalendarTriggerNode.trigger_display_name == "Google Calendar"


class TestCalendarTriggerNodeOutputPorts:
    """Tests for CalendarTriggerNode output port definitions."""

    def test_calendar_has_event_output_ports(self) -> None:
        """CalendarTriggerNode has all required output ports."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        expected_ports = [
            "event_id",
            "calendar_id",
            "summary",
            "description",
            "start",
            "end",
            "location",
            "attendees",
            "event_type",
            "minutes_until_start",
            "organizer",
            "html_link",
            "status",
            "created",
            "updated",
            "exec_out",
        ]

        for port_name in expected_ports:
            assert port_name in node.output_ports, f"Missing port: {port_name}"

    def test_calendar_output_port_count(self) -> None:
        """CalendarTriggerNode has correct number of output ports."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        # 15 payload ports + 1 exec_out = 16 total
        assert len(node.output_ports) == 16


class TestCalendarTriggerNodeConfig:
    """Tests for CalendarTriggerNode configuration handling."""

    def test_calendar_config_with_defaults(self) -> None:
        """CalendarTriggerNode handles default configuration."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1", config={})

        config = node.get_trigger_config()

        # @node_schema defaults apply: credential_name="google"
        assert config["credential_name"] == "google"
        assert config["calendar_id"] == "primary"
        assert config["trigger_on"] == "upcoming"
        assert config["minutes_before"] == 15
        assert config["polling_interval"] == 60  # Minimum enforced to 30
        assert config["filter_summary"] == []
        assert config["filter_attendees"] == []
        assert config["include_all_day"] is True

    def test_calendar_config_with_custom_values(self) -> None:
        """CalendarTriggerNode parses custom configuration."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={
                "credential_name": "my_google",
                "calendar_id": "custom_calendar_id",
                "trigger_on": "created",
                "minutes_before": 30,
            },
        )

        config = node.get_trigger_config()

        assert config["credential_name"] == "my_google"
        assert config["calendar_id"] == "custom_calendar_id"
        assert config["trigger_on"] == "created"
        assert config["minutes_before"] == 30

    def test_calendar_config_parses_summary_filter(self) -> None:
        """CalendarTriggerNode parses comma-separated summary keywords."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={"filter_summary": "Meeting, Call, Sync"},
        )

        config = node.get_trigger_config()

        assert config["filter_summary"] == ["Meeting", "Call", "Sync"]

    def test_calendar_config_parses_attendee_filter(self) -> None:
        """CalendarTriggerNode parses comma-separated attendee emails."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={"filter_attendees": "user1@example.com, user2@example.com"},
        )

        config = node.get_trigger_config()

        assert config["filter_attendees"] == ["user1@example.com", "user2@example.com"]

    def test_calendar_config_handles_empty_filters(self) -> None:
        """CalendarTriggerNode handles empty filter strings gracefully."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={
                "filter_summary": "",
                "filter_attendees": "  ",  # Whitespace only
            },
        )

        config = node.get_trigger_config()

        assert config["filter_summary"] == []
        assert config["filter_attendees"] == []

    def test_calendar_config_enforces_minimum_polling_interval(self) -> None:
        """CalendarTriggerNode enforces minimum polling interval of 30 seconds."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={"polling_interval": 10},  # Below minimum
        )

        config = node.get_trigger_config()

        # Should be clamped to minimum of 30
        assert config["polling_interval"] == 30

    def test_calendar_config_all_day_events(self) -> None:
        """CalendarTriggerNode handles all-day events configuration."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={"include_all_day": False},
        )

        config = node.get_trigger_config()

        assert config["include_all_day"] is False

    def test_calendar_config_trigger_on_options(self) -> None:
        """CalendarTriggerNode handles different trigger_on options."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        for trigger_on in ["upcoming", "created", "updated", "cancelled"]:
            node = CalendarTriggerNode(
                node_id="calendar_1",
                config={"trigger_on": trigger_on},
            )

            config = node.get_trigger_config()
            assert config["trigger_on"] == trigger_on


class TestCalendarTriggerNodeTriggerConfig:
    """Tests for CalendarTriggerNode trigger config creation."""

    def test_calendar_creates_valid_trigger_config(self) -> None:
        """CalendarTriggerNode creates valid BaseTriggerConfig."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(
            node_id="calendar_1",
            config={
                "credential_name": "google",
                "calendar_id": "primary",
                "trigger_on": "upcoming",
                "minutes_before": 15,
            },
        )

        trigger_config = node.create_trigger_config(
            workflow_id="wf_1", scenario_id="sc_1"
        )

        assert trigger_config.trigger_type == TriggerType.CALENDAR
        assert trigger_config.workflow_id == "wf_1"
        assert trigger_config.scenario_id == "sc_1"
        assert trigger_config.config["calendar_id"] == "primary"
        assert trigger_config.config["minutes_before"] == 15

    def test_calendar_trigger_config_id_generation(self) -> None:
        """CalendarTriggerNode generates trigger ID from node ID."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="my_calendar_trigger")

        trigger_config = node.create_trigger_config(workflow_id="wf_1")

        assert trigger_config.id == "trig_my_calendar_trigger"


class TestCalendarTriggerNodeExecution:
    """Tests for CalendarTriggerNode execution."""

    @pytest.mark.asyncio
    async def test_calendar_executes_as_passthrough(self, execution_context) -> None:
        """CalendarTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "data" in result


class TestCalendarTriggerNodePayload:
    """Tests for CalendarTriggerNode payload population."""

    def test_calendar_populate_from_trigger_event(
        self, sample_calendar_payload
    ) -> None:
        """CalendarTriggerNode populates output ports from trigger payload."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")
        node.populate_from_trigger_event(sample_calendar_payload)

        assert node.output_ports["event_id"].get_value() == "event123xyz"
        assert node.output_ports["calendar_id"].get_value() == "primary"
        assert node.output_ports["summary"].get_value() == "Team Meeting"
        assert node.output_ports["description"].get_value() == "Weekly sync meeting"
        assert node.output_ports["location"].get_value() == "Conference Room A"
        assert node.output_ports["event_type"].get_value() == "upcoming"
        assert node.output_ports["minutes_until_start"].get_value() == 15
        assert len(node.output_ports["attendees"].get_value()) == 2

    def test_calendar_populate_ignores_unknown_fields(self) -> None:
        """CalendarTriggerNode ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        payload = {
            "summary": "Test Event",
            "unknown_field": "should_be_ignored",
        }

        # Should not raise
        node.populate_from_trigger_event(payload)

        assert node.output_ports["summary"].get_value() == "Test Event"

    def test_calendar_populate_cancelled_event(self) -> None:
        """CalendarTriggerNode handles cancelled event payload."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        payload = {
            "event_id": "cancelled_event",
            "summary": "Cancelled Meeting",
            "event_type": "cancelled",
            "status": "cancelled",
        }

        node.populate_from_trigger_event(payload)

        assert node.output_ports["event_type"].get_value() == "cancelled"
        assert node.output_ports["status"].get_value() == "cancelled"


class TestCalendarTriggerNodeListeningState:
    """Tests for CalendarTriggerNode listening state."""

    def test_calendar_initially_not_listening(self) -> None:
        """CalendarTriggerNode starts in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        assert node.is_listening is False

    def test_calendar_set_listening_state(self) -> None:
        """CalendarTriggerNode listening state can be toggled."""
        from casare_rpa.nodes.trigger_nodes import CalendarTriggerNode

        node = CalendarTriggerNode(node_id="calendar_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
