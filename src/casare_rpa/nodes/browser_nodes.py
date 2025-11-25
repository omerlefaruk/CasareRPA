"""
Browser control nodes for Playwright automation.

This module provides nodes for controlling browser lifecycle:
launching browsers, managing tabs, and cleanup.
"""

from typing import Any, Optional

from playwright.async_api import Browser, Page, BrowserContext

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from ..utils.config import DEFAULT_BROWSER, HEADLESS_MODE, BROWSER_ARGS
from loguru import logger


class LaunchBrowserNode(BaseNode):
    """
    Launch browser node - creates a new browser instance.
    
    Opens a browser (Chromium, Firefox, or WebKit) using Playwright
    and stores it in the execution context for use by other nodes.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Launch Browser",
        browser_type: str = DEFAULT_BROWSER,
        headless: bool = HEADLESS_MODE,
        **kwargs
    ) -> None:
        """
        Initialize launch browser node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            browser_type: Browser to launch (chromium, firefox, webkit)
            headless: Whether to run in headless mode
        """
        # Default config with all Playwright options
        default_config = {
            "browser_type": browser_type,
            "headless": headless,
            # Performance options
            "slow_mo": 0,  # Slow down operations by ms (for debugging)
            "channel": "",  # Browser channel (chrome, msedge, chrome-beta)
            # Viewport options
            "viewport_width": 1280,
            "viewport_height": 720,
            # Browser identity options
            "user_agent": "",  # Custom user agent string
            "locale": "",  # Locale (e.g., "en-US")
            "timezone_id": "",  # Timezone (e.g., "America/New_York")
            "color_scheme": "light",  # Preferred color scheme (light/dark/no-preference)
            # Security options
            "ignore_https_errors": False,
            "proxy_server": "",  # Proxy server URL
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LaunchBrowserNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("browser", PortType.OUTPUT, DataType.BROWSER)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute browser launch.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with browser instance
        """
        self.status = NodeStatus.RUNNING

        try:
            from playwright.async_api import async_playwright

            browser_type = self.config.get("browser_type", DEFAULT_BROWSER)
            headless = self.config.get("headless", HEADLESS_MODE)

            logger.info(f"Launching {browser_type} browser (headless={headless})")

            # Build launch options
            launch_options = {"headless": headless}

            # Add slow_mo if specified (for debugging)
            slow_mo = self.config.get("slow_mo", 0)
            if slow_mo and int(slow_mo) > 0:
                launch_options["slow_mo"] = int(slow_mo)

            # Add channel for chromium-based browsers
            channel = self.config.get("channel", "")
            if channel and browser_type == "chromium":
                launch_options["channel"] = channel

            # Launch playwright
            playwright = await async_playwright().start()

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
            viewport_width = int(self.config.get("viewport_width", 1280))
            viewport_height = int(self.config.get("viewport_height", 720))
            context_options["viewport"] = {"width": viewport_width, "height": viewport_height}

            # User agent
            user_agent = self.config.get("user_agent", "")
            if user_agent:
                context_options["user_agent"] = user_agent

            # Locale
            locale = self.config.get("locale", "")
            if locale:
                context_options["locale"] = locale

            # Timezone
            timezone_id = self.config.get("timezone_id", "")
            if timezone_id:
                context_options["timezone_id"] = timezone_id

            # Color scheme
            color_scheme = self.config.get("color_scheme", "light")
            if color_scheme and color_scheme != "light":
                context_options["color_scheme"] = color_scheme

            # HTTPS errors
            if self.config.get("ignore_https_errors", False):
                context_options["ignore_https_errors"] = True

            # Proxy
            proxy_server = self.config.get("proxy_server", "")
            if proxy_server:
                context_options["proxy"] = {"server": proxy_server}

            logger.debug(f"Browser context options: {context_options}")

            # Create initial tab automatically with context options
            browser_context = await browser.new_context(**context_options)
            context.add_browser_context(browser_context)  # Track for cleanup
            page = await browser_context.new_page()
            
            # Navigate to URL if provided
            # Check input port first, then config
            url = self.get_input_value("url")
            if url is None:
                # Only use config if no input connection exists
                url = self.config.get("url", "")
            
            # Strip whitespace and normalize to empty string if None or whitespace-only
            url = url.strip() if url else ""
            # Substitute variables in URL like {{var_name}} using execution context
            if isinstance(url, str) and "{{" in url and "}}" in url:
                import re

                def _replace(match: re.Match) -> str:
                    var_name = match.group(1).strip()
                    value = context.get_variable(var_name)
                    if value is None:
                        raise ValueError(f"Variable '{var_name}' not found in workflow context")
                    return str(value)

                url = re.sub(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}", _replace, url)
                logger.info(f"LaunchBrowserNode URL after substitution: '{url}'")

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
            
            # Set outputs
            self.set_output_value("browser", browser)
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Browser launched successfully: {browser_type} with initial tab")
            
            return {
                "success": True,
                "data": {
                    "browser": browser,
                    "page": page,
                    "browser_type": browser_type,
                    "headless": headless
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to launch browser: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        browser_type = self.config.get("browser_type", "")
        if browser_type not in ["chromium", "firefox", "webkit"]:
            return False, f"Invalid browser type: {browser_type}"
        return True, ""


class CloseBrowserNode(BaseNode):
    """
    Close browser node - closes the browser instance.
    
    Properly closes the browser and cleans up resources.
    """
    
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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
    
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
            
            logger.info("Closing browser")
            
            # Close browser
            await browser.close()
            
            # Clear from context
            context.browser = None
            context.clear_pages()
            
            self.status = NodeStatus.SUCCESS
            logger.info("Browser closed successfully")
            
            return {
                "success": True,
                "data": {"message": "Browser closed"},
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to close browser: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


class NewTabNode(BaseNode):
    """
    New tab node - creates a new browser tab/page.
    
    Opens a new tab in the browser and optionally sets it as active.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "New Tab",
        tab_name: str = "main",
        **kwargs
    ) -> None:
        """
        Initialize new tab node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            tab_name: Name to identify this tab
        """
        config = kwargs.get("config", {"tab_name": tab_name})
        if "tab_name" not in config:
            config["tab_name"] = tab_name
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "NewTabNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER, required=False)  # Optional: uses context browser if not connected
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
            
            tab_name = self.config.get("tab_name", "main")
            
            logger.info(f"Creating new tab: {tab_name}")
            
            # Create new context and page
            browser_context = await browser.new_context()
            context.add_browser_context(browser_context)  # Track for cleanup
            page = await browser_context.new_page()
            
            # Store page in context
            context.add_page(page, tab_name)
            context.set_active_page(page, tab_name)
            
            # Set output
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Tab created successfully: {tab_name}")
            
            return {
                "success": True,
                "data": {
                    "tab_name": tab_name,
                    "page": page
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to create tab: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        tab_name = self.config.get("tab_name", "")
        if not tab_name:
            return False, "Tab name cannot be empty"
        return True, ""

