"""Visual nodes for Google Calendar operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Event Operations
# =============================================================================


class VisualCalendarListEventsNode(VisualNode):
    """Visual representation of CalendarListEventsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: List Events"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarListEventsNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
            placeholder_text="OAuth credential name",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
            placeholder_text="primary or calendar@group.calendar.google.com",
        )
        self.add_text_input(
            "time_min",
            "Start Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="2025-01-01T00:00:00Z",
        )
        self.add_text_input(
            "time_max",
            "End Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="2025-12-31T23:59:59Z",
        )
        self.add_text_input(
            "max_results",
            "Max Results",
            text="100",
            tab="properties",
        )
        self.add_text_input(
            "query",
            "Search Query",
            text="",
            tab="properties",
            placeholder_text="Free text search term",
        )
        # Advanced tab
        self.add_checkbox(
            "single_events",
            "Single Events",
            state=True,
            tab="advanced",
        )
        self.add_combo_menu(
            "order_by",
            "Order By",
            items=["startTime", "updated"],
            tab="advanced",
        )
        self.add_checkbox(
            "show_deleted",
            "Show Deleted",
            state=False,
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("time_min", DataType.STRING)
        self.add_typed_input("time_max", DataType.STRING)
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("events", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarGetEventNode(VisualNode):
    """Visual representation of CalendarGetEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Get Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarGetEventNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
        )
        self.add_text_input(
            "event_id",
            "Event ID",
            text="",
            tab="properties",
            placeholder_text="Event identifier",
        )
        # Advanced tab
        self.add_text_input(
            "time_zone",
            "Time Zone",
            text="",
            tab="advanced",
            placeholder_text="America/New_York",
        )

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
        self.add_typed_output("attendees", DataType.ARRAY)
        self.add_typed_output("organizer", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarCreateEventNode(VisualNode):
    """Visual representation of CalendarCreateEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Create Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarCreateEventNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
        )
        self.add_text_input(
            "summary",
            "Event Title",
            text="",
            tab="properties",
            placeholder_text="Meeting with Team",
        )
        self.add_text_input(
            "start_time",
            "Start Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="2025-01-15T10:00:00",
        )
        self.add_text_input(
            "end_time",
            "End Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="2025-01-15T11:00:00",
        )
        self.add_text_input(
            "description",
            "Description",
            text="",
            tab="properties",
            placeholder_text="Event description",
        )
        self.add_text_input(
            "location",
            "Location",
            text="",
            tab="properties",
            placeholder_text="Conference Room A",
        )
        self.add_text_input(
            "attendees",
            "Attendees",
            text="",
            tab="properties",
            placeholder_text="email1@example.com, email2@example.com",
        )
        # Advanced tab
        self.add_text_input(
            "time_zone",
            "Time Zone",
            text="",
            tab="advanced",
            placeholder_text="America/New_York",
        )
        self.add_combo_menu(
            "reminder_method",
            "Reminder Method",
            items=["email", "popup", "none"],
            tab="advanced",
        )
        self.add_text_input(
            "reminder_minutes",
            "Reminder Minutes",
            text="30",
            tab="advanced",
        )
        self.add_checkbox(
            "send_notifications",
            "Send Notifications",
            state=True,
            tab="advanced",
        )
        self.add_combo_menu(
            "visibility",
            "Visibility",
            items=["default", "public", "private", "confidential"],
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("summary", DataType.STRING)
        self.add_typed_input("start_time", DataType.STRING)
        self.add_typed_input("end_time", DataType.STRING)
        self.add_typed_input("description", DataType.STRING)
        self.add_typed_input("location", DataType.STRING)
        self.add_typed_input("attendees", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("ical_uid", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarUpdateEventNode(VisualNode):
    """Visual representation of CalendarUpdateEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Update Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarUpdateEventNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
        )
        self.add_text_input(
            "event_id",
            "Event ID",
            text="",
            tab="properties",
            placeholder_text="Event identifier to update",
        )
        self.add_text_input(
            "summary",
            "Event Title",
            text="",
            tab="properties",
            placeholder_text="Leave empty to keep current",
        )
        self.add_text_input(
            "start_time",
            "Start Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="Leave empty to keep current",
        )
        self.add_text_input(
            "end_time",
            "End Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="Leave empty to keep current",
        )
        self.add_text_input(
            "description",
            "Description",
            text="",
            tab="properties",
            placeholder_text="Leave empty to keep current",
        )
        self.add_text_input(
            "location",
            "Location",
            text="",
            tab="properties",
            placeholder_text="Leave empty to keep current",
        )
        self.add_text_input(
            "attendees",
            "Attendees",
            text="",
            tab="properties",
            placeholder_text="email1@example.com, email2@example.com",
        )
        # Advanced tab
        self.add_checkbox(
            "send_notifications",
            "Send Notifications",
            state=True,
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("event_id", DataType.STRING)
        self.add_typed_input("summary", DataType.STRING)
        self.add_typed_input("start_time", DataType.STRING)
        self.add_typed_input("end_time", DataType.STRING)
        self.add_typed_input("description", DataType.STRING)
        self.add_typed_input("location", DataType.STRING)
        self.add_typed_input("attendees", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("updated", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarDeleteEventNode(VisualNode):
    """Visual representation of CalendarDeleteEventNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Delete Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarDeleteEventNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
        )
        self.add_text_input(
            "event_id",
            "Event ID",
            text="",
            tab="properties",
            placeholder_text="Event identifier to delete",
        )
        # Advanced tab
        self.add_checkbox(
            "send_notifications",
            "Send Notifications",
            state=True,
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_typed_input("event_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarQuickAddNode(VisualNode):
    """Visual representation of CalendarQuickAddNode.

    Creates events using natural language text like:
    - "Meeting at 3pm tomorrow"
    - "Dinner with John on Friday at 7pm"
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Quick Add"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarQuickAddNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
        )
        self.add_text_input(
            "text",
            "Quick Add Text",
            text="",
            tab="properties",
            placeholder_text="Meeting with team tomorrow at 2pm",
        )
        # Advanced tab
        self.add_checkbox(
            "send_notifications",
            "Send Notifications",
            state=True,
            tab="advanced",
        )

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


class VisualCalendarMoveEventNode(VisualNode):
    """Visual representation of CalendarMoveEventNode.

    Moves an event from one calendar to another.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Move Event"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarMoveEventNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "source_calendar_id",
            "Source Calendar ID",
            text="primary",
            tab="properties",
            placeholder_text="Calendar to move from",
        )
        self.add_text_input(
            "event_id",
            "Event ID",
            text="",
            tab="properties",
            placeholder_text="Event identifier to move",
        )
        self.add_text_input(
            "destination_calendar_id",
            "Destination Calendar ID",
            text="",
            tab="properties",
            placeholder_text="Calendar to move to",
        )
        # Advanced tab
        self.add_checkbox(
            "send_notifications",
            "Send Notifications",
            state=True,
            tab="advanced",
        )

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


class VisualCalendarGetFreeBusyNode(VisualNode):
    """Visual representation of CalendarGetFreeBusyNode.

    Returns free/busy information for a set of calendars.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Get Free/Busy"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarGetFreeBusyNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_ids",
            "Calendar IDs",
            text="primary",
            tab="properties",
            placeholder_text="primary, work@group.calendar.google.com",
        )
        self.add_text_input(
            "time_min",
            "Start Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="2025-01-15T00:00:00Z",
        )
        self.add_text_input(
            "time_max",
            "End Time (ISO)",
            text="",
            tab="properties",
            placeholder_text="2025-01-16T00:00:00Z",
        )
        # Advanced tab
        self.add_text_input(
            "time_zone",
            "Time Zone",
            text="",
            tab="advanced",
            placeholder_text="America/New_York",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_ids", DataType.ARRAY)
        self.add_typed_input("time_min", DataType.STRING)
        self.add_typed_input("time_max", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("free_busy", DataType.OBJECT)
        self.add_typed_output("busy_periods", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Calendar Management Operations
# =============================================================================


class VisualCalendarListCalendarsNode(VisualNode):
    """Visual representation of CalendarListCalendarsNode.

    Lists all calendars accessible by the user.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: List Calendars"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarListCalendarsNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_checkbox(
            "show_hidden",
            "Show Hidden",
            state=False,
            tab="properties",
        )
        self.add_checkbox(
            "show_deleted",
            "Show Deleted",
            state=False,
            tab="properties",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("calendars", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualCalendarGetCalendarNode(VisualNode):
    """Visual representation of CalendarGetCalendarNode.

    Gets metadata for a single calendar.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Get Calendar"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarGetCalendarNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="primary",
            tab="properties",
            placeholder_text="primary or calendar@group.calendar.google.com",
        )

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


class VisualCalendarCreateCalendarNode(VisualNode):
    """Visual representation of CalendarCreateCalendarNode.

    Creates a new secondary calendar.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Create Calendar"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarCreateCalendarNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "summary",
            "Calendar Name",
            text="",
            tab="properties",
            placeholder_text="Work Calendar",
        )
        self.add_text_input(
            "description",
            "Description",
            text="",
            tab="properties",
            placeholder_text="Calendar for work events",
        )
        self.add_text_input(
            "time_zone",
            "Time Zone",
            text="",
            tab="properties",
            placeholder_text="America/New_York",
        )
        self.add_text_input(
            "location",
            "Location",
            text="",
            tab="properties",
            placeholder_text="Office Location",
        )

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


class VisualCalendarDeleteCalendarNode(VisualNode):
    """Visual representation of CalendarDeleteCalendarNode.

    Deletes a secondary calendar.
    Cannot delete the primary calendar.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Calendar: Delete Calendar"
    NODE_CATEGORY = "google/calendar"
    CASARE_NODE_CLASS = "CalendarDeleteCalendarNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
        )
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Optional: Direct access token",
        )
        # Properties tab
        self.add_text_input(
            "calendar_id",
            "Calendar ID",
            text="",
            tab="properties",
            placeholder_text="calendar@group.calendar.google.com",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("calendar_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
