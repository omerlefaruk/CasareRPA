"""
CasareRPA - End-to-End Workflow Execution Tests.

Tests complete workflow execution lifecycle:
- Start to end execution flow
- Variable passing between nodes
- Error handling and recovery
- Execution state tracking
- Event propagation

Uses real domain objects, mocks only external I/O.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.presentation.canvas.events.event_bus import EventBus, Event
from casare_rpa.domain.value_objects.types import EventType
from casare_rpa.application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def event_bus() -> EventBus:
    """Create isolated event bus for tests."""
    return EventBus()


@pytest.fixture
def event_collector(event_bus: EventBus) -> Dict[str, List[Event]]:
    """Collect events by type for verification."""
    collected: Dict[str, List[Event]] = {}

    def collector(event: Event) -> None:
        event_type = str(event.type)
        if event_type not in collected:
            collected[event_type] = []
        collected[event_type].append(event)

    # Subscribe to key events
    event_bus.subscribe(EventType.WORKFLOW_STARTED, collector)
    event_bus.subscribe(EventType.WORKFLOW_COMPLETED, collector)
    event_bus.subscribe(EventType.NODE_STARTED, collector)
    event_bus.subscribe(EventType.NODE_COMPLETED, collector)
    event_bus.subscribe(EventType.WORKFLOW_FAILED, collector)

    return collected


# =============================================================================
# TEST: COMPLETE WORKFLOW EXECUTION FROM START TO END
# =============================================================================


@pytest.mark.integration
class TestCompleteWorkflowExecution:
    """Tests for complete workflow execution lifecycle."""

    @pytest.mark.asyncio
    async def test_start_to_end_execution(self, event_bus: EventBus) -> None:
        """Test workflow executes from StartNode to EndNode successfully."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Start-End-E2E"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node({"node_id": "end", "type": "EndNode"})
        workflow.connections.append(
            NodeConnection("start", "exec_out", "end", "exec_in")
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert "start" in use_case.executed_nodes
        assert "end" in use_case.executed_nodes
        assert use_case.start_time is not None
        assert use_case.end_time is not None

    @pytest.mark.asyncio
    async def test_five_node_linear_execution(self, event_bus: EventBus) -> None:
        """Test linear workflow with 5 sequential nodes."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Five-Node-Linear"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})

        for i in range(1, 4):
            workflow.add_node(
                {
                    "node_id": f"step_{i}",
                    "type": "SetVariableNode",
                    "config": {"variable_name": f"var_{i}", "default_value": i * 10},
                }
            )

        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "step_1", "exec_in"),
                NodeConnection("step_1", "exec_out", "step_2", "exec_in"),
                NodeConnection("step_2", "exec_out", "step_3", "exec_in"),
                NodeConnection("step_3", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert len(use_case.executed_nodes) == 5
        assert use_case.context.get_variable("var_1") == 10
        assert use_case.context.get_variable("var_2") == 20
        assert use_case.context.get_variable("var_3") == 30

    @pytest.mark.asyncio
    async def test_execution_state_tracking(self, event_bus: EventBus) -> None:
        """Test execution state is properly tracked throughout workflow."""
        workflow = WorkflowSchema(WorkflowMetadata(name="State-Tracking"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_var",
                "type": "SetVariableNode",
                "config": {"variable_name": "tracked", "default_value": "value"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_var", "exec_in"),
                NodeConnection("set_var", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        state = use_case.context._state
        assert state.workflow_name == "State-Tracking"
        assert len(state.execution_path) > 0
        assert state.started_at is not None
        assert state.completed_at is not None

    @pytest.mark.asyncio
    async def test_large_workflow_execution(self, event_bus: EventBus) -> None:
        """Test workflow with 20+ nodes executes correctly."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Large-Workflow"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})

        node_count = 20
        for i in range(node_count):
            workflow.add_node(
                {
                    "node_id": f"node_{i}",
                    "type": "SetVariableNode",
                    "config": {"variable_name": f"v_{i}", "default_value": i},
                }
            )

        workflow.add_node({"node_id": "end", "type": "EndNode"})

        # Connect sequentially
        workflow.connections.append(
            NodeConnection("start", "exec_out", "node_0", "exec_in")
        )
        for i in range(node_count - 1):
            workflow.connections.append(
                NodeConnection(f"node_{i}", "exec_out", f"node_{i+1}", "exec_in")
            )
        workflow.connections.append(
            NodeConnection(f"node_{node_count - 1}", "exec_out", "end", "exec_in")
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert len(use_case.executed_nodes) == node_count + 2  # +2 for start/end
        # Verify all variables set
        for i in range(node_count):
            assert use_case.context.get_variable(f"v_{i}") == i


# =============================================================================
# TEST: VARIABLE PASSING BETWEEN NODES
# =============================================================================


@pytest.mark.integration
class TestVariablePassingBetweenNodes:
    """Tests for variable passing between workflow nodes."""

    @pytest.mark.asyncio
    async def test_set_and_get_variable(self, event_bus: EventBus) -> None:
        """Test variable set by one node is accessible to next node."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Set-Get-Variable"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_var",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "shared_data",
                    "default_value": "test_value",
                },
            }
        )
        workflow.add_node(
            {
                "node_id": "get_var",
                "type": "GetVariableNode",
                "config": {"variable_name": "shared_data"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_var", "exec_in"),
                NodeConnection("set_var", "exec_out", "get_var", "exec_in"),
                NodeConnection("get_var", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("shared_data") == "test_value"

    @pytest.mark.asyncio
    async def test_variable_overwrite(self, event_bus: EventBus) -> None:
        """Test variable can be overwritten by subsequent node."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Variable-Overwrite"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_first",
                "type": "SetVariableNode",
                "config": {"variable_name": "counter", "default_value": 1},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_second",
                "type": "SetVariableNode",
                "config": {"variable_name": "counter", "default_value": 2},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_first", "exec_in"),
                NodeConnection("set_first", "exec_out", "set_second", "exec_in"),
                NodeConnection("set_second", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        # Second value should overwrite first
        assert use_case.context.get_variable("counter") == 2

    @pytest.mark.asyncio
    async def test_multiple_independent_variables(self, event_bus: EventBus) -> None:
        """Test multiple independent variables coexist correctly."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Multi-Independent-Vars"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_a",
                "type": "SetVariableNode",
                "config": {"variable_name": "var_a", "default_value": "alpha"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_b",
                "type": "SetVariableNode",
                "config": {"variable_name": "var_b", "default_value": "beta"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_c",
                "type": "SetVariableNode",
                "config": {"variable_name": "var_c", "default_value": "gamma"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_a", "exec_in"),
                NodeConnection("set_a", "exec_out", "set_b", "exec_in"),
                NodeConnection("set_b", "exec_out", "set_c", "exec_in"),
                NodeConnection("set_c", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("var_a") == "alpha"
        assert use_case.context.get_variable("var_b") == "beta"
        assert use_case.context.get_variable("var_c") == "gamma"

    @pytest.mark.asyncio
    async def test_initial_variables_passed_to_workflow(
        self, event_bus: EventBus
    ) -> None:
        """Test initial variables are available to workflow nodes."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Initial-Vars-Pass"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "check_if",
                "type": "IfNode",
                "config": {"expression": "input_flag"},
            }
        )
        workflow.add_node(
            {
                "node_id": "true_action",
                "type": "SetVariableNode",
                "config": {"variable_name": "result", "default_value": "flag_was_true"},
            }
        )
        workflow.add_node(
            {
                "node_id": "false_action",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "result",
                    "default_value": "flag_was_false",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "check_if", "exec_in"),
                NodeConnection("check_if", "true", "true_action", "exec_in"),
                NodeConnection("check_if", "false", "false_action", "exec_in"),
                NodeConnection("true_action", "exec_out", "end", "exec_in"),
                NodeConnection("false_action", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(
            workflow,
            event_bus=event_bus,
            initial_variables={"input_flag": True},
        )
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("result") == "flag_was_true"

    @pytest.mark.asyncio
    async def test_variable_types_preserved(self, event_bus: EventBus) -> None:
        """Test different variable types are preserved through execution."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Type-Preservation"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_str",
                "type": "SetVariableNode",
                "config": {"variable_name": "str_var", "default_value": "text"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_int",
                "type": "SetVariableNode",
                "config": {"variable_name": "int_var", "default_value": 42},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_float",
                "type": "SetVariableNode",
                "config": {"variable_name": "float_var", "default_value": 3.14},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_bool",
                "type": "SetVariableNode",
                "config": {"variable_name": "bool_var", "default_value": False},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_list",
                "type": "SetVariableNode",
                "config": {"variable_name": "list_var", "default_value": [1, 2, 3]},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_str", "exec_in"),
                NodeConnection("set_str", "exec_out", "set_int", "exec_in"),
                NodeConnection("set_int", "exec_out", "set_float", "exec_in"),
                NodeConnection("set_float", "exec_out", "set_bool", "exec_in"),
                NodeConnection("set_bool", "exec_out", "set_list", "exec_in"),
                NodeConnection("set_list", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("str_var") == "text"
        assert use_case.context.get_variable("int_var") == 42
        assert use_case.context.get_variable("float_var") == 3.14
        assert use_case.context.get_variable("bool_var") is False
        assert use_case.context.get_variable("list_var") == [1, 2, 3]


# =============================================================================
# TEST: ERROR HANDLING AND RECOVERY
# =============================================================================


@pytest.mark.integration
class TestErrorHandlingAndRecovery:
    """Tests for error handling and recovery in workflows."""

    @pytest.mark.asyncio
    async def test_continue_on_error_setting(self, event_bus: EventBus) -> None:
        """Test continue_on_error setting allows workflow to proceed."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Continue-On-Error"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_before",
                "type": "SetVariableNode",
                "config": {"variable_name": "before_error", "default_value": "set"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_after",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "after_continue",
                    "default_value": "continued",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_before", "exec_in"),
                NodeConnection("set_before", "exec_out", "set_after", "exec_in"),
                NodeConnection("set_after", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(
            workflow,
            event_bus=event_bus,
            settings=ExecutionSettings(continue_on_error=True),
        )
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("before_error") == "set"
        assert use_case.context.get_variable("after_continue") == "continued"

    @pytest.mark.asyncio
    async def test_workflow_handles_missing_variable_gracefully(
        self, event_bus: EventBus
    ) -> None:
        """Test workflow handles missing variable access gracefully."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Missing-Var-Handling"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "get_missing",
                "type": "GetVariableNode",
                "config": {"variable_name": "nonexistent_var"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_fallback",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "fallback",
                    "default_value": "fallback_value",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "get_missing", "exec_in"),
                NodeConnection("get_missing", "exec_out", "set_fallback", "exec_in"),
                NodeConnection("set_fallback", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(
            workflow,
            event_bus=event_bus,
            settings=ExecutionSettings(continue_on_error=True),
        )
        result = await use_case.execute()

        # Workflow should complete with fallback value
        assert use_case.context.get_variable("fallback") == "fallback_value"

    @pytest.mark.asyncio
    async def test_branching_after_error_recovery(self, event_bus: EventBus) -> None:
        """Test workflow can branch correctly after error recovery."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Branch-After-Recovery"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_flag",
                "type": "SetVariableNode",
                "config": {"variable_name": "check_flag", "default_value": True},
            }
        )
        workflow.add_node(
            {
                "node_id": "check",
                "type": "IfNode",
                "config": {"expression": "check_flag"},
            }
        )
        workflow.add_node(
            {
                "node_id": "true_path",
                "type": "SetVariableNode",
                "config": {"variable_name": "path_taken", "default_value": "true"},
            }
        )
        workflow.add_node(
            {
                "node_id": "false_path",
                "type": "SetVariableNode",
                "config": {"variable_name": "path_taken", "default_value": "false"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_flag", "exec_in"),
                NodeConnection("set_flag", "exec_out", "check", "exec_in"),
                NodeConnection("check", "true", "true_path", "exec_in"),
                NodeConnection("check", "false", "false_path", "exec_in"),
                NodeConnection("true_path", "exec_out", "end", "exec_in"),
                NodeConnection("false_path", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("path_taken") == "true"


# =============================================================================
# TEST: EXECUTION FLOW CONTROL
# =============================================================================


@pytest.mark.integration
class TestExecutionFlowControl:
    """Tests for execution flow control patterns."""

    @pytest.mark.asyncio
    async def test_if_true_branch_execution(self, event_bus: EventBus) -> None:
        """Test IfNode correctly executes true branch."""
        workflow = WorkflowSchema(WorkflowMetadata(name="If-True-Branch"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "if_check",
                "type": "IfNode",
                "config": {"expression": "1 == 1"},
            }
        )
        workflow.add_node(
            {
                "node_id": "true_result",
                "type": "SetVariableNode",
                "config": {"variable_name": "branch", "default_value": "true_executed"},
            }
        )
        workflow.add_node(
            {
                "node_id": "false_result",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "branch",
                    "default_value": "false_executed",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "if_check", "exec_in"),
                NodeConnection("if_check", "true", "true_result", "exec_in"),
                NodeConnection("if_check", "false", "false_result", "exec_in"),
                NodeConnection("true_result", "exec_out", "end", "exec_in"),
                NodeConnection("false_result", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("branch") == "true_executed"

    @pytest.mark.asyncio
    async def test_if_false_branch_execution(self, event_bus: EventBus) -> None:
        """Test IfNode correctly executes false branch."""
        workflow = WorkflowSchema(WorkflowMetadata(name="If-False-Branch"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "if_check",
                "type": "IfNode",
                "config": {"expression": "1 == 2"},
            }
        )
        workflow.add_node(
            {
                "node_id": "true_result",
                "type": "SetVariableNode",
                "config": {"variable_name": "branch", "default_value": "true_executed"},
            }
        )
        workflow.add_node(
            {
                "node_id": "false_result",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "branch",
                    "default_value": "false_executed",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "if_check", "exec_in"),
                NodeConnection("if_check", "true", "true_result", "exec_in"),
                NodeConnection("if_check", "false", "false_result", "exec_in"),
                NodeConnection("true_result", "exec_out", "end", "exec_in"),
                NodeConnection("false_result", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("branch") == "false_executed"

    @pytest.mark.asyncio
    async def test_nested_if_conditions(self, event_bus: EventBus) -> None:
        """Test nested if conditions execute correctly."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Nested-If"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "outer_if",
                "type": "IfNode",
                "config": {"expression": "True"},
            }
        )
        workflow.add_node(
            {
                "node_id": "inner_if",
                "type": "IfNode",
                "config": {"expression": "True"},
            }
        )
        workflow.add_node(
            {
                "node_id": "nested_result",
                "type": "SetVariableNode",
                "config": {"variable_name": "nested", "default_value": "both_true"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "outer_if", "exec_in"),
                NodeConnection("outer_if", "true", "inner_if", "exec_in"),
                NodeConnection("inner_if", "true", "nested_result", "exec_in"),
                NodeConnection("nested_result", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("nested") == "both_true"

    @pytest.mark.asyncio
    async def test_conditional_based_on_variable(self, event_bus: EventBus) -> None:
        """Test conditional branching based on runtime variable."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Variable-Conditional"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_value",
                "type": "SetVariableNode",
                "config": {"variable_name": "threshold", "default_value": 100},
            }
        )
        workflow.add_node(
            {
                "node_id": "check_threshold",
                "type": "IfNode",
                "config": {"expression": "threshold > 50"},
            }
        )
        workflow.add_node(
            {
                "node_id": "high_action",
                "type": "SetVariableNode",
                "config": {"variable_name": "result", "default_value": "high"},
            }
        )
        workflow.add_node(
            {
                "node_id": "low_action",
                "type": "SetVariableNode",
                "config": {"variable_name": "result", "default_value": "low"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_value", "exec_in"),
                NodeConnection("set_value", "exec_out", "check_threshold", "exec_in"),
                NodeConnection("check_threshold", "true", "high_action", "exec_in"),
                NodeConnection("check_threshold", "false", "low_action", "exec_in"),
                NodeConnection("high_action", "exec_out", "end", "exec_in"),
                NodeConnection("low_action", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("result") == "high"


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


@pytest.mark.integration
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_workflow_metadata(self, event_bus: EventBus) -> None:
        """Test workflow with minimal metadata executes correctly."""
        workflow = WorkflowSchema(WorkflowMetadata(name=""))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node({"node_id": "end", "type": "EndNode"})
        workflow.connections.append(
            NodeConnection("start", "exec_out", "end", "exec_in")
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True

    @pytest.mark.asyncio
    async def test_variable_with_empty_string_value(self, event_bus: EventBus) -> None:
        """Test variable with empty string value is handled correctly."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Empty-String-Var"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_empty",
                "type": "SetVariableNode",
                "config": {"variable_name": "empty_var", "default_value": ""},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_empty", "exec_in"),
                NodeConnection("set_empty", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("empty_var") == ""

    @pytest.mark.asyncio
    async def test_variable_with_special_characters(self, event_bus: EventBus) -> None:
        """Test variable with special characters in value."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Special-Chars-Var"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_special",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "special_var",
                    "default_value": "Hello\nWorld\t!@#$%^&*()",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_special", "exec_in"),
                NodeConnection("set_special", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert (
            use_case.context.get_variable("special_var") == "Hello\nWorld\t!@#$%^&*()"
        )

    @pytest.mark.asyncio
    async def test_variable_with_none_value(self, event_bus: EventBus) -> None:
        """Test variable with None value."""
        workflow = WorkflowSchema(WorkflowMetadata(name="None-Value-Var"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_none",
                "type": "SetVariableNode",
                "config": {"variable_name": "none_var", "default_value": None},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_none", "exec_in"),
                NodeConnection("set_none", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("none_var") is None

    @pytest.mark.asyncio
    async def test_multiple_end_nodes_reachable_from_branches(
        self, event_bus: EventBus
    ) -> None:
        """Test workflow correctly terminates with multiple branch endpoints."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Multi-End-Branches"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "branch",
                "type": "IfNode",
                "config": {"expression": "True"},
            }
        )
        workflow.add_node(
            {
                "node_id": "true_set",
                "type": "SetVariableNode",
                "config": {"variable_name": "path", "default_value": "A"},
            }
        )
        workflow.add_node(
            {
                "node_id": "false_set",
                "type": "SetVariableNode",
                "config": {"variable_name": "path", "default_value": "B"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "branch", "exec_in"),
                NodeConnection("branch", "true", "true_set", "exec_in"),
                NodeConnection("branch", "false", "false_set", "exec_in"),
                NodeConnection("true_set", "exec_out", "end", "exec_in"),
                NodeConnection("false_set", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("path") == "A"
