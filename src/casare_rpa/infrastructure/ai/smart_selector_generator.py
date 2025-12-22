"""
CasareRPA - Smart Selector Generator

AI-powered selector generation from natural language descriptions.
Uses LLM to analyze page structure and generate robust selectors.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class GeneratedSelector:
    """
    AI-generated selector with metadata.

    Attributes:
        css_selector: Primary CSS selector
        xpath_selector: Alternative XPath selector
        confidence: Confidence score (0.0 to 1.0)
        element_description: Description of the matched element
        alternatives: List of alternative selectors
        validation_status: Whether selector was validated against DOM
        matched_elements_count: Number of elements matched (should be 1)
    """

    css_selector: str
    xpath_selector: str
    confidence: float
    element_description: str
    alternatives: List[str] = field(default_factory=list)
    validation_status: bool = False
    matched_elements_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "css_selector": self.css_selector,
            "xpath_selector": self.xpath_selector,
            "confidence": self.confidence,
            "element_description": self.element_description,
            "alternatives": self.alternatives,
            "validation_status": self.validation_status,
            "matched_elements_count": self.matched_elements_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GeneratedSelector:
        """Create from dictionary."""
        return cls(
            css_selector=data.get("css_selector", ""),
            xpath_selector=data.get("xpath_selector", ""),
            confidence=data.get("confidence", 0.0),
            element_description=data.get("element_description", ""),
            alternatives=data.get("alternatives", []),
            validation_status=data.get("validation_status", False),
            matched_elements_count=data.get("matched_elements_count", 0),
        )

    @property
    def is_unique(self) -> bool:
        """Check if selector matches exactly one element."""
        return self.matched_elements_count == 1


class SmartSelectorGenerator:
    """
    AI-powered selector generator.

    Generates robust CSS and XPath selectors from natural language
    descriptions by analyzing page HTML and optional screenshots.

    Usage:
        generator = SmartSelectorGenerator()
        selector = await generator.generate_selector(
            description="the blue submit button in the login form",
            page_html=page_html,
            screenshot=screenshot_bytes,
        )
    """

    SYSTEM_PROMPT = """You are an expert web automation selector engineer. Your task is to generate robust, unique CSS and XPath selectors for web elements based on natural language descriptions.

Guidelines for generating selectors:
1. Prefer stable attributes: id, data-testid, data-cy, aria-label, name
2. Avoid fragile attributes: class names that look generated, numeric indices
3. Use semantic selectors when possible: button[type="submit"], input[name="email"]
4. XPath can use text content: //button[contains(text(), 'Submit')]
5. Ensure selectors are unique (match exactly one element)

Respond with a JSON object:
{
    "css_selector": "the primary CSS selector",
    "xpath_selector": "equivalent XPath selector",
    "confidence": 0.0 to 1.0 (how confident you are this is the right element),
    "element_description": "brief description of the element you're targeting",
    "alternatives": ["list", "of", "alternative", "selectors"],
    "reasoning": "why you chose these selectors"
}

