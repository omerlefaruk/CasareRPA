"""
CasareRPA - Google Calendar Nodes

Nodes for interacting with Google Calendar API v3.
Supports event management, calendar management, and free/busy queries.

Event Nodes (8):
- CalendarListEventsNode: List events from a calendar
- CalendarGetEventNode: Get a single event by ID
- CalendarCreateEventNode: Create a new event
- CalendarUpdateEventNode: Update an existing event
- CalendarDeleteEventNode: Delete an event
- CalendarQuickAddNode: Create event using natural language
- CalendarMoveEventNode: Move event to another calendar
- CalendarGetFreeBusyNode: Check availability

Management Nodes (4):
- CalendarListCalendarsNode: List all accessible calendars
- CalendarGetCalendarNode: Get calendar information
- CalendarCreateCalendarNode: Create a new calendar
- CalendarDeleteCalendarNode: Delete a calendar
"""

from .calendar_base import CalendarBaseNode

from .calendar_events import (
    CalendarListEventsNode,
    CalendarGetEventNode,
    CalendarCreateEventNode,
    CalendarUpdateEventNode,
    CalendarDeleteEventNode,
    CalendarQuickAddNode,
    CalendarMoveEventNode,
    CalendarGetFreeBusyNode,
)

from .calendar_manage import (
    CalendarListCalendarsNode,
    CalendarGetCalendarNode,
    CalendarCreateCalendarNode,
    CalendarDeleteCalendarNode,
)

__all__ = [
    # Base
    "CalendarBaseNode",
    # Event Nodes (8)
    "CalendarListEventsNode",
    "CalendarGetEventNode",
    "CalendarCreateEventNode",
    "CalendarUpdateEventNode",
    "CalendarDeleteEventNode",
    "CalendarQuickAddNode",
    "CalendarMoveEventNode",
    "CalendarGetFreeBusyNode",
    # Management Nodes (4)
    "CalendarListCalendarsNode",
    "CalendarGetCalendarNode",
    "CalendarCreateCalendarNode",
    "CalendarDeleteCalendarNode",
]
