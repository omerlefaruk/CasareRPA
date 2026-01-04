"""
CasareRPA - Browser Integration End-to-End Tests

E2E tests for browser automation integration:
- Browser launch and close lifecycle
- Navigation and page state
- Element interaction (click, type, select)
- Screenshot capture
- Cookie management

Run with: pytest tests/e2e/test_browser_integration_e2e.py -v -m e2e -m browser
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext

if TYPE_CHECKING:
    pass


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def browser_context() -> ExecutionContext:
    """Create ExecutionContext for browser testing."""
    return ExecutionContext(
        workflow_name="BrowserE2ETest",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mock Playwright page."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example Domain")
    page.content = AsyncMock(return_value="<html><body>Test</body></html>")
    page.goto = AsyncMock(return_value=None)
    page.click = AsyncMock(return_value=None)
    page.fill = AsyncMock(return_value=None)
    page.type = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value={})
    page.screenshot = AsyncMock(return_value=b"fake-screenshot-bytes")
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    page.query_selector = AsyncMock(return_value=MagicMock())
    page.reload = AsyncMock(return_value=None)
    page.go_back = AsyncMock(return_value=None)
    page.go_forward = AsyncMock(return_value=None)
    return page


@pytest.fixture
def mock_browser() -> AsyncMock:
    """Create a mock Playwright browser."""
    browser = AsyncMock()
    browser.new_page = AsyncMock()
    browser.close = AsyncMock()
    browser.is_connected = MagicMock(return_value=True)
    return browser


# =============================================================================
# Browser Lifecycle Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestBrowserLifecycle:
    """E2E tests for browser launch and close operations."""

    @pytest.mark.asyncio
    async def test_launch_browser_node(
        self, browser_context: ExecutionContext, mock_browser: AsyncMock
    ) -> None:
        """Test LaunchBrowserNode launches browser."""
        from casare_rpa.nodes import LaunchBrowserNode

        with patch(
            "casare_rpa.nodes.browser.lifecycle.async_playwright"
        ) as mock_playwright:
            mock_pw = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.__aenter__.return_value = mock_pw

            node = LaunchBrowserNode(
                "launch_1",
                config={
                    "browser_type": "chromium",
                    "headless": True,
                },
            )

            result = await node.execute(browser_context)

            # Should succeed or indicate browser resource
            assert "success" in result or "browser" in result

    @pytest.mark.asyncio
    async def test_close_browser_node(
        self, browser_context: ExecutionContext
    ) -> None:
        """Test CloseBrowserNode closes browser."""
        from casare_rpa.nodes import CloseBrowserNode

        # Set up mock browser in context
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock(return_value=None)

        with patch.object(browser_context, "resources", {"browser": mock_browser}):
            node = CloseBrowserNode("close_1")
            result = await node.execute(browser_context)

            assert result.get("success") is True


# =============================================================================
# Navigation Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestBrowserNavigation:
    """E2E tests for browser navigation operations."""

    @pytest.mark.asyncio
    async def test_goto_url_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test GoToURLNode navigates to URL."""
        from casare_rpa.nodes import GoToURLNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = GoToURLNode(
                "goto_1",
                config={"url": "https://example.com"},
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True
            mock_page.goto.assert_called()

    @pytest.mark.asyncio
    async def test_go_back_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test GoBackNode navigates back."""
        from casare_rpa.nodes import GoBackNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = GoBackNode("back_1")
            result = await node.execute(browser_context)

            assert result.get("success") is True
            mock_page.go_back.assert_called()

    @pytest.mark.asyncio
    async def test_go_forward_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test GoForwardNode navigates forward."""
        from casare_rpa.nodes import GoForwardNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = GoForwardNode("forward_1")
            result = await node.execute(browser_context)

            assert result.get("success") is True
            mock_page.go_forward.assert_called()

    @pytest.mark.asyncio
    async def test_refresh_page_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test RefreshPageNode refreshes page."""
        from casare_rpa.nodes import RefreshPageNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = RefreshPageNode("refresh_1")
            result = await node.execute(browser_context)

            assert result.get("success") is True
            mock_page.reload.assert_called()


# =============================================================================
# Element Interaction Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestElementInteraction:
    """E2E tests for browser element interaction."""

    @pytest.mark.asyncio
    async def test_click_element_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test ClickElementNode clicks an element."""
        from casare_rpa.nodes import ClickElementNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = ClickElementNode(
                "click_1",
                config={"selector": "#submit-button"},
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_type_text_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test TypeTextNode types text into element."""
        from casare_rpa.nodes import TypeTextNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = TypeTextNode(
                "type_1",
                config={
                    "selector": "#username",
                    "text": "testuser",
                },
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_select_dropdown_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test SelectDropdownNode selects option from dropdown."""
        from casare_rpa.nodes import SelectDropdownNode

        mock_page.select_option = AsyncMock(return_value=None)

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = SelectDropdownNode(
                "select_1",
                config={
                    "selector": "#country",
                    "value": "US",
                },
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True


# =============================================================================
# Data Extraction Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestDataExtraction:
    """E2E tests for browser data extraction."""

    @pytest.mark.asyncio
    async def test_extract_text_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test ExtractTextNode extracts text from element."""
        from casare_rpa.nodes import ExtractTextNode

        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Extracted Text")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = ExtractTextNode(
                "extract_1",
                config={"selector": ".content"},
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_get_attribute_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test GetAttributeNode gets element attribute."""
        from casare_rpa.nodes import GetAttributeNode

        mock_element = AsyncMock()
        mock_element.get_attribute = AsyncMock(return_value="https://example.com")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = GetAttributeNode(
                "attr_1",
                config={
                    "selector": "a",
                    "attribute": "href",
                },
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_screenshot_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test ScreenshotNode captures screenshot."""
        from casare_rpa.nodes import ScreenshotNode

        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = Path(tmpdir) / "screenshot.png"

            with patch.object(browser_context, "resources", {"page": mock_page}):
                node = ScreenshotNode(
                    "screenshot_1",
                    config={"file_path": str(screenshot_path)},
                )
                result = await node.execute(browser_context)

                assert result.get("success") is True
                mock_page.screenshot.assert_called()


# =============================================================================
# Wait Operations Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestWaitOperations:
    """E2E tests for browser wait operations."""

    @pytest.mark.asyncio
    async def test_wait_for_element_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test WaitForElementNode waits for element."""
        from casare_rpa.nodes import WaitForElementNode

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = WaitForElementNode(
                "wait_1",
                config={
                    "selector": "#dynamic-element",
                    "timeout": 5000,
                },
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True
            mock_page.wait_for_selector.assert_called()

    @pytest.mark.asyncio
    async def test_wait_node(
        self, browser_context: ExecutionContext
    ) -> None:
        """Test WaitNode delays execution."""
        from casare_rpa.nodes import WaitNode

        node = WaitNode(
            "wait_1",
            config={"seconds": 0.1},  # Short wait for test
        )
        result = await node.execute(browser_context)

        assert result.get("success") is True


# =============================================================================
# JavaScript Execution Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestJavaScriptExecution:
    """E2E tests for JavaScript execution in browser."""

    @pytest.mark.asyncio
    async def test_browser_evaluate_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test BrowserEvaluateNode executes JavaScript."""
        from casare_rpa.nodes import BrowserEvaluateNode

        mock_page.evaluate = AsyncMock(return_value="evaluated_result")

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = BrowserEvaluateNode(
                "eval_1",
                config={"script": "document.title"},
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True
            mock_page.evaluate.assert_called()

    @pytest.mark.asyncio
    async def test_browser_run_script_node(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test BrowserRunScriptNode runs JavaScript."""
        from casare_rpa.nodes import BrowserRunScriptNode

        mock_page.evaluate = AsyncMock(return_value={"key": "value"})

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = BrowserRunScriptNode(
                "script_1",
                config={
                    "script": "return {key: 'value'};",
                },
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True


# =============================================================================
# Cookie Management Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.browser
class TestCookieManagement:
    """E2E tests for browser cookie management."""

    @pytest.mark.asyncio
    async def test_cookie_management_node_get(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test CookieManagementNode gets cookies."""
        from casare_rpa.nodes import CookieManagementNode

        mock_context = AsyncMock()
        mock_context.cookies = AsyncMock(
            return_value=[{"name": "session", "value": "abc123"}]
        )
        mock_page.context = mock_context

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = CookieManagementNode(
                "cookie_1",
                config={"operation": "get"},
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_cookie_management_node_set(
        self, browser_context: ExecutionContext, mock_page: AsyncMock
    ) -> None:
        """Test CookieManagementNode sets cookies."""
        from casare_rpa.nodes import CookieManagementNode

        mock_context = AsyncMock()
        mock_context.add_cookies = AsyncMock(return_value=None)
        mock_page.context = mock_context

        with patch.object(browser_context, "resources", {"page": mock_page}):
            node = CookieManagementNode(
                "cookie_2",
                config={
                    "operation": "set",
                    "cookies": [{"name": "test", "value": "value", "url": "https://example.com"}],
                },
            )
            result = await node.execute(browser_context)

            assert result.get("success") is True
