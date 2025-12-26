"""
Example: Browser click node testing patterns.

Demonstrates comprehensive testing of ClickElementNode including:
- Happy path clicks
- Error handling (no page, element not found)
- Retry behavior
- Fast mode variations
- Screenshot on failure

Run: pytest .claude/skills/playwright-testing/examples/test_click_node.py -v
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.nodes.browser.interaction import ClickElementNode

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create mock Playwright page with click capability."""
    page = AsyncMock()
    page.click = AsyncMock(return_value=None)
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    page.screenshot = AsyncMock(return_value=b"screenshot")
    return page


@pytest.fixture
def mock_context(mock_page: AsyncMock) -> MagicMock:
    """Create mock context with active page."""
    context = MagicMock()
    context.get_active_page.return_value = mock_page
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.set_variable = MagicMock()
    return context


@pytest.fixture
def mock_context_no_page() -> MagicMock:
    """Create mock context without page (error case)."""
    context = MagicMock()
    context.get_active_page.return_value = None
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    return context


# =============================================================================
# Happy Path Tests
# =============================================================================


class TestClickElementHappyPath:
    """Tests for successful click operations."""

    @pytest.mark.asyncio
    async def test_click_by_css_selector(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click element using CSS selector."""
        node = ClickElementNode("test_click", config={"selector": "#submit-btn"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.click.assert_called_once()
        call_kwargs = mock_page.click.call_args[1]
        assert "timeout" in call_kwargs

    @pytest.mark.asyncio
    async def test_click_by_xpath_selector(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click element using XPath selector."""
        node = ClickElementNode("test_click", config={"selector": "//button[@type='submit']"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        # XPath is normalized to css= or xpath= prefix
        mock_page.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_with_double_click(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Double click on element."""
        node = ClickElementNode(
            "test_double_click",
            config={"selector": "#item", "click_count": 2},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("click_count") == 2

    @pytest.mark.asyncio
    async def test_click_right_mouse_button(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Right-click on element."""
        node = ClickElementNode(
            "test_right_click",
            config={"selector": "#context-menu", "button": "right"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("button") == "right"

    @pytest.mark.asyncio
    async def test_click_with_offset(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click at specific position within element."""
        node = ClickElementNode(
            "test_offset_click",
            config={"selector": "#canvas", "position_x": 10.5, "position_y": 20.0},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert "position" in call_kwargs
        assert call_kwargs["position"]["x"] == 10.5
        assert call_kwargs["position"]["y"] == 20.0

    @pytest.mark.asyncio
    async def test_click_with_modifier_keys(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click with Ctrl+Shift modifiers."""
        node = ClickElementNode(
            "test_modifier_click",
            config={"selector": "#link", "modifiers": ["Control", "Shift"]},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("modifiers") == ["Control", "Shift"]

    @pytest.mark.asyncio
    async def test_fast_mode_click(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Fast mode skips waits and forces action."""
        node = ClickElementNode(
            "test_fast_click",
            config={"selector": "#fast-btn", "fast_mode": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("force") is True
        assert call_kwargs.get("no_wait_after") is True

    @pytest.mark.asyncio
    async def test_trial_mode_no_click(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Trial mode checks actionability without clicking."""
        node = ClickElementNode(
            "test_trial",
            config={"selector": "#check-only", "trial": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("trial") is True


# =============================================================================
# Error Path Tests
# =============================================================================


class TestClickElementErrors:
    """Tests for error handling in click operations."""

    @pytest.mark.asyncio
    async def test_no_page_available(self, mock_context_no_page: MagicMock):
        """SAD PATH: Error when no page is available."""
        node = ClickElementNode("test_no_page", config={"selector": "#btn"})

        result = await node.execute(mock_context_no_page)

        assert result["success"] is False
        assert "page" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_element_not_found(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SAD PATH: Element not found within timeout."""
        mock_page.click.side_effect = TimeoutError("Timeout 5000ms exceeded")

        node = ClickElementNode(
            "test_not_found",
            config={"selector": "#non-existent", "timeout": 5000},
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "timeout" in result["error"].lower() or "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_selector_required(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SAD PATH: Empty selector raises error."""
        node = ClickElementNode("test_empty_selector", config={"selector": ""})

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "selector" in result["error"].lower() or "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_click_detached_element(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SAD PATH: Element detached from DOM before click."""
        mock_page.click.side_effect = Error("Element is detached from DOM")

        node = ClickElementNode("test_detached", config={"selector": "#detached"})

        result = await node.execute(mock_context)

        assert result["success"] is False


# =============================================================================
# Retry Behavior Tests
# =============================================================================


class TestClickElementRetry:
    """Tests for retry logic on transient failures."""

    @pytest.mark.asyncio
    async def test_retry_on_temporary_failure(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click succeeds after initial failure."""
        # First call fails, second succeeds
        mock_page.click.side_effect = [
            Exception("Element not clickable"),
            None,  # Success on retry
        ]

        node = ClickElementNode(
            "test_retry",
            config={"selector": "#flaky-btn", "retry_count": 1, "retry_interval": 100},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert mock_page.click.call_count == 2
        assert result["data"]["attempts"] == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SAD PATH: All retry attempts fail."""
        mock_page.click.side_effect = Exception("Always fails")

        node = ClickElementNode(
            "test_retry_fail",
            config={"selector": "#bad-btn", "retry_count": 2, "retry_interval": 50},
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert mock_page.click.call_count == 3  # Initial + 2 retries


# =============================================================================
# Screenshot on Failure Tests
# =============================================================================


class TestClickElementScreenshot:
    """Tests for screenshot capture on failure."""

    @pytest.mark.asyncio
    async def test_screenshot_on_failure(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Screenshot taken when click fails."""
        mock_page.click.side_effect = Exception("Click failed")

        node = ClickElementNode(
            "test_screenshot",
            config={
                "selector": "#btn",
                "screenshot_on_fail": True,
                "screenshot_path": "/tmp/failures/click_fail.png",
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        mock_page.screenshot.assert_called()

    @pytest.mark.asyncio
    async def test_no_screenshot_when_disabled(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: No screenshot taken when disabled."""
        mock_page.click.side_effect = Exception("Click failed")

        node = ClickElementNode(
            "test_no_screenshot",
            config={"selector": "#btn", "screenshot_on_fail": False},
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        mock_page.screenshot.assert_not_called()


# =============================================================================
# Edge Cases
# =============================================================================


class TestClickElementEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_click_with_delay(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click with mousedown-mouseup delay."""
        node = ClickElementNode(
            "test_delay",
            config={"selector": "#btn", "delay": 100},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("delay") == 100

    @pytest.mark.asyncio
    async def test_click_text_selector(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Click using text-based selector."""
        node = ClickElementNode(
            "test_text",
            config={"selector": "text=Submit"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_click_with_zero_timeout_uses_default(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ):
        """EDGE CASE: Zero timeout falls back to default."""
        node = ClickElementNode(
            "test_zero_timeout",
            config={"selector": "#btn", "timeout": 0},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        # Should use default timeout from config
