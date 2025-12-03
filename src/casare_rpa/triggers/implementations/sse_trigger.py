"""
CasareRPA - Server-Sent Events (SSE) Trigger

Trigger that fires when events are received from an SSE stream.
Connects to SSE endpoints and emits events for incoming messages.
"""

import asyncio
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger

from casare_rpa.triggers.base import BaseTrigger, TriggerStatus, TriggerType
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class SSETrigger(BaseTrigger):
    """
    Trigger that listens to Server-Sent Events (SSE) streams.

    Configuration options:
        url: URL of the SSE endpoint
        event_types: List of event types to listen for (empty = all events)
        headers: Custom headers to send with connection
        auth_type: Authentication type (none, bearer, basic)
        auth_token: Token for bearer auth or "user:password" for basic
        reconnect_delay: Delay before reconnecting on disconnect (seconds)
        max_reconnects: Maximum reconnection attempts (0 = unlimited)
        filter_data: Only trigger if data contains this string

    Outputs:
        event_type: Type of SSE event (e.g., "message")
        data: Event data (string or parsed JSON)
        id: Event ID (if provided)
        retry: Retry value (if provided)
    """

    trigger_type = TriggerType.SSE
    display_name = "Server-Sent Events"
    description = "Trigger when events are received from SSE stream"
    icon = "broadcast"
    category = "External"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._listen_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._reconnect_count: int = 0
        self._last_event_id: Optional[str] = None

    async def start(self) -> bool:
        """Start listening to the SSE stream."""
        try:
            # Validate config first
            is_valid, error = self.validate_config()
            if not is_valid:
                self._error_message = error
                self._status = TriggerStatus.ERROR
                return False

            self._status = TriggerStatus.STARTING
            self._reconnect_count = 0

            # Create HTTP session with headers
            headers = self._build_headers()
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=None, sock_read=None),
            )

            # Start listening task
            self._listen_task = asyncio.create_task(self._listen_loop())
            self._status = TriggerStatus.ACTIVE

            logger.info(
                f"SSE trigger started: {self.config.name} "
                f"(url: {self.config.config.get('url')})"
            )
            return True

        except Exception as e:
            self._error_message = str(e)
            self._status = TriggerStatus.ERROR
            logger.error(f"Failed to start SSE trigger: {e}")
            return False

    async def stop(self) -> bool:
        """Stop listening to the SSE stream."""
        try:
            # Cancel listen task
            if self._listen_task and not self._listen_task.done():
                self._listen_task.cancel()
                try:
                    await self._listen_task
                except asyncio.CancelledError:
                    pass

            # Close session
            if self._session:
                await self._session.close()
                self._session = None

            self._status = TriggerStatus.INACTIVE
            logger.info(f"SSE trigger stopped: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"Error stopping SSE trigger: {e}")
            return False

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate SSE trigger configuration."""
        config = self.config.config

        # URL is required
        url = config.get("url", "")
        if not url:
            return False, "url is required"

        if not url.startswith(("http://", "https://")):
            return False, "url must be a valid HTTP(S) URL"

        # Auth type validation
        auth_type = config.get("auth_type", "none")
        valid_auth_types = ["none", "bearer", "basic"]
        if auth_type not in valid_auth_types:
            return False, f"auth_type must be one of: {valid_auth_types}"

        # Auth token required for non-none auth
        if auth_type != "none" and not config.get("auth_token"):
            return False, f"auth_token is required for auth_type '{auth_type}'"

        # Reconnect delay validation
        reconnect_delay = config.get("reconnect_delay", 5)
        if reconnect_delay < 0:
            return False, "reconnect_delay must be >= 0"

        return True, None

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for the SSE connection."""
        config = self.config.config
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }

        # Add custom headers
        custom_headers = config.get("headers", {})
        headers.update(custom_headers)

        # Add auth header
        auth_type = config.get("auth_type", "none")
        auth_token = config.get("auth_token", "")

        if auth_type == "bearer" and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        elif auth_type == "basic" and auth_token:
            import base64

            encoded = base64.b64encode(auth_token.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        # Add Last-Event-ID if we have one
        if self._last_event_id:
            headers["Last-Event-ID"] = self._last_event_id

        return headers

    async def _listen_loop(self) -> None:
        """Main SSE listening loop with reconnection."""
        max_reconnects = self.config.config.get("max_reconnects", 0)
        # Enforce minimum reconnect delay to prevent tight loop
        reconnect_delay = max(self.config.config.get("reconnect_delay", 5), 1)

        while self._status == TriggerStatus.ACTIVE:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE connection error: {e}")
                self._error_message = str(e)

                self._reconnect_count += 1
                if max_reconnects > 0 and self._reconnect_count > max_reconnects:
                    logger.error(
                        f"SSE trigger max reconnects exceeded: {self.config.name}"
                    )
                    self._status = TriggerStatus.ERROR
                    break

                logger.info(f"SSE trigger reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)

    async def _connect_and_listen(self) -> None:
        """Connect to SSE endpoint and process events."""
        if not self._session:
            raise RuntimeError("HTTP session not initialized")

        url = self.config.config.get("url")

        # Update headers for reconnection
        headers = self._build_headers()

        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()

            # Reset reconnect count on successful connection
            self._reconnect_count = 0
            logger.debug(f"SSE connected to: {url}")

            # Process SSE stream
            await self._process_stream(response)

    async def _process_stream(self, response: aiohttp.ClientResponse) -> None:
        """Process the SSE event stream."""
        event_types = set(self.config.config.get("event_types", []))
        filter_data = self.config.config.get("filter_data", "")

        # SSE event buffer
        event_type = "message"
        event_data = []
        event_id = None
        retry = None

        async for line in response.content:
            line = line.decode("utf-8").rstrip("\r\n")

            # Empty line = end of event
            if not line:
                if event_data:
                    data = "\n".join(event_data)

                    # Apply filters
                    if event_types and event_type not in event_types:
                        pass
                    elif filter_data and filter_data not in data:
                        pass
                    else:
                        await self._emit_event(event_type, data, event_id, retry)

                # Reset for next event
                event_type = "message"
                event_data = []
                event_id = None
                continue

            # Parse SSE field
            if line.startswith(":"):
                # Comment, ignore
                continue
            elif line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                event_data.append(line[5:].strip())
            elif line.startswith("id:"):
                event_id = line[3:].strip()
                self._last_event_id = event_id
            elif line.startswith("retry:"):
                try:
                    retry = int(line[6:].strip())
                except ValueError:
                    pass

    async def _emit_event(
        self,
        event_type: str,
        data: str,
        event_id: Optional[str],
        retry: Optional[int],
    ) -> None:
        """Emit a trigger event for an SSE message."""
        # Try to parse JSON data
        parsed_data: Any = data
        try:
            import json

            parsed_data = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            pass

        payload = {
            "event_type": event_type,
            "data": parsed_data,
            "id": event_id,
            "retry": retry,
        }

        await self.emit(
            payload=payload,
            metadata={
                "url": self.config.config.get("url"),
                "raw_data": data,
            },
        )

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for SSE trigger configuration."""
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
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of the SSE endpoint",
                },
                "event_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Event types to listen for (empty = all)",
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "description": "Custom headers for the connection",
                },
                "auth_type": {
                    "type": "string",
                    "enum": ["none", "bearer", "basic"],
                    "default": "none",
                    "description": "Authentication type",
                },
                "auth_token": {
                    "type": "string",
                    "description": "Auth token (bearer) or user:password (basic)",
                },
                "reconnect_delay": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 5,
                    "description": "Reconnection delay in seconds",
                },
                "max_reconnects": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0,
                    "description": "Max reconnect attempts (0 = unlimited)",
                },
                "filter_data": {
                    "type": "string",
                    "description": "Only trigger if data contains this string",
                },
            },
            "required": ["name", "url"],
        }
