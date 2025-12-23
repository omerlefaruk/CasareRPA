"""
Vision Element Finder - AI-powered element location using vision models.

Uses GPT-4V or Claude Vision to find UI elements by natural language description.
Serves as Tier 4 fallback in the healing chain when CV-based methods fail.

Usage:
    finder = VisionElementFinder()

    location = await finder.find_element(
        screenshot=screenshot_bytes,
        description="the blue login button in the top right",
        model="gpt-4o"
    )

    if location.found:
        await page.mouse.click(location.center_x, location.center_y)
"""

from __future__ import annotations

import base64
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMResourceManager,
    )


@dataclass
class ElementLocation:
    """
    Result of vision-based element finding.

    Contains bounding box coordinates and confidence score.
    """

    found: bool
    """Whether an element matching the description was found."""

    x: int = 0
    """X coordinate of bounding box top-left."""

    y: int = 0
    """Y coordinate of bounding box top-left."""

    width: int = 0
    """Width of bounding box."""

    height: int = 0
    """Height of bounding box."""

    confidence: float = 0.0
    """Model's confidence in the location (0.0 to 1.0)."""

    description_matched: str = ""
    """Description of what the model found."""

    reasoning: str = ""
    """Model's reasoning for the location."""

    model_used: str = ""
    """Model that performed the detection."""

    processing_time_ms: float = 0.0
    """Time taken for inference."""

    error_message: Optional[str] = None
    """Error message if finding failed."""

    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    """Alternative locations if multiple matches found."""

    @property
    def center_x(self) -> int:
        """Center X coordinate for clicking."""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """Center Y coordinate for clicking."""
        return self.y + self.height // 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "found": self.found,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "confidence": self.confidence,
            "description_matched": self.description_matched,
            "reasoning": self.reasoning,
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
            "alternatives": self.alternatives,
        }


# Vision-capable models
VISION_MODELS = {
    "gpt-4o": {"provider": "openai", "supports_vision": True},
    "gpt-4o-mini": {"provider": "openai", "supports_vision": True},
    "gpt-4-turbo": {"provider": "openai", "supports_vision": True},
    "claude-3-5-sonnet-latest": {"provider": "anthropic", "supports_vision": True},
    "claude-3-opus-latest": {"provider": "anthropic", "supports_vision": True},
    "claude-3-haiku-20240307": {"provider": "anthropic", "supports_vision": True},
}


ELEMENT_FINDING_PROMPT = """Analyze this screenshot and find the UI element matching this description:

**Description**: {description}

**Instructions**:
1. Look for the element that best matches the description
2. Return the EXACT pixel coordinates of a bounding box around the element
3. The coordinates should be relative to the top-left corner of the image
4. If multiple elements could match, return the most prominent/likely one
5. Estimate your confidence (0.0-1.0) in the match

**Response Format** (JSON only, no explanation):
{{
    "found": true/false,
    "x": <top-left x>,
    "y": <top-left y>,
    "width": <box width>,
    "height": <box height>,
    "confidence": <0.0-1.0>,
    "description_matched": "<what you found>",
    "reasoning": "<brief explanation>",
    "alternatives": [
        {{"x": ..., "y": ..., "width": ..., "height": ..., "description": "..."}}
    ]
}}

Return ONLY the JSON object, nothing else."""


