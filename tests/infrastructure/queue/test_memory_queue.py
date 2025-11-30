"""
Tests for MemoryQueue in-memory job queue implementation.

Tests cover:
- Basic enqueue/dequeue operations
- Priority queue ordering
- Claim and visibility timeout
- Job status updates
- Concurrent access safety
- Cleanup expired claims
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from casare_rpa.infrastructure.queue.memory_queue import (
    JobStatus,
    MemoryJob,
    MemoryQueue,
    get_memory_queue,
    initialize_memory_queue,
    shutdown_memory_queue,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def memory_queue() -> MemoryQueue:
    """Create fresh MemoryQueue instance for each test."""
    return MemoryQueue(visibility_timeout=30)


@pytest.fixture
async def started_queue() -> MemoryQueue:
    """Create and start a MemoryQueue for tests requiring running queue."""
    queue = MemoryQueue(visibility_timeout=5)
    await queue.start()
    yield queue
    await queue.stop()


@pytest.fixture
def sample_workflow_json() -> dict:
    """Sample workflow JSON for testing."""
    return {
        "name": "Test Workflow",
        "nodes": [
            {"id": "node1", "type": "start"},
            {"id": "node2", "type": "end"},
        ],
        "connections": [{"from": "node1", "to": "node2"}],
    }


# ============================================================================
# MemoryJob Tests
# ============================================================================


class TestMemoryJob:
    """Tests for MemoryJob dataclass."""

    def test_memory_job_creation_defaults(self) -> None:
        """Test MemoryJob creation with default values."""
        job = MemoryJob(
            job_id="test-123",
            workflow_id="wf-456",
            workflow_json={"nodes": []},
        )

        assert job.job_id == "test-123"
        assert job.workflow_id == "wf-456"
        assert job.priority == 10
        assert job.status == JobStatus.PENDING
        assert job.robot_id is None
        assert job.execution_mode == "lan"
        assert job.retry_count == 0
        assert job.max_retries == 3

    def test_memory_job_to_dict(self) -> None:
        """Test MemoryJob serialization to dictionary."""
        job = MemoryJob(
            job_id="test-123",
            workflow_id="wf-456",
            workflow_json={"nodes": []},
            priority=5,
            status=JobStatus.COMPLETED,
            robot_id="robot-001",
        )

        result = job.to_dict()

        assert result["job_id"] == "test-123"
        assert result["workflow_id"] == "wf-456"
        assert result["priority"] == 5
        assert result["status"] == "completed"
        assert result["robot_id"] == "robot-001"
        assert "created_at" in result

    def test_memory_job_to_dict_timestamps(self) -> None:
        """Test MemoryJob serialization handles timestamps correctly."""
        now = datetime.now(timezone.utc)
        job = MemoryJob(
            job_id="test-123",
            workflow_id="wf-456",
            workflow_json={},
            claimed_at=now,
            started_at=now,
            completed_at=now,
        )

        result = job.to_dict()

        assert result["claimed_at"] is not None
        assert result["started_at"] is not None
        assert result["completed_at"] is not None

    def test_memory_job_to_dict_null_timestamps(self) -> None:
        """Test MemoryJob serialization handles null timestamps."""
        job = MemoryJob(
            job_id="test-123",
            workflow_id="wf-456",
            workflow_json={},
        )

        result = job.to_dict()

        assert result["claimed_at"] is None
        assert result["started_at"] is None
        assert result["completed_at"] is None


# ============================================================================
# MemoryQueue Basic Operations Tests
# ============================================================================


class TestMemoryQueueBasicOperations:
    """Tests for basic queue operations."""

    @pytest.mark.asyncio
    async def test_enqueue_returns_job_id(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test enqueue returns unique job ID."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )

        assert job_id is not None
        assert len(job_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_enqueue_stores_job(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test enqueue stores job in internal dictionary."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
            priority=5,
            execution_mode="internet",
        )

        job = await memory_queue.get_job(job_id)

        assert job is not None
        assert job.workflow_id == "wf-001"
        assert job.priority == 5
        assert job.execution_mode == "internet"
        assert job.status == JobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_enqueue_multiple_jobs(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test enqueueing multiple jobs."""
        job_ids = []
        for i in range(5):
            job_id = await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
            )
            job_ids.append(job_id)

        # All job IDs should be unique
        assert len(set(job_ids)) == 5

        # All jobs should be retrievable
        for job_id in job_ids:
            job = await memory_queue.get_job(job_id)
            assert job is not None

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, memory_queue: MemoryQueue) -> None:
        """Test get_job returns None for non-existent job."""
        job = await memory_queue.get_job("non-existent-id")
        assert job is None


