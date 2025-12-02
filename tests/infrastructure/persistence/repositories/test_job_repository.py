"""
Tests for JobRepository PostgreSQL implementation.

Tests cover:
- CRUD operations (save, get_by_id, delete)
- Query methods (get_by_robot, get_by_workflow, get_by_status, get_pending, etc.)
- Status updates (update_status, update_progress, append_logs)
- Job claiming (claim_next_job with row locking)
- Entity-to-row and row-to-entity mapping
- Error handling

All database operations are mocked using AsyncMock.
"""

from datetime import datetime
from unittest.mock import AsyncMock
import pytest

from casare_rpa.domain.orchestrator.entities.job import (
    Job,
    JobPriority,
    JobStatus,
)
from casare_rpa.infrastructure.persistence.repositories.job_repository import (
    JobRepository,
)

from .conftest import create_mock_record


class TestJobRepositoryRowConversion:
    """Tests for row-to-entity and entity-to-row conversion."""

    def test_row_to_job_full_data(self, sample_job_row):
        """Test converting database row with all fields to Job entity."""
        repo = JobRepository(pool_manager=AsyncMock())
        job = repo._row_to_job(dict(sample_job_row))

        assert job.id == "job-uuid-1234"
        assert job.workflow_id == "wf-uuid-5678"
        assert job.workflow_name == "Test Workflow"
        assert job.robot_id == "robot-uuid-1234"
        assert job.status == JobStatus.PENDING
        assert job.priority == JobPriority.NORMAL
        assert job.environment == "production"
        assert job.created_by == "test-user"

    def test_row_to_job_with_running_status(self):
        """Test converting row with running job status."""
        row = create_mock_record(
            {
                "job_id": "job-running",
                "workflow_id": "wf-1",
                "workflow_name": "Running Workflow",
                "robot_uuid": "robot-1",
                "robot_name": "Robot",
                "status": "running",
                "priority": 2,  # HIGH
                "environment": "prod",
                "payload": '{"nodes": [{"id": "n1"}]}',
                "scheduled_time": None,
                "started_at": datetime(2024, 1, 15, 10, 30, 0),
                "completed_at": None,
                "duration_ms": 0,
                "progress": 45,
                "current_node": "n1",
                "result": "{}",
                "logs": "Starting execution...",
                "error_message": "",
                "created_at": datetime(2024, 1, 15, 10, 0, 0),
                "created_by": "user",
            }
        )

        repo = JobRepository(pool_manager=AsyncMock())
        job = repo._row_to_job(dict(row))

        assert job.status == JobStatus.RUNNING
        assert job.priority == JobPriority.HIGH
        assert job.progress == 45
        assert job.current_node == "n1"
        assert job.started_at == datetime(2024, 1, 15, 10, 30, 0)

    def test_row_to_job_completed_with_result(self):
        """Test converting completed job with result data."""
        row = create_mock_record(
            {
                "job_id": "job-done",
                "workflow_id": "wf-1",
                "workflow_name": "Done Workflow",
                "robot_uuid": "robot-1",
                "robot_name": "",
                "status": "completed",
                "priority": 1,
                "environment": "prod",
                "payload": "{}",
                "scheduled_time": None,
                "started_at": datetime(2024, 1, 15, 10, 0, 0),
                "completed_at": datetime(2024, 1, 15, 10, 5, 0),
                "duration_ms": 300000,
                "progress": 100,
                "current_node": "",
                "result": '{"output": "success", "data": {"count": 42}}',
                "logs": "Completed successfully",
                "error_message": "",
                "created_at": datetime(2024, 1, 15, 9, 0, 0),
                "created_by": "scheduler",
            }
        )

        repo = JobRepository(pool_manager=AsyncMock())
        job = repo._row_to_job(dict(row))

        assert job.status == JobStatus.COMPLETED
        assert job.progress == 100
        assert job.duration_ms == 300000
        assert job.result["output"] == "success"
        assert job.result["data"]["count"] == 42

    def test_row_to_job_failed_with_error(self):
        """Test converting failed job with error message."""
        row = create_mock_record(
            {
                "job_id": "job-fail",
                "workflow_id": "wf-1",
                "workflow_name": "Failed Workflow",
                "robot_uuid": "robot-1",
                "robot_name": "",
                "status": "failed",
                "priority": 1,
                "environment": "prod",
                "payload": "{}",
                "scheduled_time": None,
                "started_at": datetime(2024, 1, 15, 10, 0, 0),
                "completed_at": datetime(2024, 1, 15, 10, 1, 0),
                "duration_ms": 60000,
                "progress": 25,
                "current_node": "failed_node",
                "result": "{}",
                "logs": "Error occurred",
                "error_message": "Element not found: #login-button",
                "created_at": datetime(2024, 1, 15, 9, 0, 0),
                "created_by": "user",
            }
        )

        repo = JobRepository(pool_manager=AsyncMock())
        job = repo._row_to_job(dict(row))

        assert job.status == JobStatus.FAILED
        assert job.error_message == "Element not found: #login-button"
        assert job.current_node == "failed_node"

    def test_row_to_job_unknown_status_defaults_pending(self):
        """Test that unknown status defaults to pending."""
        row = create_mock_record(
            {
                "job_id": "job-1",
                "workflow_id": "wf-1",
                "workflow_name": "Workflow",
                "robot_uuid": "robot-1",
                "robot_name": "",
                "status": "unknown_status",
                "priority": 1,
                "environment": "default",
                "payload": "{}",
                "result": "{}",
            }
        )

        repo = JobRepository(pool_manager=AsyncMock())
        job = repo._row_to_job(dict(row))

        assert job.status == JobStatus.PENDING

    def test_row_to_job_priority_from_string(self):
        """Test priority parsing from string."""
        row = create_mock_record(
            {
                "job_id": "job-1",
                "workflow_id": "wf-1",
                "workflow_name": "Workflow",
                "robot_uuid": "robot-1",
                "robot_name": "",
                "status": "pending",
                "priority": "CRITICAL",
                "environment": "default",
                "payload": "{}",
                "result": "{}",
            }
        )

        repo = JobRepository(pool_manager=AsyncMock())
        job = repo._row_to_job(dict(row))

        assert job.priority == JobPriority.CRITICAL

    def test_job_to_params_conversion(self):
        """Test converting Job entity to database parameters."""
        job = Job(
            id="job-123",
            workflow_id="wf-456",
            workflow_name="Test Workflow",
            robot_id="robot-789",
            robot_name="Test Robot",
            status=JobStatus.QUEUED,
            priority=JobPriority.HIGH,
            environment="staging",
            workflow_json='{"nodes": []}',
            progress=10,
            current_node="node-1",
            created_by="admin",
        )

        repo = JobRepository(pool_manager=AsyncMock())
        params = repo._job_to_params(job)

        assert params["job_id"] == "job-123"
        assert params["workflow_id"] == "wf-456"
        assert params["workflow_name"] == "Test Workflow"
        assert params["robot_uuid"] == "robot-789"
        assert params["status"] == "queued"
        assert params["priority"] == 2  # HIGH = 2
        assert params["environment"] == "staging"
        assert params["progress"] == 10


