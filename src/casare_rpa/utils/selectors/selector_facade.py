"""
CasareRPA Selector Facade - Unified Selector Pipeline.

This module provides a single entry point for all selector operations:
- Normalization: Convert any selector format to Playwright-compatible
- Validation: Check selector syntax and format
- Generation: Create selectors from element data
- Healing: Self-heal broken selectors using multiple strategies
- Caching: Cache selector validation results for performance

Usage:
    from casare_rpa.utils.selectors.selector_facade import SelectorFacade

    # Singleton accessor
    facade = SelectorFacade.get_instance()

    # Normalize selector
    normalized = facade.normalize("<input id='foo'/>")

    # Validate selector
    is_valid, error = facade.validate("button.submit")

    # Heal broken selector
    result = await facade.heal(page, "broken_selector", fingerprint)

    # Test selector against page
    match_count, ms = await facade.test(page, "div#header")
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class SelectorTestResult:
    """Result of testing a selector against a page."""

    selector: str
    selector_type: str
    match_count: int
    execution_time_ms: float
    is_unique: bool
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.match_count > 0 and self.error is None


@dataclass
class HealingResult:
    """Result of a selector healing attempt."""

    success: bool
    original_selector: str
    healed_selector: str
    confidence: float
    strategy_used: str
    tier_used: str = "original"
    alternatives: list[tuple[str, float]] = field(default_factory=list)
    healing_time_ms: float = 0.0


class SelectorFacade:
    """
    Unified facade for all selector operations.

    Provides a single point of access for:
    - SelectorService (normalize, validate, generate)
    - SelectorManager (inject, activate picker)
    - SelectorHealer (heal broken selectors)
    - AISelectorHealer (AI-enhanced healing)
    - SelectorCache (caching layer)

    This facade implements the Singleton pattern to ensure
    consistent state across the application.
    """

    _instance: SelectorFacade | None = None
    _lock = asyncio.Lock()

    def __init__(self):
        """Initialize the facade with all subsystems."""
        # Lazy-loaded subsystems
        self._service = None
        self._manager = None
        self._healer = None
        self._ai_healer = None
        self._cache = None
        self._healing_chain = None

    @classmethod
    def get_instance(cls) -> SelectorFacade:
        """Get the singleton instance of SelectorFacade."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    # =========================================================================
    # Service Properties (Lazy Loading)
    # =========================================================================

    @property
    def service(self):
        """Get SelectorService for normalization, validation, and generation."""
        if self._service is None:
            from casare_rpa.application.services.selector_service import SelectorService

            self._service = SelectorService
        return self._service

    @property
    def manager(self):
        """Get SelectorManager for browser picker integration."""
        if self._manager is None:
            from casare_rpa.utils.selectors.selector_manager import SelectorManager

            self._manager = SelectorManager()
        return self._manager

    @property
    def healer(self):
        """Get SelectorHealer for heuristic healing."""
        if self._healer is None:
            from casare_rpa.utils.selectors.selector_healing import SelectorHealer

            self._healer = SelectorHealer()
        return self._healer

    @property
    def ai_healer(self):
        """Get AISelectorHealer for AI-enhanced healing."""
        if self._ai_healer is None:
            from casare_rpa.utils.selectors.ai_selector_healer import AISelectorHealer

            self._ai_healer = AISelectorHealer()
        return self._ai_healer

    @property
    def cache(self):
        """Get SelectorCache for caching validation results."""
        if self._cache is None:
            from casare_rpa.utils.selectors.selector_cache import SelectorCache

            self._cache = SelectorCache()
        return self._cache

    @property
    def healing_chain(self):
        """Get or create the healing chain for multi-tier healing."""
        if self._healing_chain is None:
            try:
                from casare_rpa.infrastructure.browser.healing.healing_chain import (
                    SelectorHealingChain,
                )

                self._healing_chain = SelectorHealingChain(enable_cv_fallback=True)
                logger.debug("Initialized healing chain with CV fallback")
            except ImportError:
                logger.warning("Healing chain not available")
        return self._healing_chain

    # =========================================================================
    # Normalization
    # =========================================================================

    def normalize(self, selector: str) -> str:
        """
        Normalize any selector format to work with Playwright.

        Supports:
        - Common CSS selectors (#id, .class)
        - XPath (//, /*, xpath=)
        - Playwright text (text=)
        - Case-insensitive text (itext=)
        - Wildcard patterns (btn-*)
        - UiPath-style XML (<webctrl .../>)

        Args:
            selector: Raw selector string in any format

        Returns:
            Normalized selector ready for Playwright
        """
        return self.service.normalize(selector)

    def detect_type(self, selector: str) -> str:
        """
        Detect the type of a selector.

        Args:
            selector: Selector string

        Returns:
            Type string: "xpath", "css", "text", "itext", "wildcard", or "unknown"
        """
        if not selector:
            return "unknown"
        s = selector.strip()
        if s.startswith(("xpath=", "//", "(/")):
            return "xpath"
        if s.startswith("text="):
            return "text"
        if s.startswith("itext="):
            return "itext"
        if "*" in s or "?" in s:
            return "wildcard"
        return "css"

    # =========================================================================
    # Validation
    # =========================================================================

    def validate(self, selector: str) -> tuple[bool, str]:
        """
        Validate selector format.

        Args:
            selector: Selector string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.service.validate(selector)

    # =========================================================================
    # Testing
    # =========================================================================

    async def test(
        self,
        page: Page,
        selector: str,
        selector_type: str = "auto",
        timeout_ms: int = 2000,
        use_cache: bool = True,
    ) -> SelectorTestResult:
        """
        Test a selector against the current page.

        Args:
            page: Playwright Page instance
            selector: Selector to test
            selector_type: Type hint ("xpath", "css", "auto")
            timeout_ms: Timeout for the test
            use_cache: Whether to use cached results

        Returns:
            SelectorTestResult with match count and timing
        """
        import time

        start = time.perf_counter()
        normalized = self.normalize(selector)
        detected_type = selector_type if selector_type != "auto" else self.detect_type(selector)

        try:
            elements = await page.query_selector_all(normalized)
            count = len(elements)
            elapsed = (time.perf_counter() - start) * 1000

            return SelectorTestResult(
                selector=normalized,
                selector_type=detected_type,
                match_count=count,
                execution_time_ms=elapsed,
                is_unique=count == 1,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return SelectorTestResult(
                selector=normalized,
                selector_type=detected_type,
                match_count=0,
                execution_time_ms=elapsed,
                is_unique=False,
                error=str(e),
            )

    # =========================================================================
    # Healing
    # =========================================================================

    async def heal(
        self,
        page: Page,
        selector: str,
        fingerprint: Any | None = None,
        healing_context: dict[str, Any] | None = None,
        timeout_ms: int = 5000,
    ) -> HealingResult:
        """
        Attempt to heal a broken selector.

        Uses a multi-tier approach:
        1. Heuristic healing (attribute matching)
        2. AI-enhanced healing (fuzzy matching, synonyms)
        3. Anchor-based healing (relative positioning)
        4. CV fallback (visual matching)

        Args:
            page: Playwright Page instance
            selector: Original selector that failed
            fingerprint: Optional element fingerprint from capture
            healing_context: Optional healing context dict
            timeout_ms: Timeout for healing attempts

        Returns:
            HealingResult with healed selector or failure details
        """
        import time

        start = time.perf_counter()

        # Try primary selector first (fast path)
        try:
            element = await page.wait_for_selector(
                self.normalize(selector),
                timeout=min(timeout_ms, 1000),
                state="attached",
            )
            if element:
                elapsed = (time.perf_counter() - start) * 1000
                return HealingResult(
                    success=True,
                    original_selector=selector,
                    healed_selector=selector,
                    confidence=1.0,
                    strategy_used="original",
                    tier_used="original",
                    healing_time_ms=elapsed,
                )
        except Exception:
            pass

        # Try healing chain if available
        if self.healing_chain and healing_context:
            try:
                result = await self.healing_chain.locate_element(
                    page=page,
                    selector=selector,
                    timeout_ms=timeout_ms,
                )
                elapsed = (time.perf_counter() - start) * 1000

                if result.success:
                    tier_name = (
                        result.tier_used.value
                        if hasattr(result.tier_used, "value")
                        else str(result.tier_used)
                    )
                    return HealingResult(
                        success=True,
                        original_selector=selector,
                        healed_selector=result.final_selector,
                        confidence=result.confidence,
                        strategy_used=result.strategy_used
                        if hasattr(result, "strategy_used")
                        else tier_name,
                        tier_used=tier_name,
                        healing_time_ms=elapsed,
                    )
            except Exception as e:
                logger.debug(f"Healing chain failed: {e}")

        # Try heuristic healer with fingerprint
        if fingerprint:
            try:
                result = await self.healer.heal(page, selector, fingerprint)
                elapsed = (time.perf_counter() - start) * 1000

                if result.success:
                    return HealingResult(
                        success=True,
                        original_selector=selector,
                        healed_selector=result.healed_selector,
                        confidence=result.confidence,
                        strategy_used=result.strategy_used,
                        tier_used="heuristic",
                        alternatives=result.alternatives,
                        healing_time_ms=elapsed,
                    )
            except Exception as e:
                logger.debug(f"Heuristic healing failed: {e}")

        # Try AI healer as final attempt
        try:
            result = await self.ai_healer.heal(page, selector, fingerprint)
            elapsed = (time.perf_counter() - start) * 1000

            if result.success:
                return HealingResult(
                    success=True,
                    original_selector=selector,
                    healed_selector=result.healed_selector,
                    confidence=result.confidence,
                    strategy_used=result.strategy_used,
                    tier_used="ai",
                    alternatives=result.alternatives,
                    healing_time_ms=elapsed,
                )
        except Exception as e:
            logger.debug(f"AI healing failed: {e}")

        # All healing attempts failed
        elapsed = (time.perf_counter() - start) * 1000
        return HealingResult(
            success=False,
            original_selector=selector,
            healed_selector=selector,
            confidence=0.0,
            strategy_used="none",
            tier_used="none",
            healing_time_ms=elapsed,
        )

    # =========================================================================
    # Generation
    # =========================================================================

    def generate_browser_fingerprint(self, element_data: dict[str, Any]) -> Any:
        """
        Generate multiple selector strategies from browser element data.

        Args:
            element_data: Dictionary with element attributes from browser

        Returns:
            ElementFingerprint with multiple selector strategies
        """
        return self.service.generate_browser_fingerprint(element_data)

    def generate_desktop_fingerprint(self, element_data: dict[str, Any]) -> Any:
        """
        Generate multiple selector strategies from desktop element data (UIA).

        Args:
            element_data: Dictionary with UIA element properties

        Returns:
            ElementFingerprint with multiple selector strategies
        """
        return self.service.generate_desktop_fingerprint(element_data)

    # =========================================================================
    # Picker Integration
    # =========================================================================

    async def inject_picker(self, page: Page) -> None:
        """
        Inject selector picker script into a page.

        Args:
            page: Playwright Page instance
        """
        await self.manager.inject_into_page(page)

    async def activate_picker(
        self,
        recording: bool = False,
        on_element_selected: Callable | None = None,
        on_recording_complete: Callable | None = None,
    ) -> None:
        """
        Activate selector picker mode on the current page.

        Args:
            recording: If True, enable recording mode
            on_element_selected: Callback when element is selected
            on_recording_complete: Callback when recording completes
        """
        await self.manager.activate_selector_mode(
            recording=recording,
            on_element_selected=on_element_selected,
            on_recording_complete=on_recording_complete,
        )

    async def deactivate_picker(self) -> None:
        """Deactivate selector picker mode."""
        await self.manager.deactivate_selector_mode()

    # =========================================================================
    # Cache Management
    # =========================================================================

    def get_cache_stats(self) -> dict[str, Any]:
        """Get selector cache statistics."""
        return self.cache.get_stats()

    def clear_cache(self, page_url: str | None = None) -> int:
        """
        Clear selector cache.

        Args:
            page_url: If provided, only clear entries for this URL

        Returns:
            Number of entries cleared
        """
        return self.cache.clear(page_url)

    def enable_cache(self) -> None:
        """Enable selector caching."""
        self.cache.enable()

    def disable_cache(self) -> None:
        """Disable selector caching."""
        self.cache.disable()


# Module-level convenience functions
def get_selector_facade() -> SelectorFacade:
    """Get the global SelectorFacade instance."""
    return SelectorFacade.get_instance()


def normalize_selector(selector: str) -> str:
    """Normalize any selector format to Playwright-compatible format."""
    return get_selector_facade().normalize(selector)


def validate_selector(selector: str) -> tuple[bool, str]:
    """Validate selector format."""
    return get_selector_facade().validate(selector)


async def test_selector(
    page: Page,
    selector: str,
    timeout_ms: int = 2000,
) -> SelectorTestResult:
    """Test a selector against the current page."""
    return await get_selector_facade().test(page, selector, timeout_ms=timeout_ms)


async def heal_selector(
    page: Page,
    selector: str,
    fingerprint: Any | None = None,
    timeout_ms: int = 5000,
) -> HealingResult:
    """Attempt to heal a broken selector."""
    return await get_selector_facade().heal(page, selector, fingerprint, timeout_ms=timeout_ms)
