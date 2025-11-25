"""
Data extraction nodes for retrieving information from pages.

This module provides nodes for extracting data: text content,
attributes, screenshots, and page information.
"""

import asyncio
from typing import Any, Optional
from pathlib import Path

from playwright.async_api import Page

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from ..utils.config import DEFAULT_NODE_TIMEOUT
from ..utils.selector_normalizer import normalize_selector
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
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
        **kwargs
    ) -> None:
        """
        Initialize extract text node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            selector: CSS or XPath selector for the element
            variable_name: Name of variable to store result
            timeout: Timeout in milliseconds
        """
        # Default config with all Playwright text extraction options
        default_config = {
            "selector": selector,
            "variable_name": variable_name,
            "timeout": timeout,
            "use_inner_text": False,  # True = innerText (visible text), False = textContent (all text)
            "strict": False,  # Require exactly one matching element
            "trim_whitespace": True,  # Trim leading/trailing whitespace from result
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

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            variable_name = self.config.get("variable_name", "extracted_text")
            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000
            use_inner_text = self.config.get("use_inner_text", False)
            trim_whitespace = self.config.get("trim_whitespace", True)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")

            logger.info(f"Extracting text from element: {normalized_selector} (use_inner_text={use_inner_text})")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for extract text: {selector}")

                    # Use locator API for better timeout support
                    locator = page.locator(normalized_selector)

                    # Apply strict mode if configured
                    if self.config.get("strict", False):
                        locator = locator.first  # Ensures exactly one element

                    # Extract text using appropriate method
                    if use_inner_text:
                        # innerText returns visible text only (respects CSS display/visibility)
                        text = await locator.inner_text(timeout=timeout)
                    else:
                        # textContent returns all text including hidden elements
                        text = await locator.text_content(timeout=timeout)

                    # Trim whitespace if configured
                    if trim_whitespace and text:
                        text = text.strip()

                    # Store in variable
                    context.set_variable(variable_name, text)

                    # Set output
                    self.set_output_value("text", text)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Text extracted successfully: {len(text) if text else 0} characters (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "text": text,
                            "variable": variable_name,
                            "use_inner_text": use_inner_text,
                            "attempts": attempts
                        },
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Extract text failed (attempt {attempts}): {e}")
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
                        path = f"extract_text_fail_{timestamp}.png"

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
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
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
            timeout: Timeout in milliseconds
        """
        # Default config with all Playwright get_attribute options
        default_config = {
            "selector": selector,
            "attribute": attribute,
            "variable_name": variable_name,
            "timeout": timeout,
            "strict": False,  # Require exactly one matching element
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

            # Normalize selector to work with Playwright (handles XPath, CSS, ARIA, etc.)
            normalized_selector = normalize_selector(selector)

            variable_name = self.config.get("variable_name", "attribute_value")
            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")

            logger.info(f"Getting attribute '{attribute}' from element: {normalized_selector}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for get attribute: {selector}")

                    # Use locator API for better timeout support
                    locator = page.locator(normalized_selector)

                    # Apply strict mode if configured
                    if self.config.get("strict", False):
                        locator = locator.first  # Ensures exactly one element

                    # Get attribute with timeout
                    value = await locator.get_attribute(attribute, timeout=timeout)

                    # Store in variable
                    context.set_variable(variable_name, value)

                    # Set output
                    self.set_output_value("value", value)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Attribute retrieved successfully: {attribute} = {value} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "attribute": attribute,
                            "value": value,
                            "variable": variable_name,
                            "attempts": attempts
                        },
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Get attribute failed (attempt {attempts}): {e}")
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
                        path = f"get_attribute_fail_{timestamp}.png"

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
        timeout: int = DEFAULT_NODE_TIMEOUT * 1000,
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
            timeout: Timeout in milliseconds
        """
        # Default config with all Playwright screenshot options
        default_config = {
            "file_path": file_path,
            "selector": selector,
            "full_page": full_page,
            "timeout": timeout,
            "type": "png",  # png or jpeg
            "quality": None,  # JPEG quality 0-100 (ignored for PNG)
            "scale": "device",  # css or device
            "animations": "allow",  # allow or disabled
            "omit_background": False,  # Make background transparent (PNG only)
            "caret": "hide",  # hide or initial - whether to hide text caret
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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

            # Clean up and normalize file path
            import os
            from datetime import datetime

            # Remove quotes that might be in the path
            file_path = file_path.strip().strip('"').strip("'")

            # Get the image type for extension
            img_type = self.config.get("type", "png")
            ext = f".{img_type}" if img_type in ("png", "jpeg") else ".png"

            # If path is a directory (ends with separator or is existing dir), auto-generate filename
            if file_path.endswith(os.sep) or file_path.endswith("/") or file_path.endswith("\\"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(file_path, f"screenshot_{timestamp}{ext}")
            elif os.path.isdir(file_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(file_path, f"screenshot_{timestamp}{ext}")

            # Normalize path and ensure it's absolute
            file_path = os.path.normpath(file_path)
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)

            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                logger.info(f"Created directory: {parent_dir}")

            selector = self.config.get("selector")
            full_page = self.config.get("full_page", False)

            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))

            logger.info(f"Taking screenshot: {file_path}")

            # Build screenshot options
            screenshot_options = {"path": file_path, "timeout": timeout}

            # Image type (png or jpeg)
            img_type = self.config.get("type", "png")
            if img_type and img_type in ("png", "jpeg"):
                screenshot_options["type"] = img_type

            # JPEG quality (0-100)
            quality = self.config.get("quality")
            if quality is not None and quality != "" and img_type == "jpeg":
                try:
                    screenshot_options["quality"] = int(quality)
                except (ValueError, TypeError):
                    pass

            # Scale (css or device)
            scale = self.config.get("scale", "device")
            if scale and scale in ("css", "device"):
                screenshot_options["scale"] = scale

            # Animations (allow or disabled)
            animations = self.config.get("animations", "allow")
            if animations and animations in ("allow", "disabled"):
                screenshot_options["animations"] = animations

            # Omit background (PNG transparency)
            if self.config.get("omit_background", False) and img_type == "png":
                screenshot_options["omit_background"] = True

            # Caret visibility (hide or initial)
            caret = self.config.get("caret", "hide")
            if caret and caret in ("hide", "initial"):
                screenshot_options["caret"] = caret

            logger.debug(f"Screenshot options: {screenshot_options}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for screenshot")

                    # Take screenshot
                    if selector:
                        # Normalize selector for Playwright
                        normalized_selector = normalize_selector(selector)
                        locator = page.locator(normalized_selector)
                        # For element screenshots, remove options not supported by locator.screenshot
                        element_options = {k: v for k, v in screenshot_options.items()
                                           if k in ("path", "timeout", "type", "quality", "scale",
                                                    "animations", "omit_background", "caret")}
                        await locator.screenshot(**element_options)
                    else:
                        screenshot_options["full_page"] = full_page
                        await page.screenshot(**screenshot_options)

                    # Set output
                    self.set_output_value("file_path", file_path)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Screenshot saved: {file_path} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "file_path": file_path,
                            "full_page": full_page,
                            "element": selector is not None,
                            "type": img_type,
                            "attempts": attempts
                        },
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Screenshot failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

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

