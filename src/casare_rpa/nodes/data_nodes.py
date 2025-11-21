"""
Data extraction nodes for retrieving information from pages.

This module provides nodes for extracting data: text content,
attributes, screenshots, and page information.
"""

from typing import Any, Optional
from pathlib import Path

from playwright.async_api import Page

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from ..utils.config import DEFAULT_NODE_TIMEOUT
from loguru import logger


class ExtractTextNode(BaseNode):
    """
    Extract text node - extracts text content from an element.
    
    Finds an element and retrieves its text content.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Extract Text",
        selector: str = "",
        variable_name: str = "extracted_text",
        **kwargs
    ) -> None:
        """
        Initialize extract text node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the element
            variable_name: Name of variable to store result
        """
        config = kwargs.get("config", {"selector": selector, "variable_name": variable_name})
        if "selector" not in config:
            config["selector"] = selector
        if "variable_name" not in config:
            config["variable_name"] = variable_name
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExtractTextNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("text", PortType.OUTPUT, DataType.STRING)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute text extraction.
        
        Args:
            context: Execution context for the workflow
            
        Returns:
            Result with extracted text
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
            
            variable_name = self.config.get("variable_name", "extracted_text")
            
            logger.info(f"Extracting text from element: {selector}")
            
            # Extract text
            element = await page.query_selector(selector)
            if element is None:
                raise ValueError(f"Element not found: {selector}")
            
            text = await element.text_content()
            
            # Store in variable
            context.set_variable(variable_name, text)
            
            # Set output
            self.set_output_value("text", text)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Text extracted successfully: {len(text) if text else 0} characters")
            
            return {
                "success": True,
                "data": {
                    "text": text,
                    "variable": variable_name
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to extract text: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


class GetAttributeNode(BaseNode):
    """
    Get attribute node - retrieves an attribute value from an element.
    
    Finds an element and gets the specified attribute value.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Get Attribute",
        selector: str = "",
        attribute: str = "",
        variable_name: str = "attribute_value",
        **kwargs
    ) -> None:
        """
        Initialize get attribute node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the element
            attribute: Attribute name to retrieve
            variable_name: Name of variable to store result
        """
        config = kwargs.get("config", {"selector": selector, "attribute": attribute, "variable_name": variable_name})
        if "selector" not in config:
            config["selector"] = selector
        if "attribute" not in config:
            config["attribute"] = attribute
        if "variable_name" not in config:
            config["variable_name"] = variable_name
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetAttributeNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_input_port("attribute", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("value", PortType.OUTPUT, DataType.STRING)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute attribute retrieval.
        
        Args:
            context: Execution context for the workflow
            
        Returns:
            Result with attribute value
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
            
            # Get attribute from input or config
            attribute = self.get_input_value("attribute")
            if attribute is None:
                attribute = self.config.get("attribute", "")
            
            if not attribute:
                raise ValueError("Attribute name is required")
            
            variable_name = self.config.get("variable_name", "attribute_value")
            
            logger.info(f"Getting attribute '{attribute}' from element: {selector}")
            
            # Get attribute
            value = await page.get_attribute(selector, attribute)
            
            # Store in variable
            context.set_variable(variable_name, value)
            
            # Set output
            self.set_output_value("value", value)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Attribute retrieved successfully: {attribute} = {value}")
            
            return {
                "success": True,
                "data": {
                    "attribute": attribute,
                    "value": value,
                    "variable": variable_name
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get attribute: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


class ScreenshotNode(BaseNode):
    """
    Screenshot node - captures a screenshot of the page or element.
    
    Takes a screenshot and saves it to a file.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Screenshot",
        file_path: str = "",
        selector: Optional[str] = None,
        full_page: bool = False,
        **kwargs
    ) -> None:
        """
        Initialize screenshot node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            file_path: Path where screenshot will be saved
            selector: Optional selector for element screenshot
            full_page: Whether to capture full scrollable page
        """
        config = kwargs.get("config", {"file_path": file_path, "selector": selector, "full_page": full_page})
        if "file_path" not in config:
            config["file_path"] = file_path
        if "selector" not in config:
            config["selector"] = selector
        if "full_page" not in config:
            config["full_page"] = full_page
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ScreenshotNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute screenshot capture.
        
        Args:
            context: Execution context for the workflow
            
        Returns:
            Result with screenshot file path
        """
        self.status = NodeStatus.RUNNING
        
        try:
            page = self.get_input_value("page")
            if page is None:
                page = context.get_active_page()
            
            if page is None:
                raise ValueError("No page instance found")
            
            # Get file path from input or config
            file_path = self.get_input_value("file_path")
            if file_path is None:
                file_path = self.config.get("file_path", "")
            
            if not file_path:
                raise ValueError("File path is required")
            
            selector = self.config.get("selector")
            full_page = self.config.get("full_page", False)
            
            logger.info(f"Taking screenshot: {file_path}")
            
            # Take screenshot
            if selector:
                element = await page.query_selector(selector)
                if element is None:
                    raise ValueError(f"Element not found: {selector}")
                await element.screenshot(path=file_path)
            else:
                await page.screenshot(path=file_path, full_page=full_page)
            
            # Set output
            self.set_output_value("file_path", file_path)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Screenshot saved: {file_path}")
            
            return {
                "success": True,
                "data": {
                    "file_path": file_path,
                    "full_page": full_page,
                    "element": selector is not None
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to take screenshot: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        file_path = self.config.get("file_path", "")
        if file_path:
            # Check if path is valid
            try:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Invalid file path: {e}"
        return True, ""

