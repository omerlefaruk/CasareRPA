"""
Global test fixtures for CasareRPA test suite.

Provides shared test infrastructure:
- Basic execution context fixtures for all node types
- Common mock objects and utilities
- Shared test configuration

Fixtures defined here are automatically available to all tests without import.
Use specialized conftest.py files in subdirectories for category-specific fixtures.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Any, Dict, Optional

from casare_rpa.core.execution_context import ExecutionContext


@pytest.fixture
def execution_context() -> Mock:
    """
    Create a basic mock execution context for node testing.

    Provides a minimal mock ExecutionContext with:
    - Variable storage and access methods
    - resolve_value method that returns input unchanged
    - No browser or desktop resources

    Returns:
        Mock ExecutionContext suitable for generic node tests.

    Usage:
        def test_my_node(execution_context) -> None:
            execution_context.variables['key'] = 'value'
            node = MyNode()
            result = await node.execute(execution_context)
    """
    context = Mock(spec=ExecutionContext)
    context.variables: Dict[str, Any] = {}
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
    context = Mock(spec=ExecutionContext)
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
    context = Mock(spec=ExecutionContext)
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    return context
