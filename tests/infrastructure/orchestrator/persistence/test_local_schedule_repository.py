"""Tests for LocalScheduleRepository."""

import pytest
from pathlib import Path
import tempfile

from casare_rpa.domain.orchestrator.entities import (
    Schedule,
    ScheduleFrequency,
    JobPriority,
)
from casare_rpa.infrastructure.orchestrator.persistence import (
    LocalStorageRepository,
    LocalScheduleRepository,
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
def schedule_repository(storage):
    """Create LocalScheduleRepository."""
    return LocalScheduleRepository(storage)


@pytest.fixture
def sample_schedule():
    """Create sample schedule entity."""
    return Schedule(
        id="sched-1",
        name="Daily Test",
        workflow_id="wf-1",
        workflow_name="Test Workflow",
        frequency=ScheduleFrequency.DAILY,
        enabled=True,
        priority=JobPriority.NORMAL,
    )


@pytest.mark.asyncio
async def test_save_schedule(schedule_repository, sample_schedule):
    """Test saving a schedule."""
    await schedule_repository.save(sample_schedule)

    # Verify schedule was saved
    retrieved = await schedule_repository.get_by_id("sched-1")
    assert retrieved is not None
    assert retrieved.id == "sched-1"
    assert retrieved.name == "Daily Test"
    assert retrieved.frequency == ScheduleFrequency.DAILY


@pytest.mark.asyncio
async def test_get_by_id_not_found(schedule_repository):
    """Test getting non-existent schedule returns None."""
    result = await schedule_repository.get_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(schedule_repository):
    """Test getting all schedules."""
    sched1 = Schedule(
        id="sched-1",
        name="Schedule 1",
        workflow_id="wf-1",
        frequency=ScheduleFrequency.DAILY,
        enabled=True,
    )
    sched2 = Schedule(
        id="sched-2",
        name="Schedule 2",
        workflow_id="wf-2",
        frequency=ScheduleFrequency.HOURLY,
        enabled=False,
    )

    await schedule_repository.save(sched1)
    await schedule_repository.save(sched2)

    all_schedules = await schedule_repository.get_all()
    assert len(all_schedules) == 2
    assert {s.id for s in all_schedules} == {"sched-1", "sched-2"}


@pytest.mark.asyncio
async def test_get_enabled(schedule_repository):
    """Test getting only enabled schedules."""
    sched1 = Schedule(
        id="sched-1",
        name="Schedule 1",
        workflow_id="wf-1",
        frequency=ScheduleFrequency.DAILY,
        enabled=True,
    )
    sched2 = Schedule(
        id="sched-2",
        name="Schedule 2",
        workflow_id="wf-2",
        frequency=ScheduleFrequency.HOURLY,
        enabled=False,
    )
    sched3 = Schedule(
        id="sched-3",
        name="Schedule 3",
        workflow_id="wf-3",
        frequency=ScheduleFrequency.WEEKLY,
        enabled=True,
    )

    await schedule_repository.save(sched1)
    await schedule_repository.save(sched2)
    await schedule_repository.save(sched3)

    enabled_schedules = await schedule_repository.get_enabled()
    assert len(enabled_schedules) == 2
    assert {s.id for s in enabled_schedules} == {"sched-1", "sched-3"}


@pytest.mark.asyncio
async def test_update_schedule(schedule_repository, sample_schedule):
    """Test updating a schedule."""
    await schedule_repository.save(sample_schedule)

    # Update schedule
    sample_schedule.enabled = False
    sample_schedule.run_count = 10
    await schedule_repository.save(sample_schedule)

    # Verify updates
    updated = await schedule_repository.get_by_id("sched-1")
    assert updated.enabled is False
    assert updated.run_count == 10


@pytest.mark.asyncio
async def test_delete_schedule(schedule_repository, sample_schedule):
    """Test deleting a schedule."""
    await schedule_repository.save(sample_schedule)

    # Verify schedule exists
    assert await schedule_repository.get_by_id("sched-1") is not None

    # Delete schedule
    await schedule_repository.delete("sched-1")

    # Verify schedule is gone
    assert await schedule_repository.get_by_id("sched-1") is None
