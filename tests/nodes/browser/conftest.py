"""
Fixtures for browser node tests.

Provides:
- Mock Playwright page object
- Mock execution context with page access
- Common browser node testing utilities
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext


@pytest.fixture
def mock_page() -> AsyncMock:
    """
    Create a mock Playwright page object.

    The mock includes common methods used by browser nodes:
    - evaluate: Execute JavaScript and return result
    - wait_for_selector: Wait for element to appear
    - screenshot: Take page screenshot
    """
    page = AsyncMock()
    page.evaluate = AsyncMock(return_value={"data": "test"})
    page.wait_for_selector = AsyncMock()
    page.screenshot = AsyncMock()
    return page


@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def mock_context(mock_page: AsyncMock) -> MagicMock:
    """
    Create a mock execution context with page access.

    The mock context provides:
    - get_active_page: Returns the mock page
    - resolve_value: Returns input unchanged (pass-through)
    - set_variable: Records variable assignments
    """
    context = MagicMock(spec=ExecutionContext)
    context.get_active_page.return_value = mock_page
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.set_variable = MagicMock()
    context.variables = {}
    context.resources = {}
    return context


@pytest.fixture
def mock_context_no_page() -> MagicMock:
    """Create a mock execution context without a page (for error testing)."""
    context = MagicMock(spec=ExecutionContext)
    context.get_active_page.return_value = None
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.set_variable = MagicMock()
    context.variables = {}
    context.resources = {}
    return context
