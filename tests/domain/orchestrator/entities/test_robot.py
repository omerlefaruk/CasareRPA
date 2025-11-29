"""Tests for Robot domain entity."""

import pytest
from datetime import datetime


class TestRobotEntity:
    """Test Robot entity behavior and invariants."""

    def test_robot_creation_with_required_fields(self):
        """Robot can be created with minimal required fields."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(id="robot1", name="Test Robot")

        assert robot.id == "robot1"
        assert robot.name == "Test Robot"
        assert robot.status == RobotStatus.OFFLINE  # Default
        assert robot.max_concurrent_jobs == 1  # Default
        assert robot.current_jobs == 0  # Default

    def test_robot_is_available_when_online_and_below_capacity(self):
        """Robot is available when online with capacity."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_jobs=2,
        )

        assert robot.is_available() is True

    def test_robot_is_unavailable_when_at_max_capacity(self):
        """Robot is unavailable when at max concurrent jobs."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_jobs=3,
        )

        assert robot.is_available() is False

    def test_robot_is_unavailable_when_busy_status(self):
        """Robot is unavailable when status is BUSY."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.BUSY,
            max_concurrent_jobs=3,
            current_jobs=1,
        )

        assert robot.is_available() is False

    def test_robot_is_unavailable_when_offline(self):
        """Robot is unavailable when offline."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.OFFLINE,
            max_concurrent_jobs=3,
            current_jobs=0,
        )

        assert robot.is_available() is False

    def test_robot_utilization_calculation(self):
        """Robot calculates utilization percentage correctly."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=4,
            current_jobs=3,
        )

        assert robot.utilization() == 75.0

    def test_robot_utilization_zero_when_no_capacity(self):
        """Robot utilization is 0 when max_concurrent_jobs is 0."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=0,
            current_jobs=0,
        )

        assert robot.utilization() == 0.0

    def test_robot_utilization_zero_when_idle(self):
        """Robot utilization is 0 when no jobs running."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=5,
            current_jobs=0,
        )

        assert robot.utilization() == 0.0

    def test_robot_can_assign_job_when_available(self):
        """Robot can accept job assignment when available."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_jobs=1,
        )

        robot.assign_job("job123")

        assert robot.current_jobs == 2

    def test_robot_cannot_assign_job_when_at_capacity(self):
        """Robot raises error when assigning job at capacity."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
        from casare_rpa.domain.orchestrator.errors import RobotAtCapacityError

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=2,
            current_jobs=2,
        )

        with pytest.raises(RobotAtCapacityError):
            robot.assign_job("job123")

    def test_robot_cannot_assign_job_when_offline(self):
        """Robot raises error when assigning job while offline."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
        from casare_rpa.domain.orchestrator.errors import RobotUnavailableError

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.OFFLINE,
            max_concurrent_jobs=3,
            current_jobs=0,
        )

        with pytest.raises(RobotUnavailableError):
            robot.assign_job("job123")

    def test_robot_complete_job_decrements_count(self):
        """Robot decrements current_jobs when job completes."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_jobs=2,
        )

        robot.complete_job("job123")

        assert robot.current_jobs == 1

    def test_robot_complete_job_cannot_go_negative(self):
        """Robot raises error when completing job with no jobs running."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
        from casare_rpa.domain.orchestrator.errors import InvalidRobotStateError

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_jobs=0,
        )

        with pytest.raises(InvalidRobotStateError):
            robot.complete_job("job123")
