"""
Data extraction nodes for retrieving information from pages.

This module provides nodes for extracting data: text content,
attributes, screenshots, and page information.

All nodes extend BrowserBaseNode for consistent patterns:
- Page access from context
- Selector normalization
- Retry logic
- Screenshot on failure
"""

import os
from datetime import datetime
from pathlib import Path

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
# ExtractTextNode
# =============================================================================


@properties(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Element Selector",
        tooltip="CSS or XPath selector for the element",
        placeholder="#content or //p[@class='text']",
    ),
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        default="extracted_text",
        label="Variable Name",
        tooltip="Name of variable to store result",
    ),
    BROWSER_TIMEOUT,
    PropertyDef(
        "use_inner_text",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Inner Text",
        tooltip="True = innerText (visible text), False = textContent (all text)",
    ),
    BROWSER_SELECTOR_STRICT,
    PropertyDef(
        "trim_whitespace",
        PropertyType.BOOLEAN,
        default=True,
        label="Trim Whitespace",
        tooltip="Trim leading/trailing whitespace from result",
    ),
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_ANCHOR_CONFIG,
)
@node(category="browser")
class ExtractTextNode(BrowserBaseNode):
    """
    Extract text node - extracts text content from an element.

    Finds an element and retrieves its text content.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

    Config (via @properties):
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

    Inputs:
        page: Browser page instance
        selector: Element selector override

    Outputs:
        text: Extracted text content
    """

    # @category: data
    # @requires: none
    # @ports: none -> text

    def __init__(
        self,
        node_id: str,
        name: str = "Extract Text",
        **kwargs,
    ) -> None:
        """Initialize extract text node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "ExtractTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port()
        self.add_selector_input_port()
        self.add_output_port("text", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute text extraction."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get extraction-specific parameters
            variable_name = self.get_parameter("variable_name", "extracted_text")
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            use_inner_text = self.get_parameter("use_inner_text", False)
            trim_whitespace = self.get_parameter("trim_whitespace", True)
            strict = self.get_parameter("strict", False)

            logger.info(
                f"Extracting text from element: {selector} (use_inner_text={use_inner_text})"
            )

            # Track healing info
            healing_tier = "original"
            final_selector = selector

            async def perform_extraction() -> str:
                nonlocal healing_tier, final_selector

                # Try with healing fallback first
                try:
                    (
                        element,
                        final_selector,
                        healing_tier,
                    ) = await self.find_element_with_healing(
                        page, selector, timeout, param_name="selector"
                    )

                    # Use element-based operations
                    if use_inner_text:
                        text = await element.inner_text()
                    else:
                        text = await element.text_content()

                except Exception as healing_error:
                    # Fall back to locator-based operations (original behavior)
                    logger.debug(f"Healing failed, trying direct locator: {healing_error}")
                    locator = page.locator(selector)
                    if strict:
                        locator = locator.first

                    if use_inner_text:
                        text = await locator.inner_text(timeout=timeout)
                    else:
                        text = await locator.text_content(timeout=timeout)

                if trim_whitespace and text:
                    text = text.strip()

                return text or ""

            result = await retry_operation(
                perform_extraction,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"extract text from {selector}",
            )

            if result.success:
                text = result.value
                context.set_variable(variable_name, text)
                self.set_output_value("text", text)

                result_data = {
                    "text": text,
                    "variable": variable_name,
                    "final_selector": final_selector,
                    "use_inner_text": use_inner_text,
                    "attempts": result.attempts,
                    "healing_tier": healing_tier,
                }
                if healing_tier != "original":
                    logger.info(f"Extract text succeeded with healing: {healing_tier} tier")
                return self.success_result(result_data)

            await self.screenshot_on_failure(page, "extract_text_fail")
            raise result.last_error or RuntimeError("Extract text failed")

        except Exception as e:
            return self.error_result(e)


# =============================================================================
# GetAttributeNode
# =============================================================================


@properties(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Element Selector",
        tooltip="CSS or XPath selector for the element",
        placeholder="#element or //a[@class='link']",
    ),
    PropertyDef(
        "attribute",
        PropertyType.STRING,
        default="",
        label="Attribute",
        tooltip="Attribute name to retrieve (e.g., href, src, data-id)",
    ),
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        default="attribute_value",
        label="Variable Name",
        tooltip="Name of variable to store result",
    ),
    BROWSER_TIMEOUT,
    BROWSER_SELECTOR_STRICT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_ANCHOR_CONFIG,
)
@node(category="browser")
class GetAttributeNode(BrowserBaseNode):
    """
    Get attribute node - retrieves an attribute value from an element.

    Finds an element and gets the specified attribute value.
    Extends BrowserBaseNode for shared page/selector/retry patterns.

    Config (via @properties):
        selector: CSS or XPath selector
        attribute: Attribute name to retrieve
        variable_name: Variable name for result
        timeout: Timeout in milliseconds
        strict: Require exactly one match
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot

    Inputs:
        page: Browser page instance
        selector: Element selector override
        attribute: Attribute name override

    Outputs:
        value: Attribute value
    """

    # @category: data
    # @requires: none
    # @ports: attribute -> value

    def __init__(
        self,
        node_id: str,
        name: str = "Get Attribute",
        **kwargs,
    ) -> None:
        """Initialize get attribute node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "GetAttributeNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port()
        self.add_selector_input_port()
        self.add_input_port("attribute", DataType.STRING)
        self.add_output_port("value", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute attribute retrieval."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)

            # Get attribute name
            attribute = self.get_parameter("attribute", "")
            if not attribute:
                raise ValueError("Attribute name is required")

            # Get other parameters
            variable_name = self.get_parameter("variable_name", "attribute_value")
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )
            strict = self.get_parameter("strict", False)

            logger.info(f"Getting attribute '{attribute}' from element: {selector}")

            # Track healing info
            healing_tier = "original"
            final_selector = selector

            async def perform_get_attribute() -> str:
                nonlocal healing_tier, final_selector

                # Try with healing fallback first
                try:
                    (
                        element,
                        final_selector,
                        healing_tier,
                    ) = await self.find_element_with_healing(
                        page, selector, timeout, param_name="selector"
                    )

                    # Special case: "value" attribute on input elements needs input_value()
                    # because get_attribute("value") returns the initial HTML value, not current
                    if attribute.lower() == "value":
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        if tag_name in ("input", "textarea", "select"):
                            value = await element.input_value()
                            return value or ""

                    # Use element-based operation for other attributes
                    value = await element.get_attribute(attribute)
                    return value or ""

                except Exception as healing_error:
                    # Fall back to locator-based operation (original behavior)
                    logger.debug(f"Healing failed, trying direct locator: {healing_error}")
                    locator = page.locator(selector)
                    if strict:
                        locator = locator.first

                    # Special case for value attribute on input elements
                    if attribute.lower() == "value":
                        try:
                            value = await locator.input_value(timeout=timeout)
                            return value or ""
                        except Exception:
                            pass  # Fall through to get_attribute

                    value = await locator.get_attribute(attribute, timeout=timeout)
                    return value or ""

            result = await retry_operation(
                perform_get_attribute,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"get attribute {attribute} from {selector}",
            )

            if result.success:
                value = result.value
                context.set_variable(variable_name, value)
                self.set_output_value("value", value)

                result_data = {
                    "attribute": attribute,
                    "value": value,
                    "variable": variable_name,
                    "final_selector": final_selector,
                    "attempts": result.attempts,
                    "healing_tier": healing_tier,
                }
                if healing_tier != "original":
                    logger.info(f"Get attribute succeeded with healing: {healing_tier} tier")
                return self.success_result(result_data)

            await self.screenshot_on_failure(page, "get_attribute_fail")
            raise result.last_error or RuntimeError("Get attribute failed")

        except Exception as e:
            return self.error_result(e)


