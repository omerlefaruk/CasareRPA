"""
Tests for JobExecutor.

Tests cover:
- Happy path: Successful job execution, progress reporting, result collection
- Sad path: Invalid workflow JSON, execution failures, timeout handling
- Edge cases: Job cancellation, result storage, concurrent execution limits
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from casare_rpa.infrastructure.agent.job_executor import (
    JobExecutionError,
    JobExecutor,
)


# ============================================================================
# Happy Path Tests - Basic Operations
# ============================================================================


class TestJobExecutorCreation:
    """Test JobExecutor initialization."""

    def test_create_with_defaults(self):
        """Creating executor with defaults succeeds."""
        executor = JobExecutor()

        assert executor.progress_callback is None
        assert executor.continue_on_error is False
        assert executor.job_timeout == 3600.0
        assert executor.active_job_count == 0

    def test_create_with_custom_settings(self, progress_callback):
        """Creating executor with custom settings succeeds."""
        executor = JobExecutor(
            progress_callback=progress_callback,
            continue_on_error=True,
            job_timeout=1800.0,
        )

        assert executor.progress_callback is progress_callback
        assert executor.continue_on_error is True
        assert executor.job_timeout == 1800.0


class TestJobExecutorExecute:
    """Test job execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_result_dict(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Execution returns result dictionary with expected fields."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(sample_job_data)

        assert "success" in result
        assert "job_id" in result
        assert "started_at" in result
        assert "completed_at" in result
        assert "duration_ms" in result
        assert "nodes_executed" in result

    @pytest.mark.asyncio
    async def test_execute_successful_job(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Successful job execution returns success=True."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(sample_job_data)

        assert result["success"] is True
        assert result["job_id"] == "job-test-001"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_execute_sets_job_variables(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Execution sets job variables in context."""
        captured_variables = {}

        def capture_use_case(workflow, event_bus, settings, initial_variables):
            captured_variables.update(initial_variables)
            return mock_execute_workflow_use_case

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase",
                side_effect=capture_use_case,
            ):
                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    await executor.execute(sample_job_data)

        assert "_job_id" in captured_variables
        assert captured_variables["_job_id"] == "job-test-001"
        assert "_job_payload" in captured_variables

    @pytest.mark.asyncio
    async def test_execute_stores_result(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Execution stores result for later retrieval."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    await executor.execute(sample_job_data)

        stored_result = executor.get_result("job-test-001")
        assert stored_result is not None
        assert stored_result["job_id"] == "job-test-001"


class TestJobExecutorProgressReporting:
    """Test progress reporting functionality."""

    @pytest.mark.asyncio
    async def test_progress_callback_invoked(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
        progress_callback,
    ):
        """Progress callback is invoked during execution."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor(progress_callback=progress_callback)
                    await executor.execute(sample_job_data)

        # Should have at least loading and completion progress
        assert len(progress_callback.calls) >= 2

    @pytest.mark.asyncio
    async def test_progress_includes_loading_message(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
        progress_callback,
    ):
        """Progress includes workflow loading message."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor(progress_callback=progress_callback)
                    await executor.execute(sample_job_data)

        # First call should be loading message
        job_id, progress, message = progress_callback.calls[0]
        assert job_id == "job-test-001"
        assert progress == 0
        assert "Loading" in message


# ============================================================================
# Sad Path Tests - Error Handling
# ============================================================================


class TestJobExecutorFailures:
    """Test error handling in job execution."""

    @pytest.mark.asyncio
    async def test_invalid_json_workflow_returns_error(self, progress_callback):
        """Invalid JSON in workflow_json returns error result."""
        job_data = {
            "job_id": "job-invalid-001",
            "workflow_name": "Invalid Workflow",
            "workflow_json": "not valid json {{{",
        }

        executor = JobExecutor(progress_callback=progress_callback)
        result = await executor.execute(job_data)

        assert result["success"] is False
        assert "Invalid workflow JSON" in result["error"]

    @pytest.mark.asyncio
    async def test_wrong_type_workflow_json_returns_error(self, progress_callback):
        """Wrong type workflow_json returns error result."""
        job_data = {
            "job_id": "job-wrong-type-001",
            "workflow_name": "Wrong Type Workflow",
            "workflow_json": 12345,  # Should be str or dict
        }

        executor = JobExecutor(progress_callback=progress_callback)
        result = await executor.execute(job_data)

        assert result["success"] is False
        assert "must be str or dict" in result["error"]

    @pytest.mark.asyncio
    async def test_failed_workflow_execution_returns_error(
        self,
        sample_job_data,
        mock_execute_workflow_use_case_failure,
    ):
        """Failed workflow execution returns error in result."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case_failure

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(sample_job_data)

        assert result["success"] is False
        assert result["error"] is not None
        assert "Test error occurred" in result["error"]

    @pytest.mark.asyncio
    async def test_execution_timeout_returns_error(self, sample_job_data):
        """Job timeout returns error in result."""
        # Create a use case that hangs
        mock_use_case = MagicMock()

        async def slow_execute():
            await asyncio.sleep(10)  # Longer than timeout
            return True

        mock_use_case.execute = slow_execute
        mock_use_case.executed_nodes = []
        mock_use_case.context = None

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor(job_timeout=0.1)  # Very short timeout
                    result = await executor.execute(sample_job_data)

        assert result["success"] is False
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_unexpected_exception_returns_error(self, sample_job_data):
        """Unexpected exception during execution returns error."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.side_effect = Exception("Unexpected error!")

            executor = JobExecutor()
            result = await executor.execute(sample_job_data)

        assert result["success"] is False
        assert "Unexpected error" in result["error"]

    @pytest.mark.asyncio
    async def test_progress_callback_error_handled(
        self, sample_job_data, mock_execute_workflow_use_case
    ):
        """Error in progress callback is handled gracefully."""

        async def failing_callback(job_id: str, progress: int, message: str) -> None:
            raise Exception("Callback failed")

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor(progress_callback=failing_callback)
                    result = await executor.execute(sample_job_data)

        # Should complete despite callback error
        assert result["job_id"] == "job-test-001"


# ============================================================================
# Result Management Tests
# ============================================================================


class TestJobExecutorResultManagement:
    """Test result storage and retrieval."""

    @pytest.mark.asyncio
    async def test_get_result_returns_none_for_unknown(self):
        """get_result returns None for unknown job ID."""
        executor = JobExecutor()
        result = executor.get_result("nonexistent-job")

        assert result is None

    @pytest.mark.asyncio
    async def test_clear_result_removes_stored_result(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """clear_result removes stored job result."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    await executor.execute(sample_job_data)

        assert executor.get_result("job-test-001") is not None

        executor.clear_result("job-test-001")

        assert executor.get_result("job-test-001") is None

    def test_clear_result_nonexistent_does_not_raise(self):
        """Clearing nonexistent result does not raise."""
        executor = JobExecutor()
        executor.clear_result("nonexistent-job")  # Should not raise


# ============================================================================
# Job Cancellation Tests
# ============================================================================


class TestJobExecutorCancellation:
    """Test job cancellation functionality."""

    def test_cancel_job_not_found_returns_false(self):
        """Cancelling unknown job returns False."""
        executor = JobExecutor()
        result = executor.cancel_job("nonexistent-job")

        assert result is False

    def test_cancel_job_in_active_jobs_returns_true(self):
        """Cancelling active job returns True."""
        executor = JobExecutor()

        # Simulate an active job
        mock_task = MagicMock()
        executor._active_jobs["job-001"] = mock_task

        result = executor.cancel_job("job-001")

        assert result is True
        mock_task.cancel.assert_called_once()


# ============================================================================
# Workflow JSON Parsing Tests
# ============================================================================


class TestJobExecutorWorkflowParsing:
    """Test workflow JSON parsing."""

    @pytest.mark.asyncio
    async def test_dict_workflow_json_accepted(self, mock_execute_workflow_use_case):
        """Dictionary workflow_json is accepted."""
        job_data = {
            "job_id": "job-dict-001",
            "workflow_name": "Dict Workflow",
            "workflow_json": {
                "name": "Test",
                "nodes": [],
                "connections": [],
            },
        }

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(job_data)

        assert result["success"] is True
        mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_string_workflow_json_parsed(self, mock_execute_workflow_use_case):
        """String workflow_json is parsed to dict."""
        workflow_dict = {
            "name": "Test",
            "nodes": [],
            "connections": [],
        }
        job_data = {
            "job_id": "job-str-001",
            "workflow_name": "String Workflow",
            "workflow_json": json.dumps(workflow_dict),
        }

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(job_data)

        assert result["success"] is True
        mock_load.assert_called_once_with(workflow_dict)


# ============================================================================
# Duration and Timing Tests
# ============================================================================


class TestJobExecutorTiming:
    """Test timing and duration tracking."""

    @pytest.mark.asyncio
    async def test_duration_calculated_correctly(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Duration is calculated in milliseconds."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(sample_job_data)

        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_timestamps_are_iso_format(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Timestamps are in ISO format."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(sample_job_data)

        # Should be parseable ISO timestamps
        datetime.fromisoformat(result["started_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(result["completed_at"].replace("Z", "+00:00"))


# ============================================================================
# Edge Cases
# ============================================================================


class TestJobExecutorEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_missing_job_id_uses_default(self, mock_execute_workflow_use_case):
        """Missing job_id uses 'unknown' as default."""
        job_data = {
            # No job_id
            "workflow_name": "Test",
            "workflow_json": {"nodes": [], "connections": []},
        }

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(job_data)

        assert result["job_id"] == "unknown"

    @pytest.mark.asyncio
    async def test_empty_workflow_json_string(self):
        """Empty workflow_json string is handled."""
        job_data = {
            "job_id": "job-empty-001",
            "workflow_name": "Empty Workflow",
            "workflow_json": "{}",
        }

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.side_effect = Exception("Empty workflow")

            executor = JobExecutor()
            result = await executor.execute(job_data)

        # Should handle gracefully
        assert result["success"] is False

    def test_active_job_count_initially_zero(self):
        """Active job count is zero on creation."""
        executor = JobExecutor()
        assert executor.active_job_count == 0

    @pytest.mark.asyncio
    async def test_initial_variables_merged_with_payload(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Initial variables are merged with job payload."""
        captured_variables = {}

        def capture_use_case(workflow, event_bus, settings, initial_variables):
            captured_variables.update(initial_variables)
            return mock_execute_workflow_use_case

        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase",
                side_effect=capture_use_case,
            ):
                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    await executor.execute(
                        sample_job_data,
                        initial_variables={"custom_var": "custom_value"},
                    )

        assert captured_variables.get("custom_var") == "custom_value"
        assert "_job_id" in captured_variables

    @pytest.mark.asyncio
    async def test_result_data_includes_execution_path(
        self,
        sample_job_data,
        mock_execute_workflow_use_case,
    ):
        """Result data includes execution path from context."""
        with patch(
            "casare_rpa.utils.workflow.workflow_loader.load_workflow_from_dict"
        ) as mock_load:
            mock_load.return_value = MagicMock()

            with patch(
                "casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase"
            ) as mock_use_case_cls:
                mock_use_case_cls.return_value = mock_execute_workflow_use_case

                with patch("casare_rpa.domain.events.EventBus"):
                    executor = JobExecutor()
                    result = await executor.execute(sample_job_data)

        assert "result_data" in result
        assert "execution_path" in result["result_data"]
