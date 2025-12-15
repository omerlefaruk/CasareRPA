"""
CasareRPA - Google Calendar Trigger Node

Trigger node that listens for Google Calendar events.
Workflow starts when an event matches the filters (upcoming, created, updated).
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    # Connection settings
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        placeholder="google",
        tooltip="Name of stored Google OAuth credential",
        tab="connection",
    ),
    # Calendar settings
    PropertyDef(
        "calendar_id",
        PropertyType.STRING,
        default="primary",
        label="Calendar ID",
        placeholder="primary",
        tooltip="Calendar ID to watch (primary = main calendar)",
    ),
    PropertyDef(
        "trigger_on",
        PropertyType.CHOICE,
        default="upcoming",
        choices=["upcoming", "created", "updated", "cancelled"],
        label="Trigger On",
        tooltip="When to trigger: upcoming events, newly created, updated, or cancelled",
    ),
    PropertyDef(
        "minutes_before",
        PropertyType.INTEGER,
        default=15,
        label="Minutes Before",
        tooltip="For upcoming: minutes before event to trigger",
    ),
    # Polling settings
    PropertyDef(
        "polling_interval",
        PropertyType.INTEGER,
        default=60,
        label="Polling Interval (sec)",
        tooltip="Seconds between checks (min 30)",
        tab="advanced",
    ),
    # Filters
    PropertyDef(
        "filter_summary",
        PropertyType.STRING,
        default="",
        label="Filter Summary",
        placeholder="Meeting,Call",
        tooltip="Comma-separated keywords in event summary (empty = all)",
    ),
    PropertyDef(
        "filter_attendees",
        PropertyType.STRING,
        default="",
        label="Filter Attendees",
        placeholder="user@example.com",
        tooltip="Only trigger if these attendees present (empty = all)",
    ),
    PropertyDef(
        "include_all_day",
        PropertyType.BOOLEAN,
        default=True,
        label="Include All-Day Events",
        tooltip="Also trigger on all-day events",
    ),
)
@node(category="triggers", exec_inputs=[])
class CalendarTriggerNode(BaseTriggerNode):
    """
    Google Calendar trigger node that listens for calendar events.

    Outputs:
    - event_id: Calendar event ID
    - calendar_id: Calendar ID
    - summary: Event title
    - description: Event description
    - start: Start time (ISO format)
    - end: End time (ISO format)
    - location: Event location
    - attendees: List of attendee emails
    - event_type: Type of trigger (upcoming, created, updated, cancelled)
    - minutes_until_start: Minutes until event starts (for upcoming)
    - organizer: Event organizer email
    - html_link: Link to event in Google Calendar
    - status: Event status (confirmed, tentative, cancelled)
    - created: When event was created
    - updated: When event was last updated
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Google Calendar"
    trigger_description = "Trigger workflow on calendar events"
    trigger_icon = "calendar"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Google Calendar Trigger"
        self.node_type = "CalendarTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define Calendar-specific output ports."""
        self.add_output_port("event_id", DataType.STRING, "Event ID")
        self.add_output_port("calendar_id", DataType.STRING, "Calendar ID")
        self.add_output_port("summary", DataType.STRING, "Summary")
        self.add_output_port("description", DataType.STRING, "Description")
        self.add_output_port("start", DataType.STRING, "Start Time")
        self.add_output_port("end", DataType.STRING, "End Time")
        self.add_output_port("location", DataType.STRING, "Location")
        self.add_output_port("attendees", DataType.LIST, "Attendees")
        self.add_output_port("event_type", DataType.STRING, "Event Type")
        self.add_output_port(
            "minutes_until_start", DataType.INTEGER, "Minutes Until Start"
        )
        self.add_output_port("organizer", DataType.STRING, "Organizer")
        self.add_output_port("html_link", DataType.STRING, "HTML Link")
        self.add_output_port("status", DataType.STRING, "Status")
        self.add_output_port("created", DataType.STRING, "Created")
        self.add_output_port("updated", DataType.STRING, "Updated")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.CALENDAR

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get Calendar-specific configuration."""
        # Parse comma-separated lists
        filter_summary_str = self.config.get("filter_summary", "")
        filter_summary = [s.strip() for s in filter_summary_str.split(",") if s.strip()]

        filter_attendees_str = self.config.get("filter_attendees", "")
        filter_attendees = [
            a.strip() for a in filter_attendees_str.split(",") if a.strip()
        ]

        return {
            "credential_name": self.config.get("credential_name", ""),
            "calendar_id": self.config.get("calendar_id", "primary"),
            "trigger_on": self.config.get("trigger_on", "upcoming"),
            "minutes_before": self.config.get("minutes_before", 15),
            "polling_interval": max(30, self.config.get("polling_interval", 60)),
            "filter_summary": filter_summary,
            "filter_attendees": filter_attendees,
            "include_all_day": self.config.get("include_all_day", True),
        }
