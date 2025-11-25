"""
Interaction nodes for element manipulation.

This module provides nodes for interacting with page elements:
clicking, typing, selecting, etc.
"""

import asyncio
from typing import Any, Optional

from playwright.async_api import Page

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from ..utils.config import DEFAULT_NODE_TIMEOUT
from ..utils.selector_normalizer import normalize_selector
from loguru import logger


class ClickElementNode(BaseNode):
    """
    Click element node - clicks on a page element.
    
    Finds an element by selector and performs a click action.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Click Element",
        selector: str = "",
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,  # Convert to milliseconds
        **kwargs
    ) -> None:
        """
        Initialize click element node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds
        """
        # Default config with all Playwright click options
        default_config = {
            "selector": selector,
            "timeout": timeout,
            "button": "left",  # left, right, middle
            "click_count": 1,  # Number of clicks (2 for double-click)
            "delay": 0,  # Delay between mousedown and mouseup in ms
            "force": False,  # Bypass actionability checks
            "position_x": None,  # Click position X offset
            "position_y": None,  # Click position Y offset
            "modifiers": [],  # Modifier keys: 'Alt', 'Control', 'Meta', 'Shift'
            "no_wait_after": False,  # Skip waiting for navigations after click
            "trial": False,  # Perform actionability checks without clicking
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
            "screenshot_on_fail": False,  # Take screenshot on failure
            "screenshot_path": "",  # Path for failure screenshot
            "highlight_before_click": False,  # Highlight element before clicking
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClickElementNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
                selector = self.config.get("selector", "")

            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000

            logger.info(f"Clicking element: {normalized_selector}")

            # Build click options
            click_options = {"timeout": timeout}

            # Button type (left, right, middle)
            button = self.config.get("button", "left")
            if button and button != "left":
                click_options["button"] = button

            # Click count (for double-click)
            click_count = self.config.get("click_count", 1)
            if click_count and str(click_count).strip():
                try:
                    click_count_int = int(click_count)
                    if click_count_int > 1:
                        click_options["click_count"] = click_count_int
                except (ValueError, TypeError):
                    pass

            # Delay between mousedown and mouseup
            delay = self.config.get("delay", 0)
            if delay and str(delay).strip():
                try:
                    delay_int = int(delay)
                    if delay_int > 0:
                        click_options["delay"] = delay_int
                except (ValueError, TypeError):
                    pass

            # Force click (bypass actionability checks)
            if self.config.get("force", False):
                click_options["force"] = True

            # Position offset
            pos_x = self.config.get("position_x")
            pos_y = self.config.get("position_y")
            if pos_x is not None and pos_y is not None:
                try:
                    click_options["position"] = {"x": float(pos_x), "y": float(pos_y)}
                except (ValueError, TypeError):
                    pass  # Ignore invalid position values

            # Modifiers (Alt, Control, Meta, Shift)
            modifiers = self.config.get("modifiers", [])
            if modifiers:
                click_options["modifiers"] = modifiers

            # No wait after (skip waiting for navigations)
            if self.config.get("no_wait_after", False):
                click_options["no_wait_after"] = True

            # Trial mode (actionability checks only)
            if self.config.get("trial", False):
                click_options["trial"] = True

            logger.debug(f"Click options: {click_options}")

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")
            highlight_before_click = self.config.get("highlight_before_click", False)

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for click: {selector}")

                    # Highlight element before clicking if requested
                    if highlight_before_click:
                        try:
                            element = await page.wait_for_selector(normalized_selector, timeout=timeout)
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

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Element clicked successfully: {selector} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"selector": selector, "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Click failed (attempt {attempts}): {e}")
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
                        path = f"click_fail_{timestamp}.png"

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
            logger.error(f"Failed to click element: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        selector = self.config.get("selector", "")
        if not selector:
            # Selector can come from input port
            return True, ""
        return True, ""


class TypeTextNode(BaseNode):
    """
    Type text node - types text into an input field.

    Finds an input element and types the specified text.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Type Text",
        selector: str = "",
        text: str = "",
        delay: int = 0,
        **kwargs
    ) -> None:
        """
        Initialize type text node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the input element
            text: Text to type
            delay: Delay between keystrokes in milliseconds
        """
        # Default config with all Playwright options
        default_config = {
            "selector": selector,
            "text": text,
            "delay": delay,
            "timeout": DEFAULT_NODE_TIMEOUT * 1000,  # Element wait timeout
            "clear_first": True,  # Clear field before typing
            "press_sequentially": False,  # Use type() for character-by-character (overrides delay)
            "force": False,  # Bypass actionability checks
            "no_wait_after": False,  # Skip waiting for navigations
            "strict": False,  # Require exactly one matching element
            "press_enter_after": False,  # Press Enter after typing
            "press_tab_after": False,  # Press Tab after typing
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
            "screenshot_on_fail": False,  # Take screenshot on failure
            "screenshot_path": "",  # Path for failure screenshot
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TypeTextNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
                selector = self.config.get("selector", "")

            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            # Get text from input or config
            text = self.get_input_value("text")
            if text is None:
                text = self.config.get("text", "")

            if text is None:
                text = ""

            # Resolve {{variable}} patterns in text
            text = context.resolve_value(text)

            # Safely parse delay with default
            delay_val = self.config.get("delay")
            if delay_val is None or delay_val == "":
                delay = 0
            else:
                try:
                    delay = int(delay_val)
                except (ValueError, TypeError):
                    delay = 0

            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000
            clear_first = self.config.get("clear_first", True)
            press_sequentially = self.config.get("press_sequentially", False)
            force = self.config.get("force", False)
            no_wait_after = self.config.get("no_wait_after", False)
            strict = self.config.get("strict", False)
            press_enter_after = self.config.get("press_enter_after", False)
            press_tab_after = self.config.get("press_tab_after", False)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")

            logger.info(f"Typing text into element: {normalized_selector}")

            # Build fill/type options
            fill_options = {"timeout": timeout}
            if force:
                fill_options["force"] = True
            if no_wait_after:
                fill_options["no_wait_after"] = True
            if strict:
                fill_options["strict"] = True

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for type text: {selector}")

                    # Type text - use fill() for immediate input, type() for character-by-character with delay
                    # Only use one method to avoid double-typing
                    if delay > 0 or press_sequentially:
                        # Clear the field first if configured, then type with delay
                        if clear_first:
                            await page.fill(normalized_selector, "", **fill_options)
                        type_delay = delay if delay > 0 else 50  # Default 50ms for press_sequentially
                        await page.type(normalized_selector, text, delay=type_delay, timeout=timeout)
                    else:
                        # Use fill() for immediate input (faster)
                        # fill() always clears the field first, so clear_first doesn't affect behavior here
                        await page.fill(normalized_selector, text, **fill_options)

                    # Press Enter after if requested
                    if press_enter_after:
                        await page.keyboard.press("Enter")

                    # Press Tab after if requested
                    if press_tab_after:
                        await page.keyboard.press("Tab")

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Text typed successfully: {selector} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "selector": selector,
                            "text_length": len(text),
                            "attempts": attempts
                        },
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Type text failed (attempt {attempts}): {e}")
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
                        path = f"type_text_fail_{timestamp}.png"

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
            logger.error(f"Failed to type text: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


class SelectDropdownNode(BaseNode):
    """
    Select dropdown node - selects an option from a dropdown.

    Finds a select element and chooses an option by value, label, or index.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Select Dropdown",
        selector: str = "",
        value: str = "",
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
        **kwargs
    ) -> None:
        """
        Initialize select dropdown node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the select element
            value: Value or label to select
            timeout: Timeout in milliseconds
        """
        # Default config with all Playwright select_option options
        default_config = {
            "selector": selector,
            "value": value,
            "timeout": timeout,
            "force": False,  # Bypass actionability checks
            "no_wait_after": False,  # Skip waiting for navigations after selection
            "strict": False,  # Require exactly one matching element
            "select_by": "value",  # value, label, or index
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
            "screenshot_on_fail": False,  # Take screenshot on failure
            "screenshot_path": "",  # Path for failure screenshot
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, val in default_config.items():
            if key not in config:
                config[key] = val

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SelectDropdownNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_input_port("value", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
                selector = self.config.get("selector", "")

            if not selector:
                raise ValueError("Selector is required")

            # Resolve {{variable}} patterns in selector
            selector = context.resolve_value(selector)

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            # Get value from input or config
            value = self.get_input_value("value")
            if value is None:
                value = self.config.get("value", "")

            if not value:
                raise ValueError("Value is required")

            # Resolve {{variable}} patterns in value
            value = context.resolve_value(value)

            # Get Playwright options from config - safely parse timeout
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000
            select_by = self.config.get("select_by", "value")

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")

            logger.info(f"Selecting dropdown option: {normalized_selector} = {value} (by={select_by})")

            # Build select options
            select_options = {"timeout": timeout}

            # Force option (bypass actionability checks)
            if self.config.get("force", False):
                select_options["force"] = True

            # No wait after (skip waiting for navigations)
            if self.config.get("no_wait_after", False):
                select_options["no_wait_after"] = True

            # Strict mode (require exactly one element)
            if self.config.get("strict", False):
                select_options["strict"] = True

            logger.debug(f"Select options: {select_options}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for select: {selector}")

                    # Select option based on select_by mode
                    if select_by == "index":
                        await page.select_option(normalized_selector, index=int(value), **select_options)
                    elif select_by == "label":
                        await page.select_option(normalized_selector, label=value, **select_options)
                    else:  # value (default)
                        await page.select_option(normalized_selector, value=value, **select_options)

                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Dropdown selected successfully: {selector} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "selector": selector,
                            "value": value,
                            "select_by": select_by,
                            "attempts": attempts
                        },
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Select dropdown failed (attempt {attempts}): {e}")
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
                        path = f"select_dropdown_fail_{timestamp}.png"

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
            logger.error(f"Failed to select dropdown: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""

