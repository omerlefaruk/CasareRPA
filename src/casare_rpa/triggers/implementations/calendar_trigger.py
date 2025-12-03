"""
CasareRPA - Google Calendar Trigger

Trigger that fires when calendar events start, are created, or updated.
Uses Google Calendar API with OAuth 2.0 authentication.

Event types:
- created: New event added to calendar
- updated: Existing event modified
- starting_soon: Event starting within X minutes
- started: Event has started
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.triggers.registry import register_trigger
from casare_rpa.triggers.implementations.google_trigger_base import GoogleTriggerBase


@register_trigger
class CalendarTrigger(GoogleTriggerBase):
    """
    Trigger that monitors Google Calendar for events.

    Configuration options:
        client_id: Google OAuth client ID
        client_secret_credential: Credential alias for client secret
        access_token_credential: Credential alias for access token
        refresh_token_credential: Credential alias for refresh token
        calendar_id: Calendar to watch (default: "primary")
        poll_interval: Check frequency in seconds (default: 60)
        event_types: List of event types to watch:
            - "created": New events
            - "updated": Modified events
            - "starting_soon": Events starting within minutes_before
            - "started": Events that have just started
        minutes_before: Minutes before event for "starting_soon" trigger (default: 15)
        query: Event search filter (optional)
        single_events: Expand recurring events into instances (default: True)
        time_min: Only events after this time (ISO format, optional)
        time_max: Only events before this time (ISO format, optional)

    Payload provided to workflow:
        event_id: Calendar event ID
        calendar_id: Calendar ID
        summary: Event title
        description: Event description
        start: Event start time (ISO format)
        end: Event end time (ISO format)
        location: Event location
        attendees: List of attendee emails
        event_type: Trigger event type (created, updated, starting_soon, started)
        minutes_until_start: Minutes until event starts (for starting_soon)
        organizer: Event organizer email
        html_link: Link to view event in Google Calendar
        status: Event status (confirmed, tentative, cancelled)
        created: When event was created
        updated: When event was last updated
    """

    trigger_type = TriggerType.CALENDAR
    display_name = "Calendar: Event"
    description = "Trigger when calendar event starts, is created, or updated"
    icon = "calendar"
    category = "Google"

    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        # Sync token for incremental sync
        self._sync_token: Optional[str] = None
        # Track events we've already notified about
        self._notified_starting_soon: Set[str] = set()
        self._notified_started: Set[str] = set()
        # Track known events for change detection
        self._known_events: Dict[str, Dict[str, Any]] = {}
        # Last poll timestamp for started detection
        self._last_poll_time: Optional[datetime] = None

    def get_required_scopes(self) -> list[str]:
        """Return required Google Calendar API scopes."""
        return [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events.readonly",
        ]

    async def start(self) -> bool:
        """Start the Calendar trigger."""
        result = await super().start()
        if result:
            try:
                await self._initialize_sync()
            except Exception as e:
                logger.warning(f"Failed to initialize Calendar sync: {e}")
        return result

    async def _initialize_sync(self) -> None:
        """Initialize calendar sync by getting initial event list."""
        client = await self._get_google_client()
        config = self.config.config
        calendar_id = config.get("calendar_id", "primary")

        # Get initial list of events to establish baseline
        params = self._build_list_params()

        try:
            response = await client.get(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events",
                params=params,
            )

            # Store sync token for incremental updates
            self._sync_token = response.get("nextSyncToken")

            # Build known events map
            for event in response.get("items", []):
                event_id = event.get("id", "")
                if event_id:
                    self._known_events[event_id] = {
                        "updated": event.get("updated", ""),
                        "start": self._get_event_start(event),
                    }

            self._last_poll_time = datetime.now(timezone.utc)
            logger.debug(
                f"Calendar sync initialized: {len(self._known_events)} events, "
                f"sync_token: {self._sync_token[:16] if self._sync_token else 'none'}..."
            )
        except Exception as e:
            logger.error(f"Failed to initialize calendar sync: {e}")
            raise

    def _build_list_params(self) -> Dict[str, str]:
        """Build query parameters for event list API."""
        config = self.config.config
        params: Dict[str, str] = {
            "maxResults": "250",
            "orderBy": "updated",
            "showDeleted": "false",
        }

        # Single events (expand recurring)
        if config.get("single_events", True):
            params["singleEvents"] = "true"
            params["orderBy"] = "startTime"

        # Time bounds
        time_min = config.get("time_min", "")
        if not time_min:
            # Default: events from now
            time_min = datetime.now(timezone.utc).isoformat()
        params["timeMin"] = time_min

        time_max = config.get("time_max", "")
        if time_max:
            params["timeMax"] = time_max

        # Search query
        query = config.get("query", "")
        if query:
            params["q"] = query

        return params

    def _get_event_start(self, event: Dict[str, Any]) -> Optional[datetime]:
        """Extract start time from event."""
        start_data = event.get("start", {})
        # Events can have dateTime (specific time) or date (all-day)
        start_str = start_data.get("dateTime") or start_data.get("date")
        if start_str:
            try:
                # Parse ISO format datetime
                if "T" in start_str:
                    return datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    # All-day event (date only)
                    return datetime.strptime(start_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
            except ValueError:
                logger.warning(f"Could not parse event start time: {start_str}")
        return None

    async def _poll(self) -> None:
        """Poll Google Calendar for changes and upcoming events."""
        config = self.config.config
        event_types = config.get("event_types", ["starting_soon"])
        if isinstance(event_types, str):
            event_types = [event_types]

        try:
            client = await self._get_google_client()
            calendar_id = config.get("calendar_id", "primary")

            # Check for created/updated events using sync
            if "created" in event_types or "updated" in event_types:
                await self._poll_for_changes(client, calendar_id, event_types)

            # Check for starting_soon/started events
            if "starting_soon" in event_types or "started" in event_types:
                await self._poll_for_upcoming(client, calendar_id, event_types)

            self._last_poll_time = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Calendar poll error: {e}")
            raise

    async def _poll_for_changes(
        self, client, calendar_id: str, event_types: List[str]
    ) -> None:
        """Poll for created/updated events using incremental sync."""
        if not self._sync_token:
            # Re-initialize if no sync token
            await self._initialize_sync()
            return

        try:
            # Use sync token for incremental updates
            response = await client.get(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events",
                params={"syncToken": self._sync_token},
            )

            # Update sync token
            self._sync_token = response.get("nextSyncToken")

            # Process changes
            for event in response.get("items", []):
                event_id = event.get("id", "")
                if not event_id:
                    continue

                # Skip cancelled events
                if event.get("status") == "cancelled":
                    if event_id in self._known_events:
                        del self._known_events[event_id]
                    continue

                # Determine if this is new or updated
                is_new = event_id not in self._known_events
                is_updated = False

                if not is_new:
                    old_updated = self._known_events[event_id].get("updated", "")
                    new_updated = event.get("updated", "")
                    is_updated = old_updated != new_updated

                # Update known events
                self._known_events[event_id] = {
                    "updated": event.get("updated", ""),
                    "start": self._get_event_start(event),
                }

                # Emit appropriate trigger
                if is_new and "created" in event_types:
                    await self._emit_event(event, "created", calendar_id)
                elif is_updated and "updated" in event_types:
                    await self._emit_event(event, "updated", calendar_id)

        except Exception as e:
            error_str = str(e)
            # If sync token is invalid, reset
            if "410" in error_str or "syncToken" in error_str.lower():
                logger.warning("Sync token invalid, reinitializing...")
                self._sync_token = None
                self._known_events.clear()
                await self._initialize_sync()
            else:
                raise

    async def _poll_for_upcoming(
        self, client, calendar_id: str, event_types: List[str]
    ) -> None:
        """Check for events starting soon or just started."""
        config = self.config.config
        minutes_before = config.get("minutes_before", 15)
        now = datetime.now(timezone.utc)

        # Get events in the near future
        time_min = now.isoformat()
        time_max = (now + timedelta(minutes=minutes_before + 5)).isoformat()

        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": "50",
        }

        query = config.get("query", "")
        if query:
            params["q"] = query

        response = await client.get(
            f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events",
            params=params,
        )

        for event in response.get("items", []):
            event_id = event.get("id", "")
            if not event_id or event.get("status") == "cancelled":
                continue

            event_start = self._get_event_start(event)
            if not event_start:
                continue

            # Calculate time until start
            time_diff = event_start - now
            minutes_until = time_diff.total_seconds() / 60

            # Check for starting_soon
            if (
                "starting_soon" in event_types
                and 0 < minutes_until <= minutes_before
                and event_id not in self._notified_starting_soon
            ):
                await self._emit_event(
                    event, "starting_soon", calendar_id, int(minutes_until)
                )
                self._notified_starting_soon.add(event_id)

            # Check for started (event started since last poll)
            if "started" in event_types and event_id not in self._notified_started:
                if minutes_until <= 0 and minutes_until > -5:
                    # Event started within last 5 minutes
                    await self._emit_event(event, "started", calendar_id, 0)
                    self._notified_started.add(event_id)

        # Cleanup old notifications (events that are now in the past)
        cutoff = now - timedelta(hours=24)
        self._notified_starting_soon = {
            eid
            for eid in self._notified_starting_soon
            if eid in self._known_events
            and self._known_events[eid].get("start")
            and self._known_events[eid]["start"] > cutoff
        }
        self._notified_started = {
            eid
            for eid in self._notified_started
            if eid in self._known_events
            and self._known_events[eid].get("start")
            and self._known_events[eid]["start"] > cutoff
        }

    async def _emit_event(
        self,
        event: Dict[str, Any],
        event_type: str,
        calendar_id: str,
        minutes_until_start: int = 0,
    ) -> None:
        """Emit trigger event for a calendar event."""
        start_data = event.get("start", {})
        end_data = event.get("end", {})

        # Extract attendees
        attendees = []
        for attendee in event.get("attendees", []):
            email = attendee.get("email", "")
            if email:
                attendees.append(email)

        # Get organizer
        organizer_data = event.get("organizer", {})
        organizer = organizer_data.get("email", "")

        payload = {
            "event_id": event.get("id", ""),
            "calendar_id": calendar_id,
            "summary": event.get("summary", ""),
            "description": event.get("description", ""),
            "start": start_data.get("dateTime") or start_data.get("date", ""),
            "end": end_data.get("dateTime") or end_data.get("date", ""),
            "location": event.get("location", ""),
            "attendees": attendees,
            "event_type": event_type,
            "minutes_until_start": minutes_until_start,
            "organizer": organizer,
            "html_link": event.get("htmlLink", ""),
            "status": event.get("status", ""),
            "created": event.get("created", ""),
            "updated": event.get("updated", ""),
            "recurring_event_id": event.get("recurringEventId", ""),
            "timezone": start_data.get("timeZone", ""),
        }

        metadata = {
            "source": "google_calendar",
            "event_type": event_type,
            "calendar_id": calendar_id,
            "event_id": event.get("id", ""),
        }

        await self.emit(payload, metadata)
        logger.info(
            f"Calendar trigger fired: {event_type} - "
            f"{event.get('summary', 'Untitled')} "
            f"(in {minutes_until_start} min)"
            if event_type == "starting_soon"
            else ""
        )

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate Google Calendar trigger configuration."""
        valid, error = super().validate_config()
        if not valid:
            return valid, error

        config = self.config.config

        # Validate event_types
        event_types = config.get("event_types", ["starting_soon"])
        if isinstance(event_types, str):
            event_types = [event_types]

        valid_types = ["created", "updated", "starting_soon", "started"]
        for et in event_types:
            if et not in valid_types:
                return (
                    False,
                    f"Invalid event_type '{et}'. Must be one of: {valid_types}",
                )

        # Validate minutes_before
        minutes_before = config.get("minutes_before", 15)
        if not isinstance(minutes_before, int) or minutes_before < 1:
            return False, "minutes_before must be a positive integer"
        if minutes_before > 1440:  # 24 hours
            return False, "minutes_before cannot exceed 1440 (24 hours)"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Google Calendar trigger configuration."""
        base_schema = super().get_config_schema()
        base_schema["properties"].update(
            {
                "calendar_id": {
                    "type": "string",
                    "default": "primary",
                    "description": "Calendar ID to monitor (default: primary)",
                },
                "event_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["created", "updated", "starting_soon", "started"],
                    },
                    "default": ["starting_soon"],
                    "description": "Types of events to trigger on",
                },
                "minutes_before": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1440,
                    "default": 15,
                    "description": "Minutes before event for 'starting_soon' trigger",
                },
                "query": {
                    "type": "string",
                    "description": "Search query to filter events",
                },
                "single_events": {
                    "type": "boolean",
                    "default": True,
                    "description": "Expand recurring events into instances",
                },
                "time_min": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Only events after this time (ISO format)",
                },
                "time_max": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Only events before this time (ISO format)",
                },
            }
        )
        return base_schema


__all__ = ["CalendarTrigger"]
