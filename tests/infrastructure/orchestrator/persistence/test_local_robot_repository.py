"""Tests for LocalRobotRepository."""

import pytest
from pathlib import Path
import tempfile

from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
from casare_rpa.infrastructure.orchestrator.persistence import (
    LocalStorageRepository,
    LocalRobotRepository,
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
def robot_repository(storage):
    """Create LocalRobotRepository."""
    return LocalRobotRepository(storage)


@pytest.fixture
def sample_robot():
    """Create sample robot entity."""
    return Robot(
        id="robot-1",
        name="Test Robot",
        status=RobotStatus.ONLINE,
        environment="production",
        max_concurrent_jobs=3,
    )


@pytest.mark.asyncio
async def test_save_robot(robot_repository, sample_robot):
    """Test saving a robot."""
    await robot_repository.save(sample_robot)

    # Verify robot was saved
    retrieved = await robot_repository.get_by_id("robot-1")
    assert retrieved is not None
    assert retrieved.id == "robot-1"
    assert retrieved.name == "Test Robot"
    assert retrieved.status == RobotStatus.ONLINE


@pytest.mark.asyncio
async def test_get_by_id_not_found(robot_repository):
    """Test getting non-existent robot returns None."""
    result = await robot_repository.get_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(robot_repository):
    """Test getting all robots."""
    robot1 = Robot(
        id="robot-1", name="Robot 1", status=RobotStatus.ONLINE, environment="prod"
    )
    robot2 = Robot(
        id="robot-2", name="Robot 2", status=RobotStatus.OFFLINE, environment="dev"
    )

    await robot_repository.save(robot1)
    await robot_repository.save(robot2)

    all_robots = await robot_repository.get_all()
    assert len(all_robots) == 2
    assert {r.id for r in all_robots} == {"robot-1", "robot-2"}


@pytest.mark.asyncio
async def test_get_all_online(robot_repository):
    """Test getting only online robots."""
    robot1 = Robot(
        id="robot-1", name="Robot 1", status=RobotStatus.ONLINE, environment="prod"
    )
    robot2 = Robot(
        id="robot-2", name="Robot 2", status=RobotStatus.OFFLINE, environment="dev"
    )
    robot3 = Robot(
        id="robot-3", name="Robot 3", status=RobotStatus.ONLINE, environment="test"
    )

    await robot_repository.save(robot1)
    await robot_repository.save(robot2)
    await robot_repository.save(robot3)

    online_robots = await robot_repository.get_all_online()
    assert len(online_robots) == 2
    assert {r.id for r in online_robots} == {"robot-1", "robot-3"}


@pytest.mark.asyncio
async def test_get_by_environment(robot_repository):
    """Test getting robots by environment."""
    robot1 = Robot(
        id="robot-1", name="Robot 1", status=RobotStatus.ONLINE, environment="prod"
    )
    robot2 = Robot(
        id="robot-2", name="Robot 2", status=RobotStatus.OFFLINE, environment="dev"
    )
    robot3 = Robot(
        id="robot-3", name="Robot 3", status=RobotStatus.ONLINE, environment="prod"
    )

    await robot_repository.save(robot1)
    await robot_repository.save(robot2)
    await robot_repository.save(robot3)

    prod_robots = await robot_repository.get_by_environment("prod")
    assert len(prod_robots) == 2
    assert {r.id for r in prod_robots} == {"robot-1", "robot-3"}


@pytest.mark.asyncio
async def test_update_status(robot_repository, sample_robot):
    """Test updating robot status."""
    await robot_repository.save(sample_robot)

    # Update status
    await robot_repository.update_status("robot-1", RobotStatus.BUSY)

    # Verify status changed
    updated = await robot_repository.get_by_id("robot-1")
    assert updated.status == RobotStatus.BUSY


@pytest.mark.asyncio
async def test_update_robot(robot_repository, sample_robot):
    """Test updating robot properties."""
    await robot_repository.save(sample_robot)

    # Update robot
    sample_robot.max_concurrent_jobs = 5
    sample_robot.status = RobotStatus.BUSY
    await robot_repository.save(sample_robot)

    # Verify updates
    updated = await robot_repository.get_by_id("robot-1")
    assert updated.max_concurrent_jobs == 5
    assert updated.status == RobotStatus.BUSY


@pytest.mark.asyncio
async def test_delete_robot(robot_repository, sample_robot):
    """Test deleting a robot."""
    await robot_repository.save(sample_robot)

    # Verify robot exists
    assert await robot_repository.get_by_id("robot-1") is not None

    # Delete robot
    await robot_repository.delete("robot-1")

    # Verify robot is gone
    assert await robot_repository.get_by_id("robot-1") is None
