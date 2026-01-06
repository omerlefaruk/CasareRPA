"""
Integration tests for Variable Resolution.

Tests variable resolution across scopes (workflow, project, global)
with real ExecutionContext.
"""

import pytest

from casare_rpa.domain.entities.project import VariableScope, VariablesFile
from casare_rpa.domain.entities.variable import Variable
from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage


@pytest.mark.integration
@pytest.mark.asyncio
async def test_variable_resolution_workflow_scope(
    execution_context: ExecutionContext,
):
    """Test setting and getting workflow-scoped variables."""
    # Arrange: Set workflow variables
    execution_context.set_variable("name", "WorkflowTest")
    execution_context.set_variable("count", 42)
    execution_context.set_variable("enabled", True)

    # Assert: Simple variable
    assert execution_context.get_variable("name") == "WorkflowTest"

    # Assert: Integer variable
    assert execution_context.get_variable("count") == 42

    # Assert: Boolean variable
    assert execution_context.get_variable("enabled") is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_variable_resolution_with_defaults(
    execution_context: ExecutionContext,
):
    """Test getting undefined variables returns None."""
    # Arrange: Set only some variables
    execution_context.set_variable("greeting", "Hello")
    # 'name' is NOT set

    # Assert: Existing variable returns value
    assert execution_context.get_variable("greeting") == "Hello"

    # Assert: Missing variable returns None
    assert execution_context.get_variable("missing_var") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_global_variables_persistence(
    sandbox_config: dict,
):
    """Test that global variables persist to disk and load back."""
    # Arrange: Create variables file with Variable objects
    variables = VariablesFile(scope=VariableScope.GLOBAL)
    var1 = Variable(
        name="global_api_key",
        type="String",
        default_value="test-key-12345",
    )
    var2 = Variable(
        name="global_timeout",
        type="Integer",
        default_value=60,
    )
    var3 = Variable(
        name="global_enabled",
        type="Boolean",
        default_value=True,
    )
    variables.set_variable(var1)
    variables.set_variable(var2)
    variables.set_variable(var3)

    # Act: Save to disk
    ProjectStorage.save_global_variables(variables)

    # Assert: File exists
    assert sandbox_config["global_variables"].exists()

    # Act: Load from disk
    loaded = ProjectStorage.load_global_variables()

    # Assert: Variables match
    assert loaded.scope == VariableScope.GLOBAL
    # get_variable returns a Variable object, access default_value
    api_key_var = loaded.get_variable("global_api_key")
    timeout_var = loaded.get_variable("global_timeout")
    enabled_var = loaded.get_variable("global_enabled")
    assert api_key_var.default_value == "test-key-12345"
    assert timeout_var.default_value == 60
    assert enabled_var.default_value is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_variables_persistence(
    sandbox_config: dict,
    sandbox_project_repository,
):
    """Test that project variables persist with the project."""
    from casare_rpa.application.use_cases import CreateProjectUseCase

    # Arrange: Create a project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = sandbox_config["config_dir"] / "var_test_project"
    result = await create_use_case.execute(name="VarTestProject", path=project_path)

    project = result.project

    # Arrange: Create project variables
    variables = VariablesFile(scope=VariableScope.PROJECT)
    var1 = Variable(
        name="project_endpoint",
        type="String",
        default_value="https://api.example.com",
    )
    var2 = Variable(
        name="project_retry_count",
        type="Integer",
        default_value=3,
    )
    variables.set_variable(var1)
    variables.set_variable(var2)

    # Act: Save variables
    ProjectStorage.save_project_variables(project, variables)

    # Assert: File exists
    assert (project.path / "variables.json").exists()

    # Act: Load variables back
    loaded = ProjectStorage.load_project_variables(project)

    # Assert: Variables match
    assert loaded.scope == VariableScope.PROJECT
    # get_variable returns a Variable object, access default_value
    endpoint_var = loaded.get_variable("project_endpoint")
    retry_var = loaded.get_variable("project_retry_count")
    assert endpoint_var.default_value == "https://api.example.com"
    assert retry_var.default_value == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_isolation():
    """Test that different ExecutionContext instances don't share variables."""
    # Arrange: Two separate contexts
    context1 = ExecutionContext(
        workflow_name="Workflow1",
        mode=ExecutionMode.NORMAL,
    )
    context2 = ExecutionContext(
        workflow_name="Workflow2",
        mode=ExecutionMode.NORMAL,
    )

    # Act: Set variable in context1 only
    context1.set_variable("shared", "from_context1")

    # Assert: Variable exists in context1
    assert context1.get_variable("shared") == "from_context1"

    # Assert: Variable does NOT exist in context2
    assert context2.get_variable("shared") is None

    # Act: Set different value in context2
    context2.set_variable("shared", "from_context2")

    # Assert: Each context has its own value
    assert context1.get_variable("shared") == "from_context1"
    assert context2.get_variable("shared") == "from_context2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_complex_types():
    """Test ExecutionContext with complex variable types."""
    context = ExecutionContext(
        workflow_name="ComplexTest",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set complex types
    context.set_variable("list_var", [1, 2, 3])
    context.set_variable("dict_var", {"key": "value", "nested": {"x": 1}})
    context.set_variable("none_var", None)

    # Assert: Complex types preserved
    assert context.get_variable("list_var") == [1, 2, 3]
    assert context.get_variable("dict_var") == {"key": "value", "nested": {"x": 1}}
    assert context.get_variable("none_var") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_update_variable():
    """Test updating existing variables."""
    context = ExecutionContext(
        workflow_name="UpdateTest",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set initial value
    context.set_variable("counter", 1)

    # Act: Update value
    context.set_variable("counter", 2)

    # Assert: New value is set
    assert context.get_variable("counter") == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_context_delete_variable():
    """Test deleting variables by setting to None."""
    context = ExecutionContext(
        workflow_name="DeleteTest",
        mode=ExecutionMode.NORMAL,
    )

    # Arrange: Set variable
    context.set_variable("temp", "value")

    # Act: Delete by setting to None
    context.set_variable("temp", None)

    # Assert: Variable is None
    assert context.get_variable("temp") is None
