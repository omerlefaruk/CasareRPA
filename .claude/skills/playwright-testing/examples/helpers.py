"""
Helper functions for Playwright/browser testing.

Provides utilities for:
- Creating comprehensive mock page objects
- Wait strategies for testing
- Screenshot comparison
- Test context management
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

# =============================================================================
# Mock Page Builder
# =============================================================================


def create_mock_page(**overrides: Any) -> AsyncMock:
    """
    Create a comprehensive mock Playwright Page object.

    Args:
        **overrides: Custom return values for specific methods

    Returns:
        AsyncMock configured as a Playwright Page

    Example:
        page = create_mock_page(
            url="https://example.com",
            evaluate_return={"title": "Test"}
        )
    """
    page = AsyncMock()

    # Navigation
    page.goto = AsyncMock(return_value=overrides.get("goto_return", None))
    page.reload = AsyncMock(return_value=overrides.get("reload_return", None))
    page.go_back = AsyncMock(return_value=overrides.get("go_back_return", None))
    page.go_forward = AsyncMock(return_value=overrides.get("go_forward_return", None))

    # Selectors
    page.query_selector = AsyncMock(
        return_value=overrides.get("query_selector_return", MagicMock())
    )
    page.query_selector_all = AsyncMock(return_value=overrides.get("query_selector_all_return", []))
    page.wait_for_selector = AsyncMock(
        return_value=overrides.get("wait_for_selector_return", MagicMock())
    )
    page.wait_for_load_state = AsyncMock(
        return_value=overrides.get("wait_for_load_state_return", None)
    )
    page.locator = MagicMock(return_value=AsyncMock())

    # Actions
    page.click = AsyncMock(return_value=overrides.get("click_return", None))
    page.fill = AsyncMock(return_value=overrides.get("fill_return", None))
    page.type = AsyncMock(return_value=overrides.get("type_return", None))
    page.press = AsyncMock(return_value=overrides.get("press_return", None))
    page.check = AsyncMock(return_value=overrides.get("check_return", None))
    page.uncheck = AsyncMock(return_value=overrides.get("uncheck_return", None))
    page.select_option = AsyncMock(return_value=overrides.get("select_option_return", None))
    page.hover = AsyncMock(return_value=overrides.get("hover_return", None))
    page.focus = AsyncMock(return_value=overrides.get("focus_return", None))

    # JavaScript execution
    page.evaluate = AsyncMock(return_value=overrides.get("evaluate_return", {"data": "test"}))
    page.evaluate_handle = AsyncMock(
        return_value=overrides.get("evaluate_handle_return", MagicMock())
    )

    # State/Content
    page.url = overrides.get("url", "https://example.com")
    page.title = AsyncMock(return_value=overrides.get("title", "Example Page"))
    page.content = AsyncMock(
        return_value=overrides.get("content", "<html><body>Test</body></html>")
    )
    page.screenshot = AsyncMock(return_value=overrides.get("screenshot_return", b"fake-screenshot"))
    page.pdf = AsyncMock(return_value=overrides.get("pdf_return", b"fake-pdf"))

    # Frame handling
    page.frames = overrides.get("frames", [])
    page.main_frame = overrides.get("main_frame", MagicMock())

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

    return page


# =============================================================================
# Wait Strategy Helpers
# =============================================================================


async def wait_for_element(
    page: AsyncMock,
    selector: str,
    timeout: int = 5000,
    state: str = "attached",
) -> MagicMock:
    """
    Wait for an element to match the specified state.

    Args:
        page: Playwright page (mock or real)
        selector: CSS or XPath selector
        timeout: Maximum time to wait in ms
        state: Element state (attached, detached, visible, hidden)

    Returns:
        ElementHandle if found

    Raises:
        TimeoutError: If element not found within timeout
    """
    try:
        return await page.wait_for_selector(selector, timeout=timeout, state=state)
    except Exception as e:
        raise TimeoutError(f"Element {selector} not found within {timeout}ms: {e}")


async def wait_for_text(
    page: AsyncMock,
    selector: str,
    expected_text: str,
    timeout: int = 5000,
) -> bool:
    """
    Wait for element to contain specific text.

    Args:
        page: Playwright page
        selector: Element selector
        expected_text: Text to wait for
        timeout: Maximum wait time in ms

    Returns:
        True if text found
    """
    element = await wait_for_element(page, selector, timeout)
    text_content = await element.text_content()
    return expected_text in text_content


async def wait_for_url(
    page: AsyncMock,
    pattern: str,
    timeout: int = 5000,
) -> bool:
    """
    Wait for URL to match pattern.

    Args:
        page: Playwright page
        pattern: URL pattern (supports wildcards)
        timeout: Maximum wait time in ms

    Returns:
        True if URL matches
    """
    await page.wait_for_url(pattern, timeout=timeout)
    return True


# =============================================================================
# Screenshot Comparison Helpers
# =============================================================================


async def take_screenshot(
    page: AsyncMock,
    path: str,
    full_page: bool = False,
) -> bytes:
    """
    Take a screenshot of the current page.

    Args:
        page: Playwright page
        path: Where to save the screenshot
        full_page: Capture full scrollable page

    Returns:
        Screenshot bytes
    """
    return await page.screenshot(path=path, full_page=full_page)


def screenshot_matches(
    actual_bytes: bytes,
    expected_bytes: bytes,
    threshold: float = 0.01,
) -> tuple[bool, float]:
    """
    Compare two screenshots for similarity.

    Args:
        actual_bytes: Actual screenshot bytes
        expected_bytes: Expected screenshot bytes
        threshold: Maximum difference ratio (0-1)

    Returns:
        Tuple of (matches, difference_ratio)

    Note:
        This is a basic pixel comparison. For production use,
        consider using perceptual diff libraries like pytest-playwright.
    """
    if len(actual_bytes) != len(expected_bytes):
        return False, 1.0

    # Simple byte-by-byte comparison
    differences = sum(a != b for a, b in zip(actual_bytes, expected_bytes, strict=False))
    ratio = differences / len(actual_bytes)

    return ratio <= threshold, ratio


# =============================================================================
# Test Context Manager
# =============================================================================


class BrowserTestSession:
    """
    Context manager for browser testing setup/teardown.

    Example:
        async with BrowserTestSession() as session:
            page = session.page
            await page.goto("https://example.com")
            # ... test code ...
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._context = None
        self.page = None

    async def __aenter__(self):
        """Set up browser session."""
        # In real tests, this would launch actual Playwright browser
        # For unit tests, use mock page
        self.page = create_mock_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser session."""
        if self.page:
            # Cleanup if needed
            pass
        return False


# =============================================================================
# Assertion Helpers
# =============================================================================


def assert_element_visible(page_result: dict) -> None:
    """Assert element is visible in page result."""
    assert page_result.get("success") is True, f"Element not visible: {page_result.get('error')}"


def assert_element_exists(page_result: dict) -> None:
    """Assert element exists in DOM."""
    assert page_result.get("success") is True, f"Element not found: {page_result.get('error')}"


def assert_text_content(page_result: dict, expected: str) -> None:
    """Assert element contains expected text."""
    assert page_result.get("success") is True
    actual = page_result.get("data", {}).get("text", "")
    assert expected in actual, f"Expected '{expected}' in '{actual}'"


# =============================================================================
# Error Simulation Helpers
# =============================================================================


def simulate_timeout_error(page: AsyncMock, method: str = "click") -> None:
    """Configure mock page to raise timeout error."""
    getattr(page, method).side_effect = TimeoutError(f"Timeout 5000ms exceeded during {method}")


def simulate_element_not_found(page: AsyncMock, method: str = "click") -> None:
    """Configure mock page to raise element not found error."""
    getattr(page, method).side_effect = Exception("Element not found")


def simulate_network_error(page: AsyncMock, method: str = "goto") -> None:
    """Configure mock page to raise network error."""
    getattr(page, method).side_effect = Exception("Network error")
