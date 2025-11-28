"""
Tests for Phase 3: DBOS Durable Execution

Verifies:
- ExecutionState value object
- ExecutionContext serialization
- Step functions
- DBOSWorkflowRunner (fallback mode without DBOS)
"""

import pytest
import asyncio
from datetime import datetime
from typing import Any, Dict

from casare_rpa.domain.value_objects.execution_state import (
    ExecutionState,
    WorkflowStatus,
    create_execution_state,
)
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
from casare_rpa.infrastructure.dbos.step_functions import (
    ExecutionStepResult,
    execute_node_step,
    initialize_context_step,
    cleanup_context_step,
)


class TestExecutionState:
    """Test ExecutionState value object."""

    def test_create_execution_state(self):
        """Test creating execution state."""
        state = create_execution_state(
            workflow_id="wf-001",
            workflow_name="Test Workflow",
            initial_variables={"count": 0},
        )

        assert state.workflow_id == "wf-001"
        assert state.workflow_name == "Test Workflow"
        assert state.variables == {"count": 0}
        assert state.status == WorkflowStatus.PENDING
        assert len(state.executed_nodes) == 0

    def test_mark_node_executed(self):
        """Test marking node as executed."""
        state = create_execution_state(
            workflow_id="wf-002",
            workflow_name="Test",
        )

        # Mark node as executed
        new_state = state.mark_node_executed("node-1")

        assert "node-1" in new_state.executed_nodes
        assert "node-1" not in state.executed_nodes  # Original unchanged
        assert new_state.last_update_time > state.last_update_time

    def test_update_variables(self):
        """Test updating variables."""
        state = create_execution_state(
            workflow_id="wf-003",
            workflow_name="Test",
            initial_variables={"x": 1},
        )

        new_state = state.update_variables({"y": 2, "x": 10})

        assert new_state.variables == {"x": 10, "y": 2}
        assert state.variables == {"x": 1}  # Original unchanged

    def test_mark_completed(self):
        """Test marking workflow as completed."""
        state = create_execution_state(
            workflow_id="wf-004",
            workflow_name="Test",
        )

        completed_state = state.mark_completed()

        assert completed_state.status == WorkflowStatus.COMPLETED
        assert completed_state.end_time is not None
        assert state.status == WorkflowStatus.PENDING  # Original unchanged

    def test_mark_failed(self):
        """Test marking workflow as failed."""
        state = create_execution_state(
            workflow_id="wf-005",
            workflow_name="Test",
        )

        failed_state = state.mark_failed(
            error_message="Node execution failed", failed_node_id="node-5"
        )

        assert failed_state.status == WorkflowStatus.FAILED
        assert failed_state.error_message == "Node execution failed"
        assert failed_state.failed_node_id == "node-5"
        assert failed_state.end_time is not None

    def test_serialization(self):
        """Test state serialization and deserialization."""
        state = create_execution_state(
            workflow_id="wf-006",
            workflow_name="Test",
            initial_variables={"count": 5},
        )

        state = state.mark_node_executed("node-1")
        state = state.mark_node_executed("node-2")
        state = state.set_variable("count", 10)

        # Serialize
        state_dict = state.to_dict()

        assert state_dict["workflow_id"] == "wf-006"
        assert state_dict["workflow_name"] == "Test"
        assert "node-1" in state_dict["executed_nodes"]
        assert "node-2" in state_dict["executed_nodes"]
        assert state_dict["variables"]["count"] == 10

        # Deserialize
        restored = ExecutionState.from_dict(state_dict)

        assert restored.workflow_id == state.workflow_id
        assert restored.workflow_name == state.workflow_name
        assert restored.executed_nodes == state.executed_nodes
        assert restored.variables == state.variables

    def test_calculate_progress(self):
        """Test progress calculation."""
        state = create_execution_state(
            workflow_id="wf-007",
            workflow_name="Test",
        )

        assert state.calculate_progress(total_nodes=10) == 0.0

        state = state.mark_node_executed("node-1")
        assert state.calculate_progress(total_nodes=10) == 10.0

        state = state.mark_node_executed("node-2")
        state = state.mark_node_executed("node-3")
        assert state.calculate_progress(total_nodes=10) == 30.0


