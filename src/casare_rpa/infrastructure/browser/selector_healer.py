"""
CasareRPA - Infrastructure: Heuristic Selector Healer

Tier 1 healing: Multi-attribute selector fallback.
Tries fallback attributes in priority order leveraging Playwright's built-in resilience.

Performance target: <400ms for tier 1 (40% of 1s total budget).
"""

import asyncio
import time
from typing import Optional
from loguru import logger

try:
    from playwright.async_api import (
        Page,
        Locator,
        TimeoutError as PlaywrightTimeoutError,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - selector healing disabled")

from casare_rpa.domain.value_objects.selector import SmartSelector, SelectorStrategy
from casare_rpa.domain.value_objects.healing_event import (
    HealingEvent,
    HealingTier,
    create_healing_event,
)


class HeuristicSelectorHealer:
    """
    Tier 1 selector healing using multi-attribute fallback.

    Tries each selector attribute in priority order:
    1. Primary attribute (data-testid, id, etc.)
    2. First fallback
    3. Second fallback
    ...
    N. Last fallback

    Leverages Playwright's built-in waiting and retry logic.
    """

    def __init__(
        self, timeout_per_attempt_ms: float = 100.0, max_total_timeout_ms: float = 400.0
    ):
        """
        Initialize heuristic healer.

        Args:
            timeout_per_attempt_ms: Timeout per attribute attempt (default 100ms)
            max_total_timeout_ms: Maximum total time for tier 1 (default 400ms)
        """
        self.timeout_per_attempt_ms = timeout_per_attempt_ms
        self.max_total_timeout_ms = max_total_timeout_ms

    async def find_element(
        self,
        page: "Page",
        selector: SmartSelector,
        workflow_name: str = "Unknown",
        node_id: Optional[str] = None,
    ) -> Optional[tuple["Locator", Optional[HealingEvent]]]:
        """
        Find element using heuristic fallback healing.

        Args:
            page: Playwright page
            selector: SmartSelector with fallbacks
            workflow_name: Workflow name for telemetry
            node_id: Node ID for telemetry

        Returns:
            Tuple of (Locator, HealingEvent) if found, or (None, None) if failed.
            HealingEvent is None if primary succeeded (no healing needed).

        Raises:
            None - returns None instead of raising exceptions
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available - cannot heal selector")
            return None

        start_time = time.perf_counter()
        url = page.url

        # Try primary first
        logger.debug(
            f"[Healing] Attempting primary: {selector.primary.strategy.value} "
            f"= '{selector.primary.value}'"
        )

        locator = await self._try_attribute(
            page, selector, selector.primary.strategy, self.timeout_per_attempt_ms
        )

        if locator is not None:
            # Primary succeeded - no healing needed
            logger.debug(f"[Healing] Primary succeeded for '{selector.id}'")
            return (locator, None)

        # Primary failed - try fallbacks
        logger.info(
            f"[Healing] Primary failed for '{selector.id}' - trying {len(selector.fallbacks)} fallbacks"
        )

        for i, fallback in enumerate(selector.fallbacks):
            # Check total timeout budget
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            if elapsed_ms >= self.max_total_timeout_ms:
                logger.warning(
                    f"[Healing] Timeout budget exceeded ({elapsed_ms:.1f}ms) - "
                    f"stopping tier 1 healing"
                )
                break

            logger.debug(
                f"[Healing] Fallback {i+1}/{len(selector.fallbacks)}: "
                f"{fallback.strategy.value} = '{fallback.value}'"
            )

            locator = await self._try_attribute(
                page, selector, fallback.strategy, self.timeout_per_attempt_ms
            )

            if locator is not None:
                # Fallback succeeded - create healing event
                healing_time_ms = (time.perf_counter() - start_time) * 1000

                logger.info(
                    f"[Healing] Tier 1 success for '{selector.id}' using {fallback.strategy.value} "
                    f"in {healing_time_ms:.1f}ms"
                )

                event = create_healing_event(
                    selector_id=selector.id,
                    selector_name=selector.name,
                    original_strategy=selector.primary.strategy,
                    successful_strategy=fallback.strategy,
                    tier=HealingTier.TIER_1_HEURISTIC,
                    healing_time_ms=healing_time_ms,
                    workflow_name=workflow_name,
                    node_id=node_id,
                    url=url,
                )

                return (locator, event)

        # All attempts failed
        healing_time_ms = (time.perf_counter() - start_time) * 1000

        logger.warning(
            f"[Healing] Tier 1 failed for '{selector.id}' - tried {len(selector.fallbacks) + 1} attributes "
            f"in {healing_time_ms:.1f}ms"
        )

        return None

    async def _try_attribute(
        self,
        page: "Page",
        selector: SmartSelector,
        strategy: SelectorStrategy,
        timeout_ms: float,
    ) -> Optional["Locator"]:
        """
        Try a single selector attribute.

        Args:
            page: Playwright page
            selector: SmartSelector
            strategy: Strategy to try
            timeout_ms: Timeout in milliseconds

        Returns:
            Locator if element found and visible, None otherwise
        """
        try:
            # Build Playwright selector
            selector_string = selector.to_playwright_selector(strategy)

            # Handle frame path if specified
            target = page
            if selector.frame_path:
                for frame_selector in selector.frame_path:
                    frame_element = target.frame_locator(frame_selector)
                    target = frame_element

            # Get locator
            locator = target.locator(selector_string)

            # Wait for element to be visible (Playwright auto-waits)
            await locator.wait_for(state="visible", timeout=timeout_ms)

            # Verify it's actually visible and enabled
            is_visible = await locator.is_visible()
            if not is_visible:
                return None

            return locator

        except PlaywrightTimeoutError:
            # Element not found within timeout - this is expected
            return None

        except Exception as e:
            # Unexpected error - log but don't raise
            logger.debug(f"[Healing] Unexpected error trying {strategy.value}: {e}")
            return None

    async def verify_healing(
        self,
        page: "Page",
        selector: SmartSelector,
        successful_strategy: SelectorStrategy,
        timeout_ms: float = 100.0,
    ) -> bool:
        """
        Verify that healed selector still works.

        Used for testing and validation.

        Args:
            page: Playwright page
            selector: SmartSelector
            successful_strategy: Strategy that previously succeeded
            timeout_ms: Verification timeout

        Returns:
            True if selector still works, False otherwise
        """
        locator = await self._try_attribute(
            page, selector, successful_strategy, timeout_ms
        )

        return locator is not None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "HeuristicSelectorHealer",
]
