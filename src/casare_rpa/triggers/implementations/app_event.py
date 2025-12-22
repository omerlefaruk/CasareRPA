"""
CasareRPA - App Event Trigger

Trigger that fires on application events (Windows, browser, or internal RPA).
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerStatus,
    TriggerType,
)
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class AppEventTrigger(BaseTrigger):
    """
    Trigger that responds to application events.

    Configuration options:
        event_source: Source of events (windows, browser, rpa)
        event_types: List of event types to monitor
        window_title_pattern: Regex pattern for window titles (windows source)
        process_name: Process name filter (windows source)
        url_pattern: URL pattern for browser events

    Supported event sources:
    - windows: Window focus, app launch, USB connect, etc.
    - browser: Tab opened, URL visited, page loaded
    - rpa: Internal RPA events (workflow complete, robot status, etc.)

    Payload provided to workflow:
        event_type: Type of event that occurred
        event_data: Event-specific data
        timestamp: When the event occurred
    """

    trigger_type = TriggerType.APP_EVENT
    display_name = "App Event"
    description = "Trigger on application or system events"
    icon = "desktop"
    category = "System"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._poll_task: Optional[asyncio.Task] = None
        self._event_subscriptions = []
        self._running = False

    async def start(self) -> bool:
        """Start the app event trigger."""
        config = self.config.config
        event_source = config.get("event_source", "rpa")

        self._running = True
        self._status = TriggerStatus.ACTIVE

        if event_source == "windows":
            success = await self._start_windows_monitor()
        elif event_source == "browser":
            success = await self._start_browser_monitor()
        elif event_source == "rpa":
            success = await self._start_rpa_monitor()
        else:
            self._error_message = f"Unknown event source: {event_source}"
            self._status = TriggerStatus.ERROR
            return False

        if not success:
            self._running = False
            self._status = TriggerStatus.ERROR
            return False

        logger.info(f"App event trigger started: {self.config.name} (source: {event_source})")
        return True

    async def stop(self) -> bool:
        """Stop the app event trigger."""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        # Unsubscribe from events
        for unsubscribe in self._event_subscriptions:
            try:
                unsubscribe()
            except Exception:
                pass
        self._event_subscriptions.clear()

        self._status = TriggerStatus.INACTIVE
        logger.info(f"App event trigger stopped: {self.config.name}")
        return True

    async def _start_windows_monitor(self) -> bool:
        """Start monitoring Windows events."""
        config = self.config.config
        config.get("event_types", ["window_focus"])

        try:
            # Try to use win32api for Windows events
            import ctypes
            from ctypes import wintypes

            # Start polling task for window monitoring
            self._poll_task = asyncio.create_task(self._poll_windows_events())
            return True

        except ImportError:
            logger.warning("win32api not available - using basic window polling")
            self._poll_task = asyncio.create_task(self._poll_windows_events())
            return True
        except Exception as e:
            self._error_message = f"Failed to start Windows monitor: {e}"
            logger.error(self._error_message)
            return False

    async def _poll_windows_events(self) -> None:
        """Poll for Windows events."""
        config = self.config.config
        window_title_pattern = config.get("window_title_pattern", "")
        config.get("process_name", "")
        poll_interval = config.get("poll_interval", 1)

        last_window_title = ""

        while self._running:
            try:
                # Get foreground window title
                import ctypes

                user32 = ctypes.windll.user32

                hwnd = user32.GetForegroundWindow()
                length = user32.GetWindowTextLengthW(hwnd) + 1
                buffer = ctypes.create_unicode_buffer(length)
                user32.GetWindowTextW(hwnd, buffer, length)
                current_title = buffer.value

                # Check if window changed
                if current_title != last_window_title:
                    last_window_title = current_title

                    # Check if matches filter
                    if window_title_pattern:
                        if not re.search(window_title_pattern, current_title, re.IGNORECASE):
                            continue

                    # Emit event
                    payload = {
                        "event_type": "window_focus",
                        "window_title": current_title,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    metadata = {
                        "source": "windows",
                    }

                    await self.emit(payload, metadata)

            except Exception as e:
                logger.debug(f"Windows event poll error: {e}")

            await asyncio.sleep(poll_interval)

    async def _start_browser_monitor(self) -> bool:
        """Start monitoring browser events."""
        # Browser events would typically require a browser extension
        # or integration with Playwright/Selenium
        logger.warning("Browser event monitoring requires browser extension integration")

        # Start a placeholder polling task
        self._poll_task = asyncio.create_task(self._poll_browser_events())
        return True

    async def _poll_browser_events(self) -> None:
        """Poll for browser events (placeholder)."""
        while self._running:
            # Browser event monitoring would be implemented here
            # This could integrate with existing Playwright sessions
            await asyncio.sleep(5)

    async def _start_rpa_monitor(self) -> bool:
        """Start monitoring internal RPA events."""
        config = self.config.config
        event_types = config.get("event_types", ["workflow_completed"])

        try:
            from casare_rpa.domain.events import (
                get_event_bus,
                WorkflowStarted,
                WorkflowCompleted,
                WorkflowFailed,
                WorkflowStopped,
                NodeStarted,
                NodeCompleted,
                NodeFailed,
            )

            event_bus = get_event_bus()

            # Map event type strings to typed event classes
            event_map = {
                "workflow_started": WorkflowStarted,
                "workflow_completed": WorkflowCompleted,
                "workflow_error": WorkflowFailed,
                "workflow_stopped": WorkflowStopped,
                "node_started": NodeStarted,
                "node_completed": NodeCompleted,
                "node_error": NodeFailed,
            }

            def make_handler(et_str: str):
                """Create event handler for event type."""

                def handler(e):
                    asyncio.create_task(self._on_rpa_event(et_str, e))

                return handler

            for event_type_str in event_types:
                event_class = event_map.get(event_type_str)
                if event_class:
                    handler = make_handler(event_type_str)
                    event_bus.subscribe(event_class, handler)
                    self._event_subscriptions.append(
                        lambda ec=event_class, h=handler: event_bus.unsubscribe(ec, h)
                    )

            return True

        except Exception as e:
            self._error_message = f"Failed to start RPA monitor: {e}"
            logger.error(self._error_message)
            return False

    async def _on_rpa_event(self, event_type: str, event) -> None:
        """Handle internal RPA event."""
        # Extract node_id from typed events (they have node_id attribute for node events)
        node_id = getattr(event, "node_id", None)

        # Extract timestamp from typed events
        timestamp = getattr(event, "timestamp", None)
        if timestamp:
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = datetime.now(timezone.utc).isoformat()

        payload = {
            "event_type": event_type,
            "node_id": node_id,
            "timestamp": timestamp_str,
        }

        metadata = {
            "source": "rpa",
        }

        await self.emit(payload, metadata)

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate app event trigger configuration."""
        config = self.config.config

        event_source = config.get("event_source", "rpa")
        valid_sources = ["windows", "browser", "rpa"]
        if event_source not in valid_sources:
            return False, f"Invalid event_source. Must be one of: {valid_sources}"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for app event configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "event_source": {
                    "type": "string",
                    "enum": ["windows", "browser", "rpa"],
                    "default": "rpa",
                    "description": "Source of events",
                },
                "event_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["workflow_completed"],
                    "description": "Event types to monitor",
                },
                "window_title_pattern": {
                    "type": "string",
                    "description": "Regex pattern for window titles (windows source)",
                },
                "process_name": {
                    "type": "string",
                    "description": "Process name filter (windows source)",
                },
                "url_pattern": {
                    "type": "string",
                    "description": "URL pattern for browser events",
                },
                "poll_interval": {
                    "type": "number",
                    "default": 1,
                    "description": "Polling interval in seconds",
                },
            },
            "required": ["name"],
        }
