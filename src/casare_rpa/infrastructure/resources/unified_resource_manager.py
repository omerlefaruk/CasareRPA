"""
Unified Resource Manager for CasareRPA Robot Agent.

Centralized resource pooling for browser, database, and HTTP connections with:
- Job-level quota enforcement
- Resource lease tracking with TTL
- LRU eviction when pool is full
- Graceful degradation
- Background cleanup of expired leases
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, TypeVar, Union

from loguru import logger
import orjson

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext


class ResourceType(Enum):
    """Types of pooled resources."""

    BROWSER = "browser"
    DATABASE = "database"
    HTTP = "http"


@dataclass
class ResourceQuota:
    """Per-job resource quota configuration."""

    max_browsers: int = 2
    max_db_connections: int = 3
    max_http_sessions: int = 5


@dataclass
class ResourceLease:
    """
    Tracks a leased resource with TTL support.

    Attributes:
        lease_id: Unique identifier for this lease
        resource_type: Type of resource (BROWSER, DATABASE, HTTP)
        resource: The actual resource object
        job_id: ID of the job that owns this lease
        leased_at: When the lease was created
        max_lease_duration: Maximum time the lease is valid
        last_activity: Last time the resource was used
    """

    resource_type: ResourceType
    resource: Any
    job_id: str
    lease_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    leased_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    max_lease_duration: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        """Check if lease has exceeded TTL."""
        return datetime.now(timezone.utc) > self.leased_at + self.max_lease_duration

    def time_remaining(self) -> timedelta:
        """Get remaining time on the lease."""
        expiry = self.leased_at + self.max_lease_duration
        remaining = expiry - datetime.now(timezone.utc)
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    def idle_time(self) -> timedelta:
        """Get time since last activity."""
        return datetime.now(timezone.utc) - self.last_activity


@dataclass
class JobResources:
    """
    Resources allocated to a job.

    Attributes:
        job_id: The job these resources belong to
        leases: List of active resource leases
        browser_context: Primary browser context (if allocated)
        db_connection: Primary database connection (if allocated)
        http_session: Primary HTTP session (if allocated)
    """

    job_id: str
    leases: List[ResourceLease] = field(default_factory=list)
    browser_context: Optional["BrowserContext"] = None
    db_connection: Optional[Any] = None
    http_session: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "job_id": self.job_id,
            "lease_count": len(self.leases),
            "has_browser": self.browser_context is not None,
            "has_db": self.db_connection is not None,
            "has_http": self.http_session is not None,
        }

    def get_lease(self, resource_type: ResourceType) -> Optional[ResourceLease]:
        """Get first lease of a given type."""
        for lease in self.leases:
            if lease.resource_type == resource_type:
                return lease
        return None

    def count_by_type(self, resource_type: ResourceType) -> int:
        """Count leases of a specific type."""
        return sum(1 for lease in self.leases if lease.resource_type == resource_type)


@dataclass
class PoolStatistics:
    """Statistics for resource pool monitoring."""

    resources_created: int = 0
    resources_destroyed: int = 0
    leases_granted: int = 0
    leases_expired: int = 0
    leases_released: int = 0
    quota_rejections: int = 0
    evictions: int = 0
    degradations: int = 0

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "resources_created": self.resources_created,
            "resources_destroyed": self.resources_destroyed,
            "leases_granted": self.leases_granted,
            "leases_expired": self.leases_expired,
            "leases_released": self.leases_released,
            "quota_rejections": self.quota_rejections,
            "evictions": self.evictions,
            "degradations": self.degradations,
        }


T = TypeVar("T")


class LRUResourceCache(Generic[T]):
    """
    LRU cache for pooled resources with eviction support.

    Uses OrderedDict to maintain insertion/access order for LRU eviction.
    """

    def __init__(self, max_size: int) -> None:
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of resources to cache
        """
        self._max_size = max_size
        self._cache: OrderedDict[str, T] = OrderedDict()
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        """Current number of cached resources."""
        return len(self._cache)

    @property
    def max_size(self) -> int:
        """Maximum cache size."""
        return self._max_size

    async def get(self, key: str) -> Optional[T]:
        """
        Get resource from cache, moving it to end (most recently used).

        Args:
            key: Resource key

        Returns:
            Resource if found, None otherwise
        """
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    async def put(self, key: str, resource: T) -> Optional[T]:
        """
        Add resource to cache, evicting LRU item if at capacity.

        Args:
            key: Resource key
            resource: Resource to cache

        Returns:
            Evicted resource if eviction occurred, None otherwise
        """
        async with self._lock:
            evicted: Optional[T] = None

            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = resource
            else:
                if len(self._cache) >= self._max_size:
                    _, evicted = self._cache.popitem(last=False)
                self._cache[key] = resource

            return evicted

    async def remove(self, key: str) -> Optional[T]:
        """
        Remove resource from cache.

        Args:
            key: Resource key

        Returns:
            Removed resource if found, None otherwise
        """
        async with self._lock:
            return self._cache.pop(key, None)

    async def peek_lru(self) -> Optional[tuple[str, T]]:
        """
        Peek at the least recently used item without removing it.

        Returns:
            Tuple of (key, resource) for LRU item, or None if empty
        """
        async with self._lock:
            if not self._cache:
                return None
            key = next(iter(self._cache))
            return (key, self._cache[key])

    async def evict_lru(self) -> Optional[tuple[str, T]]:
        """
        Evict and return the least recently used item.

        Returns:
            Tuple of (key, resource) for evicted item, or None if empty
        """
        async with self._lock:
            if not self._cache:
                return None
            return self._cache.popitem(last=False)

    async def clear(self) -> List[T]:
        """
        Clear all resources from cache.

        Returns:
            List of all removed resources
        """
        async with self._lock:
            resources = list(self._cache.values())
            self._cache.clear()
            return resources

    async def keys(self) -> List[str]:
        """Get all cache keys."""
        async with self._lock:
            return list(self._cache.keys())