class VisionElementFinder:
    """
    Find UI elements using vision language models.

    Uses GPT-4V, Claude Vision, or other multimodal models to locate
    elements by natural language description. Useful when:
    - Selectors are broken beyond repair
    - Element has no stable attributes
    - Need to find by visual appearance (color, icon, position)

    Example:
        finder = VisionElementFinder()

        # Find by description
        location = await finder.find_element(
            screenshot=await page.screenshot(),
            description="the green Submit button"
        )

        # Click at found location
        if location.found:
            await page.mouse.click(location.center_x, location.center_y)
    """

    DEFAULT_MODEL = "gpt-4o"
    MAX_RETRIES = 2

    def __init__(
        self,
        llm_manager: Optional[LLMResourceManager] = None,
        default_model: str = DEFAULT_MODEL,
        confidence_threshold: float = 0.6,
        timeout_ms: float = 10000.0,
    ) -> None:
        """
        Initialize vision element finder.

        Args:
            llm_manager: LLM resource manager (created if not provided).
            default_model: Default vision model to use.
            confidence_threshold: Minimum confidence to accept result.
            timeout_ms: Maximum time for vision inference.
        """
        self._llm_manager = llm_manager
        self._default_model = default_model
        self._confidence_threshold = confidence_threshold
        self._timeout_ms = timeout_ms

        logger.debug(
            f"VisionElementFinder initialized "
            f"(model={default_model}, confidence_threshold={confidence_threshold})"
        )

    def _get_llm_manager(self) -> "LLMResourceManager":
        """Get or create LLM resource manager."""
        if self._llm_manager is None:
            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                LLMResourceManager,
            )

            self._llm_manager = LLMResourceManager()
        return self._llm_manager

    async def find_element(
        self,
        screenshot: bytes,
        description: str,
        model: Optional[str] = None,
        context_hint: Optional[str] = None,
    ) -> ElementLocation:
        """
        Find a UI element by natural language description.

        Args:
            screenshot: PNG screenshot bytes.
            description: Natural language description of element to find.
                Examples: "the blue login button", "email input field",
                "hamburger menu icon in the top left"
            model: Vision model to use (default: gpt-4o).
            context_hint: Additional context about the page/app.

        Returns:
            ElementLocation with coordinates and confidence.
        """
        start_time = time.perf_counter()
        model = model or self._default_model

        if model not in VISION_MODELS:
            logger.warning(
                f"Model {model} may not support vision. "
                f"Supported models: {list(VISION_MODELS.keys())}"
            )

        logger.info(f"Vision element finding: '{description}' using {model}")

        try:
            # Build prompt with context
            prompt = ELEMENT_FINDING_PROMPT.format(description=description)
            if context_hint:
                prompt = f"**Page Context**: {context_hint}\n\n{prompt}"

            # Encode screenshot
            image_base64 = base64.b64encode(screenshot).decode("utf-8")

            # Call vision model
            llm = self._get_llm_manager()

            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                ImageContent,
            )

            response = await llm.vision_completion(
                prompt=prompt,
                images=[ImageContent(base64_data=image_base64, media_type="image/png")],
                model=model,
                temperature=0.1,  # Low temperature for precise coordinates
                max_tokens=500,
            )

            # Parse response
            result = self._parse_vision_response(response.content)
            processing_time = (time.perf_counter() - start_time) * 1000

            if result["found"]:
                location = ElementLocation(
                    found=True,
                    x=result.get("x", 0),
                    y=result.get("y", 0),
                    width=result.get("width", 0),
                    height=result.get("height", 0),
                    confidence=result.get("confidence", 0.5),
                    description_matched=result.get("description_matched", description),
                    reasoning=result.get("reasoning", ""),
                    model_used=model,
                    processing_time_ms=processing_time,
                    alternatives=result.get("alternatives", []),
                )

                # Check confidence threshold
                if location.confidence < self._confidence_threshold:
                    logger.warning(
                        f"Vision found element but low confidence: "
                        f"{location.confidence:.2f} < {self._confidence_threshold}"
                    )
                    location.found = False
                    location.error_message = f"Low confidence: {location.confidence:.2f}"
                else:
                    logger.info(
                        f"Vision element found at ({location.center_x}, {location.center_y}) "
                        f"confidence={location.confidence:.2f}"
                    )

                return location

            return ElementLocation(
                found=False,
                error_message=result.get("reasoning", "Element not found"),
                model_used=model,
                processing_time_ms=processing_time,
            )

        except json.JSONDecodeError as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Vision response parsing failed: {e}")
            return ElementLocation(
                found=False,
                error_message=f"Invalid JSON response: {e}",
                model_used=model,
                processing_time_ms=processing_time,
            )
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Vision element finding failed: {e}")
            return ElementLocation(
                found=False,
                error_message=str(e),
                model_used=model,
                processing_time_ms=processing_time,
            )

    def _parse_vision_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from vision model.

        Args:
            content: Raw response content from model.

        Returns:
            Parsed dictionary with element location data.
        """
        content = content.strip()

        # Try to extract JSON from markdown code blocks
        if "```json" in content:
            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
        elif "```" in content:
            match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)

        # Try to find JSON object in response
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        result = json.loads(content)

        # Validate required fields
        if "found" not in result:
            result["found"] = all(key in result for key in ["x", "y", "width", "height"])

        # Ensure coordinates are integers
        for key in ["x", "y", "width", "height"]:
            if key in result:
                result[key] = int(result[key])

        return result

    async def find_elements_batch(
        self,
        screenshot: bytes,
        descriptions: List[str],
        model: Optional[str] = None,
    ) -> List[ElementLocation]:
        """
        Find multiple elements in a single vision call.

        More efficient than calling find_element multiple times as it
        sends only one image to the model.

        Args:
            screenshot: PNG screenshot bytes.
            descriptions: List of element descriptions to find.
            model: Vision model to use.

        Returns:
            List of ElementLocation results, one per description.
        """
        start_time = time.perf_counter()
        model = model or self._default_model

        if len(descriptions) == 1:
            return [await self.find_element(screenshot, descriptions[0], model)]

        logger.info(f"Vision batch finding: {len(descriptions)} elements using {model}")

        try:
            # Build batch prompt
            items = "\n".join(f"{i+1}. {desc}" for i, desc in enumerate(descriptions))
            prompt = f"""Analyze this screenshot and find these UI elements:

