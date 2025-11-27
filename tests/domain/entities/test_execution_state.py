"""
Tests for ExecutionState domain entity.
Covers state tracking, variable management, execution flow.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.domain.value_objects.types import ExecutionMode


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_project_context() -> MagicMock:
    """Create mock project context."""
    ctx = MagicMock()
    ctx.get_global_variables.return_value = {"global_var": "global_value"}
    ctx.get_project_variables.return_value = {"project_var": "project_value"}
    ctx.get_scenario_variables.return_value = {"scenario_var": "scenario_value"}
    ctx.resolve_credential_path.return_value = "vault/path/to/cred"
    return ctx


# ============================================================================
# Initialization Tests
# ============================================================================


class TestExecutionStateInitialization:
    """Tests for ExecutionState initialization."""

    def test_create_default_state(self) -> None:
        """Create state with defaults."""
        state = ExecutionState()
        assert state.workflow_name == "Untitled"
        assert state.mode == ExecutionMode.NORMAL
        assert state.started_at is not None
        assert state.completed_at is None
        assert state.stopped is False

    def test_create_with_workflow_name(self) -> None:
        """Create state with workflow name."""
        state = ExecutionState(workflow_name="My Workflow")
        assert state.workflow_name == "My Workflow"

    def test_create_with_debug_mode(self) -> None:
        """Create state with debug mode."""
        state = ExecutionState(mode=ExecutionMode.DEBUG)
        assert state.mode == ExecutionMode.DEBUG

    def test_create_with_validate_mode(self) -> None:
        """Create state with validate mode."""
        state = ExecutionState(mode=ExecutionMode.VALIDATE)
        assert state.mode == ExecutionMode.VALIDATE

    def test_create_with_initial_variables(self) -> None:
        """Create state with initial variables."""
        state = ExecutionState(initial_variables={"x": 1, "y": "hello"})
        assert state.get_variable("x") == 1
        assert state.get_variable("y") == "hello"

    def test_create_with_project_context(self, mock_project_context: MagicMock) -> None:
        """Create state with project context."""
        state = ExecutionState(project_context=mock_project_context)
        assert state.has_project_context is True
        assert state.project_context == mock_project_context


# ============================================================================
# Variable Hierarchy Tests
# ============================================================================


class TestVariableHierarchy:
    """Tests for variable scoping hierarchy."""

    def test_global_variables_loaded(self, mock_project_context: MagicMock) -> None:
        """Global variables are loaded from context."""
        state = ExecutionState(project_context=mock_project_context)
        assert state.get_variable("global_var") == "global_value"

    def test_project_overrides_global(self, mock_project_context: MagicMock) -> None:
        """Project variables override global."""
        mock_project_context.get_global_variables.return_value = {"shared": "global"}
        mock_project_context.get_project_variables.return_value = {"shared": "project"}
        mock_project_context.get_scenario_variables.return_value = {}

        state = ExecutionState(project_context=mock_project_context)
        assert state.get_variable("shared") == "project"

    def test_scenario_overrides_project(self, mock_project_context: MagicMock) -> None:
        """Scenario variables override project."""
        mock_project_context.get_global_variables.return_value = {}
        mock_project_context.get_project_variables.return_value = {"shared": "project"}
        mock_project_context.get_scenario_variables.return_value = {
            "shared": "scenario"
        }

        state = ExecutionState(project_context=mock_project_context)
        assert state.get_variable("shared") == "scenario"

    def test_runtime_overrides_scenario(self, mock_project_context: MagicMock) -> None:
        """Runtime variables override scenario."""
        mock_project_context.get_scenario_variables.return_value = {
            "shared": "scenario"
        }

        state = ExecutionState(
            project_context=mock_project_context,
            initial_variables={"shared": "runtime"},
        )
        assert state.get_variable("shared") == "runtime"

    def test_all_scopes_merge(self, mock_project_context: MagicMock) -> None:
        """All scopes merge with proper priority."""
        mock_project_context.get_global_variables.return_value = {"a": 1}
        mock_project_context.get_project_variables.return_value = {"b": 2}
        mock_project_context.get_scenario_variables.return_value = {"c": 3}

        state = ExecutionState(
            project_context=mock_project_context,
            initial_variables={"d": 4},
        )
        assert state.get_variable("a") == 1
        assert state.get_variable("b") == 2
        assert state.get_variable("c") == 3
        assert state.get_variable("d") == 4


# ============================================================================
# Variable Management Tests
# ============================================================================


class TestVariableManagement:
    """Tests for variable get/set/delete operations."""

    def test_set_variable(self) -> None:
        """Set a variable."""
        state = ExecutionState()
        state.set_variable("count", 42)
        assert state.get_variable("count") == 42

    def test_set_variable_overwrites(self) -> None:
        """Setting variable overwrites existing."""
        state = ExecutionState(initial_variables={"x": 1})
        state.set_variable("x", 2)
        assert state.get_variable("x") == 2

    def test_get_variable_exists(self) -> None:
        """Get existing variable."""
        state = ExecutionState(initial_variables={"name": "test"})
        assert state.get_variable("name") == "test"

    def test_get_variable_not_exists_default(self) -> None:
        """Get non-existing variable returns default."""
        state = ExecutionState()
        assert state.get_variable("missing") is None
        assert state.get_variable("missing", "default") == "default"

    def test_has_variable_true(self) -> None:
        """has_variable returns True for existing."""
        state = ExecutionState(initial_variables={"exists": True})
        assert state.has_variable("exists") is True

    def test_has_variable_false(self) -> None:
        """has_variable returns False for non-existing."""
        state = ExecutionState()
        assert state.has_variable("missing") is False

    def test_delete_variable(self) -> None:
        """Delete a variable."""
        state = ExecutionState(initial_variables={"to_delete": "value"})
        state.delete_variable("to_delete")
        assert state.has_variable("to_delete") is False

    def test_delete_variable_not_exists(self) -> None:
        """Deleting non-existing variable is silent."""
        state = ExecutionState()
        state.delete_variable("missing")  # Should not raise

    def test_clear_variables(self) -> None:
        """Clear all variables."""
        state = ExecutionState(initial_variables={"a": 1, "b": 2, "c": 3})
        state.clear_variables()
        assert len(state.variables) == 0


# ============================================================================
# Variable Types Tests
# ============================================================================


class TestVariableTypes:
    """Tests for various variable types."""

    def test_string_variable(self) -> None:
        """String variable storage."""
        state = ExecutionState()
        state.set_variable("text", "Hello, World!")
        assert state.get_variable("text") == "Hello, World!"

    def test_integer_variable(self) -> None:
        """Integer variable storage."""
        state = ExecutionState()
        state.set_variable("num", 42)
        assert state.get_variable("num") == 42

    def test_float_variable(self) -> None:
        """Float variable storage."""
        state = ExecutionState()
        state.set_variable("pi", 3.14159)
        assert state.get_variable("pi") == 3.14159

    def test_boolean_variable(self) -> None:
        """Boolean variable storage."""
        state = ExecutionState()
        state.set_variable("flag", True)
        assert state.get_variable("flag") is True

    def test_list_variable(self) -> None:
        """List variable storage."""
        state = ExecutionState()
        state.set_variable("items", [1, 2, 3])
        assert state.get_variable("items") == [1, 2, 3]

    def test_dict_variable(self) -> None:
        """Dict variable storage."""
        state = ExecutionState()
        state.set_variable("config", {"key": "value"})
        assert state.get_variable("config") == {"key": "value"}

    def test_none_variable(self) -> None:
        """None variable storage."""
        state = ExecutionState()
        state.set_variable("empty", None)
        assert state.get_variable("empty") is None
        assert state.has_variable("empty") is True


# ============================================================================
# Credential Resolution Tests
# ============================================================================


class TestCredentialResolution:
    """Tests for credential path resolution."""

    def test_resolve_credential_with_context(
        self, mock_project_context: MagicMock
    ) -> None:
        """Resolve credential with project context."""
        state = ExecutionState(project_context=mock_project_context)
        path = state.resolve_credential_path("my_cred")
        assert path == "vault/path/to/cred"
        mock_project_context.resolve_credential_path.assert_called_with("my_cred")

    def test_resolve_credential_no_context(self) -> None:
        """Resolve credential without context returns None."""
        state = ExecutionState()
        path = state.resolve_credential_path("my_cred")
        assert path is None


# ============================================================================
# Execution Flow Tests
# ============================================================================


class TestExecutionFlow:
    """Tests for execution flow tracking."""

    def test_set_current_node(self) -> None:
        """Set current executing node."""
        state = ExecutionState()
        state.set_current_node("node_001")
        assert state.current_node_id == "node_001"

    def test_execution_path_tracked(self) -> None:
        """Execution path is tracked."""
        state = ExecutionState()
        state.set_current_node("node_001")
        state.set_current_node("node_002")
        state.set_current_node("node_003")
        path = state.get_execution_path()
        assert path == ["node_001", "node_002", "node_003"]

    def test_execution_path_copy(self) -> None:
        """get_execution_path returns a copy."""
        state = ExecutionState()
        state.set_current_node("node_001")
        path = state.get_execution_path()
        path.append("fake_node")
        assert len(state.execution_path) == 1


# ============================================================================
# Error Tracking Tests
# ============================================================================


class TestErrorTracking:
    """Tests for error tracking."""

    def test_add_error(self) -> None:
        """Add error to state."""
        state = ExecutionState()
        state.add_error("node_001", "Something went wrong")
        errors = state.get_errors()
        assert len(errors) == 1
        assert errors[0] == ("node_001", "Something went wrong")

    def test_add_multiple_errors(self) -> None:
        """Add multiple errors."""
        state = ExecutionState()
        state.add_error("node_001", "Error 1")
        state.add_error("node_002", "Error 2")
        assert len(state.errors) == 2

    def test_get_errors_copy(self) -> None:
        """get_errors returns a copy."""
        state = ExecutionState()
        state.add_error("node_001", "Error")
        errors = state.get_errors()
        errors.append(("fake", "fake"))
        assert len(state.errors) == 1


# ============================================================================
# Stop Control Tests
# ============================================================================


class TestStopControl:
    """Tests for stop control."""

    def test_initial_not_stopped(self) -> None:
        """State starts not stopped."""
        state = ExecutionState()
        assert state.is_stopped() is False

    def test_stop(self) -> None:
        """Stop the execution."""
        state = ExecutionState()
        state.stop()
        assert state.is_stopped() is True

    def test_stopped_flag(self) -> None:
        """Direct stopped flag access."""
        state = ExecutionState()
        state.stopped = True
        assert state.is_stopped() is True


# ============================================================================
# Completion Tests
# ============================================================================


class TestCompletion:
    """Tests for marking completion."""

    def test_mark_completed(self) -> None:
        """Mark execution as completed."""
        state = ExecutionState()
        assert state.completed_at is None
        state.mark_completed()
        assert state.completed_at is not None

    def test_completed_after_started(self) -> None:
        """Completed timestamp is after started."""
        state = ExecutionState()
        state.mark_completed()
        assert state.completed_at >= state.started_at


# ============================================================================
# Execution Summary Tests
# ============================================================================


class TestExecutionSummary:
    """Tests for execution summary."""

    def test_summary_basic(self) -> None:
        """Basic summary fields."""
        state = ExecutionState(workflow_name="Test Flow")
        summary = state.get_execution_summary()
        assert summary["workflow_name"] == "Test Flow"
        assert summary["mode"] == "NORMAL"
        assert summary["started_at"] is not None
        assert summary["completed_at"] is None
        assert summary["duration_seconds"] is None

    def test_summary_with_execution(self) -> None:
        """Summary after execution."""
        state = ExecutionState()
        state.set_current_node("node_1")
        state.set_current_node("node_2")
        state.add_error("node_2", "Error")
        state.mark_completed()

        summary = state.get_execution_summary()
        assert summary["nodes_executed"] == 2
        assert summary["execution_path"] == ["node_1", "node_2"]
        assert len(summary["errors"]) == 1
        assert summary["duration_seconds"] is not None

    def test_summary_variables_count(self) -> None:
        """Summary includes variables count."""
        state = ExecutionState(initial_variables={"a": 1, "b": 2})
        summary = state.get_execution_summary()
        assert summary["variables_count"] == 2


# ============================================================================
# String Representation Tests
# ============================================================================


class TestExecutionStateRepr:
    """Tests for __repr__ method."""

    def test_repr_basic(self) -> None:
        """Basic string representation."""
        state = ExecutionState(workflow_name="Demo")
        rep = repr(state)
        assert "Demo" in rep
        assert "NORMAL" in rep

    def test_repr_with_execution(self) -> None:
        """Repr shows executed nodes count."""
        state = ExecutionState()
        state.set_current_node("n1")
        state.set_current_node("n2")
        rep = repr(state)
        assert "nodes_executed=2" in rep


# ============================================================================
# Property Access Tests
# ============================================================================


class TestPropertyAccess:
    """Tests for property accessors."""

    def test_project_context_property(self, mock_project_context: MagicMock) -> None:
        """Access project context property."""
        state = ExecutionState(project_context=mock_project_context)
        assert state.project_context == mock_project_context

    def test_project_context_none(self) -> None:
        """Project context is None when not set."""
        state = ExecutionState()
        assert state.project_context is None

    def test_has_project_context_true(self, mock_project_context: MagicMock) -> None:
        """has_project_context returns True."""
        state = ExecutionState(project_context=mock_project_context)
        assert state.has_project_context is True

    def test_has_project_context_false(self) -> None:
        """has_project_context returns False."""
        state = ExecutionState()
        assert state.has_project_context is False
