"""
Playwright Manager - Singleton for Playwright instance lifecycle.

PERFORMANCE: Starting Playwright has ~200-500ms overhead. By using a singleton,
we pay the startup cost only once per process, avoid memory churn, and enable
faster browser launches on subsequent calls.
"""

import threading
from typing import Optional

from loguru import logger


class PlaywrightManager:
    """
    Singleton manager for Playwright instance lifecycle.

    Provides a single Playwright instance shared across all browser operations
    within the application. This significantly reduces startup overhead when
    launching multiple browsers or restarting workflows.

    Usage:
        # Get Playwright instance (creates if needed)
        pw = await PlaywrightManager.get_playwright()
        browser = await pw.chromium.launch()

        # Cleanup on app shutdown
        await PlaywrightManager.cleanup()
    """

    _instance: Optional["PlaywrightManager"] = None
    _playwright = None
    _lock: threading.Lock = threading.Lock()  # threading.Lock is safe at module level

    def __new__(cls) -> "PlaywrightManager":
        """Enforce singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_playwright(cls):
        """
        Get or create the singleton Playwright instance.

        PERFORMANCE: Avoids calling async_playwright().start() on every browser
        launch. The Playwright instance is process-wide and reused across
        workflow executions.

        Returns:
            Playwright instance ready for browser launching
        """
        if cls._playwright is not None:
            return cls._playwright

        with cls._lock:
            # Double-check after acquiring lock
            if cls._playwright is not None:
                return cls._playwright

            from playwright.async_api import async_playwright

            logger.info("Initializing Playwright singleton (first browser launch)")
            cls._playwright = await async_playwright().start()
            return cls._playwright

    @classmethod
    async def cleanup(cls) -> None:
        """
        Shutdown the Playwright singleton.

        Called during application shutdown to clean up resources.
        Safe to call multiple times.
        """
        with cls._lock:
            if cls._playwright is not None:
                try:
                    await cls._playwright.stop()
                    logger.info("Playwright singleton shutdown complete")
                except Exception as e:
                    logger.warning(f"Error shutting down Playwright: {e}")
                finally:
                    cls._playwright = None

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if Playwright has been initialized.

        Returns:
            True if Playwright instance exists
        """
        return cls._playwright is not None

    @classmethod
    async def get_browser_types(cls):
        """
        Get available browser types from Playwright.

        Returns:
            Tuple of (chromium, firefox, webkit) browser type objects
        """
        pw = await cls.get_playwright()
        return pw.chromium, pw.firefox, pw.webkit


# Module-level convenience functions for backward compatibility
async def get_playwright_singleton():
    """
    Get or create the singleton Playwright instance.

    Convenience wrapper for PlaywrightManager.get_playwright().
    Maintains backward compatibility with existing code.

    Returns:
        Playwright instance
    """
    return await PlaywrightManager.get_playwright()


async def shutdown_playwright_singleton():
    """
    Shutdown the Playwright singleton.

    Convenience wrapper for PlaywrightManager.cleanup().
    Maintains backward compatibility with existing code.
    """
    await PlaywrightManager.cleanup()
