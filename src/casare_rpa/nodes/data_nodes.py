"""
Data extraction nodes for retrieving information from pages.

This module provides nodes for extracting data: text content,
attributes, screenshots, and page information.
"""

import asyncio
from typing import Optional
from pathlib import Path


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
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="CSS or XPath selector for the element",
    ),
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        default="extracted_text",
        label="Variable Name",
        tooltip="Name of variable to store result",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        min_value=0,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
    ),
    PropertyDef(
        "use_inner_text",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Inner Text",
        tooltip="True = innerText (visible text), False = textContent (all text)",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict",
        tooltip="Require exactly one matching element",
    ),
    PropertyDef(
        "trim_whitespace",
        PropertyType.BOOLEAN,
        default=True,
        label="Trim Whitespace",
        tooltip="Trim leading/trailing whitespace from result",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms",
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.STRING,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot",
    ),
)
@executable_node
class ExtractTextNode(BaseNode):
    """
    Extract text node - extracts text content from an element.

    Finds an element and retrieves its text content.

    Config (via @node_schema):
        selector: CSS or XPath selector
        variable_name: Variable name for result
        timeout: Timeout in milliseconds
        use_inner_text: Use innerText vs textContent
        strict: Require exactly one match
        trim_whitespace: Trim whitespace
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Extract Text",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExtractTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
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
            page = self.get_parameter("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            selector = self.get_parameter("selector", "")
            if not selector:
                raise ValueError("Selector is required")

            selector = context.resolve_value(selector)
            normalized_selector = normalize_selector(selector)

            variable_name = self.get_parameter("variable_name", "extracted_text")
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            use_inner_text = self.get_parameter("use_inner_text", False)
            trim_whitespace = self.get_parameter("trim_whitespace", True)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            logger.info(
                f"Extracting text from element: {normalized_selector} (use_inner_text={use_inner_text})"
            )

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for extract text: {selector}"
                        )

                    # Use locator API for better timeout support
                    locator = page.locator(normalized_selector)

                    # Apply strict mode if configured
                    if self.get_parameter("strict", False):
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
                    logger.info(
                        f"Text extracted successfully: {len(text) if text else 0} characters (attempt {attempts})"
                    )

                    return {
                        "success": True,
                        "data": {
                            "text": text,
                            "variable": variable_name,
                            "use_inner_text": use_inner_text,
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
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
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="CSS or XPath selector for the element",
    ),
    PropertyDef(
        "attribute",
        PropertyType.STRING,
        default="",
        label="Attribute",
        tooltip="Attribute name to retrieve",
    ),
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        default="attribute_value",
        label="Variable Name",
        tooltip="Name of variable to store result",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        min_value=0,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict",
        tooltip="Require exactly one matching element",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms",
    ),
    PropertyDef(
        "screenshot_on_fail",
        PropertyType.BOOLEAN,
        default=False,
        label="Screenshot on Fail",
        tooltip="Take screenshot on failure",
    ),
    PropertyDef(
        "screenshot_path",
        PropertyType.STRING,
        default="",
        label="Screenshot Path",
        tooltip="Path for failure screenshot",
    ),
)
@executable_node
class GetAttributeNode(BaseNode):
    """
    Get attribute node - retrieves an attribute value from an element.

    Finds an element and gets the specified attribute value.

    Config (via @node_schema):
        selector: CSS or XPath selector
        attribute: Attribute name to retrieve
        variable_name: Variable name for result
        timeout: Timeout in milliseconds
        strict: Require exactly one match
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Get Attribute",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetAttributeNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("selector", PortType.INPUT, DataType.STRING)
        self.add_input_port("attribute", PortType.INPUT, DataType.STRING)
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
            page = self.get_parameter("page")
            if page is None:
                page = context.get_active_page()

            if page is None:
                raise ValueError("No page instance found")

            selector = self.get_parameter("selector", "")
            if not selector:
                raise ValueError("Selector is required")

            attribute = self.get_parameter("attribute", "")
            if not attribute:
                raise ValueError("Attribute name is required")

            selector = context.resolve_value(selector)
            attribute = context.resolve_value(attribute)
            normalized_selector = normalize_selector(selector)

            variable_name = self.get_parameter("variable_name", "attribute_value")
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            screenshot_on_fail = self.get_parameter("screenshot_on_fail", False)
            screenshot_path = self.get_parameter("screenshot_path", "")

            logger.info(
                f"Getting attribute '{attribute}' from element: {normalized_selector}"
            )

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for get attribute: {selector}"
                        )

                    # Use locator API for better timeout support
                    locator = page.locator(normalized_selector)

                    # Apply strict mode if configured
                    if self.get_parameter("strict", False):
                        locator = locator.first  # Ensures exactly one element

                    # Get attribute with timeout
                    value = await locator.get_attribute(attribute, timeout=timeout)

                    # Store in variable
                    context.set_variable(variable_name, value)

                    # Set output
                    self.set_output_value("value", value)

                    self.status = NodeStatus.SUCCESS
                    logger.info(
                        f"Attribute retrieved successfully: {attribute} = {value} (attempt {attempts})"
                    )

                    return {
                        "success": True,
                        "data": {
                            "attribute": attribute,
                            "value": value,
                            "variable": variable_name,
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Get attribute failed (attempt {attempts}): {e}"
                        )
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
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        default="",
        label="File Path",
        tooltip="Path where screenshot will be saved",
    ),
    PropertyDef(
        "selector",
        PropertyType.STRING,
        default="",
        label="Selector",
        tooltip="Optional selector for element screenshot",
    ),
    PropertyDef(
        "full_page",
        PropertyType.BOOLEAN,
        default=False,
        label="Full Page",
        tooltip="Whether to capture full scrollable page",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=DEFAULT_NODE_TIMEOUT * 1000,
        min_value=0,
        label="Timeout (ms)",
        tooltip="Timeout in milliseconds",
    ),
    PropertyDef(
        "type",
        PropertyType.CHOICE,
        default="png",
        choices=["png", "jpeg"],
        label="Image Type",
        tooltip="Image type: png or jpeg",
    ),
    PropertyDef(
        "quality",
        PropertyType.INTEGER,
        default=None,
        min_value=0,
        max_value=100,
        label="JPEG Quality",
        tooltip="JPEG quality 0-100 (ignored for PNG)",
    ),
    PropertyDef(
        "scale",
        PropertyType.CHOICE,
        default="device",
        choices=["css", "device"],
        label="Scale",
        tooltip="css or device scale",
    ),
    PropertyDef(
        "animations",
        PropertyType.CHOICE,
        default="allow",
        choices=["allow", "disabled"],
        label="Animations",
        tooltip="allow or disabled animations",
    ),
    PropertyDef(
        "omit_background",
        PropertyType.BOOLEAN,
        default=False,
        label="Omit Background",
        tooltip="Make background transparent (PNG only)",
    ),
    PropertyDef(
        "caret",
        PropertyType.CHOICE,
        default="hide",
        choices=["hide", "initial"],
        label="Caret",
        tooltip="hide or initial - whether to hide text caret",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms",
    ),
)
@executable_node
class ScreenshotNode(BaseNode):
    """
    Screenshot node - captures a screenshot of the page or element.

    Takes a screenshot and saves it to a file.

    Config (via @node_schema):
        file_path: Path where screenshot will be saved
        selector: Optional selector for element screenshot
        full_page: Whether to capture full scrollable page
        timeout: Timeout in milliseconds
        type: Image type (png or jpeg)
        quality: JPEG quality 0-100
        scale: css or device scale
        animations: allow or disabled
        omit_background: Make background transparent
        caret: hide or initial
        retry_count: Retry attempts
        retry_interval: Delay between retries
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Screenshot",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ScreenshotNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("page", PortType.INPUT, DataType.PAGE)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
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

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            # Clean up and normalize file path
            import os
            from datetime import datetime

            # Remove quotes that might be in the path
            file_path = file_path.strip().strip('"').strip("'")

            # Get the image type for extension
            img_type = self.config.get("type", "png")
            ext = f".{img_type}" if img_type in ("png", "jpeg") else ".png"

            # If path is a directory (ends with separator or is existing dir), auto-generate filename
            if (
                file_path.endswith(os.sep)
                or file_path.endswith("/")
                or file_path.endswith("\\")
            ):
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

            # Resolve {{variable}} patterns in selector if present
            if selector:
                selector = context.resolve_value(selector)

            # Safely parse timeout with default
            timeout_val = self.config.get("timeout")
            if timeout_val is None or timeout_val == "":
                timeout = DEFAULT_NODE_TIMEOUT * 1000
            else:
                try:
                    timeout = int(timeout_val)
                except (ValueError, TypeError):
                    timeout = DEFAULT_NODE_TIMEOUT * 1000

            # Helper to safely parse int values with defaults
            # Get retry options
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)

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
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for screenshot"
                        )

                    # Take screenshot
                    if selector:
                        # Normalize selector for Playwright
                        normalized_selector = normalize_selector(selector)
                        locator = page.locator(normalized_selector)
                        # For element screenshots, remove options not supported by locator.screenshot
                        element_options = {
                            k: v
                            for k, v in screenshot_options.items()
                            if k
                            in (
                                "path",
                                "timeout",
                                "type",
                                "quality",
                                "scale",
                                "animations",
                                "omit_background",
                                "caret",
                            )
                        }
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
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
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
            return {"success": False, "error": str(e), "next_nodes": []}

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
