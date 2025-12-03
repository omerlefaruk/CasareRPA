"""
Interaction nodes for element manipulation.

This module provides nodes for interacting with page elements:
clicking, typing, selecting, etc.

All nodes extend BrowserBaseNode for consistent patterns:
- Page access from context
- Selector normalization
- Retry logic
- Screenshot on failure
"""

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_FORCE,
    BROWSER_NO_WAIT_AFTER,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_SELECTOR_STRICT,
    BROWSER_TIMEOUT,
)
from casare_rpa.config import DEFAULT_NODE_TIMEOUT
from casare_rpa.utils import safe_int
from casare_rpa.utils.resilience import retry_operation


# =============================================================================
# ClickElementNode
# =============================================================================


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Element Selector",
        tooltip="CSS or XPath selector for the element to click",
        placeholder="#button-id or //button[@name='submit']",
    ),
    BROWSER_TIMEOUT,
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
    BROWSER_FORCE,
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
    BROWSER_NO_WAIT_AFTER,
    PropertyDef(
        "trial",
        PropertyType.BOOLEAN,
        default=False,
        label="Trial Mode",
        tooltip="Perform actionability checks without clicking",
    ),
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    PropertyDef(
        "highlight_before_click",
        PropertyType.BOOLEAN,
        default=False,
        label="Highlight Element",
        tooltip="Highlight element before clicking",
    ),
)
@executable_node
class ClickElementNode(BrowserBaseNode):
    """
    Click element node - clicks on a page element.

    Finds an element by selector and performs a click action.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

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
        **kwargs,
    ) -> None:
        """Initialize click element node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "ClickElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_selector_input_port()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute element click."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get click-specific parameters
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            button = self.get_parameter("button", "left")
            click_count = safe_int(self.get_parameter("click_count", 1), 1)
            delay = safe_int(self.get_parameter("delay", 0), 0)
            force = self.get_parameter("force", False)
            position_x = self.get_parameter("position_x")
            position_y = self.get_parameter("position_y")
            modifiers = self.get_parameter("modifiers", [])
            no_wait_after = self.get_parameter("no_wait_after", False)
            trial = self.get_parameter("trial", False)

            logger.info(f"Clicking element: {selector}")

            # Build click options
            click_options = self._build_click_options(
                timeout=timeout,
                button=button,
                click_count=click_count,
                delay=delay,
                force=force,
                position_x=position_x,
                position_y=position_y,
                modifiers=modifiers,
                no_wait_after=no_wait_after,
                trial=trial,
            )

            logger.debug(f"Click options: {click_options}")

            async def perform_click() -> bool:
                await self.highlight_if_enabled(page, selector, timeout)
                await page.click(selector, **click_options)
                return True

            result = await retry_operation(
                perform_click,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"click {selector}",
            )

            if result.success:
                self.set_output_value("page", page)
                return self.success_result(
                    {"selector": selector, "attempts": result.attempts}
                )

            # Handle failure
            await self.screenshot_on_failure(page, "click_fail")
            raise result.last_error or RuntimeError("Click failed")

        except Exception as e:
            return self.error_result(e)

    def _build_click_options(
        self,
        timeout: int,
        button: str,
        click_count: int,
        delay: int,
        force: bool,
        position_x: Any,
        position_y: Any,
        modifiers: list,
        no_wait_after: bool,
        trial: bool,
    ) -> dict:
        """Build Playwright click options dictionary."""
        options: dict = {"timeout": timeout}

        if button and button != "left":
            options["button"] = button
        if click_count > 1:
            options["click_count"] = click_count
        if delay > 0:
            options["delay"] = delay
        if force:
            options["force"] = True
        if position_x is not None and position_y is not None:
            try:
                options["position"] = {"x": float(position_x), "y": float(position_y)}
            except (ValueError, TypeError):
                pass
        if modifiers:
            options["modifiers"] = modifiers
        if no_wait_after:
            options["no_wait_after"] = True
        if trial:
            options["trial"] = True

        return options


