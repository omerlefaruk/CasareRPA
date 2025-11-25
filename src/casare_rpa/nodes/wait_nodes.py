"""
Wait and timing nodes for synchronization.

This module provides nodes for waiting: fixed delays, element waits,
and navigation waits.
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


class WaitNode(BaseNode):
    """
    Wait node - pauses execution for a specified duration.
    
    Simple delay node for fixed-time waits.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Wait",
        duration: float = 1.0,
        **kwargs
    ) -> None:
        """
        Initialize wait node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            duration: Wait duration in seconds
        """
        config = kwargs.get("config", {"duration": duration})
        if "duration" not in config:
            config["duration"] = duration
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("duration", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
    
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
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to wait: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        duration = self.config.get("duration", 0)
        if duration < 0:
            return False, "Duration must be non-negative"
        return True, ""


class WaitForElementNode(BaseNode):
    """
    Wait for element node - waits for an element to appear.

    Waits until an element matching the selector is visible on the page.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Element",
        selector: str = "",
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
        state: str = "visible",
        **kwargs
    ) -> None:
        """
        Initialize wait for element node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds
            state: Element state to wait for (visible, hidden, attached, detached)
        """
        # Default config with all Playwright wait_for_selector options
        default_config = {
            "selector": selector,
            "timeout": timeout,
            "state": state,
            "strict": False,  # Require exactly one matching element
            "poll_interval": 100,  # Polling interval in ms (custom, for retry logic)
            "retry_count": 0,  # Number of retries after timeout (0 = no retry)
            "retry_interval": 1000,  # Delay between retries in ms
            "screenshot_on_fail": False,  # Take screenshot on failure
            "screenshot_path": "",  # Path for failure screenshot
            "highlight_on_find": False,  # Briefly highlight element when found
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitForElementNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)
    
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
                selector = self.config.get("selector", "")
            
            if not selector:
                raise ValueError("Selector is required")
            
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
            state = self.config.get("state", "visible")
            
            logger.info(f"Waiting for element: {normalized_selector} (state={state})")
            
            # Wait for element
            await page.wait_for_selector(
                normalized_selector,
                timeout=timeout,
                state=state
            )
            
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Element appeared: {selector}")
            
            return {
                "success": True,
                "data": {
                    "selector": selector,
                    "state": state
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to wait for element: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        state = self.config.get("state", "visible")
        if state not in ["visible", "hidden", "attached", "detached"]:
            return False, f"Invalid state: {state}"
        return True, ""


class WaitForNavigationNode(BaseNode):
    """
    Wait for navigation node - waits for page navigation to complete.

    Waits for the page to navigate to a new URL or reload.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Wait For Navigation",
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
        wait_until: str = "load",
        **kwargs
    ) -> None:
        """
        Initialize wait for navigation node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            timeout: Timeout in milliseconds
            wait_until: Event to wait for (load, domcontentloaded, networkidle, commit)
        """
        # Default config with all Playwright wait_for_load_state options
        default_config = {
            "timeout": timeout,
            "wait_until": wait_until,
            "url_pattern": "",  # Optional URL pattern to wait for (glob or regex)
            "url_use_regex": False,  # Treat url_pattern as regex instead of glob
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WaitForNavigationNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
            
            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000
            wait_until = self.config.get("wait_until", "load")
            
            logger.info(f"Waiting for navigation (wait_until={wait_until})")
            
            # Wait for navigation
            await page.wait_for_load_state(wait_until, timeout=timeout)
            
            self.set_output_value("page", page)
            
            self.status = NodeStatus.SUCCESS
            logger.info("Navigation completed")
            
            return {
                "success": True,
                "data": {
                    "url": page.url,
                    "wait_until": wait_until
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to wait for navigation: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        wait_until = self.config.get("wait_until", "load")
        if wait_until not in ["load", "domcontentloaded", "networkidle"]:
            return False, f"Invalid wait_until: {wait_until}"
        return True, ""

