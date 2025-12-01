"""
CasareRPA - Infrastructure: Browser Resource Manager
Manages Playwright browser instances, contexts, and pages.
"""

from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page


class BrowserResourceManager:
    """
    Browser resource manager - manages Playwright infrastructure.

    This infrastructure component is responsible for:
    - Managing browser instances
    - Tracking browser contexts
    - Managing pages (tabs)
    - Async resource cleanup

    It contains NO domain logic - only infrastructure concerns.
    """

    def __init__(self) -> None:
        """Initialize browser resource manager."""
        # Playwright resources
        self.browser: Optional["Browser"] = None
        self.browser_contexts: List["BrowserContext"] = []
        self.pages: Dict[str, "Page"] = {}  # Named pages for multiple tabs
        self.active_page: Optional["Page"] = None

    def set_browser(self, browser: "Browser") -> None:
        """
        Set the active browser instance.

        Args:
            browser: Playwright browser instance
        """
        self.browser = browser
        logger.debug("Browser instance set in resource manager")

    def get_browser(self) -> Optional["Browser"]:
        """
        Get the active browser instance.

        Returns:
            Browser instance or None
        """
        return self.browser

    def add_browser_context(self, context: "BrowserContext") -> None:
        """
        Track a browser context for cleanup.

        Args:
            context: Playwright browser context object
        """
        self.browser_contexts.append(context)
        logger.debug(f"Browser context added (total: {len(self.browser_contexts)})")

    def get_browser_contexts(self) -> List["BrowserContext"]:
        """
        Get all tracked browser contexts.

        Returns:
            List of browser contexts
        """
        return self.browser_contexts.copy()

    def set_page(
        self, page: "Page", name: str = "default", set_active: bool = True
    ) -> None:
        """
        Add a page and optionally set it as active.

        Args:
            page: Playwright page object
            name: Page identifier (for multiple tabs)
            set_active: If True, set this page as active
        """
        self.pages[name] = page
        if set_active:
            self.active_page = page
        logger.debug(f"Page set: {name} (active: {set_active})")

    def add_page(self, page: "Page", name: str) -> None:
        """
        Add a page to the resource manager.

        Args:
            page: Playwright page object
            name: Page identifier
        """
        self.pages[name] = page
        logger.debug(f"Page added: {name}")

    def get_page(self, name: str = "default") -> Optional["Page"]:
        """
        Get a page by name.

        Args:
            name: Page identifier

        Returns:
            Page instance or None
        """
        return self.pages.get(name)

    def get_active_page(self) -> Optional["Page"]:
        """
        Get the currently active page.

        Returns:
            Active page or None
        """
        return self.active_page

    def set_active_page(self, page: "Page", name: str = "default") -> None:
        """
        Set the active page and store it with a name.

        Args:
            page: Playwright page object
            name: Page identifier (for multiple tabs)
        """
        self.active_page = page
        self.pages[name] = page
        logger.debug(f"Active page set: {name}")

    def close_page(self, name: str) -> None:
        """
        Close and remove a named page.

        Args:
            name: Page identifier
        """
        if name in self.pages:
            page = self.pages[name]
            del self.pages[name]
            if self.active_page == page:
                self.active_page = None
            logger.debug(f"Page closed: {name}")

    def clear_pages(self) -> None:
        """Clear all pages from the manager."""
        self.pages.clear()
        self.active_page = None
        logger.debug("All pages cleared")

    async def cleanup(self, skip_browser: bool = False) -> None:
        """
        Clean up all Playwright resources (close browser, pages, contexts).

        Should be called when execution completes or fails.
        This is an async operation that properly closes all Playwright resources.

        Args:
            skip_browser: If True, keep the browser open (for "do not close" option)
        """
        if skip_browser:
            logger.info("Browser cleanup skipped - keeping browser open")
            # Clear references but don't close resources
            self.pages.clear()
            self.active_page = None
            self.browser_contexts.clear()
            self.browser = None
            return

        # Close all pages
        for name, page in list(self.pages.items()):
            try:
                await page.close()
                logger.debug(f"Page '{name}' closed")
            except Exception as e:
                logger.warning(f"Error closing page '{name}': {e}")

        self.pages.clear()
        self.active_page = None

        # Close all browser contexts
        for i, context in enumerate(self.browser_contexts):
            try:
                await context.close()
                logger.debug(f"Browser context {i} closed")
            except Exception as e:
                logger.warning(f"Error closing browser context {i}: {e}")

        self.browser_contexts.clear()

        # Close browser
        if self.browser:
            try:
                await self.browser.close()
                logger.debug("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self.browser = None

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"BrowserResourceManager("
            f"browser={'set' if self.browser else 'None'}, "
            f"contexts={len(self.browser_contexts)}, "
            f"pages={len(self.pages)})"
        )
