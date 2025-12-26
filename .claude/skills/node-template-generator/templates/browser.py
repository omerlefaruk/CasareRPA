"""
Browser Node Template

For nodes that use Playwright for web automation.
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
    PropertyDef("wait_for_selector", PropertyType.STRING, default=""),
)
@node(category="browser")
class BrowserNodeTemplate(BaseNode):
    """
    Template for browser automation nodes.

    Inputs:
        url (DataType.STRING): URL to navigate to
        timeout (DataType.INTEGER): Timeout in milliseconds

    Outputs:
        success (DataType.BOOLEAN): Whether operation succeeded
        title (DataType.STRING): Page title after navigation
    """

    def __init__(self):
        super().__init__(
            id="browser_template",
            name="Browser Template",
            category="browser",
        )
        # Exec ports for flow control
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data ports
        self.add_input_port("url", DataType.STRING)
        self.add_input_port("timeout", DataType.INTEGER)
        self.add_input_port("wait_for_selector", DataType.STRING)

        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("title", DataType.STRING)

    async def execute(self, context) -> dict:
        """
        Execute browser navigation.

        Args:
            context: Execution context with browser resource

        Returns:
            dict with success status and output data
        """
        try:
            # Get parameters (dual-source: port -> config fallback)
            url = self.get_parameter("url")
            timeout = self.get_parameter("timeout", 30000)
            wait_selector = self.get_parameter("wait_for_selector", "")

            # Get browser page from resource manager
            from casare_rpa.infrastructure.resources.browser_manager import BrowserResourceManager

            page = await BrowserResourceManager.get_page()

            logger.info(f"Navigating to {url}")

            # Navigate to URL
            await page.goto(url, timeout=timeout)

            # Wait for selector if provided
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)

            # Get page title
            title = await page.title()

            logger.info(f"Navigation successful, page title: {title}")

            self.set_output_value("success", True)
            self.set_output_value("title", title)

            return {"success": True, "next_nodes": ["exec_out"]}

        except Exception as exc:
            logger.error(f"Browser navigation failed: {exc}")
            self.set_output_value("success", False)
            self.set_output_value("title", "")
            return {"success": False, "error": str(exc), "next_nodes": ["exec_out"]}
