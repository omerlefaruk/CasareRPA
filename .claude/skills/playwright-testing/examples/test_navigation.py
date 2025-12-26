"""
Example: Page navigation testing patterns.

Demonstrates testing of browser navigation including:
- Page goto with URL patterns
- Wait strategies (load state, selector, URL)
- Navigation error handling
- Browser history (back, forward, reload)

Run: pytest .claude/skills/playwright-testing/examples/test_navigation.py -v
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.nodes.browser.navigation import GotoUrlNode, WaitForLoadStateNode

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create mock Playwright page with navigation capabilities."""
    page = AsyncMock()
    page.goto = AsyncMock(return_value=None)
    page.reload = AsyncMock(return_value=None)
    page.go_back = AsyncMock(return_value=None)
    page.go_forward = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock(return_value=None)
    page.wait_for_url = AsyncMock(return_value=None)
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example Page")
    return page


@pytest.fixture
def mock_context(mock_page: AsyncMock) -> MagicMock:
    """Create mock context with active page."""
    context = MagicMock()
    context.get_active_page.return_value = mock_page
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    return context


# =============================================================================
# Goto URL Tests
# =============================================================================


class TestGotoUrlNode:
    """Tests for GotoUrlNode navigation."""

    @pytest.mark.asyncio
    async def test_navigate_to_url(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Navigate to absolute URL."""
        node = GotoUrlNode("test_goto", config={"url": "https://example.com"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.goto.assert_called_once_with("https://example.com", timeout=30000)

    @pytest.mark.asyncio
    async def test_navigate_relative_url(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Navigate to relative URL."""
        node = GotoUrlNode("test_relative", config={"url": "/dashboard"})

        result = await node.execute(mock_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_url_from_input_port(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: URL from input port overrides config."""
        node = GotoUrlNode("test_input", config={"url": "https://default.com"})
        node.set_input_value("url", "https://input.com")

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.goto.assert_called_once_with("https://input.com", timeout=30000)

    @pytest.mark.asyncio
    async def test_wait_until_networkidle(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Wait until network is idle after navigation."""
        node = GotoUrlNode(
            "test_wait",
            config={"url": "https://example.com", "wait_until": "networkidle"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.goto.call_args[1]
        assert call_kwargs.get("wait_until") == "networkidle"

    @pytest.mark.asyncio
    async def test_custom_timeout(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Custom timeout for navigation."""
        node = GotoUrlNode(
            "test_timeout",
            config={"url": "https://example.com", "timeout": 60000},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.goto.call_args[1]
        assert call_kwargs.get("timeout") == 60000

    @pytest.mark.asyncio
    async def test_navigation_error(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SAD PATH: Navigation fails."""
        mock_page.goto.side_effect = Exception("Navigation failed")

        node = GotoUrlNode("test_fail", config={"url": "https://bad-url.com"})

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "navigation" in result["error"].lower() or "failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_empty_url_error(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SAD PATH: Empty URL raises error."""
        node = GotoUrlNode("test_empty", config={"url": ""})

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "url" in result["error"].lower() or "required" in result["error"].lower()


# =============================================================================
# Wait for Load State Tests
# =============================================================================


class TestWaitForLoadState:
    """Tests for WaitForLoadStateNode."""

    @pytest.mark.asyncio
    async def test_wait_for_loadstate_domcontentloaded(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ):
        """SUCCESS: Wait for DOM content loaded."""
        node = WaitForLoadStateNode(
            "test_dom",
            config={"state": "domcontentloaded"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_once_with("domcontentloaded", timeout=30000)

    @pytest.mark.asyncio
    async def test_wait_for_loadstate_load(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Wait for load event."""
        node = WaitForLoadStateNode(
            "test_load",
            config={"state": "load"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_once_with("load", timeout=30000)

    @pytest.mark.asyncio
    async def test_wait_for_networkidle(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Wait for network idle."""
        node = WaitForLoadStateNode(
            "test_networkidle",
            config={"state": "networkidle"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_once_with("networkidle", timeout=30000)

    @pytest.mark.asyncio
    async def test_custom_wait_timeout(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Custom timeout for wait."""
        node = WaitForLoadStateNode(
            "test_wait_timeout",
            config={"state": "load", "timeout": 60000},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_once_with("load", timeout=60000)


# =============================================================================
# History Navigation Tests
# =============================================================================


class TestHistoryNavigation:
    """Tests for browser history navigation."""

    @pytest.mark.asyncio
    async def test_go_back(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Navigate back in history."""
        from casare_rpa.nodes.browser.navigation import GoBackNode

        node = GoBackNode("test_back")

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.go_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_forward(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Navigate forward in history."""
        from casare_rpa.nodes.browser.navigation import GoForwardNode

        node = GoForwardNode("test_forward")

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.go_forward.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_page(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Reload current page."""
        from casare_rpa.nodes.browser.navigation import ReloadNode

        node = ReloadNode("test_reload")

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.reload.assert_called_once()


# =============================================================================
# Wait Strategy Examples
# =============================================================================


class TestWaitStrategies:
    """Examples of different wait strategies in browser automation."""

    @pytest.mark.asyncio
    async def test_wait_for_selector_example(self, mock_context: MagicMock, mock_page: AsyncMock):
        """Example: Wait for specific selector before proceeding."""
        from casare_rpa.nodes.browser.navigation import WaitForSelectorNode

        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())

        node = WaitForSelectorNode(
            "test_selector_wait",
            config={"selector": "#content-loaded", "timeout": 10000},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_selector.assert_called_once_with(
            "#content-loaded", timeout=10000, state="attached"
        )

    @pytest.mark.asyncio
    async def test_wait_for_url_pattern(self, mock_context: MagicMock, mock_page: AsyncMock):
        """Example: Wait for URL to match pattern."""
        from casare_rpa.nodes.browser.navigation import WaitForUrlNode

        mock_page.wait_for_url = AsyncMock(return_value=None)

        node = WaitForUrlNode(
            "test_url_wait",
            config={"url_pattern": "**/success", "timeout": 15000},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_url.assert_called_once_with("**/success", timeout=15000)

    @pytest.mark.asyncio
    async def test_wait_for_function_example(self, mock_context: MagicMock, mock_page: AsyncMock):
        """Example: Wait for custom JavaScript condition."""
        from casare_rpa.nodes.browser.scripting import ExecuteScriptNode

        mock_page.evaluate = AsyncMock(return_value=True)

        # Wait for a custom condition using JavaScript
        node = ExecuteScriptNode(
            "test_function_wait",
            config={
                "script": "() => document.readyState === 'complete' && window.jQuery !== undefined",
                "timeout": 20000,
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
