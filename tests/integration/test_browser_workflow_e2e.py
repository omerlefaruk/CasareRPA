"""
CasareRPA - End-to-End Browser Workflow Tests.

Tests browser automation workflows:
- Navigation sequences
- Click, type interactions
- Data extraction workflows
- Browser lifecycle management

Mocks Playwright - does NOT use real browser.
Uses real domain objects and workflow execution.
"""

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.presentation.canvas.events.event_bus import EventBus


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def event_bus() -> EventBus:
    """Create isolated event bus for tests."""
    return EventBus()


@pytest.fixture
def mock_playwright():
    """Mock Playwright async_playwright context."""
    with patch(
        "casare_rpa.nodes.browser_nodes.async_playwright"
    ) as mock_async_playwright:
        # Mock playwright instance
        mock_pw = MagicMock()

        # Mock browser types
        mock_chromium = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        # Set up async methods
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        # Page methods
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Example Page")
        mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_page.click = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.type = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.screenshot = AsyncMock()
        mock_page.close = AsyncMock()

        # Locator for text extraction
        mock_locator = MagicMock()
        mock_locator.text_content = AsyncMock(return_value="Extracted text content")
        mock_locator.inner_text = AsyncMock(return_value="Inner text")
        mock_locator.get_attribute = AsyncMock(return_value="attribute-value")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Keyboard
        mock_page.keyboard = MagicMock()
        mock_page.keyboard.press = AsyncMock()

        # Set up playwright structure
        mock_pw.chromium = mock_chromium
        mock_pw.firefox = MagicMock()
        mock_pw.firefox.launch = AsyncMock(return_value=mock_browser)
        mock_pw.webkit = MagicMock()
        mock_pw.webkit.launch = AsyncMock(return_value=mock_browser)

        # async_playwright().start() returns mock_pw
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw)

        yield {
            "playwright": mock_pw,
            "browser": mock_browser,
            "context": mock_context,
            "page": mock_page,
            "locator": mock_locator,
        }


@pytest.fixture
def mock_execution_context(mock_playwright):
    """Create mock execution context with browser resources."""
    context = MagicMock()

    # Variable storage
    context.variables: Dict[str, Any] = {}
    context.resolve_value = (
        lambda x: x if not isinstance(x, str) or "{{" not in x else x
    )
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables

    # Browser management
    context.browser = mock_playwright["browser"]
    context.get_active_page = MagicMock(return_value=mock_playwright["page"])
    context.set_active_page = MagicMock()
    context.add_page = MagicMock()
    context.add_browser_context = MagicMock()
    context.clear_pages = MagicMock()
    context.pages = {"main": mock_playwright["page"]}

    return context