class TestJobRepositorySave:
    """Tests for save operation."""

    @pytest.mark.asyncio
    async def test_save_job_success(self, mock_pool_manager, mock_connection):
        """Test successful job save (upsert)."""
        mock_connection.execute.return_value = "INSERT 1"
        job = Job(
            id="job-new",
            workflow_id="wf-1",
            workflow_name="New Workflow",
            robot_id="robot-1",
            status=JobStatus.PENDING,
        )

        repo = JobRepository(pool_manager=mock_pool_manager)
        result = await repo.save(job)

        assert result.id == "job-new"
        mock_connection.execute.assert_awaited_once()

        # Verify SQL contains INSERT with ON CONFLICT
        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO jobs" in sql
        assert "ON CONFLICT (job_id) DO UPDATE" in sql

    @pytest.mark.asyncio
    async def test_save_job_with_result(self, mock_pool_manager, mock_connection):
        """Test saving job with result serializes to JSONB."""
        job = Job(
            id="job-result",
            workflow_id="wf-1",
            workflow_name="Workflow",
            robot_id="robot-1",
            result={"output": "data", "count": 100},
        )

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.save(job)

        call_args = mock_connection.execute.call_args
        params = call_args[0]
        # Result should be JSON string
        result_param = params[15]  # Position in SQL
        assert "output" in result_param
        assert "count" in result_param

    @pytest.mark.asyncio
    async def test_save_job_database_error(self, mock_pool_manager, mock_connection):
        """Test save handles database errors properly."""
        mock_connection.execute.side_effect = Exception("Constraint violation")
        job = Job(
            id="job-err",
            workflow_id="wf-1",
            workflow_name="Error Job",
            robot_id="robot-1",
        )

        repo = JobRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception) as exc_info:
            await repo.save(job)

        assert "Constraint violation" in str(exc_info.value)


class TestJobRepositoryGetById:
    """Tests for get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test getting existing job by ID."""
        mock_connection.fetchrow.return_value = sample_job_row

        repo = JobRepository(pool_manager=mock_pool_manager)
        job = await repo.get_by_id("job-uuid-1234")

        assert job is not None
        assert job.id == "job-uuid-1234"
        assert job.workflow_name == "Test Workflow"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_pool_manager, mock_connection):
        """Test getting non-existent job returns None."""
        mock_connection.fetchrow.return_value = None

        repo = JobRepository(pool_manager=mock_pool_manager)
        job = await repo.get_by_id("nonexistent")

        assert job is None