If the element cannot be found or description is ambiguous, set confidence to 0 and explain in reasoning."""

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> None:
        """
        Initialize the smart selector generator.

        Args:
            model: LLM model to use (vision-capable for screenshots)
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._llm_manager: Optional[Any] = None

    async def _get_llm_manager(self) -> Any:
        """Get or create LLM resource manager."""
        if self._llm_manager is None:
            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                LLMResourceManager,
                LLMConfig,
                LLMProvider,
            )

            self._llm_manager = LLMResourceManager()

            if "claude" in self._model.lower():
                provider = LLMProvider.ANTHROPIC
            else:
                provider = LLMProvider.OPENAI

            config = LLMConfig(
                provider=provider,
                model=self._model,
            )
            self._llm_manager.configure(config)

        return self._llm_manager

    def _simplify_html(self, html: str, max_length: int = 50000) -> str:
        """
        Simplify HTML to reduce token usage while preserving structure.

        Removes scripts, styles, and excessive whitespace.
        Truncates if still too long.
        """
        # Remove script and style content
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Remove inline styles and event handlers (reduce noise)
        html = re.sub(r'\s+style="[^"]*"', "", html)
        html = re.sub(r"\s+on\w+=\"[^\"]*\"", "", html)

        # Normalize whitespace
        html = re.sub(r"\s+", " ", html)
        html = re.sub(r">\s+<", ">\n<", html)

        # Truncate if needed
        if len(html) > max_length:
            # Try to truncate at a tag boundary
            truncated = html[:max_length]
            last_close = truncated.rfind(">")
            if last_close > max_length - 1000:
                truncated = truncated[: last_close + 1]
            html = truncated + "\n<!-- HTML truncated -->"
            logger.warning(f"HTML truncated from {len(html)} to {max_length} chars")

        return html.strip()

    def _build_generation_prompt(
        self,
        description: str,
        page_html: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the selector generation prompt."""
        simplified_html = self._simplify_html(page_html)

        prompt_parts = [
            "## Selector Generation Request",
            "",
            f"**Target Element Description**: {description}",
        ]

        if context:
            if context.get("page_url"):
                prompt_parts.append(f"**Page URL**: {context['page_url']}")
            if context.get("page_title"):
                prompt_parts.append(f"**Page Title**: {context['page_title']}")
            if context.get("hints"):
                prompt_parts.append(f"**Additional Hints**: {context['hints']}")

        prompt_parts.extend(
            [
                "",
                "**Page HTML**:",
                "```html",
                simplified_html,
                "```",
                "",
                "Generate a unique, robust selector for the described element.",
                "If a screenshot is provided, use visual context to improve accuracy.",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_llm_response(self, response_text: str) -> GeneratedSelector:
        """Parse LLM response into GeneratedSelector."""
        content = response_text.strip()

        # Extract JSON from markdown code blocks
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            content = content[start:end].strip()

        try:
            data = json.loads(content)
            return GeneratedSelector(
                css_selector=data.get("css_selector", ""),
                xpath_selector=data.get("xpath_selector", ""),
                confidence=float(data.get("confidence", 0.0)),
                element_description=data.get("element_description", ""),
                alternatives=data.get("alternatives", []),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return GeneratedSelector(
                css_selector="",
                xpath_selector="",
                confidence=0.0,
                element_description=f"Parse error: {response_text[:200]}",
            )

    async def generate_selector(
        self,
        description: str,
        page_html: str,
        screenshot: Optional[bytes] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> GeneratedSelector:
        """
        Generate selectors from a natural language description.

        Args:
            description: Natural language description of the target element
                e.g., "the submit button in the login form"
            page_html: Current page HTML content
            screenshot: Optional page screenshot bytes (PNG/JPEG)
            context: Optional context dict with page_url, page_title, hints

        Returns:
            GeneratedSelector with CSS and XPath selectors
        """
        try:
            manager = await self._get_llm_manager()
            prompt = self._build_generation_prompt(description, page_html, context)

            if screenshot:
                from casare_rpa.infrastructure.resources.llm_resource_manager import (
                    ImageContent,
                )

                screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")
                images = [
                    ImageContent(
                        base64_data=screenshot_b64,
                        media_type="image/png",
                    )
                ]

                response = await manager.vision_completion(
                    prompt=prompt,
                    images=images,
                    model=self._model,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
            else:
                response = await manager.completion(
                    prompt=prompt,
                    model=self._model,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )

            logger.debug(
                f"Smart selector generated: model={response.model}, "
                f"tokens={response.total_tokens}"
            )

            return self._parse_llm_response(response.content)

        except Exception as e:
            logger.error(f"Smart selector generation failed: {e}")
            return GeneratedSelector(
                css_selector="",
                xpath_selector="",
                confidence=0.0,
                element_description=f"Generation failed: {e}",
            )

    async def generate_and_validate(
        self,
        description: str,
        page: Any,
        screenshot: Optional[bytes] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> GeneratedSelector:
        """
        Generate selectors and validate them against the page.

        Args:
            description: Natural language description
            page: Playwright Page instance for validation
            screenshot: Optional screenshot bytes
            context: Optional context dict

        Returns:
            GeneratedSelector with validation status
        """
        # Get page HTML
        page_html = await page.content()

        # Add page context
        if context is None:
            context = {}
        context["page_url"] = page.url
        context["page_title"] = await page.title()

        # Take screenshot if not provided
        if screenshot is None:
            try:
                screenshot = await page.screenshot(type="png")
            except Exception as e:
                logger.warning(f"Failed to take screenshot: {e}")

        # Generate selector
        selector = await self.generate_selector(
            description=description,
            page_html=page_html,
            screenshot=screenshot,
            context=context,
        )

        # Validate selectors
        if selector.css_selector:
            selector = await self._validate_selector(page, selector)

        return selector

    async def _validate_selector(
        self,
        page: Any,
        selector: GeneratedSelector,
    ) -> GeneratedSelector:
        """Validate generated selector against page DOM."""
        try:
            # Try CSS selector first
            if selector.css_selector:
                elements = await page.query_selector_all(selector.css_selector)
                selector.matched_elements_count = len(elements)
                selector.validation_status = len(elements) == 1

                if not selector.validation_status:
                    logger.warning(
                        f"CSS selector matched {len(elements)} elements "
                        f"(expected 1): {selector.css_selector}"
                    )

                    # Try alternatives
                    for alt in selector.alternatives:
                        try:
                            alt_elements = await page.query_selector_all(alt)
                            if len(alt_elements) == 1:
                                logger.info(f"Alternative selector is unique: {alt}")
                                selector.css_selector = alt
                                selector.matched_elements_count = 1
                                selector.validation_status = True
                                break
                        except Exception:
                            continue

            # Validate XPath as fallback
            if not selector.validation_status and selector.xpath_selector:
                try:
                    xpath_elements = await page.locator(f"xpath={selector.xpath_selector}").all()
                    if len(xpath_elements) == 1:
                        selector.validation_status = True
                        selector.matched_elements_count = 1
                        logger.info("XPath selector validates as unique")
                except Exception as e:
                    logger.warning(f"XPath validation failed: {e}")

        except Exception as e:
            logger.error(f"Selector validation failed: {e}")
            selector.validation_status = False

        return selector

    async def refine_selector(
        self,
        original_selector: str,
        description: str,
        page: Any,
        issue: str = "not unique",
    ) -> GeneratedSelector:
        """
        Refine an existing selector that has issues.

        Args:
            original_selector: The problematic selector
            description: Element description
            page: Playwright Page instance
            issue: Description of the issue (e.g., "not unique", "not found")

        Returns:
            Refined GeneratedSelector
        """
        await page.content()

        context = {
            "page_url": page.url,
            "page_title": await page.title(),
            "hints": f"Original selector '{original_selector}' is {issue}. "
            f"Generate a more specific/robust alternative.",
        }

        return await self.generate_and_validate(
            description=description,
            page=page,
            context=context,
        )

    async def generate_multiple_options(
        self,
        description: str,
        page: Any,
        count: int = 5,
    ) -> List[GeneratedSelector]:
        """
        Generate multiple selector options for user to choose from.

        Args:
            description: Element description
            page: Playwright Page instance
            count: Number of options to generate

        Returns:
            List of GeneratedSelector options
        """
        # Generate primary selector
        primary = await self.generate_and_validate(description, page)
        results = [primary]

        # Generate alternatives by varying the prompt
        variations = [
            f"{description} (prefer data-testid attribute)",
            f"{description} (prefer aria labels)",
            f"{description} (prefer ID selector)",
            f"{description} (use XPath with text content)",
        ]

        for variation in variations[: count - 1]:
            try:
                option = await self.generate_and_validate(variation, page)
                if option.css_selector and option.css_selector != primary.css_selector:
                    results.append(option)
            except Exception as e:
                logger.warning(f"Failed to generate variation: {e}")

        # Sort by confidence and validation status
        results.sort(
            key=lambda x: (x.validation_status, x.confidence),
            reverse=True,
        )

        return results


__all__ = [
    "SmartSelectorGenerator",
    "GeneratedSelector",
]