# ============================================================================
# MemoryQueue Claim Tests
# ============================================================================


class TestMemoryQueueClaim:
    """Tests for job claiming functionality."""

    @pytest.mark.asyncio
    async def test_claim_returns_job(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test claim returns highest priority job."""
        await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )

        job = await memory_queue.claim(robot_id="robot-001")

        assert job is not None
        assert job.workflow_id == "wf-001"
        assert job.status == JobStatus.CLAIMED
        assert job.robot_id == "robot-001"
        assert job.claimed_at is not None

    @pytest.mark.asyncio
    async def test_claim_empty_queue_returns_none(
        self, memory_queue: MemoryQueue
    ) -> None:
        """Test claim returns None when queue is empty."""
        job = await memory_queue.claim(robot_id="robot-001")
        assert job is None

    @pytest.mark.asyncio
    async def test_claim_priority_order(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test jobs are claimed in priority order (lower = higher priority)."""
        # Enqueue jobs with different priorities
        await memory_queue.enqueue(
            workflow_id="wf-low",
            workflow_json=sample_workflow_json,
            priority=15,
        )
        await memory_queue.enqueue(
            workflow_id="wf-high",
            workflow_json=sample_workflow_json,
            priority=5,
        )
        await memory_queue.enqueue(
            workflow_id="wf-medium",
            workflow_json=sample_workflow_json,
            priority=10,
        )

        # First claim should get highest priority (lowest number)
        job1 = await memory_queue.claim(robot_id="robot-001")
        assert job1.workflow_id == "wf-high"

        job2 = await memory_queue.claim(robot_id="robot-001")
        assert job2.workflow_id == "wf-medium"

        job3 = await memory_queue.claim(robot_id="robot-001")
        assert job3.workflow_id == "wf-low"

    @pytest.mark.asyncio
    async def test_claim_execution_mode_filter(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test claim filters by execution mode."""
        await memory_queue.enqueue(
            workflow_id="wf-lan",
            workflow_json=sample_workflow_json,
            execution_mode="lan",
        )
        await memory_queue.enqueue(
            workflow_id="wf-internet",
            workflow_json=sample_workflow_json,
            execution_mode="internet",
        )

        # Claim only internet jobs
        job = await memory_queue.claim(robot_id="robot-001", execution_mode="internet")

        assert job is not None
        assert job.workflow_id == "wf-internet"
        assert job.execution_mode == "internet"

    @pytest.mark.asyncio
    async def test_claim_no_matching_execution_mode(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test claim returns None when no jobs match execution mode."""
        await memory_queue.enqueue(
            workflow_id="wf-lan",
            workflow_json=sample_workflow_json,
            execution_mode="lan",
        )

        job = await memory_queue.claim(robot_id="robot-001", execution_mode="internet")

        assert job is None

    @pytest.mark.asyncio
    async def test_claimed_job_not_reclaimed(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test claimed job cannot be claimed by another robot."""
        await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )

        job1 = await memory_queue.claim(robot_id="robot-001")
        job2 = await memory_queue.claim(robot_id="robot-002")

        assert job1 is not None
        assert job2 is None


# ============================================================================
# MemoryQueue Status Update Tests
# ============================================================================


class TestMemoryQueueStatusUpdate:
    """Tests for job status update functionality."""

    @pytest.mark.asyncio
    async def test_update_status_running(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test updating job status to running sets started_at."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )

        result = await memory_queue.update_status(job_id, JobStatus.RUNNING)

        assert result is True
        job = await memory_queue.get_job(job_id)
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    @pytest.mark.asyncio
    async def test_update_status_completed(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test updating job status to completed sets completed_at."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )
        await memory_queue.claim(robot_id="robot-001")

        result = await memory_queue.update_status(
            job_id,
            JobStatus.COMPLETED,
            result={"output": "success"},
        )

        assert result is True
        job = await memory_queue.get_job(job_id)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result == {"output": "success"}

    @pytest.mark.asyncio
    async def test_update_status_failed_with_error(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test updating job status to failed stores error message."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )

        result = await memory_queue.update_status(
            job_id,
            JobStatus.FAILED,
            error="Connection timeout",
        )

        assert result is True
        job = await memory_queue.get_job(job_id)
        assert job.status == JobStatus.FAILED
        assert job.error == "Connection timeout"

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, memory_queue: MemoryQueue) -> None:
        """Test update_status returns False for non-existent job."""
        result = await memory_queue.update_status(
            "non-existent-id",
            JobStatus.COMPLETED,
        )
        assert result is False


# ============================================================================
# MemoryQueue Visibility Timeout Tests
# ============================================================================


class TestMemoryQueueVisibilityTimeout:
    """Tests for visibility timeout and claim expiration."""

    @pytest.mark.asyncio
    async def test_extend_claim_success(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test extending claim updates claimed_at timestamp."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )
        job = await memory_queue.claim(robot_id="robot-001")
        original_claimed_at = job.claimed_at

        await asyncio.sleep(0.1)
        result = await memory_queue.extend_claim(job_id)

        assert result is True
        updated_job = await memory_queue.get_job(job_id)
        assert updated_job.claimed_at > original_claimed_at

    @pytest.mark.asyncio
    async def test_extend_claim_not_found(self, memory_queue: MemoryQueue) -> None:
        """Test extend_claim returns False for non-existent job."""
        result = await memory_queue.extend_claim("non-existent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_extend_claim_not_claimed(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test extend_claim returns False for unclaimed job."""
        job_id = await memory_queue.enqueue(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
        )

        result = await memory_queue.extend_claim(job_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_expired_claim_returned_to_queue(
        self, sample_workflow_json: dict
    ) -> None:
        """Test expired claims are returned to queue by cleanup task."""
        # Use short visibility timeout
        queue = MemoryQueue(visibility_timeout=1)
        await queue.start()

        try:
            job_id = await queue.enqueue(
                workflow_id="wf-001",
                workflow_json=sample_workflow_json,
            )

            # Claim the job
            job = await queue.claim(robot_id="robot-001")
            assert job is not None
            assert job.status == JobStatus.CLAIMED

            # Wait for visibility timeout + cleanup interval to expire
            # Cleanup runs every 5 seconds, so need to wait longer
            await asyncio.sleep(7)

            # Job should be back in queue
            reclaimed_job = await queue.claim(robot_id="robot-002")
            assert reclaimed_job is not None
            assert reclaimed_job.job_id == job_id
            assert reclaimed_job.robot_id == "robot-002"

        finally:
            await queue.stop()


# ============================================================================
# MemoryQueue Query Tests
# ============================================================================


class TestMemoryQueueQueries:
    """Tests for queue query methods."""

    @pytest.mark.asyncio
    async def test_get_jobs_by_status(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test getting jobs filtered by status."""
        # Create jobs with different statuses
        for i in range(3):
            await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
            )

        # Claim one job
        await memory_queue.claim(robot_id="robot-001")

        queued_jobs = await memory_queue.get_jobs_by_status(JobStatus.QUEUED)
        claimed_jobs = await memory_queue.get_jobs_by_status(JobStatus.CLAIMED)

        assert len(queued_jobs) == 2
        assert len(claimed_jobs) == 1

    @pytest.mark.asyncio
    async def test_get_jobs_by_robot(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test getting jobs assigned to a specific robot."""
        for i in range(3):
            await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
            )

        await memory_queue.claim(robot_id="robot-001")
        await memory_queue.claim(robot_id="robot-002")

        robot1_jobs = await memory_queue.get_jobs_by_robot("robot-001")
        robot2_jobs = await memory_queue.get_jobs_by_robot("robot-002")

        assert len(robot1_jobs) == 1
        assert len(robot2_jobs) == 1
        assert robot1_jobs[0].robot_id == "robot-001"

    @pytest.mark.asyncio
    async def test_get_queue_depth(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test getting queue depth."""
        for i in range(5):
            await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
                execution_mode="lan" if i % 2 == 0 else "internet",
            )

        total_depth = await memory_queue.get_queue_depth()
        lan_depth = await memory_queue.get_queue_depth(execution_mode="lan")
        internet_depth = await memory_queue.get_queue_depth(execution_mode="internet")

        assert total_depth == 5
        assert lan_depth == 3  # 0, 2, 4
        assert internet_depth == 2  # 1, 3

    @pytest.mark.asyncio
    async def test_get_jobs_by_status_limit(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test limit parameter on get_jobs_by_status."""
        for i in range(10):
            await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
            )

        jobs = await memory_queue.get_jobs_by_status(JobStatus.QUEUED, limit=5)
        assert len(jobs) == 5


# ============================================================================
# MemoryQueue Lifecycle Tests
# ============================================================================


class TestMemoryQueueLifecycle:
    """Tests for queue start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_stop(self, memory_queue: MemoryQueue) -> None:
        """Test starting and stopping queue."""
        assert memory_queue._running is False
        assert memory_queue._cleanup_task is None

        await memory_queue.start()

        assert memory_queue._running is True
        assert memory_queue._cleanup_task is not None

        await memory_queue.stop()

        assert memory_queue._running is False

    @pytest.mark.asyncio
    async def test_double_start(self, memory_queue: MemoryQueue) -> None:
        """Test starting queue twice is safe."""
        await memory_queue.start()
        task1 = memory_queue._cleanup_task

        await memory_queue.start()
        task2 = memory_queue._cleanup_task

        assert task1 is task2  # Same task, not recreated

        await memory_queue.stop()

    @pytest.mark.asyncio
    async def test_double_stop(self, memory_queue: MemoryQueue) -> None:
        """Test stopping queue twice is safe."""
        await memory_queue.start()
        await memory_queue.stop()
        await memory_queue.stop()  # Should not raise


# ============================================================================
# Singleton Tests
# ============================================================================


class TestMemoryQueueSingleton:
    """Tests for singleton pattern and module-level functions."""

    @pytest.mark.asyncio
    async def test_get_memory_queue_returns_same_instance(self) -> None:
        """Test get_memory_queue returns singleton."""
        # Reset global state
        await shutdown_memory_queue()

        queue1 = get_memory_queue()
        queue2 = get_memory_queue()

        assert queue1 is queue2

        await shutdown_memory_queue()

    @pytest.mark.asyncio
    async def test_initialize_memory_queue(self) -> None:
        """Test initialize_memory_queue starts the queue."""
        await shutdown_memory_queue()

        queue = await initialize_memory_queue()

        assert queue._running is True

        await shutdown_memory_queue()

    @pytest.mark.asyncio
    async def test_shutdown_memory_queue(self) -> None:
        """Test shutdown_memory_queue stops and clears singleton."""
        await shutdown_memory_queue()

        queue = await initialize_memory_queue()
        assert queue._running is True

        await shutdown_memory_queue()

        # Getting queue again should create new instance
        new_queue = get_memory_queue()
        assert new_queue is not queue
        assert new_queue._running is False

        await shutdown_memory_queue()


# ============================================================================
# Concurrency Tests
# ============================================================================


class TestMemoryQueueConcurrency:
    """Tests for concurrent access safety."""

    @pytest.mark.asyncio
    async def test_concurrent_enqueue(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test concurrent enqueue operations are safe."""

        async def enqueue_job(i: int) -> str:
            return await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
            )

        # Enqueue 100 jobs concurrently
        tasks = [enqueue_job(i) for i in range(100)]
        job_ids = await asyncio.gather(*tasks)

        # All job IDs should be unique
        assert len(set(job_ids)) == 100

        # All jobs should be retrievable
        for job_id in job_ids:
            job = await memory_queue.get_job(job_id)
            assert job is not None

    @pytest.mark.asyncio
    async def test_concurrent_claim(
        self, memory_queue: MemoryQueue, sample_workflow_json: dict
    ) -> None:
        """Test concurrent claim operations are safe."""
        # Enqueue 10 jobs
        for i in range(10):
            await memory_queue.enqueue(
                workflow_id=f"wf-{i:03d}",
                workflow_json=sample_workflow_json,
            )

        async def claim_job(robot_id: str) -> MemoryJob | None:
            return await memory_queue.claim(robot_id=robot_id)

        # 20 robots try to claim concurrently
        tasks = [claim_job(f"robot-{i:03d}") for i in range(20)]
        results = await asyncio.gather(*tasks)

        # Only 10 should succeed (one per job)
        claimed = [r for r in results if r is not None]
        assert len(claimed) == 10

        # Each job should be claimed by different robot
        robot_ids = {job.robot_id for job in claimed}
        assert len(robot_ids) == 10