# =============================================================================
# TypeTextNode
# =============================================================================


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Input Selector",
        tooltip="CSS or XPath selector for the input element",
        placeholder="#email or //input[@name='username']",
    ),
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        required=False,
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
    BROWSER_TIMEOUT,
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
    BROWSER_FORCE,
    BROWSER_NO_WAIT_AFTER,
    BROWSER_SELECTOR_STRICT,
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
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
@executable_node
class TypeTextNode(BrowserBaseNode):
    """
    Type text node - types text into an input field.

    Finds an input element and types the specified text.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

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
        **kwargs,
    ) -> None:
        """Initialize type text node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "TypeTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_selector_input_port()
        self.add_input_port("text", PortType.INPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute text typing."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get text parameter (allow empty string)
            text = self.get_parameter("text", "") or ""
            text = context.resolve_value(text)

            # Get type-specific parameters
            delay = safe_int(self.get_parameter("delay", 0), 0)
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            clear_first = self.get_parameter("clear_first", True)
            press_sequentially = self.get_parameter("press_sequentially", False)
            force = self.get_parameter("force", False)
            no_wait_after = self.get_parameter("no_wait_after", False)
            strict = self.get_parameter("strict", False)
            press_enter_after = self.get_parameter("press_enter_after", False)
            press_tab_after = self.get_parameter("press_tab_after", False)

            logger.info(f"Typing text into element: {selector}")

            # Build fill/type options
            fill_options = self._build_fill_options(
                timeout=timeout,
                force=force,
                no_wait_after=no_wait_after,
                strict=strict,
            )

            async def perform_type() -> bool:
                if delay > 0 or press_sequentially:
                    if clear_first:
                        await page.fill(selector, "", **fill_options)
                    type_delay = delay if delay > 0 else 50
                    await page.type(selector, text, delay=type_delay, timeout=timeout)
                else:
                    await page.fill(selector, text, **fill_options)

                if press_enter_after:
                    await page.keyboard.press("Enter")
                if press_tab_after:
                    await page.keyboard.press("Tab")

                return True

            result = await retry_operation(
                perform_type,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"type text into {selector}",
            )

            if result.success:
                self.set_output_value("page", page)
                return self.success_result(
                    {
                        "selector": selector,
                        "text_length": len(text),
                        "attempts": result.attempts,
                    }
                )

            await self.screenshot_on_failure(page, "type_text_fail")
            raise result.last_error or RuntimeError("Type text failed")

        except Exception as e:
            return self.error_result(e)

    def _build_fill_options(
        self,
        timeout: int,
        force: bool,
        no_wait_after: bool,
        strict: bool,
    ) -> dict:
        """Build Playwright fill options dictionary."""
        options: dict = {"timeout": timeout}
        if force:
            options["force"] = True
        if no_wait_after:
            options["no_wait_after"] = True
        if strict:
            options["strict"] = True
        return options


# =============================================================================
# SelectDropdownNode
# =============================================================================


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Select Selector",
        tooltip="CSS or XPath selector for the select element",
        placeholder="#country or //select[@name='region']",
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        required=False,
        label="Value",
        tooltip="Value, label, or index to select",
        placeholder="Option value, label, or index",
    ),
    BROWSER_TIMEOUT,
    BROWSER_FORCE,
    BROWSER_NO_WAIT_AFTER,
    BROWSER_SELECTOR_STRICT,
    PropertyDef(
        "select_by",
        PropertyType.CHOICE,
        default="value",
        choices=["value", "label", "index"],
        label="Select By",
        tooltip="Selection method (value, label, or index)",
    ),
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
@executable_node
class SelectDropdownNode(BrowserBaseNode):
    """
    Select dropdown node - selects an option from a dropdown.

    Finds a select element and chooses an option by value, label, or index.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

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
        **kwargs,
    ) -> None:
        """Initialize select dropdown node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "SelectDropdownNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_selector_input_port()
        self.add_input_port("value", PortType.INPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute dropdown selection."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get value parameter
            value = self.get_parameter("value")
            if not value:
                raise ValueError("Value is required")
            value = context.resolve_value(value)

            # Get select-specific parameters
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            force = self.get_parameter("force", False)
            no_wait_after = self.get_parameter("no_wait_after", False)
            strict = self.get_parameter("strict", False)
            select_by = self.get_parameter("select_by", "value")

            logger.info(
                f"Selecting dropdown option: {selector} = {value} (by={select_by})"
            )

            # Build select options
            select_options = self._build_select_options(
                timeout=timeout,
                force=force,
                no_wait_after=no_wait_after,
                strict=strict,
            )

            async def perform_select() -> bool:
                if select_by == "index":
                    await page.select_option(
                        selector, index=int(value), **select_options
                    )
                elif select_by == "label":
                    await page.select_option(selector, label=value, **select_options)
                else:
                    await page.select_option(selector, value=value, **select_options)
                return True

            result = await retry_operation(
                perform_select,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"select dropdown {selector}",
            )

            if result.success:
                self.set_output_value("page", page)
                return self.success_result(
                    {
                        "selector": selector,
                        "value": value,
                        "select_by": select_by,
                        "attempts": result.attempts,
                    }
                )

            await self.screenshot_on_failure(page, "select_dropdown_fail")
            raise result.last_error or RuntimeError("Select dropdown failed")

        except Exception as e:
            return self.error_result(e)

    def _build_select_options(
        self,
        timeout: int,
        force: bool,
        no_wait_after: bool,
        strict: bool,
    ) -> dict:
        """Build Playwright select options dictionary."""
        options: dict = {"timeout": timeout}
        if force:
            options["force"] = True
        if no_wait_after:
            options["no_wait_after"] = True
        if strict:
            options["strict"] = True
        return options
