"""
Browser tab management nodes.

Handles creating and improved tab switching logic.
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

    def _validate_config(self) -> Tuple[bool, str]:
        """Validate node configuration."""
        tab_name = self.get_parameter("tab_name", "")
        if not tab_name:
            return False, "Tab name cannot be empty"
        return True, ""
