"""
Google Calendar API Client

Async client for interacting with the Google Calendar API v3.
Supports events, calendars, and free/busy queries.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiohttp
from loguru import logger


class GoogleCalendarAPIError(Exception):
    """Exception raised for Google Calendar API errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        reason: Optional[str] = None,
    ):
        self.error_code = error_code
        self.reason = reason
        super().__init__(message)


@dataclass
class CalendarConfig:
    """Configuration for Google Calendar API client."""

    access_token: str
    base_url: str = "https://www.googleapis.com/calendar/v3"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class CalendarEvent:
    """Represents a Google Calendar event."""

    id: str
    calendar_id: str = ""
    summary: str = ""
    description: str = ""
    location: str = ""
    status: str = ""
    html_link: str = ""
    created: str = ""
    updated: str = ""
    start: Optional[dict] = None
    end: Optional[dict] = None
    attendees: List[dict] = field(default_factory=list)
    organizer: Optional[dict] = None
    creator: Optional[dict] = None
    recurrence: List[str] = field(default_factory=list)
    recurring_event_id: Optional[str] = None
    reminders: Optional[dict] = None
    conference_data: Optional[dict] = None
    attachments: List[dict] = field(default_factory=list)
    visibility: str = "default"
    transparency: str = "opaque"
    color_id: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict, calendar_id: str = "") -> "CalendarEvent":
        """Create CalendarEvent from API response."""
        return cls(
            id=data.get("id", ""),
            calendar_id=calendar_id,
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            location=data.get("location", ""),
            status=data.get("status", ""),
            html_link=data.get("htmlLink", ""),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            start=data.get("start"),
            end=data.get("end"),
            attendees=data.get("attendees", []),
            organizer=data.get("organizer"),
            creator=data.get("creator"),
            recurrence=data.get("recurrence", []),
            recurring_event_id=data.get("recurringEventId"),
            reminders=data.get("reminders"),
            conference_data=data.get("conferenceData"),
            attachments=data.get("attachments", []),
            visibility=data.get("visibility", "default"),
            transparency=data.get("transparency", "opaque"),
            color_id=data.get("colorId"),
            raw=data,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "location": self.location,
            "status": self.status,
            "start": self.start,
            "end": self.end,
            "attendees": self.attendees,
            "html_link": self.html_link,
            "organizer": self.organizer,
        }


@dataclass
class Calendar:
    """Represents a Google Calendar."""

    id: str
    summary: str = ""
    description: str = ""
    location: str = ""
    timezone: str = ""
    access_role: str = ""
    background_color: str = ""
    foreground_color: str = ""
    selected: bool = False
    primary: bool = False
    hidden: bool = False
    deleted: bool = False
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> "Calendar":
        """Create Calendar from API response."""
        return cls(
            id=data.get("id", ""),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            location=data.get("location", ""),
            timezone=data.get("timeZone", ""),
            access_role=data.get("accessRole", ""),
            background_color=data.get("backgroundColor", ""),
            foreground_color=data.get("foregroundColor", ""),
            selected=data.get("selected", False),
            primary=data.get("primary", False),
            hidden=data.get("hidden", False),
            deleted=data.get("deleted", False),
            raw=data,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "timezone": self.timezone,
            "access_role": self.access_role,
            "primary": self.primary,
        }


@dataclass
class FreeBusyInfo:
    """Represents free/busy information for a calendar."""

    calendar_id: str
    busy_periods: List[dict] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)

    @classmethod
    def from_response(cls, calendar_id: str, data: dict) -> "FreeBusyInfo":
        """Create FreeBusyInfo from API response."""
        return cls(
            calendar_id=calendar_id,
            busy_periods=data.get("busy", []),
            errors=data.get("errors", []),
        )


