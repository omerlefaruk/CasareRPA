"""
Playwright test helper utilities for CasareRPA.

Provides reusable testing utilities for browser automation nodes.
Used by tests/nodes/browser/ and can be used for workflow testing.

Usage:
    from scripts.playwright_test_helpers import create_browser_test_context

    async def test_my_node():
        async with create_browser_test_context() as ctx:
            result = await ctx.node.execute(ctx.context)
            assert result["success"]
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from loguru import logger

# =============================================================================
# Mock Page Creation
# =============================================================================


def create_full_mock_page(
    url: str = "https://example.com",
    title: str = "Test Page",
) -> AsyncMock:
    """
    Create a comprehensive mock Playwright Page object.

    Includes all common methods used by CasareRPA browser nodes:
    - Navigation: goto, reload, go_back, go_forward
    - Selectors: query_selector, wait_for_selector, locator
    - Actions: click, fill, type, press, check, select_option
    - JavaScript: evaluate, evaluate_handle
    - State: url, title, content, screenshot

    Args:
        url: Initial page URL
        title: Initial page title

    Returns:
        AsyncMock configured as Playwright Page
    """
    page = AsyncMock()

    # Properties
    page.url = url
    page.title = AsyncMock(return_value=title)
    page.content = AsyncMock(
        return_value=f"<html><head><title>{title}</title></head><body></body></html>"
    )
    page.frames = []

    # Navigation
    page.goto = AsyncMock(return_value=None)
    page.reload = AsyncMock(return_value=None)
    page.go_back = AsyncMock(return_value=None)
    page.go_forward = AsyncMock(return_value=None)

    # Selectors
    page.query_selector = AsyncMock(return_value=MagicMock())
    page.query_selector_all = AsyncMock(return_value=[])
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    page.wait_for_load_state = AsyncMock(return_value=None)

    # Actions
    page.click = AsyncMock(return_value=None)
    page.fill = AsyncMock(return_value=None)
    page.type = AsyncMock(return_value=None)
    page.press = AsyncMock(return_value=None)
    page.check = AsyncMock(return_value=None)
    page.uncheck = AsyncMock(return_value=None)
    page.select_option = AsyncMock(return_value=None)
    page.hover = AsyncMock(return_value=None)
    page.focus = AsyncMock(return_value=None)

    # JavaScript
    page.evaluate = AsyncMock(return_value={"result": "success"})
    page.evaluate_handle = AsyncMock(return_value=MagicMock())
    page.wait_for_function = AsyncMock(return_value=None)

    # Screenshots
    page.screenshot = AsyncMock(return_value=b"mock_screenshot_bytes")
    page.pdf = AsyncMock(return_value=b"mock_pdf_bytes")

    # Keyboard/Mouse
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock(return_value=None)
    page.keyboard.type = AsyncMock(return_value=None)
    page.keyboard.down = AsyncMock(return_value=None)
    page.keyboard.up = AsyncMock(return_value=None)

    page.mouse = MagicMock()
    page.mouse.click = AsyncMock(return_value=None)
    page.mouse.move = AsyncMock(return_value=None)
    page.mouse.down = AsyncMock(return_value=None)
    page.mouse.up = AsyncMock(return_value=None)
    page.mouse.wheel = AsyncMock(return_value=None)

    # Locator (modern Playwright API)
    mock_locator = AsyncMock()
    mock_locator.click = AsyncMock(return_value=None)
    mock_locator.fill = AsyncMock(return_value=None)
    mock_locator.count = AsyncMock(return_value=1)
    mock_locator.first = MagicMock(return_value=mock_locator)
    page.locator = MagicMock(return_value=mock_locator)

    logger.debug(f"Created full mock page: url={url}, title={title}")
    return page


# =============================================================================
# Test Context Builder
# =============================================================================


@asynccontextmanager
async def create_browser_test_context(
    node: Any | None = None,
    url: str = "https://example.com",
) -> AsyncGenerator[dict, None]:
    """
    Create a complete browser testing context.

    Provides:
    - mock_page: Configured Playwright Page mock
    - mock_context: ExecutionContext with page attached
    - node: Optional node instance

    Args:
        node: Optional node to test
        url: Initial page URL

    Yields:
        Dict with 'page', 'context', and optionally 'node'

    Example:
        @pytest.mark.asyncio
        async def test_my_node():
            from casare_rpa.nodes.browser.my_node import MyNode

            node = MyNode("test", config={"selector": "#btn"})
            async with create_browser_test_context(node) as ctx:
                result = await ctx["node"].execute(ctx["context"])
                assert result["success"]
    """
    from casare_rpa.infrastructure.execution import ExecutionContext

    mock_page = create_full_mock_page(url=url)

    # Create mock context
    mock_context = MagicMock(spec=ExecutionContext)
    mock_context.get_active_page = MagicMock(return_value=mock_page)
    mock_context.resolve_value = MagicMock(side_effect=lambda x: x)
    mock_context.set_variable = MagicMock()
    mock_context.get_variable = MagicMock(return_value=None)
    mock_context.variables = {}
    mock_context.resources = {}
    mock_context.workflow_id = "test-workflow"

    result = {"page": mock_page, "context": mock_context}
    if node:
        result["node"] = node

    yield result

    # Cleanup
    mock_page.reset_mock()


# =============================================================================
# Error Simulation
# =============================================================================


class ErrorSimulator:
    """
    Simulate common Playwright errors for testing error handling.

    Example:
        simulator = ErrorSimulator(mock_page)
        simulator.timeout("click")
        # Now page.click() will raise TimeoutError
    """

    def __init__(self, page: AsyncMock) -> None:
        self._page = page

    def timeout(self, method: str = "click", timeout_ms: int = 5000) -> None:
        """Make a method raise TimeoutError."""
        getattr(self._page, method).side_effect = TimeoutError(
            f"Timeout {timeout_ms}ms exceeded during {method}"
        )

    def not_found(self, method: str = "click") -> None:
        """Make a method raise element not found error."""
        getattr(self._page, method).side_effect = Exception(f"Element not found during {method}")

    def network_error(self, method: str = "goto") -> None:
        """Make a method raise network error."""
        getattr(self._page, method).side_effect = Exception("Network error")

    def detached(self, method: str = "click") -> None:
        """Make a method raise detached element error."""
        getattr(self._page, method).side_effect = Exception("Element is detached from DOM")

    def javascript_error(self, method: str = "evaluate") -> None:
        """Make a method raise JavaScript evaluation error."""
        getattr(self._page, method).side_effect = Exception("JavaScript evaluation failed")


# =============================================================================
# Screenshot Test Helpers
# =============================================================================


async def save_test_screenshot(
    page: AsyncMock,
    test_name: str,
    output_dir: str | Path = "test_screenshots",
) -> Path:
    """
    Save a screenshot during test execution.

    Args:
        page: Playwright page (mock or real)
        test_name: Name of the test for filename
        output_dir: Directory to save screenshots

    Returns:
        Path to saved screenshot
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    filename = f"{test_name.replace('/', '_').replace(' ', '_')}.png"
    filepath = output_path / filename

    await page.screenshot(path=str(filepath))
    logger.info(f"Screenshot saved: {filepath}")
    return filepath


