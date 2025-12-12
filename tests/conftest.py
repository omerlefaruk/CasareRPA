"""
Global test fixtures for CasareRPA test suite.

Provides shared test infrastructure:
- Basic execution context fixtures for all node types
- Common mock objects and utilities
- Shared test configuration
- Workflow test helpers (WorkflowTestCase, MockFactory, etc.)
- Visual regression testing utilities

Fixtures defined here are automatically available to all tests without import.
Use specialized conftest.py files in subdirectories for category-specific fixtures.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Any, Dict, List, Optional

# ExecutionContext imported for Mock spec only - actual context mocked
# Using local Mock definition to avoid deprecated import warning
# The mock doesn't need the real class, just its interface

# Import test helpers
from tests.helpers.mock_factory import MockFactory
from tests.helpers.workflow_test_case import WorkflowTestCase
from tests.helpers.workflow_assertions import WorkflowAssertions
from tests.helpers.visual_regression import VisualRegressionTest


@pytest.fixture
def execution_context() -> Mock:
    """
    Create a basic mock execution context for node testing.

    Provides a minimal mock ExecutionContext with:
    - Variable storage and access methods
    - resolve_value method that returns input unchanged
    - get_execution_summary for EndNode tests
    - No browser or desktop resources

    Returns:
        Mock ExecutionContext suitable for generic node tests.

    Usage:
        def test_my_node(execution_context) -> None:
            execution_context.variables['key'] = 'value'
            node = MyNode()
            result = await node.execute(execution_context)
    """
    context = Mock()
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables
    context.get_execution_summary = lambda: {
        "workflow_name": "Test Workflow",
        "nodes_executed": 5,
        "errors": [],
        "duration_ms": 1234,
    }
    return context


@pytest.fixture
def execution_context_with_variables() -> Mock:
    """
    Create an execution context pre-populated with common test variables.

    Provides fixture with:
    - Basic variable storage
    - Pre-set test variables (test_var, test_number, test_list, test_dict)
    - All standard execution context methods

    Returns:
        Mock ExecutionContext with pre-populated variables.

    Usage:
        def test_variable_node(execution_context_with_variables) -> None:
            # Variables already available: test_var='value', test_number=42, etc.
            result = await node.execute(execution_context_with_variables)
    """
    context = Mock()
    context.variables: Dict[str, Any] = {
        "test_var": "value",
        "test_number": 42,
        "test_list": [1, 2, 3],
        "test_dict": {"key": "value"},
        "test_boolean": True,
        "test_float": 3.14,
    }
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables
    return context


@pytest.fixture
def mock_execution_context() -> Mock:
    """
    Alias for execution_context fixture for compatibility.

    Some test files use mock_execution_context naming convention.

    Returns:
        Mock ExecutionContext.
    """
    context = Mock()
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    return context


# =============================================================================
# WORKFLOW TEST HELPERS
# =============================================================================


@pytest.fixture
def workflow_test_case() -> type:
    """
    Provide WorkflowTestCase class for fluent workflow testing.

    Usage:
        @pytest.mark.asyncio
        async def test_my_workflow(workflow_test_case):
            await (workflow_test_case(my_workflow_json)
                .given_variable('input', 'value')
                .when_executed()
                .then_succeeded()
                .then_variable_equals('output', 'expected'))

    Returns:
        WorkflowTestCase class
    """
    return WorkflowTestCase


@pytest.fixture
def workflow_assertions() -> type:
    """
    Provide WorkflowAssertions class for static assertions.

    Usage:
        def test_context_state(workflow_assertions, execution_context):
            workflow_assertions.assert_variable_equals(context, 'key', 'value')
            workflow_assertions.assert_list_length(context, 'items', 5)

    Returns:
        WorkflowAssertions class
    """
    return WorkflowAssertions


# =============================================================================
# MOCK FACTORY FIXTURES
# =============================================================================


@pytest.fixture
def mock_factory() -> type:
    """
    Provide MockFactory class for creating pre-built mocks.

    Usage:
        def test_with_mocks(mock_factory):
            page = mock_factory.mock_page()
            browser = mock_factory.mock_browser()
            response = mock_factory.mock_http_response(status=200)

    Returns:
        MockFactory class
    """
    return MockFactory


@pytest.fixture
def mock_page() -> AsyncMock:
    """
    Create a mock Playwright page.

    Returns:
        AsyncMock configured as Playwright Page
    """
    return MockFactory.mock_page()


@pytest.fixture
def mock_browser() -> AsyncMock:
    """
    Create a mock Playwright browser.

    Returns:
        AsyncMock configured as Playwright Browser
    """
    return MockFactory.mock_browser()


@pytest.fixture
def mock_browser_context() -> AsyncMock:
    """
    Create a mock Playwright browser context.

    Returns:
        AsyncMock configured as Playwright BrowserContext
    """
    return MockFactory.mock_browser_context()


@pytest.fixture
def mock_element() -> AsyncMock:
    """
    Create a mock Playwright element handle.

    Returns:
        AsyncMock configured as Playwright ElementHandle
    """
    return MockFactory.mock_element()


@pytest.fixture
def mock_http_response() -> AsyncMock:
    """
    Create a mock HTTP response with default values.

    Returns:
        AsyncMock configured as aiohttp ClientResponse
    """
    return MockFactory.mock_http_response()


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """
    Create a mock HTTP client.

    Returns:
        AsyncMock configured as HTTP client
    """
    return MockFactory.mock_http_client()


@pytest.fixture
def mock_database_connection() -> AsyncMock:
    """
    Create a mock database connection.

    Returns:
        AsyncMock configured as asyncpg Connection
    """
    return MockFactory.mock_database_connection()


@pytest.fixture
def mock_credential_provider() -> AsyncMock:
    """
    Create a mock credential provider.

    Returns:
        AsyncMock configured as VaultCredentialProvider
    """
    return MockFactory.mock_credential_provider()


@pytest.fixture
def mock_ui_control() -> MagicMock:
    """
    Create a mock UIAutomation control.

    Returns:
        MagicMock configured as UIAutomation Control
    """
    return MockFactory.mock_ui_control()


# =============================================================================
# VISUAL REGRESSION FIXTURES
# =============================================================================


@pytest.fixture
def visual_test() -> VisualRegressionTest:
    """
    Create a visual regression test helper.

    Usage:
        def test_canvas_ui(visual_test, canvas_widget):
            result = visual_test.compare_with_baseline(
                "canvas_with_nodes",
                visual_test.capture_canvas(canvas_widget)
            )
            assert result.passed

    Returns:
        VisualRegressionTest instance
    """
    return VisualRegressionTest()


# =============================================================================
# EXECUTION CONTEXT WITH BROWSER
# =============================================================================


@pytest.fixture
def execution_context_with_browser() -> Mock:
    """
    Create an execution context with mocked browser resources.

    Provides:
    - Mock page attached as active page
    - Mock browser attached
    - Standard variable methods

    Returns:
        Mock ExecutionContext with browser resources
    """
    context = Mock()
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables

    # Attach browser resources
    mock_page = MockFactory.mock_page()
    mock_browser = MockFactory.mock_browser()

    context.get_active_page = Mock(return_value=mock_page)
    context.get_page = Mock(return_value=mock_page)
    context.get_browser = Mock(return_value=mock_browser)
    context.set_active_page = Mock()
    context.set_browser = Mock()

    # Store references for test access
    context._mock_page = mock_page
    context._mock_browser = mock_browser

    return context


@pytest.fixture
def execution_context_with_http() -> Mock:
    """
    Create an execution context with mocked HTTP client.

    Returns:
        Mock ExecutionContext with HTTP client resource
    """
    context = Mock()
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables

    # Attach HTTP client
    mock_client = MockFactory.mock_http_client()
    context.resources = {"http_client": mock_client}
    context._mock_http_client = mock_client

    return context


@pytest.fixture
def execution_context_with_credentials(
    credentials: Optional[Dict[str, Any]] = None,
) -> Mock:
    """
    Create an execution context with mocked credential provider.

    Args:
        credentials: Dict of alias -> credential value to mock

    Returns:
        Mock ExecutionContext with credential provider
    """
    context = Mock()
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables

    # Attach credential provider
    mock_provider = MockFactory.mock_credential_provider(credentials or {})
    context.resources = {"credential_provider": mock_provider}
    context._credential_provider = mock_provider
    context.get_credential_provider = AsyncMock(return_value=mock_provider)
    context.resolve_credential = mock_provider.get_credential

    return context
