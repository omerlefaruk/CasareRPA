"""
Wait and timing nodes for synchronization.

This module provides nodes for waiting: fixed delays, element waits,
and navigation waits.

Browser-related wait nodes extend BrowserBaseNode for consistent patterns:
- Page access from context
- Selector normalization
- Retry logic
- Screenshot on failure
"""

import asyncio

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_ANCHOR_CONFIG,
    BROWSER_ELEMENT_STATE,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_SELECTOR_STRICT,
    BROWSER_TIMEOUT,
    BROWSER_WAIT_UNTIL,
)
from casare_rpa.config import DEFAULT_NODE_TIMEOUT
from casare_rpa.utils import safe_int


# =============================================================================
# WaitNode - Simple time-based wait (not browser-specific)
# =============================================================================


@properties(
    PropertyDef(
        "duration",
        PropertyType.FLOAT,
        default=1.0,
        label="Duration (seconds)",
        tooltip="Wait duration in seconds",
    )
)
@node(category="browser")
class WaitNode(BaseNode):
    """
    Wait node - pauses execution for a specified duration.

    Simple delay node for fixed-time waits.
    Does NOT extend BrowserBaseNode as it doesn't require a page.
    """

    # @category: browser
    # @requires: none
    # @ports: duration -> none

    def __init__(
        self, node_id: str, name: str = "Wait", duration: float = 1.0, **kwargs
    ) -> None:
        """Initialize wait node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("duration", DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute wait."""
        self.status = NodeStatus.RUNNING

        try:
            duration = self.get_input_value("duration")
            if duration is None:
                duration = self.config.get("duration", 1.0)

            if isinstance(duration, str):
                duration = float(duration)

            if duration < 0:
                raise ValueError("Duration must be non-negative")

            logger.info(f"Waiting for {duration} seconds")
            await asyncio.sleep(duration)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Wait completed: {duration} seconds")

            return {
                "success": True,
                "data": {"duration": duration},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to wait: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        duration = self.config.get("duration", 0)
        if duration < 0:
            return False, "Duration must be non-negative"
        return True, ""


# =============================================================================
# WaitForElementNode - Browser element wait
# =============================================================================


@properties(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Element Selector",
        tooltip="CSS or XPath selector for the element",
        placeholder="#element-id or //div[@class='content']",
    ),
    BROWSER_TIMEOUT,
    BROWSER_ELEMENT_STATE,
    BROWSER_SELECTOR_STRICT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    PropertyDef(
        "highlight_on_find",
        PropertyType.BOOLEAN,
        default=False,
        label="Highlight on Find",
        tooltip="Briefly highlight element when found",
    ),
    BROWSER_ANCHOR_CONFIG,
)
@node(category="browser")
class WaitForElementNode(BrowserBaseNode):
    """
    Wait for element node - waits for an element to appear.

    Waits until an element matching the selector is in the specified state.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

    Config (via @properties):
        selector: CSS or XPath selector
        timeout: Timeout in milliseconds
        state: Element state to wait for (visible, hidden, attached, detached)
        strict: Require exactly one match
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot
        highlight_on_find: Highlight element when found

    Inputs:
        page: Browser page instance
        selector: Element selector override

    Outputs:
        page: Browser page instance (passthrough)
        found: Whether element was found (BOOLEAN)
    """

    # @category: browser
    # @requires: none
    # @ports: none -> found

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Element",
        **kwargs,
    ) -> None:
        """Initialize wait for element node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "WaitForElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_selector_input_port()
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute wait for element."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get wait-specific parameters
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            state = self.get_parameter("state", "visible")
            strict = self.get_parameter("strict", False)
            retry_count = safe_int(self.get_parameter("retry_count", 0), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval", 1000), 1000)

            logger.info(f"Waiting for element: {selector} (state={state})")

            # Build wait options
            wait_options = {"timeout": timeout, "state": state}
            if strict:
                wait_options["strict"] = True

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                attempts += 1
                try:
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for element: {selector}"
                        )

                    element = await page.wait_for_selector(selector, **wait_options)

                    # Highlight if enabled
                    await self.highlight_if_enabled(page, selector, timeout)

                    self.set_output_value("page", page)
                    self.set_output_value("found", True)

                    return self.success_result(
                        {
                            "selector": selector,
                            "state": state,
                            "attempts": attempts,
                            "found": True,
                        }
                    )

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Wait for element failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)

            # All attempts failed
            await self.screenshot_on_failure(page, "wait_element_fail")

            self.set_output_value("page", page)
            self.set_output_value("found", False)

            if last_error:
                raise last_error
            raise RuntimeError(f"Element not found: {selector}")

        except Exception as e:
            self.set_output_value("found", False)
            return self.error_result(e, {"found": False})

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        state = self.config.get("state", "visible")
        valid_states = ["visible", "hidden", "attached", "detached"]
        if state not in valid_states:
            return False, f"Invalid state: {state}. Must be one of: {valid_states}"
        return True, ""


# =============================================================================
# WaitForNavigationNode - Browser navigation wait
# =============================================================================


@properties(
    BROWSER_TIMEOUT,
    BROWSER_WAIT_UNTIL,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
@node(category="browser")
class WaitForNavigationNode(BrowserBaseNode):
    """
    Wait for navigation node - waits for page navigation to complete.

    Waits for the page to navigate to a new URL or reload.
    Extends BrowserBaseNode for shared page/retry patterns.

    Config (via @properties):
        timeout: Timeout in milliseconds
        wait_until: Event to wait for (load, domcontentloaded, networkidle, commit)
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot

    Inputs:
        page: Browser page instance

    Outputs:
        page: Browser page instance (passthrough)
    """

    # @category: browser
    # @requires: none
    # @ports: via base class helpers

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Navigation",
        **kwargs,
    ) -> None:
        """Initialize wait for navigation node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "WaitForNavigationNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute wait for navigation."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get navigation-specific parameters
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            wait_until = self.get_parameter("wait_until", "load")
            retry_count = safe_int(self.get_parameter("retry_count", 0), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval", 1000), 1000)

            logger.info(f"Waiting for navigation (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                attempts += 1
                try:
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for navigation"
                        )

                    await page.wait_for_load_state(wait_until, timeout=timeout)

                    self.set_output_value("page", page)

                    return self.success_result(
                        {
                            "url": page.url,
                            "wait_until": wait_until,
                            "attempts": attempts,
                        }
                    )

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Wait for navigation failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)

            # All attempts failed
            await self.screenshot_on_failure(page, "wait_navigation_fail")

            if last_error:
                raise last_error
            raise RuntimeError("Navigation wait failed")

        except Exception as e:
            return self.error_result(e)

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        wait_until = self.config.get("wait_until", "load")
        valid_states = ["load", "domcontentloaded", "networkidle", "commit"]
        if wait_until not in valid_states:
            return (
                False,
                f"Invalid wait_until: {wait_until}. Must be one of: {valid_states}",
            )
        return True, ""