class BrowserPool:
    """
    Pool of Playwright browser contexts with LRU eviction.

    Manages browser lifecycle, context reuse, and LRU eviction for efficiency.
    """

    def __init__(self, max_size: int = 5, headless: bool = True) -> None:
        """
        Initialize browser pool.

        Args:
            max_size: Maximum number of browser contexts
            headless: Whether to run browser in headless mode
        """
        self.max_size = max_size
        self._headless = headless
        self._browser: Optional["Browser"] = None
        self._available_contexts: LRUResourceCache["BrowserContext"] = LRUResourceCache(max_size)
        self._in_use_contexts: Dict[str, "BrowserContext"] = {}  # job_id -> context
        self._lock = asyncio.Lock()
        self._started = False
        self._stats = PoolStatistics()

    async def start(self) -> None:
        """Start the browser pool and launch browser."""
        if self._started:
            return

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
            self._started = True
            logger.info(f"Browser pool started (max_size={self.max_size})")
        except ImportError:
            logger.warning("Playwright not available, browser pool disabled")
            self._stats.degradations += 1
        except Exception as e:
            logger.error(f"Failed to start browser pool: {e}")
            self._stats.degradations += 1

    async def stop(self) -> None:
        """Stop the pool and close all resources."""
        async with self._lock:
            # Close available contexts from LRU cache
            cached_contexts = await self._available_contexts.clear()
            for context in cached_contexts:
                try:
                    await context.close()
                    self._stats.resources_destroyed += 1
                except Exception as e:
                    logger.warning(f"Error closing available context: {e}")

            for job_id, context in self._in_use_contexts.items():
                try:
                    await context.close()
                    self._stats.resources_destroyed += 1
                    logger.warning(f"Force-closed context for job {job_id[:8]}")
                except Exception as e:
                    logger.warning(f"Error closing in-use context: {e}")

            self._in_use_contexts.clear()

            # Close browser
            if self._browser:
                try:
                    await self._browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
                self._browser = None

            # Stop playwright
            if hasattr(self, "_playwright"):
                try:
                    await self._playwright.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playwright: {e}")

            self._started = False
            logger.info("Browser pool stopped")

    async def acquire(self, job_id: str, timeout: float = 30.0) -> Optional["BrowserContext"]:
        """
        Acquire a browser context for a job.

        Args:
            job_id: Job requesting the context
            timeout: Maximum time to wait for a context

        Returns:
            BrowserContext or None if unavailable
        """
        if not self._started or not self._browser:
            logger.warning("Browser pool not started, cannot acquire context")
            return None

        start_time = time.time()

        while True:
            async with self._lock:
                # Check if job already has a context
                if job_id in self._in_use_contexts:
                    return self._in_use_contexts[job_id]

                # Try to get from LRU cache (reuse available context)
                evicted = await self._available_contexts.evict_lru()
                if evicted:
                    _, context = evicted
                    self._in_use_contexts[job_id] = context
                    self._stats.leases_granted += 1
                    logger.debug(f"Reused browser context for job {job_id[:8]}")
                    return context

                # Create new context if under limit
                total_contexts = self._available_contexts.size + len(self._in_use_contexts)
                if total_contexts < self.max_size:
                    try:
                        context = await self._browser.new_context()
                        self._in_use_contexts[job_id] = context
                        self._stats.resources_created += 1
                        self._stats.leases_granted += 1
                        logger.debug(f"Created new browser context for job {job_id[:8]}")
                        return context
                    except Exception as e:
                        logger.error(f"Failed to create browser context: {e}")
                        return None

            # Check timeout
            if (time.time() - start_time) >= timeout:
                logger.warning(
                    f"Browser pool exhausted (max_size={self.max_size}), "
                    f"job {job_id[:8]} timed out after {timeout}s"
                )
                return None

            await asyncio.sleep(0.1)

    async def release(self, job_id: str) -> bool:
        """
        Release a browser context back to the pool.

        Args:
            job_id: Job releasing the context

        Returns:
            True if released successfully
        """
        async with self._lock:
            context = self._in_use_contexts.pop(job_id, None)
            if context is None:
                return False

            # Clear context state for reuse
            try:
                await context.clear_cookies()
                # Close all pages
                pages = context.pages
                for page in pages:
                    try:
                        await page.close()
                    except Exception:
                        pass

                # Add back to LRU cache
                cache_key = f"ctx_{id(context)}_{time.time()}"
                evicted = await self._available_contexts.put(cache_key, context)
                if evicted:
                    try:
                        await evicted.close()
                        self._stats.evictions += 1
                    except Exception:
                        pass

                self._stats.leases_released += 1
                logger.debug(f"Released browser context from job {job_id[:8]}")
                return True
            except Exception as e:
                logger.warning(f"Error clearing context, closing instead: {e}")
                try:
                    await context.close()
                    self._stats.resources_destroyed += 1
                except Exception:
                    pass
                return True

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "started": self._started,
            "max_size": self.max_size,
            "available": self._available_contexts.size,
            "in_use": len(self._in_use_contexts),
            "in_use_jobs": list(self._in_use_contexts.keys()),
            **self._stats.to_dict(),
        }


