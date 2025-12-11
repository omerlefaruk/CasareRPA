"""
CasareRPA - Google Calendar Management Nodes

Nodes for managing calendars: list, get, create, delete.
"""

from __future__ import annotations

from typing import Any

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
    default="",
    required=True,
    label="Calendar ID",
    placeholder="calendar_id@group.calendar.google.com",
    tooltip="The unique calendar identifier",
)


# ============================================================================
# CalendarListCalendarsNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    PropertyDef(
        "show_hidden",
        PropertyType.BOOLEAN,
        default=False,
        label="Show Hidden",
        tooltip="Include hidden calendars in the list",
    ),
    PropertyDef(
        "show_deleted",
        PropertyType.BOOLEAN,
        default=False,
        label="Show Deleted",
        tooltip="Include deleted calendars in the list",
    ),
    PropertyDef(
        "min_access_role",
        PropertyType.CHOICE,
        default="",
        choices=["", "freeBusyReader", "reader", "writer", "owner"],
        label="Minimum Access Role",
        tooltip="Filter calendars by minimum access level",
    ),
)
@executable_node
class CalendarListCalendarsNode(CalendarBaseNode):
    """
    List all calendars accessible to the user.

    Inputs:
        - show_hidden: Include hidden calendars
        - show_deleted: Include deleted calendars
        - min_access_role: Filter by access level

    Outputs:
        - calendars: List of calendar objects
        - calendar_count: Number of calendars
        - primary_calendar: Primary calendar info
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: show_hidden, show_deleted, min_access_role -> calendars, calendar_count, primary_calendar

    NODE_TYPE = "calendar_list_calendars"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: List Calendars"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar List Calendars", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "show_hidden", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port(
            "show_deleted", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port(
            "min_access_role", PortType.INPUT, DataType.STRING, required=False
        )

        self.add_output_port("calendars", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("calendar_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("primary_calendar", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """List all accessible calendars."""
        show_hidden = self.get_parameter("show_hidden") or False
        show_deleted = self.get_parameter("show_deleted") or False
        min_access_role = self.get_parameter("min_access_role") or ""

        if hasattr(context, "resolve_value"):
            show_hidden = context.resolve_value(show_hidden)
            show_deleted = context.resolve_value(show_deleted)
            min_access_role = context.resolve_value(min_access_role)

        logger.debug("Listing calendars")

        calendars = await client.list_calendars(
            min_access_role=min_access_role if min_access_role else None,
            show_deleted=bool(show_deleted),
            show_hidden=bool(show_hidden),
        )

        calendar_dicts = [c.to_dict() for c in calendars]

        primary_calendar = {}
        for cal in calendars:
            if cal.primary:
                primary_calendar = cal.to_dict()
                break

        self._set_success_outputs()
        self.set_output_value("calendars", calendar_dicts)
        self.set_output_value("calendar_count", len(calendars))
        self.set_output_value("primary_calendar", primary_calendar)

        logger.info(f"Listed {len(calendars)} calendars")

        return {
            "success": True,
            "calendars": calendar_dicts,
            "calendar_count": len(calendars),
            "primary_calendar": primary_calendar,
            "next_nodes": [],
        }


# ============================================================================
# CalendarGetCalendarNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
)
@executable_node
class CalendarGetCalendarNode(CalendarBaseNode):
    """
    Get calendar information by ID.

    Inputs:
        - calendar_id: Calendar ID

    Outputs:
        - calendar: Calendar object with all details
        - summary: Calendar name
        - timezone: Calendar timezone
        - access_role: User's access role
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id -> calendar, summary, timezone, access_role

    NODE_TYPE = "calendar_get_calendar"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Get Calendar"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Get Calendar", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=True
        )

        self.add_output_port("calendar", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("summary", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("timezone", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("access_role", PortType.OUTPUT, DataType.STRING)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Get calendar information."""
        calendar_id = self.get_parameter("calendar_id")

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)

        if not calendar_id:
            self._set_error_outputs("Calendar ID is required")
            return {
                "success": False,
                "error": "Calendar ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Getting calendar {calendar_id}")

        calendar = await client.get_calendar(calendar_id)

        self._set_success_outputs()
        self.set_output_value("calendar", calendar.to_dict())
        self.set_output_value("summary", calendar.summary)
        self.set_output_value("timezone", calendar.timezone)
        self.set_output_value("access_role", calendar.access_role)

        logger.info(f"Got calendar: {calendar.summary}")

        return {
            "success": True,
            "calendar": calendar.to_dict(),
            "summary": calendar.summary,
            "timezone": calendar.timezone,
            "access_role": calendar.access_role,
            "next_nodes": [],
        }


# ============================================================================
# CalendarCreateCalendarNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    PropertyDef(
        "summary",
        PropertyType.STRING,
        default="",
        required=True,
        label="Calendar Name",
        placeholder="Work Calendar",
        tooltip="The name of the new calendar",
    ),
    PropertyDef(
        "description",
        PropertyType.TEXT,
        default="",
        label="Description",
        placeholder="Calendar for work events",
        tooltip="Description of the calendar",
    ),
    PropertyDef(
        "location",
        PropertyType.STRING,
        default="",
        label="Location",
        placeholder="New York, NY",
        tooltip="Geographic location associated with the calendar",
    ),
    PropertyDef(
        "timezone",
        PropertyType.STRING,
        default="",
        label="Timezone",
        placeholder="America/New_York",
        tooltip="Timezone for the calendar (e.g., America/New_York)",
    ),
)
@executable_node
class CalendarCreateCalendarNode(CalendarBaseNode):
    """
    Create a new Google Calendar.

    Inputs:
        - summary: Calendar name
        - description: Calendar description
        - location: Calendar location
        - timezone: Calendar timezone

    Outputs:
        - calendar_id: Created calendar ID
        - calendar: Full calendar object
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: summary, description, location, timezone -> calendar_id, calendar

    NODE_TYPE = "calendar_create_calendar"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Create Calendar"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Create Calendar", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port("summary", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "description", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("location", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("timezone", PortType.INPUT, DataType.STRING, required=False)

        self.add_output_port("calendar_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("calendar", PortType.OUTPUT, DataType.DICT)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Create a new calendar."""
        summary = self.get_parameter("summary")
        description = self.get_parameter("description") or ""
        location = self.get_parameter("location") or ""
        timezone = self.get_parameter("timezone") or ""

        if hasattr(context, "resolve_value"):
            summary = context.resolve_value(summary)
            description = context.resolve_value(description)
            location = context.resolve_value(location)
            timezone = context.resolve_value(timezone)

        if not summary:
            self._set_error_outputs("Calendar name is required")
            return {
                "success": False,
                "error": "Calendar name is required",
                "next_nodes": [],
            }

        logger.debug(f"Creating calendar '{summary}'")

        calendar = await client.create_calendar(
            summary=summary,
            description=description if description else None,
            location=location if location else None,
            timezone=timezone if timezone else None,
        )

        self._set_success_outputs()
        self.set_output_value("calendar_id", calendar.id)
        self.set_output_value("calendar", calendar.to_dict())

        logger.info(f"Created calendar: {calendar.id}")

        return {
            "success": True,
            "calendar_id": calendar.id,
            "calendar": calendar.to_dict(),
            "next_nodes": [],
        }


# ============================================================================
# CalendarDeleteCalendarNode
# ============================================================================


@node_schema(
    CALENDAR_ACCESS_TOKEN,
    CALENDAR_CREDENTIAL_NAME,
    CALENDAR_ID,
    PropertyDef(
        "confirm_delete",
        PropertyType.BOOLEAN,
        default=False,
        required=True,
        label="Confirm Delete",
        tooltip="Must be true to confirm calendar deletion (prevents accidental deletion)",
    ),
)
@executable_node
class CalendarDeleteCalendarNode(CalendarBaseNode):
    """
    Delete a Google Calendar.

    WARNING: This action is irreversible. The primary calendar cannot be deleted.

    Inputs:
        - calendar_id: Calendar ID to delete
        - confirm_delete: Must be true to confirm deletion

    Outputs:
        - deleted_id: Deleted calendar ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: calendar_id, confirm_delete -> deleted_id

    NODE_TYPE = "calendar_delete_calendar"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Calendar: Delete Calendar"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Calendar Delete Calendar", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        self.add_input_port(
            "calendar_id", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "confirm_delete", PortType.INPUT, DataType.BOOLEAN, required=True
        )

        self.add_output_port("deleted_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """Delete a calendar."""
        calendar_id = self.get_parameter("calendar_id")
        confirm_delete = self.get_parameter("confirm_delete")

        if hasattr(context, "resolve_value"):
            calendar_id = context.resolve_value(calendar_id)
            confirm_delete = context.resolve_value(confirm_delete)

        if not calendar_id:
            self._set_error_outputs("Calendar ID is required")
            return {
                "success": False,
                "error": "Calendar ID is required",
                "next_nodes": [],
            }

        if not confirm_delete:
            self._set_error_outputs("confirm_delete must be true to delete a calendar")
            return {
                "success": False,
                "error": "confirm_delete must be true to delete a calendar",
                "next_nodes": [],
            }

        if calendar_id == "primary":
            self._set_error_outputs("Cannot delete primary calendar")
            return {
                "success": False,
                "error": "Cannot delete primary calendar",
                "next_nodes": [],
            }

        logger.debug(f"Deleting calendar {calendar_id}")

        await client.delete_calendar(calendar_id)

        self._set_success_outputs()
        self.set_output_value("deleted_id", calendar_id)

        logger.info(f"Deleted calendar: {calendar_id}")

        return {
            "success": True,
            "deleted_id": calendar_id,
            "next_nodes": [],
        }


__all__ = [
    "CalendarListCalendarsNode",
    "CalendarGetCalendarNode",
    "CalendarCreateCalendarNode",
    "CalendarDeleteCalendarNode",
]
