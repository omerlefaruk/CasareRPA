"""
Wait and timing nodes for synchronization.

This module provides nodes for waiting: fixed delays, element waits,
and navigation waits.
"""

import asyncio


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
from ..utils.config import DEFAULT_NODE_TIMEOUT
from ..utils.selectors.selector_normalizer import normalize_selector
from loguru import logger


@node_schema(
    PropertyDef(
        "duration",
        PropertyType.FLOAT,
        default=1.0,
        label="Duration (seconds)",
        tooltip="Wait duration in seconds",
    )
)
@executable_node
class WaitNode(BaseNode):
    """
    Wait node - pauses execution for a specified duration.

    Simple delay node for fixed-time waits.
    """

    def __init__(
        self, node_id: str, name: str = "Wait", duration: float = 1.0, **kwargs
    ) -> None:
        """
        Initialize wait node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            duration: Wait duration in seconds (ignored when config provided)

        Note:
            The @node_schema decorator automatically handles default_config.
            No manual config merging needed!
        """
        # Config automatically populated by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("duration", PortType.INPUT, DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute wait.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result after wait completes
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get duration from input or config
            duration = self.get_input_value("duration")
            if duration is None:
                duration = self.config.get("duration", 1.0)

            # Convert to float if it's a string
            if isinstance(duration, str):
                duration = float(duration)

            if duration < 0:
                raise ValueError("Duration must be non-negative")

            logger.info(f"Waiting for {duration} seconds")

            # Wait
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


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="CSS or XPath selector for the element",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        min_value=0,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
    ),
    PropertyDef(
        "state",
        PropertyType.CHOICE,
        default="visible",
        choices=["visible", "hidden", "attached", "detached"],
        label="State",
        tooltip="Element state to wait for",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict",
        tooltip="Require exactly one matching element",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries after timeout",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms",
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.STRING,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot",
    ),
    PropertyDef(
        "highlight_on_find",
        PropertyType.BOOLEAN,
        default=False,
        label="Highlight on Find",
        tooltip="Briefly highlight element when found",
    ),
)
@executable_node
class WaitForElementNode(BaseNode):
    """
    Wait for element node - waits for an element to appear.

    Waits until an element matching the selector is visible on the page.

    Config (via @node_schema):
        selector: CSS or XPath selector
        timeout: Timeout in milliseconds
        state: Element state to wait for
        strict: Require exactly one match
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot
        highlight_on_find: Highlight element when found
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Element",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitForElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)
        self.add_output_port("found", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute wait for element.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result when element appears
        """
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_parameter("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            selector = self.get_parameter("selector", "")
            if not selector:
                raise ValueError("Selector is required")

            selector = context.resolve_value(selector)
            normalized_selector = normalize_selector(selector)

            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            state = self.get_parameter("state", "visible")
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")
            highlight_on_find = self.get_parameter("highlight_on_find", False)
            strict = self.get_parameter("strict", False)

            # Resolve {{variable}} patterns in screenshot_path if provided
            if screenshot_path:
                screenshot_path = context.resolve_value(screenshot_path)

            logger.info(f"Waiting for element: {normalized_selector} (state={state})")

            # Build wait options
            wait_options = {
                "timeout": timeout,
                "state": state,
            }
            if strict:
                wait_options["strict"] = True

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1  # Initial attempt + retries

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for element: {selector}"
                        )

                    # Wait for element
                    element = await page.wait_for_selector(
                        normalized_selector, **wait_options
                    )

                    # Highlight element if requested
                    if highlight_on_find and element:
                        try:
                            await element.evaluate("""
                                el => {
                                    const original = el.style.outline;
                                    el.style.outline = '3px solid #00ff00';
                                    setTimeout(() => { el.style.outline = original; }, 500);
                                }
                            """)
                            await asyncio.sleep(0.5)  # Wait for highlight to show
                        except Exception:
                            pass  # Ignore highlight errors

                    self.set_output_value("page", page)
                    self.set_output_value("found", True)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Element appeared: {selector} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "selector": selector,
                            "state": state,
                            "attempts": attempts,
                            "found": True,
                        },
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Wait for element failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(
                            retry_interval / 1000
                        )  # Convert ms to seconds
                    else:
                        # Last attempt failed
                        break

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime

                    if screenshot_path:
                        path = screenshot_path
                    else:
                        # Generate default path
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"wait_element_fail_{timestamp}.png"

                    # Ensure directory exists
                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    await page.screenshot(path=path)
                    logger.info(f"Failure screenshot saved: {path}")
                except Exception as ss_error:
                    logger.warning(f"Failed to take screenshot: {ss_error}")

            # Element not found after all attempts
            self.set_output_value("page", page)
            self.set_output_value("found", False)
            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("found", False)
            logger.error(f"Failed to wait for element: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"found": False},
                "next_nodes": [],
            }

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        state = self.config.get("state", "visible")
        if state not in ["visible", "hidden", "attached", "detached"]:
            return False, f"Invalid state: {state}"
        return True, ""


@node_schema(
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        min_value=0,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        choices=["load", "domcontentloaded", "networkidle"],
        label="Wait Until",
        tooltip="Event to wait for",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries after timeout",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms",
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.STRING,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot",
    ),
)
@executable_node
class WaitForNavigationNode(BaseNode):
    """
    Wait for navigation node - waits for page navigation to complete.

    Waits for the page to navigate to a new URL or reload.

    Config (via @node_schema):
        timeout: Timeout in milliseconds
        wait_until: Event to wait for
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Navigation",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitForNavigationNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute wait for navigation.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result when navigation completes
        """
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_parameter("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            wait_until = self.get_parameter("wait_until", "load")
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            # Resolve {{variable}} patterns in screenshot_path if provided
            if screenshot_path:
                screenshot_path = context.resolve_value(screenshot_path)

            logger.info(f"Waiting for navigation (wait_until={wait_until})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1  # Initial attempt + retries

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for navigation"
                        )

                    # Wait for navigation
                    await page.wait_for_load_state(wait_until, timeout=timeout)

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Navigation completed (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "url": page.url,
                            "wait_until": wait_until,
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Wait for navigation failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(
                            retry_interval / 1000
                        )  # Convert ms to seconds
                    else:
                        # Last attempt failed
                        break

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime

                    if screenshot_path:
                        path = screenshot_path
                    else:
                        # Generate default path
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"wait_navigation_fail_{timestamp}.png"

                    # Ensure directory exists
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
            logger.error(f"Failed to wait for navigation: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        wait_until = self.config.get("wait_until", "load")
        if wait_until not in ["load", "domcontentloaded", "networkidle"]:
            return False, f"Invalid wait_until: {wait_until}"
        return True, ""
