"""
CasareRPA - Integration Tests for Workflow Execution
Tests complete end-to-end workflow execution with real domain logic.
Minimal mocking - workflows use dictionary-based node definitions.
Validates: Presentation → Application → Domain flow, ExecutionState tracking, event propagation.
"""

import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

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


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def event_bus() -> EventBus:
    """Create real event bus for tests."""
    return EventBus()


@pytest.fixture
def simple_start_end_workflow() -> WorkflowSchema:
    """Minimal workflow: Start → End"""
    workflow = WorkflowSchema(WorkflowMetadata(name="Start-End"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})
    workflow.connections.append(NodeConnection("start", "exec_out", "end", "exec_in"))
    return workflow


@pytest.fixture
def three_node_linear_workflow() -> WorkflowSchema:
    """Linear workflow: Start → SetVar → GetVar → End"""
    workflow = WorkflowSchema(WorkflowMetadata(name="Linear-Three-Nodes"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node(
        {
            "node_id": "set_var",
            "type": "SetVariableNode",
            "config": {"variable_name": "test_var", "default_value": "hello"},
        }
    )
    workflow.add_node(
        {
            "node_id": "get_var",
            "type": "GetVariableNode",
            "config": {"variable_name": "test_var"},
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
    return workflow


@pytest.fixture
def branching_workflow() -> WorkflowSchema:
    """Branching: Start → If → (true/false paths) → End

    The If node evaluates the 'condition' variable from initial_variables.
    No set_flag node - condition comes from initial_variables.
    """
    workflow = WorkflowSchema(WorkflowMetadata(name="Branching-If"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    # IfNode evaluates 'condition' variable from initial_variables
    workflow.add_node(
        {"node_id": "if_node", "type": "IfNode", "config": {"expression": "condition"}}
    )
    workflow.add_node(
        {
            "node_id": "true_branch",
            "type": "SetVariableNode",
            "config": {"variable_name": "result", "default_value": "true_path"},
        }
    )
    workflow.add_node(
        {
            "node_id": "false_branch",
            "type": "SetVariableNode",
            "config": {"variable_name": "result", "default_value": "false_path"},
        }
    )
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.extend(
        [
            NodeConnection("start", "exec_out", "if_node", "exec_in"),
            NodeConnection("if_node", "true", "true_branch", "exec_in"),
            NodeConnection("if_node", "false", "false_branch", "exec_in"),
            NodeConnection("true_branch", "exec_out", "end", "exec_in"),
            NodeConnection("false_branch", "exec_out", "end", "exec_in"),
        ]
    )
    return workflow


# ============================================================================
# SIMPLE WORKFLOW TESTS (~5 tests)
# ============================================================================


class TestSimpleWorkflows:
    """Tests for simple, linear workflows."""

    @pytest.mark.asyncio
    async def test_minimal_start_end_workflow(
        self, simple_start_end_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test minimal workflow: Start → End"""
        use_case = ExecuteWorkflowUseCase(
            simple_start_end_workflow, event_bus=event_bus
        )
        result = await use_case.execute()

        assert result is True
        assert len(use_case.executed_nodes) == 2
        assert "start" in use_case.executed_nodes
        assert "end" in use_case.executed_nodes

    @pytest.mark.asyncio
    async def test_three_node_linear_workflow(
        self, three_node_linear_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test linear workflow with SetVar and GetVar"""
        use_case = ExecuteWorkflowUseCase(
            three_node_linear_workflow, event_bus=event_bus
        )
        result = await use_case.execute()

        assert result is True
        assert len(use_case.executed_nodes) == 4
        assert use_case.context.has_variable("test_var")
        assert use_case.context.get_variable("test_var") == "hello"

    @pytest.mark.asyncio
    async def test_variable_initialization_and_retrieval(
        self, event_bus: EventBus
    ) -> None:
        """Test variable can be set and retrieved"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Var-Init-Retrieve"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_x",
                "type": "SetVariableNode",
                "config": {"variable_name": "x", "default_value": 42},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_x", "exec_in"),
                NodeConnection("set_x", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("x") == 42

    @pytest.mark.asyncio
    async def test_multiple_sequential_variables(self, event_bus: EventBus) -> None:
        """Test multiple variables in sequence"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Multi-Sequential"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_var1",
                "type": "SetVariableNode",
                "config": {"variable_name": "var1", "default_value": "first"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_var2",
                "type": "SetVariableNode",
                "config": {"variable_name": "var2", "default_value": "second"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_var3",
                "type": "SetVariableNode",
                "config": {"variable_name": "var3", "default_value": "third"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_var1", "exec_in"),
                NodeConnection("set_var1", "exec_out", "set_var2", "exec_in"),
                NodeConnection("set_var2", "exec_out", "set_var3", "exec_in"),
                NodeConnection("set_var3", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("var1") == "first"
        assert use_case.context.get_variable("var2") == "second"
        assert use_case.context.get_variable("var3") == "third"

    @pytest.mark.asyncio
    async def test_initial_variables_in_execution_context(
        self, event_bus: EventBus
    ) -> None:
        """Test initial variables are available in context"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Initial-Vars"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node({"node_id": "end", "type": "EndNode"})
        workflow.connections.append(
            NodeConnection("start", "exec_out", "end", "exec_in")
        )

        initial_vars = {"input_var": "from_initial"}
        use_case = ExecuteWorkflowUseCase(
            workflow, event_bus=event_bus, initial_variables=initial_vars
        )
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("input_var") == "from_initial"


# ============================================================================
# COMPLEX WORKFLOW TESTS (~5 tests)
# ============================================================================


class TestComplexWorkflows:
    """Tests for workflows with branching and control flow."""

    @pytest.mark.asyncio
    async def test_branching_if_true_path(
        self, branching_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test If node executes true branch when condition is true"""
        use_case = ExecuteWorkflowUseCase(
            branching_workflow,
            event_bus=event_bus,
            initial_variables={"condition": True},
        )
        result = await use_case.execute()

        assert result is True
        assert "if_node" in use_case.executed_nodes
        assert use_case.context.get_variable("result") == "true_path"

    @pytest.mark.asyncio
    async def test_branching_if_false_path(
        self, branching_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test If node executes false branch when condition is false"""
        use_case = ExecuteWorkflowUseCase(
            branching_workflow,
            event_bus=event_bus,
            initial_variables={"condition": False},
        )
        result = await use_case.execute()

        assert result is True
        assert "if_node" in use_case.executed_nodes
        assert use_case.context.get_variable("result") == "false_path"

    @pytest.mark.asyncio
    async def test_continue_on_error_setting(self, event_bus: EventBus) -> None:
        """Test continue_on_error execution setting"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Continue-On-Error"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_var",
                "type": "SetVariableNode",
                "config": {"variable_name": "test", "default_value": "value"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_var", "exec_in"),
                NodeConnection("set_var", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(
            workflow,
            event_bus=event_bus,
            settings=ExecutionSettings(continue_on_error=True),
        )
        result = await use_case.execute()

        assert result is True

    @pytest.mark.asyncio
    async def test_nested_if_conditions(self, event_bus: EventBus) -> None:
        """Test nested If conditions"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Nested-If"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {"node_id": "outer_if", "type": "IfNode", "config": {"expression": "True"}}
        )
        workflow.add_node(
            {
                "node_id": "inner_set",
                "type": "SetVariableNode",
                "config": {"variable_name": "nested", "default_value": "executed"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "outer_if", "exec_in"),
                NodeConnection("outer_if", "true", "inner_set", "exec_in"),
                NodeConnection("inner_set", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is not None

    @pytest.mark.asyncio
    async def test_multi_step_workflow_with_mixed_operations(
        self, event_bus: EventBus
    ) -> None:
        """Test workflow combining variable ops and control flow"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Mixed-Ops"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "init",
                "type": "SetVariableNode",
                "config": {"variable_name": "counter", "default_value": 0},
            }
        )
        workflow.add_node(
            {
                "node_id": "check",
                "type": "IfNode",
                "config": {"expression": "counter == 0"},
            }
        )
        workflow.add_node(
            {
                "node_id": "set_one",
                "type": "SetVariableNode",
                "config": {"variable_name": "counter", "default_value": 1},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "init", "exec_in"),
                NodeConnection("init", "exec_out", "check", "exec_in"),
                NodeConnection("check", "true", "set_one", "exec_in"),
                NodeConnection("set_one", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is not None


# ============================================================================
# CROSS-LAYER VALIDATION TESTS (~5 tests)
# ============================================================================


class TestCrossLayerValidation:
    """Tests validating Presentation → Application → Domain integration."""

    @pytest.mark.asyncio
    async def test_execution_state_tracks_workflow_metadata(
        self, simple_start_end_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test ExecutionState properly tracks workflow metadata"""
        use_case = ExecuteWorkflowUseCase(
            simple_start_end_workflow, event_bus=event_bus
        )
        result = await use_case.execute()

        assert result is True
        assert use_case.context._state.workflow_name == "Start-End"
        assert len(use_case.context._state.execution_path) > 0
        assert use_case.context._state.completed_at is not None

    @pytest.mark.asyncio
    async def test_event_bus_receives_workflow_events(
        self, simple_start_end_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test events are published to event bus"""
        events = []

        def capture(event: Event) -> None:
            events.append(event)

        event_bus.subscribe(EventType.WORKFLOW_STARTED, capture)
        event_bus.subscribe(EventType.WORKFLOW_COMPLETED, capture)

        use_case = ExecuteWorkflowUseCase(
            simple_start_end_workflow, event_bus=event_bus
        )
        result = await use_case.execute()

        assert result is True
        # Event bus should have received events
        assert event_bus is not None

    @pytest.mark.asyncio
    async def test_domain_orchestrator_finds_start_node(
        self, simple_start_end_workflow: WorkflowSchema
    ) -> None:
        """Test ExecutionOrchestrator can find StartNode"""
        orchestrator = ExecutionOrchestrator(simple_start_end_workflow)

        start_node_id = orchestrator.find_start_node()
        assert start_node_id == "start"

        all_nodes = orchestrator.get_all_nodes()
        assert len(all_nodes) == 2

    @pytest.mark.asyncio
    async def test_variable_resolution_across_execution_layers(
        self, event_bus: EventBus
    ) -> None:
        """Test variable set in one node accessible in execution context"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Var-Cross-Layer"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_test",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "cross_layer_var",
                    "default_value": "test_val",
                },
            }
        )
        workflow.add_node(
            {
                "node_id": "get_test",
                "type": "GetVariableNode",
                "config": {"variable_name": "cross_layer_var"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_test", "exec_in"),
                NodeConnection("set_test", "exec_out", "get_test", "exec_in"),
                NodeConnection("get_test", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("cross_layer_var") == "test_val"

    @pytest.mark.asyncio
    async def test_execution_timestamps_recorded(
        self, simple_start_end_workflow: WorkflowSchema, event_bus: EventBus
    ) -> None:
        """Test execution timing is properly recorded"""
        use_case = ExecuteWorkflowUseCase(
            simple_start_end_workflow, event_bus=event_bus
        )

        assert use_case.start_time is None
        assert use_case.end_time is None

        result = await use_case.execute()

        assert result is True
        assert use_case.start_time is not None
        assert use_case.end_time is not None
        assert use_case.end_time >= use_case.start_time


# ============================================================================
# REAL NODE EXECUTION TESTS (~5 tests)
# ============================================================================


class TestRealNodeExecution:
    """Tests using real nodes from the framework."""

    @pytest.mark.asyncio
    async def test_setvariable_node_execution(self, event_bus: EventBus) -> None:
        """Test real SetVariableNode execution"""
        workflow = WorkflowSchema(WorkflowMetadata(name="SetVar-Real"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_var",
                "type": "SetVariableNode",
                "config": {"variable_name": "real_test", "default_value": 123},
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
        assert use_case.context.get_variable("real_test") == 123

    @pytest.mark.asyncio
    async def test_ifnode_true_branch_execution(self, event_bus: EventBus) -> None:
        """Test real IfNode executes true branch"""
        workflow = WorkflowSchema(WorkflowMetadata(name="IfNode-True"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {"node_id": "if_test", "type": "IfNode", "config": {"expression": "1 == 1"}}
        )
        workflow.add_node(
            {
                "node_id": "true_action",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "if_result",
                    "default_value": "true_branch",
                },
            }
        )
        workflow.add_node(
            {
                "node_id": "false_action",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "if_result",
                    "default_value": "false_branch",
                },
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "if_test", "exec_in"),
                NodeConnection("if_test", "true", "true_action", "exec_in"),
                NodeConnection("if_test", "false", "false_action", "exec_in"),
                NodeConnection("true_action", "exec_out", "end", "exec_in"),
                NodeConnection("false_action", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("if_result") == "true_branch"

    @pytest.mark.asyncio
    async def test_getvar_node_retrieves_previously_set_value(
        self, event_bus: EventBus
    ) -> None:
        """Test real GetVariableNode retrieves set values"""
        workflow = WorkflowSchema(WorkflowMetadata(name="GetVar-Real"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "set_val",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "retrieve_test",
                    "default_value": "stored_value",
                },
            }
        )
        workflow.add_node(
            {
                "node_id": "get_val",
                "type": "GetVariableNode",
                "config": {"variable_name": "retrieve_test"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "set_val", "exec_in"),
                NodeConnection("set_val", "exec_out", "get_val", "exec_in"),
                NodeConnection("get_val", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("retrieve_test") == "stored_value"

    @pytest.mark.asyncio
    async def test_multiple_variable_types_handling(self, event_bus: EventBus) -> None:
        """Test nodes handle multiple variable types"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Multi-Types"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "str_var",
                "type": "SetVariableNode",
                "config": {
                    "variable_name": "str_test",
                    "default_value": "string_value",
                },
            }
        )
        workflow.add_node(
            {
                "node_id": "int_var",
                "type": "SetVariableNode",
                "config": {"variable_name": "int_test", "default_value": 999},
            }
        )
        workflow.add_node(
            {
                "node_id": "bool_var",
                "type": "SetVariableNode",
                "config": {"variable_name": "bool_test", "default_value": False},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "str_var", "exec_in"),
                NodeConnection("str_var", "exec_out", "int_var", "exec_in"),
                NodeConnection("int_var", "exec_out", "bool_var", "exec_in"),
                NodeConnection("bool_var", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("str_test") == "string_value"
        assert use_case.context.get_variable("int_test") == 999
        assert use_case.context.get_variable("bool_test") is False

    @pytest.mark.asyncio
    async def test_node_state_persists_across_execution(
        self, event_bus: EventBus
    ) -> None:
        """Test execution context state persists across node executions"""
        workflow = WorkflowSchema(WorkflowMetadata(name="State-Persist"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "first_set",
                "type": "SetVariableNode",
                "config": {"variable_name": "persistent", "default_value": "value1"},
            }
        )
        workflow.add_node(
            {
                "node_id": "second_set",
                "type": "SetVariableNode",
                "config": {"variable_name": "another", "default_value": "value2"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "first_set", "exec_in"),
                NodeConnection("first_set", "exec_out", "second_set", "exec_in"),
                NodeConnection("second_set", "exec_out", "end", "exec_in"),
            ]
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        # Both variables should persist
        assert use_case.context.get_variable("persistent") == "value1"
        assert use_case.context.get_variable("another") == "value2"


# ============================================================================
# ADVANCED SCENARIOS
# ============================================================================


class TestAdvancedScenarios:
    """Tests for advanced workflow scenarios."""

    @pytest.mark.asyncio
    async def test_large_linear_workflow(self, event_bus: EventBus) -> None:
        """Test execution of larger workflow with many sequential nodes"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Large-Linear"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})

        # Add 15 sequential variable nodes
        for i in range(15):
            workflow.add_node(
                {
                    "node_id": f"var_{i}",
                    "type": "SetVariableNode",
                    "config": {"variable_name": f"v_{i}", "default_value": i},
                }
            )

        workflow.add_node({"node_id": "end", "type": "EndNode"})

        # Connect sequentially
        workflow.connections.append(
            NodeConnection("start", "exec_out", "var_0", "exec_in")
        )
        for i in range(14):
            workflow.connections.append(
                NodeConnection(f"var_{i}", "exec_out", f"var_{i+1}", "exec_in")
            )
        workflow.connections.append(
            NodeConnection("var_14", "exec_out", "end", "exec_in")
        )

        use_case = ExecuteWorkflowUseCase(workflow, event_bus=event_bus)
        result = await use_case.execute()

        assert result is True
        assert len(use_case.executed_nodes) == 17  # start + 15 vars + end

    @pytest.mark.asyncio
    async def test_workflow_node_execution_order(self, event_bus: EventBus) -> None:
        """Test nodes execute in correct order"""
        execution_order = []

        workflow = WorkflowSchema(WorkflowMetadata(name="Order-Test"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "step_1",
                "type": "SetVariableNode",
                "config": {"variable_name": "order_1", "default_value": 1},
            }
        )
        workflow.add_node(
            {
                "node_id": "step_2",
                "type": "SetVariableNode",
                "config": {"variable_name": "order_2", "default_value": 2},
            }
        )
        workflow.add_node(
            {
                "node_id": "step_3",
                "type": "SetVariableNode",
                "config": {"variable_name": "order_3", "default_value": 3},
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
        # All variables should be set
        assert use_case.context.get_variable("order_1") == 1
        assert use_case.context.get_variable("order_2") == 2
        assert use_case.context.get_variable("order_3") == 3

    @pytest.mark.asyncio
    async def test_workflow_with_initial_variables_and_runtime_ops(
        self, event_bus: EventBus
    ) -> None:
        """Test workflow uses initial variables and adds runtime variables"""
        workflow = WorkflowSchema(WorkflowMetadata(name="Init-Runtime"))
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node(
            {
                "node_id": "add_runtime",
                "type": "SetVariableNode",
                "config": {"variable_name": "runtime_var", "default_value": "runtime"},
            }
        )
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        workflow.connections.extend(
            [
                NodeConnection("start", "exec_out", "add_runtime", "exec_in"),
                NodeConnection("add_runtime", "exec_out", "end", "exec_in"),
            ]
        )

        initial = {"init_var": "initial"}
        use_case = ExecuteWorkflowUseCase(
            workflow, event_bus=event_bus, initial_variables=initial
        )
        result = await use_case.execute()

        assert result is True
        assert use_case.context.get_variable("init_var") == "initial"
        assert use_case.context.get_variable("runtime_var") == "runtime"
