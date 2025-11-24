"""
Interaction nodes for element manipulation.

This module provides nodes for interacting with page elements:
clicking, typing, selecting, etc.
"""

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
        config = kwargs.get("config", {"selector": selector, "timeout": timeout})
        if "selector" not in config:
            config["selector"] = selector
        if "timeout" not in config:
            config["timeout"] = timeout
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
            
            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)
            
            timeout = self.config.get("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            
            logger.info(f"Clicking element: {normalized_selector}")
            
            # Click element
            await page.click(normalized_selector, timeout=timeout)
            
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Element clicked successfully: {selector}")
            
            return {
                "success": True,
                "data": {"selector": selector},
                "next_nodes": ["exec_out"]
            }
            
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
        config = kwargs.get("config", {"selector": selector, "text": text, "delay": delay})
        if "selector" not in config:
            config["selector"] = selector
        if "text" not in config:
            config["text"] = text
        if "delay" not in config:
            config["delay"] = delay
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
            
            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)
            
            # Get text from input or config
            text = self.get_input_value("text")
            if text is None:
                text = self.config.get("text", "")
            
            if text is None:
                text = ""
            
            delay = self.config.get("delay", 0)
            
            logger.info(f"Typing text into element: {normalized_selector}")

            # Type text - use fill() for immediate input, type() for character-by-character with delay
            # Only use one method to avoid double-typing
            if delay > 0:
                # Clear the field first, then type with delay
                await page.fill(normalized_selector, "")
                await page.type(normalized_selector, text, delay=delay)
            else:
                # Use fill() for immediate input (faster)
                await page.fill(normalized_selector, text)
            
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Text typed successfully: {selector}")
            
            return {
                "success": True,
                "data": {
                    "selector": selector,
                    "text_length": len(text)
                },
                "next_nodes": ["exec_out"]
            }
            
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
        **kwargs
    ) -> None:
        """
        Initialize select dropdown node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the select element
            value: Value or label to select
        """
        config = kwargs.get("config", {"selector": selector, "value": value})
        if "selector" not in config:
            config["selector"] = selector
        if "value" not in config:
            config["value"] = value
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
            
            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)
            
            # Get value from input or config
            value = self.get_input_value("value")
            if value is None:
                value = self.config.get("value", "")
            
            if not value:
                raise ValueError("Value is required")
            
            logger.info(f"Selecting dropdown option: {normalized_selector} = {value}")
            
            # Select option
            await page.select_option(normalized_selector, value)
            
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Dropdown selected successfully: {selector}")
            
            return {
                "success": True,
                "data": {
                    "selector": selector,
                    "value": value
                },
                "next_nodes": ["exec_out"]
            }
            
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

