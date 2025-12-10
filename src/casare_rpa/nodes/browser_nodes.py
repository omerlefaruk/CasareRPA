"""
Browser control nodes for Playwright automation.

This module provides nodes for controlling browser lifecycle:
launching browsers, managing tabs, and cleanup.
"""

import asyncio
from typing import Optional

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils.resilience import retry_operation
from ..utils.config import DEFAULT_BROWSER, HEADLESS_MODE, BROWSER_ARGS
from loguru import logger


# =============================================================================
# PERFORMANCE: Playwright Singleton (via PlaywrightManager)
# =============================================================================
# Starting Playwright has overhead (~200-500ms). Using PlaywrightManager, we:
# - Pay the startup cost only once per process
# - Avoid memory churn from multiple Playwright instances
# - Enable faster browser launches on subsequent calls
# - Centralize lifecycle management in infrastructure layer

from casare_rpa.infrastructure.browser.playwright_manager import (
    PlaywrightManager,
    get_playwright_singleton,
    shutdown_playwright_singleton,
)


@node_schema(
    PropertyDef(
        "url",
        PropertyType.STRING,
        default="",
        label="URL",
        placeholder="https://example.com",
        tooltip="Initial URL to navigate to after launching browser",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "browser_type",
        PropertyType.CHOICE,
        default=DEFAULT_BROWSER,
        choices=["chromium", "firefox", "webkit"],
        label="Browser Type",
        tooltip="Browser to launch (chromium, firefox, or webkit)",
    ),
    PropertyDef(
        "headless",
        PropertyType.BOOLEAN,
        default=HEADLESS_MODE,
        label="Headless Mode",
        tooltip="Run browser without visible window",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "window_state",
        PropertyType.CHOICE,
        default="normal",
        choices=["normal", "maximized", "minimized"],
        label="Window State",
        tooltip="Initial window state (normal, maximized, or minimized)",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "do_not_close",
        PropertyType.BOOLEAN,
        default=True,
        label="Do Not Close After Launch",
        tooltip="Keep browser open after workflow execution completes",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "slow_mo",
        PropertyType.INTEGER,
        default=0,
        label="Slow Motion (ms)",
        tooltip="Slow down operations by milliseconds (for debugging)",
        min_value=0,
    ),
    PropertyDef(
        "channel",
        PropertyType.STRING,
        default="",
        label="Browser Channel",
        tooltip="Browser channel (chrome, msedge, chrome-beta) - chromium only",
        placeholder="chrome, msedge, etc.",
    ),
    PropertyDef(
        "viewport_width",
        PropertyType.INTEGER,
        default=1280,
        label="Viewport Width",
        tooltip="Browser viewport width in pixels",
        min_value=1,
    ),
    PropertyDef(
        "viewport_height",
        PropertyType.INTEGER,
        default=720,
        label="Viewport Height",
        tooltip="Browser viewport height in pixels",
        min_value=1,
    ),
    PropertyDef(
        "user_agent",
        PropertyType.STRING,
        default="",
        label="User Agent",
        tooltip="Custom user agent string",
        placeholder="Mozilla/5.0 ...",
    ),
    PropertyDef(
        "locale",
        PropertyType.STRING,
        default="",
        label="Locale",
        tooltip="Browser locale (e.g., en-US, es-ES)",
        placeholder="en-US",
    ),
    PropertyDef(
        "timezone_id",
        PropertyType.STRING,
        default="",
        label="Timezone ID",
        tooltip="Timezone identifier (e.g., America/New_York)",
        placeholder="America/New_York",
    ),
    PropertyDef(
        "color_scheme",
        PropertyType.CHOICE,
        default="light",
        choices=["light", "dark", "no-preference"],
        label="Color Scheme",
        tooltip="Preferred color scheme for the browser",
    ),
    PropertyDef(
        "ignore_https_errors",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore HTTPS Errors",
        tooltip="Ignore HTTPS certificate errors",
    ),
    PropertyDef(
        "proxy_server",
        PropertyType.STRING,
        default="",
        label="Proxy Server",
        tooltip="Proxy server URL",
        placeholder="http://proxy.example.com:8080",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
        min_value=0,
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=2000,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "window_wait",
        PropertyType.INTEGER,
        default=100,
        label="Window Wait (ms)",
        tooltip="Time to wait for browser window detection (for maximize/minimize). Set to 0 to skip.",
        min_value=0,
        tab="advanced",
    ),
)
@executable_node
class LaunchBrowserNode(BaseNode):
    """
    Launch browser node - creates a new browser instance.

    Opens a browser (Chromium, Firefox, or WebKit) using Playwright
    and stores it in the execution context for use by other nodes.
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: url -> browser, page, window

    def __init__(
        self,
        node_id: str,
        name: str = "Launch Browser",
        **kwargs,
    ) -> None:
        """
        Initialize launch browser node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LaunchBrowserNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("url", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("browser", PortType.OUTPUT, DataType.BROWSER)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)
        self.add_output_port("window", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute browser launch.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with browser instance
        """
        self.status = NodeStatus.RUNNING

        # Get retry options
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 2000)

        last_error = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                if attempts > 1:
                    logger.info(
                        f"Retry attempt {attempts - 1}/{retry_count} for browser launch"
                    )

                browser_type = self.get_parameter("browser_type", DEFAULT_BROWSER)
                headless = self.get_parameter("headless", HEADLESS_MODE)

                logger.info(f"Launching {browser_type} browser (headless={headless})")

                # Build launch options
                launch_options = {"headless": headless}

                # Add slow_mo if specified (for debugging)
                slow_mo = self.get_parameter("slow_mo", 0)
                if slow_mo > 0:
                    launch_options["slow_mo"] = slow_mo

                # Add channel for chromium-based browsers
                channel = self.get_parameter("channel", "")
                if channel and browser_type == "chromium":
                    launch_options["channel"] = channel

                # PERFORMANCE: Use Playwright singleton instead of creating new instance
                # This avoids ~200-500ms startup overhead on subsequent browser launches
                playwright = await get_playwright_singleton()

                # Get browser type and launch with options
                if browser_type == "firefox":
                    browser = await playwright.firefox.launch(**launch_options)
                elif browser_type == "webkit":
                    browser = await playwright.webkit.launch(**launch_options)
                else:  # chromium (default)
                    # Add chromium-specific args
                    launch_options["args"] = BROWSER_ARGS
                    browser = await playwright.chromium.launch(**launch_options)

                # Store browser in context
                context.browser = browser

                # Build browser context options
                context_options = {}

                # Viewport settings
                viewport_width = self.get_parameter("viewport_width", 1280)
                viewport_height = self.get_parameter("viewport_height", 720)
                context_options["viewport"] = {
                    "width": viewport_width,
                    "height": viewport_height,
                }

                # User agent
                user_agent = self.get_parameter("user_agent", "")
                if user_agent:
                    context_options["user_agent"] = user_agent

                # Locale
                locale = self.get_parameter("locale", "")
                if locale:
                    context_options["locale"] = locale

                # Timezone
                timezone_id = self.get_parameter("timezone_id", "")
                if timezone_id:
                    context_options["timezone_id"] = timezone_id

                # Color scheme
                color_scheme = self.get_parameter("color_scheme", "light")
                if color_scheme and color_scheme != "light":
                    context_options["color_scheme"] = color_scheme

                # HTTPS errors
                if self.get_parameter("ignore_https_errors", False):
                    context_options["ignore_https_errors"] = True

                # Proxy
                proxy_server = self.get_parameter("proxy_server", "")
                if proxy_server:
                    context_options["proxy"] = {"server": proxy_server}

                logger.debug(f"Browser context options: {context_options}")

                # Create initial tab automatically with context options
                browser_context = await browser.new_context(**context_options)
                context.add_browser_context(browser_context)  # Track for cleanup
                page = await browser_context.new_page()

                # Navigate to URL if provided
                url = self.get_parameter("url", "")

                # Strip whitespace and normalize to empty string if None or whitespace-only
                url = url.strip() if url else ""

                # Resolve {{variable}} patterns in URL using context variables
                url = context.resolve_value(url)
                logger.debug(
                    f"LaunchBrowserNode URL after variable resolution: '{url}'"
                )

                if url:
                    # Add protocol if missing
                    if not url.startswith(("http://", "https://", "file://", "about:")):
                        url = f"https://{url}"
                    logger.info(f"Navigating to URL: {url}")
                    await page.goto(url)
                else:
                    logger.info("Opening blank page")
                    await page.goto("about:blank")

                # Store page in context
                tab_name = "main"
                context.add_page(page, tab_name)
                context.set_active_page(page, tab_name)

                # Store do_not_close flag in context for cleanup handling
                do_not_close = self.get_parameter("do_not_close", False)
                if do_not_close:
                    context.set_variable("_browser_do_not_close", True)
                    logger.info("Browser marked as 'do not close' after execution")

                # Set outputs
                self.set_output_value("browser", browser)
                self.set_output_value("page", page)

                # Get browser window for desktop window operations (maximize/minimize)
                browser_window = None
                window_wait = self.get_parameter("window_wait", 100)
                if not headless and window_wait >= 0:
                    try:
                        import uiautomation as auto
                        from casare_rpa.desktop.element import DesktopElement
                        from concurrent.futures import (
                            ThreadPoolExecutor,
                            TimeoutError as FuturesTimeoutError,
                        )

                        # Wait for window to fully initialize
                        if window_wait > 0:
                            await asyncio.sleep(window_wait / 1000)

                        def find_browser_window():
                            """Find browser window using efficient class name search."""
                            # Use WindowControl directly with ClassName - much faster than iterating all
                            browser_classes = [
                                "Chrome_WidgetWin_1",
                                "MozillaWindowClass",
                            ]
                            for class_name in browser_classes:
                                try:
                                    window = auto.WindowControl(
                                        ClassName=class_name, searchDepth=1
                                    )
                                    if window.Exists(
                                        0.5, 0.1
                                    ):  # 500ms max wait, 100ms interval
                                        return window, class_name
                                except Exception:
                                    continue
                            return None, None

                        # Run window search in thread with 2 second timeout to avoid blocking
                        loop = asyncio.get_event_loop()
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            try:
                                window, class_name = await asyncio.wait_for(
                                    loop.run_in_executor(executor, find_browser_window),
                                    timeout=2.0,
                                )
                                if window:
                                    browser_window = DesktopElement(window)
                                    logger.info(
                                        f"Found browser window: {window.Name} (class={class_name})"
                                    )

                                    # Apply window state
                                    window_state = self.get_parameter(
                                        "window_state", "normal"
                                    )
                                    if window_state == "maximized":
                                        try:
                                            window.Maximize()
                                            logger.info("Browser window maximized")
                                        except Exception as max_err:
                                            logger.warning(
                                                f"Failed to maximize window: {max_err}"
                                            )
                                    elif window_state == "minimized":
                                        try:
                                            window.Minimize()
                                            logger.info("Browser window minimized")
                                        except Exception as min_err:
                                            logger.warning(
                                                f"Failed to minimize window: {min_err}"
                                            )
                                    # "normal" state - no action needed (default)
                                else:
                                    logger.debug(
                                        "Browser window not found within timeout"
                                    )
                            except asyncio.TimeoutError:
                                logger.debug(
                                    "Browser window search timed out (2s) - skipping"
                                )

                    except Exception as e:
                        logger.warning(f"Could not get browser window handle: {e}")

                self.set_output_value("window", browser_window)

                # Emit BROWSER_PAGE_READY event for UI to enable picker/recorder
                try:
                    from casare_rpa.domain.events import get_event_bus, Event
                    from casare_rpa.domain.value_objects.types import EventType

                    event_bus = get_event_bus()
                    handlers = event_bus._handlers.get(EventType.BROWSER_PAGE_READY, [])
                    logger.info(
                        f"Publishing BROWSER_PAGE_READY (bus={id(event_bus)}, handlers={len(handlers)})"
                    )
                    event_bus.publish(
                        Event(
                            EventType.BROWSER_PAGE_READY,
                            data={"page": page},
                            node_id=getattr(self, "node_id", None),
                        )
                    )
                    logger.info("BROWSER_PAGE_READY event published successfully")
                except Exception as e:
                    logger.error(f"Could not emit BROWSER_PAGE_READY event: {e}")

                self.status = NodeStatus.SUCCESS
                logger.info(
                    f"Browser launched successfully: {browser_type} with initial tab (attempt {attempts})"
                )

                return {
                    "success": True,
                    "data": {
                        "browser": browser,
                        "page": page,
                        "window": browser_window,
                        "browser_type": browser_type,
                        "headless": headless,
                        "attempts": attempts,
                    },
                    "next_nodes": ["exec_out"],
                }

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    logger.warning(f"Browser launch failed (attempt {attempts}): {e}")
                    await asyncio.sleep(retry_interval / 1000)
                else:
                    break

        # All retries exhausted
        self.status = NodeStatus.ERROR
        logger.error(
            f"Failed to launch browser after {attempts} attempts: {last_error}"
        )
        return {"success": False, "error": str(last_error), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        browser_type = self.get_parameter("browser_type", "")
        if browser_type not in ["chromium", "firefox", "webkit"]:
            return False, f"Invalid browser type: {browser_type}"
        return True, ""


@node_schema(
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        label="Timeout (ms)",
        tooltip="Timeout for close operation in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "force_close",
        PropertyType.BOOLEAN,
        default=False,
        label="Force Close",
        tooltip="Force close even if pages have unsaved changes",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
        min_value=0,
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in milliseconds",
        min_value=0,
    ),
)
@executable_node
class CloseBrowserNode(BaseNode):
    """
    Close browser node - closes the browser instance.

    Properly closes the browser and cleans up resources.
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: browser -> none

    def __init__(self, node_id: str, name: str = "Close Browser", **kwargs) -> None:
        """
        Initialize close browser node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CloseBrowserNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER, required=False)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute browser close.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get browser from input or context
            browser = self.get_input_value("browser")
            if browser is None:
                browser = context.browser

            if browser is None:
                raise ValueError("No browser instance found to close")

            # Get retry options
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)

            logger.info("Closing browser")

            async def close_browser():
                await browser.close()
                context.browser = None
                context.clear_pages()
                return True

            result = await retry_operation(
                close_browser,
                max_attempts=retry_count + 1,
                delay_seconds=retry_interval / 1000,
                operation_name="browser close",
            )

            if result.success:
                self.status = NodeStatus.SUCCESS
                logger.info(f"Browser closed successfully (attempt {result.attempts})")
                return {
                    "success": True,
                    "data": {"message": "Browser closed", "attempts": result.attempts},
                    "next_nodes": ["exec_out"],
                }
            else:
                raise result.last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to close browser: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


@node_schema(
    PropertyDef(
        "tab_name",
        PropertyType.STRING,
        default="main",
        label="Tab Name",
        tooltip="Name to identify this tab",
        required=True,
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "url",
        PropertyType.STRING,
        default="",
        label="URL",
        tooltip="Optional URL to navigate to after creating tab",
        placeholder="https://example.com",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        label="Timeout (ms)",
        tooltip="Navigation timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        label="Wait Until",
        tooltip="Navigation wait event",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
        min_value=0,
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Failure",
        tooltip="Take screenshot when tab creation fails",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.FILE_PATH,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot (auto-generated if empty)",
        placeholder="screenshots/error.png",
    ),
)
@executable_node
class NewTabNode(BaseNode):
    """
    New tab node - creates a new browser tab/page.

    Opens a new tab in the browser and optionally sets it as active.
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: browser -> page

    def __init__(self, node_id: str, name: str = "New Tab", **kwargs) -> None:
        """
        Initialize new tab node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "NewTabNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER, required=False)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute new tab creation.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with new page instance
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get browser from input or context
            browser = self.get_input_value("browser")
            if browser is None:
                browser = context.browser

            if browser is None:
                raise ValueError("No browser instance found")

            tab_name = self.get_parameter("tab_name", "main")
            url = self.get_parameter("url", "")
            timeout = self.get_parameter("timeout", 30000)
            wait_until = self.get_parameter("wait_until", "load")
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            logger.info(f"Creating new tab: {tab_name}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1
            page = None

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for new tab"
                        )

                    # Reuse existing browser context if available (much faster)
                    # Creating a new page in existing context shares cookies/session
                    current_page = context.get_active_page()
                    if current_page:
                        # Reuse the existing context from current page
                        browser_context = current_page.context
                        page = await browser_context.new_page()
                        logger.debug("Created new page in existing browser context")
                    else:
                        # No existing context - create a new one
                        browser_context = await browser.new_context()
                        context.add_browser_context(
                            browser_context
                        )  # Track for cleanup
                        page = await browser_context.new_page()
                        logger.debug("Created new browser context for first page")

                    # Navigate to URL if specified
                    if url and url.strip():
                        nav_url = url.strip()
                        # Resolve {{variable}} patterns in URL
                        nav_url = context.resolve_value(nav_url)
                        logger.debug(
                            f"NewTabNode URL after variable resolution: '{nav_url}'"
                        )
                        # Add protocol if missing
                        if not nav_url.startswith(
                            ("http://", "https://", "file://", "about:")
                        ):
                            nav_url = f"https://{nav_url}"
                        logger.info(f"Navigating new tab to: {nav_url}")
                        await page.goto(nav_url, timeout=timeout, wait_until=wait_until)

                    # Store page in context
                    context.add_page(page, tab_name)
                    context.set_active_page(page, tab_name)

                    # Set output
                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(
                        f"Tab created successfully: {tab_name} (attempt {attempts})"
                    )

                    return {
                        "success": True,
                        "data": {
                            "tab_name": tab_name,
                            "page": page,
                            "url": url if url else "about:blank",
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"New tab creation failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime

                    if screenshot_path:
                        path = screenshot_path
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"new_tab_fail_{timestamp}.png"

                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    await page.screenshot(path=path)
                    logger.info(f"Failure screenshot saved: {path}")
                except Exception as ss_error:
                    logger.warning(f"Failed to take screenshot: {ss_error}")

            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to create tab: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        tab_name = self.get_parameter("tab_name", "")
        if not tab_name:
            return False, "Tab name cannot be empty"
        return True, ""


@node_schema(
    PropertyDef(
        "min_width",
        PropertyType.INTEGER,
        default=0,
        label="Min Width (px)",
        tooltip="Minimum image width in pixels (0 = no filter)",
        min_value=0,
    ),
    PropertyDef(
        "min_height",
        PropertyType.INTEGER,
        default=0,
        label="Min Height (px)",
        tooltip="Minimum image height in pixels (0 = no filter)",
        min_value=0,
    ),
    PropertyDef(
        "include_backgrounds",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Backgrounds",
        tooltip="Include CSS background images",
    ),
    PropertyDef(
        "file_types",
        PropertyType.STRING,
        default="",
        label="File Types",
        tooltip="Comma-separated file extensions to include (empty = all)",
        placeholder="jpg,png,webp",
    ),
)
@executable_node
class GetAllImagesNode(BaseNode):
    """
    Get all images from the current page.

    Extracts all image URLs (from <img> tags and CSS background images)
    from the current page. Can filter by minimum size and file type.

    Outputs:
        - images: List of image URLs
        - count: Number of images found
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: none -> images, count

    def __init__(self, node_id: str, name: str = "Get All Images", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetAllImagesNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_output_port("images", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Extract all image URLs from the page."""
        try:
            page = context.get_active_page()
            if not page:
                raise ValueError("No active page. Launch browser and navigate first.")

            min_width = self.get_parameter("min_width", 0)
            min_height = self.get_parameter("min_height", 0)
            include_backgrounds = self.get_parameter("include_backgrounds", True)
            file_types_str = self.get_parameter("file_types", "")

            # Parse allowed file types
            allowed_types = []
            if file_types_str:
                allowed_types = [
                    f".{t.strip().lower().lstrip('.')}"
                    for t in file_types_str.split(",")
                ]

            # JavaScript to extract all images
            js_code = """
            (includeBackgrounds) => {
                const images = [];
                const seen = new Set();

                // Get all <img> elements
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.dataset.src || img.getAttribute('data-lazy-src');
                    if (src && !seen.has(src)) {
                        seen.add(src);
                        images.push({
                            url: src,
                            width: img.naturalWidth || img.width || 0,
                            height: img.naturalHeight || img.height || 0,
                            alt: img.alt || '',
                            type: 'img'
                        });
                    }
                });

                // Get <source> elements in <picture>
                document.querySelectorAll('picture source').forEach(source => {
                    const srcset = source.srcset;
                    if (srcset) {
                        // Parse srcset and get the largest image
                        const urls = srcset.split(',').map(s => s.trim().split(' ')[0]);
                        urls.forEach(url => {
                            if (url && !seen.has(url)) {
                                seen.add(url);
                                images.push({
                                    url: url,
                                    width: 0,
                                    height: 0,
                                    alt: '',
                                    type: 'source'
                                });
                            }
                        });
                    }
                });

                // Get CSS background images if requested
                if (includeBackgrounds) {
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            const match = bgImage.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/);
                            if (match && match[1] && !seen.has(match[1])) {
                                seen.add(match[1]);
                                images.push({
                                    url: match[1],
                                    width: 0,
                                    height: 0,
                                    alt: '',
                                    type: 'background'
                                });
                            }
                        }
                    });
                }

                return images;
            }
            """

            # Execute JavaScript
            all_images = await page.evaluate(js_code, include_backgrounds)

            # Filter by size and file type
            filtered_images = []
            for img in all_images:
                url = img.get("url", "")
                if not url or url.startswith("data:"):
                    continue

                # Check size filter
                width = img.get("width", 0)
                height = img.get("height", 0)
                if min_width > 0 and width < min_width:
                    continue
                if min_height > 0 and height < min_height:
                    continue

                # Check file type filter
                if allowed_types:
                    url_lower = url.lower().split("?")[0]  # Remove query params
                    if not any(url_lower.endswith(ext) for ext in allowed_types):
                        continue

                filtered_images.append(url)

            # Set outputs
            self.set_output_value("images", filtered_images)
            self.set_output_value("count", len(filtered_images))

            self.status = NodeStatus.SUCCESS
            logger.info(f"Found {len(filtered_images)} images on page")

            return {
                "success": True,
                "data": {"images": filtered_images, "count": len(filtered_images)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get images: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "save_path",
        PropertyType.FILE_PATH,
        default="",
        label="Save Path",
        tooltip="Local file path to save to (supports {{variables}})",
        placeholder="C:/downloads/file.pdf",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "use_browser",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Browser Context",
        tooltip="Use browser context for download (for authenticated sites)",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        label="Timeout (ms)",
        tooltip="Download timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=True,
        label="Overwrite Existing",
        tooltip="Overwrite existing file if it exists",
    ),
    PropertyDef(
        "verify_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Verify SSL Certificate",
        tooltip="Verify SSL certificate when downloading. Disable only for trusted internal sites with self-signed certificates.",
    ),
)
@executable_node
class DownloadFileNode(BaseNode):
    """
    Download a file from URL to local path.

    Downloads any file (image, document, etc.) from a URL and saves it
    to a local file path. Supports both direct URL downloads and
    downloading through the browser context for authenticated sessions.

    Inputs:
        - url: URL of the file to download
        - filename: Optional filename override

    Outputs:
        - path: Full path where file was saved
        - size: File size in bytes
        - success: Whether download succeeded
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: url, filename -> path, attachment_file, size, success

    def __init__(self, node_id: str, name: str = "Download File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DownloadFileNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("filename", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("attachment_file", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Download file from URL."""
        import os
        import urllib.request
        import ssl
        from urllib.parse import urlparse, unquote

        try:
            url = self.get_parameter("url")
            filename_override = self.get_input_value("filename")

            # Resolve variables
            if hasattr(context, "resolve_value"):
                if url:
                    url = context.resolve_value(url)
                if filename_override:
                    filename_override = context.resolve_value(filename_override)

            if not url:
                raise ValueError("URL is required")

            save_path = self.get_parameter("save_path", "")
            if hasattr(context, "resolve_value") and save_path:
                save_path = context.resolve_value(save_path)

            use_browser = self.get_parameter("use_browser", False)
            timeout = self.get_parameter("timeout", 30000)
            overwrite = self.get_parameter("overwrite", True)

            # Determine filename
            if filename_override:
                filename = filename_override
            else:
                # Extract filename from URL
                parsed = urlparse(url)
                filename = os.path.basename(unquote(parsed.path))
                if not filename or "." not in filename:
                    # Generate a filename based on URL hash
                    import hashlib

                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    # Try to guess extension from URL
                    ext = ".jpg"  # Default
                    url_lower = url.lower()
                    for e in [".png", ".gif", ".webp", ".svg", ".jpeg", ".bmp"]:
                        if e in url_lower:
                            ext = e
                            break
                    filename = f"download_{url_hash}{ext}"

            # Determine full save path
            if save_path:
                if os.path.isdir(save_path):
                    full_path = os.path.join(save_path, filename)
                else:
                    # save_path is the full file path
                    full_path = save_path
            else:
                # Default to downloads folder
                downloads_dir = os.path.expanduser("~/Downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                full_path = os.path.join(downloads_dir, filename)

            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # Check if file exists
            if os.path.exists(full_path) and not overwrite:
                # Add number suffix
                base, ext = os.path.splitext(full_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                full_path = f"{base}_{counter}{ext}"

            file_size = 0

            if use_browser:
                # Download using browser context (for authenticated sessions)
                page = context.get_active_page()
                if not page:
                    raise ValueError("No active page for browser download")

                # Use page.request to download
                response = await page.request.get(url, timeout=timeout)
                content = await response.body()

                with open(full_path, "wb") as f:
                    f.write(content)
                file_size = len(content)
            else:
                # Direct download using urllib (run in executor to not block)
                import asyncio

                verify_ssl = self.get_parameter("verify_ssl", True)

                def download_file():
                    # Create SSL context based on verify_ssl setting
                    if verify_ssl:
                        ctx = ssl.create_default_context()
                    else:
                        # WARNING: Disabling SSL verification is insecure
                        # Only use for trusted internal sites with self-signed certs
                        logger.warning(
                            f"SSL verification disabled for download from {url}. "
                            "This is insecure and should only be used for trusted internal sites."
                        )
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE

                    req = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        },
                    )
                    with urllib.request.urlopen(
                        req, timeout=timeout / 1000, context=ctx
                    ) as response:
                        content = response.read()
                        with open(full_path, "wb") as f:
                            f.write(content)
                        return len(content)

                loop = asyncio.get_event_loop()
                file_size = await loop.run_in_executor(None, download_file)

            # Set outputs
            self.set_output_value("path", full_path)
            self.set_output_value("attachment_file", [full_path])
            self.set_output_value("size", file_size)
            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Downloaded {url} to {full_path} ({file_size} bytes)")

            return {
                "success": True,
                "data": {"path": full_path, "size": file_size, "url": url},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("success", False)
            logger.error(f"Failed to download file: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
