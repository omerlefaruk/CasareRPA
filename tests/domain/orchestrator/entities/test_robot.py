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
        assert robot.current_jobs == 0  # Default (computed from current_job_ids)
        assert robot.current_job_ids == []  # Default

    def test_robot_is_available_when_online_and_below_capacity(self):
        """Robot is available when online with capacity."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_job_ids=["job1", "job2"],
        )

        assert robot.is_available is True
        assert robot.current_jobs == 2

    def test_robot_is_unavailable_when_at_max_capacity(self):
        """Robot is unavailable when at max concurrent jobs."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_job_ids=["job1", "job2", "job3"],
        )

        assert robot.is_available is False
        assert robot.current_jobs == 3

    def test_robot_is_unavailable_when_busy_status(self):
        """Robot is unavailable when status is BUSY."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.BUSY,
            max_concurrent_jobs=3,
            current_job_ids=["job1"],
        )

        assert robot.is_available is False

    def test_robot_is_unavailable_when_offline(self):
        """Robot is unavailable when offline."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.OFFLINE,
            max_concurrent_jobs=3,
            current_job_ids=[],
        )

        assert robot.is_available is False

    def test_robot_utilization_calculation(self):
        """Robot calculates utilization percentage correctly."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=4,
            current_job_ids=["job1", "job2", "job3"],
        )

        assert robot.utilization == 75.0

    def test_robot_utilization_zero_when_no_capacity(self):
        """Robot utilization is 0 when max_concurrent_jobs is 0."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=0,
            current_job_ids=[],
        )

        assert robot.utilization == 0.0

    def test_robot_utilization_zero_when_idle(self):
        """Robot utilization is 0 when no jobs running."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=5,
            current_job_ids=[],
        )

        assert robot.utilization == 0.0

    def test_robot_can_assign_job_when_available(self):
        """Robot can accept job assignment when available."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_job_ids=["existing_job"],
        )

        robot.assign_job("job123")

        assert robot.current_jobs == 2
        assert "job123" in robot.current_job_ids

    def test_robot_cannot_assign_job_when_at_capacity(self):
        """Robot raises error when assigning job at capacity."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
        from casare_rpa.domain.orchestrator.errors import RobotAtCapacityError

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=2,
            current_job_ids=["job1", "job2"],
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
            current_job_ids=[],
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
            current_job_ids=["job123", "job456"],
        )

        robot.complete_job("job123")

        assert robot.current_jobs == 1
        assert "job123" not in robot.current_job_ids
        assert "job456" in robot.current_job_ids

    def test_robot_complete_job_not_assigned_raises_error(self):
        """Robot raises error when completing job that's not assigned."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
        from casare_rpa.domain.orchestrator.errors import InvalidRobotStateError

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_job_ids=[],
        )

        with pytest.raises(InvalidRobotStateError):
            robot.complete_job("job123")


class TestRobotCapabilities:
    """Test Robot capability features."""

    def test_robot_has_capability(self):
        """Robot correctly reports having a capability."""
        from casare_rpa.domain.orchestrator.entities import (
            Robot,
            RobotStatus,
            RobotCapability,
        )

        robot = Robot(
            id="robot1",
            name="Browser Robot",
            status=RobotStatus.ONLINE,
            capabilities={RobotCapability.BROWSER, RobotCapability.DESKTOP},
        )

        assert robot.has_capability(RobotCapability.BROWSER) is True
        assert robot.has_capability(RobotCapability.GPU) is False

    def test_robot_has_all_capabilities(self):
        """Robot correctly checks multiple capabilities."""
        from casare_rpa.domain.orchestrator.entities import (
            Robot,
            RobotStatus,
            RobotCapability,
        )

        robot = Robot(
            id="robot1",
            name="Full Robot",
            status=RobotStatus.ONLINE,
            capabilities={
                RobotCapability.BROWSER,
                RobotCapability.DESKTOP,
                RobotCapability.GPU,
            },
        )

        assert (
            robot.has_all_capabilities(
                {RobotCapability.BROWSER, RobotCapability.DESKTOP}
            )
            is True
        )
        assert (
            robot.has_all_capabilities(
                {RobotCapability.BROWSER, RobotCapability.SECURE}
            )
            is False
        )


