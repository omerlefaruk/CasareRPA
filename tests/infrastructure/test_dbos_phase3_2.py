"""
Tests for Phase 3.2: DBOS Workflow Decoration.

Verifies:
- Decorated functions can be imported
- Fallback mode works when DBOS unavailable
- workflow_id parameter is properly handled
- Step functions maintain structure
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestDecoratedWorkflowRunner:
    """Test decorated workflow runner."""

    @pytest.mark.asyncio
    async def test_import_decorated_workflow(self):
        """Test that decorated workflow can be imported."""
        from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
            execute_workflow_durable,
            start_durable_workflow,
            get_workflow_status,
            DBOS_AVAILABLE,
        )

        assert callable(execute_workflow_durable)
        assert callable(start_durable_workflow)
        assert callable(get_workflow_status)
        assert isinstance(DBOS_AVAILABLE, bool)

    @pytest.mark.asyncio
    async def test_fallback_mode_without_dbos(self):
        """Test workflow execution in fallback mode (no DBOS)."""
        # Force fallback mode
        with patch(
            "casare_rpa.infrastructure.dbos.workflow_runner_decorated.DBOS_AVAILABLE",
            False,
        ):
            from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
                execute_workflow_durable,
            )

            # Create minimal workflow data
            workflow_data = {
                "metadata": {
                    "name": "Test Workflow",
                    "description": "Test",
                    "workflow_id": "test-001",
                },
                "nodes": [],
                "connections": [],
            }

            # Execute should work in fallback mode
            result = await execute_workflow_durable(
                workflow_id="test-001",
                workflow_data=workflow_data,
                initial_variables={},
            )

            assert isinstance(result, dict)
            assert "workflow_id" in result
            assert result["workflow_id"] == "test-001"

    @pytest.mark.asyncio
    async def test_start_durable_workflow_fire_and_forget(self):
        """Test starting workflow without waiting."""
        with patch(
            "casare_rpa.infrastructure.dbos.workflow_runner_decorated.DBOS_AVAILABLE",
            False,
        ):
            from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
                start_durable_workflow,
            )
            from casare_rpa.domain.entities.workflow import (
                WorkflowSchema,
                WorkflowMetadata,
            )

            workflow = WorkflowSchema(
                metadata=WorkflowMetadata(name="Test", description="Test workflow")
            )

            # Start without waiting
            info = await start_durable_workflow(
                workflow=workflow, wait_for_result=False
            )

            assert "workflow_id" in info
            assert "status" in info
            assert info["status"] == "started"

    @pytest.mark.asyncio
    async def test_workflow_id_parameter(self):
        """Test that workflow_id is properly passed through."""
        with patch(
            "casare_rpa.infrastructure.dbos.workflow_runner_decorated.DBOS_AVAILABLE",
            False,
        ):
            from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
                start_durable_workflow,
            )
            from casare_rpa.domain.entities.workflow import (
                WorkflowSchema,
                WorkflowMetadata,
            )

            workflow = WorkflowSchema(
                metadata=WorkflowMetadata(name="Test", description="Test")
            )

            # Provide explicit workflow_id
            info = await start_durable_workflow(
                workflow=workflow, workflow_id="custom-id-123", wait_for_result=False
            )

            assert info["workflow_id"] == "custom-id-123"


class TestDecoratedStepFunctions:
    """Test decorated step functions."""

    @pytest.mark.asyncio
    async def test_import_decorated_steps(self):
        """Test that decorated step functions can be imported."""
        from casare_rpa.infrastructure.dbos.step_functions_decorated import (
            initialize_context_step,
            execute_node_step,
            cleanup_context_step,
            transfer_data_step,
            DBOS_AVAILABLE,
        )

        assert callable(initialize_context_step)
        assert callable(execute_node_step)
        assert callable(cleanup_context_step)
        assert callable(transfer_data_step)
        assert isinstance(DBOS_AVAILABLE, bool)

    @pytest.mark.asyncio
    async def test_initialize_context_step_fallback(self):
        """Test initialize_context_step in fallback mode."""
        with patch(
            "casare_rpa.infrastructure.dbos.step_functions_decorated.DBOS_AVAILABLE",
            False,
        ):
            from casare_rpa.infrastructure.dbos.step_functions_decorated import (
                initialize_context_step,
            )

            context_state = await initialize_context_step(
                workflow_name="Test Workflow", initial_variables={"count": 5}
            )

            assert isinstance(context_state, dict)
            assert context_state["workflow_name"] == "Test Workflow"
            assert context_state["variables"]["count"] == 5

    @pytest.mark.asyncio
    async def test_cleanup_context_step_fallback(self):
        """Test cleanup_context_step in fallback mode."""
        with patch(
            "casare_rpa.infrastructure.dbos.step_functions_decorated.DBOS_AVAILABLE",
            False,
        ):
            from casare_rpa.infrastructure.dbos.step_functions_decorated import (
                cleanup_context_step,
            )
            from casare_rpa.infrastructure.execution.execution_context import (
                ExecutionContext,
            )

            context = ExecutionContext(workflow_name="Test")

            result = await cleanup_context_step(context, timeout=5.0)

            assert result is True

    @pytest.mark.asyncio
    async def test_execute_node_step_structure(self):
        """Test that execute_node_step maintains expected structure."""
        with patch(
            "casare_rpa.infrastructure.dbos.step_functions_decorated.DBOS_AVAILABLE",
            False,
        ):
            from casare_rpa.infrastructure.dbos.step_functions_decorated import (
                execute_node_step,
                ExecutionStepResult,
            )
            from casare_rpa.infrastructure.execution.execution_context import (
                ExecutionContext,
            )

            # Create mock node
            mock_node = MagicMock()
            mock_node.id = "node-1"
            mock_node.__class__.__name__ = "MockNode"
            mock_node.config = {}
            mock_node.status = None
            mock_node.execution_count = 0
            mock_node.execute = AsyncMock(
                return_value={"success": True, "data": "test"}
            )

            context = ExecutionContext(workflow_name="Test")

            result = await execute_node_step(
                node=mock_node, context=context, node_id="node-1", node_timeout=10.0
            )

            # Verify result structure
            assert isinstance(result, ExecutionStepResult)
            assert result.success is True
            assert result.node_id == "node-1"
            assert result.execution_time > 0
            assert result.result["success"] is True


class TestDecoratorCompatibility:
    """Test decorator compatibility and fallback behavior."""

    def test_dbos_available_flag(self):
        """Test that DBOS_AVAILABLE flag is consistent."""
        from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
            DBOS_AVAILABLE as wf_available,
        )
        from casare_rpa.infrastructure.dbos.step_functions_decorated import (
            DBOS_AVAILABLE as sf_available,
        )

        # Both should have same availability
        assert wf_available == sf_available

    @pytest.mark.asyncio
    async def test_decorated_functions_are_async(self):
        """Test that all decorated functions are async."""
        import inspect
        from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
            execute_workflow_durable,
        )
        from casare_rpa.infrastructure.dbos.step_functions_decorated import (
            initialize_context_step,
            execute_node_step,
            cleanup_context_step,
        )

        assert inspect.iscoroutinefunction(execute_workflow_durable)
        assert inspect.iscoroutinefunction(initialize_context_step)
        assert inspect.iscoroutinefunction(execute_node_step)
        assert inspect.iscoroutinefunction(cleanup_context_step)


# ============================================================================
# Integration Test Placeholders
# ============================================================================


@pytest.mark.skip(reason="Requires running DBOS instance")
@pytest.mark.asyncio
async def test_actual_dbos_workflow_execution():
    """
    Integration test with real DBOS runtime.

    This test requires:
    - DBOS installed (pip install dbos)
    - PostgreSQL running
    - DB_PASSWORD environment variable set
    - DBOS initialized (dbos migrate)

    Run with:
        export DB_PASSWORD=postgres
        dbos start  # In separate terminal
        pytest tests/infrastructure/test_dbos_phase3_2.py::test_actual_dbos_workflow_execution -v
    """
    from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
        start_durable_workflow,
    )
    from casare_rpa.domain.entities.workflow import WorkflowSchema, WorkflowMetadata

    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(
            name="DBOS Integration Test", description="Test real DBOS execution"
        )
    )

    result = await start_durable_workflow(
        workflow=workflow, workflow_id="dbos-int-test-001", wait_for_result=True
    )

    assert result["success"] in [True, False]  # Should complete either way
    assert result["workflow_id"] == "dbos-int-test-001"


@pytest.mark.skip(reason="Requires running DBOS instance")
@pytest.mark.asyncio
async def test_dbos_crash_recovery():
    """
    Test DBOS crash recovery mechanism.

    This test simulates a crash and verifies workflow resumes from checkpoint.

    Requires:
    - DBOS running
    - Long-running workflow (>10s)
    - Manual process restart
    """
    pass  # To be implemented in Phase 3.4
