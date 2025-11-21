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
        config = kwargs.get("config", {"browser_type": browser_type, "headless": headless})
        if "browser_type" not in config:
            config["browser_type"] = browser_type
        if "headless" not in config:
            config["headless"] = headless
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LaunchBrowserNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("browser", PortType.OUTPUT, DataType.BROWSER)
    
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
            
            # Launch playwright
            playwright = await async_playwright().start()
            
            # Get browser type
            if browser_type == "firefox":
                browser = await playwright.firefox.launch(headless=headless)
            elif browser_type == "webkit":
                browser = await playwright.webkit.launch(headless=headless)
            else:  # chromium (default)
                browser = await playwright.chromium.launch(
                    headless=headless,
                    args=BROWSER_ARGS
                )
            
            # Store browser in context
            context.browser = browser
            
            # Set output
            self.set_output_value("browser", browser)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Browser launched successfully: {browser_type}")
            
            return {
                "success": True,
                "data": {
                    "browser": browser,
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
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER)
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
            page = await browser_context.new_page()
            
            # Store page in context
            context.add_page(tab_name, page)
            context.set_active_page(tab_name)
            
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

