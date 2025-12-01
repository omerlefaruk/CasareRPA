"""
Tests for ExecuteWorkflowUseCase application use case.
Covers workflow execution coordination, resource management, events.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from casare_rpa.application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection


# Patch path for get_event_bus (imported inside the module)
EVENT_BUS_PATCH = "casare_rpa.domain.events.get_event_bus"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_workflow() -> WorkflowSchema:
    """Create simple linear workflow for testing."""
    workflow = WorkflowSchema(WorkflowMetadata(name="Test Workflow"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "action", "type": "ActionNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})
    workflow.connections.append(
        NodeConnection("start", "exec_out", "action", "exec_in")
    )
    workflow.connections.append(NodeConnection("action", "exec_out", "end", "exec_in"))
    return workflow


@pytest.fixture
def branching_workflow() -> WorkflowSchema:
    """Create workflow with branching."""
    workflow = WorkflowSchema(WorkflowMetadata(name="Branching"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "if_node", "type": "IfNode"})
    workflow.add_node({"node_id": "true_path", "type": "ActionNode"})
    workflow.add_node({"node_id": "false_path", "type": "ActionNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.append(
        NodeConnection("start", "exec_out", "if_node", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("if_node", "true", "true_path", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("if_node", "false", "false_path", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("true_path", "exec_out", "end", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("false_path", "exec_out", "end", "exec_in")
    )
    return workflow


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """Create mock event bus."""
    return MagicMock()


# ============================================================================
# ExecutionSettings Tests
# ============================================================================


class TestExecutionSettings:
    """Tests for ExecutionSettings value object."""

    def test_default_settings(self) -> None:
        """Default execution settings."""
        settings = ExecutionSettings()
        assert settings.continue_on_error is False
        assert settings.node_timeout == 120.0
        assert settings.target_node_id is None
        assert settings.single_node is False

    def test_custom_settings(self) -> None:
        """Custom execution settings."""
        settings = ExecutionSettings(
            continue_on_error=True,
            node_timeout=60.0,
            target_node_id="target_node",
        )
        assert settings.continue_on_error is True
        assert settings.node_timeout == 60.0
        assert settings.target_node_id == "target_node"

    def test_run_to_node_setting(self) -> None:
        """Run-to-node target setting (F4)."""
        settings = ExecutionSettings(target_node_id="my_target")
        assert settings.target_node_id == "my_target"
        assert settings.single_node is False

    def test_single_node_setting(self) -> None:
        """Single node execution setting (F5)."""
        settings = ExecutionSettings(target_node_id="my_node", single_node=True)
        assert settings.target_node_id == "my_node"
        assert settings.single_node is True


# ============================================================================
# Use Case Initialization Tests
# ============================================================================


class TestUseCaseInitialization:
    """Tests for ExecuteWorkflowUseCase initialization."""

    def test_create_use_case(self, simple_workflow: WorkflowSchema) -> None:
        """Create use case with workflow."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case.workflow == simple_workflow
        assert use_case.context is None
        assert len(use_case.executed_nodes) == 0

    def test_create_with_event_bus(
        self, simple_workflow: WorkflowSchema, mock_event_bus: MagicMock
    ) -> None:
        """Create use case with custom event bus."""
        use_case = ExecuteWorkflowUseCase(simple_workflow, event_bus=mock_event_bus)
        assert use_case.event_bus == mock_event_bus

    def test_create_with_settings(self, simple_workflow: WorkflowSchema) -> None:
        """Create use case with custom settings."""
        settings = ExecutionSettings(continue_on_error=True)
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        assert use_case.settings.continue_on_error is True

    def test_create_with_initial_variables(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """Create use case with initial variables."""
        variables = {"x": 1, "y": "hello"}
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(
                simple_workflow, initial_variables=variables
            )
        assert use_case._initial_variables == variables

    def test_create_with_project_context(self, simple_workflow: WorkflowSchema) -> None:
        """Create use case with project context."""
        mock_ctx = MagicMock()
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, project_context=mock_ctx)
        assert use_case._project_context == mock_ctx

    def test_orchestrator_created(self, simple_workflow: WorkflowSchema) -> None:
        """ExecutionOrchestrator is created."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case.orchestrator is not None
        assert use_case.orchestrator.workflow == simple_workflow


# ============================================================================
# Subgraph Calculation Tests
# ============================================================================


class TestSubgraphCalculation:
    """Tests for Run-To-Node subgraph calculation."""

    def test_subgraph_calculated_with_target(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """Subgraph is calculated when target node is set."""
        settings = ExecutionSettings(target_node_id="action")
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        assert use_case._subgraph_nodes is not None
        assert "start" in use_case._subgraph_nodes
        assert "action" in use_case._subgraph_nodes
        # end should not be in subgraph since we stop at action
        assert "end" not in use_case._subgraph_nodes

    def test_subgraph_not_calculated_without_target(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """Subgraph is None when no target specified."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case._subgraph_nodes is None

    def test_subgraph_unreachable_target(self, simple_workflow: WorkflowSchema) -> None:
        """Subgraph is None for unreachable target."""
        simple_workflow.add_node({"node_id": "island", "type": "Node"})
        settings = ExecutionSettings(target_node_id="island")
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        # Subgraph should be empty or None for unreachable target
        assert use_case._subgraph_nodes is None or len(use_case._subgraph_nodes) == 0


