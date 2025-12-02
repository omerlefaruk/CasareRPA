"""Tests for ExecuteLocalUseCase.

Tests the local workflow execution orchestration with:
- Mock event bus
- Three-scenario pattern: SUCCESS, ERROR, EDGE_CASES
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from casare_rpa.application.orchestrator.use_cases.execute_local import (
    ExecuteLocalUseCase,
    ExecutionResult,
)


class TestExecutionResult:
    """Tests for ExecutionResult value class."""

    def test_execution_result_success(self) -> None:
        """ExecutionResult with success=True - all properties correct."""
        result = ExecutionResult(
            success=True,
            workflow_name="Test Workflow",
            variables={"output": "value"},
            error=None,
            executed_nodes=5,
            total_nodes=5,
            duration_ms=1234,
        )

        assert result.success is True
        assert result.workflow_name == "Test Workflow"
        assert result.variables == {"output": "value"}
        assert result.error is None
        assert result.executed_nodes == 5
        assert result.total_nodes == 5
        assert result.duration_ms == 1234

    def test_execution_result_failure(self) -> None:
        """ExecutionResult with success=False - error captured."""
        result = ExecutionResult(
            success=False,
            workflow_name="Failed Workflow",
            variables={},
            error="Node timeout exceeded",
            executed_nodes=3,
            total_nodes=5,
        )

        assert result.success is False
        assert result.error == "Node timeout exceeded"
        assert result.executed_nodes == 3

    def test_execution_result_progress_calculation(self) -> None:
        """ExecutionResult.progress - calculates percentage correctly."""
        result = ExecutionResult(
            success=True,
            workflow_name="Test",
            variables={},
            executed_nodes=3,
            total_nodes=6,
        )

        assert result.progress == 50.0

    def test_execution_result_progress_zero_nodes(self) -> None:
        """ExecutionResult.progress with 0 total nodes - handles edge case."""
        result = ExecutionResult(
            success=True,
            workflow_name="Empty",
            variables={},
            executed_nodes=0,
            total_nodes=0,
        )

        assert result.progress == 100.0  # Success with 0 nodes = 100%

    def test_execution_result_progress_zero_nodes_failure(self) -> None:
        """ExecutionResult.progress with 0 total nodes and failure."""
        result = ExecutionResult(
            success=False,
            workflow_name="Empty Failed",
            variables={},
            executed_nodes=0,
            total_nodes=0,
        )

        assert result.progress == 0.0  # Failure with 0 nodes = 0%

    def test_execution_result_to_dict(self) -> None:
        """ExecutionResult.to_dict - serializes all properties."""
        result = ExecutionResult(
            success=True,
            workflow_name="Test Workflow",
            variables={"key": "value"},
            error=None,
            executed_nodes=5,
            total_nodes=5,
            duration_ms=1500,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["workflow_name"] == "Test Workflow"
        assert data["variables"] == {"key": "value"}
        assert data["error"] is None
        assert data["executed_nodes"] == 5
        assert data["total_nodes"] == 5
        assert data["duration_ms"] == 1500
        assert data["progress"] == 100.0

    def test_execution_result_repr(self) -> None:
        """ExecutionResult.__repr__ - readable string format."""
        result = ExecutionResult(
            success=True,
            workflow_name="Test",
            variables={},
            executed_nodes=5,
            total_nodes=5,
        )

        repr_str = repr(result)

        assert "SUCCESS" in repr_str
        assert "Test" in repr_str
        assert "100.0%" in repr_str


class TestExecuteLocalSuccess:
    """Happy path tests for ExecuteLocalUseCase."""

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self) -> None:
        """Execute valid workflow - returns success result."""
        # Arrange
        mock_event_bus = Mock()
        use_case = ExecuteLocalUseCase(event_bus=mock_event_bus)

        workflow_data = {
            "metadata": {
                "name": "Test Workflow",
                "description": "Test",
                "version": "1.0",
            },
            "nodes": {
                "node-1": {"type": "StartNode"},
                "node-2": {"type": "EndNode"},
            },
            "connections": [{"source": "node-1", "target": "node-2"}],
            "variables": {},
        }

        # Mock the ExecuteWorkflowUseCase that gets created
        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_use_case_instance = AsyncMock()
            mock_use_case_instance.execute.return_value = True
            mock_use_case_instance.context = Mock(variables={"result": "ok"})
            mock_use_case_instance.start_time = datetime.utcnow()
            mock_use_case_instance.end_time = datetime.utcnow()
            mock_use_case_instance.executed_nodes = ["node-1", "node-2"]
            mock_use_case_class.return_value = mock_use_case_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Test Workflow"
                mock_workflow.nodes = ["node-1", "node-2"]
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(
                    workflow_data=workflow_data,
                    variables={"input": "test"},
                )

        # Assert
        assert result.success is True
        assert result.workflow_name == "Test Workflow"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_workflow_with_variables(self) -> None:
        """Execute workflow with initial variables - variables passed through."""
        # Arrange
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Vars Workflow", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={"input": "test", "output": "done"})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = []
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Vars Workflow"
                mock_workflow.nodes = []
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(
                    workflow_data=workflow_data,
                    variables={"input": "test"},
                )

        # Assert
        assert result.success is True
        assert "input" in result.variables
        assert "output" in result.variables

    @pytest.mark.asyncio
    async def test_execute_workflow_partial_execution(self) -> None:
        """Execute workflow to specific node - partial execution mode."""
        # Arrange
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Partial Workflow", "version": "1.0"},
            "nodes": {
                "node-1": {"type": "StartNode"},
                "node-2": {"type": "ProcessNode"},
                "node-3": {"type": "EndNode"},
            },
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = ["node-1", "node-2"]
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Partial Workflow"
                mock_workflow.nodes = ["node-1", "node-2", "node-3"]
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(
                    workflow_data=workflow_data,
                    run_to_node_id="node-2",
                )

        # Assert
        assert result.success is True
        assert result.executed_nodes == 2
        assert result.total_nodes == 3

    @pytest.mark.asyncio
    async def test_execute_from_json_success(self) -> None:
        """Execute workflow from JSON string - parses and executes."""
        # Arrange
        use_case = ExecuteLocalUseCase()

        workflow_json = """{
            "metadata": {"name": "JSON Workflow", "version": "1.0"},
            "nodes": {},
            "connections": []
        }"""

        with patch.object(use_case, "execute") as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True,
                workflow_name="JSON Workflow",
                variables={},
            )

            # Act
            result = await use_case.execute_from_json(
                workflow_json=workflow_json,
                variables={"test": "value"},
            )

        # Assert
        assert result.success is True
        assert result.workflow_name == "JSON Workflow"
        mock_execute.assert_awaited_once()


class TestExecuteLocalError:
    """Sad path tests for ExecuteLocalUseCase."""

    @pytest.mark.asyncio
    async def test_execute_empty_workflow_data_raises_error(self) -> None:
        """Execute with empty workflow_data - raises ValueError."""
        use_case = ExecuteLocalUseCase()

        # Act & Assert
        with pytest.raises(ValueError, match="workflow_data cannot be empty"):
            await use_case.execute(workflow_data={})

    @pytest.mark.asyncio
    async def test_execute_none_workflow_data_raises_error(self) -> None:
        """Execute with None workflow_data - raises ValueError."""
        use_case = ExecuteLocalUseCase()

        # Act & Assert
        with pytest.raises(ValueError, match="workflow_data cannot be empty"):
            await use_case.execute(workflow_data=None)

    @pytest.mark.asyncio
    async def test_execute_invalid_workflow_format_returns_error(self) -> None:
        """Execute with invalid workflow format - returns error result."""
        use_case = ExecuteLocalUseCase()

        # Missing both 'metadata' and 'name' keys
        workflow_data = {
            "something_else": "invalid",
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
        ) as mock_schema:
            mock_schema.from_dict.side_effect = ValueError("Invalid format")

            # Act
            result = await use_case.execute(workflow_data=workflow_data)

        # Assert
        assert result.success is False
        assert "Failed to parse workflow" in result.error

    @pytest.mark.asyncio
    async def test_execute_from_json_invalid_json(self) -> None:
        """Execute from invalid JSON string - returns error result."""
        use_case = ExecuteLocalUseCase()

        # Act
        result = await use_case.execute_from_json(
            workflow_json="{invalid json}",
        )

        # Assert
        assert result.success is False
        assert "Invalid JSON" in result.error

    @pytest.mark.asyncio
    async def test_execute_workflow_failure(self) -> None:
        """Execute workflow that fails - returns error result."""
        # Arrange
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Failing Workflow", "version": "1.0"},
            "nodes": {"node-1": {"type": "FailingNode"}},
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = False  # Execution failed
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = ["node-1"]
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Failing Workflow"
                mock_workflow.nodes = ["node-1"]
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(workflow_data=workflow_data)

        # Assert
        assert result.success is False
        assert result.error == "Execution failed"

    @pytest.mark.asyncio
    async def test_execute_workflow_exception(self) -> None:
        """Execute workflow that throws exception - captured in error result."""
        # Arrange
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Exception Workflow", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.side_effect = RuntimeError("Unexpected error")
            mock_instance.executed_nodes = []
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Exception Workflow"
                mock_workflow.nodes = ["node-1"]
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(workflow_data=workflow_data)

        # Assert
        assert result.success is False
        assert "Unexpected error" in result.error


class TestExecuteLocalEdgeCases:
    """Edge case tests for ExecuteLocalUseCase."""

    @pytest.mark.asyncio
    async def test_execute_legacy_workflow_format(self) -> None:
        """Execute workflow in legacy format (name at root) - converts and executes."""
        use_case = ExecuteLocalUseCase()

        # Legacy format without metadata wrapper
        workflow_data = {
            "name": "Legacy Workflow",
            "description": "Old format",
            "version": "1.0",
            "nodes": {},
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = []
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Legacy Workflow"
                mock_workflow.nodes = []
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(workflow_data=workflow_data)

        # Assert
        assert result.success is True
        assert result.workflow_name == "Legacy Workflow"

    @pytest.mark.asyncio
    async def test_execute_single_node_mode(self) -> None:
        """Execute in single node mode - only executes target node."""
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Single Node Test", "version": "1.0"},
            "nodes": {
                "node-1": {"type": "StartNode"},
                "node-2": {"type": "TargetNode"},
                "node-3": {"type": "EndNode"},
            },
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = ["node-2"]  # Only target node
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Single Node Test"
                mock_workflow.nodes = ["node-1", "node-2", "node-3"]
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(
                    workflow_data=workflow_data,
                    run_to_node_id="node-2",
                    single_node=True,
                )

        # Assert
        assert result.success is True
        assert result.executed_nodes == 1

    @pytest.mark.asyncio
    async def test_execute_continue_on_error_mode(self) -> None:
        """Execute with continue_on_error=True - passes setting to executor."""
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Continue Workflow", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = []
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Continue Workflow"
                mock_workflow.nodes = []
                mock_schema.from_dict.return_value = mock_workflow

                with patch(
                    "casare_rpa.application.orchestrator.use_cases.execute_local.ExecutionSettings"
                ) as mock_settings:
                    # Act
                    result = await use_case.execute(
                        workflow_data=workflow_data,
                        continue_on_error=True,
                        node_timeout=60.0,
                    )

                    # Assert: Settings created with correct params
                    mock_settings.assert_called_once()
                    call_kwargs = mock_settings.call_args.kwargs
                    assert call_kwargs["continue_on_error"] is True
                    assert call_kwargs["node_timeout"] == 60.0

    @pytest.mark.asyncio
    async def test_execute_without_event_bus(self) -> None:
        """Execute without event bus - still works (optional dependency)."""
        use_case = ExecuteLocalUseCase(event_bus=None)

        workflow_data = {
            "metadata": {"name": "No Events Workflow", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = datetime.utcnow()
            mock_instance.end_time = datetime.utcnow()
            mock_instance.executed_nodes = []
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "No Events Workflow"
                mock_workflow.nodes = []
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(workflow_data=workflow_data)

        # Assert
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_duration_calculation(self) -> None:
        """Execute workflow - duration_ms calculated correctly."""
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Timed Workflow", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }

        start = datetime(2025, 1, 1, 12, 0, 0, 0)
        end = datetime(2025, 1, 1, 12, 0, 1, 500000)  # 1.5 seconds later

        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.ExecuteWorkflowUseCase"
        ) as mock_use_case_class:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = True
            mock_instance.context = Mock(variables={})
            mock_instance.start_time = start
            mock_instance.end_time = end
            mock_instance.executed_nodes = []
            mock_use_case_class.return_value = mock_instance

            with patch(
                "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
            ) as mock_schema:
                mock_workflow = Mock()
                mock_workflow.metadata.name = "Timed Workflow"
                mock_workflow.nodes = []
                mock_schema.from_dict.return_value = mock_workflow

                # Act
                result = await use_case.execute(workflow_data=workflow_data)

        # Assert: 1.5 seconds = 1500ms
        assert result.duration_ms == 1500

    @pytest.mark.asyncio
    async def test_execute_preserves_variables_on_failure(self) -> None:
        """Execute failing workflow - original variables preserved in result."""
        use_case = ExecuteLocalUseCase()

        workflow_data = {
            "metadata": {"name": "Preserve Vars", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }
        initial_vars = {"input": "test", "config": {"key": "value"}}

        # Simulate parse failure to test variable preservation
        with patch(
            "casare_rpa.application.orchestrator.use_cases.execute_local.WorkflowSchema"
        ) as mock_schema:
            mock_schema.from_dict.side_effect = ValueError("Parse error")

            # Act
            result = await use_case.execute(
                workflow_data=workflow_data,
                variables=initial_vars,
            )

        # Assert
        assert result.success is False
        assert result.variables == initial_vars
