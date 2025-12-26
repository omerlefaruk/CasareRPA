"""
Concurrent resource manager for parallel agent execution.

Manages shared resources like browser instances, desktop contexts,
and HTTP connections for concurrent agent access.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.task_decomposition import ResourceType


class PartitionedResource:
    """
    A resource partition for isolated concurrent access.

    Represents an isolated view of a shared resource (e.g., a browser
    context within a shared browser instance).
    """

    def __init__(
        self,
        resource: Any,
        partition_id: str,
        partition_handle: Any = None,
    ) -> None:
        self.resource = resource
        self.partition_id = partition_id
        self.partition_handle = partition_handle
        self.is_closed = False

    async def close(self) -> None:
        """Close the partition and release resources."""
        if not self.is_closed and self.partition_handle:
            try:
                if hasattr(self.partition_handle, "close"):
                    await self.partition_handle.close()
            except Exception as e:
                logger.warning(f"Error closing partition {self.partition_id}: {e}")
            finally:
                self.is_closed = True

    def __repr__(self) -> str:
        return f"PartitionedResource(id={self.partition_id}, closed={self.is_closed})"


class ConcurrentResourceManager:
    """
    Manage shared resources for parallel agent execution.

    Handles:
    - Browser instances
    - Desktop contexts (exclusive access)
    - HTTP clients
    - File system access
    """

    def __init__(
        self,
        max_browsers: int = 3,
        max_http_clients: int = 10,
    ) -> None:
        self._browser_semaphore = asyncio.Semaphore(max_browsers)
        self._desktop_semaphore = asyncio.Semaphore(1)  # Desktop is exclusive
        self._http_semaphore = asyncio.Semaphore(max_http_clients)
        self._browser_pool: list[Any] = []
        self._http_pool: dict[str, Any] = {}
        self._allocations: dict[str, PartitionedResource] = {}
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire_browser(
        self,
        agent_id: str,
        partition_id: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Acquire a browser instance for an agent.

        Args:
            agent_id: ID of the agent acquiring the browser
            partition_id: Optional partition ID for isolated context
            timeout: Maximum time to wait for acquisition

        Yields:
            Browser instance or PartitionedResource

        Example:
            async with resource_manager.acquire_browser("agent_1", "partition_1") as browser:
                await browser.goto("https://example.com")
        """
        try:
            await asyncio.wait_for(self._browser_semaphore.acquire(), timeout)
        except TimeoutError:
            raise TimeoutError(f"Agent {agent_id} timed out waiting for browser")

        try:
            # Get or create browser
            browser = await self._get_or_create_browser()

            # Create partitioned context if requested
            if partition_id:
                partition = await self._create_browser_partition(browser, partition_id)
                async with self._lock:
                    self._allocations[f"{agent_id}_{partition_id}"] = partition
                yield partition
            else:
                yield browser

        finally:
            self._browser_semaphore.release()

    @asynccontextmanager
    async def acquire_desktop(
        self,
        agent_id: str,
        timeout: float = 30.0,
    ):
        """
        Acquire desktop context (exclusive access).

        Desktop automation cannot run in parallel due to OS limitations.

        Args:
            agent_id: ID of the agent acquiring desktop
            timeout: Maximum time to wait

        Yields:
            Desktop context
        """
        try:
            await asyncio.wait_for(self._desktop_semaphore.acquire(), timeout)
        except TimeoutError:
            raise TimeoutError(f"Agent {agent_id} timed out waiting for desktop")

        try:
            desktop = await self._create_desktop_context()
            yield desktop
        finally:
            self._desktop_semaphore.release()

    @asynccontextmanager
    async def acquire_http_client(
        self,
        agent_id: str,
        timeout: float = 5.0,
    ):
        """
        Acquire an HTTP client.

        Args:
            agent_id: ID of the agent
            timeout: Maximum time to wait

        Yields:
            HTTP client
        """
        try:
            await asyncio.wait_for(self._http_semaphore.acquire(), timeout)
        except TimeoutError:
            raise TimeoutError(f"Agent {agent_id} timed out waiting for HTTP client")

        try:
            client = await self._get_or_create_http_client()
            yield client
        finally:
            self._http_semaphore.release()

    async def _get_or_create_browser(self):
        """Get or create a browser instance."""
        # Placeholder - actual implementation would use BrowserResourceManager
        if not self._browser_pool:
            # Would normally create a browser via BrowserResourceManager
            pass
        return self._browser_pool[0] if self._browser_pool else None

    async def _create_browser_partition(
        self,
        browser: Any,
        partition_id: str,
    ) -> PartitionedResource:
        """Create a partitioned browser context."""
        # Placeholder - actual implementation would create a browser context
        return PartitionedResource(
            resource=browser,
            partition_id=partition_id,
            partition_handle=None,  # Would be the actual browser context
        )

    async def _create_desktop_context(self):
        """Create a desktop automation context."""
        # Placeholder - actual implementation would use DesktopContext
        return None

    async def _get_or_create_http_client(self):
        """Get or create an HTTP client."""
        # Placeholder - actual implementation would use UnifiedHttpClient
        return None

    async def cleanup_agent_resources(self, agent_id: str) -> None:
        """
        Clean up all resources held by an agent.

        Args:
            agent_id: Agent whose resources should be cleaned up
        """
        async with self._lock:
            to_remove = [key for key in self._allocations.keys() if key.startswith(f"{agent_id}_")]

            for key in to_remove:
                partition = self._allocations.pop(key)
                await partition.close()

    async def shutdown(self) -> None:
        """Shutdown and clean up all resources."""
        async with self._lock:
            for partition in self._allocations.values():
                await partition.close()
            self._allocations.clear()
            self._browser_pool.clear()
            self._http_pool.clear()


class ResourceRequest:
    """Request for resource acquisition."""

    def __init__(
        self,
        resource_type: ResourceType,
        agent_id: str,
        partition_id: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.resource_type = resource_type
        self.agent_id = agent_id
        self.partition_id = partition_id
        self.timeout = timeout


class ResourcePool:
    """
    Generic resource pool with semaphore-based concurrency control.

    Can be used for any resource type that needs concurrent access limits.
    """

    def __init__(
        self,
        resource_factory,
        max_concurrent: int = 10,
        pool_size: int = 5,
    ) -> None:
        self._factory = resource_factory
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._created_count = 0
        self._max_pool_size = pool_size
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self, timeout: float = 30.0):
        """Acquire a resource from the pool."""
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout)
        except TimeoutError:
            raise TimeoutError("Timed out waiting for resource from pool")

        resource = None
        try:
            # Try to get from pool
            try:
                resource = self._pool.get_nowait()
            except asyncio.QueueEmpty:
                # Create new resource if pool not full
                async with self._lock:
                    if self._created_count < self._max_pool_size:
                        resource = await self._factory()
                        self._created_count += 1
                    else:
                        # Wait for a resource to be returned
                        resource = await self._pool.get()

            yield resource

        finally:
            self._semaphore.release()
            if resource is not None:
                try:
                    await self._pool.put(resource)
                except asyncio.QueueFull:
                    # Pool is full, discard resource
                    pass

    async def close(self) -> None:
        """Close all resources in the pool."""
        while not self._pool.empty():
            try:
                resource = self._pool.get_nowait()
                if hasattr(resource, "close"):
                    await resource.close()
            except asyncio.QueueEmpty:
                break