{items}

**Response Format** (JSON array):
[
    {{
        "index": 1,
        "found": true/false,
        "x": <top-left x>,
        "y": <top-left y>,
        "width": <box width>,
        "height": <box height>,
        "confidence": <0.0-1.0>,
        "description_matched": "<what you found>"
    }},
    ...
]

Return ONLY the JSON array, nothing else."""

            # Encode screenshot
            image_base64 = base64.b64encode(screenshot).decode("utf-8")

            # Call vision model
            llm = self._get_llm_manager()

            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                ImageContent,
            )

            response = await llm.vision_completion(
                prompt=prompt,
                images=[ImageContent(base64_data=image_base64, media_type="image/png")],
                model=model,
                temperature=0.1,
                max_tokens=1000,
            )

            # Parse batch response
            processing_time = (time.perf_counter() - start_time) * 1000
            results = self._parse_batch_response(response.content, descriptions)

            # Add timing info
            for result in results:
                result.model_used = model
                result.processing_time_ms = processing_time / len(descriptions)

            return results

        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Vision batch finding failed: {e}")
            # Return error results for all descriptions
            return [
                ElementLocation(
                    found=False,
                    error_message=str(e),
                    model_used=model,
                    processing_time_ms=processing_time / len(descriptions),
                )
                for _ in descriptions
            ]

    def _parse_batch_response(
        self,
        content: str,
        descriptions: List[str],
    ) -> List[ElementLocation]:
        """Parse batch vision response."""
        content = content.strip()

        # Extract JSON array
        if "```json" in content:
            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
        elif "```" in content:
            match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)

        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        data = json.loads(content)

        # Map results to descriptions by index
        results: List[ElementLocation] = []
        for i, desc in enumerate(descriptions):
            # Find matching result
            item = next((r for r in data if r.get("index") == i + 1), None)

            if item and item.get("found"):
                results.append(
                    ElementLocation(
                        found=True,
                        x=int(item.get("x", 0)),
                        y=int(item.get("y", 0)),
                        width=int(item.get("width", 0)),
                        height=int(item.get("height", 0)),
                        confidence=item.get("confidence", 0.5),
                        description_matched=item.get("description_matched", desc),
                    )
                )
            else:
                results.append(
                    ElementLocation(
                        found=False,
                        error_message=f"Element not found: {desc}",
                    )
                )

        return results

    async def verify_element(
        self,
        screenshot: bytes,
        description: str,
        expected_location: ElementLocation,
        model: Optional[str] = None,
        tolerance: int = 50,
    ) -> bool:
        """
        Verify an element is still at expected location.

        Useful for confirming an element hasn't moved before clicking.

        Args:
            screenshot: Current screenshot bytes.
            description: Element description.
            expected_location: Previously found location.
            model: Vision model to use.
            tolerance: Pixel tolerance for position match.

        Returns:
            True if element is at expected location (within tolerance).
        """
        current = await self.find_element(screenshot, description, model)

        if not current.found:
            return False

        dx = abs(current.center_x - expected_location.center_x)
        dy = abs(current.center_y - expected_location.center_y)

        return dx <= tolerance and dy <= tolerance


__all__ = [
    "VisionElementFinder",
    "ElementLocation",
    "VISION_MODELS",
]
