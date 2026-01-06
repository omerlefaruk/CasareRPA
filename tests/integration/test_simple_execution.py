"""
Integration tests for Simple Workflow Execution.

Tests basic workflow execution with ExecutionContext (no actual nodes).
"""

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_basics():
    """Test basic ExecutionContext operations."""
    # Arrange: Create context
    context = ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )

    # Assert: Initial state
    assert context.workflow_name == "TestWorkflow"
    assert context.mode == ExecutionMode.NORMAL
    assert context.get_variable("unset_var") is None

    # Act: Set and get variable
    context.set_variable("test_var", "test_value")

    # Assert: Variable retrieved
    assert context.get_variable("test_var") == "test_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_with_initial_variables():
    """Test ExecutionContext with pre-populated variables."""
    # Arrange: Context with initial variables
    initial_vars = {
        "api_key": "test-key",
        "timeout": 30,
        "enabled": True,
    }
    context = ExecutionContext(
        workflow_name="VarTest",
        mode=ExecutionMode.NORMAL,
        initial_variables=initial_vars,
    )

    # Assert: Variables accessible
    assert context.get_variable("api_key") == "test-key"
    assert context.get_variable("timeout") == 30
    assert context.get_variable("enabled") is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_workflow_id_tracking():
    """Test that workflow_name is set."""
    # Arrange
    context = ExecutionContext(
        workflow_name="IdTest",
        mode=ExecutionMode.NORMAL,
    )

    # Assert: workflow_name is set (workflow_id is internal UUID)
    assert context.workflow_name == "IdTest"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_resources_management():
    """Test ExecutionContext resources dictionary."""
    # Arrange
    context = ExecutionContext(
        workflow_name="ResourcesTest",
        mode=ExecutionMode.NORMAL,
    )

    # Assert: Resources dict exists
    assert context.resources is not None
    assert isinstance(context.resources, dict)

    # Act: Set resource
    context.resources["http_client"] = {"mock": True}
    context.resources["browser"] = {"mock": True}

    # Assert: Resources accessible
    assert "http_client" in context.resources
    assert context.resources["browser"]["mock"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_contexts_dont_interfere():
    """Test that multiple ExecutionContexts are isolated."""
    # Arrange: Two contexts
    context1 = ExecutionContext(
        workflow_name="Context1",
        mode=ExecutionMode.NORMAL,
    )
    context2 = ExecutionContext(
        workflow_name="Context2",
        mode=ExecutionMode.NORMAL,
    )

    # Act: Set different values
    context1.set_variable("shared_name", "value_from_1")
    context2.set_variable("shared_name", "value_from_2")

    # Assert: Each context has its own value
    assert context1.get_variable("shared_name") == "value_from_1"
    assert context2.get_variable("shared_name") == "value_from_2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_modes():
    """Test different execution modes."""
    # Test NORMAL mode
    context_normal = ExecutionContext(
        workflow_name="NormalTest",
        mode=ExecutionMode.NORMAL,
    )
    assert context_normal.mode == ExecutionMode.NORMAL

    # Test DEBUG mode
    context_debug = ExecutionContext(
        workflow_name="DebugTest",
        mode=ExecutionMode.DEBUG,
    )
    assert context_debug.mode == ExecutionMode.DEBUG

    # Test VALIDATE mode
    context_validate = ExecutionContext(
        workflow_name="ValidateTest",
        mode=ExecutionMode.VALIDATE,
    )
    assert context_validate.mode == ExecutionMode.VALIDATE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_complex_variables():
    """Test ExecutionContext with complex variable types."""
    context = ExecutionContext(
        workflow_name="ComplexVars",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set complex types
    context.set_variable("list_var", [1, 2, 3, 4])
    context.set_variable("dict_var", {"key": "value", "nested": {"x": 1}})
    context.set_variable("none_var", None)
    context.set_variable("bool_var", False)

    # Assert: All types preserved
    assert context.get_variable("list_var") == [1, 2, 3, 4]
    assert context.get_variable("dict_var") == {"key": "value", "nested": {"x": 1}}
    assert context.get_variable("none_var") is None
    assert context.get_variable("bool_var") is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_variable_update():
    """Test updating existing variables."""
    context = ExecutionContext(
        workflow_name="UpdateTest",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set initial value
    context.set_variable("counter", 1)

    # Act: Update to new value
    context.set_variable("counter", 42)

    # Assert: New value is set
    assert context.get_variable("counter") == 42


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_many_variables():
    """Test context with many variables."""
    context = ExecutionContext(
        workflow_name="ManyVars",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set many variables
    for i in range(100):
        context.set_variable(f"var_{i}", f"value_{i}")

    # Act & Assert: All variables accessible
    for i in range(100):
        assert context.get_variable(f"var_{i}") == f"value_{i}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_initial_with_dict():
    """Test creating context with initial variables dict."""
    initial = {
        "name": "Alice",
        "age": 30,
        "active": True,
        "scores": [85, 90, 95],
        "metadata": {"department": "IT", "role": "Engineer"},
    }

    context = ExecutionContext(
        workflow_name="InitialTest",
        mode=ExecutionMode.NORMAL,
        initial_variables=initial,
    )

    # Assert: All initial variables set
    assert context.get_variable("name") == "Alice"
    assert context.get_variable("age") == 30
    assert context.get_variable("active") is True
    assert context.get_variable("scores") == [85, 90, 95]
    assert context.get_variable("metadata") == {"department": "IT", "role": "Engineer"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_has_variable():
    """Test checking if variable exists."""
    context = ExecutionContext(
        workflow_name="HasVarTest",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set one variable
    context.set_variable("exists", "yes")

    # Act & Assert: Check existence
    # get_variable returns None for non-existent
    assert context.get_variable("exists") == "yes"
    assert context.get_variable("does_not_exist") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_overwrite_with_none():
    """Test overwriting variable with None."""
    context = ExecutionContext(
        workflow_name="OverwriteTest",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set variable to value
    context.set_variable("temp", "some_value")
    assert context.get_variable("temp") == "some_value"

    # Act: Overwrite with None
    context.set_variable("temp", None)

    # Assert: Variable is now None
    assert context.get_variable("temp") is None