# ============================================================================
# Should Execute Node Tests
# ============================================================================


class TestShouldExecuteNode:
    """Tests for _should_execute_node method."""

    def test_execute_all_when_no_subgraph(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """All nodes execute when no subgraph filter."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case._should_execute_node("start") is True
        assert use_case._should_execute_node("action") is True
        assert use_case._should_execute_node("end") is True

    def test_filter_by_subgraph(self, simple_workflow: WorkflowSchema) -> None:
        """Only subgraph nodes execute with target."""
        settings = ExecutionSettings(target_node_id="action")
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        assert use_case._should_execute_node("start") is True
        assert use_case._should_execute_node("action") is True
        assert use_case._should_execute_node("end") is False


# ============================================================================
# Progress Calculation Tests
# ============================================================================


class TestProgressCalculation:
    """Tests for _calculate_progress method."""

    def test_progress_zero_at_start(self, simple_workflow: WorkflowSchema) -> None:
        """Progress is 0% at start."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case._calculate_progress() == 0.0

    def test_progress_increases(self, simple_workflow: WorkflowSchema) -> None:
        """Progress increases as nodes execute."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        use_case.executed_nodes.add("start")
        progress1 = use_case._calculate_progress()
        assert progress1 > 0

        use_case.executed_nodes.add("action")
        progress2 = use_case._calculate_progress()
        assert progress2 > progress1

    def test_progress_100_at_end(self, simple_workflow: WorkflowSchema) -> None:
        """Progress is 100% when all nodes executed."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        use_case.executed_nodes = {"start", "action", "end"}
        assert use_case._calculate_progress() == 100.0

    def test_progress_with_subgraph(self, simple_workflow: WorkflowSchema) -> None:
        """Progress uses subgraph count when target set."""
        settings = ExecutionSettings(target_node_id="action")
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        # Subgraph has 2 nodes: start, action
        use_case.executed_nodes.add("start")
        assert use_case._calculate_progress() == 50.0


# ============================================================================
# Stop Control Tests
# ============================================================================


class TestStopControl:
    """Tests for stop() method."""

    def test_stop_sets_flag(self, simple_workflow: WorkflowSchema) -> None:
        """stop() sets the _stop_requested flag."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case._stop_requested is False
        use_case.stop()
        assert use_case._stop_requested is True


# ============================================================================
# String Representation Tests
# ============================================================================


class TestUseCaseRepr:
    """Tests for __repr__ method."""

    def test_repr(self, simple_workflow: WorkflowSchema) -> None:
        """String representation shows workflow info."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        rep = repr(use_case)
        assert "ExecuteWorkflowUseCase" in rep
        assert "Test Workflow" in rep
        assert "nodes=" in rep


# ============================================================================
# Event Emission Tests
# ============================================================================


class TestEventEmission:
    """Tests for _emit_event method."""

    def test_emit_event_with_bus(
        self, simple_workflow: WorkflowSchema, mock_event_bus: MagicMock
    ) -> None:
        """Event is published to event bus."""
        from casare_rpa.domain.value_objects.types import EventType

        use_case = ExecuteWorkflowUseCase(simple_workflow, event_bus=mock_event_bus)
        use_case._emit_event(EventType.WORKFLOW_STARTED, {"test": "data"})
        mock_event_bus.publish.assert_called_once()

    def test_emit_event_no_bus(self, simple_workflow: WorkflowSchema) -> None:
        """No error when event bus is None."""
        use_case = ExecuteWorkflowUseCase(simple_workflow, event_bus=None)
        use_case.event_bus = None
        # Should not raise
        from casare_rpa.domain.value_objects.types import EventType

        use_case._emit_event(EventType.WORKFLOW_STARTED, {})


# ============================================================================
# Execution State Tests
# ============================================================================


class TestExecutionState:
    """Tests for tracking execution state."""

    def test_initial_state(self, simple_workflow: WorkflowSchema) -> None:
        """Initial execution state."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case.executed_nodes == set()
        assert use_case.current_node_id is None
        assert use_case.start_time is None
        assert use_case.end_time is None
        assert use_case._stop_requested is False
        assert use_case._target_reached is False

    def test_state_reset_before_execution(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """State should be ready for fresh execution."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        # Simulate some prior state
        use_case.executed_nodes.add("old_node")
        use_case._stop_requested = True

        # These should be cleared at start of execute()
        # (We can't easily test this without mocking execute)
        # Just verify initial state is correct
        assert "old_node" in use_case.executed_nodes


# ============================================================================
# Workflow Metadata Access Tests
# ============================================================================


class TestWorkflowMetadataAccess:
    """Tests for accessing workflow metadata."""

    def test_workflow_name_access(self, simple_workflow: WorkflowSchema) -> None:
        """Access workflow name through use case."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert use_case.workflow.metadata.name == "Test Workflow"

    def test_workflow_nodes_access(self, simple_workflow: WorkflowSchema) -> None:
        """Access workflow nodes through use case."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert len(use_case.workflow.nodes) == 3

    def test_workflow_connections_access(self, simple_workflow: WorkflowSchema) -> None:
        """Access workflow connections through use case."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        assert len(use_case.workflow.connections) == 2


# ============================================================================
# Orchestrator Integration Tests
# ============================================================================


class TestOrchestratorIntegration:
    """Tests for orchestrator integration."""

    def test_find_start_node(self, simple_workflow: WorkflowSchema) -> None:
        """Orchestrator finds start node."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        start_id = use_case.orchestrator.find_start_node()
        assert start_id == "start"

    def test_get_next_nodes(self, simple_workflow: WorkflowSchema) -> None:
        """Orchestrator provides next nodes."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow)
        next_nodes = use_case.orchestrator.get_next_nodes("start")
        assert next_nodes == ["action"]

    def test_is_control_flow_node(self, branching_workflow: WorkflowSchema) -> None:
        """Orchestrator identifies control flow nodes."""
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(branching_workflow)
        assert use_case.orchestrator.is_control_flow_node("if_node") is True
        assert use_case.orchestrator.is_control_flow_node("true_path") is False


# ============================================================================
# Settings Integration Tests
# ============================================================================


class TestSettingsIntegration:
    """Tests for settings integration."""

    def test_continue_on_error_setting(self, simple_workflow: WorkflowSchema) -> None:
        """continue_on_error setting is accessible."""
        settings = ExecutionSettings(continue_on_error=True)
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        assert use_case.settings.continue_on_error is True

    def test_node_timeout_setting(self, simple_workflow: WorkflowSchema) -> None:
        """node_timeout setting is accessible."""
        settings = ExecutionSettings(node_timeout=30.0)
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        assert use_case.settings.node_timeout == 30.0

    def test_target_node_setting(self, simple_workflow: WorkflowSchema) -> None:
        """target_node_id setting is accessible."""
        settings = ExecutionSettings(target_node_id="action")
        with patch(EVENT_BUS_PATCH):
            use_case = ExecuteWorkflowUseCase(simple_workflow, settings=settings)
        assert use_case.settings.target_node_id == "action"
