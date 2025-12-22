"""
Navigation nodes for web page navigation.

This module provides nodes for controlling page navigation:
going to URLs, back/forward navigation, and page refresh.

All navigation nodes extend BrowserBaseNode for:
- Consistent page access via get_page()
- Screenshot on failure support
- Healing chain integration
"""

import asyncio

from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from loguru import logger

from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils import safe_int
from casare_rpa.config import DEFAULT_PAGE_LOAD_TIMEOUT


@properties(
    PropertyDef(
        "url",
        PropertyType.STRING,
        default="",
        label="URL",
        placeholder="https://example.com",
        tooltip="URL to navigate to",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_PAGE_LOAD_TIMEOUT,
        label="Timeout (ms)",
        tooltip="Page load timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        label="Wait Until",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        tooltip="Navigation event to wait for",
    ),
    PropertyDef(
        "referer",
        PropertyType.STRING,
        default="",
        label="Referer",
        placeholder="Optional referer header",
        tooltip="Optional HTTP referer header",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on navigation failure",
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
        label="Screenshot on Fail",
        tooltip="Take screenshot on navigation failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.FILE_PATH,
        default="",
        label="Screenshot Path",
        placeholder="Optional path for failure screenshot",
        tooltip="Path to save failure screenshot",
    ),
    PropertyDef(
        "ignore_https_errors",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore HTTPS Errors",
        tooltip="Ignore HTTPS certificate errors",
    ),
)
@node(category="browser")
class GoToURLNode(BrowserBaseNode):
    """
    Go to URL node - navigates to a specified URL.

    Loads a web page at the given URL with optional timeout configuration.
    Extends BrowserBaseNode for consistent page access and error handling.
    """

    # @category: browser
    # @requires: none
    # @ports: page, url -> page

    def __init__(
        self,
        node_id: str,
        name: str = "Go To URL",
        url: str = "",
        timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT,
        **kwargs,
    ) -> None:
        """
        Initialize go to URL node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            url: URL to navigate to (ignored when config provided)
            timeout: Page load timeout in milliseconds (ignored when config provided)

        Note:
            The @properties decorator automatically handles default_config.
            No manual config merging needed!
        """
        # Config automatically populated by @properties decorator
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "GoToURLNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Note: Port signature is (name, data_type, label=None, required=True)
        self.add_input_port(
            "page", DataType.PAGE, required=False
        )  # Optional: uses active page if not connected
        self.add_input_port(
            "url", DataType.STRING, required=False
        )  # Optional: uses config value if not connected
        self.add_output_port("page", DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute navigation to URL.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with page instance
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get page from input or context
            page = self.get_input_value("page")
            logger.info(
                f"Page from input: {page} (type: {type(page).__name__ if page else 'None'})"
            )

            if page is None:
                page = context.get_active_page()
                logger.info(
                    f"Page from context: {page} (type: {type(page).__name__ if page else 'None'})"
                )

            if page is None:
                raise ValueError("No page instance found")

            # Get URL using unified parameter accessor
            url = self.get_parameter("url")
            logger.info(f"URL from parameter: '{url}'")

            # Resolve {{variable}} patterns in url

            if not url:
                logger.error(f"URL validation failed. url='{url}', config={self.config}")
                raise ValueError("URL is required")

            # Add protocol if missing
            if not url.startswith(("http://", "https://", "file://")):
                url = f"https://{url}"

            timeout = self.get_parameter("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.get_parameter("wait_until", "load")
            referer = self.get_parameter("referer", "")

            # Get retry options
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            # Resolve {{variable}} patterns in referer and screenshot_path

            logger.info(f"Navigating to URL: {url} (wait_until={wait_until})")

            # Build navigation options
            goto_options = {"timeout": timeout, "wait_until": wait_until}
            if referer:
                goto_options["referer"] = referer

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for URL: {url}")

                    # Navigate to URL
                    response = await page.goto(url, **goto_options)

                    # Set output
                    self.set_output_value("page", page)

                    # Emit BROWSER_PAGE_READY event for UI to enable picker/recorder
                    # This is needed when browser was already open and user runs Navigate
                    try:
                        from casare_rpa.domain.events import (
                            get_event_bus,
                            BrowserPageReady,
                        )

                        event_bus = get_event_bus()
                        event_bus.publish(
                            BrowserPageReady(
                                page=page,
                                node_id=getattr(self, "node_id", None),
                            )
                        )
                        logger.debug("BrowserPageReady event published from GoToURLNode")
                    except Exception as e:
                        logger.debug(f"Could not emit BrowserPageReady event: {e}")

                    self.status = NodeStatus.SUCCESS
                    logger.info(
                        f"Navigation completed: {url} (status: {response.status if response else 'N/A'}, attempt {attempts})"
                    )

                    return {
                        "success": True,
                        "data": {
                            "url": url,
                            "status": response.status if response else None,
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Navigation failed (attempt {attempts}): {e}")
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
                        path = f"navigation_fail_{timestamp}.png"

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
            logger.error(f"Failed to navigate to URL: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        # URL can come from input port, so empty config is ok
        # Protocol is auto-added in execute() if missing
        return True, ""


@properties(
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_PAGE_LOAD_TIMEOUT,
        label="Timeout (ms)",
        tooltip="Page load timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        label="Wait Until",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        tooltip="Navigation event to wait for",
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
@node(category="browser")
class GoBackNode(BrowserBaseNode):
    """
    Go back node - navigates back in browser history.

    Extends BrowserBaseNode for consistent page access and error handling.
    """

    # @category: browser
    # @requires: none
    # @ports: page -> page

    def __init__(self, node_id: str, name: str = "Go Back", **kwargs) -> None:
        """
        Initialize go back node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @properties decorator automatically handles default_config.
            No manual config merging needed!
        """
        # Config automatically populated by @properties decorator
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "GoBackNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", DataType.PAGE, required=False)
        self.add_output_port("page", DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute back navigation.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with page instance
        """
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_input_value("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            timeout = self.get_parameter("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.get_parameter("wait_until", "load")
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)

            logger.info(f"Navigating back (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for go back")

                    await page.go_back(timeout=timeout, wait_until=wait_until)

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Back navigation completed (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"url": page.url, "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Go back failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to go back: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


@properties(
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_PAGE_LOAD_TIMEOUT,
        label="Timeout (ms)",
        tooltip="Page load timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        label="Wait Until",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        tooltip="Navigation event to wait for",
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
@node(category="browser")
class GoForwardNode(BrowserBaseNode):
    """
    Go forward node - navigates forward in browser history.

    Extends BrowserBaseNode for consistent page access and error handling.
    """

    # @category: browser
    # @requires: none
    # @ports: page -> page

    def __init__(self, node_id: str, name: str = "Go Forward", **kwargs) -> None:
        """
        Initialize go forward node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @properties decorator automatically handles default_config.
            No manual config merging needed!
        """
        # Config automatically populated by @properties decorator
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "GoForwardNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", DataType.PAGE, required=False)
        self.add_output_port("page", DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute forward navigation.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with page instance
        """
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_input_value("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            timeout = self.get_parameter("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.get_parameter("wait_until", "load")
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)

            logger.info(f"Navigating forward (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for go forward")

                    await page.go_forward(timeout=timeout, wait_until=wait_until)

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Forward navigation completed (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"url": page.url, "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Go forward failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to go forward: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


@properties(
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_PAGE_LOAD_TIMEOUT,
        label="Timeout (ms)",
        tooltip="Page load timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        label="Wait Until",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        tooltip="Navigation event to wait for",
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
@node(category="browser")
class RefreshPageNode(BrowserBaseNode):
    """
    Refresh page node - reloads the current page.

    Extends BrowserBaseNode for consistent page access and error handling.
    """

    # @category: browser
    # @requires: none
    # @ports: page -> page

    def __init__(self, node_id: str, name: str = "Refresh Page", **kwargs) -> None:
        """
        Initialize refresh page node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @properties decorator automatically handles default_config.
            No manual config merging needed!
        """
        # Config automatically populated by @properties decorator
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "RefreshPageNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", DataType.PAGE, required=False)
        self.add_output_port("page", DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute page refresh.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with page instance
        """
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_input_value("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            timeout = self.get_parameter("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.get_parameter("wait_until", "load")
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)

            logger.info(f"Refreshing page (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for page refresh")

                    await page.reload(timeout=timeout, wait_until=wait_until)

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Page refreshed successfully (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"url": page.url, "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Refresh failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to refresh page: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""
