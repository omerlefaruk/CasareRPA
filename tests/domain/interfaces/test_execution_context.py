"""
Tests for IExecutionContext Protocol.

Tests cover:
- Protocol compliance: verify concrete ExecutionContext implements IExecutionContext
- All interface methods: test each method/property is available
- Type checking: ensure protocol methods have correct signatures
"""

import pytest
from typing import Protocol, get_type_hints, runtime_checkable
from unittest.mock import Mock, AsyncMock

# Import the protocol
from casare_rpa.domain.interfaces.execution_context import IExecutionContext


# ============================================================================
# Protocol Definition Tests
# ============================================================================


class TestProtocolDefinition:
    """Tests for IExecutionContext protocol definition."""

    def test_iexecution_context_is_protocol(self):
        """IExecutionContext should be a Protocol."""
        assert hasattr(IExecutionContext, "__protocol_attrs__") or issubclass(
            IExecutionContext, Protocol
        )

    def test_protocol_has_expected_properties(self):
        """Protocol should define expected properties."""
        expected_properties = [
            "workflow_name",
            "mode",
            "variables",
            "resources",
            "has_project_context",
            "project_context",
            "current_node_id",
            "execution_path",
            "stopped",
        ]

        # Check methods exist on the protocol
        for prop in expected_properties:
            assert hasattr(IExecutionContext, prop), f"Missing property: {prop}"

    def test_protocol_has_variable_management_methods(self):
        """Protocol should define variable management methods."""
        expected_methods = [
            "set_variable",
            "get_variable",
            "has_variable",
            "delete_variable",
            "resolve_value",
        ]

        for method in expected_methods:
            assert hasattr(IExecutionContext, method), f"Missing method: {method}"

    def test_protocol_has_execution_flow_methods(self):
        """Protocol should define execution flow methods."""
        expected_methods = [
            "set_current_node",
            "add_error",
            "stop_execution",
            "is_stopped",
            "mark_completed",
            "get_execution_summary",
        ]

        for method in expected_methods:
            assert hasattr(IExecutionContext, method), f"Missing method: {method}"

    def test_protocol_has_browser_management_methods(self):
        """Protocol should define browser management methods."""
        expected_methods = [
            "get_active_page",
            "set_active_page",
            "get_page",
            "add_page",
        ]

        for method in expected_methods:
            assert hasattr(IExecutionContext, method), f"Missing method: {method}"

    def test_protocol_has_parallel_execution_methods(self):
        """Protocol should define parallel execution methods."""
        expected_methods = [
            "clone_for_branch",
            "create_workflow_context",
            "merge_branch_results",
        ]

        for method in expected_methods:
            assert hasattr(IExecutionContext, method), f"Missing method: {method}"

    def test_protocol_has_lifecycle_methods(self):
        """Protocol should define lifecycle methods."""
        expected_methods = [
            "cleanup",
            "pause_checkpoint",
        ]

        for method in expected_methods:
            assert hasattr(IExecutionContext, method), f"Missing method: {method}"


# ============================================================================
# Concrete Implementation Compliance Tests
# ============================================================================