class TestExecutionContextSerialization:
    """Test ExecutionContext serialization for DBOS."""

    @pytest.mark.asyncio
    async def test_context_serialization(self):
        """Test serializing and deserializing ExecutionContext."""
        # Create context
        context = ExecutionContext(
            workflow_name="Test Workflow",
            initial_variables={"x": 10, "y": 20},
        )

        # Set some state
        context.set_variable("z", 30)
        context.set_current_node("node-1")

        # Serialize
        context_dict = context.to_dict()

        assert context_dict["workflow_name"] == "Test Workflow"
        assert context_dict["variables"]["x"] == 10
        assert context_dict["variables"]["y"] == 20
        assert context_dict["variables"]["z"] == 30
        assert context_dict["current_node_id"] == "node-1"

        # Deserialize
        restored = ExecutionContext.from_dict(context_dict)

        assert restored.workflow_name == "Test Workflow"
        assert restored.get_variable("x") == 10
        assert restored.get_variable("y") == 20
        assert restored.get_variable("z") == 30
        assert restored.current_node_id == "node-1"

        # Cleanup
        await restored.cleanup()

    @pytest.mark.asyncio
    async def test_context_does_not_serialize_resources(self):
        """Test that Playwright resources are NOT serialized."""
        context = ExecutionContext(
            workflow_name="Test",
            initial_variables={"count": 1},
        )

        # Simulate setting browser (won't actually create one)
        # In real usage, browser would be created by nodes

        context_dict = context.to_dict()

        # Verify browser/pages are NOT in serialized state
        assert "browser" not in context_dict
        assert "pages" not in context_dict
        assert "browser_contexts" not in context_dict

        # Variables and other state should be serialized
        assert context_dict["variables"]["count"] == 1

        await context.cleanup()


class TestStepFunctions:
    """Test DBOS step functions."""

    @pytest.mark.asyncio
    async def test_initialize_context_step(self):
        """Test context initialization step."""
        context_state = await initialize_context_step(
            workflow_name="Test Workflow",
            initial_variables={"x": 5},
        )

        assert context_state["workflow_name"] == "Test Workflow"
        assert context_state["variables"]["x"] == 5

    @pytest.mark.asyncio
    async def test_cleanup_context_step(self):
        """Test context cleanup step."""
        context = ExecutionContext(workflow_name="Test")

        result = await cleanup_context_step(context, timeout=5.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_execution_step_result(self):
        """Test ExecutionStepResult."""
        result = ExecutionStepResult(
            success=True,
            node_id="node-1",
            execution_time=1.5,
            result={"data": "test"},
        )

        assert result.success is True
        assert result.node_id == "node-1"
        assert result.execution_time == 1.5
        assert result.result["data"] == "test"

        # Serialize
        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["node_id"] == "node-1"
        assert result_dict["execution_time"] == 1.5

        # Deserialize
        restored = ExecutionStepResult.from_dict(result_dict)

        assert restored.success == result.success
        assert restored.node_id == result.node_id
        assert restored.execution_time == result.execution_time


class TestDBOSWorkflowRunnerFallback:
    """Test DBOSWorkflowRunner in fallback mode (without DBOS)."""

    @pytest.mark.asyncio
    async def test_fallback_mode_warning(self, caplog):
        """Test that fallback mode logs warning when DBOS unavailable."""
        from casare_rpa.infrastructure.dbos.workflow_runner import (
            DBOSWorkflowRunner,
            DBOS_AVAILABLE,
        )
        from casare_rpa.domain.entities.workflow import WorkflowSchema, WorkflowMetadata

        # Create minimal workflow
        metadata = WorkflowMetadata(
            name="Test Workflow",
            description="Test",
        )
        workflow = WorkflowSchema(metadata=metadata)

        runner = DBOSWorkflowRunner(workflow=workflow)

        # If DBOS not available, should log warning
        if not DBOS_AVAILABLE:
            # execute() will fallback to standard mode
            # This will fail due to no StartNode, but that's expected
            try:
                await runner.execute()
            except Exception:
                pass  # Expected to fail - no StartNode

            # Check for fallback warning or durable mode indicator
            messages = [rec.message.lower() for rec in caplog.records]
            assert any(
                "fallback" in msg or "no (fallback mode)" in msg for msg in messages
            )


# ============================================================================
# Integration Test (requires actual workflow)
# ============================================================================


@pytest.mark.skip(reason="Requires full workflow setup")
@pytest.mark.asyncio
async def test_end_to_end_durable_execution():
    """
    End-to-end test of durable execution.

    This test will be implemented in Phase 3.4 when crash recovery
    tests are added.

    Should verify:
    - Workflow starts
    - Nodes execute as @steps
    - State checkpointed after each step
    - Workflow completes
    """
    pass


@pytest.mark.skip(reason="Requires DBOS runtime and crash simulation")
@pytest.mark.asyncio
async def test_crash_recovery():
    """
    Test crash recovery.

    Should verify:
    - Workflow starts
    - Process killed mid-execution
    - Workflow resumes from checkpoint
    - No duplicate execution
    - Exactly-once guarantees
    """
    pass
