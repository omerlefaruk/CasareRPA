"""
Tests for Selector Healing Chain.

These tests verify the tiered fallback chain for self-healing selectors.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.infrastructure.browser.healing.models import (
    AnchorElement,
    AnchorHealingResult,
    BoundingRect,
    SpatialContext,
    SpatialRelation,
)
from casare_rpa.infrastructure.browser.healing.telemetry import (
    HealingTelemetry,
    HealingTier,
)
from casare_rpa.infrastructure.browser.healing.healing_chain import (
    HealingChainResult,
    SelectorHealingChain,
    create_healing_chain,
)


class TestHealingChainResult:
    """Tests for HealingChainResult dataclass."""

    def test_successful_result(self) -> None:
        """Verify successful result creation."""
        result = HealingChainResult(
            success=True,
            original_selector="#button",
            final_selector='button:has-text("Submit")',
            tier_used=HealingTier.HEURISTIC,
            confidence=0.85,
            total_time_ms=45.0,
        )

        assert result.success is True
        assert result.tier_used == HealingTier.HEURISTIC
        assert result.confidence == 0.85

    def test_failed_result(self) -> None:
        """Verify failed result creation."""
        result = HealingChainResult(
            success=False,
            original_selector="#broken",
            final_selector="#broken",
            tier_used=HealingTier.FAILED,
            confidence=0.0,
            total_time_ms=400.0,
            tier_results={
                "original": {"success": False},
                "heuristic": {"success": False},
                "anchor": {"success": False},
            },
        )

        assert result.success is False
        assert result.tier_used == HealingTier.FAILED
        assert len(result.tier_results) == 3


class TestSelectorHealingChain:
    """Tests for SelectorHealingChain class."""

    def test_initialization(self) -> None:
        """Verify default initialization."""
        chain = SelectorHealingChain()

        assert chain._healing_budget_ms == 400.0
        assert chain._enable_cv_fallback is False

    def test_custom_initialization(self) -> None:
        """Verify custom initialization."""
        telemetry = HealingTelemetry()
        chain = SelectorHealingChain(
            telemetry=telemetry,
            healing_budget_ms=500.0,
            enable_cv_fallback=True,
        )

        assert chain._healing_budget_ms == 500.0
        assert chain._enable_cv_fallback is True
        assert chain._telemetry is telemetry

    def test_healing_budget_setter(self) -> None:
        """Verify healing budget minimum enforcement."""
        chain = SelectorHealingChain()

        chain.healing_budget_ms = 30.0
        assert chain.healing_budget_ms == 50.0  # Minimum enforced

        chain.healing_budget_ms = 600.0
        assert chain.healing_budget_ms == 600.0


class TestSelectorHealingChainAsync:
    """Async tests for SelectorHealingChain."""

    @pytest.mark.asyncio
    async def test_locate_element_original_success(self) -> None:
        """Verify original selector success path."""
        chain = SelectorHealingChain()

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        result = await chain.locate_element(mock_page, "#button")

        assert result.success is True
        assert result.tier_used == HealingTier.ORIGINAL
        assert result.final_selector == "#button"
        assert result.element is mock_element

    @pytest.mark.asyncio
    async def test_locate_element_heuristic_fallback(self) -> None:
        """Verify heuristic healing fallback."""
        chain = SelectorHealingChain()

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_page.url = "https://example.com"

        # Original selector fails
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

        # Store a fingerprint for heuristic healing
        from casare_rpa.utils.selectors.selector_healing import ElementFingerprint

        fingerprint = ElementFingerprint(
            tag_name="button",
            text_content="Submit",
            id_attr="",
            class_list=["btn", "primary"],
        )
        chain._fingerprints["#button"] = fingerprint
        chain._heuristic_healer.store_fingerprint("#button", fingerprint)

        # Mock heuristic healing to succeed
        async def mock_query_selector(selector: str):
            if "Submit" in selector or "button" in selector.lower():
                return mock_element
            return None

        mock_page.query_selector = mock_query_selector

        # Mock the heuristic healer's heal method
        from casare_rpa.utils.selectors.selector_healing import HealingResult

        with patch.object(
            chain._heuristic_healer,
            "heal",
            new_callable=AsyncMock,
            return_value=HealingResult(
                success=True,
                original_selector="#button",
                healed_selector='button:has-text("Submit")',
                confidence=0.8,
                strategy_used="text-content",
            ),
        ):
            result = await chain.locate_element(mock_page, "#button")

        assert result.success is True
        assert result.tier_used == HealingTier.HEURISTIC

    @pytest.mark.asyncio
    async def test_locate_element_anchor_fallback(self) -> None:
        """Verify anchor healing fallback when heuristic fails."""
        chain = SelectorHealingChain()

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_page.url = "https://example.com"

        # Original selector fails
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

        # Store spatial context for anchor healing
        anchor = AnchorElement(
            selector='label[for="email"]',
            tag_name="label",
            text_content="Email",
            rect=BoundingRect(x=10, y=100, width=50, height=20),
            stability_score=0.9,
            attributes={"forAttr": "email"},
        )
        context = SpatialContext(
            anchor_relations=[(anchor, SpatialRelation.LEFT_OF, 40.0)],
            dom_path="form/div",
            visual_quadrant="top-left",
        )
        chain._spatial_contexts["#email-input"] = context
        chain._anchor_healer.store_context("#email-input", context)

        # Mock page queries
        mock_anchor = AsyncMock()

        async def mock_query_selector(selector: str):
            if selector == 'label[for="email"]':
                return mock_anchor
            elif selector == "#email":
                return mock_element
            return None

        mock_page.query_selector = mock_query_selector

        # Mock heuristic healing to fail
        from casare_rpa.utils.selectors.selector_healing import HealingResult

        with patch.object(
            chain._heuristic_healer,
            "heal",
            new_callable=AsyncMock,
            return_value=HealingResult(
                success=False,
                original_selector="#email-input",
                healed_selector="",
                confidence=0.0,
                strategy_used="none",
            ),
        ):
            result = await chain.locate_element(mock_page, "#email-input")

        assert result.success is True
        assert result.tier_used == HealingTier.ANCHOR
        assert result.final_selector == "#email"

    @pytest.mark.asyncio
    async def test_locate_element_all_tiers_fail(self) -> None:
        """Verify handling when all tiers fail."""
        chain = SelectorHealingChain()

        mock_page = AsyncMock()
        mock_page.url = "https://example.com"

        # All selectors fail
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
        mock_page.query_selector = AsyncMock(return_value=None)

        # Mock heuristic to fail
        from casare_rpa.utils.selectors.selector_healing import HealingResult

        with patch.object(
            chain._heuristic_healer,
            "heal",
            new_callable=AsyncMock,
            return_value=HealingResult(
                success=False,
                original_selector="#broken",
                healed_selector="",
                confidence=0.0,
                strategy_used="none",
            ),
        ):
            result = await chain.locate_element(mock_page, "#broken")

        assert result.success is False
        assert result.tier_used == HealingTier.FAILED
        assert result.final_selector == "#broken"

    @pytest.mark.asyncio
    async def test_capture_element_context(self) -> None:
        """Verify context capture for an element."""
        chain = SelectorHealingChain()

        mock_page = AsyncMock()

        # Mock fingerprint capture
        from casare_rpa.utils.selectors.selector_healing import ElementFingerprint

        with patch.object(
            chain._heuristic_healer,
            "capture_fingerprint",
            new_callable=AsyncMock,
            return_value=ElementFingerprint(
                tag_name="input",
                text_content="",
                id_attr="email",
            ),
        ):
            # Mock spatial context capture
            mock_page.evaluate = AsyncMock(
                return_value={
                    "targetRect": {"x": 100, "y": 100, "width": 200, "height": 30},
                    "anchors": [
                        {
                            "tag": "label",
                            "text": "Email",
                            "rect": {"x": 10, "y": 100, "width": 50, "height": 20},
                            "forAttr": "email",
                            "id": "",
                            "distance": 40.0,
                        }
                    ],
                    "containerSelector": "#form",
                    "visualQuadrant": "top-left",
                    "domPath": "form/div",
                }
            )

            success = await chain.capture_element_context(mock_page, "#email")

        assert success is True
        assert "#email" in chain._fingerprints
        assert "#email" in chain._spatial_contexts

    @pytest.mark.asyncio
    async def test_telemetry_recording(self) -> None:
        """Verify telemetry is recorded correctly."""
        telemetry = HealingTelemetry()
        chain = SelectorHealingChain(telemetry=telemetry)

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_page.url = "https://example.com/page"
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        await chain.locate_element(mock_page, "#button")

        stats = telemetry.get_overall_stats()
        assert stats["total_uses"] == 1
        assert stats["original_successes"] == 1

    def test_get_stats(self) -> None:
        """Verify stats retrieval."""
        telemetry = HealingTelemetry()
        chain = SelectorHealingChain(telemetry=telemetry)

        # Record some events directly to telemetry
        telemetry.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#b", "url", True, HealingTier.HEURISTIC, 30.0)

        stats = chain.get_stats()
        assert stats["total_uses"] == 2

    def test_export_report(self) -> None:
        """Verify report export."""
        telemetry = HealingTelemetry()
        chain = SelectorHealingChain(telemetry=telemetry)

        telemetry.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)

        report = chain.export_report()
        assert "overall" in report
        assert "tier_breakdown" in report


class TestCreateHealingChain:
    """Tests for convenience factory function."""

    def test_create_default(self) -> None:
        """Verify default chain creation."""
        chain = create_healing_chain()

        assert chain._healing_budget_ms == 400.0
        assert chain._enable_cv_fallback is False

    def test_create_custom(self) -> None:
        """Verify custom chain creation."""
        chain = create_healing_chain(healing_budget_ms=600, enable_cv=True)

        assert chain._healing_budget_ms == 600.0
        assert chain._enable_cv_fallback is True