class TestConcreteImplementation:
    """Tests to verify concrete ExecutionContext implements IExecutionContext."""

    @pytest.fixture
    def execution_context(self):
        """Create a real ExecutionContext for testing."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )
        from casare_rpa.domain.value_objects.types import ExecutionMode

        return ExecutionContext(
            workflow_name="TestWorkflow",
            mode=ExecutionMode.NORMAL,
            initial_variables={"test_var": "test_value"},
        )

    def test_concrete_has_workflow_name(self, execution_context):
        """Concrete implementation should have workflow_name property."""
        assert hasattr(execution_context, "workflow_name")
        assert execution_context.workflow_name == "TestWorkflow"

    def test_concrete_has_mode(self, execution_context):
        """Concrete implementation should have mode property."""
        from casare_rpa.domain.value_objects.types import ExecutionMode

        assert hasattr(execution_context, "mode")
        assert execution_context.mode == ExecutionMode.NORMAL

    def test_concrete_has_variables(self, execution_context):
        """Concrete implementation should have variables property."""
        assert hasattr(execution_context, "variables")
        assert isinstance(execution_context.variables, dict)
        assert execution_context.variables.get("test_var") == "test_value"

    def test_concrete_has_resources(self, execution_context):
        """Concrete implementation should have resources property."""
        assert hasattr(execution_context, "resources")
        assert isinstance(execution_context.resources, dict)

    def test_concrete_has_stopped(self, execution_context):
        """Concrete implementation should have stopped property."""
        assert hasattr(execution_context, "stopped")
        assert execution_context.stopped is False

    def test_concrete_set_variable(self, execution_context):
        """Concrete implementation should implement set_variable."""
        execution_context.set_variable("new_var", "new_value")
        assert execution_context.get_variable("new_var") == "new_value"

    def test_concrete_get_variable(self, execution_context):
        """Concrete implementation should implement get_variable."""
        result = execution_context.get_variable("test_var")
        assert result == "test_value"

    def test_concrete_get_variable_with_default(self, execution_context):
        """Concrete implementation should return default for missing variable."""
        result = execution_context.get_variable("nonexistent", "default")
        assert result == "default"

    def test_concrete_has_variable(self, execution_context):
        """Concrete implementation should implement has_variable."""
        assert execution_context.has_variable("test_var") is True
        assert execution_context.has_variable("nonexistent") is False

    def test_concrete_delete_variable(self, execution_context):
        """Concrete implementation should implement delete_variable."""
        execution_context.set_variable("to_delete", "value")
        assert execution_context.has_variable("to_delete")
        execution_context.delete_variable("to_delete")
        assert not execution_context.has_variable("to_delete")

    def test_concrete_resolve_value(self, execution_context):
        """Concrete implementation should implement resolve_value."""
        # Simple values should pass through
        assert execution_context.resolve_value("plain_text") == "plain_text"
        assert execution_context.resolve_value(42) == 42

    def test_concrete_stop_execution(self, execution_context):
        """Concrete implementation should implement stop_execution."""
        assert execution_context.stopped is False
        execution_context.stop_execution()
        assert execution_context.stopped is True

    def test_concrete_is_stopped(self, execution_context):
        """Concrete implementation should implement is_stopped."""
        assert execution_context.is_stopped() is False
        execution_context.stop_execution()
        assert execution_context.is_stopped() is True

    def test_concrete_get_execution_summary(self, execution_context):
        """Concrete implementation should implement get_execution_summary."""
        summary = execution_context.get_execution_summary()
        assert isinstance(summary, dict)
        assert "workflow_name" in summary or "name" in summary

    def test_concrete_has_project_context(self, execution_context):
        """Concrete implementation should implement has_project_context."""
        assert hasattr(execution_context, "has_project_context")
        # Without project context, should return False
        assert execution_context.has_project_context is False

    def test_concrete_project_context(self, execution_context):
        """Concrete implementation should implement project_context."""
        assert hasattr(execution_context, "project_context")
        # Without project context, should return None
        assert execution_context.project_context is None

    def test_concrete_current_node_id(self, execution_context):
        """Concrete implementation should implement current_node_id."""
        assert hasattr(execution_context, "current_node_id")
        # Initially None
        assert execution_context.current_node_id is None

    def test_concrete_execution_path(self, execution_context):
        """Concrete implementation should implement execution_path."""
        assert hasattr(execution_context, "execution_path")
        assert isinstance(execution_context.execution_path, list)

    def test_concrete_get_active_page(self, execution_context):
        """Concrete implementation should implement get_active_page."""
        result = execution_context.get_active_page()
        # Initially None
        assert result is None

    def test_concrete_get_page(self, execution_context):
        """Concrete implementation should implement get_page."""
        result = execution_context.get_page("default")
        # Initially None
        assert result is None

    def test_concrete_clone_for_branch(self, execution_context):
        """Concrete implementation should implement clone_for_branch."""
        branch_context = execution_context.clone_for_branch("test_branch")
        assert branch_context is not execution_context
        # Variables should be copied
        assert branch_context.get_variable("test_var") == "test_value"

    def test_concrete_create_workflow_context(self, execution_context):
        """Concrete implementation should implement create_workflow_context."""
        workflow_context = execution_context.create_workflow_context("sub_workflow")
        assert workflow_context is not execution_context
        # Variables should be shared (same reference)
        execution_context.set_variable("shared_var", "shared_value")
        assert workflow_context.get_variable("shared_var") == "shared_value"

    def test_concrete_merge_branch_results(self, execution_context):
        """Concrete implementation should implement merge_branch_results."""
        branch_variables = {"result_a": 1, "result_b": 2}
        execution_context.merge_branch_results("branch1", branch_variables)
        # Variables should be namespaced
        assert execution_context.get_variable("branch1_result_a") == 1
        assert execution_context.get_variable("branch1_result_b") == 2


# ============================================================================
# Async Method Tests
# ============================================================================


class TestAsyncMethods:
    """Tests for async methods of IExecutionContext."""

    @pytest.fixture
    def execution_context(self):
        """Create a real ExecutionContext for testing."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )
        from casare_rpa.domain.value_objects.types import ExecutionMode

        return ExecutionContext(
            workflow_name="TestWorkflow",
            mode=ExecutionMode.NORMAL,
        )

    @pytest.mark.asyncio
    async def test_cleanup_is_async(self, execution_context):
        """cleanup should be an async method."""
        import asyncio
        import inspect

        assert inspect.iscoroutinefunction(execution_context.cleanup)
        # Should not raise
        await execution_context.cleanup()

    @pytest.mark.asyncio
    async def test_pause_checkpoint_is_async(self, execution_context):
        """pause_checkpoint should be an async method."""
        import inspect

        assert inspect.iscoroutinefunction(execution_context.pause_checkpoint)
        # Should not raise (pause_event is set by default)
        await execution_context.pause_checkpoint()


