"""
CasareRPA - File Watch Trigger

Trigger that fires when files in a watched directory change.
Uses watchdog library for efficient filesystem monitoring.
"""

import asyncio
import fnmatch
from datetime import datetime, timezone
from pathlib import Path
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
class FileWatchTrigger(BaseTrigger):
    """
    Trigger that monitors filesystem changes.

    Configuration options:
        watch_path: Directory path to watch
        patterns: File patterns to match (e.g., ["*.pdf", "*.csv"])
        recursive: Watch subdirectories
        events: Event types to watch (created, modified, deleted, moved)
        debounce_ms: Debounce time in milliseconds to prevent rapid re-triggers

    Payload provided to workflow:
        file_path: Full path of the changed file
        file_name: Name of the file
        event_type: Type of change (created, modified, deleted, moved)
        timestamp: When the event occurred
    """

    trigger_type = TriggerType.FILE_WATCH
    display_name = "File Watch"
    description = "Trigger when files change in a directory"
    icon = "folder"
    category = "Local"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._observer = None
        self._handler = None
        self._task: Optional[asyncio.Task] = None
        self._pending_events: Dict[str, datetime] = {}
        self._debounce_task: Optional[asyncio.Task] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> bool:
        """Start the file watch trigger."""
        config = self.config.config
        watch_path = config.get("watch_path", "")

        if not watch_path:
            self._error_message = "watch_path is required"
            self._status = TriggerStatus.ERROR
            return False

        path = Path(watch_path)
        if not path.exists():
            self._error_message = f"Watch path does not exist: {watch_path}"
            self._status = TriggerStatus.ERROR
            return False

        if not path.is_dir():
            self._error_message = f"Watch path is not a directory: {watch_path}"
            self._status = TriggerStatus.ERROR
            return False

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileSystemEvent

            # Store event loop reference for cross-thread communication
            # This avoids calling asyncio.get_event_loop() from watchdog's thread
            self._event_loop = asyncio.get_running_loop()

            # Create custom event handler
            trigger = self  # Capture reference for handler
            loop = self._event_loop  # Capture for closure

            class TriggerHandler(FileSystemEventHandler):
                def on_any_event(self, event: FileSystemEvent):
                    if event.is_directory:
                        return

                    # Check if event type is in our watched events
                    event_type = event.event_type  # created, modified, deleted, moved
                    watched_events = config.get("events", ["created", "modified"])
                    if event_type not in watched_events:
                        return

                    # Check if file matches patterns
                    patterns = config.get("patterns", ["*"])
                    file_name = Path(event.src_path).name
                    matches = any(fnmatch.fnmatch(file_name, p) for p in patterns)
                    if not matches:
                        return

                    # Queue the event for debounced processing
                    # Use stored event loop reference (captured in closure)
                    # to avoid calling asyncio.get_event_loop() from this thread
                    asyncio.run_coroutine_threadsafe(
                        trigger._queue_event(event.src_path, event_type),
                        loop,
                    )

            self._handler = TriggerHandler()
            self._observer = Observer()

            recursive = config.get("recursive", False)
            self._observer.schedule(self._handler, str(path), recursive=recursive)
            self._observer.start()

            self._status = TriggerStatus.ACTIVE
            logger.info(
                f"File watch trigger started: {self.config.name} "
                f"(path: {watch_path}, recursive: {recursive})"
            )
            return True

        except ImportError:
            logger.error("watchdog not installed. Install with: pip install watchdog")
            self._status = TriggerStatus.ERROR
            self._error_message = "watchdog not installed"
            return False
        except Exception as e:
            logger.error(f"Failed to start file watch trigger: {e}")
            self._status = TriggerStatus.ERROR
            self._error_message = str(e)
            return False

    async def stop(self) -> bool:
        """Stop the file watch trigger."""
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=5)
            except Exception as e:
                logger.warning(f"Error stopping file observer: {e}")
            self._observer = None

        if self._debounce_task:
            self._debounce_task.cancel()
            self._debounce_task = None

        self._pending_events.clear()
        self._status = TriggerStatus.INACTIVE
        logger.info(f"File watch trigger stopped: {self.config.name}")
        return True

    async def _queue_event(self, file_path: str, event_type: str) -> None:
        """Queue a file event for debounced processing."""
        debounce_ms = self.config.config.get("debounce_ms", 1000)

        # Record the event
        self._pending_events[file_path] = datetime.now(timezone.utc)

        # Cancel existing debounce task if any
        if self._debounce_task and not self._debounce_task.done():
            return  # Let the existing task handle it

        # Create new debounce task
        self._debounce_task = asyncio.create_task(
            self._process_events_after_debounce(debounce_ms / 1000.0, event_type)
        )

    async def _process_events_after_debounce(
        self, debounce_seconds: float, event_type: str
    ) -> None:
        """Process pending events after debounce period."""
        await asyncio.sleep(debounce_seconds)

        # Process all pending events
        events_to_process = dict(self._pending_events)
        self._pending_events.clear()

        for file_path, timestamp in events_to_process.items():
            path = Path(file_path)
            payload = {
                "file_path": str(path),
                "file_name": path.name,
                "file_dir": str(path.parent),
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
            }

            metadata = {
                "source": "file_watch",
                "watch_path": self.config.config.get("watch_path", ""),
            }

            await self.emit(payload, metadata)

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate file watch configuration."""
        config = self.config.config

        watch_path = config.get("watch_path", "")
        if not watch_path:
            return False, "watch_path is required"

        # SECURITY: Validate path to prevent watching sensitive system directories
        try:
            resolved_path = Path(watch_path).resolve()

            # Block watching sensitive system directories
            blocked_paths = [
                Path("C:/Windows").resolve(),
                Path("C:/Program Files").resolve(),
                Path("C:/Program Files (x86)").resolve(),
                Path("/etc").resolve(),
                Path("/var").resolve(),
                Path("/usr").resolve(),
                Path("/bin").resolve(),
                Path("/sbin").resolve(),
            ]

            for blocked in blocked_paths:
                try:
                    # Check if resolved_path is under a blocked directory
                    resolved_path.relative_to(blocked)
                    return (
                        False,
                        f"Cannot watch system directory: {watch_path}. "
                        "File watching is not allowed for sensitive system paths.",
                    )
                except ValueError:
                    # Path is not relative to blocked path - this is fine
                    pass

            # Check for path traversal attempts in the original path
            if ".." in watch_path:
                return (
                    False,
                    "Path traversal detected in watch_path. "
                    "Please use an absolute path without '..' components.",
                )

        except Exception as e:
            return False, f"Invalid watch_path: {e}"

        # Validate events
        events = config.get("events", ["created", "modified"])
        valid_events = ["created", "modified", "deleted", "moved"]
        for event in events:
            if event not in valid_events:
                return (
                    False,
                    f"Invalid event type: {event}. Must be one of: {valid_events}",
                )

        # Validate debounce
        debounce = config.get("debounce_ms", 1000)
        if debounce < 0:
            return False, "debounce_ms must be >= 0"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for file watch configuration."""
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
                "watch_path": {
                    "type": "string",
                    "description": "Directory path to watch",
                },
                "patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["*"],
                    "description": "File patterns to match (glob syntax)",
                    "examples": [["*.pdf", "*.csv"], ["invoice_*.xml"]],
                },
                "recursive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Watch subdirectories",
                },
                "events": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["created", "modified", "deleted", "moved"],
                    },
                    "default": ["created", "modified"],
                    "description": "File event types to watch",
                },
                "debounce_ms": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 1000,
                    "description": "Debounce time in milliseconds",
                },
            },
            "required": ["name", "watch_path"],
        }