class DatabasePool:
    """
    Pool of database connections using asyncpg.

    Wraps asyncpg's built-in connection pooling with job tracking and statistics.
    """

    def __init__(self, max_size: int = 10) -> None:
        """
        Initialize database pool.

        Args:
            max_size: Maximum number of connections
        """
        self.max_size = max_size
        self._pool: Optional[Any] = None
        self._in_use: Dict[str, Any] = {}  # job_id -> connection
        self._lock = asyncio.Lock()
        self._started = False
        self._stats = PoolStatistics()

    async def start(self, postgres_url: str) -> None:
        """
        Start the pool with given connection string.

        Args:
            postgres_url: PostgreSQL connection URL
        """
        if self._started:
            return

        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(
                postgres_url,
                min_size=2,
                max_size=self.max_size,
                command_timeout=30,
                statement_cache_size=0,  # Required for pgbouncer/Supabase
            )
            self._started = True
            logger.info(f"Database pool started (max_size={self.max_size})")
        except ImportError:
            logger.warning("asyncpg not available, database pool disabled")
            self._stats.degradations += 1
        except Exception as e:
            logger.error(f"Failed to start database pool: {e}")
            self._stats.degradations += 1

    async def stop(self) -> None:
        """Stop the pool and close all connections."""
        async with self._lock:
            # Release in-use connections
            for job_id, conn in list(self._in_use.items()):
                try:
                    if self._pool:
                        await self._pool.release(conn)
                    self._stats.resources_destroyed += 1
                except Exception as e:
                    logger.warning(f"Error releasing connection for job {job_id}: {e}")

            self._in_use.clear()

            # Close pool
            if self._pool:
                try:
                    await self._pool.close()
                except Exception as e:
                    logger.warning(f"Error closing database pool: {e}")
                self._pool = None

            self._started = False
            logger.info("Database pool stopped")

    async def acquire(self, job_id: str, timeout: float = 30.0) -> Optional[Any]:
        """
        Acquire a database connection for a job.

        Args:
            job_id: Job requesting the connection
            timeout: Maximum time to wait for a connection

        Returns:
            Connection or None if unavailable
        """
        if not self._started or not self._pool:
            return None

        async with self._lock:
            if job_id in self._in_use:
                return self._in_use[job_id]

            try:
                conn = await self._pool.acquire(timeout=timeout)
                self._in_use[job_id] = conn
                self._stats.leases_granted += 1
                self._stats.resources_created += 1
                logger.debug(f"Acquired database connection for job {job_id[:8]}")
                return conn
            except Exception as e:
                logger.error(f"Failed to acquire database connection: {e}")
                return None

    async def release(self, job_id: str) -> bool:
        """
        Release a database connection back to pool.

        Args:
            job_id: Job releasing the connection

        Returns:
            True if released successfully
        """
        async with self._lock:
            conn = self._in_use.pop(job_id, None)
            if conn is None:
                return False

            try:
                if self._pool:
                    await self._pool.release(conn)
                self._stats.leases_released += 1
                logger.debug(f"Released database connection from job {job_id[:8]}")
                return True
            except Exception as e:
                logger.warning(f"Error releasing database connection: {e}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        pool_stats = {}
        if self._pool:
            pool_stats = {
                "pool_size": self._pool.get_size(),
                "pool_free": self._pool.get_idle_size(),
            }
        return {
            "started": self._started,
            "max_size": self.max_size,
            "in_use": len(self._in_use),
            **pool_stats,
            **self._stats.to_dict(),
        }


class HTTPPool:
    """
    Pool of HTTP client sessions using UnifiedHttpClient.

    Manages persistent HTTP sessions for efficiency with LRU eviction support.
    Uses UnifiedHttpClient for consistent resilience patterns across the platform.
    """

    def __init__(self, max_size: int = 20) -> None:
        """
        Initialize HTTP pool.

        Args:
            max_size: Maximum number of concurrent sessions
        """
        from casare_rpa.infrastructure.http import (
            UnifiedHttpClient,
            UnifiedHttpClientConfig,
        )

        self.max_size = max_size
        self._sessions: Dict[str, UnifiedHttpClient] = {}  # job_id -> client
        self._available_sessions: LRUResourceCache[UnifiedHttpClient] = LRUResourceCache(max_size)
        self._lock = asyncio.Lock()
        self._started = False
        self._stats = PoolStatistics()
        # Store references for creating clients
        self._client_class = UnifiedHttpClient
        self._config_class = UnifiedHttpClientConfig

    async def start(self) -> None:
        """Start the HTTP pool."""
        self._started = True
        logger.info(f"HTTP pool started (max_size={self.max_size})")

    async def stop(self) -> None:
        """Stop the pool and close all sessions."""
        async with self._lock:
            # Close in-use sessions
            for job_id, client in list(self._sessions.items()):
                try:
                    await client.close()
                    self._stats.resources_destroyed += 1
                except Exception as e:
                    logger.warning(f"Error closing HTTP client for job {job_id}: {e}")

            self._sessions.clear()

            # Close cached sessions
            cached_sessions = await self._available_sessions.clear()
            for client in cached_sessions:
                try:
                    await client.close()
                    self._stats.resources_destroyed += 1
                except Exception as e:
                    logger.warning(f"Error closing cached HTTP client: {e}")

            self._started = False
            logger.info("HTTP pool stopped")

    async def acquire(self, job_id: str, timeout: float = 30.0) -> Optional[Any]:
        """
        Acquire an HTTP client for a job.

        Args:
            job_id: Job requesting the client
            timeout: Maximum time to wait for a client

        Returns:
            UnifiedHttpClient or None
        """
        if not self._started:
            return None

        start_time = time.time()

        while True:
            async with self._lock:
                # Check if job already has a session
                if job_id in self._sessions:
                    return self._sessions[job_id]

                # Try to reuse from LRU cache
                evicted = await self._available_sessions.evict_lru()
                if evicted:
                    _, client = evicted
                    self._sessions[job_id] = client
                    self._stats.leases_granted += 1
                    logger.debug(f"Reused HTTP client for job {job_id[:8]}")
                    return client

                # Create new session if under limit
                total_sessions = self._available_sessions.size + len(self._sessions)
                if total_sessions < self.max_size:
                    try:
                        # Create UnifiedHttpClient with default config
                        config = self._config_class(
                            default_timeout=30.0,
                            max_retries=3,
                        )
                        client = self._client_class(config)
                        await client.start()
                        self._sessions[job_id] = client
                        self._stats.resources_created += 1
                        self._stats.leases_granted += 1
                        logger.debug(f"Created HTTP client for job {job_id[:8]}")
                        return client
                    except ImportError:
                        logger.warning("aiohttp not available, HTTP pool disabled")
                        self._stats.degradations += 1
                        return None
                    except Exception as e:
                        logger.error(f"Failed to create HTTP client: {e}")
                        return None

            # Check timeout
            if (time.time() - start_time) >= timeout:
                logger.warning(
                    f"HTTP pool exhausted (max_size={self.max_size}), "
                    f"job {job_id[:8]} timed out after {timeout}s"
                )
                return None

            await asyncio.sleep(0.1)

    async def release(self, job_id: str) -> bool:
        """
        Release an HTTP client back to pool.

        Args:
            job_id: Job releasing the client

        Returns:
            True if released successfully
        """
        async with self._lock:
            client = self._sessions.pop(job_id, None)
            if client is None:
                return False

            # Add to LRU cache for reuse (UnifiedHttpClient can be reused)
            cache_key = f"http_{id(client)}_{time.time()}"
            evicted = await self._available_sessions.put(cache_key, client)
            if evicted:
                try:
                    await evicted.close()
                    self._stats.evictions += 1
                except Exception:
                    pass

            self._stats.leases_released += 1
            logger.debug(f"Released HTTP client from job {job_id[:8]}")
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "started": self._started,
            "max_size": self.max_size,
            "in_use": len(self._sessions),
            "available": self._available_sessions.size,
            **self._stats.to_dict(),
        }