# ============================================================================
# Mock Implementation Tests
# ============================================================================


class TestMockImplementation:
    """Tests using mock implementation to verify protocol usage patterns."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock that follows IExecutionContext protocol."""
        context = Mock()
        context.workflow_name = "MockWorkflow"
        context.mode = Mock()
        context.variables = {}
        context.resources = {}
        context.has_project_context = False
        context.project_context = None
        context.current_node_id = None
        context.execution_path = []
        context.stopped = False

        # Variable management
        context.set_variable = Mock()
        context.get_variable = Mock(return_value="mock_value")
        context.has_variable = Mock(return_value=True)
        context.delete_variable = Mock()
        context.resolve_value = Mock(side_effect=lambda x: x)

        # Execution flow
        context.set_current_node = Mock()
        context.add_error = Mock()
        context.stop_execution = Mock()
        context.is_stopped = Mock(return_value=False)
        context.mark_completed = Mock()
        context.get_execution_summary = Mock(return_value={})

        # Browser management
        context.get_active_page = Mock(return_value=None)
        context.set_active_page = Mock()
        context.get_page = Mock(return_value=None)
        context.add_page = Mock()

        # Parallel execution
        context.clone_for_branch = Mock(return_value=Mock())
        context.create_workflow_context = Mock(return_value=Mock())
        context.merge_branch_results = Mock()

        # Lifecycle
        context.cleanup = AsyncMock()
        context.pause_checkpoint = AsyncMock()

        return context

    def test_mock_can_be_used_as_context(self, mock_context):
        """Mock context should work in place of real context."""
        # Simulate node execution using the context
        mock_context.set_variable("output", "result")
        mock_context.set_variable.assert_called_once_with("output", "result")

        value = mock_context.get_variable("input")
        mock_context.get_variable.assert_called_once_with("input")
        assert value == "mock_value"

    def test_mock_execution_flow(self, mock_context):
        """Mock context should support execution flow operations."""
        from casare_rpa.domain.value_objects.types import NodeId

        node_id = NodeId("test_node")

        mock_context.set_current_node(node_id)
        mock_context.set_current_node.assert_called_once_with(node_id)

        mock_context.add_error(node_id, "Test error")
        mock_context.add_error.assert_called_once_with(node_id, "Test error")

    @pytest.mark.asyncio
    async def test_mock_async_methods(self, mock_context):
        """Mock context async methods should work correctly."""
        await mock_context.cleanup()
        mock_context.cleanup.assert_awaited_once()

        await mock_context.pause_checkpoint()
        mock_context.pause_checkpoint.assert_awaited_once()


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def execution_context(self):
        """Create a real ExecutionContext for testing."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )
        from casare_rpa.domain.value_objects.types import ExecutionMode

        return ExecutionContext(
            workflow_name="TestWorkflow",
            mode=ExecutionMode.NORMAL,
        )

    def test_set_variable_with_none_value(self, execution_context):
        """Setting variable to None should work."""
        execution_context.set_variable("null_var", None)
        assert execution_context.get_variable("null_var") is None
        assert execution_context.has_variable("null_var") is True

    def test_set_variable_with_complex_value(self, execution_context):
        """Setting variable to complex object should work."""
        complex_obj = {"nested": {"deep": [1, 2, 3]}}
        execution_context.set_variable("complex_var", complex_obj)
        assert execution_context.get_variable("complex_var") == complex_obj

    def test_delete_nonexistent_variable(self, execution_context):
        """Deleting nonexistent variable should not raise."""
        # Should not raise
        execution_context.delete_variable("nonexistent")

    def test_empty_workflow_name(self):
        """ExecutionContext should work with empty workflow name."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )
        from casare_rpa.domain.value_objects.types import ExecutionMode

        context = ExecutionContext(workflow_name="", mode=ExecutionMode.NORMAL)
        assert context.workflow_name == ""

    def test_multiple_stop_calls(self, execution_context):
        """Multiple stop_execution calls should be idempotent."""
        execution_context.stop_execution()
        execution_context.stop_execution()
        execution_context.stop_execution()
        assert execution_context.stopped is True

    def test_clone_preserves_mode(self, execution_context):
        """clone_for_branch should preserve execution mode."""
        from casare_rpa.domain.value_objects.types import ExecutionMode

        branch = execution_context.clone_for_branch("test_branch")
        assert branch.mode == execution_context.mode