# =============================================================================
# Wait Strategy Test Helpers
# =============================================================================


class WaitAssertions:
    """
    Assertions for wait-based operations.

    Example:
        waits = WaitAssertions()
        waits.assert_called_with_timeout(mock_page.wait_for_selector, 5000)
    """

    @staticmethod
    def assert_timeout_used(mock_method: AsyncMock, expected_timeout: int) -> None:
        """Assert method was called with specific timeout."""
        if mock_method.called:
            call_kwargs = mock_method.call_args[1] if mock_method.call_args else {}
            actual_timeout = call_kwargs.get("timeout", 0)
            assert (
                actual_timeout == expected_timeout
            ), f"Expected timeout {expected_timeout}, got {actual_timeout}"

    @staticmethod
    def assert_state_used(mock_method: AsyncMock, expected_state: str) -> None:
        """Assert wait_for_selector was called with specific state."""
        if mock_method.called:
            call_kwargs = mock_method.call_args[1] if mock_method.call_args else {}
            actual_state = call_kwargs.get("state", "")
            assert (
                actual_state == expected_state
            ), f"Expected state '{expected_state}', got '{actual_state}'"


# =============================================================================
# Page Object Model Test Helpers
# =============================================================================


class PageObjectTester:
    """
    Base class for testing page objects.

    Example:
        class TestLoginPage(PageObjectTester):
            def test_login_success(self):
                page = self.create_page()
                login_page = LoginPage(page)
                await login_page.login("user", "pass")
                assert await login_page.is_logged_in()
    """

    def create_page(self, **overrides: Any) -> AsyncMock:
        """Create a mock page for testing."""
        return create_full_mock_page(**overrides)

    def assert_element_clicked(self, page: AsyncMock, selector: str) -> None:
        """Assert element was clicked."""
        if page.click.called:
            call_args = page.click.call_args[0]
            assert selector in str(call_args), f"Expected click on {selector}"

    def assert_text_entered(self, page: AsyncMock, text: str) -> None:
        """Assert text was entered."""
        if page.fill.called:
            call_args = page.fill.call_args[0]
            assert text in str(call_args), f"Expected text '{text}' to be entered"


# =============================================================================
# Workflow Test Helpers
# =============================================================================


async def execute_browser_workflow(
    nodes: list[Any],
    initial_context: MagicMock | None = None,
) -> list[dict]:
    """
    Execute a sequence of browser nodes for testing.

    Args:
        nodes: List of node instances to execute
        initial_context: Optional pre-configured context

    Returns:
        List of execution results

    Example:
        nodes = [
            GotoUrlNode("goto", config={"url": "https://example.com"}),
            ClickElementNode("click", config={"selector": "#button"}),
        ]
        results = await execute_browser_workflow(nodes)
        assert all(r["success"] for r in results)
    """
    if initial_context is None:
        mock_page = create_full_mock_page()
        initial_context = MagicMock()
        initial_context.get_active_page = MagicMock(return_value=mock_page)
        initial_context.resolve_value = MagicMock(side_effect=lambda x: x)
        initial_context.set_variable = MagicMock()

    results = []
    for node in nodes:
        try:
            result = await node.execute(initial_context)
            results.append(result)
            if not result.get("success"):
                logger.warning(f"Node {node.node_id} failed: {result.get('error')}")
                break
        except Exception as e:
            logger.error(f"Node {node.node_id} raised exception: {e}")
            results.append({"success": False, "error": str(e)})
            break

    return results
