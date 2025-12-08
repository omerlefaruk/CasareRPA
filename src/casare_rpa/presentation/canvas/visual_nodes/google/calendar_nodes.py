"""Visual nodes for Google Calendar operations.

All nodes use Google credential picker for OAuth authentication.
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeGoogleCredentialWidget,
)

# Google Calendar API scope
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]


class VisualGoogleCalendarBaseNode(VisualNode):
    """Base class for Google Calendar visual nodes with credential picker integration."""

    REQUIRED_SCOPES = CALENDAR_SCOPE

    def __init__(self, qgraphics_item=None) -> None:
        super().__init__(qgraphics_item)

    def setup_widgets(self) -> None:
        """Setup credential picker widget."""
        self._cred_widget = NodeGoogleCredentialWidget(
            name="credential_id",
            label="Google Account",
            scopes=self.REQUIRED_SCOPES,
        )
        if self._cred_widget:
            self.add_custom_widget(self._cred_widget)
            self._cred_widget.setParentItem(self.view)


# =============================================================================
# Event Operations
# =============================================================================


class VisualCalendarListEventsNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarListEventsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: List Events"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarListEventsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("time_min", DataType.STRING)
        self.add_typed_input("time_max", DataType.STRING)
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("events", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarGetEventNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarGetEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Get Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarGetEventNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("event_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("event", DataType.OBJECT)
        self.add_typed_output("summary", DataType.STRING)
        self.add_typed_output("start_time", DataType.STRING)
        self.add_typed_output("end_time", DataType.STRING)
        self.add_typed_output("description", DataType.STRING)
        self.add_typed_output("location", DataType.STRING)
        self.add_typed_output("attendees", DataType.LIST)
        self.add_typed_output("organizer", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarCreateEventNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarCreateEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Create Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarCreateEventNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("summary", DataType.STRING)
        self.add_typed_input("start_time", DataType.STRING)
        self.add_typed_input("end_time", DataType.STRING)
        self.add_typed_input("description", DataType.STRING)
        self.add_typed_input("location", DataType.STRING)
        self.add_typed_input("attendees", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("ical_uid", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarUpdateEventNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarUpdateEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Update Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarUpdateEventNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("event_id", DataType.STRING)
        self.add_typed_input("summary", DataType.STRING)
        self.add_typed_input("start_time", DataType.STRING)
        self.add_typed_input("end_time", DataType.STRING)
        self.add_typed_input("description", DataType.STRING)
        self.add_typed_input("location", DataType.STRING)
        self.add_typed_input("attendees", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("updated", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarDeleteEventNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarDeleteEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Delete Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarDeleteEventNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("event_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarQuickAddNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarQuickAddNode.

    Creates events using natural language text like:
    - "Meeting at 3pm tomorrow"
    - "Dinner with John on Friday at 7pm"
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Quick Add"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarQuickAddNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("summary", DataType.STRING)
        self.add_typed_output("start_time", DataType.STRING)
        self.add_typed_output("end_time", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarMoveEventNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarMoveEventNode.

    Moves an event from one calendar to another.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Move Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarMoveEventNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("source_calendar_id", DataType.STRING)
        self.add_typed_input("event_id", DataType.STRING)
        self.add_typed_input("destination_calendar_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarGetFreeBusyNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarGetFreeBusyNode.

    Returns free/busy information for a set of calendars.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Get Free/Busy"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarGetFreeBusyNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_ids", DataType.LIST)
        self.add_typed_input("time_min", DataType.STRING)
        self.add_typed_input("time_max", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("free_busy", DataType.OBJECT)
        self.add_typed_output("busy_periods", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Calendar Management Operations
# =============================================================================


class VisualCalendarListCalendarsNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarListCalendarsNode.

    Lists all calendars accessible by the user.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: List Calendars"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarListCalendarsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("calendars", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarGetCalendarNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarGetCalendarNode.

    Gets metadata for a single calendar.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Get Calendar"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarGetCalendarNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("calendar", DataType.OBJECT)
        self.add_typed_output("summary", DataType.STRING)
        self.add_typed_output("description", DataType.STRING)
        self.add_typed_output("time_zone", DataType.STRING)
        self.add_typed_output("access_role", DataType.STRING)
        self.add_typed_output("primary", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarCreateCalendarNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarCreateCalendarNode.

    Creates a new secondary calendar.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Create Calendar"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarCreateCalendarNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("summary", DataType.STRING)
        self.add_typed_input("description", DataType.STRING)
        self.add_typed_input("time_zone", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("calendar_id", DataType.STRING)
        self.add_typed_output("summary", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarDeleteCalendarNode(VisualGoogleCalendarBaseNode):
    """Visual representation of CalendarDeleteCalendarNode.

    Deletes a secondary calendar.
    Cannot delete the primary calendar.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Delete Calendar"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarDeleteCalendarNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