class TestJobRepositoryGetByRobot:
    """Tests for get_by_robot operation."""

    @pytest.mark.asyncio
    async def test_get_by_robot(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test getting jobs by robot ID."""
        mock_connection.fetch.return_value = [sample_job_row]

        repo = JobRepository(pool_manager=mock_pool_manager)
        jobs = await repo.get_by_robot("robot-uuid-1234")

        assert len(jobs) == 1
        assert jobs[0].robot_id == "robot-uuid-1234"

        # Verify SQL query
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "robot_uuid = $1" in sql
        assert "ORDER BY created_at DESC" in sql


class TestJobRepositoryGetByWorkflow:
    """Tests for get_by_workflow operation."""

    @pytest.mark.asyncio
    async def test_get_by_workflow(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test getting jobs by workflow ID."""
        mock_connection.fetch.return_value = [sample_job_row]

        repo = JobRepository(pool_manager=mock_pool_manager)
        jobs = await repo.get_by_workflow("wf-uuid-5678")

        assert len(jobs) == 1

        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "workflow_id = $1" in sql


class TestJobRepositoryGetByStatus:
    """Tests for get_by_status operation."""

    @pytest.mark.asyncio
    async def test_get_by_status_pending(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test filtering jobs by pending status."""
        mock_connection.fetch.return_value = [sample_job_row]

        repo = JobRepository(pool_manager=mock_pool_manager)
        jobs = await repo.get_by_status(JobStatus.PENDING)

        assert len(jobs) == 1

        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "status = $1" in sql
        assert "ORDER BY priority DESC, created_at ASC" in sql

    @pytest.mark.asyncio
    async def test_get_pending_alias(self, mock_pool_manager, mock_connection):
        """Test get_pending calls get_by_status with PENDING."""
        mock_connection.fetch.return_value = []

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.get_pending()

        call_args = mock_connection.fetch.call_args
        assert call_args[0][1] == "pending"

    @pytest.mark.asyncio
    async def test_get_queued_alias(self, mock_pool_manager, mock_connection):
        """Test get_queued calls get_by_status with QUEUED."""
        mock_connection.fetch.return_value = []

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.get_queued()

        call_args = mock_connection.fetch.call_args
        assert call_args[0][1] == "queued"

    @pytest.mark.asyncio
    async def test_get_running_alias(self, mock_pool_manager, mock_connection):
        """Test get_running calls get_by_status with RUNNING."""
        mock_connection.fetch.return_value = []

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.get_running()

        call_args = mock_connection.fetch.call_args
        assert call_args[0][1] == "running"


class TestJobRepositoryGetPendingForRobot:
    """Tests for get_pending_for_robot operation."""

    @pytest.mark.asyncio
    async def test_get_pending_for_robot(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test getting pending jobs for specific robot."""
        mock_connection.fetch.return_value = [sample_job_row]

        repo = JobRepository(pool_manager=mock_pool_manager)
        jobs = await repo.get_pending_for_robot("robot-uuid-1234")

        assert len(jobs) == 1

        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "robot_uuid = $1" in sql
        assert "status IN ('pending', 'queued')" in sql


class TestJobRepositoryUpdateStatus:
    """Tests for update_status operation."""

    @pytest.mark.asyncio
    async def test_update_status_to_running(self, mock_pool_manager, mock_connection):
        """Test updating job status to running sets started_at."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.update_status("job-123", JobStatus.RUNNING)

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "started_at = $" in sql

    @pytest.mark.asyncio
    async def test_update_status_to_completed_sets_completed_at(
        self, mock_pool_manager, mock_connection
    ):
        """Test updating to completed/failed sets completed_at."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.update_status(
            "job-123",
            JobStatus.COMPLETED,
            result={"output": "success"},
        )

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "completed_at = $" in sql
        assert "result = $" in sql

    @pytest.mark.asyncio
    async def test_update_status_to_failed_with_error(
        self, mock_pool_manager, mock_connection
    ):
        """Test updating to failed with error message."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.update_status(
            "job-123",
            JobStatus.FAILED,
            error_message="Connection timeout",
        )

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "error_message = $" in sql

        # Find error message in params
        params = call_args[0]
        assert "Connection timeout" in params


class TestJobRepositoryUpdateProgress:
    """Tests for update_progress operation."""

    @pytest.mark.asyncio
    async def test_update_progress(self, mock_pool_manager, mock_connection):
        """Test updating job progress."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.update_progress("job-123", 75, "current-node")

        call_args = mock_connection.execute.call_args
        params = call_args[0]
        assert params[1] == "job-123"
        assert params[2] == 75
        assert params[3] == "current-node"

    @pytest.mark.asyncio
    async def test_update_progress_clamped(self, mock_pool_manager, mock_connection):
        """Test progress is clamped to 0-100 range."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)

        # Test upper bound
        await repo.update_progress("job-123", 150, "")
        call_args = mock_connection.execute.call_args
        assert call_args[0][2] == 100

        # Test lower bound
        await repo.update_progress("job-123", -10, "")
        call_args = mock_connection.execute.call_args
        assert call_args[0][2] == 0


class TestJobRepositoryAppendLogs:
    """Tests for append_logs operation."""

    @pytest.mark.asyncio
    async def test_append_logs(self, mock_pool_manager, mock_connection):
        """Test appending to job logs."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.append_logs("job-123", "New log entry")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "logs = logs ||" in sql


class TestJobRepositoryCalculateDuration:
    """Tests for calculate_duration operation."""

    @pytest.mark.asyncio
    async def test_calculate_duration(self, mock_pool_manager, mock_connection):
        """Test calculating job duration from timestamps."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.calculate_duration("job-123")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "EXTRACT(EPOCH FROM (completed_at - started_at))" in sql


class TestJobRepositoryDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_pool_manager, mock_connection):
        """Test deleting existing job returns True."""
        mock_connection.execute.return_value = "DELETE 1"

        repo = JobRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("job-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_pool_manager, mock_connection):
        """Test deleting non-existent job returns False."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = JobRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("nonexistent")

        assert result is False


class TestJobRepositoryDeleteOldJobs:
    """Tests for delete_old_jobs operation."""

    @pytest.mark.asyncio
    async def test_delete_old_jobs(self, mock_pool_manager, mock_connection):
        """Test deleting old completed/failed jobs."""
        mock_connection.execute.return_value = "DELETE 10"

        repo = JobRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_old_jobs(days=30)

        assert count == 10

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "status IN ('completed', 'failed', 'cancelled', 'timeout')" in sql
        assert "created_at < NOW()" in sql


class TestJobRepositoryClaimNextJob:
    """Tests for claim_next_job operation with row locking."""

    @pytest.mark.asyncio
    async def test_claim_next_job_success(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test atomically claiming next pending job."""
        # First fetchrow returns the job to claim
        # Second fetchrow returns updated job
        updated_row = create_mock_record(
            {
                **dict(sample_job_row),
                "status": "queued",
                "robot_uuid": "robot-claimer",
            }
        )
        mock_connection.fetchrow.side_effect = [sample_job_row, updated_row]

        repo = JobRepository(pool_manager=mock_pool_manager)
        job = await repo.claim_next_job("robot-claimer")

        assert job is not None
        assert job.status == JobStatus.QUEUED

        # Verify SELECT FOR UPDATE SKIP LOCKED
        first_call = mock_connection.fetchrow.call_args_list[0]
        sql = first_call[0][0]
        assert "FOR UPDATE SKIP LOCKED" in sql
        assert "status = 'pending'" in sql
        assert "ORDER BY priority DESC" in sql

    @pytest.mark.asyncio
    async def test_claim_next_job_none_available(
        self, mock_pool_manager, mock_connection
    ):
        """Test claiming when no jobs available returns None."""
        mock_connection.fetchrow.return_value = None

        repo = JobRepository(pool_manager=mock_pool_manager)
        job = await repo.claim_next_job("robot-claimer")

        assert job is None

    @pytest.mark.asyncio
    async def test_claim_next_job_uses_transaction(
        self, mock_pool_manager, mock_connection, sample_job_row
    ):
        """Test claiming uses transaction for atomicity."""
        updated_row = create_mock_record(
            {
                **dict(sample_job_row),
                "status": "queued",
            }
        )
        mock_connection.fetchrow.side_effect = [sample_job_row, updated_row]

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.claim_next_job("robot-1")

        # Verify transaction context manager was used
        mock_connection.transaction.assert_called_once()


class TestJobRepositoryConnectionManagement:
    """Tests for connection pool management."""

    @pytest.mark.asyncio
    async def test_connection_released_after_success(
        self, mock_pool_manager, mock_pool, mock_connection, sample_job_row
    ):
        """Test connection is released after successful operation."""
        mock_connection.fetchrow.return_value = sample_job_row

        repo = JobRepository(pool_manager=mock_pool_manager)
        await repo.get_by_id("job-123")

        mock_pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_after_error(
        self, mock_pool_manager, mock_pool, mock_connection
    ):
        """Test connection is released even after error."""
        mock_connection.fetchrow.side_effect = Exception("DB error")

        repo = JobRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_by_id("job-123")

        mock_pool.release.assert_awaited_once_with(mock_connection)
