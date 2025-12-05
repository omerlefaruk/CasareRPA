"""
Fixtures for utility node tests.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def execution_context() -> Mock:
    """
    Create execution context for utility node testing.

    Returns:
        Mock ExecutionContext with variable storage and resolution.
    """
    context = Mock()
    context.variables = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables
    return context
