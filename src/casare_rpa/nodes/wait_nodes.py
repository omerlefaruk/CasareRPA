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
from casare_rpa.nodes.utils.type_converters import safe_int
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
    # Basic options
    PropertyDef(
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="CSS or XPath selector for the element",
        tab="properties",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
        tab="properties",
    ),
    PropertyDef(
        "state",
        PropertyType.CHOICE,
        default="visible",
        choices=["visible", "hidden", "attached", "detached"],
        label="State",
        tooltip="Element state to wait for",
        tab="properties",
    ),
    # Advanced options
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict Mode",
        tooltip="Require exactly one matching element",
        tab="advanced",
    ),
    PropertyDef(
        "poll_interval",
        PropertyType.INTEGER,
        default=100,
        label="Poll Interval (ms)",
        tooltip="Polling interval in milliseconds",
        tab="advanced",
    ),
    PropertyDef(
        "highlight_on_find",
        PropertyType.BOOLEAN,
        default=False,
        label="Highlight on Find",
        tooltip="Briefly highlight element when found",
        tab="advanced",
    ),
    # Retry options
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries after timeout",
        tab="retry",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in milliseconds",
        tab="retry",
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Fail",
        tooltip="Take screenshot when wait fails",
        tab="retry",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.STRING,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot (auto-generated if empty)",
        tab="retry",
    ),
)
@executable_node
class WaitForElementNode(BaseNode):
    """
    Wait for element node - waits for an element to appear.

    Waits until an element matching the selector is visible on the page.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Element",
        **kwargs,
    ) -> None:
        """
        Initialize wait for element node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @node_schema decorator automatically handles default_config.
        """
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
            page = self.get_input_value("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            # Get selector from input or config
            selector = self.get_input_value("selector")
            if selector is None:
                selector = self.get_parameter("selector", "")

            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            # Get parameters
            timeout = safe_int(
                self.get_parameter("timeout"), DEFAULT_NODE_TIMEOUT * 1000
            )
            state = self.get_parameter("state", "visible")
            strict = self.get_parameter("strict", False)
            highlight_on_find = self.get_parameter("highlight_on_find", False)

            # Get retry options
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

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
    # Basic options
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
        tab="properties",
    ),
    PropertyDef(
        "wait_until",
        PropertyType.CHOICE,
        default="load",
        choices=["load", "domcontentloaded", "networkidle"],
        label="Wait Until",
        tooltip="Event to wait for before considering navigation complete",
        tab="properties",
    ),
    # Advanced options
    PropertyDef(
        "url_pattern",
        PropertyType.STRING,
        default="",
        label="URL Pattern",
        tooltip="Optional URL pattern to wait for (glob or regex)",
        tab="advanced",
    ),
    PropertyDef(
        "url_use_regex",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Regex",
        tooltip="Treat URL pattern as regex instead of glob",
        tab="advanced",
    ),
    # Retry options
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries after timeout",
        tab="retry",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in milliseconds",
        tab="retry",
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Fail",
        tooltip="Take screenshot when wait fails",
        tab="retry",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.STRING,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot (auto-generated if empty)",
        tab="retry",
    ),
)
@executable_node
class WaitForNavigationNode(BaseNode):
    """
    Wait for navigation node - waits for page navigation to complete.

    Waits for the page to navigate to a new URL or reload.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Navigation",
        **kwargs,
    ) -> None:
        """
        Initialize wait for navigation node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @node_schema decorator automatically handles default_config.
        """
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
            page = self.get_input_value("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            # Get parameters
            timeout = safe_int(
                self.get_parameter("timeout"), DEFAULT_NODE_TIMEOUT * 1000
            )
            wait_until = self.get_parameter("wait_until", "load")

            # Get retry options
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)
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
