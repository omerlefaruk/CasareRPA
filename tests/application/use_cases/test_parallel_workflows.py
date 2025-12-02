"""
Unit tests for multi-workflow parallel execution.

Tests the "Run All Workflows" feature (Shift+F5) that executes
multiple independent workflows concurrently with SHARED variables
but SEPARATE browser instances.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from casare_rpa.infrastructure.execution import ExecutionContext


class TestExecutionContextCreateWorkflowContext:
    """Tests for ExecutionContext.create_workflow_context()."""

    def test_create_workflow_context_shares_variables(self):
        """Test that workflow context shares the same variables dict."""
        context = ExecutionContext(workflow_name="main")
        context.set_variable("shared_var", "original")

        # Create workflow context
        workflow_ctx = context.create_workflow_context("workflow_0")

        # Variables should be the SAME object (shared)
        assert workflow_ctx._state.variables is context._state.variables

        # Changes in one should reflect in the other
        workflow_ctx.set_variable("shared_var", "modified_by_workflow")
        assert context.get_variable("shared_var") == "modified_by_workflow"

        # New variables in workflow should appear in main
        workflow_ctx.set_variable("new_var", "from_workflow")
        assert context.has_variable("new_var")
        assert context.get_variable("new_var") == "from_workflow"

    def test_create_workflow_context_sets_workflow_name(self):
        """Test that workflow context has correct workflow name variable."""
        context = ExecutionContext(workflow_name="main")

        workflow_ctx = context.create_workflow_context("workflow_1")

        assert workflow_ctx.get_variable("_workflow_name") == "workflow_1"

    def test_create_workflow_context_separate_browser_manager(self):
        """Test that each workflow context has its own BrowserResourceManager."""
        context = ExecutionContext(workflow_name="main")

        workflow_ctx_1 = context.create_workflow_context("workflow_0")
        workflow_ctx_2 = context.create_workflow_context("workflow_1")

        # Each should have a different _resources manager
        assert workflow_ctx_1._resources is not context._resources
        assert workflow_ctx_2._resources is not context._resources
        assert workflow_ctx_1._resources is not workflow_ctx_2._resources

    def test_create_workflow_context_shares_pause_event(self):
        """Test that workflow context shares the same pause event."""
        pause_event = asyncio.Event()
        pause_event.set()
        context = ExecutionContext(workflow_name="main", pause_event=pause_event)

        workflow_ctx = context.create_workflow_context("workflow_0")

        assert workflow_ctx.pause_event is pause_event


class TestExecutionOrchestratorFindAllStartNodes:
    """Tests for ExecutionOrchestrator.find_all_start_nodes()."""

    def test_find_all_start_nodes_empty_workflow(self):
        """Test finding start nodes in empty workflow."""
        from casare_rpa.domain.services.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        # Create mock workflow with no nodes
        workflow = MagicMock()
        workflow.nodes = {}

        orchestrator = ExecutionOrchestrator(workflow)
        start_nodes = orchestrator.find_all_start_nodes()

        assert start_nodes == []

    def test_find_all_start_nodes_single_start(self):
        """Test finding single start node."""
        from casare_rpa.domain.services.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        workflow = MagicMock()
        workflow.nodes = {
            "node_1": {"node_type": "StartNode"},
            "node_2": {"node_type": "ClickNode"},
        }

        orchestrator = ExecutionOrchestrator(workflow)
        start_nodes = orchestrator.find_all_start_nodes()

        assert len(start_nodes) == 1
        assert "node_1" in start_nodes

    def test_find_all_start_nodes_multiple_starts(self):
        """Test finding multiple start nodes."""
        from casare_rpa.domain.services.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        workflow = MagicMock()
        workflow.nodes = {
            "start_1": {"node_type": "StartNode"},
            "click_1": {"node_type": "ClickNode"},
            "start_2": {"node_type": "StartNode"},
            "type_1": {"node_type": "TypeNode"},
            "start_3": {"node_type": "StartNode"},
        }

        orchestrator = ExecutionOrchestrator(workflow)
        start_nodes = orchestrator.find_all_start_nodes()

        assert len(start_nodes) == 3
        assert "start_1" in start_nodes
        assert "start_2" in start_nodes
        assert "start_3" in start_nodes

    def test_find_all_start_nodes_handles_type_key(self):
        """Test finding start nodes with 'type' key instead of 'node_type'."""
        from casare_rpa.domain.services.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        workflow = MagicMock()
        workflow.nodes = {
            "node_1": {"type": "StartNode"},  # Uses 'type' key
            "node_2": {"node_type": "StartNode"},  # Uses 'node_type' key
        }

        orchestrator = ExecutionOrchestrator(workflow)
        start_nodes = orchestrator.find_all_start_nodes()

        assert len(start_nodes) == 2


class TestExecuteWorkflowRunAll:
    """Tests for ExecuteWorkflowUseCase.execute(run_all=True)."""

    @pytest.mark.asyncio
    async def test_execute_run_all_calls_parallel_workflows(self):
        """Test that run_all=True triggers parallel workflow execution."""
        from casare_rpa.application.use_cases.execute_workflow import (
            ExecuteWorkflowUseCase,
        )
        from casare_rpa.domain.events import get_event_bus

        # Create mock workflow with multiple start nodes
        workflow = MagicMock()
        workflow.metadata.name = "test_workflow"
        workflow.nodes = {
            "start_1": {"node_type": "StartNode"},
            "start_2": {"node_type": "StartNode"},
        }
        workflow.connections = []

        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=get_event_bus(),
        )

        # Mock the parallel execution method
        use_case._execute_parallel_workflows = AsyncMock()
        use_case.orchestrator.find_all_start_nodes = MagicMock(
            return_value=["start_1", "start_2"]
        )

        # Execute with run_all=True
        await use_case.execute(run_all=True)

        # Should have called parallel workflows
        use_case._execute_parallel_workflows.assert_awaited_once_with(
            ["start_1", "start_2"]
        )

    @pytest.mark.asyncio
    async def test_execute_run_all_single_start_runs_normally(self):
        """Test that run_all with single start node runs normally."""
        from casare_rpa.application.use_cases.execute_workflow import (
            ExecuteWorkflowUseCase,
        )
        from casare_rpa.domain.events import get_event_bus

        workflow = MagicMock()
        workflow.metadata.name = "test_workflow"
        workflow.nodes = {"start_1": {"node_type": "StartNode"}}
        workflow.connections = []

        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=get_event_bus(),
        )

        use_case._execute_from_node = AsyncMock()
        use_case.orchestrator.find_all_start_nodes = MagicMock(return_value=["start_1"])

        await use_case.execute(run_all=True)

        # With single start node, should use normal execution
        use_case._execute_from_node.assert_awaited_once_with("start_1")


class TestParallelWorkflowFailureIsolation:
    """Tests for failure isolation in parallel workflow execution."""

    @pytest.mark.asyncio
    async def test_parallel_workflows_continue_on_failure(self):
        """Test that other workflows continue when one fails."""
        from casare_rpa.application.use_cases.execute_workflow import (
            ExecuteWorkflowUseCase,
        )
        from casare_rpa.domain.events import get_event_bus

        workflow = MagicMock()
        workflow.metadata.name = "test_workflow"
        workflow.nodes = {
            "start_1": {"node_type": "StartNode"},
            "start_2": {"node_type": "StartNode"},
            "start_3": {"node_type": "StartNode"},
        }
        workflow.connections = []

        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=get_event_bus(),
        )

        # Initialize context before testing parallel workflows
        use_case.context = ExecutionContext(workflow_name="test_workflow")

        # Track which workflows were executed
        executed_workflows = []

        async def mock_execute_with_context(start_id, context):
            executed_workflows.append(start_id)
            if start_id == "start_2":
                raise Exception("Workflow 2 failed")

        use_case._execute_from_node_with_context = mock_execute_with_context

        # Execute parallel workflows
        await use_case._execute_parallel_workflows(["start_1", "start_2", "start_3"])

        # All workflows should have been attempted despite failure in one
        assert len(executed_workflows) == 3


class TestSharedVariablesBetweenWorkflows:
    """Tests for shared variables between parallel workflows."""

    @pytest.mark.asyncio
    async def test_workflows_can_share_variables(self):
        """Test that workflows share the same variable dictionary."""
        context = ExecutionContext(workflow_name="main")

        # Create two workflow contexts
        ctx_1 = context.create_workflow_context("workflow_0")
        ctx_2 = context.create_workflow_context("workflow_1")

        # Set variable in workflow 1
        ctx_1.set_variable("counter", 1)

        # Should be visible in workflow 2
        assert ctx_2.has_variable("counter")
        assert ctx_2.get_variable("counter") == 1

        # Modify in workflow 2
        ctx_2.set_variable("counter", 2)

        # Should be visible in workflow 1 and main
        assert ctx_1.get_variable("counter") == 2
        assert context.get_variable("counter") == 2