class GoogleCalendarClient:
    """
    Async client for Google Calendar API.

    Features:
    - OAuth 2.0 authentication via access token
    - Event CRUD operations
    - Calendar management
    - Free/busy queries
    - Natural language event creation (quick add)

    Usage:
        config = CalendarConfig(access_token="ya29.xxx...")
        client = GoogleCalendarClient(config)

        async with client:
            events = await client.list_events(
                calendar_id="primary",
                time_min=datetime.now(),
                max_results=10
            )
    """

    def __init__(self, config: CalendarConfig):
        """Initialize the Google Calendar client.

        Args:
            config: CalendarConfig with access token and settings
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "GoogleCalendarClient":
        """Enter async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Make a request to the Google Calendar API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data

        Returns:
            API response data

        Raises:
            GoogleCalendarAPIError: If the API returns an error
        """
        session = await self._ensure_session()
        url = f"{self.config.base_url}/{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                ) as response:
                    if response.status == 204:
                        return {}

                    result = await response.json()

                    if response.status >= 400:
                        error = result.get("error", {})
                        error_code = error.get("code", response.status)
                        reason = error.get("message", "Unknown error")

                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", "5"))
                            logger.warning(
                                f"Calendar rate limited. Waiting {retry_after}s..."
                            )
                            await asyncio.sleep(retry_after)
                            continue

                        if response.status == 401:
                            raise GoogleCalendarAPIError(
                                "Authentication failed. Access token may be expired.",
                                error_code=401,
                                reason="unauthorized",
                            )

                        raise GoogleCalendarAPIError(
                            f"Calendar API error: {reason}",
                            error_code=error_code,
                            reason=reason,
                        )

                    return result

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(
                        f"Calendar request failed (attempt {attempt + 1}): {e}"
                    )
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise GoogleCalendarAPIError(f"Network error: {e}") from e

        raise GoogleCalendarAPIError("Max retries exceeded")

    # =========================================================================
    # Event Methods
    # =========================================================================

    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 250,
        q: Optional[str] = None,
        order_by: str = "startTime",
        single_events: bool = True,
        show_deleted: bool = False,
        page_token: Optional[str] = None,
    ) -> tuple[List[CalendarEvent], Optional[str]]:
        """
        List events from a calendar.

        Args:
            calendar_id: Calendar ID (default: "primary")
            time_min: Start time filter (inclusive)
            time_max: End time filter (exclusive)
            max_results: Maximum number of events (default 250)
            q: Search query for event text
            order_by: Sort order ("startTime" or "updated")
            single_events: Expand recurring events to instances
            show_deleted: Include deleted events
            page_token: Token for pagination

        Returns:
            Tuple of (list of CalendarEvents, next page token)
        """
        params: dict[str, Any] = {
            "maxResults": min(max_results, 2500),
            "singleEvents": str(single_events).lower(),
            "showDeleted": str(show_deleted).lower(),
            "orderBy": order_by,
        }

        if time_min:
            params["timeMin"] = self._format_datetime(time_min)
        if time_max:
            params["timeMax"] = self._format_datetime(time_max)
        if q:
            params["q"] = q
        if page_token:
            params["pageToken"] = page_token

        result = await self._request(
            "GET",
            f"calendars/{calendar_id}/events",
            params=params,
        )

        events = [
            CalendarEvent.from_response(item, calendar_id)
            for item in result.get("items", [])
        ]
        next_token = result.get("nextPageToken")

        logger.debug(f"Listed {len(events)} events from calendar {calendar_id}")
        return events, next_token

    async def get_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> CalendarEvent:
        """
        Get a single event by ID.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID

        Returns:
            CalendarEvent with event details
        """
        result = await self._request(
            "GET",
            f"calendars/{calendar_id}/events/{event_id}",
        )
        return CalendarEvent.from_response(result, calendar_id)

    async def create_event(
        self,
        calendar_id: str,
        summary: str,
        start: dict,
        end: dict,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[dict]] = None,
        reminders: Optional[dict] = None,
        recurrence: Optional[List[str]] = None,
        visibility: str = "default",
        send_updates: str = "all",
        conference_data_version: Optional[int] = None,
    ) -> CalendarEvent:
        """
        Create a new calendar event.

        Args:
            calendar_id: Calendar ID
            summary: Event title
            start: Start time dict (e.g., {"dateTime": "...", "timeZone": "..."})
            end: End time dict
            description: Event description
            location: Event location
            attendees: List of attendee dicts [{"email": "..."}]
            reminders: Reminders config {"useDefault": False, "overrides": [...]}
            recurrence: RRULE strings for recurring events
            visibility: "default", "public", "private", "confidential"
            send_updates: "all", "externalOnly", "none"
            conference_data_version: Set to 1 to create Meet link

        Returns:
            Created CalendarEvent
        """
        event_data: dict[str, Any] = {
            "summary": summary,
            "start": start,
            "end": end,
        }

        if description:
            event_data["description"] = description
        if location:
            event_data["location"] = location
        if attendees:
            event_data["attendees"] = attendees
        if reminders:
            event_data["reminders"] = reminders
        if recurrence:
            event_data["recurrence"] = recurrence
        if visibility != "default":
            event_data["visibility"] = visibility

        params: dict[str, Any] = {"sendUpdates": send_updates}
        if conference_data_version is not None:
            params["conferenceDataVersion"] = conference_data_version

        result = await self._request(
            "POST",
            f"calendars/{calendar_id}/events",
            params=params,
            json_data=event_data,
        )

        logger.info(f"Created event: {result.get('id')}")
        return CalendarEvent.from_response(result, calendar_id)

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        event_data: dict,
        send_updates: str = "all",
    ) -> CalendarEvent:
        """
        Update an existing event.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID
            event_data: Fields to update (partial update supported)
            send_updates: "all", "externalOnly", "none"

        Returns:
            Updated CalendarEvent
        """
        params = {"sendUpdates": send_updates}

        result = await self._request(
            "PATCH",
            f"calendars/{calendar_id}/events/{event_id}",
            params=params,
            json_data=event_data,
        )

        logger.info(f"Updated event: {event_id}")
        return CalendarEvent.from_response(result, calendar_id)

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
        send_updates: str = "all",
    ) -> bool:
        """
        Delete an event.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID
            send_updates: "all", "externalOnly", "none"

        Returns:
            True if deleted successfully
        """
        params = {"sendUpdates": send_updates}

        await self._request(
            "DELETE",
            f"calendars/{calendar_id}/events/{event_id}",
            params=params,
        )

        logger.info(f"Deleted event: {event_id}")
        return True

    async def quick_add_event(
        self,
        calendar_id: str,
        text: str,
        send_updates: str = "all",
    ) -> CalendarEvent:
        """
        Create an event using natural language.

        Args:
            calendar_id: Calendar ID
            text: Natural language event description
                  (e.g., "Meeting tomorrow at 3pm for 1 hour")
            send_updates: "all", "externalOnly", "none"

        Returns:
            Created CalendarEvent
        """
        params = {
            "text": text,
            "sendUpdates": send_updates,
        }

        result = await self._request(
            "POST",
            f"calendars/{calendar_id}/events/quickAdd",
            params=params,
        )

        logger.info(f"Quick added event: {result.get('id')}")
        return CalendarEvent.from_response(result, calendar_id)

    async def move_event(
        self,
        calendar_id: str,
        event_id: str,
        destination_calendar_id: str,
        send_updates: str = "all",
    ) -> CalendarEvent:
        """
        Move an event to another calendar.

        Args:
            calendar_id: Source calendar ID
            event_id: Event ID
            destination_calendar_id: Destination calendar ID
            send_updates: "all", "externalOnly", "none"

        Returns:
            Moved CalendarEvent
        """
        params = {
            "destination": destination_calendar_id,
            "sendUpdates": send_updates,
        }

        result = await self._request(
            "POST",
            f"calendars/{calendar_id}/events/{event_id}/move",
            params=params,
        )

        logger.info(f"Moved event {event_id} to {destination_calendar_id}")
        return CalendarEvent.from_response(result, destination_calendar_id)

    # =========================================================================
    # Calendar Methods
    # =========================================================================

    async def list_calendars(
        self,
        min_access_role: Optional[str] = None,
        show_deleted: bool = False,
        show_hidden: bool = False,
    ) -> List[Calendar]:
        """
        List all calendars accessible to the user.

        Args:
            min_access_role: Filter by minimum access role
                            ("freeBusyReader", "reader", "writer", "owner")
            show_deleted: Include deleted calendars
            show_hidden: Include hidden calendars

        Returns:
            List of Calendar objects
        """
        params: dict[str, Any] = {
            "showDeleted": str(show_deleted).lower(),
            "showHidden": str(show_hidden).lower(),
        }

        if min_access_role:
            params["minAccessRole"] = min_access_role

        result = await self._request("GET", "users/me/calendarList", params=params)

        calendars = [Calendar.from_response(item) for item in result.get("items", [])]

        logger.debug(f"Listed {len(calendars)} calendars")
        return calendars

    async def get_calendar(self, calendar_id: str) -> Calendar:
        """
        Get a calendar by ID.

        Args:
            calendar_id: Calendar ID

        Returns:
            Calendar object
        """
        result = await self._request(
            "GET",
            f"users/me/calendarList/{calendar_id}",
        )
        return Calendar.from_response(result)

    async def create_calendar(
        self,
        summary: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Calendar:
        """
        Create a new calendar.

        Args:
            summary: Calendar name
            description: Calendar description
            location: Calendar location
            timezone: Calendar timezone (e.g., "America/New_York")

        Returns:
            Created Calendar
        """
        calendar_data: dict[str, Any] = {"summary": summary}

        if description:
            calendar_data["description"] = description
        if location:
            calendar_data["location"] = location
        if timezone:
            calendar_data["timeZone"] = timezone

        result = await self._request(
            "POST",
            "calendars",
            json_data=calendar_data,
        )

        logger.info(f"Created calendar: {result.get('id')}")
        return Calendar.from_response(result)

    async def delete_calendar(self, calendar_id: str) -> bool:
        """
        Delete a calendar.

        Args:
            calendar_id: Calendar ID (cannot be "primary")

        Returns:
            True if deleted successfully

        Raises:
            GoogleCalendarAPIError: If trying to delete primary calendar
        """
        if calendar_id == "primary":
            raise GoogleCalendarAPIError(
                "Cannot delete primary calendar",
                error_code=400,
                reason="primaryCalendarDeletion",
            )

        await self._request("DELETE", f"calendars/{calendar_id}")
        logger.info(f"Deleted calendar: {calendar_id}")
        return True

    # =========================================================================
    # Free/Busy Methods
    # =========================================================================

    async def get_free_busy(
        self,
        calendar_ids: List[str],
        time_min: datetime,
        time_max: datetime,
        group_expansion_max: int = 100,
        calendar_expansion_max: int = 50,
    ) -> dict[str, FreeBusyInfo]:
        """
        Query free/busy information for calendars.

        Args:
            calendar_ids: List of calendar IDs to query
            time_min: Start of time range
            time_max: End of time range
            group_expansion_max: Max group members to expand
            calendar_expansion_max: Max calendars to expand

        Returns:
            Dictionary mapping calendar ID to FreeBusyInfo
        """
        request_data = {
            "timeMin": self._format_datetime(time_min),
            "timeMax": self._format_datetime(time_max),
            "items": [{"id": cal_id} for cal_id in calendar_ids],
            "groupExpansionMax": group_expansion_max,
            "calendarExpansionMax": calendar_expansion_max,
        }

        result = await self._request(
            "POST",
            "freeBusy",
            json_data=request_data,
        )

        calendars_data = result.get("calendars", {})
        free_busy_info = {}

        for cal_id, data in calendars_data.items():
            free_busy_info[cal_id] = FreeBusyInfo.from_response(cal_id, data)

        logger.debug(f"Got free/busy for {len(free_busy_info)} calendars")
        return free_busy_info

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for API (RFC3339)."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


__all__ = [
    "GoogleCalendarClient",
    "GoogleCalendarAPIError",
    "CalendarConfig",
    "CalendarEvent",
    "Calendar",
    "FreeBusyInfo",
]
