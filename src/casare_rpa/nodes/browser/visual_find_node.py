"""
Visual Find Element Node - Find elements using AI vision models.

Uses GPT-4V, Claude Vision, or other multimodal models to locate
UI elements by natural language description.

Usage in workflow:
    1. Connect to browser page
    2. Provide element description (e.g., "blue login button")
    3. Get element location for subsequent actions
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_TIMEOUT,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)


# =============================================================================
# Property Constants
# =============================================================================

ELEMENT_DESCRIPTION = PropertyDef(
    "element_description",
    PropertyType.STRING,
    default="",
    required=True,
    label="Element Description",
    tooltip="Natural language description of the element to find (e.g., 'blue login button')",
    placeholder="the blue Login button in the top right corner",
)

VISION_MODEL = PropertyDef(
    "vision_model",
    PropertyType.CHOICE,
    default="gpt-4o",
    choices=[
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-latest",
    ],
    label="Vision Model",
    tooltip="AI vision model to use for element detection",
)

CONFIDENCE_THRESHOLD = PropertyDef(
    "confidence_threshold",
    PropertyType.NUMBER,
    default=0.6,
    min_value=0.0,
    max_value=1.0,
    label="Confidence Threshold",
    tooltip="Minimum confidence score to accept the result (0.0-1.0)",
)

CONTEXT_HINT = PropertyDef(
    "context_hint",
    PropertyType.STRING,
    default="",
    required=False,
    label="Page Context Hint",
    tooltip="Additional context about the page (e.g., 'login form')",
    placeholder="This is a login page for the admin portal",
    tab="advanced",
)

CLICK_AFTER_FIND = PropertyDef(
    "click_after_find",
    PropertyType.BOOLEAN,
    default=False,
    label="Click After Find",
    tooltip="Automatically click the element after finding it",
)


@node(category="browser")
@properties(
    ELEMENT_DESCRIPTION,
    VISION_MODEL,
    CONFIDENCE_THRESHOLD,
    CONTEXT_HINT,
    CLICK_AFTER_FIND,
    BROWSER_TIMEOUT,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
class VisualFindElementNode(BrowserBaseNode):
    """
    Find UI elements using AI vision models.

    Uses GPT-4V, Claude Vision, or other multimodal models to locate
    elements by natural language description. Useful when:
    - Element has no stable selectors
    - Need to find by visual appearance
    - Selectors keep breaking due to UI changes

    Config (via @properties):
        element_description: Natural language description (required)
        vision_model: AI model to use (default: gpt-4o)
        confidence_threshold: Min confidence (default: 0.6)
        context_hint: Additional page context (optional)
        click_after_find: Auto-click after finding (default: False)

    Inputs:
        page: Browser page instance
        description: Element description override (optional)

    Outputs:
        x: X coordinate of element center
        y: Y coordinate of element center
        width: Element bounding box width
        height: Element bounding box height
        confidence: Detection confidence score
        found: Whether element was found
        page: Passthrough browser page
    """

    # @category: browser
    # @requires: page
    # @ports: page, description -> x, y, width, height, confidence, found, page

    NODE_NAME = "Visual Find Element"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Visual Find Element",
    ):
        super().__init__(node_id, config or {}, name=name)
        self.node_type = "VisualFindElementNode"
        self._vision_finder = None

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Inputs
        self.add_exec_input("exec_in")
        self.add_input_port("page", DataType.PAGE, required=False)
        self.add_input_port("description", DataType.STRING, required=False)

        # Outputs
        self.add_exec_output("exec_out")
        self.add_output_port("x", DataType.INTEGER)
        self.add_output_port("y", DataType.INTEGER)
        self.add_output_port("width", DataType.INTEGER)
        self.add_output_port("height", DataType.INTEGER)
        self.add_output_port("confidence", DataType.NUMBER)
        self.add_output_port("found", DataType.BOOLEAN)
        self.add_output_port("page", DataType.PAGE)

    def _get_vision_finder(self) -> Any:
        """Get or create vision element finder."""
        if self._vision_finder is None:
            try:
                from casare_rpa.infrastructure.ai.vision_element_finder import (
                    VisionElementFinder,
                )

                self._vision_finder = VisionElementFinder()
            except ImportError as e:
                raise ImportError(
                    "VisionElementFinder not available. " "Install with: pip install litellm"
                ) from e
        return self._vision_finder

    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute visual element finding."""
        try:
            # Get page
            page = self.get_page(context)

            # Get description (from port or config)
            description = self.get_input_value("description")
            if not description:
                description = self.get_parameter("element_description", "")

            if not description:
                return self.error_result("Element description is required")

            # Get other parameters
            model = self.get_parameter("vision_model", "gpt-4o")
            confidence_threshold = self.get_parameter("confidence_threshold", 0.6)
            context_hint = self.get_parameter("context_hint", "")
            click_after = self.get_parameter("click_after_find", False)

            logger.info(f"[{self.name}] Finding element: '{description}' using {model}")

            # Get vision finder
            finder = self._get_vision_finder()
            finder._confidence_threshold = confidence_threshold

            # Take screenshot
            screenshot_bytes = await page.screenshot(type="png")

            # Find element
            result = await finder.find_element(
                screenshot=screenshot_bytes,
                description=description,
                model=model,
                context_hint=context_hint if context_hint else None,
            )

            if result.found:
                logger.info(
                    f"[{self.name}] Found element at ({result.center_x}, {result.center_y}) "
                    f"confidence={result.confidence:.2f}"
                )

                # Click if requested
                if click_after:
                    logger.info(f"[{self.name}] Clicking at ({result.center_x}, {result.center_y})")
                    await page.mouse.click(result.center_x, result.center_y)

                self.set_output_value("page", page)

                return self.success_result(
                    {
                        "x": result.center_x,
                        "y": result.center_y,
                        "width": result.width,
                        "height": result.height,
                        "confidence": result.confidence,
                        "found": True,
                        "description_matched": result.description_matched,
                        "reasoning": result.reasoning,
                    }
                )

            # Element not found
            logger.warning(
                f"[{self.name}] Element not found: '{description}' - " f"{result.error_message}"
            )

            # Screenshot on fail
            await self.screenshot_on_failure(page, f"visual_find_{self.node_id}")

            self.set_output_value("page", page)

            return self.success_result(
                {
                    "x": 0,
                    "y": 0,
                    "width": 0,
                    "height": 0,
                    "confidence": 0.0,
                    "found": False,
                    "error": result.error_message,
                }
            )

        except Exception as e:
            logger.error(f"[{self.name}] Visual find failed: {e}")
            return self.error_result(str(e))


# =============================================================================
# Property Export
# =============================================================================

__all__ = [
    "VisualFindElementNode",
    "ELEMENT_DESCRIPTION",
    "VISION_MODEL",
    "CONFIDENCE_THRESHOLD",
    "CONTEXT_HINT",
    "CLICK_AFTER_FIND",
]
