"""
Tests for Tier 1 Heuristic Selector Healer.

Verifies:
- Multi-attribute fallback logic
- Healing event generation
- Timeout handling
- Playwright integration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.domain.value_objects.selector import (
    SmartSelector,
    SelectorAttribute,
    SelectorStrategy,
    create_smart_selector,
)
from casare_rpa.domain.value_objects.healing_event import HealingTier
from casare_rpa.infrastructure.browser.selector_healer import HeuristicSelectorHealer


class TestSmartSelector:
    """Test SmartSelector value object."""

    def test_create_smart_selector(self):
        """Test creating SmartSelector."""
        selector = create_smart_selector(
            id="btn-submit",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="submit-button",
            fallback_specs=[
                (SelectorStrategy.ID, "btnSubmit"),
                (SelectorStrategy.TEXT, "Submit"),
            ],
            name="Submit Button",
        )

        assert selector.id == "btn-submit"
        assert selector.name == "Submit Button"
        assert selector.primary.strategy == SelectorStrategy.DATA_TESTID
        assert selector.primary.value == "submit-button"
        assert len(selector.fallbacks) == 2

    def test_to_playwright_selector_data_testid(self):
        """Test converting DATA_TESTID to Playwright selector."""
        selector = SmartSelector(
            id="test",
            primary=SelectorAttribute(
                strategy=SelectorStrategy.DATA_TESTID, value="my-button"
            ),
        )

        assert selector.to_playwright_selector() == "[data-testid='my-button']"

    def test_to_playwright_selector_id(self):
        """Test converting ID to Playwright selector."""
        selector = SmartSelector(
            id="test",
            primary=SelectorAttribute(strategy=SelectorStrategy.ID, value="btnSubmit"),
        )

        assert selector.to_playwright_selector() == "#btnSubmit"

    def test_to_playwright_selector_text(self):
        """Test converting TEXT to Playwright selector."""
        selector = SmartSelector(
            id="test",
            primary=SelectorAttribute(strategy=SelectorStrategy.TEXT, value="Click me"),
        )

        assert selector.to_playwright_selector() == "text='Click me'"

    def test_to_playwright_selector_class(self):
        """Test converting CLASS to Playwright selector."""
        selector = SmartSelector(
            id="test",
            primary=SelectorAttribute(
                strategy=SelectorStrategy.CLASS, value="btn-primary"
            ),
        )

        assert selector.to_playwright_selector() == ".btn-primary"

    def test_to_playwright_selector_specific_strategy(self):
        """Test converting specific fallback strategy."""
        selector = create_smart_selector(
            id="test",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="primary",
            fallback_specs=[(SelectorStrategy.TEXT, "Fallback Text")],
        )

        # Get specific fallback
        result = selector.to_playwright_selector(SelectorStrategy.TEXT)
        assert result == "text='Fallback Text'"

    def test_add_fallback(self):
        """Test adding fallback attribute."""
        selector = SmartSelector(
            id="test",
            primary=SelectorAttribute(
                strategy=SelectorStrategy.DATA_TESTID, value="primary"
            ),
        )

        new_selector = selector.add_fallback(
            SelectorAttribute(strategy=SelectorStrategy.TEXT, value="Click")
        )

        assert len(new_selector.fallbacks) == 1
        assert new_selector.fallbacks[0].strategy == SelectorStrategy.TEXT
        assert len(selector.fallbacks) == 0  # Original unchanged

    def test_promote_fallback(self):
        """Test promoting fallback to primary."""
        selector = create_smart_selector(
            id="test",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="primary",
            fallback_specs=[
                (SelectorStrategy.TEXT, "Text Fallback"),
                (SelectorStrategy.ID, "idFallback"),
            ],
        )

        # Promote TEXT to primary
        new_selector = selector.promote_fallback(SelectorStrategy.TEXT)

        assert new_selector.primary.strategy == SelectorStrategy.TEXT
        assert new_selector.primary.value == "Text Fallback"
        assert len(new_selector.fallbacks) == 2
        assert new_selector.fallbacks[0].strategy == SelectorStrategy.DATA_TESTID

    def test_serialization(self):
        """Test selector serialization."""
        selector = create_smart_selector(
            id="btn-1",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="button-1",
            fallback_specs=[(SelectorStrategy.TEXT, "Button")],
        )

        # Serialize
        data = selector.to_dict()

        assert data["id"] == "btn-1"
        assert data["primary"]["strategy"] == "data-testid"
        assert data["primary"]["value"] == "button-1"
        assert len(data["fallbacks"]) == 1

        # Deserialize
        restored = SmartSelector.from_dict(data)

        assert restored.id == selector.id
        assert restored.primary.strategy == selector.primary.strategy
        assert len(restored.fallbacks) == len(selector.fallbacks)


@pytest.mark.skipif(
    not pytest.importorskip("playwright", minversion=None),
    reason="Playwright not available",
)
class TestHeuristicSelectorHealer:
    """Test HeuristicSelectorHealer (requires Playwright)."""

    @pytest.mark.asyncio
    async def test_find_element_primary_succeeds(self):
        """Test finding element with primary selector (no healing)."""
        # Mock Playwright page and locator
        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_locator.wait_for = AsyncMock()

        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.locator = MagicMock(return_value=mock_locator)

        selector = create_smart_selector(
            id="btn-submit",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="submit-btn",
        )

        healer = HeuristicSelectorHealer()

        result = await healer.find_element(
            page=mock_page, selector=selector, workflow_name="Test Workflow"
        )

        assert result is not None
        locator, event = result

        assert locator is not None
        assert event is None  # No healing needed

    @pytest.mark.asyncio
    async def test_find_element_fallback_succeeds(self):
        """Test healing with fallback selector."""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        # Mock primary failing, fallback succeeding
        primary_locator = AsyncMock()
        primary_locator.wait_for = AsyncMock(
            side_effect=PlaywrightTimeoutError("timeout")
        )

        fallback_locator = AsyncMock()
        fallback_locator.is_visible = AsyncMock(return_value=True)
        fallback_locator.wait_for = AsyncMock()

        mock_page = MagicMock()
        mock_page.url = "https://example.com/page"

        call_count = [0]

        def locator_side_effect(selector_string):
            call_count[0] += 1
            if call_count[0] == 1:
                return primary_locator  # First call (primary)
            else:
                return fallback_locator  # Second call (fallback)

        mock_page.locator = MagicMock(side_effect=locator_side_effect)

        selector = create_smart_selector(
            id="btn-submit",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="submit-btn",
            fallback_specs=[(SelectorStrategy.TEXT, "Submit")],
        )

        healer = HeuristicSelectorHealer()

        result = await healer.find_element(
            page=mock_page,
            selector=selector,
            workflow_name="Test Workflow",
            node_id="node-123",
        )

        assert result is not None
        locator, event = result

        assert locator is not None
        assert event is not None
        assert event.tier == HealingTier.TIER_1_HEURISTIC
        assert event.original_strategy == SelectorStrategy.DATA_TESTID
        assert event.successful_strategy == SelectorStrategy.TEXT
        assert event.workflow_name == "Test Workflow"
        assert event.node_id == "node-123"
        assert event.healing_time_ms > 0

    @pytest.mark.asyncio
    async def test_find_element_all_fail(self):
        """Test when all selector strategies fail."""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        # Mock all locators failing
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(side_effect=PlaywrightTimeoutError("timeout"))

        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.locator = MagicMock(return_value=mock_locator)

        selector = create_smart_selector(
            id="btn-submit",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="submit-btn",
            fallback_specs=[
                (SelectorStrategy.TEXT, "Submit"),
                (SelectorStrategy.ID, "btnSubmit"),
            ],
        )

        healer = HeuristicSelectorHealer()

        result = await healer.find_element(
            page=mock_page, selector=selector, workflow_name="Test Workflow"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_timeout_budget_enforcement(self):
        """Test that total timeout budget is enforced."""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        # Mock slow locators
        async def slow_wait_for(*args, **kwargs):
            await asyncio.sleep(0.15)  # 150ms per attempt
            raise PlaywrightTimeoutError("timeout")

        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(side_effect=slow_wait_for)

        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Create selector with many fallbacks
        selector = create_smart_selector(
            id="btn",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="btn",
            fallback_specs=[
                (SelectorStrategy.ID, "btn1"),
                (SelectorStrategy.TEXT, "Button"),
                (SelectorStrategy.CLASS, "btn-class"),
                (SelectorStrategy.ARIA_LABEL, "Button Label"),
            ],
        )

        healer = HeuristicSelectorHealer(
            timeout_per_attempt_ms=100,
            max_total_timeout_ms=400,  # Should stop after ~2-3 attempts
        )

        import time

        start = time.perf_counter()

        result = await healer.find_element(
            page=mock_page, selector=selector, workflow_name="Test"
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result is None
        # Should stop before trying all 5 attributes
        assert elapsed_ms < 800  # Would be 750ms if all 5 attempts ran


@pytest.mark.skipif(
    not pytest.importorskip("playwright", minversion=None),
    reason="Playwright not available",
)
class TestHealingIntegration:
    """Integration tests with mocked Playwright."""

    @pytest.mark.asyncio
    async def test_frame_path_handling(self):
        """Test selector in iframe."""
        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_locator.wait_for = AsyncMock()

        mock_frame_locator = MagicMock()
        mock_frame_locator.locator = MagicMock(return_value=mock_locator)

        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.frame_locator = MagicMock(return_value=mock_frame_locator)

        selector = create_smart_selector(
            id="iframe-btn",
            primary_strategy=SelectorStrategy.DATA_TESTID,
            primary_value="btn",
            frame_path=["#myframe"],
        )

        healer = HeuristicSelectorHealer()

        result = await healer.find_element(
            page=mock_page, selector=selector, workflow_name="Test"
        )

        assert result is not None
        locator, event = result
        assert locator is not None

        # Verify frame_locator was called
        mock_page.frame_locator.assert_called_once_with("#myframe")
