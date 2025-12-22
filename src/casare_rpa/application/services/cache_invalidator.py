import asyncio
from casare_rpa.domain.events import get_event_bus
from casare_rpa.domain.events.workflow_events import WorkflowStarted
from casare_rpa.infrastructure.cache.manager import TieredCacheManager
from loguru import logger


class CacheInvalidator:
    """
    Listens to DomainEvents and invalidates cache entries.
    """

    def __init__(self, cache_manager: TieredCacheManager):
        self.cache_manager = cache_manager
        self.bus = get_event_bus()

    def start(self):
        """Subscribe to events."""
        # Use a wrapper to handle async in sync EventBus
        self.bus.subscribe(WorkflowStarted, self._wrap_async(self._on_workflow_started))
        logger.info("CacheInvalidator started and subscribed to events.")

    def _wrap_async(self, coro_func):
        """Wraps an async function to be called from a sync context."""

        def wrapper(event):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(coro_func(event))
            except RuntimeError:
                # No loop running, run in a new one (less ideal)
                asyncio.run(coro_func(event))

        return wrapper

    async def _on_workflow_started(self, event: WorkflowStarted):
        """Clear node-specific caches for this workflow."""
        prefix = f"node:{event.workflow_id}"
        logger.debug(f"Invalidating cache for prefix: {prefix}")
        await self.cache_manager.delete_by_prefix(prefix)

    async def invalidate_namespace(self, namespace: str, tenant_id: str = None):
        """Manually invalidate a namespace."""
        prefix = f"{namespace}:"
        if tenant_id:
            prefix += f"{tenant_id}:"

        logger.info(f"Manually invalidating cache namespace: {prefix}")
        await self.cache_manager.delete_by_prefix(prefix)
