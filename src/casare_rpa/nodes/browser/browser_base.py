"""
Base class for browser automation nodes.

Provides shared functionality for all Playwright-based nodes:
- Page access from context (input port or active page)
- Selector normalization (XPath, CSS, ARIA)
- Retry logic with configurable attempts and intervals
- Screenshot capture on failure
- Consistent error handling and logging

Usage:
    from casare_rpa.nodes.browser.browser_base import BrowserBaseNode

    @node_schema(BROWSER_SELECTOR, BROWSER_TIMEOUT, ...)
    @executable_node
    class MyBrowserNode(BrowserBaseNode):
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)
            # ... node logic ...
"""

import asyncio
import os
from abc import ABC
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, TypeVar

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils.selectors.selector_normalizer import normalize_selector
from casare_rpa.config import DEFAULT_NODE_TIMEOUT


T = TypeVar("T")


class PlaywrightError(Exception):
    """Base exception for Playwright-related errors in browser nodes."""

    def __init__(
        self,
        message: str,
        selector: Optional[str] = None,
        timeout: Optional[int] = None,
        attempts: int = 1,
    ):
        super().__init__(message)
        self.selector = selector
        self.timeout = timeout
        self.attempts = attempts


class ElementNotFoundError(PlaywrightError):
    """Raised when element cannot be found within timeout."""

    pass


class PageNotAvailableError(PlaywrightError):
    """Raised when no page instance is available."""

    pass


async def get_page_from_context(
    node: "BrowserBaseNode",
    context: ExecutionContext,
    port_name: str = "page",
) -> Any:
    """
    Get page instance from input port or context.

    Standard pattern for all browser nodes to access the active page.

    Args:
        node: The browser node instance
        context: Execution context
        port_name: Name of the page input port (default: "page")

    Returns:
        Playwright Page instance

    Raises:
        PageNotAvailableError: If no page is available
    """
    page = node.get_input_value(port_name)
    if page is None:
        page = context.get_active_page()

    if page is None:
        raise PageNotAvailableError(
            "No page instance found. Launch browser and navigate first."
        )

    return page


async def take_failure_screenshot(
    page: Any,
    screenshot_path: str = "",
    prefix: str = "failure",
) -> Optional[str]:
    """
    Take a screenshot on failure for debugging.

    Args:
        page: Playwright Page instance
        screenshot_path: Custom path for screenshot (auto-generated if empty)
        prefix: Prefix for auto-generated filename

    Returns:
        Path where screenshot was saved, or None if failed
    """
    if not page:
        return None

    try:
        if screenshot_path:
            path = screenshot_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{prefix}_{timestamp}.png"

        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        await page.screenshot(path=path)
        logger.info(f"Failure screenshot saved: {path}")
        return path

    except Exception as e:
        logger.warning(f"Failed to take screenshot: {e}")
        return None


async def highlight_element(
    page: Any,
    selector: str,
    timeout: int = 5000,
    color: str = "#ff0000",
    duration: float = 0.3,
) -> None:
    """
    Briefly highlight an element before action (for debugging).

    Args:
        page: Playwright Page instance
        selector: Normalized selector for element
        timeout: Max time to wait for element
        color: Highlight outline color
        duration: How long to show highlight in seconds
    """
    try:
        element = await page.wait_for_selector(selector, timeout=timeout)
        if element:
            await element.evaluate(
                f"""
                el => {{
                    const original = el.style.outline;
                    el.style.outline = '3px solid {color}';
                    setTimeout(() => {{ el.style.outline = original; }}, {int(duration * 1000)});
                }}
                """
            )
            await asyncio.sleep(duration)
    except Exception:
        pass  # Ignore highlight errors


