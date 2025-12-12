"""
Selector Healing Chain.

Implements the tiered fallback chain for self-healing selectors:
Original -> Heuristic -> Anchor -> CV -> Vision AI

Tiers:
    0. Original: Direct selector (no healing)
    1. Heuristic: Attribute-based fallbacks
    2. Anchor: Spatial relationship healing
    3. CV: Template matching + OCR
    4. Vision: AI vision models (GPT-4V/Claude)

Each tier is attempted in sequence until one succeeds or all fail.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, TYPE_CHECKING

from loguru import logger

from casare_rpa.infrastructure.browser.healing.anchor_healer import AnchorHealer
from casare_rpa.infrastructure.browser.healing.cv_healer import (
    CVContext,
    CVHealer,
    CVHealingResult,
    CVStrategy,
)
from casare_rpa.infrastructure.browser.healing.models import (
    AnchorHealingResult,
    SpatialContext,
)
from casare_rpa.infrastructure.browser.healing.telemetry import (
    HealingTelemetry,
    HealingTier,
    get_healing_telemetry,
)
from casare_rpa.utils.selectors.selector_healing import (
    ElementFingerprint,
    SelectorHealer,
)

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class HealingChainResult:
    """
    Result of the full healing chain attempt.

    Contains the final result and details of each tier's attempt.
    """

    success: bool
    """Whether element was found."""

    original_selector: str
    """The original selector."""

    final_selector: str
    """The selector that worked (or original if failed)."""

    tier_used: HealingTier
    """Which tier succeeded."""

    confidence: float
    """Confidence score of the result."""

    total_time_ms: float
    """Total time for the healing chain."""

    tier_results: Dict[str, Any] = field(default_factory=dict)
    """Results from each tier attempted."""

    element: Optional[Any] = None
    """The located ElementHandle (if found)."""

    @property
    def cv_click_coordinates(self) -> Optional[Tuple[int, int]]:
        """
        Get click coordinates if CV healing was used.

        Returns:
            Tuple of (x, y) coordinates if CV tier succeeded, None otherwise.
        """
        if self.tier_used != HealingTier.CV:
            return None

        cv_result = self.tier_results.get("cv", {})
        if isinstance(cv_result, dict):
            click_x = cv_result.get("click_x")
            click_y = cv_result.get("click_y")
            if click_x is not None and click_y is not None:
                return (click_x, click_y)
        return None

    @property
    def is_cv_result(self) -> bool:
        """Check if this result requires coordinate-based clicking."""
        return self.tier_used == HealingTier.CV and self.element is None


class HealingStrategy(Protocol):
    """Protocol for healing strategy implementations."""

    async def heal(
        self,
        page: Any,
        selector: str,
        **kwargs: Any,
    ) -> Any:
        """Attempt to heal a selector."""
        ...


class SelectorHealingChain:
    """
    Tiered healing chain for self-healing selectors.

    Attempts healing in priority order:
    1. Original selector (no healing)
    2. Heuristic healing (Tier 1) - attribute-based fallbacks
    3. Anchor healing (Tier 2) - spatial relationship based
    4. CV healing (Tier 3) - computer vision (OCR + template)
    5. Vision AI healing (Tier 4) - GPT-4V/Claude Vision

    Example:
        chain = SelectorHealingChain()

        # During recording, capture context
        await chain.capture_element_context(page, "#submit-btn")

        # During playback, use the chain
        result = await chain.locate_element(page, "#submit-btn")
        if result.success:
            await result.element.click()

        # Get statistics
        stats = chain.get_stats()
    """

    # Maximum cache sizes for LRU-style eviction
    MAX_FINGERPRINTS = 500
    MAX_SPATIAL_CONTEXTS = 200
    MAX_CV_CONTEXTS = 100  # Smaller limit due to image data
    MAX_VISION_CONTEXTS = 50  # Even smaller for vision descriptions

    def __init__(
        self,
        heuristic_healer: Optional[SelectorHealer] = None,
        anchor_healer: Optional[AnchorHealer] = None,
        cv_healer: Optional[CVHealer] = None,
        vision_finder: Optional[Any] = None,
        telemetry: Optional[HealingTelemetry] = None,
        healing_budget_ms: float = 400.0,
        cv_budget_ms: float = 2000.0,
        vision_budget_ms: float = 10000.0,
        enable_cv_fallback: bool = False,
        enable_vision_fallback: bool = False,
        vision_model: str = "gpt-4o",
    ) -> None:
        """
        Initialize the healing chain.

        Args:
            heuristic_healer: Tier 1 heuristic healer (created if not provided).
            anchor_healer: Tier 2 anchor healer (created if not provided).
            cv_healer: Tier 3 CV healer (created if not provided when enabled).
            vision_finder: Tier 4 Vision AI finder (created if not provided).
            telemetry: Telemetry collector (global instance if not provided).
            healing_budget_ms: Maximum time budget for Tier 1-2 healing attempts.
            cv_budget_ms: Maximum time budget for Tier 3 CV healing (default 2000ms).
            vision_budget_ms: Maximum time budget for Tier 4 Vision AI (default 10000ms).
            enable_cv_fallback: Whether to enable CV fallback (Tier 3).
            enable_vision_fallback: Whether to enable Vision AI fallback (Tier 4).
            vision_model: Vision model to use (default: gpt-4o).
        """
        self._heuristic_healer = heuristic_healer or SelectorHealer()
        self._anchor_healer = anchor_healer or AnchorHealer()
        self._cv_healer = cv_healer
        self._vision_finder = vision_finder
        self._telemetry = telemetry or get_healing_telemetry()
        self._healing_budget_ms = healing_budget_ms
        self._cv_budget_ms = cv_budget_ms
        self._vision_budget_ms = vision_budget_ms
        self._enable_cv_fallback = enable_cv_fallback
        self._enable_vision_fallback = enable_vision_fallback
        self._vision_model = vision_model

        # Initialize CV healer lazily when enabled
        if enable_cv_fallback and self._cv_healer is None:
            self._cv_healer = CVHealer(budget_ms=cv_budget_ms)

        # Initialize Vision finder lazily when enabled
        if enable_vision_fallback and self._vision_finder is None:
            try:
                from casare_rpa.infrastructure.ai.vision_element_finder import (
                    VisionElementFinder,
                )

                self._vision_finder = VisionElementFinder(
                    default_model=vision_model,
                    timeout_ms=vision_budget_ms,
                )
            except ImportError:
                logger.warning("VisionElementFinder not available")

        # Element fingerprints for heuristic healing
        self._fingerprints: Dict[str, ElementFingerprint] = {}

        # Spatial contexts for anchor healing
        self._spatial_contexts: Dict[str, SpatialContext] = {}

        # CV contexts for computer vision healing
        self._cv_contexts: Dict[str, CVContext] = {}

        # Vision contexts (element descriptions for AI)
        self._vision_contexts: Dict[str, str] = {}

        logger.debug(
            f"SelectorHealingChain initialized (budget={healing_budget_ms}ms, "
            f"cv={enable_cv_fallback}, vision={enable_vision_fallback}, "
            f"cv_budget={cv_budget_ms}ms, vision_budget={vision_budget_ms}ms)"
        )

    def _store_fingerprint(
        self, selector: str, fingerprint: ElementFingerprint
    ) -> None:
        """Store fingerprint with LRU-style eviction when at capacity."""
        if len(self._fingerprints) >= self.MAX_FINGERPRINTS:
            oldest = next(iter(self._fingerprints))
            del self._fingerprints[oldest]
        self._fingerprints[selector] = fingerprint

    def _store_spatial_context(self, selector: str, context: SpatialContext) -> None:
        """Store spatial context with LRU-style eviction when at capacity."""
        if len(self._spatial_contexts) >= self.MAX_SPATIAL_CONTEXTS:
            oldest = next(iter(self._spatial_contexts))
            del self._spatial_contexts[oldest]
        self._spatial_contexts[selector] = context

    def _store_cv_context(self, selector: str, context: CVContext) -> None:
        """Store CV context with LRU-style eviction when at capacity."""
        if len(self._cv_contexts) >= self.MAX_CV_CONTEXTS:
            oldest = next(iter(self._cv_contexts))
            del self._cv_contexts[oldest]
        self._cv_contexts[selector] = context

    def _store_vision_context(self, selector: str, description: str) -> None:
        """Store vision context (element description) with LRU-style eviction."""
        if len(self._vision_contexts) >= self.MAX_VISION_CONTEXTS:
            oldest = next(iter(self._vision_contexts))
            del self._vision_contexts[oldest]
        self._vision_contexts[selector] = description

    def clear_contexts(self) -> None:
        """Clear all cached contexts to free memory."""
        self._fingerprints.clear()
        self._spatial_contexts.clear()
        self._cv_contexts.clear()
        self._vision_contexts.clear()
        logger.debug("Cleared all healing chain contexts")

    async def capture_element_context(
        self,
        page: Page,
        selector: str,
    ) -> bool:
        """
        Capture all healing context for an element.

        Captures both fingerprint (for heuristic healing) and spatial context
        (for anchor healing) in a single pass.

        Args:
            page: Playwright Page object.
            selector: The selector to capture context for.

        Returns:
            True if context was captured successfully.
        """
        try:
            # Capture heuristic fingerprint
            fingerprint = await self._heuristic_healer.capture_fingerprint(
                page, selector
            )
            if fingerprint:
                self._store_fingerprint(selector, fingerprint)
                self._heuristic_healer.store_fingerprint(selector, fingerprint)

            # Capture spatial context for anchor healing
            spatial_context = await self._anchor_healer.capture_spatial_context(
                page, selector
            )
            if spatial_context:
                self._store_spatial_context(selector, spatial_context)
                self._anchor_healer.store_context(selector, spatial_context)

            # Capture CV context if CV fallback is enabled
            cv_context = None
            if self._enable_cv_fallback and self._cv_healer:
                cv_context = await self._cv_healer.capture_cv_context(page, selector)
                if cv_context:
                    self._store_cv_context(selector, cv_context)
                    self._cv_healer.store_context(selector, cv_context)

            # Capture vision context (element description) for Vision AI
            vision_description = None
            if self._enable_vision_fallback:
                vision_description = await self._capture_vision_description(
                    page, selector
                )
                if vision_description:
                    self._store_vision_context(selector, vision_description)

            success = (
                fingerprint is not None
                or spatial_context is not None
                or cv_context is not None
                or vision_description is not None
            )
            if success:
                logger.debug(
                    f"Captured context for {selector}: "
                    f"fingerprint={'yes' if fingerprint else 'no'}, "
                    f"spatial={'yes' if spatial_context else 'no'}, "
                    f"cv={'yes' if cv_context else 'no'}, "
                    f"vision={'yes' if vision_description else 'no'}"
                )
            else:
                logger.warning(f"Failed to capture any context for: {selector}")

            return success

        except Exception as e:
            logger.error(f"Error capturing context for {selector}: {e}")
            return False

    async def locate_element(
        self,
        page: Page,
        selector: str,
        timeout_ms: float = 5000,
        target_tag: Optional[str] = None,
    ) -> HealingChainResult:
        """
        Locate an element using the healing chain.

        Attempts each healing tier until the element is found or all fail.

        Args:
            page: Playwright Page object.
            selector: The original selector.
            timeout_ms: Timeout for initial selector attempt.
            target_tag: Expected tag name for better healing.

        Returns:
            HealingChainResult with the located element or failure details.
        """
        start_time = time.perf_counter()
        tier_results: Dict[str, Any] = {}
        tiers_attempted: List[str] = []

        # Tier 0: Try original selector first
        try:
            element = await page.wait_for_selector(
                selector,
                timeout=min(timeout_ms, 2000),
                state="attached",
            )
            if element:
                total_time = (time.perf_counter() - start_time) * 1000
                self._record_telemetry(
                    selector=selector,
                    page_url=page.url,
                    success=True,
                    tier_used=HealingTier.ORIGINAL,
                    healing_time_ms=0.0,
                    tiers_attempted=["original"],
                )
                return HealingChainResult(
                    success=True,
                    original_selector=selector,
                    final_selector=selector,
                    tier_used=HealingTier.ORIGINAL,
                    confidence=1.0,
                    total_time_ms=total_time,
                    element=element,
                )
        except Exception:
            pass

        tiers_attempted.append("original")
        tier_results["original"] = {"success": False}

        remaining_budget = self._healing_budget_ms - (
            (time.perf_counter() - start_time) * 1000
        )

        # Tier 1: Heuristic healing
        if remaining_budget > 50:
            heuristic_result = await self._try_heuristic_healing(
                page, selector, remaining_budget
            )
            tier_results["heuristic"] = heuristic_result
            tiers_attempted.append("heuristic")

            if heuristic_result.get("success"):
                healed_selector = heuristic_result["healed_selector"]
                element = await self._try_selector(page, healed_selector)

                if element:
                    total_time = (time.perf_counter() - start_time) * 1000
                    self._record_telemetry(
                        selector=selector,
                        page_url=page.url,
                        success=True,
                        tier_used=HealingTier.HEURISTIC,
                        healing_time_ms=total_time,
                        healed_selector=healed_selector,
                        confidence=heuristic_result.get("confidence", 0.8),
                        tiers_attempted=tiers_attempted,
                    )
                    return HealingChainResult(
                        success=True,
                        original_selector=selector,
                        final_selector=healed_selector,
                        tier_used=HealingTier.HEURISTIC,
                        confidence=heuristic_result.get("confidence", 0.8),
                        total_time_ms=total_time,
                        tier_results=tier_results,
                        element=element,
                    )

        remaining_budget = self._healing_budget_ms - (
            (time.perf_counter() - start_time) * 1000
        )

        # Tier 2: Anchor healing
        if remaining_budget > 50:
            anchor_result = await self._try_anchor_healing(page, selector, target_tag)
            tier_results["anchor"] = (
                anchor_result.to_dict()
                if hasattr(anchor_result, "to_dict")
                else anchor_result
            )
            tiers_attempted.append("anchor")

            if isinstance(anchor_result, AnchorHealingResult) and anchor_result.success:
                element = await self._try_selector(page, anchor_result.healed_selector)

                if element:
                    total_time = (time.perf_counter() - start_time) * 1000
                    self._record_telemetry(
                        selector=selector,
                        page_url=page.url,
                        success=True,
                        tier_used=HealingTier.ANCHOR,
                        healing_time_ms=total_time,
                        healed_selector=anchor_result.healed_selector,
                        confidence=anchor_result.confidence,
                        tiers_attempted=tiers_attempted,
                    )
                    return HealingChainResult(
                        success=True,
                        original_selector=selector,
                        final_selector=anchor_result.healed_selector,
                        tier_used=HealingTier.ANCHOR,
                        confidence=anchor_result.confidence,
                        total_time_ms=total_time,
                        tier_results=tier_results,
                        element=element,
                    )

        # Tier 3: CV fallback (computer vision based)
        if self._enable_cv_fallback and self._cv_healer:
            cv_context = self._cv_contexts.get(selector)
            search_text = cv_context.text_content if cv_context else None

            cv_result = await self._try_cv_healing(
                page, selector, search_text, cv_context
            )
            tier_results["cv"] = (
                cv_result.to_dict() if hasattr(cv_result, "to_dict") else cv_result
            )
            tiers_attempted.append("cv")

            if isinstance(cv_result, CVHealingResult) and cv_result.success:
                total_time = (time.perf_counter() - start_time) * 1000
                self._record_telemetry(
                    selector=selector,
                    page_url=page.url,
                    success=True,
                    tier_used=HealingTier.CV,
                    healing_time_ms=total_time,
                    healed_selector=f"cv:({cv_result.click_x},{cv_result.click_y})",
                    confidence=cv_result.confidence,
                    tiers_attempted=tiers_attempted,
                )
                return HealingChainResult(
                    success=True,
                    original_selector=selector,
                    final_selector=f"cv:({cv_result.click_x},{cv_result.click_y})",
                    tier_used=HealingTier.CV,
                    confidence=cv_result.confidence,
                    total_time_ms=total_time,
                    tier_results=tier_results,
                    element=None,  # CV returns coordinates, not element
                    # Store click coordinates in tier_results for caller
                )

        # Tier 4: Vision AI fallback (GPT-4V/Claude Vision)
        if self._enable_vision_fallback and self._vision_finder:
            vision_description = self._vision_contexts.get(selector)

            vision_result = await self._try_vision_healing(
                page, selector, vision_description
            )
            tier_results["vision"] = vision_result
            tiers_attempted.append("vision")

            if vision_result.get("success"):
                total_time = (time.perf_counter() - start_time) * 1000
                click_x = vision_result.get("click_x", 0)
                click_y = vision_result.get("click_y", 0)
                self._record_telemetry(
                    selector=selector,
                    page_url=page.url,
                    success=True,
                    tier_used=HealingTier.VISION,
                    healing_time_ms=total_time,
                    healed_selector=f"vision:({click_x},{click_y})",
                    confidence=vision_result.get("confidence", 0.5),
                    tiers_attempted=tiers_attempted,
                )
                return HealingChainResult(
                    success=True,
                    original_selector=selector,
                    final_selector=f"vision:({click_x},{click_y})",
                    tier_used=HealingTier.VISION,
                    confidence=vision_result.get("confidence", 0.5),
                    total_time_ms=total_time,
                    tier_results=tier_results,
                    element=None,  # Vision returns coordinates, not element
                )

        # All tiers failed
        total_time = (time.perf_counter() - start_time) * 1000
        self._record_telemetry(
            selector=selector,
            page_url=page.url,
            success=False,
            tier_used=HealingTier.FAILED,
            healing_time_ms=total_time,
            tiers_attempted=tiers_attempted,
            error_message="All healing tiers failed",
        )

        logger.warning(
            f"Healing chain failed for: {selector} "
            f"(attempted: {tiers_attempted}, time: {total_time:.1f}ms)"
        )

        return HealingChainResult(
            success=False,
            original_selector=selector,
            final_selector=selector,
            tier_used=HealingTier.FAILED,
            confidence=0.0,
            total_time_ms=total_time,
            tier_results=tier_results,
        )

    async def _try_heuristic_healing(
        self,
        page: Page,
        selector: str,
        budget_ms: float,
    ) -> Dict[str, Any]:
        """
        Attempt Tier 1 heuristic healing.

        Args:
            page: Playwright Page object.
            selector: Original selector.
            budget_ms: Time budget in milliseconds.

        Returns:
            Dictionary with healing result.
        """
        try:
            fingerprint = self._fingerprints.get(selector)
            result = await self._heuristic_healer.heal(page, selector, fingerprint)

            return {
                "success": result.success,
                "healed_selector": result.healed_selector,
                "confidence": result.confidence,
                "strategy": result.strategy_used,
            }

        except Exception as e:
            logger.debug(f"Heuristic healing failed for {selector}: {e}")
            return {"success": False, "error": str(e)}

    async def _try_anchor_healing(
        self,
        page: Page,
        selector: str,
        target_tag: Optional[str] = None,
    ) -> AnchorHealingResult:
        """
        Attempt Tier 2 anchor healing.

        Args:
            page: Playwright Page object.
            selector: Original selector.
            target_tag: Expected tag name.

        Returns:
            AnchorHealingResult.
        """
        try:
            context = self._spatial_contexts.get(selector)
            return await self._anchor_healer.heal(
                page, selector, context=context, target_tag=target_tag
            )

        except Exception as e:
            logger.debug(f"Anchor healing failed for {selector}: {e}")
            return AnchorHealingResult(
                success=False,
                original_selector=selector,
                healed_selector="",
                confidence=0.0,
                strategy="anchor-error",
            )

    async def _try_cv_healing(
        self,
        page: Page,
        selector: str,
        search_text: Optional[str] = None,
        context: Optional[CVContext] = None,
    ) -> CVHealingResult:
        """
        Attempt Tier 3 CV healing using computer vision.

        Uses OCR text detection and template matching as last-resort healing.
        Slower than DOM-based tiers but can handle major UI changes.

        Args:
            page: Playwright Page object.
            selector: Original selector.
            search_text: Text to search for using OCR.
            context: CV context with template and position data.

        Returns:
            CVHealingResult with click coordinates or failure details.
        """
        if not self._cv_healer:
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.OCR_TEXT,
                confidence=0.0,
                error_message="CV healer not initialized",
            )

        try:
            result = await self._cv_healer.heal(
                page=page,
                selector=selector,
                search_text=search_text,
                context=context,
            )
            return result

        except Exception as e:
            logger.error(f"CV healing failed for {selector}: {e}")
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.OCR_TEXT,
                confidence=0.0,
                error_message=str(e),
            )

    async def _try_vision_healing(
        self,
        page: Page,
        selector: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Attempt Tier 4 Vision AI healing using GPT-4V/Claude Vision.

        Uses vision language models to find elements by natural language
        description. Most expensive but can handle arbitrary UI changes.

        Args:
            page: Playwright Page object.
            selector: Original selector.
            description: Natural language description of the element.

        Returns:
            Dictionary with healing result including coordinates.
        """
        if not self._vision_finder:
            return {
                "success": False,
                "error": "Vision finder not initialized",
            }

        try:
            # Build description from context if not provided
            effective_description = description
            if not effective_description:
                # Try to extract description from selector
                effective_description = self._selector_to_description(selector)

            if not effective_description:
                return {
                    "success": False,
                    "error": "No element description available",
                }

            # Take screenshot
            screenshot_bytes = await page.screenshot(type="png")

            # Use vision finder
            result = await self._vision_finder.find_element(
                screenshot=screenshot_bytes,
                description=effective_description,
                model=self._vision_model,
            )

            if result.found:
                logger.info(
                    f"Vision healing succeeded for {selector}: "
                    f"({result.center_x}, {result.center_y}) "
                    f"confidence={result.confidence:.2f}"
                )
                return {
                    "success": True,
                    "click_x": result.center_x,
                    "click_y": result.center_y,
                    "confidence": result.confidence,
                    "description_matched": result.description_matched,
                    "reasoning": result.reasoning,
                    "processing_time_ms": result.processing_time_ms,
                }

            return {
                "success": False,
                "error": result.error_message or "Element not found",
                "processing_time_ms": result.processing_time_ms,
            }

        except Exception as e:
            logger.error(f"Vision healing failed for {selector}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _selector_to_description(self, selector: str) -> Optional[str]:
        """
        Convert a CSS/XPath selector to a natural language description.

        Args:
            selector: CSS or XPath selector string.

        Returns:
            Natural language description, or None if cannot convert.
        """
        # Extract meaningful parts from selector
        description_parts = []

        # Handle ID selectors
        if "#" in selector:
            import re

            match = re.search(r"#([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            if match:
                id_name = match.group(1).replace("-", " ").replace("_", " ")
                description_parts.append(f"element with id '{id_name}'")

        # Handle class selectors
        if "." in selector:
            import re

            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            if classes:
                class_names = ", ".join(c.replace("-", " ") for c in classes[:3])
                description_parts.append(f"element with class '{class_names}'")

        # Handle button/input types
        if "button" in selector.lower():
            description_parts.append("button")
        elif "input" in selector.lower():
            description_parts.append("input field")
        elif "submit" in selector.lower():
            description_parts.append("submit button")
        elif "login" in selector.lower():
            description_parts.append("login button")

        # Handle text content selectors
        if "text=" in selector.lower() or ":has-text" in selector:
            import re

            match = re.search(r'(?:text=|:has-text\(["\'])([^"\']+)', selector)
            if match:
                text = match.group(1)
                description_parts.append(f"element containing text '{text}'")

        if description_parts:
            return " ".join(description_parts)

        return None

    async def _capture_vision_description(
        self,
        page: Page,
        selector: str,
    ) -> Optional[str]:
        """
        Capture a natural language description of an element for vision healing.

        Args:
            page: Playwright Page object.
            selector: Selector for the target element.

        Returns:
            Natural language description, or None if element not found.
        """
        try:
            element = await page.query_selector(selector)
            if not element:
                return None

            # Extract element properties for description
            properties = await element.evaluate(
                """el => {
                    return {
                        tag: el.tagName.toLowerCase(),
                        text: (el.textContent || '').trim().slice(0, 50),
                        type: el.getAttribute('type'),
                        placeholder: el.getAttribute('placeholder'),
                        value: el.value,
                        ariaLabel: el.getAttribute('aria-label'),
                        title: el.getAttribute('title'),
                        className: el.className,
                        id: el.id
                    };
                }"""
            )

            # Build description from properties
            parts = []

            # Tag-based description
            tag = properties.get("tag", "")
            if tag == "button":
                parts.append("button")
            elif tag == "input":
                input_type = properties.get("type", "text")
                parts.append(f"{input_type} input field")
            elif tag == "a":
                parts.append("link")
            elif tag == "select":
                parts.append("dropdown")
            elif tag == "textarea":
                parts.append("text area")
            else:
                parts.append(f"{tag} element")

            # Add text content
            text = properties.get("text", "")
            if text:
                parts.append(f"with text '{text}'")

            # Add placeholder
            placeholder = properties.get("placeholder")
            if placeholder:
                parts.append(f"placeholder '{placeholder}'")

            # Add aria-label
            aria_label = properties.get("ariaLabel")
            if aria_label:
                parts.append(f"labeled '{aria_label}'")

            # Add ID/class hints
            elem_id = properties.get("id")
            if elem_id:
                parts.append(f"(id: {elem_id})")

            description = " ".join(parts)
            logger.debug(f"Captured vision description for {selector}: {description}")
            return description

        except Exception as e:
            logger.debug(f"Failed to capture vision description for {selector}: {e}")
            return self._selector_to_description(selector)

    async def _try_selector(
        self,
        page: Page,
        selector: str,
    ) -> Optional[Any]:
        """
        Try to locate an element with a selector.

        Args:
            page: Playwright Page object.
            selector: Selector to try.

        Returns:
            ElementHandle if found, None otherwise.
        """
        try:
            element = await page.query_selector(selector)
            return element
        except Exception:
            return None

    def _record_telemetry(
        self,
        selector: str,
        page_url: str,
        success: bool,
        tier_used: HealingTier,
        healing_time_ms: float,
        healed_selector: Optional[str] = None,
        confidence: float = 1.0,
        tiers_attempted: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a healing event to telemetry."""
        self._telemetry.record_event(
            selector=selector,
            page_url=page_url,
            success=success,
            tier_used=tier_used,
            healing_time_ms=healing_time_ms,
            healed_selector=healed_selector,
            confidence=confidence,
            tiers_attempted=tiers_attempted,
            error_message=error_message,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get healing chain statistics."""
        return self._telemetry.get_overall_stats()

    def get_tier_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get per-tier statistics."""
        return self._telemetry.get_tier_stats()

    def get_problematic_selectors(
        self,
        min_uses: int = 5,
        max_success_rate: float = 0.8,
    ) -> List[Any]:
        """Get selectors that frequently need healing."""
        return self._telemetry.get_problematic_selectors(min_uses, max_success_rate)

    def export_report(self) -> Dict[str, Any]:
        """Export comprehensive healing report."""
        return self._telemetry.export_report()

    @property
    def healing_budget_ms(self) -> float:
        """Get healing time budget."""
        return self._healing_budget_ms

    @healing_budget_ms.setter
    def healing_budget_ms(self, value: float) -> None:
        """Set healing time budget."""
        self._healing_budget_ms = max(50.0, value)


# Convenience function for creating configured chain
def create_healing_chain(
    healing_budget_ms: float = 400.0,
    cv_budget_ms: float = 2000.0,
    vision_budget_ms: float = 10000.0,
    enable_cv: bool = False,
    enable_vision: bool = False,
    vision_model: str = "gpt-4o",
) -> SelectorHealingChain:
    """
    Create a configured healing chain.

    Args:
        healing_budget_ms: Maximum time for Tier 1-2 healing attempts.
        cv_budget_ms: Maximum time for Tier 3 CV healing (default 2000ms).
        vision_budget_ms: Maximum time for Tier 4 Vision AI (default 10000ms).
        enable_cv: Whether to enable CV fallback (Tier 3).
        enable_vision: Whether to enable Vision AI fallback (Tier 4).
        vision_model: Vision model to use (gpt-4o, claude-3-5-sonnet-latest, etc.).

    Returns:
        Configured SelectorHealingChain instance.
    """
    return SelectorHealingChain(
        healing_budget_ms=healing_budget_ms,
        cv_budget_ms=cv_budget_ms,
        vision_budget_ms=vision_budget_ms,
        enable_cv_fallback=enable_cv,
        enable_vision_fallback=enable_vision,
        vision_model=vision_model,
    )


__all__ = [
    "HealingChainResult",
    "SelectorHealingChain",
    "create_healing_chain",
]
