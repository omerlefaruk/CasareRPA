"""
CasareRPA - Smart Selector Node

AI-powered selector generation from natural language descriptions.
Uses LLM to analyze page structure and generate robust selectors.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode


@properties(
    PropertyDef(
        "description",
        PropertyType.STRING,
        required=True,
        label="Element Description",
        tooltip="Natural language description of the target element",
        placeholder="the blue submit button in the login form",
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o",
        label="AI Model",
        tooltip="LLM model for selector generation (vision-capable recommended)",
    ),
    PropertyDef(
        "selector_type",
        PropertyType.CHOICE,
        default="css",
        choices=["css", "xpath", "auto"],
        label="Selector Type",
        tooltip="Preferred selector type (auto picks best)",
    ),
    PropertyDef(
        "use_screenshot",
        PropertyType.BOOLEAN,
        default=True,
        label="Use Screenshot",
        tooltip="Include page screenshot for better accuracy",
    ),
    PropertyDef(
        "validate_selector",
        PropertyType.BOOLEAN,
        default=True,
        label="Validate Selector",
        tooltip="Validate selector against current page",
    ),
    PropertyDef(
        "require_unique",
        PropertyType.BOOLEAN,
        default=True,
        label="Require Unique",
        tooltip="Fail if selector matches multiple elements",
    ),
)
@node(category="browser")
class SmartSelectorNode(BrowserBaseNode):
    """
    AI-powered selector generation from natural language.

    Generates CSS and XPath selectors by analyzing the page HTML
    and optional screenshot using an LLM.

    Input Ports:
        - page: Playwright Page instance
        - description: Natural language element description (optional, use param)
        - hints: Additional hints for selector generation

    Output Ports:
        - selector: Generated selector string
        - selector_type: Type of selector (css/xpath)
        - confidence: Confidence score (0.0 to 1.0)
        - element_description: AI's description of matched element
        - alternatives: List of alternative selectors
        - is_unique: Whether selector matches exactly one element
        - page: Pass-through page instance
    """

    # @category: browser
    # @requires: litellm playwright
    # @ports: page, description, hints -> selector, selector_type, confidence, element_description, alternatives, is_unique, page

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Smart Selector node."""
        super().__init__(node_id, config)
        self.name = "Smart Selector"
        self.node_type = "SmartSelectorNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_page_input_port(required=False)
        self.add_input_port("description", DataType.STRING, required=False)
        self.add_input_port("hints", DataType.STRING, required=False)

        # Output ports
        self.add_output_port("selector", DataType.STRING)
        self.add_output_port("selector_type", DataType.STRING)
        self.add_output_port("confidence", DataType.FLOAT)
        self.add_output_port("element_description", DataType.STRING)
        self.add_output_port("alternatives", DataType.LIST)
        self.add_output_port("is_unique", DataType.BOOLEAN)
        self.add_page_output_port()

    async def execute(self, context: Any) -> ExecutionResult:
        """
        Execute smart selector generation.

        Args:
            context: Execution context

        Returns:
            Result with generated selector
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get page
            page = await self.get_page_async(context)

            # Get description (from input port or parameter)
            description = self.get_input_value("description")
            if not description:
                description = self.get_parameter("description", "")
            if not description:
                self.status = NodeStatus.ERROR
                return self.error_result("Element description is required")

            # Resolve variables in description

            # Get parameters
            model = self.get_parameter("model", "gpt-4o")
            selector_type = self.get_parameter("selector_type", "css")
            use_screenshot = self.get_parameter("use_screenshot", True)
            validate = self.get_parameter("validate_selector", True)
            require_unique = self.get_parameter("require_unique", True)

            # Get hints
            hints = self.get_input_value("hints") or ""

            logger.info(f"Generating selector for: {description}")

            # Generate selector
            generated = await self._generate_selector(
                page=page,
                description=description,
                model=model,
                use_screenshot=use_screenshot,
                validate=validate,
                hints=hints,
            )

            # Select appropriate selector type
            if selector_type == "xpath" and generated.xpath_selector:
                selector = generated.xpath_selector
                sel_type = "xpath"
            elif selector_type == "css" and generated.css_selector:
                selector = generated.css_selector
                sel_type = "css"
            elif selector_type == "auto":
                # Prefer CSS, but use XPath if CSS is empty or less confident
                if generated.css_selector:
                    selector = generated.css_selector
                    sel_type = "css"
                elif generated.xpath_selector:
                    selector = generated.xpath_selector
                    sel_type = "xpath"
                else:
                    selector = ""
                    sel_type = "none"
            else:
                selector = generated.css_selector or generated.xpath_selector
                sel_type = "css" if generated.css_selector else "xpath"

            # Check uniqueness requirement
            if require_unique and not generated.is_unique and selector:
                logger.warning(
                    f"Selector matches {generated.matched_elements_count} elements "
                    f"(required unique): {selector}"
                )
                self.status = NodeStatus.ERROR
                return self.error_result(
                    f"Selector is not unique (matches {generated.matched_elements_count} elements)",
                    data={
                        "selector": selector,
                        "matched_count": generated.matched_elements_count,
                    },
                )

            # Set outputs
            self.set_output_value("selector", selector)
            self.set_output_value("selector_type", sel_type)
            self.set_output_value("confidence", generated.confidence)
            self.set_output_value("element_description", generated.element_description)
            self.set_output_value("alternatives", generated.alternatives)
            self.set_output_value("is_unique", generated.is_unique)
            self.set_output_value("page", page)

            logger.info(
                f"Smart selector generated: {selector} "
                f"(type={sel_type}, confidence={generated.confidence:.1%})"
            )

            self.status = NodeStatus.SUCCESS
            return self.success_result(
                data={
                    "selector": selector,
                    "selector_type": sel_type,
                    "confidence": generated.confidence,
                    "is_unique": generated.is_unique,
                }
            )

        except ImportError as e:
            logger.error(f"LLM dependencies not available: {e}")
            self.status = NodeStatus.ERROR
            return self.error_result(f"LLM dependencies not available: {e}")

        except Exception as e:
            logger.error(f"Smart selector generation failed: {e}")
            self.status = NodeStatus.ERROR
            return self.error_result(str(e))

    async def _generate_selector(
        self,
        page: Any,
        description: str,
        model: str,
        use_screenshot: bool,
        validate: bool,
        hints: str,
    ) -> Any:
        """Generate selector using AI."""
        from casare_rpa.infrastructure.ai.smart_selector_generator import (
            SmartSelectorGenerator,
        )

        generator = SmartSelectorGenerator(model=model)

        # Build context
        context: dict[str, Any] = {}
        if hints:
            context["hints"] = hints

        # Get screenshot if enabled
        screenshot: bytes | None = None
        if use_screenshot:
            try:
                screenshot = await page.screenshot(type="png")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

        if validate:
            return await generator.generate_and_validate(
                description=description,
                page=page,
                screenshot=screenshot,
                context=context if context else None,
            )
        else:
            page_html = await page.content()
            context["page_url"] = page.url
            context["page_title"] = await page.title()

            return await generator.generate_selector(
                description=description,
                page_html=page_html,
                screenshot=screenshot,
                context=context if context else None,
            )


@properties(
    PropertyDef(
        "description",
        PropertyType.STRING,
        required=True,
        label="Element Description",
        tooltip="Natural language description of the target element",
        placeholder="the search input field",
    ),
    PropertyDef(
        "option_count",
        PropertyType.INTEGER,
        default=3,
        min_value=1,
        max_value=10,
        label="Option Count",
        tooltip="Number of selector options to generate",
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o",
        label="AI Model",
        tooltip="LLM model for selector generation",
    ),
)
@node(category="browser")
class SmartSelectorOptionsNode(BrowserBaseNode):
    """
    Generate multiple selector options for user selection.

    Generates multiple CSS/XPath selector options that the user
    can choose from, useful for finding the most robust selector.

    Input Ports:
        - page: Playwright Page instance
        - description: Element description (optional, use param)

    Output Ports:
        - options: List of selector option dictionaries
        - best_selector: The best (highest confidence) selector
        - page: Pass-through page instance
    """

    # @category: browser
    # @requires: litellm playwright
    # @ports: page, description -> options, best_selector, page

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Smart Selector Options node."""
        super().__init__(node_id, config)
        self.name = "Smart Selector Options"
        self.node_type = "SmartSelectorOptionsNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port(required=False)
        self.add_input_port("description", DataType.STRING, required=False)

        self.add_output_port("options", DataType.LIST)
        self.add_output_port("best_selector", DataType.STRING)
        self.add_page_output_port()

    async def execute(self, context: Any) -> ExecutionResult:
        """
        Execute selector options generation.

        Args:
            context: Execution context

        Returns:
            Result with selector options
        """
        self.status = NodeStatus.RUNNING

        try:
            page = await self.get_page_async(context)

            description = self.get_input_value("description")
            if not description:
                description = self.get_parameter("description", "")
            if not description:
                self.status = NodeStatus.ERROR
                return self.error_result("Element description is required")

            model = self.get_parameter("model", "gpt-4o")
            option_count = self.get_parameter("option_count", 3)

            logger.info(f"Generating {option_count} selector options for: {description}")

            from casare_rpa.infrastructure.ai.smart_selector_generator import (
                SmartSelectorGenerator,
            )

            generator = SmartSelectorGenerator(model=model)
            options = await generator.generate_multiple_options(
                description=description,
                page=page,
                count=option_count,
            )

            # Convert to dicts
            options_data = [opt.to_dict() for opt in options]
            best_selector = options[0].css_selector if options else ""

            self.set_output_value("options", options_data)
            self.set_output_value("best_selector", best_selector)
            self.set_output_value("page", page)

            logger.info(f"Generated {len(options)} selector options")

            self.status = NodeStatus.SUCCESS
            return self.success_result(
                data={
                    "option_count": len(options),
                    "best_selector": best_selector,
                }
            )

        except Exception as e:
            logger.error(f"Selector options generation failed: {e}")
            self.status = NodeStatus.ERROR
            return self.error_result(str(e))


