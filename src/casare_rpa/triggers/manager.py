"""
CasareRPA - Trigger Manager

Central coordinator for all workflow triggers. Manages trigger lifecycle,
routes events to job creation, and handles HTTP server for webhooks.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import uuid

from loguru import logger

from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerEvent,
    TriggerType,
)
from casare_rpa.triggers.registry import get_trigger_registry


# Type alias for job creation callback
JobCreatorCallback = Callable[[TriggerEvent], Any]


def _get_default_webhook_host() -> str:
    """
    Determine default host for webhook server based on environment.

    If CASARE_WEBHOOK_URL is set to a tunnel URL (casare.net),
    bind to 0.0.0.0 to allow tunnel connections. Otherwise, use
    127.0.0.1 for security.
    """
    webhook_url = os.getenv("CASARE_WEBHOOK_URL", "")
    if "casare.net" in webhook_url or webhook_url.startswith("https://"):
        return "0.0.0.0"  # Allow tunnel/external connections
    return "127.0.0.1"  # Local only (secure default)


class TriggerManager:
    """
    Central coordinator for all workflow triggers.

    Responsibilities:
    - Create, start, stop triggers
    - Route TriggerEvents to job creation
    - Manage HTTP server for webhook triggers
    - Persist trigger configurations
    - Provide API for UI/external access

    Environment Variables:
        CASARE_WEBHOOK_URL: If set to tunnel URL (e.g., https://webhooks.casare.net),
                           the webhook server binds to 0.0.0.0 to accept tunnel connections.

    Usage:
        manager = TriggerManager(on_trigger_event=job_creator_callback)
        await manager.start()

        # Register a trigger
        config = BaseTriggerConfig(
            id="trig_123",
            name="My Webhook",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="scen_abc",
            workflow_id="wf_xyz",
            config={"endpoint": "/webhooks/my-hook"}
        )
        await manager.register_trigger(config)

        # Later...
        await manager.stop()
    """

    def __init__(
        self,
        on_trigger_event: Optional[JobCreatorCallback] = None,
        http_port: int = 8766,
        http_host: Optional[str] = None,
    ) -> None:
        """
        Initialize the trigger manager.

        Args:
            on_trigger_event: Callback invoked when a trigger fires
            http_port: Port for webhook HTTP server
            http_host: Host to bind HTTP server to. If None, auto-detects based on
                       CASARE_WEBHOOK_URL (0.0.0.0 for tunnel, 127.0.0.1 for local).
        """
        self._on_trigger_event = on_trigger_event
        self._http_port = http_port
        self._http_host = http_host or _get_default_webhook_host()

        # Trigger storage
        self._triggers: Dict[str, BaseTrigger] = {}
        self._trigger_configs: Dict[str, BaseTriggerConfig] = {}

        # State
        self._running = False
        self._http_server = None
        self._http_app = None

        # Webhook routes
        self._webhook_routes: Dict[str, str] = {}  # path -> trigger_id

        # Callable workflows (for WorkflowCallTrigger)
        self._callables: Dict[str, str] = {}  # alias -> trigger_id

        # Registry reference
        self._registry = get_trigger_registry()

        # Public webhook base URL (for UI display)
        self._webhook_base_url = os.getenv(
            "CASARE_WEBHOOK_URL", f"http://localhost:{http_port}"
        )

        logger.debug(
            f"TriggerManager initialized (http_port={http_port}, "
            f"host={self._http_host}, base_url={self._webhook_base_url})"
        )

    @property
    def webhook_base_url(self) -> str:
        """Get the public webhook base URL for external services to call."""
        return self._webhook_base_url

    def get_webhook_url(self, trigger_id: str) -> str:
        """
        Get the full webhook URL for a trigger.

        Args:
            trigger_id: The trigger ID

        Returns:
            Full URL like https://webhooks.casare.net/hooks/{trigger_id}
        """
        return f"{self._webhook_base_url}/hooks/{trigger_id}"

    def get_webhook_url_by_path(self, path: str) -> str:
        """
        Get the full webhook URL for a custom path.

        Args:
            path: Custom path (e.g., "/my-webhook" or "my-webhook")

        Returns:
            Full URL like https://webhooks.casare.net/webhooks/my-webhook
        """
        # Normalize path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._webhook_base_url}/webhooks{path}"

    async def start(self) -> None:
        """Start the trigger manager and all enabled triggers."""
        if self._running:
            logger.warning("TriggerManager already running")
            return

        self._running = True
        logger.info("TriggerManager starting...")

        # Start HTTP server for webhooks
        await self._start_http_server()

        # Start all enabled triggers
        for trigger_id, trigger in self._triggers.items():
            if trigger.config.enabled:
                try:
                    await trigger.start()
                except Exception as e:
                    logger.error(f"Failed to start trigger {trigger_id}: {e}")

        logger.info(f"TriggerManager started with {len(self._triggers)} triggers")

    async def stop(self) -> None:
        """Stop the trigger manager and all triggers."""
        if not self._running:
            return

        logger.info("TriggerManager stopping...")

        # Stop all triggers
        for trigger_id, trigger in self._triggers.items():
            try:
                await trigger.stop()
            except Exception as e:
                logger.error(f"Failed to stop trigger {trigger_id}: {e}")

        # Stop HTTP server
        await self._stop_http_server()

        self._running = False
        logger.info("TriggerManager stopped")

    async def _start_http_server(self) -> None:
        """Start HTTP server for webhook endpoints."""
        try:
            from aiohttp import web

            self._http_app = web.Application()

            # Add webhook routes
            self._http_app.router.add_post(
                "/hooks/{trigger_id}", self._handle_webhook_by_id
            )
            self._http_app.router.add_post(
                "/webhooks/{path:.*}", self._handle_webhook_by_path
            )
            self._http_app.router.add_post("/forms/{trigger_id}", self._handle_form)
            self._http_app.router.add_get("/health", self._handle_health)

            runner = web.AppRunner(self._http_app)
            await runner.setup()
            # SECURITY: Bind to configured host (default: localhost only)
            # Use 0.0.0.0 only if external access is explicitly required
            site = web.TCPSite(runner, self._http_host, self._http_port)
            await site.start()
            self._http_server = runner

            if self._http_host == "0.0.0.0":
                logger.warning(
                    f"Webhook HTTP server bound to ALL interfaces (0.0.0.0:{self._http_port}). "
                    "This exposes the server to the network. Use 127.0.0.1 for local-only access."
                )
            logger.info(
                f"Webhook HTTP server started on {self._http_host}:{self._http_port}"
            )

        except ImportError:
            logger.warning("aiohttp not installed - webhook triggers disabled")
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")

    async def _stop_http_server(self) -> None:
        """Stop HTTP server."""
        if self._http_server:
            try:
                await self._http_server.cleanup()
                self._http_server = None
                self._http_app = None
                logger.info("Webhook HTTP server stopped")
            except Exception as e:
                logger.error(f"Error stopping HTTP server: {e}")

    async def _handle_webhook_by_id(self, request) -> Any:
        """Handle webhook request by trigger ID."""

        trigger_id = request.match_info["trigger_id"]
        return await self._process_webhook(request, trigger_id)

    async def _handle_webhook_by_path(self, request) -> Any:
        """Handle webhook request by custom path."""
        from aiohttp import web

        path = "/" + request.match_info["path"]
        trigger_id = self._webhook_routes.get(path)

        if not trigger_id:
            return web.json_response({"error": "Unknown webhook path"}, status=404)

        return await self._process_webhook(request, trigger_id)

    async def _process_webhook(self, request, trigger_id: str) -> Any:
        """Process a webhook request for a trigger."""
        from aiohttp import web
        from .webhook_auth import verify_webhook_auth

        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return web.json_response({"error": "Trigger not found"}, status=404)

        if not trigger.config.enabled:
            return web.json_response({"error": "Trigger is disabled"}, status=403)

        # Get trigger config
        config = trigger.config.config

        # Read raw body for HMAC verification
        body = await request.read()

        # Verify authentication (supports api_key, bearer, hmac_sha256, etc.)
        is_valid, auth_error = verify_webhook_auth(config, dict(request.headers), body)
        if not is_valid:
            logger.warning(
                f"Webhook auth failed for trigger {trigger_id}: {auth_error}"
            )
            return web.json_response(
                {"error": auth_error or "Authentication failed"}, status=401
            )

        # Parse payload from already-read body
        try:
            if body:
                import json

                payload = json.loads(body)
            else:
                payload = {}
        except Exception:
            payload = {}

        # Add request metadata
        metadata = {
            "source": "webhook",
            "method": request.method,
            "path": str(request.path),
            "headers": dict(request.headers),
            "remote": request.remote,
        }

        # Fire the trigger
        success = await trigger.emit(payload, metadata)

        if success:
            return web.json_response(
                {
                    "status": "accepted",
                    "trigger_id": trigger_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            return web.json_response(
                {"error": "Trigger failed or in cooldown"}, status=429
            )

    async def _handle_form(self, request) -> Any:
        """Handle form submission."""
        from aiohttp import web

        trigger_id = request.match_info["trigger_id"]
        trigger = self._triggers.get(trigger_id)

        if not trigger:
            return web.json_response({"error": "Trigger not found"}, status=404)

        if not trigger.config.enabled:
            return web.json_response({"error": "Trigger disabled"}, status=403)

        # Parse form data
        try:
            data = await request.post()
            payload = dict(data)
        except Exception:
            try:
                payload = await request.json()
            except Exception:
                payload = {}

        metadata = {
            "source": "form",
            "path": str(request.path),
        }

        success = await trigger.emit(payload, metadata)

        if success:
            return web.json_response({"status": "accepted"})
        return web.json_response({"error": "Failed"}, status=500)

    async def _handle_health(self, request) -> Any:
        """Health check endpoint."""
        from aiohttp import web

        return web.json_response(
            {
                "status": "healthy",
                "triggers_active": len(
                    [t for t in self._triggers.values() if t.is_active]
                ),
                "triggers_total": len(self._triggers),
            }
        )

    async def _on_trigger_fired(self, event: TriggerEvent) -> None:
        """
        Handle trigger event internally.

        This is the callback passed to triggers, which routes
        events to the external job creator callback.
        """
        logger.info(
            f"Trigger event received: {event.trigger_id} ({event.trigger_type.value})"
        )

        if self._on_trigger_event:
            try:
                result = self._on_trigger_event(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in trigger event handler: {e}")

    # ==================== Public API ====================

    async def register_trigger(
        self, config: BaseTriggerConfig
    ) -> Optional[BaseTrigger]:
        """
        Register and start a new trigger.

        Args:
            config: Trigger configuration

        Returns:
            Created trigger instance or None if failed
        """
        # Check if already exists
        if config.id in self._triggers:
            logger.warning(f"Trigger {config.id} already exists")
            return self._triggers[config.id]

        # Create trigger instance
        trigger = self._registry.create_instance(
            config.trigger_type, config, self._on_trigger_fired
        )

        if not trigger:
            logger.error(f"Failed to create trigger: {config.trigger_type.value}")
            return None

        # Validate configuration
        is_valid, error_msg = trigger.validate_config()
        if not is_valid:
            logger.error(f"Invalid trigger config: {error_msg}")
            return None

        # Store trigger
        self._triggers[config.id] = trigger
        self._trigger_configs[config.id] = config

        # Register webhook route if applicable
        if config.trigger_type == TriggerType.WEBHOOK:
            endpoint = config.config.get("endpoint", "")
            if endpoint:
                self._webhook_routes[endpoint] = config.id

        # Register callable if applicable
        if config.trigger_type == TriggerType.WORKFLOW_CALL:
            alias = config.config.get("call_alias", "")
            if alias:
                self._callables[alias] = config.id

        # Start trigger if manager is running and trigger is enabled
        if self._running and config.enabled:
            try:
                await trigger.start()
            except Exception as e:
                logger.error(f"Failed to start trigger {config.id}: {e}")

        logger.info(f"Registered trigger: {config.name} ({config.trigger_type.value})")
        return trigger

    async def unregister_trigger(self, trigger_id: str) -> bool:
        """
        Unregister and stop a trigger.

        Args:
            trigger_id: ID of trigger to remove

        Returns:
            True if removed, False if not found
        """
        trigger = self._triggers.pop(trigger_id, None)
        if not trigger:
            return False

        # Stop the trigger
        try:
            await trigger.stop()
        except Exception as e:
            logger.error(f"Error stopping trigger {trigger_id}: {e}")

        # Remove from other registries
        config = self._trigger_configs.pop(trigger_id, None)
        if config:
            # Remove webhook route
            if config.trigger_type == TriggerType.WEBHOOK:
                endpoint = config.config.get("endpoint", "")
                self._webhook_routes.pop(endpoint, None)

            # Remove callable
            if config.trigger_type == TriggerType.WORKFLOW_CALL:
                alias = config.config.get("call_alias", "")
                self._callables.pop(alias, None)

        logger.info(f"Unregistered trigger: {trigger_id}")
        return True

    async def update_trigger(
        self, trigger_id: str, config: BaseTriggerConfig
    ) -> Optional[BaseTrigger]:
        """
        Update an existing trigger.

        Args:
            trigger_id: ID of trigger to update
            config: New configuration

        Returns:
            Updated trigger or None if failed
        """
        # Remove old trigger
        await self.unregister_trigger(trigger_id)

        # Register with new config
        config.id = trigger_id  # Preserve ID
        return await self.register_trigger(config)

    async def enable_trigger(self, trigger_id: str) -> bool:
        """Enable a trigger."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False

        trigger.config.enabled = True
        if self._running:
            try:
                await trigger.start()
            except Exception as e:
                logger.error(f"Failed to start trigger {trigger_id}: {e}")
                return False

        logger.info(f"Enabled trigger: {trigger_id}")
        return True

    async def disable_trigger(self, trigger_id: str) -> bool:
        """Disable a trigger."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False

        trigger.config.enabled = False
        try:
            await trigger.stop()
        except Exception as e:
            logger.error(f"Error stopping trigger {trigger_id}: {e}")

        logger.info(f"Disabled trigger: {trigger_id}")
        return True

    async def fire_trigger(
        self, trigger_id: str, payload: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Manually fire a trigger.

        Args:
            trigger_id: ID of trigger to fire
            payload: Optional payload data

        Returns:
            Event ID if fired, None if failed
        """
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            logger.warning(f"Trigger not found: {trigger_id}")
            return None

        if not trigger.config.enabled:
            logger.warning(f"Cannot fire disabled trigger: {trigger_id}")
            return None

        metadata = {
            "source": "manual",
            "fired_at": datetime.now(timezone.utc).isoformat(),
        }
        success = await trigger.emit(payload or {}, metadata)

        if success:
            return f"evt_{uuid.uuid4().hex[:8]}"
        return None

    async def call_workflow(
        self, alias: str, params: Optional[Dict[str, Any]] = None, wait: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Call a workflow by its callable alias.

        Used by WorkflowCallTrigger to invoke sub-workflows.

        Args:
            alias: Callable alias registered by WorkflowCallTrigger
            params: Parameters to pass to the workflow
            wait: Whether to wait for completion (not implemented yet)

        Returns:
            Result dict or None if not found
        """
        trigger_id = self._callables.get(alias)
        if not trigger_id:
            logger.warning(f"No callable workflow with alias: {alias}")
            return None

        event_id = await self.fire_trigger(trigger_id, params)
        if event_id:
            return {"event_id": event_id, "status": "submitted"}
        return None

    def get_trigger(self, trigger_id: str) -> Optional[BaseTrigger]:
        """Get a trigger by ID."""
        return self._triggers.get(trigger_id)

    def get_trigger_config(self, trigger_id: str) -> Optional[BaseTriggerConfig]:
        """Get trigger configuration by ID."""
        return self._trigger_configs.get(trigger_id)

    def get_all_triggers(self) -> List[BaseTrigger]:
        """Get all triggers."""
        return list(self._triggers.values())

    def get_triggers_by_scenario(self, scenario_id: str) -> List[BaseTrigger]:
        """Get all triggers for a scenario."""
        return [
            t for t in self._triggers.values() if t.config.scenario_id == scenario_id
        ]

    def get_triggers_by_type(self, trigger_type: TriggerType) -> List[BaseTrigger]:
        """Get all triggers of a specific type."""
        return [t for t in self._triggers.values() if t.trigger_type == trigger_type]

    def get_active_triggers(self) -> List[BaseTrigger]:
        """Get all active (running) triggers."""
        return [t for t in self._triggers.values() if t.is_active]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get trigger manager statistics.

        Returns:
            Dictionary with stats
        """
        triggers = list(self._triggers.values())
        return {
            "total_triggers": len(triggers),
            "active_triggers": len([t for t in triggers if t.is_active]),
            "enabled_triggers": len([t for t in triggers if t.config.enabled]),
            "total_fired": sum(t.config.trigger_count for t in triggers),
            "total_success": sum(t.config.success_count for t in triggers),
            "total_errors": sum(t.config.error_count for t in triggers),
            "triggers_by_type": {
                tt.value: len([t for t in triggers if t.trigger_type == tt])
                for tt in TriggerType
            },
            "http_server_running": self._http_server is not None,
            "http_port": self._http_port,
            "webhook_routes": len(self._webhook_routes),
            "callables": len(self._callables),
        }

    @property
    def is_running(self) -> bool:
        """Check if manager is running."""
        return self._running

    @property
    def http_port(self) -> int:
        """Get HTTP server port."""
        return self._http_port

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TriggerManager("
            f"triggers={len(self._triggers)}, "
            f"running={self._running})"
        )
