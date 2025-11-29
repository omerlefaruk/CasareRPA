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
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,  # Can come from input port
        label="Element Selector",
        tooltip="CSS or XPath selector for the element to click",
        placeholder="#button-id or //button[@name='submit']",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        label="Timeout (ms)",
        tooltip="Maximum time to wait for element in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "button",
        PropertyType.CHOICE,
        default="left",
        choices=["left", "right", "middle"],
        label="Mouse Button",
        tooltip="Which mouse button to click",
    ),
    PropertyDef(
        "click_count",
        PropertyType.INTEGER,
        default=1,
        label="Click Count",
        tooltip="Number of clicks (2 for double-click)",
        min_value=1,
    ),
    PropertyDef(
        "delay",
        PropertyType.INTEGER,
        default=0,
        label="Delay (ms)",
        tooltip="Delay between mousedown and mouseup in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force Click",
        tooltip="Bypass actionability checks",
    ),
    PropertyDef(
        "position_x",
        PropertyType.FLOAT,
        default=None,
        label="Position X",
        tooltip="Click position X offset (optional)",
    ),
    PropertyDef(
        "position_y",
        PropertyType.FLOAT,
        default=None,
        label="Position Y",
        tooltip="Click position Y offset (optional)",
    ),
    PropertyDef(
        "modifiers",
        PropertyType.MULTI_CHOICE,
        default=[],
        choices=["Alt", "Control", "Meta", "Shift"],
        label="Modifier Keys",
        tooltip="Modifier keys to hold during click",
    ),
    PropertyDef(
        "no_wait_after",
        PropertyType.BOOLEAN,
        default=False,
        label="No Wait After",
        tooltip="Skip waiting for navigations after click",
    ),
    PropertyDef(
        "trial",
        PropertyType.BOOLEAN,
        default=False,
        label="Trial Mode",
        tooltip="Perform actionability checks without clicking",
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
        label="Screenshot On Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.FILE_PATH,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot (auto-generated if empty)",
    ),
    PropertyDef(
        "highlight_before_click",
        PropertyType.BOOLEAN,
        default=False,
        label="Highlight Element",
        tooltip="Highlight element before clicking",
    ),
)
@executable_node
class ClickElementNode(BaseNode):
    """
    Click element node - clicks on a page element.

    Finds an element by selector and performs a click action.

    Config (via @node_schema):
        selector: CSS or XPath selector
        timeout: Timeout in milliseconds (default: 30000)
        button: Mouse button (left, right, middle)
        click_count: Number of clicks (2 for double-click)
        delay: Delay between mousedown/mouseup in ms
        force: Bypass actionability checks
        position_x/position_y: Click position offsets
        modifiers: Modifier keys (Alt, Control, Meta, Shift)
        no_wait_after: Skip waiting for navigations
        trial: Actionability checks only
        retry_count: Number of retries on failure
        retry_interval: Delay between retries in ms
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for failure screenshot
        highlight_before_click: Highlight element before clicking

    Inputs:
        page: Browser page instance
        selector: Element selector override

    Outputs:
        page: Browser page instance (passthrough)
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Click Element",
        selector: str = "",
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
        **kwargs,
    ) -> None:
        """
        Initialize click element node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector (ignored when config provided)
            timeout: Timeout in milliseconds (ignored when config provided)

        Note:
            The @node_schema decorator automatically handles default_config.
        """
        # Config auto-merged by @node_schema decorator
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

            # NEW: Unified parameter accessor
            selector = self.get_parameter("selector")
            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            # Get all parameters using unified accessor
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            button = self.get_parameter("button", "left")
            click_count = self.get_parameter("click_count", 1)
            delay = self.get_parameter("delay", 0)
            force = self.get_parameter("force", False)
            position_x = self.get_parameter("position_x")
            position_y = self.get_parameter("position_y")
            modifiers = self.get_parameter("modifiers", [])
            no_wait_after = self.get_parameter("no_wait_after", False)
            trial = self.get_parameter("trial", False)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")
            highlight_before_click = self.get_parameter("highlight_before_click", False)

            # Type conversions
            timeout = safe_int(timeout, DEFAULT_NODE_TIMEOUT * 1000)
            click_count = safe_int(click_count, 1)
            delay = safe_int(delay, 0)
            retry_count = safe_int(retry_count, 0)
            retry_interval = safe_int(retry_interval, 1000)

            logger.info(f"Clicking element: {normalized_selector}")

            # Build click options
            click_options = {"timeout": timeout}

            if button and button != "left":
                click_options["button"] = button

            if click_count > 1:
                click_options["click_count"] = click_count

            if delay > 0:
                click_options["delay"] = delay

            if force:
                click_options["force"] = True

            if position_x is not None and position_y is not None:
                try:
                    click_options["position"] = {
                        "x": float(position_x),
                        "y": float(position_y),
                    }
                except (ValueError, TypeError):
                    pass

            if modifiers:
                click_options["modifiers"] = modifiers

            if no_wait_after:
                click_options["no_wait_after"] = True

            if trial:
                click_options["trial"] = True

            logger.debug(f"Click options: {click_options}")

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
                        pass

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
        # Schema handles validation via @node_schema decorator
        return True, ""


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,  # Can come from input port
        label="Input Selector",
        tooltip="CSS or XPath selector for the input element",
        placeholder="#email or //input[@name='username']",
    ),
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        required=False,  # Can come from input port
        label="Text",
        tooltip="Text to type into the input field",
        placeholder="Text to enter...",
    ),
    PropertyDef(
        "delay",
        PropertyType.INTEGER,
        default=0,
        label="Keystroke Delay (ms)",
        tooltip="Delay between keystrokes in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        label="Timeout (ms)",
        tooltip="Element wait timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "clear_first",
        PropertyType.BOOLEAN,
        default=True,
        label="Clear First",
        tooltip="Clear field before typing",
    ),
    PropertyDef(
        "press_sequentially",
        PropertyType.BOOLEAN,
        default=False,
        label="Press Sequentially",
        tooltip="Use type() for character-by-character (overrides delay)",
    ),
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force",
        tooltip="Bypass actionability checks",
    ),
    PropertyDef(
        "no_wait_after",
        PropertyType.BOOLEAN,
        default=False,
        label="No Wait After",
        tooltip="Skip waiting for navigations",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict",
        tooltip="Require exactly one matching element",
    ),
    PropertyDef(
        "press_enter_after",
        PropertyType.BOOLEAN,
        default=False,
        label="Press Enter After",
        tooltip="Press Enter key after typing",
    ),
    PropertyDef(
        "press_tab_after",
        PropertyType.BOOLEAN,
        default=False,
        label="Press Tab After",
        tooltip="Press Tab key after typing",
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
        label="Screenshot On Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.FILE_PATH,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot (auto-generated if empty)",
    ),
)
@executable_node
class TypeTextNode(BaseNode):
    """
    Type text node - types text into an input field.

    Finds an input element and types the specified text.

    Config (via @node_schema):
        selector: CSS or XPath selector
        text: Text to type
        delay: Delay between keystrokes in ms
        timeout: Element wait timeout in ms
        clear_first: Clear field before typing
        press_sequentially: Use type() for character-by-character
        force: Bypass actionability checks
        no_wait_after: Skip waiting for navigations
        strict: Require exactly one matching element
        press_enter_after: Press Enter after typing
        press_tab_after: Press Tab after typing
        retry_count: Number of retries on failure
        retry_interval: Delay between retries in ms
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for failure screenshot

    Inputs:
        page: Browser page instance
        selector: Element selector override
        text: Text to type override

    Outputs:
        page: Browser page instance (passthrough)
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Type Text",
        selector: str = "",
        text: str = "",
        delay: int = 0,
        **kwargs,
    ) -> None:
        """
        Initialize type text node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector (ignored when config provided)
            text: Text to type (ignored when config provided)
            delay: Delay between keystrokes (ignored when config provided)

        Note:
            The @node_schema decorator automatically handles default_config.
        """
        # Config auto-merged by @node_schema decorator
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

            # NEW: Unified parameter accessor
            selector = self.get_parameter("selector")
            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright
            normalized_selector = normalize_selector(selector)

            # Get text parameter (allow empty string)
            text = self.get_parameter("text", "")
            if text is None:
                text = ""

            # Resolve {{variable}} patterns in text
            text = context.resolve_value(text)

            # Get all other parameters
            delay = self.get_parameter("delay", 0)
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            clear_first = self.get_parameter("clear_first", True)
            press_sequentially = self.get_parameter("press_sequentially", False)
            force = self.get_parameter("force", False)
            no_wait_after = self.get_parameter("no_wait_after", False)
            strict = self.get_parameter("strict", False)
            press_enter_after = self.get_parameter("press_enter_after", False)
            press_tab_after = self.get_parameter("press_tab_after", False)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            # Type conversions
            delay = safe_int(delay, 0)
            timeout = safe_int(timeout, DEFAULT_NODE_TIMEOUT * 1000)
            retry_count = safe_int(retry_count, 0)
            retry_interval = safe_int(retry_interval, 1000)

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
        # Schema handles validation via @node_schema decorator
        return True, ""


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,  # Can come from input port
        label="Select Selector",
        tooltip="CSS or XPath selector for the select element",
        placeholder="#country or //select[@name='region']",
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        required=False,  # Can come from input port
        label="Value",
        tooltip="Value, label, or index to select",
        placeholder="Option value, label, or index",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        label="Timeout (ms)",
        tooltip="Maximum time to wait in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force",
        tooltip="Bypass actionability checks",
    ),
    PropertyDef(
        "no_wait_after",
        PropertyType.BOOLEAN,
        default=False,
        label="No Wait After",
        tooltip="Skip waiting for navigations after selection",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict",
        tooltip="Require exactly one matching element",
    ),
    PropertyDef(
        "select_by",
        PropertyType.CHOICE,
        default="value",
        choices=["value", "label", "index"],
        label="Select By",
        tooltip="Selection method (value, label, or index)",
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
        label="Screenshot On Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.FILE_PATH,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot (auto-generated if empty)",
    ),
)
@executable_node
class SelectDropdownNode(BaseNode):
    """
    Select dropdown node - selects an option from a dropdown.

    Finds a select element and chooses an option by value, label, or index.

    Config (via @node_schema):
        selector: CSS or XPath selector
        value: Value, label, or index to select
        timeout: Timeout in milliseconds
        force: Bypass actionability checks
        no_wait_after: Skip waiting for navigations
        strict: Require exactly one matching element
        select_by: Selection method (value, label, index)
        retry_count: Number of retries on failure
        retry_interval: Delay between retries in ms
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for failure screenshot

    Inputs:
        page: Browser page instance
        selector: Element selector override
        value: Value to select override

    Outputs:
        page: Browser page instance (passthrough)
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Select Dropdown",
        selector: str = "",
        value: str = "",
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
        **kwargs,
    ) -> None:
        """
        Initialize select dropdown node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector (ignored when config provided)
            value: Value or label to select (ignored when config provided)
            timeout: Timeout in milliseconds (ignored when config provided)

        Note:
            The @node_schema decorator automatically handles default_config.
        """
        # Config auto-merged by @node_schema decorator
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

            # NEW: Unified parameter accessor
            selector = self.get_parameter("selector")
            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright
            normalized_selector = normalize_selector(selector)

            # Get value parameter
            value = self.get_parameter("value")
            if not value:
                raise ValueError("Value is required")

            # Resolve {{variable}} patterns in value
            value = context.resolve_value(value)

            # Get all other parameters
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            force = self.get_parameter("force", False)
            no_wait_after = self.get_parameter("no_wait_after", False)
            strict = self.get_parameter("strict", False)
            select_by = self.get_parameter("select_by", "value")
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            # Type conversions
            timeout = safe_int(timeout, DEFAULT_NODE_TIMEOUT * 1000)
            retry_count = safe_int(retry_count, 0)
            retry_interval = safe_int(retry_interval, 1000)

            logger.info(
                f"Selecting dropdown option: {normalized_selector} = {value} (by={select_by})"
            )

            # Build select options
            select_options = {"timeout": timeout}

            if force:
                select_options["force"] = True

            if no_wait_after:
                select_options["no_wait_after"] = True

            if strict:
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
        # Schema handles validation via @node_schema decorator
        return True, ""