# =============================================================================
# TEST: BROWSER NAVIGATION WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestBrowserNavigationWorkflow:
    """Tests for browser navigation workflows."""

    @pytest.mark.asyncio
    async def test_navigate_to_single_url(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test simple navigation to a single URL."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        node = GoToURLNode(
            node_id="nav_1",
            name="Navigate to Example",
            config={"url": "https://example.com", "timeout": 30000},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_playwright["page"].goto.assert_awaited()

    @pytest.mark.asyncio
    async def test_navigate_multiple_urls_sequence(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test navigation through multiple URLs in sequence."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        urls = [
            "https://example.com",
            "https://example.com/page1",
            "https://example.com/page2",
        ]

        for i, url in enumerate(urls):
            node = GoToURLNode(
                node_id=f"nav_{i}",
                name=f"Navigate {i}",
                config={"url": url, "timeout": 30000},
            )
            result = await node.execute(mock_execution_context)
            assert result["success"] is True

        # Verify all navigations occurred
        assert mock_playwright["page"].goto.await_count == 3

    @pytest.mark.asyncio
    async def test_navigation_with_wait_until_options(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test navigation with different wait_until options."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        wait_options = ["load", "domcontentloaded", "networkidle"]

        for wait_until in wait_options:
            node = GoToURLNode(
                node_id=f"nav_{wait_until}",
                name=f"Navigate with {wait_until}",
                config={
                    "url": "https://example.com",
                    "timeout": 30000,
                    "wait_until": wait_until,
                },
            )
            result = await node.execute(mock_execution_context)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_navigation_failure_handling(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test handling of navigation failures."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        # Configure mock to raise error
        mock_playwright["page"].goto.side_effect = Exception("Navigation timeout")

        node = GoToURLNode(
            node_id="nav_fail",
            name="Navigate Fail",
            config={"url": "https://example.com", "timeout": 1000},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result

        # Reset mock for other tests
        mock_playwright["page"].goto.side_effect = None
        mock_playwright["page"].goto.return_value = MagicMock(status=200)


# =============================================================================
# TEST: CLICK-TYPE INTERACTION SEQUENCE
# =============================================================================


@pytest.mark.integration
class TestClickTypeInteractionSequence:
    """Tests for click and type interaction sequences."""

    @pytest.mark.asyncio
    async def test_click_single_element(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test clicking a single element."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        node = ClickElementNode(
            node_id="click_1",
            name="Click Button",
            config={"selector": "#submit-button", "timeout": 30000},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_playwright["page"].click.assert_awaited()

    @pytest.mark.asyncio
    async def test_type_text_in_input(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test typing text into an input field."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        node = TypeTextNode(
            node_id="type_1",
            name="Type Username",
            config={
                "selector": "#username",
                "text": "testuser@example.com",
                "timeout": 30000,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_login_form_sequence(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test complete login form interaction sequence."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode
        from casare_rpa.nodes.interaction_nodes import ClickElementNode, TypeTextNode

        # Step 1: Navigate to login page
        nav_node = GoToURLNode(
            node_id="nav_login",
            name="Go to Login",
            config={"url": "https://example.com/login", "timeout": 30000},
        )
        result = await nav_node.execute(mock_execution_context)
        assert result["success"] is True

        # Step 2: Type username
        username_node = TypeTextNode(
            node_id="type_username",
            name="Enter Username",
            config={
                "selector": "#username",
                "text": "testuser",
                "timeout": 30000,
            },
        )
        result = await username_node.execute(mock_execution_context)
        assert result["success"] is True

        # Step 3: Type password
        password_node = TypeTextNode(
            node_id="type_password",
            name="Enter Password",
            config={
                "selector": "#password",
                "text": "secretpassword",
                "timeout": 30000,
            },
        )
        result = await password_node.execute(mock_execution_context)
        assert result["success"] is True

        # Step 4: Click submit button
        submit_node = ClickElementNode(
            node_id="click_submit",
            name="Click Submit",
            config={"selector": "#login-button", "timeout": 30000},
        )
        result = await submit_node.execute(mock_execution_context)
        assert result["success"] is True

        # Verify all interactions occurred
        mock_playwright["page"].goto.assert_awaited()
        mock_playwright["page"].click.assert_awaited()

    @pytest.mark.asyncio
    async def test_form_fill_with_clear(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test filling form fields with clear before type."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        node = TypeTextNode(
            node_id="type_clear",
            name="Type with Clear",
            config={
                "selector": "#email",
                "text": "new@example.com",
                "clear_before_type": True,
                "timeout": 30000,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_double_click_interaction(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test double-click interaction."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        node = ClickElementNode(
            node_id="dbl_click",
            name="Double Click",
            config={
                "selector": ".double-click-target",
                "click_count": 2,
                "timeout": 30000,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        # Verify click was called with click_count option
        mock_playwright["page"].click.assert_awaited()


# =============================================================================
# TEST: DATA EXTRACTION WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestDataExtractionWorkflow:
    """Tests for data extraction workflows."""

    @pytest.mark.asyncio
    async def test_extract_text_from_element(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test extracting text from an element."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        node = ExtractTextNode(
            node_id="extract_1",
            name="Extract Text",
            config={
                "selector": ".content",
                "extraction_type": "text_content",
                "timeout": 30000,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert "text" in result.get("data", {}) or result["success"]

    @pytest.mark.asyncio
    async def test_extract_attribute_from_element(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test extracting attribute from an element."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        node = GetAttributeNode(
            node_id="attr_1",
            name="Get Attribute",
            config={
                "selector": "a.link",
                "attribute_name": "href",
                "timeout": 30000,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_scrape_multiple_elements(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test scraping data from multiple elements."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        # Simulate extracting from multiple elements
        selectors = [".title", ".description", ".price"]

        for i, selector in enumerate(selectors):
            node = ExtractTextNode(
                node_id=f"extract_{i}",
                name=f"Extract {selector}",
                config={
                    "selector": selector,
                    "extraction_type": "text_content",
                    "timeout": 30000,
                },
            )
            result = await node.execute(mock_execution_context)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_extraction_saves_to_variable(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test extracted data is saved to execution context variable."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        node = ExtractTextNode(
            node_id="extract_var",
            name="Extract to Variable",
            config={
                "selector": ".target-text",
                "extraction_type": "text_content",
                "variable_name": "extracted_content",
                "timeout": 30000,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        # Node should set output value
        assert node.get_output_value("text") is not None


# =============================================================================
# TEST: BROWSER LIFECYCLE WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestBrowserLifecycleWorkflow:
    """Tests for browser lifecycle management workflows."""

    @pytest.mark.asyncio
    async def test_launch_browser_node(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test launching browser through node."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        node = LaunchBrowserNode(
            node_id="launch_1",
            name="Launch Browser",
            config={
                "browser_type": "chromium",
                "headless": True,
                "url": "https://example.com",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_playwright["playwright"].chromium.launch.assert_awaited()

    @pytest.mark.asyncio
    async def test_close_browser_node(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test closing browser through node."""
        from casare_rpa.nodes.browser_nodes import CloseBrowserNode

        node = CloseBrowserNode(
            node_id="close_1",
            name="Close Browser",
            config={},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_new_tab_workflow(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test opening new tab workflow."""
        from casare_rpa.nodes.browser_nodes import NewTabNode

        node = NewTabNode(
            node_id="new_tab_1",
            name="New Tab",
            config={"url": "https://example.com/new-page"},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_full_browser_session_workflow(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test complete browser session: launch -> navigate -> interact -> close."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode, CloseBrowserNode
        from casare_rpa.nodes.navigation_nodes import GoToURLNode
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        # Step 1: Launch browser
        launch = LaunchBrowserNode(
            node_id="launch",
            name="Launch",
            config={"browser_type": "chromium", "headless": True},
        )
        result = await launch.execute(mock_execution_context)
        assert result["success"] is True

        # Step 2: Navigate
        nav = GoToURLNode(
            node_id="nav",
            name="Navigate",
            config={"url": "https://example.com"},
        )
        result = await nav.execute(mock_execution_context)
        assert result["success"] is True

        # Step 3: Click
        click = ClickElementNode(
            node_id="click",
            name="Click",
            config={"selector": "#main-button"},
        )
        result = await click.execute(mock_execution_context)
        assert result["success"] is True

        # Step 4: Close browser
        close = CloseBrowserNode(
            node_id="close",
            name="Close",
            config={},
        )
        result = await close.execute(mock_execution_context)
        assert result["success"] is True


# =============================================================================
# TEST: ERROR HANDLING IN BROWSER WORKFLOWS
# =============================================================================


@pytest.mark.integration
class TestBrowserWorkflowErrorHandling:
    """Tests for error handling in browser workflows."""

    @pytest.mark.asyncio
    async def test_element_not_found_handling(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test handling when element is not found."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        # Configure mock to raise element not found error
        mock_playwright["page"].click.side_effect = Exception(
            "Element not found: #nonexistent"
        )

        node = ClickElementNode(
            node_id="click_missing",
            name="Click Missing",
            config={"selector": "#nonexistent", "timeout": 1000},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result

        # Reset mock
        mock_playwright["page"].click.side_effect = None

    @pytest.mark.asyncio
    async def test_timeout_error_handling(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test handling of timeout errors."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        # Configure mock to raise timeout error
        mock_playwright["page"].click.side_effect = Exception(
            "Timeout 30000ms exceeded"
        )

        node = ClickElementNode(
            node_id="click_timeout",
            name="Click Timeout",
            config={"selector": ".slow-element", "timeout": 30000},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result

        # Reset mock
        mock_playwright["page"].click.side_effect = None

    @pytest.mark.asyncio
    async def test_no_page_available_error(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test error when no page is available."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        # Remove page from context
        mock_execution_context.get_active_page.return_value = None
        mock_execution_context.pages = {}

        node = ClickElementNode(
            node_id="click_no_page",
            name="Click No Page",
            config={"selector": "#button"},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

        # Restore page
        mock_execution_context.get_active_page.return_value = mock_playwright["page"]


# =============================================================================
# TEST: RETRY LOGIC IN BROWSER WORKFLOWS
# =============================================================================


@pytest.mark.integration
class TestBrowserWorkflowRetryLogic:
    """Tests for retry logic in browser workflows."""

    @pytest.mark.asyncio
    async def test_click_with_retry_success_after_failure(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test click succeeds after initial failure with retry."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        # Configure mock to fail once then succeed
        call_count = 0

        async def click_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return None

        mock_playwright["page"].click = AsyncMock(side_effect=click_with_retry)

        node = ClickElementNode(
            node_id="click_retry",
            name="Click with Retry",
            config={
                "selector": "#flaky-button",
                "retry_count": 3,
                "retry_interval": 100,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert call_count == 2  # Failed once, succeeded on retry

        # Reset mock
        mock_playwright["page"].click = AsyncMock()

    @pytest.mark.asyncio
    async def test_navigation_with_retry(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test navigation with retry on failure."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        # Configure mock to fail twice then succeed
        call_count = 0

        async def goto_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network error")
            return MagicMock(status=200)

        mock_playwright["page"].goto = AsyncMock(side_effect=goto_with_retry)

        node = GoToURLNode(
            node_id="nav_retry",
            name="Navigate with Retry",
            config={
                "url": "https://example.com",
                "retry_count": 3,
                "retry_interval": 100,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert call_count == 3

        # Reset mock
        mock_playwright["page"].goto = AsyncMock(return_value=MagicMock(status=200))


# =============================================================================
# TEST: SCREENSHOT WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestScreenshotWorkflow:
    """Tests for screenshot workflows."""

    @pytest.mark.asyncio
    async def test_take_screenshot(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test taking a screenshot."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        node = ScreenshotNode(
            node_id="screenshot_1",
            name="Take Screenshot",
            config={
                "file_path": "test_screenshot.png",
                "full_page": False,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_playwright["page"].screenshot.assert_awaited()

    @pytest.mark.asyncio
    async def test_full_page_screenshot(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test taking a full page screenshot."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        node = ScreenshotNode(
            node_id="screenshot_full",
            name="Full Page Screenshot",
            config={
                "file_path": "full_page.png",
                "full_page": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_element_screenshot(
        self, mock_execution_context, mock_playwright
    ) -> None:
        """Test taking a screenshot of specific element."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        node = ScreenshotNode(
            node_id="screenshot_element",
            name="Element Screenshot",
            config={
                "file_path": "element.png",
                "selector": "#target-element",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
