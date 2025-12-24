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

from casare_rpa.config import DEFAULT_NODE_TIMEOUT
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
    BROWSER_FORCE,
    BROWSER_NO_WAIT_AFTER,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_SELECTOR_STRICT,
    BROWSER_TIMEOUT,
)
from casare_rpa.utils import safe_int
from casare_rpa.utils.resilience import retry_operation

# =============================================================================
# ClickElementNode
# =============================================================================


@properties(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Element Selector",
        tooltip="CSS or XPath selector for the element to click",
        placeholder="#button-id or //button[@name='submit']",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "fast_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Fast Mode",
        tooltip="Optimize for speed: skip waits, force action, reduced timeout",
        essential=True,  # Show when collapsed
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
    BROWSER_ANCHOR_CONFIG,
)
@node(category="browser")
class ClickElementNode(BrowserBaseNode):
    """
    Click element node - clicks on a page element.

    Finds an element by selector and performs a click action.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

    Config (via @properties):
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

    # @category: browser
    # @requires: none
    # @ports: via base class helpers

    def __init__(
        self,
        node_id: str,
        name: str = "Click Element",
        **kwargs,
    ) -> None:
        """Initialize click element node."""
        super().__init__(node_id, name=name, **kwargs)
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

            # Check for fast mode - optimizes for speed over reliability
            fast_mode = self.get_parameter("fast_mode", False)

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

            # Fast mode overrides for maximum speed
            if fast_mode:
                timeout = min(timeout, 5000)  # Cap at 5 seconds
                force = True  # Skip actionability checks
                no_wait_after = True  # Skip navigation waits
                logger.debug(
                    f"Fast mode enabled: timeout={timeout}ms, force=True, no_wait_after=True"
                )

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

            # Track healing info for result
            healing_tier = "original"
            final_selector = selector

            async def perform_click() -> bool:
                nonlocal healing_tier, final_selector

                # First try with healing fallback
                try:
                    (
                        element,
                        final_selector,
                        healing_tier,
                    ) = await self.find_element_with_healing(
                        page, selector, timeout, param_name="selector"
                    )
                    await self.highlight_if_enabled(page, final_selector, timeout)
                    await element.click(**click_options)
                    return True
                except Exception as healing_error:
                    # If healing also fails, fall back to direct click (original behavior)
                    # This allows Playwright's built-in waiting to have a chance
                    logger.debug(f"Healing failed, trying direct click: {healing_error}")
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
                result_data = {
                    "selector": selector,
                    "final_selector": final_selector,
                    "attempts": result.attempts,
                    "healing_tier": healing_tier,
                }
                if healing_tier != "original":
                    logger.info(f"Click succeeded with healing: {healing_tier} tier")
                return self.success_result(result_data)

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
        # Only set position if explicitly configured (not default 0,0)
        # Position (0,0) means top-left corner which is rarely intended
        if position_x is not None and position_y is not None:
            try:
                px, py = float(position_x), float(position_y)
                # Skip if both are 0 (default/unset) - let Playwright click center
                if px != 0.0 or py != 0.0:
                    options["position"] = {"x": px, "y": py}
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


@properties(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Input Selector",
        tooltip="CSS or XPath selector for the input element",
        placeholder="#email or //input[@name='username']",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        required=False,
        label="Text",
        tooltip="Text to type into the input field",
        placeholder="Text to enter...",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "fast_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Fast Mode",
        tooltip="Optimize for speed: skip waits, force action, reduced timeout (best for form filling)",
        essential=True,  # Show when collapsed - important for users
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
    BROWSER_ANCHOR_CONFIG,
)
@node(category="browser")
class TypeTextNode(BrowserBaseNode):
    """
    Type text node - types text into an input field.

    Finds an input element and types the specified text.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

    Config (via @properties):
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

    # @category: browser
    # @requires: none
    # @ports: text -> none

    def __init__(
        self,
        node_id: str,
        name: str = "Type Text",
        **kwargs,
    ) -> None:
        """Initialize type text node."""
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "TypeTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_selector_input_port()
        self.add_input_port("text", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute text typing."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get text parameter (allow empty string)
            text = self.get_parameter("text", "") or ""

            # Check for fast mode - optimizes for speed over reliability
            fast_mode = self.get_parameter("fast_mode", False)

            # Get type-specific parameters with fast mode overrides
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

            # Fast mode overrides for maximum speed
            if fast_mode:
                timeout = min(timeout, 5000)  # Cap at 5 seconds
                force = True  # Skip actionability checks
                no_wait_after = True  # Skip navigation waits
                clear_first = False  # Skip clearing (assume empty fields)
                logger.debug(
                    f"Fast mode enabled: timeout={timeout}ms, force=True, no_wait_after=True"
                )

            logger.info(f"Typing text into element: {selector}")

            # Build fill/type options
            fill_options = self._build_fill_options(
                timeout=timeout,
                force=force,
                no_wait_after=no_wait_after,
                strict=strict,
            )

            # Track healing info
            healing_tier = "original"
            final_selector = selector

            # Track if we navigated from label to input
            label_nav_method = "original"

            async def perform_type() -> bool:
                nonlocal healing_tier, final_selector, label_nav_method

                # Try with healing fallback first
                try:
                    (
                        element,
                        final_selector,
                        healing_tier,
                    ) = await self.find_element_with_healing(
                        page, selector, timeout, param_name="selector"
                    )

                    # Auto-navigate from label to input if needed
                    element, label_nav_method = await self.navigate_label_to_input(
                        page, element, timeout
                    )
                    if label_nav_method != "original":
                        logger.info(f"Auto-navigated from label to input via {label_nav_method}")

                    # Use element-based operations for better reliability
                    if delay > 0 or press_sequentially:
                        if clear_first:
                            await element.fill("")
                        type_delay = delay if delay > 0 else 50
                        await element.type(text, delay=type_delay)
                    else:
                        await element.fill(text)

                except Exception as healing_error:
                    # Fall back to selector-based operations (original behavior)
                    logger.debug(f"Healing failed, trying direct type: {healing_error}")
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
                result_data = {
                    "selector": selector,
                    "final_selector": final_selector,
                    "text_length": len(text),
                    "attempts": result.attempts,
                    "healing_tier": healing_tier,
                    "label_navigation": label_nav_method,
                }
                if healing_tier != "original":
                    logger.info(f"Type text succeeded with healing: {healing_tier} tier")
                if label_nav_method != "original":
                    logger.info(f"Type text auto-navigated from label to input: {label_nav_method}")
                return self.success_result(result_data)

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


@properties(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Select Selector",
        tooltip="CSS or XPath selector for the select element",
        placeholder="#country or //select[@name='region']",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        required=False,
        label="Value",
        tooltip="Value, label, or index to select",
        placeholder="Option value, label, or index",
        essential=True,  # Show when collapsed
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
    BROWSER_ANCHOR_CONFIG,
)
@node(category="browser")
class SelectDropdownNode(BrowserBaseNode):
    """
    Select dropdown node - selects an option from a dropdown.

    Finds a select element and chooses an option by value, label, or index.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

    Config (via @properties):
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

    # @category: browser
    # @requires: none
    # @ports: value -> none

    def __init__(
        self,
        node_id: str,
        name: str = "Select Dropdown",
        **kwargs,
    ) -> None:
        """Initialize select dropdown node."""
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "SelectDropdownNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_selector_input_port()
        self.add_input_port("value", DataType.STRING)

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

            # Get select-specific parameters
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            force = self.get_parameter("force", False)
            no_wait_after = self.get_parameter("no_wait_after", False)
            strict = self.get_parameter("strict", False)
            select_by = self.get_parameter("select_by", "value")

            logger.info(f"Selecting dropdown option: {selector} = {value} (by={select_by})")

            # Build select options
            select_options = self._build_select_options(
                timeout=timeout,
                force=force,
                no_wait_after=no_wait_after,
                strict=strict,
            )

            async def perform_select() -> bool:
                if select_by == "index":
                    await page.select_option(selector, index=int(value), **select_options)
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


# =============================================================================
# ImageClickNode
# =============================================================================


@properties(
    PropertyDef(
        "image_template",
        PropertyType.STRING,
        default="",
        required=False,
        label="Image Template",
        tooltip="Base64-encoded image template or healing context key",
        placeholder="Captured from selector dialog",
        essential=True,
    ),
    PropertyDef(
        "similarity_threshold",
        PropertyType.FLOAT,
        default=0.8,
        label="Similarity Threshold",
        tooltip="Minimum match similarity (0.0-1.0)",
        min_value=0.5,
        max_value=1.0,
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
        "click_offset_x",
        PropertyType.INTEGER,
        default=0,
        label="Offset X",
        tooltip="X offset from center of matched region",
    ),
    PropertyDef(
        "click_offset_y",
        PropertyType.INTEGER,
        default=0,
        label="Offset Y",
        tooltip="Y offset from center of matched region",
    ),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
@node(category="browser")
class ImageClickNode(BrowserBaseNode):
    """
    Image click node - clicks at a location found by image/template matching.

    Uses computer vision to find a template image on the page and clicks
    at the center of the matched region. Useful when selectors are unreliable
    or for visual elements without proper DOM structure.

    Config (via @properties):
        image_template: Base64-encoded image or healing context reference
        similarity_threshold: Minimum match similarity (0.0-1.0)
        button: Mouse button (left, right, middle)
        click_count: Number of clicks
        click_offset_x: X offset from match center
        click_offset_y: Y offset from match center
        timeout: Operation timeout in milliseconds
        retry_count: Number of retries on failure
        retry_interval: Delay between retries in ms

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
        name: str = "Image Click",
        **kwargs,
    ) -> None:
        """Initialize image click node."""
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "ImageClickNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute image-based click."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get parameters
            similarity = self.get_parameter("similarity_threshold", 0.8)
            button = self.get_parameter("button", "left")
            click_count = safe_int(self.get_parameter("click_count", 1), 1)
            offset_x = safe_int(self.get_parameter("click_offset_x", 0), 0)
            offset_y = safe_int(self.get_parameter("click_offset_y", 0), 0)
            safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )

            # Get image template from healing context or direct parameter
            template_bytes = await self._get_template_bytes()
            if not template_bytes:
                raise ValueError(
                    "No image template available. "
                    "Pick an element with the selector dialog first."
                )

            logger.info(f"Image click: searching for template ({len(template_bytes)} bytes)")

            async def perform_image_click() -> dict:
                # Capture page screenshot
                screenshot_bytes = await page.screenshot(type="png")

                # Find template match
                match = await self._find_template_match(
                    screenshot_bytes, template_bytes, similarity
                )

                if not match:
                    raise RuntimeError(f"Template not found on page (threshold: {similarity:.0%})")

                # Calculate click position
                click_x = match["center_x"] + offset_x
                click_y = match["center_y"] + offset_y

                logger.info(
                    f"Template found at ({match['center_x']}, {match['center_y']}) "
                    f"with {match['similarity']:.1%} similarity, clicking at ({click_x}, {click_y})"
                )

                # Perform click at coordinates
                await page.mouse.click(
                    click_x,
                    click_y,
                    button=button,
                    click_count=click_count,
                )

                return {
                    "click_x": click_x,
                    "click_y": click_y,
                    "match_x": match["x"],
                    "match_y": match["y"],
                    "match_width": match["width"],
                    "match_height": match["height"],
                    "similarity": match["similarity"],
                }

            result = await retry_operation(
                perform_image_click,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name="image click",
            )

            if result.success:
                self.set_output_value("page", page)
                return self.success_result(
                    {
                        **result.value,
                        "attempts": result.attempts,
                    }
                )

            await self.screenshot_on_failure(page, "image_click_fail")
            raise result.last_error or RuntimeError("Image click failed")

        except Exception as e:
            return self.error_result(e)

    async def _get_template_bytes(self) -> bytes | None:
        """Get template image bytes from config or healing context."""
        import base64

        # First check for direct image_template parameter (base64)
        image_template = self.get_parameter("image_template", "")
        if image_template and len(image_template) > 100:
            # Looks like base64 data
            try:
                return base64.b64decode(image_template)
            except Exception:
                pass

        # Check healing context from selector dialog
        healing_context = self.get_parameter("selector_healing_context", None)
        if healing_context and isinstance(healing_context, dict):
            cv_template = healing_context.get("cv_template", {})
            if cv_template and "image_base64" in cv_template:
                try:
                    return base64.b64decode(cv_template["image_base64"])
                except Exception:
                    pass

        return None

    async def _find_template_match(
        self,
        screenshot_bytes: bytes,
        template_bytes: bytes,
        threshold: float,
    ) -> dict | None:
        """Find template in screenshot using CV matching."""
        try:
            from casare_rpa.infrastructure.browser.healing.cv_healer import CVHealer

            cv_healer = CVHealer()
            if not cv_healer.is_available:
                raise RuntimeError("OpenCV not available for image matching")

            # Convert bytes to CV images
            screenshot = cv_healer._bytes_to_cv_image(screenshot_bytes)
            template = cv_healer._bytes_to_cv_image(template_bytes)

            # Perform matching
            import asyncio

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None,
                cv_healer._perform_template_matching,
                screenshot,
                template,
            )

            # Filter by threshold and get best match
            valid_matches = [m for m in matches if m.similarity >= threshold]
            if not valid_matches:
                return None

            best = max(valid_matches, key=lambda m: m.similarity)
            return {
                "x": best.x,
                "y": best.y,
                "width": best.width,
                "height": best.height,
                "center_x": best.center_x,
                "center_y": best.center_y,
                "similarity": best.similarity,
            }

        except ImportError:
            logger.error("CV matching requires opencv-python")
            raise RuntimeError("Install opencv-python for image matching") from None
        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            return None


