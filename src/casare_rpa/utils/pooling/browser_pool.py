"""
Browser context pool for CasareRPA.

Provides connection pooling for Playwright browser contexts to improve
performance when running multiple workflows or requiring many browser tabs.
"""

import asyncio
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Set
from loguru import logger

from playwright.async_api import Browser, BrowserContext, Playwright


class PooledContext:
    """A browser context managed by the pool."""

    def __init__(self, context: BrowserContext):
        """Initialize a pooled context."""
        self.context = context
        self.created_at = time.time()
        self.last_used = time.time()
        self.use_count = 0
        self.is_in_use = False
        self._id = id(context)  # Unique ID for hashing

    def __hash__(self) -> int:
        """Make PooledContext hashable by using unique ID."""
        return self._id

    def __eq__(self, other: object) -> bool:
        """Compare by ID."""
        if not isinstance(other, PooledContext):
            return False
        return self._id == other._id

    def mark_used(self) -> None:
        """Mark the context as used."""
        self.last_used = time.time()
        self.use_count += 1
        self.is_in_use = True

    def release(self) -> None:
        """Mark the context as available."""
        self.is_in_use = False

    def is_stale(self, max_age_seconds: float) -> bool:
        """Check if context is older than max age."""
        return (time.time() - self.created_at) > max_age_seconds

    def is_idle(self, idle_timeout_seconds: float) -> bool:
        """Check if context has been idle too long."""
        return (time.time() - self.last_used) > idle_timeout_seconds