# =============================================================================
# ScreenshotNode
# =============================================================================


@properties(
    PropertyDef(
        "file_path",
        PropertyType.FILE_PATH,
        default="",
        label="File Path",
        tooltip="Path where screenshot will be saved",
        placeholder="screenshots/capture.png",
    ),
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=False,
        label="Element Selector",
        tooltip="Optional selector for element screenshot",
        placeholder="#element or leave empty for full page",
    ),
    PropertyDef(
        "full_page",
        PropertyType.BOOLEAN,
        default=False,
        label="Full Page",
        tooltip="Whether to capture full scrollable page",
    ),
    BROWSER_TIMEOUT,
    PropertyDef(
        "type",
        PropertyType.CHOICE,
        default="png",
        choices=["png", "jpeg"],
        label="Image Type",
        tooltip="Image format: png or jpeg",
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
        tooltip="Image scale: css or device",
    ),
    PropertyDef(
        "animations",
        PropertyType.CHOICE,
        default="allow",
        choices=["allow", "disabled"],
        label="Animations",
        tooltip="Allow or disable animations during capture",
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
        tooltip="Whether to hide text caret",
    ),
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
)
@node(category="browser")
class ScreenshotNode(BrowserBaseNode):
    """
    Screenshot node - captures a screenshot of the page or element.

    Takes a screenshot and saves it to a file.
    Extends BrowserBaseNode for shared page/retry patterns.

    Config (via @properties):
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

    Inputs:
        page: Browser page instance
        file_path: Screenshot file path override

    Outputs:
        file_path: Path where screenshot was saved
        attachment_file: List containing file path (for attachments)
    """

    # @category: data
    # @requires: none
    # @ports: file_path -> file_path, attachment_file

    def __init__(
        self,
        node_id: str,
        name: str = "Screenshot",
        **kwargs,
    ) -> None:
        """Initialize screenshot node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "ScreenshotNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port()
        self.add_input_port("file_path", DataType.STRING)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("attachment_file", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute screenshot capture."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get file path
            file_path = self.get_parameter("file_path", "")
            if not file_path:
                raise ValueError("File path is required")
            file_path = self._normalize_file_path(file_path)

            # Get screenshot options
            selector = self.get_optional_normalized_selector(context)
            full_page = self.get_parameter("full_page", False)
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )

            logger.info(f"Taking screenshot: {file_path}")

            # Build screenshot options
            screenshot_options = self._build_screenshot_options(timeout)

            async def perform_screenshot() -> str:
                if selector:
                    locator = page.locator(selector)
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
                return file_path

            result = await retry_operation(
                perform_screenshot,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name="screenshot capture",
            )

            if result.success:
                self.set_output_value("file_path", file_path)
                self.set_output_value("attachment_file", [file_path])

                img_type = self.get_parameter("type", "png")
                return self.success_result(
                    {
                        "file_path": file_path,
                        "full_page": full_page,
                        "element": bool(selector),
                        "type": img_type,
                        "attempts": result.attempts,
                    }
                )

            raise result.last_error or RuntimeError("Screenshot failed")

        except Exception as e:
            return self.error_result(e)

    def _normalize_file_path(self, file_path: str) -> str:
        """Normalize and prepare the screenshot file path."""
        file_path = file_path.strip().strip('"').strip("'")

        img_type = self.get_parameter("type", "png")
        ext = f".{img_type}" if img_type in ("png", "jpeg") else ".png"

        # If path is a directory, auto-generate filename
        if file_path.endswith(os.sep) or file_path.endswith("/") or file_path.endswith("\\"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(file_path, f"screenshot_{timestamp}{ext}")
        elif os.path.isdir(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(file_path, f"screenshot_{timestamp}{ext}")

        file_path = os.path.normpath(file_path)
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        # Create parent directory
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            logger.info(f"Created directory: {parent_dir}")

        return file_path

    def _build_screenshot_options(self, timeout: int) -> dict:
        """Build Playwright screenshot options dictionary."""
        file_path = self.get_parameter("file_path", "")
        file_path = file_path.strip().strip('"').strip("'")
        file_path = self._normalize_file_path(file_path)

        options: dict = {"path": file_path, "timeout": timeout}

        img_type = self.get_parameter("type", "png")
        if img_type in ("png", "jpeg"):
            options["type"] = img_type

        quality = self.get_parameter("quality")
        if quality is not None and quality != "" and img_type == "jpeg":
            try:
                options["quality"] = int(quality)
            except (ValueError, TypeError):
                pass

        scale = self.get_parameter("scale", "device")
        if scale in ("css", "device"):
            options["scale"] = scale

        animations = self.get_parameter("animations", "allow")
        if animations in ("allow", "disabled"):
            options["animations"] = animations

        if self.get_parameter("omit_background", False) and img_type == "png":
            options["omit_background"] = True

        caret = self.get_parameter("caret", "hide")
        if caret in ("hide", "initial"):
            options["caret"] = caret

        return options

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        file_path = self.get_parameter("file_path", "")
        if file_path:
            try:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Invalid file path: {e}"
        return True, ""
