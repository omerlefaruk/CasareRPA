"""
Interaction nodes for element manipulation.

This module provides nodes for interacting with page elements:
clicking, typing, selecting, etc.
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
from casare_rpa.nodes.utils import retry_operation, safe_int
from ..utils.config import DEFAULT_NODE_TIMEOUT
from ..utils.selectors.selector_normalizer import normalize_selector
from loguru import logger


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
        "button",
        PropertyType.CHOICE,
        default="left",
        choices=["left", "right", "middle"],
        label="Button",
        tooltip="Mouse button to use for click",
        tab="properties",
    ),
    # Click behavior
    PropertyDef(
        "click_count",
        PropertyType.INTEGER,
        default=1,
        label="Click Count",
        tooltip="Number of clicks (2 for double-click)",
        tab="advanced",
    ),
    PropertyDef(
        "delay",
        PropertyType.INTEGER,
        default=0,
        label="Delay (ms)",
        tooltip="Delay between mousedown and mouseup in milliseconds",
        tab="advanced",
    ),
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force Click",
        tooltip="Bypass actionability checks",
        tab="advanced",
    ),
    # Position offset
    PropertyDef(
        "position_x",
        PropertyType.STRING,
        default="",
        label="Position X",
        tooltip="Click position X offset (leave empty for center)",
        tab="advanced",
    ),
    PropertyDef(
        "position_y",
        PropertyType.STRING,
        default="",
        label="Position Y",
        tooltip="Click position Y offset (leave empty for center)",
        tab="advanced",
    ),
    PropertyDef(
        "no_wait_after",
        PropertyType.BOOLEAN,
        default=False,
        label="No Wait After",
        tooltip="Skip waiting for navigations after click",
        tab="advanced",
    ),
    PropertyDef(
        "trial",
        PropertyType.BOOLEAN,
        default=False,
        label="Trial Mode",
        tooltip="Perform actionability checks without clicking",
        tab="advanced",
    ),
    PropertyDef(
        "highlight_before_click",
        PropertyType.BOOLEAN,
        default=False,
        label="Highlight Before Click",
        tooltip="Briefly highlight element before clicking",
        tab="advanced",
    ),
    # Retry options
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
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
        tooltip="Take screenshot when click fails",
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
class ClickElementNode(BaseNode):
    """
    Click element node - clicks on a page element.

    Finds an element by selector and performs a click action.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Click Element",
        **kwargs,
    ) -> None:
        """
        Initialize click element node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @node_schema decorator automatically handles default_config.
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClickElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute element click.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with success status
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

            # Safely parse timeout with default
            timeout = safe_int(
                self.get_parameter("timeout"), DEFAULT_NODE_TIMEOUT * 1000
            )

            logger.info(f"Clicking element: {normalized_selector}")

            # Build click options
            click_options = {"timeout": timeout}

            # Button type (left, right, middle)
            button = self.get_parameter("button", "left")
            if button and button != "left":
                click_options["button"] = button

            # Click count (for double-click)
            click_count = safe_int(self.get_parameter("click_count"), 1)
            if click_count > 1:
                click_options["click_count"] = click_count

            # Delay between mousedown and mouseup
            delay = safe_int(self.get_parameter("delay"), 0)
            if delay > 0:
                click_options["delay"] = delay

            # Force click (bypass actionability checks)
            if self.get_parameter("force", False):
                click_options["force"] = True

            # Position offset
            pos_x = self.get_parameter("position_x", "")
            pos_y = self.get_parameter("position_y", "")
            if pos_x and pos_y:
                try:
                    click_options["position"] = {"x": float(pos_x), "y": float(pos_y)}
                except (ValueError, TypeError):
                    pass  # Ignore invalid position values

            # No wait after (skip waiting for navigations)
            if self.get_parameter("no_wait_after", False):
                click_options["no_wait_after"] = True

            # Trial mode (actionability checks only)
            if self.get_parameter("trial", False):
                click_options["trial"] = True

            logger.debug(f"Click options: {click_options}")

            # Get retry options
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")
            highlight_before_click = self.get_parameter("highlight_before_click", False)

            async def perform_click():
                # Highlight element before clicking if requested
                if highlight_before_click:
                    try:
                        element = await page.wait_for_selector(
                            normalized_selector, timeout=timeout
                        )
                        if element:
                            await element.evaluate("""
                                el => {
                                    const original = el.style.outline;
                                    el.style.outline = '3px solid #ff0000';
                                    setTimeout(() => { el.style.outline = original; }, 300);
                                }
                            """)
                            await asyncio.sleep(0.3)
                    except Exception:
                        pass  # Ignore highlight errors

                # Click element
                await page.click(normalized_selector, **click_options)
                return True

            result = await retry_operation(
                perform_click,
                max_attempts=retry_count + 1,
                delay_seconds=retry_interval / 1000,
                operation_name=f"click {selector}",
            )

            if result.success:
                self.set_output_value("page", page)
                self.status = NodeStatus.SUCCESS
                logger.info(
                    f"Element clicked successfully: {selector} (attempt {result.attempts})"
                )
                return {
                    "success": True,
                    "data": {"selector": selector, "attempts": result.attempts},
                    "next_nodes": ["exec_out"],
                }

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime

                    if screenshot_path:
                        path = screenshot_path
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"click_fail_{timestamp}.png"

                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    await page.screenshot(path=path)
                    logger.info(f"Failure screenshot saved: {path}")
                except Exception as ss_error:
                    logger.warning(f"Failed to take screenshot: {ss_error}")

            raise result.last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to click element: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        selector = self.config.get("selector", "")
        if not selector:
            # Selector can come from input port
            return True, ""
        return True, ""


@node_schema(
    # Basic options
    PropertyDef(
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="CSS or XPath selector for the input element",
        tab="properties",
    ),
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        label="Text",
        tooltip="Text to type into the element",
        tab="properties",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        label="Timeout (ms)",
        tooltip="Element wait timeout in milliseconds",
        tab="properties",
    ),
    PropertyDef(
        "clear_first",
        PropertyType.BOOLEAN,
        default=True,
        label="Clear First",
        tooltip="Clear field before typing",
        tab="properties",
    ),
    # Advanced options
    PropertyDef(
        "delay",
        PropertyType.INTEGER,
        default=0,
        label="Delay (ms)",
        tooltip="Delay between keystrokes in milliseconds",
        tab="advanced",
    ),
    PropertyDef(
        "press_sequentially",
        PropertyType.BOOLEAN,
        default=False,
        label="Press Sequentially",
        tooltip="Type character-by-character (overrides delay)",
        tab="advanced",
    ),
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force",
        tooltip="Bypass actionability checks",
        tab="advanced",
    ),
    PropertyDef(
        "no_wait_after",
        PropertyType.BOOLEAN,
        default=False,
        label="No Wait After",
        tooltip="Skip waiting for navigations",
        tab="advanced",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict Mode",
        tooltip="Require exactly one matching element",
        tab="advanced",
    ),
    PropertyDef(
        "press_enter_after",
        PropertyType.BOOLEAN,
        default=False,
        label="Press Enter After",
        tooltip="Press Enter key after typing",
        tab="advanced",
    ),
    PropertyDef(
        "press_tab_after",
        PropertyType.BOOLEAN,
        default=False,
        label="Press Tab After",
        tooltip="Press Tab key after typing",
        tab="advanced",
    ),
    # Retry options
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
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
        tooltip="Take screenshot when typing fails",
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
class TypeTextNode(BaseNode):
    """
    Type text node - types text into an input field.

    Finds an input element and types the specified text.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Type Text",
        **kwargs,
    ) -> None:
        """
        Initialize type text node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @node_schema decorator automatically handles default_config.
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TypeTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute text typing.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with success status
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

            # Get text from input or config
            text = self.get_input_value("text")
            if text is None:
                text = self.get_parameter("text", "")

            if text is None:
                text = ""

            # Resolve {{variable}} patterns in text
            text = context.resolve_value(text)

            # Get parameters
            delay = safe_int(self.get_parameter("delay"), 0)
            timeout = safe_int(
                self.get_parameter("timeout"), DEFAULT_NODE_TIMEOUT * 1000
            )
            clear_first = self.get_parameter("clear_first", True)
            press_sequentially = self.get_parameter("press_sequentially", False)
            force = self.get_parameter("force", False)
            no_wait_after = self.get_parameter("no_wait_after", False)
            strict = self.get_parameter("strict", False)
            press_enter_after = self.get_parameter("press_enter_after", False)
            press_tab_after = self.get_parameter("press_tab_after", False)

            # Get retry options
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            logger.info(f"Typing text into element: {normalized_selector}")

            # Build fill/type options
            fill_options = {"timeout": timeout}
            if force:
                fill_options["force"] = True
            if no_wait_after:
                fill_options["no_wait_after"] = True
            if strict:
                fill_options["strict"] = True

            async def perform_type():
                # Type text - use fill() for immediate input, type() for character-by-character with delay
                if delay > 0 or press_sequentially:
                    # Clear the field first if configured, then type with delay
                    if clear_first:
                        await page.fill(normalized_selector, "", **fill_options)
                    type_delay = delay if delay > 0 else 50
                    await page.type(
                        normalized_selector, text, delay=type_delay, timeout=timeout
                    )
                else:
                    # Use fill() for immediate input (faster)
                    await page.fill(normalized_selector, text, **fill_options)

                # Press Enter after if requested
                if press_enter_after:
                    await page.keyboard.press("Enter")

                # Press Tab after if requested
                if press_tab_after:
                    await page.keyboard.press("Tab")

                return True

            result = await retry_operation(
                perform_type,
                max_attempts=retry_count + 1,
                delay_seconds=retry_interval / 1000,
                operation_name=f"type text into {selector}",
            )

            if result.success:
                self.set_output_value("page", page)
                self.status = NodeStatus.SUCCESS
                logger.info(
                    f"Text typed successfully: {selector} (attempt {result.attempts})"
                )
                return {
                    "success": True,
                    "data": {
                        "selector": selector,
                        "text_length": len(text),
                        "attempts": result.attempts,
                    },
                    "next_nodes": ["exec_out"],
                }

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime

                    if screenshot_path:
                        path = screenshot_path
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"type_text_fail_{timestamp}.png"

                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    await page.screenshot(path=path)
                    logger.info(f"Failure screenshot saved: {path}")
                except Exception as ss_error:
                    logger.warning(f"Failed to take screenshot: {ss_error}")

            raise result.last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to type text: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


@node_schema(
    # Basic options
    PropertyDef(
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="CSS or XPath selector for the select element",
        tab="properties",
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        label="Value",
        tooltip="Value, label, or index to select",
        tab="properties",
    ),
    PropertyDef(
        "select_by",
        PropertyType.CHOICE,
        default="value",
        choices=["value", "label", "index"],
        label="Select By",
        tooltip="How to match the option",
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
    # Advanced options
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force",
        tooltip="Bypass actionability checks",
        tab="advanced",
    ),
    PropertyDef(
        "no_wait_after",
        PropertyType.BOOLEAN,
        default=False,
        label="No Wait After",
        tooltip="Skip waiting for navigations after selection",
        tab="advanced",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict Mode",
        tooltip="Require exactly one matching element",
        tab="advanced",
    ),
    # Retry options
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
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
        tooltip="Take screenshot when selection fails",
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
class SelectDropdownNode(BaseNode):
    """
    Select dropdown node - selects an option from a dropdown.

    Finds a select element and chooses an option by value, label, or index.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Select Dropdown",
        **kwargs,
    ) -> None:
        """
        Initialize select dropdown node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node

        Note:
            The @node_schema decorator automatically handles default_config.
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SelectDropdownNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_input_port("value", PortType.INPUT, DataType.STRING)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute dropdown selection.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with success status
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

            # Get value from input or config
            value = self.get_input_value("value")
            if value is None:
                value = self.get_parameter("value", "")

            if not value:
                raise ValueError("Value is required")

            # Resolve {{variable}} patterns in value
            value = context.resolve_value(value)

            # Get parameters
            timeout = safe_int(
                self.get_parameter("timeout"), DEFAULT_NODE_TIMEOUT * 1000
            )
            select_by = self.get_parameter("select_by", "value")

            # Get retry options
            retry_count = safe_int(self.get_parameter("retry_count"), 0)
            retry_interval = safe_int(self.get_parameter("retry_interval"), 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            logger.info(
                f"Selecting dropdown option: {normalized_selector} = {value} (by={select_by})"
            )

            # Build select options
            select_options = {"timeout": timeout}

            # Force option (bypass actionability checks)
            if self.get_parameter("force", False):
                select_options["force"] = True

            # No wait after (skip waiting for navigations)
            if self.get_parameter("no_wait_after", False):
                select_options["no_wait_after"] = True

            # Strict mode (require exactly one element)
            if self.get_parameter("strict", False):
                select_options["strict"] = True

            logger.debug(f"Select options: {select_options}")

            async def perform_select():
                # Select option based on select_by mode
                if select_by == "index":
                    await page.select_option(
                        normalized_selector, index=int(value), **select_options
                    )
                elif select_by == "label":
                    await page.select_option(
                        normalized_selector, label=value, **select_options
                    )
                else:  # value (default)
                    await page.select_option(
                        normalized_selector, value=value, **select_options
                    )
                return True

            result = await retry_operation(
                perform_select,
                max_attempts=retry_count + 1,
                delay_seconds=retry_interval / 1000,
                operation_name=f"select dropdown {selector}",
            )

            if result.success:
                self.set_output_value("page", page)
                self.status = NodeStatus.SUCCESS
                logger.info(
                    f"Dropdown selected successfully: {selector} (attempt {result.attempts})"
                )
                return {
                    "success": True,
                    "data": {
                        "selector": selector,
                        "value": value,
                        "select_by": select_by,
                        "attempts": result.attempts,
                    },
                    "next_nodes": ["exec_out"],
                }

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime

                    if screenshot_path:
                        path = screenshot_path
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"select_dropdown_fail_{timestamp}.png"

                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    await page.screenshot(path=path)
                    logger.info(f"Failure screenshot saved: {path}")
                except Exception as ss_error:
                    logger.warning(f"Failed to take screenshot: {ss_error}")

            raise result.last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to select dropdown: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""