# =============================================================================
# PressKeyNode
# =============================================================================


@properties(
    PropertyDef(
        "key",
        PropertyType.STRING,
        default="Enter",
        required=True,
        label="Key",
        tooltip="Key to press (e.g., Enter, Escape, Tab, F1, ArrowDown, etc.)",
        placeholder="Escape",
        essential=True,
    ),
    PropertyDef(
        "delay",
        PropertyType.INTEGER,
        default=0,
        label="Delay (ms)",
        tooltip="Optional delay between keydown and keyup in milliseconds",
        min_value=0,
    ),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
)
@node(category="browser")
class PressKeyNode(BrowserBaseNode):
    """
    Press key node - presses a keyboard key on the browser page.

    Uses Playwright's page.keyboard.press() to simulate keyboard input.
    Useful for pressing keys like Escape to dismiss modals, Enter to submit,
    Tab to navigate, or any special keys.

    Config (via @properties):
        key: Key to press (Enter, Escape, Tab, F1-F12, ArrowUp/Down/Left/Right, etc.)
        delay: Delay between keydown and keyup in ms
        timeout: Operation timeout in milliseconds
        retry_count: Number of retries on failure
        retry_interval: Delay between retries in ms

    Inputs:
        page: Browser page instance

    Outputs:
        page: Browser page instance (passthrough)

    Example keys:
        - Enter, Escape, Tab, Backspace, Delete
        - ArrowUp, ArrowDown, ArrowLeft, ArrowRight
        - Home, End, PageUp, PageDown
        - F1-F12
        - Control+A, Shift+Tab (key combinations)
    """

    # @category: browser
    # @requires: none
    # @ports: via base class helpers

    def __init__(
        self,
        node_id: str,
        name: str = "Press Key",
        **kwargs,
    ) -> None:
        """Initialize press key node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "PressKeyNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute keyboard key press."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get parameters
            key = self.get_parameter("key", "Enter")
            if not key:
                raise ValueError("Key is required")

            delay = safe_int(self.get_parameter("delay", 0), 0)

            logger.info(f"Pressing key: {key}")

            async def perform_key_press() -> bool:
                if delay > 0:
                    await page.keyboard.press(key, delay=delay)
                else:
                    await page.keyboard.press(key)
                return True

            result = await retry_operation(
                perform_key_press,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"press key {key}",
            )

            if result.success:
                self.set_output_value("page", page)
                return self.success_result(
                    {
                        "key": key,
                        "delay": delay,
                        "attempts": result.attempts,
                    }
                )

            raise result.last_error or RuntimeError(f"Failed to press key: {key}")

        except Exception as e:
            return self.error_result(e)