class BrowserBaseNode(BaseNode, ABC):
    """
    Abstract base class for browser automation nodes.

    Provides common functionality for Playwright-based operations:
    - Page retrieval from context
    - Selector normalization
    - Retry logic
    - Screenshot on failure
    - Standard input/output port patterns

    Subclasses should:
    1. Define ports in _define_ports()
    2. Implement execute() using helper methods
    3. Use @node_schema with property constants
    """

    def __init__(
        self, node_id: str, config: Optional[dict] = None, **kwargs: Any
    ) -> None:
        """
        Initialize browser base node.

        Args:
            node_id: Unique identifier for this node
            config: Node configuration (from @node_schema defaults + user config)
            **kwargs: Additional arguments (name, etc.)
        """
        super().__init__(node_id, config or {})
        self.name = kwargs.get("name", self.__class__.__name__)
        self.node_type = self.__class__.__name__

    # =========================================================================
    # Page Access
    # =========================================================================

    def get_page(self, context: ExecutionContext) -> Any:
        """
        Get page from input port or context (sync wrapper for common pattern).

        NOTE: For async contexts, prefer using get_page_async().

        Args:
            context: Execution context

        Returns:
            Playwright Page instance

        Raises:
            PageNotAvailableError: If no page is available
        """
        page = self.get_input_value("page")
        if page is None:
            page = context.get_active_page()

        if page is None:
            raise PageNotAvailableError(
                "No page instance found. Launch browser and navigate first."
            )

        return page

    async def get_page_async(self, context: ExecutionContext) -> Any:
        """
        Get page from input port or context (async version).

        Args:
            context: Execution context

        Returns:
            Playwright Page instance

        Raises:
            PageNotAvailableError: If no page is available
        """
        return await get_page_from_context(self, context)

    # =========================================================================
    # Selector Handling
    # =========================================================================

    def get_normalized_selector(
        self,
        context: ExecutionContext,
        param_name: str = "selector",
    ) -> str:
        """
        Get selector parameter, resolve variables, and normalize for Playwright.

        Args:
            context: Execution context (for variable resolution)
            param_name: Parameter name containing selector

        Returns:
            Normalized selector string ready for Playwright

        Raises:
            ValueError: If selector is required but empty
        """
        selector = self.get_parameter(param_name, "")
        if not selector:
            raise ValueError(f"{param_name} is required")

        selector = context.resolve_value(selector)
        return normalize_selector(selector)

    def get_optional_normalized_selector(
        self,
        context: ExecutionContext,
        param_name: str = "selector",
    ) -> Optional[str]:
        """
        Get optional selector parameter, resolve variables, and normalize.

        Unlike get_normalized_selector(), returns None if selector is empty.

        Args:
            context: Execution context
            param_name: Parameter name containing selector

        Returns:
            Normalized selector string, or None if empty
        """
        selector = self.get_parameter(param_name, "")
        if not selector or not selector.strip():
            return None

        selector = context.resolve_value(selector)
        return normalize_selector(selector)

    # =========================================================================
    # Retry Logic
    # =========================================================================

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "operation",
        retry_count: Optional[int] = None,
        retry_interval: Optional[int] = None,
    ) -> tuple[T, int]:
        """
        Execute an async operation with retry logic.

        Uses retry_count and retry_interval from node config if not provided.

        Args:
            operation: Async callable to execute
            operation_name: Name for logging
            retry_count: Override retry count (default: from config)
            retry_interval: Override retry interval in ms (default: from config)

        Returns:
            Tuple of (result, attempts) where attempts is 1-based count

        Raises:
            Last exception if all attempts fail
        """
        if retry_count is None:
            retry_count = self.get_parameter("retry_count", 0)
        if retry_interval is None:
            retry_interval = self.get_parameter("retry_interval", 1000)

        last_error: Optional[Exception] = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            attempts += 1
            try:
                if attempts > 1:
                    logger.info(
                        f"Retry attempt {attempts - 1}/{retry_count} for {operation_name}"
                    )

                result = await operation()
                return result, attempts

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    logger.warning(f"{operation_name} failed (attempt {attempts}): {e}")
                    await asyncio.sleep(retry_interval / 1000)

        if last_error:
            raise last_error
        raise RuntimeError(f"{operation_name} failed without exception")

    # =========================================================================
    # Screenshot on Failure
    # =========================================================================

    async def screenshot_on_failure(
        self,
        page: Any,
        prefix: str = "failure",
    ) -> Optional[str]:
        """
        Take screenshot if screenshot_on_fail is enabled.

        Uses screenshot_on_fail and screenshot_path from node config.

        Args:
            page: Playwright Page instance
            prefix: Prefix for auto-generated filename

        Returns:
            Screenshot path if taken, None otherwise
        """
        if not self.get_parameter("screenshot_on_fail", False):
            return None

        screenshot_path = self.get_parameter("screenshot_path", "")
        return await take_failure_screenshot(page, screenshot_path, prefix)

    # =========================================================================
    # Element Highlighting
    # =========================================================================

    async def highlight_if_enabled(
        self,
        page: Any,
        selector: str,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Highlight element if highlight_before_action is enabled.

        Uses highlight_before_action from node config.

        Args:
            page: Playwright Page instance
            selector: Normalized selector
            timeout: Override timeout (default: from config)
        """
        highlight_enabled = self.get_parameter("highlight_before_action", False)
        # Also check legacy name
        if not highlight_enabled:
            highlight_enabled = self.get_parameter("highlight_before_click", False)
        if not highlight_enabled:
            highlight_enabled = self.get_parameter("highlight_on_find", False)

        if not highlight_enabled:
            return

        if timeout is None:
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)

        await highlight_element(page, selector, timeout)

    # =========================================================================
    # Common Port Patterns
    # =========================================================================

    def add_page_input_port(self, required: bool = False) -> None:
        """Add standard page input port."""
        self.add_input_port("page", DataType.PAGE, required=required)

    def add_page_output_port(self) -> None:
        """Add standard page output port."""
        self.add_output_port("page", DataType.PAGE)

    def add_page_passthrough_ports(self, required: bool = False) -> None:
        """Add page input and output ports for passthrough pattern."""
        self.add_page_input_port(required=required)
        self.add_page_output_port()

    def add_selector_input_port(self) -> None:
        """Add standard selector input port."""
        self.add_input_port("selector", DataType.STRING, required=False)

    # =========================================================================
    # Result Building
    # =========================================================================

    def success_result(
        self,
        data: dict[str, Any],
        next_nodes: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Build standard success result.

        Args:
            data: Result data dictionary
            next_nodes: Execution ports to continue (default: ["exec_out"])

        Returns:
            ExecutionResult dictionary
        """
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": data,
            "next_nodes": next_nodes or ["exec_out"],
        }

    def error_result(
        self,
        error: str | Exception,
        data: Optional[dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Build standard error result.

        Args:
            error: Error message or exception
            data: Optional additional data

        Returns:
            ExecutionResult dictionary
        """
        self.status = NodeStatus.ERROR
        error_msg = str(error)
        logger.error(f"{self.__class__.__name__} failed: {error_msg}")

        result: dict[str, Any] = {
            "success": False,
            "error": error_msg,
            "next_nodes": [],
        }
        if data:
            result["data"] = data
        return result

    # =========================================================================
    # Default Implementations
    # =========================================================================

    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate node configuration.

        Override in subclass for custom validation.
        Default: always valid (schema handles validation).
        """
        return True, ""