class BrowserContextPool:
    """
    Pool of reusable browser contexts for improved performance.

    Features:
    - Pre-creates a minimum number of contexts
    - Dynamically grows up to max_size
    - Recycles contexts for reuse
    - Cleans up stale/idle contexts
    - Thread-safe for async operations
    """

    def __init__(
        self,
        browser: Browser,
        min_size: int = 1,
        max_size: int = 10,
        max_context_age: float = 300.0,  # 5 minutes
        idle_timeout: float = 60.0,  # 1 minute
        context_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the browser context pool.

        Args:
            browser: Playwright Browser instance
            min_size: Minimum number of contexts to keep warm
            max_size: Maximum number of contexts allowed
            max_context_age: Maximum age of a context in seconds before recycling
            idle_timeout: Time after which idle contexts are closed
            context_options: Options to pass when creating new contexts
        """
        self._browser = browser
        self._min_size = min_size
        self._max_size = max_size
        self._max_context_age = max_context_age
        self._idle_timeout = idle_timeout
        self._context_options = context_options or {}

        # Pool state
        self._available: Deque[PooledContext] = deque()
        self._in_use: Set[PooledContext] = set()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._closed = False

        # Statistics
        self._stats = {
            "contexts_created": 0,
            "contexts_closed": 0,
            "contexts_recycled": 0,
            "acquire_count": 0,
            "release_count": 0,
            "wait_count": 0,
        }

    async def initialize(self) -> None:
        """Initialize the pool with minimum contexts."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info(
                f"Initializing browser context pool (min={self._min_size}, max={self._max_size})"
            )

            # Create minimum number of contexts
            for _ in range(self._min_size):
                try:
                    pooled = await self._create_context()
                    self._available.append(pooled)
                except Exception as e:
                    logger.warning(f"Failed to pre-create context: {e}")
                    break

            self._initialized = True
            logger.info(f"Browser context pool initialized with {len(self._available)} contexts")

    async def _create_context(self) -> PooledContext:
        """Create a new pooled context."""
        context = await self._browser.new_context(**self._context_options)
        self._stats["contexts_created"] += 1
        logger.debug(
            f"Created new browser context (total created: {self._stats['contexts_created']})"
        )
        return PooledContext(context=context)

    async def acquire(self, timeout: float = 30.0) -> BrowserContext:
        """
        Acquire a browser context from the pool.

        Args:
            timeout: Maximum time to wait for a context

        Returns:
            A browser context ready to use

        Raises:
            asyncio.TimeoutError: If no context available within timeout
            RuntimeError: If pool is closed
        """
        if self._closed:
            raise RuntimeError("Pool is closed")

        if not self._initialized:
            await self.initialize()

        start_time = time.time()
        self._stats["acquire_count"] += 1

        while True:
            async with self._lock:
                # Try to get an available context
                while self._available:
                    pooled = self._available.popleft()

                    # Check if context is still valid
                    if pooled.is_stale(self._max_context_age):
                        logger.debug("Closing stale context from pool")
                        await self._close_context(pooled)
                        continue

                    # Found a valid context
                    pooled.mark_used()
                    self._in_use.add(pooled)
                    self._stats["contexts_recycled"] += 1
                    logger.debug(f"Acquired recycled context (use count: {pooled.use_count})")
                    return pooled.context

                # No available context - can we create a new one?
                total_contexts = len(self._available) + len(self._in_use)
                if total_contexts < self._max_size:
                    try:
                        pooled = await self._create_context()
                        pooled.mark_used()
                        self._in_use.add(pooled)
                        logger.debug("Acquired newly created context")
                        return pooled.context
                    except Exception as e:
                        logger.warning(f"Failed to create new context: {e}")

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise asyncio.TimeoutError(
                    f"Could not acquire browser context within {timeout}s "
                    f"(pool: {len(self._in_use)} in use, {len(self._available)} available)"
                )

            # Wait and retry
            self._stats["wait_count"] += 1
            await asyncio.sleep(0.1)

    async def release(self, context: BrowserContext) -> None:
        """
        Release a browser context back to the pool.

        Args:
            context: The browser context to release
        """
        if self._closed:
            # Pool is closed, just close the context
            try:
                await context.close()
            except Exception:
                pass
            return

        self._stats["release_count"] += 1

        async with self._lock:
            # Find the pooled context
            pooled = None
            for p in self._in_use:
                if p.context == context:
                    pooled = p
                    break

            if pooled is None:
                # Context not from this pool - close it
                logger.warning("Releasing context not from this pool")
                try:
                    await context.close()
                except Exception:
                    pass
                return

            # Remove from in_use
            self._in_use.discard(pooled)
            pooled.release()

            # Should we recycle or close?
            if pooled.is_stale(self._max_context_age):
                logger.debug("Closing stale context on release")
                await self._close_context(pooled)
            elif len(self._available) >= self._max_size:
                # Pool is at capacity, close this one
                logger.debug("Pool at capacity, closing released context")
                await self._close_context(pooled)
            else:
                # Return to available pool
                self._available.append(pooled)
                logger.debug(f"Released context back to pool (available: {len(self._available)})")

    async def _close_context(self, pooled: PooledContext) -> None:
        """Close a pooled context and update stats."""
        try:
            await pooled.context.close()
            self._stats["contexts_closed"] += 1
        except Exception as e:
            logger.warning(f"Error closing context: {e}")

    async def cleanup_idle(self) -> int:
        """
        Clean up idle contexts beyond the minimum pool size.

        Returns:
            Number of contexts cleaned up
        """
        cleaned = 0

        async with self._lock:
            # Only clean up if we have more than min_size available
            while len(self._available) > self._min_size:
                # Check the oldest available context
                if not self._available:
                    break

                pooled = self._available[0]

                if pooled.is_idle(self._idle_timeout) or pooled.is_stale(self._max_context_age):
                    self._available.popleft()
                    await self._close_context(pooled)
                    cleaned += 1
                else:
                    # Oldest is not idle, newer ones won't be either
                    break

        if cleaned:
            logger.info(f"Cleaned up {cleaned} idle browser contexts")

        return cleaned

    async def close(self) -> None:
        """Close the pool and all contexts."""
        if self._closed:
            return

        logger.info("Closing browser context pool...")

        async with self._lock:
            self._closed = True

            # Close all in-use contexts
            for pooled in list(self._in_use):
                await self._close_context(pooled)
            self._in_use.clear()

            # Close all available contexts
            while self._available:
                pooled = self._available.popleft()
                await self._close_context(pooled)

        logger.info("Browser context pool closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            **self._stats,
            "available": len(self._available),
            "in_use": len(self._in_use),
            "max_size": self._max_size,
            "min_size": self._min_size,
            "initialized": self._initialized,
            "closed": self._closed,
        }

    @property
    def available_count(self) -> int:
        """Number of available contexts."""
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        """Number of contexts currently in use."""
        return len(self._in_use)

    @property
    def total_count(self) -> int:
        """Total number of contexts in the pool."""
        return len(self._available) + len(self._in_use)