@properties(
    PropertyDef(
        "original_selector",
        PropertyType.STRING,
        required=True,
        label="Original Selector",
        tooltip="The problematic selector to refine",
    ),
    PropertyDef(
        "description",
        PropertyType.STRING,
        required=True,
        label="Element Description",
        tooltip="Description of the target element",
    ),
    PropertyDef(
        "issue",
        PropertyType.CHOICE,
        default="not unique",
        choices=["not unique", "not found", "wrong element", "unstable"],
        label="Issue Type",
        tooltip="What's wrong with the original selector",
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o",
        label="AI Model",
        tooltip="LLM model for selector refinement",
    ),
)
@node(category="browser")
class RefineSelectorNode(BrowserBaseNode):
    """
    Refine a problematic selector using AI.

    Takes an existing selector that has issues (not unique, not found, etc.)
    and generates a better alternative.

    Input Ports:
        - page: Playwright Page instance
        - original_selector: The problematic selector (optional, use param)
        - description: Element description (optional, use param)

    Output Ports:
        - selector: Refined selector
        - selector_type: Type of selector
        - confidence: Confidence score
        - is_unique: Whether selector is unique
        - page: Pass-through page instance
    """

    # @category: browser
    # @requires: litellm playwright
    # @ports: page, original_selector, description -> selector, selector_type, confidence, is_unique, page

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Refine Selector node."""
        super().__init__(node_id, config)
        self.name = "Refine Selector"
        self.node_type = "RefineSelectorNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port(required=False)
        self.add_input_port("original_selector", DataType.STRING, required=False)
        self.add_input_port("description", DataType.STRING, required=False)

        self.add_output_port("selector", DataType.STRING)
        self.add_output_port("selector_type", DataType.STRING)
        self.add_output_port("confidence", DataType.FLOAT)
        self.add_output_port("is_unique", DataType.BOOLEAN)
        self.add_page_output_port()

    async def execute(self, context: Any) -> ExecutionResult:
        """
        Execute selector refinement.

        Args:
            context: Execution context

        Returns:
            Result with refined selector
        """
        self.status = NodeStatus.RUNNING

        try:
            page = await self.get_page_async(context)

            original_selector = self.get_input_value("original_selector") or self.get_parameter(
                "original_selector", ""
            )
            description = self.get_input_value("description") or self.get_parameter(
                "description", ""
            )

            if not original_selector or not description:
                self.status = NodeStatus.ERROR
                return self.error_result("Both original_selector and description are required")

            model = self.get_parameter("model", "gpt-4o")
            issue = self.get_parameter("issue", "not unique")

            logger.info(f"Refining selector: {original_selector} (issue: {issue})")

            from casare_rpa.infrastructure.ai.smart_selector_generator import (
                SmartSelectorGenerator,
            )

            generator = SmartSelectorGenerator(model=model)
            refined = await generator.refine_selector(
                original_selector=original_selector,
                description=description,
                page=page,
                issue=issue,
            )

            selector = refined.css_selector or refined.xpath_selector
            sel_type = "css" if refined.css_selector else "xpath"

            self.set_output_value("selector", selector)
            self.set_output_value("selector_type", sel_type)
            self.set_output_value("confidence", refined.confidence)
            self.set_output_value("is_unique", refined.is_unique)
            self.set_output_value("page", page)

            logger.info(
                f"Selector refined: {selector} "
                f"(confidence={refined.confidence:.1%}, unique={refined.is_unique})"
            )

            self.status = NodeStatus.SUCCESS
            return self.success_result(
                data={
                    "selector": selector,
                    "selector_type": sel_type,
                    "confidence": refined.confidence,
                    "is_unique": refined.is_unique,
                }
            )

        except Exception as e:
            logger.error(f"Selector refinement failed: {e}")
            self.status = NodeStatus.ERROR
            return self.error_result(str(e))


__all__ = [
    "SmartSelectorNode",
    "SmartSelectorOptionsNode",
    "RefineSelectorNode",
]
