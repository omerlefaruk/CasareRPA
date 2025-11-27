"""
Navigation nodes for web page navigation.

This module provides nodes for controlling page navigation:
going to URLs, back/forward navigation, and page refresh.
"""

import asyncio


from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from ..utils.config import DEFAULT_PAGE_LOAD_TIMEOUT
from loguru import logger


def safe_int(value, default: int) -> int:
    """Safely parse int values with defaults."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class GoToURLNode(BaseNode):
    """
    Go to URL node - navigates to a specified URL.

    Loads a web page at the given URL with optional timeout configuration.
    """

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
            url: URL to navigate to
            timeout: Page load timeout in milliseconds
        """
        # Default config with all Playwright options
        default_config = {
            "url": url,
            "timeout": timeout,
            "wait_until": "load",  # load, domcontentloaded, networkidle, commit
            "referer": "",  # Optional referer header
            "retry_count": 0,  # Number of retries on navigation failure
            "retry_interval": 1000,  # Delay between retries in ms
            "screenshot_on_fail": False,  # Take screenshot on failure
            "screenshot_path": "",  # Path for failure screenshot
            "ignore_https_errors": False,  # Ignore HTTPS certificate errors
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GoToURLNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port(
            "page", PortType.INPUT, DataType.PAGE, required=False
        )  # Optional: uses active page if not connected
        self.add_input_port(
            "url", PortType.INPUT, DataType.STRING, required=False
        )  # Optional: uses config value if not connected
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

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

            # Get URL from input or config
            url = self.get_input_value("url")
            logger.info(f"URL from input port: '{url}'")
            logger.info(f"Node config: {self.config}")

            if url is None:
                url = self.config.get("url", "")
                logger.info(f"URL from config: '{url}'")

            # Resolve {{variable}} patterns in url
            url = context.resolve_value(url)

            if not url:
                logger.error(
                    f"URL validation failed. url='{url}', config={self.config}"
                )
                raise ValueError("URL is required")

            # Add protocol if missing
            if not url.startswith(("http://", "https://", "file://")):
                url = f"https://{url}"

            timeout = self.config.get("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.config.get("wait_until", "load")
            referer = self.config.get("referer", "")

            # Get retry options
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")

            # Resolve {{variable}} patterns in referer and screenshot_path
            referer = context.resolve_value(referer)
            screenshot_path = context.resolve_value(screenshot_path)

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
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for URL: {url}"
                        )

                    # Navigate to URL
                    response = await page.goto(url, **goto_options)

                    # Set output
                    self.set_output_value("page", page)

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
        url = self.config.get("url", "")
        if not url:
            # URL can come from input port, so empty config is ok
            return True, ""

        # Basic URL validation
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "URL must start with http:// or https://"

        return True, ""


class GoBackNode(BaseNode):
    """
    Go back node - navigates back in browser history.
    """

    def __init__(self, node_id: str, name: str = "Go Back", **kwargs) -> None:
        """
        Initialize go back node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        # Default config with Playwright options
        default_config = {
            "timeout": DEFAULT_PAGE_LOAD_TIMEOUT,
            "wait_until": "load",  # load, domcontentloaded, networkidle, commit
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GoBackNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

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

            timeout = self.config.get("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.config.get("wait_until", "load")
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)

            logger.info(f"Navigating back (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for go back"
                        )

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


class GoForwardNode(BaseNode):
    """
    Go forward node - navigates forward in browser history.
    """

    def __init__(self, node_id: str, name: str = "Go Forward", **kwargs) -> None:
        """
        Initialize go forward node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        # Default config with Playwright options
        default_config = {
            "timeout": DEFAULT_PAGE_LOAD_TIMEOUT,
            "wait_until": "load",  # load, domcontentloaded, networkidle, commit
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GoForwardNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

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

            timeout = self.config.get("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.config.get("wait_until", "load")
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)

            logger.info(f"Navigating forward (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for go forward"
                        )

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


class RefreshPageNode(BaseNode):
    """
    Refresh page node - reloads the current page.
    """

    def __init__(self, node_id: str, name: str = "Refresh Page", **kwargs) -> None:
        """
        Initialize refresh page node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        # Default config with Playwright options
        default_config = {
            "timeout": DEFAULT_PAGE_LOAD_TIMEOUT,
            "wait_until": "load",  # load, domcontentloaded, networkidle, commit
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RefreshPageNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

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

            timeout = self.config.get("timeout", DEFAULT_PAGE_LOAD_TIMEOUT)
            wait_until = self.config.get("wait_until", "load")
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)

            logger.info(f"Refreshing page (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for page refresh"
                        )

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
