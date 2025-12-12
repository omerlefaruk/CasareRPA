"""
Browser lifecycle nodes.

Handles launching and closing browser instances.
"""

import asyncio
from typing import Tuple

from loguru import logger

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
from casare_rpa.utils.config import (
    DEFAULT_BROWSER,
    HEADLESS_MODE,
    BROWSER_ARGS,
    PLAYWRIGHT_IGNORE_ARGS,
)
from casare_rpa.infrastructure.browser.playwright_manager import (
    get_playwright_singleton,
)


def _get_browser_profile_path(
    profile_mode: str, custom_path: str = ""
) -> Tuple[str, str]:
    """
    Resolve browser profile path and profile directory based on profile mode.

    Args:
        profile_mode: One of 'none', 'custom', 'chrome_default', 'chrome_profile_1',
                      'chrome_profile_2', 'edge_default'
        custom_path: Custom path to use when profile_mode is 'custom'

    Returns:
        Tuple of (user_data_dir, profile_directory)
        - Empty strings for 'none' mode
        - For system profiles, returns the User Data path and profile subdirectory name
    """
    if profile_mode == "none":
        return "", ""
    elif profile_mode == "custom":
        return custom_path, ""

    import os

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if not local_appdata:
        logger.warning("LOCALAPPDATA environment variable not found")
        return "", ""

    # Map profile modes to (user_data_dir, profile_directory)
    # Chrome/Edge store profiles as subdirectories within "User Data"
    profile_config = {
        "chrome_default": (
            os.path.join(local_appdata, "Google", "Chrome", "User Data"),
            "Default",
        ),
        "chrome_profile_1": (
            os.path.join(local_appdata, "Google", "Chrome", "User Data"),
            "Profile 1",
        ),
        "chrome_profile_2": (
            os.path.join(local_appdata, "Google", "Chrome", "User Data"),
            "Profile 2",
        ),
        "edge_default": (
            os.path.join(local_appdata, "Microsoft", "Edge", "User Data"),
            "Default",
        ),
    }

    return profile_config.get(profile_mode, ("", ""))


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
        "profile_mode",
        PropertyType.CHOICE,
        default="none",
        choices=[
            "none",
            "custom",
            "chrome_default",
            "chrome_profile_1",
            "chrome_profile_2",
            "edge_default",
        ],
        label="Profile Mode",
        tooltip="Browser profile for persistent sessions. 'none'=fresh browser, 'custom'=use User Data Directory path, others=use system browser profiles (close browser first!)",
        essential=True,
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
        "user_data_dir",
        PropertyType.STRING,
        default="",
        label="User Data Directory",
        tooltip="Path to custom browser profile directory (only used when Profile Mode is 'custom')",
        placeholder="C:/BrowserProfiles/instagram",
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

                # Resolve profile path based on profile_mode setting
                profile_mode = self.get_parameter("profile_mode", "none")
                custom_user_data_dir = self.get_parameter("user_data_dir", "")
                user_data_dir, profile_directory = _get_browser_profile_path(
                    profile_mode, custom_user_data_dir
                )

                logger.info(
                    f"Launching {browser_type} browser (headless={headless}, profile_mode={profile_mode})"
                )

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

                # Build browser context options (used for both persistent and non-persistent)
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

                # Check if using persistent context (user_data_dir specified)
                if user_data_dir:
                    # Use persistent context - this preserves login state, cookies, etc.
                    import os

                    # Only create directory for custom profiles, not for system browser profiles
                    if profile_mode == "custom":
                        os.makedirs(user_data_dir, exist_ok=True)

                    if profile_directory:
                        logger.info(
                            f"Using system browser profile: {user_data_dir} (profile: {profile_directory})"
                        )
                    else:
                        logger.info(
                            f"Using persistent browser profile: {user_data_dir}"
                        )

                    # Merge launch options into context options for persistent context
                    persistent_options = {**context_options, **launch_options}
                    if browser_type == "chromium":
                        # Start with base browser args
                        args = list(BROWSER_ARGS)

                        # When using system browser profiles, remove --disable-web-security
                        # Chrome rejects this flag with default user-data-dir
                        if profile_directory:
                            args = [
                                arg
                                for arg in args
                                if not arg.startswith("--disable-web-security")
                            ]
                            args.append(f"--profile-directory={profile_directory}")

                        persistent_options["args"] = args
                    # Remove Playwright's default automation-revealing args
                    persistent_options["ignore_default_args"] = PLAYWRIGHT_IGNORE_ARGS

                    # Get browser type object
                    if browser_type == "firefox":
                        browser_type_obj = playwright.firefox
                    elif browser_type == "webkit":
                        browser_type_obj = playwright.webkit
                    else:
                        browser_type_obj = playwright.chromium

                    # Launch persistent context (combines browser + context)
                    try:
                        browser_context = (
                            await browser_type_obj.launch_persistent_context(
                                user_data_dir, **persistent_options
                            )
                        )
                    except Exception as launch_err:
                        # Check for profile lock error (exitCode=21)
                        err_str = str(launch_err)
                        if (
                            "exitCode=21" in err_str
                            or "Target page, context or browser has been closed"
                            in err_str
                        ):
                            if profile_directory:
                                raise RuntimeError(
                                    f"Cannot launch browser: Chrome profile '{profile_directory}' is locked. "
                                    f"Please close Chrome completely before using system profiles. "
                                    f"Alternatively, use 'custom' or 'none' profile mode."
                                ) from launch_err
                            else:
                                raise RuntimeError(
                                    f"Cannot launch browser: Profile directory '{user_data_dir}' is locked. "
                                    f"Close any browser using this profile, or choose a different directory."
                                ) from launch_err
                        raise
                    context.add_browser_context(browser_context)  # Track for cleanup

                    # Persistent context is itself the "browser" (no separate browser object)
                    browser = None
                    context.browser = browser_context  # Store context as browser

                    # Get existing page or create new one
                    if browser_context.pages:
                        page = browser_context.pages[0]
                    else:
                        page = await browser_context.new_page()
                else:
                    # Regular browser launch (non-persistent)
                    # Get browser type and launch with options
                    if browser_type == "firefox":
                        browser = await playwright.firefox.launch(**launch_options)
                    elif browser_type == "webkit":
                        browser = await playwright.webkit.launch(**launch_options)
                    else:  # chromium (default)
                        # Add chromium-specific args and anti-detection settings
                        launch_options["args"] = BROWSER_ARGS
                        launch_options["ignore_default_args"] = PLAYWRIGHT_IGNORE_ARGS
                        browser = await playwright.chromium.launch(**launch_options)

                    # Store browser in context
                    context.browser = browser

                    # Create initial tab automatically with context options
                    browser_context = await browser.new_context(**context_options)
                    context.add_browser_context(browser_context)  # Track for cleanup
                    page = await browser_context.new_page()

                # Inject anti-detection JavaScript
                # This runs before any page script to hide automation markers
                anti_detect_script = """
                // Override navigator.webdriver to hide automation
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });

                // Override navigator.plugins to look like a real browser
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', filename: 'internal-nacl-plugin'}
                    ],
                    configurable: true
                });

                // Override navigator.languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    configurable: true
                });

                // Remove automation-related properties from window
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

                // Override permissions query to hide automation
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({state: Notification.permission}) :
                        originalQuery(parameters)
                );
                """

                try:
                    # For persistent context, browser_context is the context
                    # For regular browser, browser_context is also available
                    await browser_context.add_init_script(anti_detect_script)
                    logger.debug("Anti-detection script injected")
                except Exception as script_err:
                    logger.warning(
                        f"Failed to inject anti-detection script: {script_err}"
                    )

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
                # Set outputs - for persistent context, browser_context acts as the browser
                self.set_output_value(
                    "browser", browser if browser else browser_context
                )
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

    def _validate_config(self) -> Tuple[bool, str]:
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

    def _validate_config(self) -> Tuple[bool, str]:
        """Validate node configuration."""
        return True, ""