class UnifiedResourceManager:
    """
    Centralized resource pooling for browser, database, and HTTP connections.

    Features:
    - Job-level quota enforcement
    - Resource lease tracking
    - TTL-based cleanup
    - LRU eviction when pool full
    - Graceful degradation

    Usage:
        async with UnifiedResourceManager() as manager:
            resources = await manager.acquire_resources_for_job(
                job_id, workflow_json
            )
            try:
                # Use resources.browser_context, etc.
                pass
            finally:
                await manager.release_resources(resources)
    """

    def __init__(
        self,
        browser_pool_size: int = 5,
        db_pool_size: int = 10,
        http_pool_size: int = 20,
        max_browsers_per_job: int = 2,
        max_db_connections_per_job: int = 3,
        max_http_sessions_per_job: int = 5,
        lease_ttl_minutes: int = 30,
        postgres_url: Optional[str] = None,
        quota: Optional[ResourceQuota] = None,
        cleanup_interval_seconds: float = 60.0,
    ) -> None:
        """
        Initialize unified resource manager.

        Args:
            browser_pool_size: Max browser contexts
            db_pool_size: Max database connections
            http_pool_size: Max HTTP sessions
            max_browsers_per_job: Max browsers per job
            max_db_connections_per_job: Max DB connections per job
            max_http_sessions_per_job: Max HTTP sessions per job
            lease_ttl_minutes: Default lease TTL
            postgres_url: PostgreSQL connection string
            quota: ResourceQuota for per-job limits (overrides individual params)
            cleanup_interval_seconds: Interval between cleanup runs
        """
        # Pools
        self.browser_pool = BrowserPool(max_size=browser_pool_size)
        self.db_pool = DatabasePool(max_size=db_pool_size)
        self.http_pool = HTTPPool(max_size=http_pool_size)

        # Quota enforcement (use provided quota or build from individual params)
        self.quota = quota or ResourceQuota(
            max_browsers=max_browsers_per_job,
            max_db_connections=max_db_connections_per_job,
            max_http_sessions=max_http_sessions_per_job,
        )

        # Legacy properties for backwards compatibility
        self.max_browsers_per_job = self.quota.max_browsers
        self.max_db_connections_per_job = self.quota.max_db_connections
        self.max_http_sessions_per_job = self.quota.max_http_sessions

        # Lease configuration
        self.lease_ttl = timedelta(minutes=lease_ttl_minutes)
        self.cleanup_interval = cleanup_interval_seconds

        # Active leases (job_id -> List[ResourceLease])
        self.active_leases: Dict[str, List[ResourceLease]] = {}
        self._leases_lock = asyncio.Lock()

        # Connection strings
        self._postgres_url = postgres_url

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Workflow analysis cache
        self._workflow_capabilities: Dict[str, Dict[str, bool]] = {}

        # Global statistics
        self._stats = PoolStatistics()

    async def start(self) -> None:
        """Start all resource pools and background cleanup task."""
        logger.info("Starting unified resource manager")

        self._shutdown_event.clear()

        await self.browser_pool.start()
        await self.http_pool.start()

        if self._postgres_url:
            await self.db_pool.start(self._postgres_url)

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_leases())

        logger.info("Unified resource manager started")

    async def stop(self) -> None:
        """Stop all resource pools and cleanup."""
        logger.info("Stopping unified resource manager")

        self._running = False
        self._shutdown_event.set()

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # Stop pools concurrently
        await asyncio.gather(
            self.browser_pool.stop(),
            self.db_pool.stop(),
            self.http_pool.stop(),
            return_exceptions=True,
        )

        # Clear leases
        async with self._leases_lock:
            self.active_leases.clear()

        logger.info("Unified resource manager stopped")

    def _check_quota(self, job_id: str, resource_type: ResourceType) -> bool:
        """
        Check if job can acquire another resource of the given type.

        Args:
            job_id: Job requesting resource
            resource_type: Type of resource

        Returns:
            True if within quota, False otherwise
        """
        current_leases = self.active_leases.get(job_id, [])
        count = sum(1 for lease in current_leases if lease.resource_type == resource_type)

        limits = {
            ResourceType.BROWSER: self.quota.max_browsers,
            ResourceType.DATABASE: self.quota.max_db_connections,
            ResourceType.HTTP: self.quota.max_http_sessions,
        }

        limit = limits.get(resource_type, 0)
        return count < limit

    def analyze_workflow_needs(self, workflow_json: Union[str, Dict]) -> Dict[str, bool]:
        """
        Analyze workflow to determine required resources.

        Args:
            workflow_json: Workflow definition as JSON string or dict

        Returns:
            Dict with needs_browser, needs_database, needs_http
        """
        try:
            # Handle both string (from API) and dict (JSONB auto-converted)
            if isinstance(workflow_json, str):
                workflow = orjson.loads(workflow_json)
            else:
                workflow = workflow_json

            # Handle both dict-format (keyed by node_id) and list-format nodes
            nodes_data = workflow.get("nodes", {})
            if nodes_data is None:
                nodes = []
            elif isinstance(nodes_data, dict):
                nodes = list(nodes_data.values())
            else:
                nodes = nodes_data

            needs_browser = False
            needs_database = False
            needs_http = False

            browser_node_types = {
                "OpenBrowserNode",
                "NavigateNode",
                "ClickNode",
                "TypeTextNode",
                "ExtractTextNode",
                "WaitForElementNode",
                "ScreenshotNode",
            }

            http_node_types = {
                "HTTPRequestNode",
                "RESTAPINode",
                "WebhookNode",
            }

            for node in nodes:
                # Support both "node_type" (our format) and "type" (legacy)
                node_type = node.get("node_type") or node.get("type", "")
                if node_type in browser_node_types:
                    needs_browser = True
                if node_type in http_node_types:
                    needs_http = True

            return {
                "needs_browser": needs_browser,
                "needs_database": needs_database,
                "needs_http": needs_http,
            }
        except Exception as e:
            logger.warning(f"Failed to analyze workflow needs: {e}")
            return {
                "needs_browser": True,  # Conservative default
                "needs_database": False,
                "needs_http": False,
            }

    async def acquire_resources_for_job(
        self,
        job_id: str,
        workflow_json: Union[str, Dict],
        lease_duration: Optional[timedelta] = None,
    ) -> JobResources:
        """
        Acquire pooled resources for a job.

        Enforces quotas to prevent job monopolization.
        Pre-warms resources based on workflow analysis.

        Args:
            job_id: Job identifier
            workflow_json: Workflow definition (string or dict)
            lease_duration: Custom lease duration (defaults to manager's lease_ttl)

        Returns:
            JobResources with acquired resources

        Raises:
            ValueError: If job exceeds quota for any resource type
        """
        leases: List[ResourceLease] = []
        resources = JobResources(job_id=job_id)
        duration = lease_duration or self.lease_ttl

        # Analyze workflow needs
        needs = self.analyze_workflow_needs(workflow_json)
        self._workflow_capabilities[job_id] = needs

        try:
            # Acquire browser if needed (with quota check)
            if needs["needs_browser"]:
                if not self._check_quota(job_id, ResourceType.BROWSER):
                    self._stats.quota_rejections += 1
                    logger.warning(
                        f"Job {job_id[:8]} exceeded browser quota ({self.quota.max_browsers})"
                    )
                else:
                    context = await self.browser_pool.acquire(job_id)
                    if context:
                        resources.browser_context = context
                        leases.append(
                            ResourceLease(
                                resource_type=ResourceType.BROWSER,
                                resource=context,
                                job_id=job_id,
                                max_lease_duration=duration,
                            )
                        )
                        self._stats.leases_granted += 1
                        logger.debug(f"Pre-warmed browser context for job {job_id[:8]}")
                    else:
                        self._stats.degradations += 1
                        logger.warning(
                            f"Browser context unavailable for job {job_id[:8]} (graceful degradation)"
                        )

            # Acquire database connection if needed (with quota check)
            if needs["needs_database"]:
                if not self._check_quota(job_id, ResourceType.DATABASE):
                    self._stats.quota_rejections += 1
                    logger.warning(
                        f"Job {job_id[:8]} exceeded database quota ({self.quota.max_db_connections})"
                    )
                else:
                    conn = await self.db_pool.acquire(job_id)
                    if conn:
                        resources.db_connection = conn
                        leases.append(
                            ResourceLease(
                                resource_type=ResourceType.DATABASE,
                                resource=conn,
                                job_id=job_id,
                                max_lease_duration=duration,
                            )
                        )
                        self._stats.leases_granted += 1
                        logger.debug(f"Pre-warmed database connection for job {job_id[:8]}")
                    else:
                        self._stats.degradations += 1
                        logger.warning(
                            f"Database connection unavailable for job {job_id[:8]} (graceful degradation)"
                        )

            # Acquire HTTP client if needed (with quota check)
            if needs["needs_http"]:
                if not self._check_quota(job_id, ResourceType.HTTP):
                    self._stats.quota_rejections += 1
                    logger.warning(
                        f"Job {job_id[:8]} exceeded HTTP session quota ({self.quota.max_http_sessions})"
                    )
                else:
                    client = await self.http_pool.acquire(job_id)
                    if client:
                        resources.http_session = client
                        leases.append(
                            ResourceLease(
                                resource_type=ResourceType.HTTP,
                                resource=client,
                                job_id=job_id,
                                max_lease_duration=duration,
                            )
                        )
                        self._stats.leases_granted += 1
                        logger.debug(f"Pre-warmed HTTP client for job {job_id[:8]}")
                    else:
                        self._stats.degradations += 1
                        logger.warning(
                            f"HTTP client unavailable for job {job_id[:8]} (graceful degradation)"
                        )

            # Track leases
            resources.leases = leases
            async with self._leases_lock:
                self.active_leases[job_id] = leases

            logger.info(
                f"Acquired resources for job {job_id[:8]}: "
                f"browser={resources.browser_context is not None}, "
                f"db={resources.db_connection is not None}, "
                f"http={resources.http_session is not None}"
            )

            return resources

        except Exception:
            # Rollback on failure
            for lease in leases:
                try:
                    await self._release_single_lease(lease)
                except Exception as rollback_error:
                    logger.warning(f"Error during resource rollback: {rollback_error}")
            raise

    async def _release_single_lease(self, lease: ResourceLease) -> None:
        """
        Release a single lease back to its pool.

        Args:
            lease: The lease to release
        """
        if lease.resource_type == ResourceType.BROWSER:
            await self.browser_pool.release(lease.job_id)
        elif lease.resource_type == ResourceType.DATABASE:
            await self.db_pool.release(lease.job_id)
        elif lease.resource_type == ResourceType.HTTP:
            await self.http_pool.release(lease.job_id)

    async def release_resources(self, resources: JobResources) -> None:
        """
        Release resources back to pools.

        Args:
            resources: JobResources to release
        """
        job_id = resources.job_id

        for lease in resources.leases:
            try:
                await self._release_single_lease(lease)
                self._stats.leases_released += 1
            except Exception as e:
                logger.warning(
                    f"Error releasing {lease.resource_type.value} for job {job_id[:8]}: {e}"
                )

        # Remove leases
        async with self._leases_lock:
            self.active_leases.pop(job_id, None)
        self._workflow_capabilities.pop(job_id, None)

        logger.info(f"Released all resources for job {job_id[:8]}")

    async def release_all_job_resources(self, job_id: str) -> None:
        """
        Release all resources for a specific job by job ID.

        Args:
            job_id: Job whose resources to release
        """
        async with self._leases_lock:
            leases = self.active_leases.pop(job_id, [])

        for lease in leases:
            try:
                await self._release_single_lease(lease)
                self._stats.leases_released += 1
            except Exception as e:
                logger.warning(f"Error releasing resource for job {job_id[:8]}: {e}")

        self._workflow_capabilities.pop(job_id, None)

        if leases:
            logger.info(f"Released {len(leases)} resources for job {job_id[:8]}")

    async def _cleanup_expired_leases(self) -> None:
        """Background task to cleanup expired leases."""
        logger.info("Started lease cleanup background task")

        while not self._shutdown_event.is_set():
            try:
                await self._run_cleanup_cycle()
            except Exception as e:
                logger.exception(f"Cleanup task error: {e}")

            # Wait for cleanup interval or shutdown
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.cleanup_interval,
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                pass  # Continue cleanup loop

        logger.info("Lease cleanup background task stopped")

    async def _run_cleanup_cycle(self) -> None:
        """Run a single cleanup cycle for expired leases."""
        expired_leases: List[ResourceLease] = []

        async with self._leases_lock:
            for job_id, leases in list(self.active_leases.items()):
                for lease in leases:
                    if lease.is_expired():
                        expired_leases.append(lease)

        for lease in expired_leases:
            logger.warning(
                f"Force-releasing expired {lease.resource_type.value} "
                f"lease for job {lease.job_id[:8]} "
                f"(leased_at={lease.leased_at.isoformat()}, ttl={lease.max_lease_duration})"
            )
            try:
                await self._release_single_lease(lease)
                self._stats.leases_expired += 1
            except Exception as e:
                logger.error(f"Error releasing expired lease: {e}")

        # Update lease tracking after cleanup
        if expired_leases:
            async with self._leases_lock:
                for job_id, leases in list(self.active_leases.items()):
                    remaining = [lease for lease in leases if not lease.is_expired()]
                    if remaining:
                        self.active_leases[job_id] = remaining
                    else:
                        self.active_leases.pop(job_id, None)

            logger.info(f"Cleanup cycle released {len(expired_leases)} expired leases")

    def get_job_leases(self, job_id: str) -> List[ResourceLease]:
        """
        Get all active leases for a job.

        Args:
            job_id: Job ID

        Returns:
            List of active leases (copy)
        """
        return self.active_leases.get(job_id, []).copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics."""
        total_leases = sum(len(leases) for leases in self.active_leases.values())

        return {
            "global": self._stats.to_dict(),
            "browser_pool": self.browser_pool.get_stats(),
            "db_pool": self.db_pool.get_stats(),
            "http_pool": self.http_pool.get_stats(),
            "active_jobs": len(self.active_leases),
            "total_leases": total_leases,
            "leased_jobs": list(self.active_leases.keys()),
            "quota": {
                "max_browsers_per_job": self.quota.max_browsers,
                "max_db_per_job": self.quota.max_db_connections,
                "max_http_per_job": self.quota.max_http_sessions,
            },
        }

    async def __aenter__(self) -> "UnifiedResourceManager":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit."""
        await self.stop()
        return False


__all__ = [
    "ResourceType",
    "ResourceQuota",
    "ResourceLease",
    "JobResources",
    "PoolStatistics",
    "LRUResourceCache",
    "BrowserPool",
    "DatabasePool",
    "HTTPPool",
    "UnifiedResourceManager",
]
