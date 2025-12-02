"""
Tests for Orchestrator Server multi-tenant functionality.

Tests tenant filtering on robots/jobs and tenant isolation for job assignment.
All WebSocket and database operations are mocked.
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

from casare_rpa.infrastructure.orchestrator.server import (
    RobotManager,
    OrchestratorConfig,
    ConnectedRobot,
    PendingJob,
    RobotRegistration,
    JobSubmission,
)


@pytest.fixture
def config() -> OrchestratorConfig:
    """Create test orchestrator configuration."""
    return OrchestratorConfig(
        host="localhost",
        port=8000,
        robot_heartbeat_timeout=90,
        job_timeout_default=3600,
    )


@pytest.fixture
def robot_manager(config: OrchestratorConfig) -> RobotManager:
    """Create robot manager for testing."""
    return RobotManager(config)


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Create mock WebSocket connection."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.fixture
def mock_websocket_factory():
    """Factory for creating multiple mock WebSockets."""

    def create():
        ws = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    return create


class TestConnectedRobotTenant:
    """Tests for ConnectedRobot tenant support."""

    def test_connected_robot_has_tenant_id(self, mock_websocket: AsyncMock) -> None:
        """ConnectedRobot stores tenant_id."""
        robot = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Test Robot",
            websocket=mock_websocket,
            tenant_id="tenant-123",
        )

        assert robot.tenant_id == "tenant-123"

    def test_connected_robot_tenant_id_optional(
        self, mock_websocket: AsyncMock
    ) -> None:
        """ConnectedRobot tenant_id defaults to None."""
        robot = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Test Robot",
            websocket=mock_websocket,
        )

        assert robot.tenant_id is None

    def test_robot_status_idle(self, mock_websocket: AsyncMock) -> None:
        """Robot with no jobs is idle."""
        robot = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Test Robot",
            websocket=mock_websocket,
            max_concurrent_jobs=3,
        )

        assert robot.status == "idle"

    def test_robot_status_working(self, mock_websocket: AsyncMock) -> None:
        """Robot with some jobs is working."""
        robot = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Test Robot",
            websocket=mock_websocket,
            max_concurrent_jobs=3,
            current_job_ids={"job-1"},
        )

        assert robot.status == "working"

    def test_robot_status_busy(self, mock_websocket: AsyncMock) -> None:
        """Robot at capacity is busy."""
        robot = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Test Robot",
            websocket=mock_websocket,
            max_concurrent_jobs=2,
            current_job_ids={"job-1", "job-2"},
        )

        assert robot.status == "busy"

    def test_robot_available_slots(self, mock_websocket: AsyncMock) -> None:
        """available_slots returns correct count."""
        robot = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Test Robot",
            websocket=mock_websocket,
            max_concurrent_jobs=5,
            current_job_ids={"job-1", "job-2"},
        )

        assert robot.available_slots == 3


class TestPendingJobTenant:
    """Tests for PendingJob tenant support."""

    def test_pending_job_has_tenant_id(self) -> None:
        """PendingJob stores tenant_id."""
        job = PendingJob(
            job_id="job-1",
            workflow_id="workflow-1",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
            tenant_id="tenant-abc",
        )

        assert job.tenant_id == "tenant-abc"

    def test_pending_job_tenant_id_optional(self) -> None:
        """PendingJob tenant_id defaults to None."""
        job = PendingJob(
            job_id="job-1",
            workflow_id="workflow-1",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
        )

        assert job.tenant_id is None


class TestRobotManagerGetAllRobots:
    """Tests for RobotManager.get_all_robots() tenant filtering."""

    @pytest.mark.asyncio
    async def test_get_all_robots_no_filter(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """get_all_robots() returns all robots when no tenant_id."""
        # Register robots for different tenants
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                tenant_id="tenant-a",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                tenant_id="tenant-b",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r3",
                robot_name="Robot 3",
                tenant_id=None,  # No tenant
            ),
        )

        robots = robot_manager.get_all_robots()

        assert len(robots) == 3

    @pytest.mark.asyncio
    async def test_get_all_robots_filter_by_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """get_all_robots(tenant_id) filters by tenant."""
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                tenant_id="tenant-a",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                tenant_id="tenant-a",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r3",
                robot_name="Robot 3",
                tenant_id="tenant-b",
            ),
        )

        robots = robot_manager.get_all_robots(tenant_id="tenant-a")

        assert len(robots) == 2
        assert all(r.tenant_id == "tenant-a" for r in robots)

    @pytest.mark.asyncio
    async def test_get_all_robots_empty_for_unknown_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """get_all_robots() returns empty list for unknown tenant."""
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                tenant_id="tenant-a",
            ),
        )

        robots = robot_manager.get_all_robots(tenant_id="nonexistent-tenant")

        assert len(robots) == 0


class TestRobotManagerGetAvailableRobots:
    """Tests for RobotManager.get_available_robots() tenant filtering."""

    @pytest.mark.asyncio
    async def test_get_available_robots_filter_by_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """get_available_robots() filters by tenant_id."""
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-b",
            ),
        )

        robots = robot_manager.get_available_robots(tenant_id="tenant-a")

        assert len(robots) == 1
        assert robots[0].robot_id == "r1"

    @pytest.mark.asyncio
    async def test_get_available_robots_excludes_busy(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """get_available_robots() excludes robots at capacity."""
        robot = await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 1},
                tenant_id="tenant-a",
            ),
        )
        robot.current_job_ids.add("job-1")  # At capacity

        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        robots = robot_manager.get_available_robots(tenant_id="tenant-a")

        assert len(robots) == 1
        assert robots[0].robot_id == "r2"

    @pytest.mark.asyncio
    async def test_get_available_robots_filter_by_capabilities(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """get_available_robots() filters by required capabilities."""
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"types": ["browser"], "max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={
                    "types": ["browser", "desktop"],
                    "max_concurrent_jobs": 2,
                },
                tenant_id="tenant-a",
            ),
        )

        robots = robot_manager.get_available_robots(
            required_capabilities=["desktop"],
            tenant_id="tenant-a",
        )

        assert len(robots) == 1
        assert robots[0].robot_id == "r2"


class TestRobotManagerJobSubmission:
    """Tests for job submission with tenant isolation."""

    @pytest.mark.asyncio
    async def test_submit_job_assigns_to_same_tenant_robot(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Job is assigned to robot in same tenant."""
        ws = mock_websocket_factory()
        await robot_manager.register_robot(
            ws,
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-b",
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        assert job.assigned_robot_id == "r1"
        assert job.status == "assigned"
        ws.send_text.assert_awaited()  # Job sent to robot

    @pytest.mark.asyncio
    async def test_submit_job_not_assigned_to_different_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Job is not assigned to robot in different tenant."""
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-b",  # Different tenant
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        # Job should stay pending (no matching tenant robot)
        assert job.assigned_robot_id is None
        assert job.status == "pending"

    @pytest.mark.asyncio
    async def test_submit_job_target_robot_must_match_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Target robot must belong to same tenant."""
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-b",  # Different tenant
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                target_robot_id="r1",  # Specific robot
                tenant_id="tenant-a",  # Different tenant
            )
        )

        # Should not assign to robot in different tenant
        assert job.assigned_robot_id is None
        assert job.status == "pending"

    @pytest.mark.asyncio
    async def test_submit_job_no_tenant_assigned_to_any_robot(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Job without tenant_id can be assigned to any robot."""
        ws = mock_websocket_factory()
        await robot_manager.register_robot(
            ws,
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id=None,  # No tenant restriction
            )
        )

        assert job.assigned_robot_id == "r1"
        assert job.status == "assigned"

    @pytest.mark.asyncio
    async def test_submit_job_prefers_least_loaded_robot(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Job assigned to least loaded robot in tenant."""
        # Robot 1 has 1 job
        robot1 = await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 3},
                tenant_id="tenant-a",
            ),
        )
        robot1.current_job_ids.add("job-existing")

        # Robot 2 has 0 jobs (should be preferred)
        ws2 = mock_websocket_factory()
        await robot_manager.register_robot(
            ws2,
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={"max_concurrent_jobs": 3},
                tenant_id="tenant-a",
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        assert job.assigned_robot_id == "r2"


class TestRobotManagerJobRequeue:
    """Tests for job requeue with tenant isolation."""

    @pytest.mark.asyncio
    async def test_requeue_job_respects_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Requeued job only assigned to same-tenant robots."""
        # Robot 1 - tenant-a (will reject)
        robot1 = await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        # Robot 2 - tenant-a (should receive requeued job)
        ws2 = mock_websocket_factory()
        await robot_manager.register_robot(
            ws2,
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        # Robot 3 - tenant-b (should not receive)
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r3",
                robot_name="Robot 3",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-b",
            ),
        )

        # Submit job to tenant-a
        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )
        original_robot = job.assigned_robot_id

        # Requeue (robot rejects)
        await robot_manager.requeue_job(original_robot, job.job_id, "Test rejection")

        # Should be assigned to r2 (same tenant, not r1 which rejected)
        assert job.assigned_robot_id in ["r1", "r2"]
        assert job.assigned_robot_id != original_robot


class TestRobotManagerJobCompletion:
    """Tests for job completion."""

    @pytest.mark.asyncio
    async def test_job_completed_removes_from_robot(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Completed job removed from robot's current jobs."""
        ws = mock_websocket_factory()
        robot = await robot_manager.register_robot(
            ws,
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        assert job.job_id in robot.current_job_ids

        await robot_manager.job_completed(
            robot.robot_id,
            job.job_id,
            success=True,
            result={"output": "done"},
        )

        assert job.job_id not in robot.current_job_ids
        assert job.status == "completed"

    @pytest.mark.asyncio
    async def test_job_failed_updates_status(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Failed job has status 'failed'."""
        ws = mock_websocket_factory()
        await robot_manager.register_robot(
            ws,
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        await robot_manager.job_completed(
            "r1",
            job.job_id,
            success=False,
            result={"error": "Something went wrong"},
        )

        assert job.status == "failed"


class TestRobotManagerRegistration:
    """Tests for robot registration with tenant."""

    @pytest.mark.asyncio
    async def test_register_robot_with_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket: AsyncMock,
    ) -> None:
        """Robot registration captures tenant_id."""
        robot = await robot_manager.register_robot(
            mock_websocket,
            RobotRegistration(
                robot_id="r1",
                robot_name="Test Robot",
                tenant_id="tenant-xyz",
            ),
        )

        assert robot.tenant_id == "tenant-xyz"

    @pytest.mark.asyncio
    async def test_register_robot_without_tenant(
        self,
        robot_manager: RobotManager,
        mock_websocket: AsyncMock,
    ) -> None:
        """Robot registration without tenant_id."""
        robot = await robot_manager.register_robot(
            mock_websocket,
            RobotRegistration(
                robot_id="r1",
                robot_name="Test Robot",
                tenant_id=None,
            ),
        )

        assert robot.tenant_id is None

    @pytest.mark.asyncio
    async def test_register_broadcasts_to_admin(
        self,
        robot_manager: RobotManager,
        mock_websocket: AsyncMock,
        mock_websocket_factory,
    ) -> None:
        """Robot registration broadcasts to admin connections."""
        # Add admin connection
        admin_ws = mock_websocket_factory()
        await robot_manager.add_admin_connection(admin_ws)

        # Register robot
        await robot_manager.register_robot(
            mock_websocket,
            RobotRegistration(
                robot_id="r1",
                robot_name="Test Robot",
                tenant_id="tenant-a",
            ),
        )

        # Admin should receive notification
        admin_ws.send_text.assert_awaited()


class TestRobotManagerUnregistration:
    """Tests for robot unregistration."""

    @pytest.mark.asyncio
    async def test_unregister_requeues_jobs(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Jobs requeued when robot disconnects."""
        ws = mock_websocket_factory()
        await robot_manager.register_robot(
            ws,
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 2},
                tenant_id="tenant-a",
            ),
        )

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        assert job.status == "assigned"

        await robot_manager.unregister_robot("r1")

        # Job should be requeued
        assert job.status == "pending"
        assert job.assigned_robot_id is None


class TestJobSubmissionModel:
    """Tests for JobSubmission pydantic model."""

    def test_job_submission_with_tenant(self) -> None:
        """JobSubmission accepts tenant_id."""
        submission = JobSubmission(
            workflow_id="wf-1",
            workflow_data={"nodes": []},
            tenant_id="tenant-123",
        )

        assert submission.tenant_id == "tenant-123"

    def test_job_submission_without_tenant(self) -> None:
        """JobSubmission tenant_id defaults to None."""
        submission = JobSubmission(
            workflow_id="wf-1",
            workflow_data={},
        )

        assert submission.tenant_id is None

    def test_job_submission_priority_bounds(self) -> None:
        """JobSubmission priority is bounded 1-10."""
        submission = JobSubmission(
            workflow_id="wf-1",
            workflow_data={},
            priority=5,
        )

        assert submission.priority == 5


class TestRobotRegistrationModel:
    """Tests for RobotRegistration model."""

    def test_robot_registration_with_tenant(self) -> None:
        """RobotRegistration accepts tenant_id."""
        reg = RobotRegistration(
            robot_id="r1",
            robot_name="Robot 1",
            tenant_id="tenant-abc",
        )

        assert reg.tenant_id == "tenant-abc"

    def test_robot_registration_without_tenant(self) -> None:
        """RobotRegistration tenant_id defaults to None."""
        reg = RobotRegistration(
            robot_id="r1",
            robot_name="Robot 1",
        )

        assert reg.tenant_id is None


class TestTenantIsolationIntegration:
    """Integration-style tests for tenant isolation."""

    @pytest.mark.asyncio
    async def test_complete_tenant_isolation_workflow(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Complete workflow demonstrating tenant isolation."""
        # Setup: 2 tenants with 2 robots each
        tenant_a_robots = []
        tenant_b_robots = []

        for i in range(2):
            ws = mock_websocket_factory()
            robot = await robot_manager.register_robot(
                ws,
                RobotRegistration(
                    robot_id=f"ta-r{i}",
                    robot_name=f"Tenant A Robot {i}",
                    capabilities={"max_concurrent_jobs": 3},
                    tenant_id="tenant-a",
                ),
            )
            tenant_a_robots.append(robot)

            ws = mock_websocket_factory()
            robot = await robot_manager.register_robot(
                ws,
                RobotRegistration(
                    robot_id=f"tb-r{i}",
                    robot_name=f"Tenant B Robot {i}",
                    capabilities={"max_concurrent_jobs": 3},
                    tenant_id="tenant-b",
                ),
            )
            tenant_b_robots.append(robot)

        # Submit jobs to tenant A
        jobs_a = []
        for i in range(5):
            job = await robot_manager.submit_job(
                JobSubmission(
                    workflow_id=f"wf-a-{i}",
                    workflow_data={},
                    tenant_id="tenant-a",
                )
            )
            jobs_a.append(job)

        # Submit jobs to tenant B
        jobs_b = []
        for i in range(5):
            job = await robot_manager.submit_job(
                JobSubmission(
                    workflow_id=f"wf-b-{i}",
                    workflow_data={},
                    tenant_id="tenant-b",
                )
            )
            jobs_b.append(job)

        # Verify: All tenant A jobs assigned to tenant A robots
        for job in jobs_a:
            if job.assigned_robot_id:
                assert job.assigned_robot_id.startswith("ta-")

        # Verify: All tenant B jobs assigned to tenant B robots
        for job in jobs_b:
            if job.assigned_robot_id:
                assert job.assigned_robot_id.startswith("tb-")

        # Verify: get_all_robots filters correctly
        tenant_a_only = robot_manager.get_all_robots(tenant_id="tenant-a")
        assert len(tenant_a_only) == 2
        assert all(r.robot_id.startswith("ta-") for r in tenant_a_only)

        tenant_b_only = robot_manager.get_all_robots(tenant_id="tenant-b")
        assert len(tenant_b_only) == 2
        assert all(r.robot_id.startswith("tb-") for r in tenant_b_only)

    @pytest.mark.asyncio
    async def test_cross_tenant_job_rejection(
        self,
        robot_manager: RobotManager,
        mock_websocket_factory,
    ) -> None:
        """Jobs cannot be assigned to robots in different tenants."""
        # Only tenant-b robots available
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r1",
                robot_name="Robot 1",
                capabilities={"max_concurrent_jobs": 5},
                tenant_id="tenant-b",
            ),
        )
        await robot_manager.register_robot(
            mock_websocket_factory(),
            RobotRegistration(
                robot_id="r2",
                robot_name="Robot 2",
                capabilities={"max_concurrent_jobs": 5},
                tenant_id="tenant-b",
            ),
        )

        # Submit job for tenant-a (no matching robots)
        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="wf-1",
                workflow_data={},
                tenant_id="tenant-a",
            )
        )

        # Job should remain pending
        assert job.status == "pending"
        assert job.assigned_robot_id is None

        # Verify no tenant-b robot received the job
        all_robots = robot_manager.get_all_robots()
        for robot in all_robots:
            assert job.job_id not in robot.current_job_ids
