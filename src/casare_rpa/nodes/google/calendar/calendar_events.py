"""
CasareRPA - Google Calendar Event Nodes

Nodes for managing calendar events: list, get, create, update, delete, quick add, move, free/busy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_calendar_client import (
    GoogleCalendarClient,
)
from casare_rpa.nodes.google.google_base import CalendarBaseNode


# ============================================================================
# Reusable Property Definitions
# ============================================================================

CALENDAR_ACCESS_TOKEN = PropertyDef(
    "access_token",
    PropertyType.STRING,
    default="",
    label="Access Token",
    placeholder="ya29.a0...",
    tooltip="OAuth 2.0 access token for Google Calendar API",
    tab="connection",
)

CALENDAR_CREDENTIAL_NAME = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="google_calendar",
    tooltip="Name of stored OAuth credential (alternative to access token)",
    tab="connection",
)

CALENDAR_ID = PropertyDef(
    "calendar_id",
    PropertyType.STRING,
    default="primary",
    label="Calendar ID",
    placeholder="primary",
    tooltip="Calendar ID (use 'primary' for the user's primary calendar)",
)

EVENT_ID = PropertyDef(
    "event_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="Event ID",
    placeholder="abc123xyz",
    tooltip="The unique event identifier",
)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from string or return if already datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_attendees(attendees_str: str) -> List[dict]:
    """Parse comma-separated emails into attendee list."""
    if not attendees_str:
        return []
    return [
        {"email": email.strip()} for email in attendees_str.split(",") if email.strip()
    ]


# ============================================================================
# CalendarListEventsNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    PropertyDef(
        "time_min",
        PropertyType.STRING,
        default="",
        label="Start Time",
        placeholder="2024-01-01T00:00:00Z",
        tooltip="Filter events starting after this time (ISO 8601 format)",
    ),
    PropertyDef(
        "time_max",
        PropertyType.STRING,
        default="",
        label="End Time",
        placeholder="2024-12-31T23:59:59Z",
        tooltip="Filter events ending before this time (ISO 8601 format)",
    ),
    PropertyDef(
        "query",
        PropertyType.STRING,
        default="",
        label="Search Query",
        placeholder="meeting",
        tooltip="Free-text search within event fields",
    ),
    PropertyDef(
        "max_results",
        PropertyType.INTEGER,
        default=100,
        label="Max Results",
        tooltip="Maximum number of events to return (1-2500)",
    ),
)
@executable_node
class CalendarListEventsNode(CalendarBaseNode):
    """
    List events from a Google Calendar.

    Inputs:
        - calendar_id: Calendar ID (default: "primary")
        - time_min: Start time filter (ISO 8601)
        - time_max: End time filter (ISO 8601)
        - query: Text search query
        - max_results: Maximum events to return

    Outputs:
        - events: List of event objects
        - event_count: Number of events returned
        - next_page_token: Token for pagination
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, time_min, time_max, query, max_results -> events, event_count, next_page_token

    NODE_TYPE = "calendar_list_events"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: List Events"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar List Events", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("time_min", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("time_max", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("query", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "max_results", PortType.INPUT, DataType.INTEGER, required=False
        )

        self.add_output_port("events", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("event_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("next_page_token", PortType.OUTPUT, DataType.STRING)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """List events from calendar."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)

        time_min_str = self.get_parameter("time_min") or ""
        time_max_str = self.get_parameter("time_max") or ""
        query = self.get_parameter("query") or ""
        max_results = self.get_parameter("max_results") or 100

        if hasattr(context, "resolve_value"):
            time_min_str = context.resolve_value(time_min_str)
            time_max_str = context.resolve_value(time_max_str)
            query = context.resolve_value(query)
            max_results = context.resolve_value(max_results)

        time_min = _parse_datetime(time_min_str)
        time_max = _parse_datetime(time_max_str)

        logger.debug(f"Listing events from calendar {calendar_id}")

        events, next_token = await client.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=int(max_results),
            q=query if query else None,
        )

        event_dicts = [e.to_dict() for e in events]

        self._set_success_outputs()
        self.set_output_value("events", event_dicts)
        self.set_output_value("event_count", len(events))
        self.set_output_value("next_page_token", next_token or "")

        logger.info(f"Listed {len(events)} events")

        return {
            "success": True,
            "events": event_dicts,
            "event_count": len(events),
            "next_page_token": next_token,
            "next_nodes": [],
        }


# ============================================================================
# CalendarGetEventNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    EVENT_ID,
)
@executable_node
class CalendarGetEventNode(CalendarBaseNode):
    """
    Get a single calendar event by ID.

    Inputs:
        - calendar_id: Calendar ID
        - event_id: Event ID

    Outputs:
        - event: Event object with all details
        - summary: Event title
        - start: Start time
        - end: End time
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, event_id -> event, summary, start, end

    NODE_TYPE = "calendar_get_event"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Get Event"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Get Event", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("event_id", PortType.INPUT, DataType.STRING, required=True)

        self.add_output_port("event", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("summary", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("start", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("end", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Get a single event."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        event_id = self.get_parameter("event_id")

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            event_id = context.resolve_value(event_id)

        if not event_id:
            self._set_error_outputs("Event ID is required")
            return {"success": False, "error": "Event ID is required", "next_nodes": []}

        logger.debug(f"Getting event {event_id} from calendar {calendar_id}")

        event = await client.get_event(calendar_id, event_id)

        self._set_success_outputs()
        self.set_output_value("event", event.to_dict())
        self.set_output_value("summary", event.summary)
        self.set_output_value("start", event.start or {})
        self.set_output_value("end", event.end or {})

        logger.info(f"Got event: {event.summary}")

        return {
            "success": True,
            "event": event.to_dict(),
            "summary": event.summary,
            "next_nodes": [],
        }


# ============================================================================
# CalendarCreateEventNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    PropertyDef(
        "summary",
        PropertyType.STRING,
        default="",
        required=True,
        label="Event Title",
        placeholder="Team Meeting",
        tooltip="The title/summary of the event",
    ),
    PropertyDef(
        "start_datetime",
        PropertyType.STRING,
        default="",
        required=True,
        label="Start Time",
        placeholder="2024-01-15T09:00:00-05:00",
        tooltip="Start date/time in ISO 8601 format",
    ),
    PropertyDef(
        "end_datetime",
        PropertyType.STRING,
        default="",
        required=True,
        label="End Time",
        placeholder="2024-01-15T10:00:00-05:00",
        tooltip="End date/time in ISO 8601 format",
    ),
    PropertyDef(
        "timezone",
        PropertyType.STRING,
        default="",
        label="Timezone",
        placeholder="America/New_York",
        tooltip="Timezone for the event (e.g., America/New_York)",
    ),
    PropertyDef(
        "description",
        PropertyType.TEXT,
        default="",
        label="Description",
        placeholder="Event description...",
        tooltip="Detailed description of the event",
    ),
    PropertyDef(
        "location",
        PropertyType.STRING,
        default="",
        label="Location",
        placeholder="Conference Room A",
        tooltip="Event location or meeting room",
    ),
    PropertyDef(
        "attendees",
        PropertyType.STRING,
        default="",
        label="Attendees",
        placeholder="user1@example.com, user2@example.com",
        tooltip="Comma-separated email addresses of attendees",
    ),
    PropertyDef(
        "send_updates",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "externalOnly", "none"],
        label="Send Updates",
        tooltip="Who to notify about event changes",
    ),
)
@executable_node
class CalendarCreateEventNode(CalendarBaseNode):
    """
    Create a new calendar event.

    Inputs:
        - calendar_id: Calendar ID
        - summary: Event title
        - start_datetime: Start time (ISO 8601)
        - end_datetime: End time (ISO 8601)
        - timezone: Optional timezone
        - description: Event description
        - location: Event location
        - attendees: Comma-separated emails

    Outputs:
        - event_id: Created event ID
        - html_link: Link to view event
        - event: Full event object
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, summary, start_datetime, end_datetime, timezone, description, location, attendees -> event_id, html_link, event

    NODE_TYPE = "calendar_create_event"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Create Event"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Create Event", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("summary", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "start_datetime", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "end_datetime", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("timezone", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "description", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("location", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "attendees", PortType.INPUT, DataType.STRING, required=False
        )

        self.add_output_port("event_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("html_link", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("event", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Create a new event."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        summary = self.get_parameter("summary")
        start_datetime = self.get_parameter("start_datetime")
        end_datetime = self.get_parameter("end_datetime")
        timezone = self.get_parameter("timezone") or ""
        description = self.get_parameter("description") or ""
        location = self.get_parameter("location") or ""
        attendees_str = self.get_parameter("attendees") or ""
        send_updates = self.get_parameter("send_updates") or "all"

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            summary = context.resolve_value(summary)
            start_datetime = context.resolve_value(start_datetime)
            end_datetime = context.resolve_value(end_datetime)
            timezone = context.resolve_value(timezone)
            description = context.resolve_value(description)
            location = context.resolve_value(location)
            attendees_str = context.resolve_value(attendees_str)
            send_updates = context.resolve_value(send_updates)

        if not summary:
            self._set_error_outputs("Event title is required")
            return {
                "success": False,
                "error": "Event title is required",
                "next_nodes": [],
            }

        if not start_datetime:
            self._set_error_outputs("Start time is required")
            return {
                "success": False,
                "error": "Start time is required",
                "next_nodes": [],
            }

        if not end_datetime:
            self._set_error_outputs("End time is required")
            return {"success": False, "error": "End time is required", "next_nodes": []}

        start = {"dateTime": start_datetime}
        end = {"dateTime": end_datetime}
        if timezone:
            start["timeZone"] = timezone
            end["timeZone"] = timezone

        attendees = _parse_attendees(attendees_str)

        logger.debug(f"Creating event '{summary}' in calendar {calendar_id}")

        event = await client.create_event(
            calendar_id=calendar_id,
            summary=summary,
            start=start,
            end=end,
            description=description if description else None,
            location=location if location else None,
            attendees=attendees if attendees else None,
            send_updates=send_updates,
        )

        self._set_success_outputs()
        self.set_output_value("event_id", event.id)
        self.set_output_value("html_link", event.html_link)
        self.set_output_value("event", event.to_dict())

        logger.info(f"Created event: {event.id}")

        return {
            "success": True,
            "event_id": event.id,
            "html_link": event.html_link,
            "event": event.to_dict(),
            "next_nodes": [],
        }


# ============================================================================
# CalendarUpdateEventNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    EVENT_ID,
    PropertyDef(
        "summary",
        PropertyType.STRING,
        default="",
        label="New Title",
        placeholder="Updated Meeting Title",
        tooltip="New event title (leave empty to keep current)",
    ),
    PropertyDef(
        "start_datetime",
        PropertyType.STRING,
        default="",
        label="New Start Time",
        placeholder="2024-01-15T09:00:00-05:00",
        tooltip="New start time (leave empty to keep current)",
    ),
    PropertyDef(
        "end_datetime",
        PropertyType.STRING,
        default="",
        label="New End Time",
        placeholder="2024-01-15T10:00:00-05:00",
        tooltip="New end time (leave empty to keep current)",
    ),
    PropertyDef(
        "description",
        PropertyType.TEXT,
        default="",
        label="New Description",
        tooltip="New description (leave empty to keep current)",
    ),
    PropertyDef(
        "location",
        PropertyType.STRING,
        default="",
        label="New Location",
        tooltip="New location (leave empty to keep current)",
    ),
    PropertyDef(
        "send_updates",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "externalOnly", "none"],
        label="Send Updates",
        tooltip="Who to notify about event changes",
    ),
)
@executable_node
class CalendarUpdateEventNode(CalendarBaseNode):
    """
    Update an existing calendar event.

    Inputs:
        - calendar_id: Calendar ID
        - event_id: Event ID
        - summary: New title (optional)
        - start_datetime: New start time (optional)
        - end_datetime: New end time (optional)
        - description: New description (optional)
        - location: New location (optional)

    Outputs:
        - event_id: Updated event ID
        - event: Updated event object
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, event_id, summary, start_datetime, end_datetime, description, location -> event_id, event

    NODE_TYPE = "calendar_update_event"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Update Event"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Update Event", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("event_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("summary", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "start_datetime", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "end_datetime", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "description", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("location", PortType.INPUT, DataType.STRING, required=False)

        self.add_output_port("event_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("event", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Update an existing event."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        event_id = self.get_parameter("event_id")
        summary = self.get_parameter("summary") or ""
        start_datetime = self.get_parameter("start_datetime") or ""
        end_datetime = self.get_parameter("end_datetime") or ""
        description = self.get_parameter("description") or ""
        location = self.get_parameter("location") or ""
        send_updates = self.get_parameter("send_updates") or "all"

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            event_id = context.resolve_value(event_id)
            summary = context.resolve_value(summary)
            start_datetime = context.resolve_value(start_datetime)
            end_datetime = context.resolve_value(end_datetime)
            description = context.resolve_value(description)
            location = context.resolve_value(location)
            send_updates = context.resolve_value(send_updates)

        if not event_id:
            self._set_error_outputs("Event ID is required")
            return {"success": False, "error": "Event ID is required", "next_nodes": []}

        event_data: dict[str, Any] = {}

        if summary:
            event_data["summary"] = summary
        if start_datetime:
            event_data["start"] = {"dateTime": start_datetime}
        if end_datetime:
            event_data["end"] = {"dateTime": end_datetime}
        if description:
            event_data["description"] = description
        if location:
            event_data["location"] = location

        if not event_data:
            self._set_error_outputs("At least one field to update is required")
            return {
                "success": False,
                "error": "At least one field to update is required",
                "next_nodes": [],
            }

        logger.debug(f"Updating event {event_id}")

        event = await client.update_event(
            calendar_id=calendar_id,
            event_id=event_id,
            event_data=event_data,
            send_updates=send_updates,
        )

        self._set_success_outputs()
        self.set_output_value("event_id", event.id)
        self.set_output_value("event", event.to_dict())

        logger.info(f"Updated event: {event.id}")

        return {
            "success": True,
            "event_id": event.id,
            "event": event.to_dict(),
            "next_nodes": [],
        }


# ============================================================================
# CalendarDeleteEventNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    EVENT_ID,
    PropertyDef(
        "send_updates",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "externalOnly", "none"],
        label="Send Updates",
        tooltip="Who to notify about event deletion",
    ),
)
@executable_node
class CalendarDeleteEventNode(CalendarBaseNode):
    """
    Delete a calendar event.

    Inputs:
        - calendar_id: Calendar ID
        - event_id: Event ID to delete
        - send_updates: Notification preference

    Outputs:
        - deleted_id: Deleted event ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, event_id -> deleted_id

    NODE_TYPE = "calendar_delete_event"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Delete Event"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Delete Event", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("event_id", PortType.INPUT, DataType.STRING, required=True)

        self.add_output_port("deleted_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Delete an event."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        event_id = self.get_parameter("event_id")
        send_updates = self.get_parameter("send_updates") or "all"

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            event_id = context.resolve_value(event_id)
            send_updates = context.resolve_value(send_updates)

        if not event_id:
            self._set_error_outputs("Event ID is required")
            return {"success": False, "error": "Event ID is required", "next_nodes": []}

        logger.debug(f"Deleting event {event_id}")

        await client.delete_event(
            calendar_id=calendar_id,
            event_id=event_id,
            send_updates=send_updates,
        )

        self._set_success_outputs()
        self.set_output_value("deleted_id", event_id)

        logger.info(f"Deleted event: {event_id}")

        return {
            "success": True,
            "deleted_id": event_id,
            "next_nodes": [],
        }


# ============================================================================
# CalendarQuickAddNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        required=True,
        label="Event Text",
        placeholder="Meeting with John tomorrow at 3pm for 1 hour",
        tooltip="Natural language description of the event",
    ),
    PropertyDef(
        "send_updates",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "externalOnly", "none"],
        label="Send Updates",
        tooltip="Who to notify about event creation",
    ),
)
@executable_node
class CalendarQuickAddNode(CalendarBaseNode):
    """
    Create an event using natural language.

    Uses Google's natural language processing to parse event details
    from plain text (e.g., "Meeting tomorrow at 3pm for 1 hour").

    Inputs:
        - calendar_id: Calendar ID
        - text: Natural language event description

    Outputs:
        - event_id: Created event ID
        - summary: Parsed event title
        - start: Parsed start time
        - end: Parsed end time
        - event: Full event object
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, text -> event_id, summary, start, end, event

    NODE_TYPE = "calendar_quick_add"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Quick Add"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Quick Add", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("text", PortType.INPUT, DataType.STRING, required=True)

        self.add_output_port("event_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("summary", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("start", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("end", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("event", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Quick add an event with natural language."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        text = self.get_parameter("text")
        send_updates = self.get_parameter("send_updates") or "all"

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            text = context.resolve_value(text)
            send_updates = context.resolve_value(send_updates)

        if not text:
            self._set_error_outputs("Event text is required")
            return {
                "success": False,
                "error": "Event text is required",
                "next_nodes": [],
            }

        logger.debug(f"Quick adding event: '{text}'")

        event = await client.quick_add_event(
            calendar_id=calendar_id,
            text=text,
            send_updates=send_updates,
        )

        self._set_success_outputs()
        self.set_output_value("event_id", event.id)
        self.set_output_value("summary", event.summary)
        self.set_output_value("start", event.start or {})
        self.set_output_value("end", event.end or {})
        self.set_output_value("event", event.to_dict())

        logger.info(f"Quick added event: {event.id} - {event.summary}")

        return {
            "success": True,
            "event_id": event.id,
            "summary": event.summary,
            "event": event.to_dict(),
            "next_nodes": [],
        }


# ============================================================================
# CalendarMoveEventNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    EVENT_ID,
    PropertyDef(
        "destination_calendar_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Destination Calendar",
        placeholder="calendar_id@group.calendar.google.com",
        tooltip="Calendar ID to move the event to",
    ),
    PropertyDef(
        "send_updates",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "externalOnly", "none"],
        label="Send Updates",
        tooltip="Who to notify about event move",
    ),
)
@executable_node
class CalendarMoveEventNode(CalendarBaseNode):
    """
    Move an event to another calendar.

    Inputs:
        - calendar_id: Source calendar ID
        - event_id: Event ID to move
        - destination_calendar_id: Target calendar ID

    Outputs:
        - event_id: Moved event ID
        - new_calendar_id: Destination calendar ID
        - event: Updated event object
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, event_id, destination_calendar_id -> event_id, new_calendar_id, event

    NODE_TYPE = "calendar_move_event"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Move Event"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Move Event", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("event_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "destination_calendar_id", PortType.INPUT, DataType.STRING, required=True
        )

        self.add_output_port("event_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("new_calendar_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("event", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Move an event to another calendar."""
        calendar_id = self.get_parameter("calendar_id") or "primary"
        event_id = self.get_parameter("event_id")
        destination_calendar_id = self.get_parameter("destination_calendar_id")
        send_updates = self.get_parameter("send_updates") or "all"

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            event_id = context.resolve_value(event_id)
            destination_calendar_id = context.resolve_value(destination_calendar_id)
            send_updates = context.resolve_value(send_updates)

        if not event_id:
            self._set_error_outputs("Event ID is required")
            return {"success": False, "error": "Event ID is required", "next_nodes": []}

        if not destination_calendar_id:
            self._set_error_outputs("Destination calendar ID is required")
            return {
                "success": False,
                "error": "Destination calendar ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Moving event {event_id} to {destination_calendar_id}")

        event = await client.move_event(
            calendar_id=calendar_id,
            event_id=event_id,
            destination_calendar_id=destination_calendar_id,
            send_updates=send_updates,
        )

        self._set_success_outputs()
        self.set_output_value("event_id", event.id)
        self.set_output_value("new_calendar_id", destination_calendar_id)
        self.set_output_value("event", event.to_dict())

        logger.info(f"Moved event {event_id} to {destination_calendar_id}")

        return {
            "success": True,
            "event_id": event.id,
            "new_calendar_id": destination_calendar_id,
            "event": event.to_dict(),
            "next_nodes": [],
        }


# ============================================================================
# CalendarGetFreeBusyNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    PropertyDef(
        "calendar_ids",
        PropertyType.STRING,
        default="primary",
        required=True,
        label="Calendar IDs",
        placeholder="primary, calendar2@group.calendar.google.com",
        tooltip="Comma-separated calendar IDs to check availability",
    ),
    PropertyDef(
        "time_min",
        PropertyType.STRING,
        default="",
        required=True,
        label="Start Time",
        placeholder="2024-01-15T09:00:00-05:00",
        tooltip="Start of time range to check (ISO 8601)",
    ),
    PropertyDef(
        "time_max",
        PropertyType.STRING,
        default="",
        required=True,
        label="End Time",
        placeholder="2024-01-15T17:00:00-05:00",
        tooltip="End of time range to check (ISO 8601)",
    ),
)
@executable_node
class CalendarGetFreeBusyNode(CalendarBaseNode):
    """
    Query free/busy information for calendars.

    Inputs:
        - calendar_ids: Comma-separated calendar IDs
        - time_min: Start of time range (ISO 8601)
        - time_max: End of time range (ISO 8601)

    Outputs:
        - free_busy: Dictionary mapping calendar ID to busy periods
        - is_busy: Boolean - true if any calendar has conflicts
        - busy_count: Total number of busy periods
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_ids, time_min, time_max -> free_busy, is_busy, busy_count

    NODE_TYPE = "calendar_get_free_busy"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Get Free/Busy"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Get Free/Busy", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_ids", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("time_min", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("time_max", PortType.INPUT, DataType.STRING, required=True)

        self.add_output_port("free_busy", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("is_busy", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("busy_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Query free/busy information."""
        calendar_ids_str = self.get_parameter("calendar_ids")
        time_min_str = self.get_parameter("time_min")
        time_max_str = self.get_parameter("time_max")

        if hasattr(context, "resolve_value"):
            calendar_ids_str = context.resolve_value(calendar_ids_str)
            time_min_str = context.resolve_value(time_min_str)
            time_max_str = context.resolve_value(time_max_str)

        if not calendar_ids_str:
            self._set_error_outputs("Calendar IDs are required")
            return {
                "success": False,
                "error": "Calendar IDs are required",
                "next_nodes": [],
            }

        if not time_min_str:
            self._set_error_outputs("Start time is required")
            return {
                "success": False,
                "error": "Start time is required",
                "next_nodes": [],
            }

        if not time_max_str:
            self._set_error_outputs("End time is required")
            return {"success": False, "error": "End time is required", "next_nodes": []}

        calendar_ids = [
            cid.strip() for cid in calendar_ids_str.split(",") if cid.strip()
        ]
        time_min = _parse_datetime(time_min_str)
        time_max = _parse_datetime(time_max_str)

        if not time_min or not time_max:
            self._set_error_outputs("Invalid time format")
            return {"success": False, "error": "Invalid time format", "next_nodes": []}

        logger.debug(f"Getting free/busy for {len(calendar_ids)} calendars")

        free_busy_info = await client.get_free_busy(
            calendar_ids=calendar_ids,
            time_min=time_min,
            time_max=time_max,
        )

        free_busy_dict = {}
        total_busy = 0
        for cal_id, info in free_busy_info.items():
            free_busy_dict[cal_id] = {
                "busy": info.busy_periods,
                "errors": info.errors,
            }
            total_busy += len(info.busy_periods)

        is_busy = total_busy > 0

        self._set_success_outputs()
        self.set_output_value("free_busy", free_busy_dict)
        self.set_output_value("is_busy", is_busy)
        self.set_output_value("busy_count", total_busy)

        logger.info(f"Free/busy query: {total_busy} busy periods found")

        return {
            "success": True,
            "free_busy": free_busy_dict,
            "is_busy": is_busy,
            "busy_count": total_busy,
            "next_nodes": [],
        }


__all__ = [
    "CalendarListEventsNode",
    "CalendarGetEventNode",
    "CalendarCreateEventNode",
    "CalendarUpdateEventNode",
    "CalendarDeleteEventNode",
    "CalendarQuickAddNode",
    "CalendarMoveEventNode",
    "CalendarGetFreeBusyNode",
]
