"""
Shared fixtures for browser node tests.

Provides mock execution context, mock browser, and mock page objects
for testing browser automation nodes without launching real browsers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Optional


@pytest.fixture
def mock_page():
    """
    Create a mock Playwright page object.

    Returns:
        Mock page with async methods for navigation, interaction, and data extraction.
    """
    page = MagicMock()
    page.url = "https://example.com"

    # Navigation methods
    page.goto = AsyncMock(return_value=Mock(status=200))
    page.go_back = AsyncMock()
    page.go_forward = AsyncMock()
    page.reload = AsyncMock()
    page.close = AsyncMock()

    # Wait methods
    page.wait_for_selector = AsyncMock(return_value=Mock())
    page.wait_for_load_state = AsyncMock()

    # Interaction methods
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.type = AsyncMock()
    page.select_option = AsyncMock()

    # Data extraction
    page.evaluate = AsyncMock(return_value=[])
    page.screenshot = AsyncMock()

    # Locator
    mock_locator = MagicMock()
    mock_locator.text_content = AsyncMock(return_value="Test text content")
    mock_locator.inner_text = AsyncMock(return_value="Test inner text")
    mock_locator.get_attribute = AsyncMock(return_value="test-value")
    mock_locator.screenshot = AsyncMock()
    mock_locator.first = mock_locator
    page.locator = MagicMock(return_value=mock_locator)

    # Keyboard
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()

    return page


@pytest.fixture
def mock_browser_context(mock_page):
    """
    Create a mock Playwright browser context.

    Returns:
        Mock browser context that creates mock pages.
    """
    context = MagicMock()
    context.new_page = AsyncMock(return_value=mock_page)
    context.close = AsyncMock()
    return context


@pytest.fixture
def mock_browser(mock_browser_context):
    """
    Create a mock Playwright browser object.

    Returns:
        Mock browser that creates mock contexts.
    """
    browser = MagicMock()
    browser.new_context = AsyncMock(return_value=mock_browser_context)
    browser.close = AsyncMock()
    browser.contexts = [mock_browser_context]
    return browser


@pytest.fixture
def execution_context(mock_page, mock_browser):
    """
    Create a mock execution context with browser resources.

    Returns:
        Mock ExecutionContext with variable storage and browser management.
    """
    context = MagicMock()

    # Variable storage
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x if not isinstance(x, str) else x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables

    # Browser management
    context.browser = mock_browser
    context.get_active_page = MagicMock(return_value=mock_page)
    context.set_active_page = MagicMock()
    context.add_page = MagicMock()
    context.add_browser_context = MagicMock()
    context.clear_pages = MagicMock()

    # Pages dict
    context.pages = {"main": mock_page}

    return context


@pytest.fixture
def execution_context_no_browser():
    """
    Create a mock execution context without browser.

    Returns:
        Mock ExecutionContext with no browser/page resources.
    """
    context = MagicMock()

    # Variable storage
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x if not isinstance(x, str) else x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )

    # No browser
    context.browser = None
    context.get_active_page = MagicMock(return_value=None)
    context.pages = {}

    return context


@pytest.fixture
def execution_context_no_page(mock_browser):
    """
    Create a mock execution context with browser but no active page.

    Returns:
        Mock ExecutionContext with browser but no active page.
    """
    context = MagicMock()

    # Variable storage
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x if not isinstance(x, str) else x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )

    # Browser but no page
    context.browser = mock_browser
    context.get_active_page = MagicMock(return_value=None)
    context.add_browser_context = MagicMock()
    context.add_page = MagicMock()
    context.set_active_page = MagicMock()
    context.pages = {}

    return context