class BrowserPoolManager:
    """
    Manages browser and context pools for the entire application.

    Provides a singleton-like pattern for accessing browser pools
    across different parts of the application.
    """

    def __init__(self) -> None:
        """Initialize the pool manager."""
        self._playwright: Optional[Playwright] = None
        self._browsers: Dict[str, Browser] = {}
        self._pools: Dict[str, BrowserContextPool] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        pool_min_size: int = 1,
        pool_max_size: int = 10,
        browser_args: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the pool manager with a browser.

        Args:
            browser_type: Type of browser (chromium, firefox, webkit)
            headless: Whether to run headless
            pool_min_size: Minimum contexts in pool
            pool_max_size: Maximum contexts in pool
            browser_args: Additional browser arguments
        """
        async with self._lock:
            if self._initialized:
                return

            from playwright.async_api import async_playwright

            logger.info(f"Initializing BrowserPoolManager with {browser_type}")

            self._playwright = await async_playwright().start()

            # Get browser launcher
            if browser_type == "firefox":
                launcher = self._playwright.firefox
            elif browser_type == "webkit":
                launcher = self._playwright.webkit
            else:
                launcher = self._playwright.chromium

            # Launch browser
            launch_args = browser_args or []
            browser = await launcher.launch(headless=headless, args=launch_args)
            self._browsers[browser_type] = browser

            # Create pool
            pool = BrowserContextPool(
                browser=browser,
                min_size=pool_min_size,
                max_size=pool_max_size,
            )
            await pool.initialize()
            self._pools[browser_type] = pool

            self._initialized = True
            logger.info(f"BrowserPoolManager initialized with {browser_type} pool")

    async def get_pool(self, browser_type: str = "chromium") -> Optional[BrowserContextPool]:
        """Get the context pool for a browser type."""
        return self._pools.get(browser_type)

    async def acquire_context(
        self, browser_type: str = "chromium", timeout: float = 30.0
    ) -> BrowserContext:
        """
        Acquire a browser context from the pool.

        Args:
            browser_type: Type of browser
            timeout: Maximum time to wait

        Returns:
            A browser context ready to use
        """
        pool = self._pools.get(browser_type)
        if pool is None:
            raise RuntimeError(f"No pool available for browser type: {browser_type}")
        return await pool.acquire(timeout)

    async def release_context(
        self, context: BrowserContext, browser_type: str = "chromium"
    ) -> None:
        """
        Release a browser context back to the pool.

        Args:
            context: The context to release
            browser_type: Type of browser
        """
        pool = self._pools.get(browser_type)
        if pool:
            await pool.release(context)

    async def cleanup(self) -> None:
        """Clean up idle contexts in all pools."""
        for pool in self._pools.values():
            await pool.cleanup_idle()

    async def close(self) -> None:
        """Close all pools and browsers."""
        logger.info("Closing BrowserPoolManager...")

        # Close all pools
        for pool in self._pools.values():
            await pool.close()
        self._pools.clear()

        # Close all browsers
        for browser in self._browsers.values():
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        self._browsers.clear()

        # Stop playwright
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self._initialized = False
        logger.info("BrowserPoolManager closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all pools."""
        return {browser_type: pool.get_stats() for browser_type, pool in self._pools.items()}

    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized


# Global pool manager instance
_pool_manager: Optional[BrowserPoolManager] = None


def get_browser_pool_manager() -> BrowserPoolManager:
    """Get the global browser pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = BrowserPoolManager()
    return _pool_manager


async def reset_browser_pool_manager() -> None:
    """Reset the global browser pool manager (useful for testing)."""
    global _pool_manager
    if _pool_manager is not None:
        await _pool_manager.close()
    _pool_manager = None
