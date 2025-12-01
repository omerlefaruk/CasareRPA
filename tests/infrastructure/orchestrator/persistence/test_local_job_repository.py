"""Tests for LocalJobRepository."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from casare_rpa.domain.orchestrator.entities import Job, JobStatus, JobPriority
from casare_rpa.infrastructure.orchestrator.persistence import (
    LocalStorageRepository,
    LocalJobRepository,
)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create LocalStorageRepository with temp directory."""
    return LocalStorageRepository(storage_dir=temp_storage_dir)


@pytest.fixture
def job_repository(storage):
    """Create LocalJobRepository."""
    return LocalJobRepository(storage)


@pytest.fixture
def sample_job():
    """Create sample job entity."""
    return Job(
        id="job-1",
        workflow_id="wf-1",
        workflow_name="Test Workflow",
        robot_id="robot-1",
        robot_name="Test Robot",
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL,
        workflow_json='{"nodes": []}',
    )


@pytest.mark.asyncio
async def test_save_job(job_repository, sample_job):
    """Test saving a job."""
    await job_repository.save(sample_job)

    # Verify job was saved
    retrieved = await job_repository.get_by_id("job-1")
    assert retrieved is not None
    assert retrieved.id == "job-1"
    assert retrieved.workflow_name == "Test Workflow"
    assert retrieved.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_get_by_id_not_found(job_repository):
    """Test getting non-existent job returns None."""
    result = await job_repository.get_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(job_repository):
    """Test getting all jobs."""
    now = datetime.now(timezone.utc)
    job1 = Job(
        id="job-1",
        workflow_id="wf-1",
        workflow_name="Workflow 1",
        robot_id="robot-1",
        status=JobStatus.PENDING,
        created_at=now,
    )
    job2 = Job(
        id="job-2",
        workflow_id="wf-2",
        workflow_name="Workflow 2",
        robot_id="robot-2",
        status=JobStatus.RUNNING,
        created_at=now,
    )

    await job_repository.save(job1)
    await job_repository.save(job2)

    all_jobs = await job_repository.get_all()
    assert len(all_jobs) == 2
    assert {j.id for j in all_jobs} == {"job-1", "job-2"}


@pytest.mark.asyncio
async def test_get_by_status(job_repository):
    """Test getting jobs by status."""
    now = datetime.now(timezone.utc)
    job1 = Job(
        id="job-1",
        workflow_id="wf-1",
        workflow_name="Workflow 1",
        robot_id="robot-1",
        status=JobStatus.PENDING,
        created_at=now,
    )
    job2 = Job(
        id="job-2",
        workflow_id="wf-2",
        workflow_name="Workflow 2",
        robot_id="robot-2",
        status=JobStatus.RUNNING,
        created_at=now,
    )
    job3 = Job(
        id="job-3",
        workflow_id="wf-3",
        workflow_name="Workflow 3",
        robot_id="robot-3",
        status=JobStatus.PENDING,
        created_at=now,
    )

    await job_repository.save(job1)
    await job_repository.save(job2)
    await job_repository.save(job3)

    pending_jobs = await job_repository.get_by_status(JobStatus.PENDING)
    assert len(pending_jobs) == 2
    assert {j.id for j in pending_jobs} == {"job-1", "job-3"}


@pytest.mark.asyncio
async def test_get_by_robot(job_repository):
    """Test getting jobs by robot ID."""
    now = datetime.now(timezone.utc)
    job1 = Job(
        id="job-1",
        workflow_id="wf-1",
        workflow_name="Workflow 1",
        robot_id="robot-1",
        status=JobStatus.PENDING,
        created_at=now,
    )
    job2 = Job(
        id="job-2",
        workflow_id="wf-2",
        workflow_name="Workflow 2",
        robot_id="robot-2",
        status=JobStatus.RUNNING,
        created_at=now,
    )
    job3 = Job(
        id="job-3",
        workflow_id="wf-3",
        workflow_name="Workflow 3",
        robot_id="robot-1",
        status=JobStatus.COMPLETED,
        created_at=now,
    )

    await job_repository.save(job1)
    await job_repository.save(job2)
    await job_repository.save(job3)

    robot1_jobs = await job_repository.get_by_robot("robot-1")
    assert len(robot1_jobs) == 2
    assert {j.id for j in robot1_jobs} == {"job-1", "job-3"}


@pytest.mark.asyncio
async def test_get_by_workflow(job_repository):
    """Test getting jobs by workflow ID."""
    now = datetime.now(timezone.utc)
    job1 = Job(
        id="job-1",
        workflow_id="wf-1",
        workflow_name="Workflow 1",
        robot_id="robot-1",
        status=JobStatus.PENDING,
        created_at=now,
    )
    job2 = Job(
        id="job-2",
        workflow_id="wf-2",
        workflow_name="Workflow 2",
        robot_id="robot-2",
        status=JobStatus.RUNNING,
        created_at=now,
    )
    job3 = Job(
        id="job-3",
        workflow_id="wf-1",
        workflow_name="Workflow 1",
        robot_id="robot-3",
        status=JobStatus.COMPLETED,
        created_at=now,
    )

    await job_repository.save(job1)
    await job_repository.save(job2)
    await job_repository.save(job3)

    wf1_jobs = await job_repository.get_by_workflow("wf-1")
    assert len(wf1_jobs) == 2
    assert {j.id for j in wf1_jobs} == {"job-1", "job-3"}


@pytest.mark.asyncio
async def test_update_job(job_repository, sample_job):
    """Test updating an existing job."""
    await job_repository.save(sample_job)

    # Update job status
    sample_job.status = JobStatus.RUNNING
    sample_job.progress = 50
    await job_repository.save(sample_job)

    # Verify updates
    updated = await job_repository.get_by_id("job-1")
    assert updated.status == JobStatus.RUNNING
    assert updated.progress == 50


@pytest.mark.asyncio
async def test_delete_job(job_repository, sample_job):
    """Test deleting a job."""
    await job_repository.save(sample_job)

    # Verify job exists
    assert await job_repository.get_by_id("job-1") is not None

    # Delete job
    await job_repository.delete("job-1")

    # Verify job is gone
    assert await job_repository.get_by_id("job-1") is None