class TestRobotWorkflowAssignment:
    """Test Robot workflow assignment features."""

    def test_robot_assign_workflow(self):
        """Robot can be assigned to a workflow."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(id="robot1", name="Test", status=RobotStatus.ONLINE)

        robot.assign_workflow("wf-1")

        assert robot.is_assigned_to_workflow("wf-1") is True
        assert "wf-1" in robot.assigned_workflows

    def test_robot_unassign_workflow(self):
        """Robot can be unassigned from a workflow."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            assigned_workflows=["wf-1", "wf-2"],
        )

        robot.unassign_workflow("wf-1")

        assert robot.is_assigned_to_workflow("wf-1") is False
        assert robot.is_assigned_to_workflow("wf-2") is True

    def test_robot_assign_workflow_idempotent(self):
        """Assigning same workflow twice is idempotent."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus

        robot = Robot(id="robot1", name="Test", status=RobotStatus.ONLINE)

        robot.assign_workflow("wf-1")
        robot.assign_workflow("wf-1")  # Second assign

        assert robot.assigned_workflows.count("wf-1") == 1


class TestRobotDuplicateJobAssignment:
    """Test duplicate job assignment prevention."""

    def test_robot_cannot_assign_duplicate_job(self):
        """Robot raises error when assigning already assigned job."""
        from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
        from casare_rpa.domain.orchestrator.errors import DuplicateJobAssignmentError

        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_job_ids=["job123"],
        )

        with pytest.raises(DuplicateJobAssignmentError):
            robot.assign_job("job123")


class TestRobotSerialization:
    """Test Robot serialization/deserialization."""

    def test_robot_to_dict(self):
        """Robot serializes to dictionary correctly."""
        from casare_rpa.domain.orchestrator.entities import (
            Robot,
            RobotStatus,
            RobotCapability,
        )

        robot = Robot(
            id="robot1",
            name="Test Robot",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            capabilities={RobotCapability.BROWSER},
            assigned_workflows=["wf-1"],
            current_job_ids=["job1", "job2"],
        )

        data = robot.to_dict()

        assert data["id"] == "robot1"
        assert data["name"] == "Test Robot"
        assert data["status"] == "online"
        assert data["max_concurrent_jobs"] == 3
        assert data["current_jobs"] == 2  # Backward compatibility
        assert data["current_job_ids"] == ["job1", "job2"]
        assert "browser" in data["capabilities"]
        assert "wf-1" in data["assigned_workflows"]

    def test_robot_from_dict(self):
        """Robot deserializes from dictionary correctly."""
        from casare_rpa.domain.orchestrator.entities import (
            Robot,
            RobotStatus,
            RobotCapability,
        )

        data = {
            "id": "robot1",
            "name": "Test Robot",
            "status": "online",
            "max_concurrent_jobs": 3,
            "capabilities": ["browser", "desktop"],
            "assigned_workflows": ["wf-1"],
            "current_job_ids": ["job1"],
        }

        robot = Robot.from_dict(data)

        assert robot.id == "robot1"
        assert robot.status == RobotStatus.ONLINE
        assert RobotCapability.BROWSER in robot.capabilities
        assert robot.current_jobs == 1

    def test_robot_from_dict_backward_compatibility(self):
        """Robot handles legacy current_jobs field."""
        from casare_rpa.domain.orchestrator.entities import Robot

        # Legacy data with current_jobs count
        data = {
            "id": "robot1",
            "name": "Test Robot",
            "status": "online",
            "max_concurrent_jobs": 3,
            "current_jobs": 2,  # Old format
        }

        robot = Robot.from_dict(data)

        # Should create placeholder job IDs
        assert robot.current_jobs == 2
        assert len(robot.current_job_ids) == 2
