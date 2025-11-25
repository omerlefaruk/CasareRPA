"""
Unit tests for CasareRPA Orchestrator Dispatcher.
Tests JobDispatcher, RobotPool, and LoadBalancingStrategy.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from casare_rpa.orchestrator.models import (
    Job, JobStatus, JobPriority,
    Robot, RobotStatus,
    Workflow, WorkflowStatus
)
from casare_rpa.orchestrator.dispatcher import (
    LoadBalancingStrategy,
    RobotPool,
    JobDispatcher
)
from casare_rpa.orchestrator.job_queue import JobQueue


# ==================== FIXTURES ====================

@pytest.fixture
def sample_workflow():
    """Create a sample workflow."""
    return Workflow(
        id="wf-001",
        name="Test Workflow",
        description="A test workflow",
        status=WorkflowStatus.PUBLISHED,
        version="1.0.0"
    )


@pytest.fixture
def sample_job(sample_workflow):
    """Create a sample job."""
    return Job(
        id="job-001",
        workflow_id=sample_workflow.id,
        workflow_name=sample_workflow.name,
        robot_id="",
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL
    )


@pytest.fixture
def sample_robot():
    """Create a sample robot."""
    return Robot(
        id="robot-001",
        name="Test Robot 1",
        status=RobotStatus.ONLINE,
        current_jobs=0,
        max_concurrent_jobs=3,
        last_heartbeat=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def robot_factory():
    """Factory to create multiple robots."""
    def create_robot(
        id: str,
        name: str,
        status: RobotStatus = RobotStatus.ONLINE,
        current_jobs: int = 0,
        max_concurrent_jobs: int = 3,
        tags: list = None
    ):
        return Robot(
            id=id,
            name=name,
            status=status,
            current_jobs=current_jobs,
            max_concurrent_jobs=max_concurrent_jobs,
            tags=tags or [],
            last_heartbeat=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
    return create_robot


@pytest.fixture
def multiple_robots(robot_factory):
    """Create multiple robots with different states."""
    return [
        robot_factory("robot-1", "Robot 1", RobotStatus.ONLINE, 0, 3),
        robot_factory("robot-2", "Robot 2", RobotStatus.ONLINE, 1, 3),
        robot_factory("robot-3", "Robot 3", RobotStatus.ONLINE, 2, 3),
        robot_factory("robot-4", "Robot 4", RobotStatus.BUSY, 3, 3),
        robot_factory("robot-5", "Robot 5", RobotStatus.OFFLINE, 0, 3),
    ]


# ==================== ROBOT POOL TESTS ====================

class TestRobotPool:
    """Tests for RobotPool class."""

    def test_create_empty_pool(self):
        """Test creating an empty pool."""
        pool = RobotPool(name="test-pool")

        assert pool.name == "test-pool"
        assert len(pool.tags) == 0
        assert pool.max_concurrent_jobs is None
        assert pool.allowed_workflows is None
        assert len(pool.get_robots()) == 0

    def test_create_pool_with_tags(self):
        """Test creating a pool with tags."""
        pool = RobotPool(name="tagged-pool", tags=["production", "web"])

        assert "production" in pool.tags
        assert "web" in pool.tags

    def test_create_pool_with_limits(self):
        """Test creating a pool with limits."""
        pool = RobotPool(
            name="limited-pool",
            max_concurrent_jobs=10,
            allowed_workflows={"wf-1", "wf-2"}
        )

        assert pool.max_concurrent_jobs == 10
        assert pool.allowed_workflows == {"wf-1", "wf-2"}

    def test_add_robot_no_tags(self, sample_robot):
        """Test adding a robot to pool without tags."""
        pool = RobotPool(name="test-pool")

        result = pool.add_robot(sample_robot)

        assert result is True
        assert sample_robot.id in [r.id for r in pool.get_robots()]

    def test_add_robot_matching_tags(self, robot_factory):
        """Test adding robot that matches pool tags."""
        pool = RobotPool(name="prod-pool", tags=["production"])
        robot = robot_factory("r1", "Robot 1", tags=["production", "web"])

        result = pool.add_robot(robot)

        assert result is True
        assert len(pool.get_robots()) == 1

    def test_add_robot_not_matching_tags(self, robot_factory):
        """Test adding robot that doesn't match pool tags."""
        pool = RobotPool(name="prod-pool", tags=["production"])
        robot = robot_factory("r1", "Robot 1", tags=["development"])

        result = pool.add_robot(robot)

        assert result is False
        assert len(pool.get_robots()) == 0

    def test_add_robot_partial_tags(self, robot_factory):
        """Test adding robot with partial tag match fails."""
        pool = RobotPool(name="multi-tag", tags=["production", "web"])
        robot = robot_factory("r1", "Robot 1", tags=["production"])  # Missing "web"

        result = pool.add_robot(robot)

        assert result is False

    def test_remove_robot(self, sample_robot):
        """Test removing a robot from pool."""
        pool = RobotPool(name="test-pool")
        pool.add_robot(sample_robot)

        pool.remove_robot(sample_robot.id)

        assert len(pool.get_robots()) == 0

    def test_remove_nonexistent_robot(self):
        """Test removing non-existent robot is safe."""
        pool = RobotPool(name="test-pool")
        pool.remove_robot("nonexistent")  # Should not raise

    def test_get_available_robots(self, multiple_robots):
        """Test getting available robots from pool."""
        pool = RobotPool(name="test-pool")
        for robot in multiple_robots:
            pool.add_robot(robot)

        available = pool.get_available_robots()

        # Should only include ONLINE robots with capacity
        assert len(available) == 3  # Robots 1, 2, 3 (not BUSY or OFFLINE)
        for robot in available:
            assert robot.status == RobotStatus.ONLINE
            assert robot.current_jobs < robot.max_concurrent_jobs

    def test_get_current_job_count(self, multiple_robots):
        """Test getting current job count across pool."""
        pool = RobotPool(name="test-pool")
        for robot in multiple_robots:
            pool.add_robot(robot)

        job_count = pool.get_current_job_count()

        # 0 + 1 + 2 + 3 + 0 = 6
        assert job_count == 6

    def test_can_accept_job_unlimited(self, sample_robot):
        """Test pool without limit can always accept jobs."""
        pool = RobotPool(name="unlimited-pool")
        pool.add_robot(sample_robot)

        assert pool.can_accept_job() is True

    def test_can_accept_job_under_limit(self, robot_factory):
        """Test pool under limit can accept jobs."""
        pool = RobotPool(name="limited-pool", max_concurrent_jobs=5)
        robot = robot_factory("r1", "Robot 1", current_jobs=2)
        pool.add_robot(robot)

        assert pool.can_accept_job() is True

    def test_cannot_accept_job_at_limit(self, robot_factory):
        """Test pool at limit cannot accept jobs."""
        pool = RobotPool(name="limited-pool", max_concurrent_jobs=3)
        robot = robot_factory("r1", "Robot 1", current_jobs=3)
        pool.add_robot(robot)

        assert pool.can_accept_job() is False

    def test_is_workflow_allowed_no_restrictions(self):
        """Test workflow is allowed when no restrictions."""
        pool = RobotPool(name="test-pool")
        assert pool.is_workflow_allowed("any-workflow") is True

    def test_is_workflow_allowed(self):
        """Test workflow is allowed when in set."""
        pool = RobotPool(name="test-pool", allowed_workflows={"wf-1", "wf-2"})

        assert pool.is_workflow_allowed("wf-1") is True
        assert pool.is_workflow_allowed("wf-2") is True
        assert pool.is_workflow_allowed("wf-3") is False

    def test_utilization_empty_pool(self):
        """Test utilization of empty pool."""
        pool = RobotPool(name="empty-pool")
        assert pool.utilization == 0.0

    def test_utilization_calculation(self, robot_factory):
        """Test utilization calculation."""
        pool = RobotPool(name="test-pool")
        pool.add_robot(robot_factory("r1", "Robot 1", current_jobs=2, max_concurrent_jobs=4))
        pool.add_robot(robot_factory("r2", "Robot 2", current_jobs=3, max_concurrent_jobs=4))

        # 5 jobs / 8 capacity = 62.5%
        assert pool.utilization == 62.5

    def test_online_count(self, multiple_robots):
        """Test counting online robots."""
        pool = RobotPool(name="test-pool")
        for robot in multiple_robots:
            pool.add_robot(robot)

        # 3 ONLINE + 1 BUSY + 1 OFFLINE
        assert pool.online_count == 3


# ==================== JOB DISPATCHER TESTS ====================

class TestJobDispatcher:
    """Tests for JobDispatcher class."""

    @pytest.fixture
    def dispatcher(self):
        """Create a JobDispatcher instance."""
        return JobDispatcher(strategy=LoadBalancingStrategy.LEAST_LOADED)

    @pytest.fixture
    def dispatcher_with_robots(self, dispatcher, multiple_robots):
        """Create a dispatcher with registered robots."""
        for robot in multiple_robots:
            dispatcher.register_robot(robot)
        return dispatcher

    def test_create_dispatcher_with_strategy(self):
        """Test creating dispatcher with different strategies."""
        strategies = [
            LoadBalancingStrategy.ROUND_ROBIN,
            LoadBalancingStrategy.LEAST_LOADED,
            LoadBalancingStrategy.RANDOM,
            LoadBalancingStrategy.AFFINITY
        ]

        for strategy in strategies:
            dispatcher = JobDispatcher(strategy=strategy)
            assert dispatcher._strategy == strategy

    def test_register_robot(self, dispatcher, sample_robot):
        """Test registering a robot."""
        result = dispatcher.register_robot(sample_robot)

        assert result is True
        assert sample_robot.id in [r.id for r in dispatcher.get_all_robots()]

    def test_register_robot_to_pool(self, dispatcher, sample_robot):
        """Test registering robot to a specific pool."""
        dispatcher.create_pool("prod-pool")

        result = dispatcher.register_robot(sample_robot, pool_name="prod-pool")

        assert result is True
        pool = dispatcher.get_pool("prod-pool")
        assert sample_robot.id in [r.id for r in pool.get_robots()]

    def test_register_robot_to_nonexistent_pool(self, dispatcher, sample_robot):
        """Test registering robot to non-existent pool uses default."""
        result = dispatcher.register_robot(sample_robot, pool_name="nonexistent")

        assert result is True
        # Should be added to default pool
        default_pool = dispatcher.get_pool("default")
        assert sample_robot.id in [r.id for r in default_pool.get_robots()]

    def test_unregister_robot(self, dispatcher, sample_robot):
        """Test unregistering a robot."""
        dispatcher.register_robot(sample_robot)
        dispatcher.unregister_robot(sample_robot.id)

        assert sample_robot.id not in [r.id for r in dispatcher.get_all_robots()]

    def test_unregister_nonexistent_robot(self, dispatcher):
        """Test unregistering non-existent robot is safe."""
        dispatcher.unregister_robot("nonexistent")  # Should not raise

    def test_update_robot(self, dispatcher, sample_robot):
        """Test updating robot state."""
        dispatcher.register_robot(sample_robot)

        sample_robot.current_jobs = 2
        dispatcher.update_robot(sample_robot)

        robot = dispatcher.get_robot(sample_robot.id)
        assert robot.current_jobs == 2

    def test_update_robot_status_change_callback(self, dispatcher, robot_factory):
        """Test status change callback is called."""
        callback = Mock()
        dispatcher.set_callbacks(on_robot_status_change=callback)

        # Register initial robot
        initial_robot = robot_factory("r1", "Robot 1", status=RobotStatus.ONLINE)
        dispatcher.register_robot(initial_robot)

        # Create updated version with new status (needs to be a different object)
        updated_robot = robot_factory("r1", "Robot 1", status=RobotStatus.BUSY)
        dispatcher.update_robot(updated_robot)

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[1] == RobotStatus.ONLINE  # old status
        assert args[2] == RobotStatus.BUSY  # new status

    def test_update_robot_heartbeat(self, dispatcher, sample_robot):
        """Test updating robot heartbeat."""
        old_heartbeat = sample_robot.last_heartbeat
        dispatcher.register_robot(sample_robot)

        dispatcher.update_robot_heartbeat(sample_robot.id)

        robot = dispatcher.get_robot(sample_robot.id)
        assert robot.last_heartbeat >= old_heartbeat

    def test_get_robot(self, dispatcher, sample_robot):
        """Test getting robot by ID."""
        dispatcher.register_robot(sample_robot)

        robot = dispatcher.get_robot(sample_robot.id)

        assert robot is not None
        assert robot.id == sample_robot.id

    def test_get_nonexistent_robot(self, dispatcher):
        """Test getting non-existent robot returns None."""
        robot = dispatcher.get_robot("nonexistent")
        assert robot is None

    def test_get_all_robots(self, dispatcher_with_robots):
        """Test getting all robots."""
        robots = dispatcher_with_robots.get_all_robots()
        assert len(robots) == 5

    def test_get_available_robots(self, dispatcher_with_robots):
        """Test getting available robots."""
        available = dispatcher_with_robots.get_available_robots()

        # Only ONLINE with capacity
        assert len(available) == 3
        for robot in available:
            assert robot.is_available

    def test_get_robots_by_status(self, dispatcher_with_robots):
        """Test getting robots by status."""
        online = dispatcher_with_robots.get_robots_by_status(RobotStatus.ONLINE)
        busy = dispatcher_with_robots.get_robots_by_status(RobotStatus.BUSY)
        offline = dispatcher_with_robots.get_robots_by_status(RobotStatus.OFFLINE)

        assert len(online) == 3
        assert len(busy) == 1
        assert len(offline) == 1


# ==================== POOL MANAGEMENT TESTS ====================

class TestDispatcherPoolManagement:
    """Tests for dispatcher pool management."""

    @pytest.fixture
    def dispatcher(self):
        return JobDispatcher()

    def test_create_pool(self, dispatcher):
        """Test creating a pool."""
        pool = dispatcher.create_pool(
            name="test-pool",
            tags=["test"],
            max_concurrent_jobs=10
        )

        assert pool is not None
        assert pool.name == "test-pool"
        assert dispatcher.get_pool("test-pool") is not None

    def test_create_pool_adds_matching_robots(self, dispatcher, robot_factory):
        """Test creating pool adds matching existing robots."""
        robot = robot_factory("r1", "Robot 1", tags=["production"])
        dispatcher.register_robot(robot)

        pool = dispatcher.create_pool("prod-pool", tags=["production"])

        assert len(pool.get_robots()) == 1

    def test_delete_pool(self, dispatcher):
        """Test deleting a pool."""
        dispatcher.create_pool("to-delete")

        result = dispatcher.delete_pool("to-delete")

        assert result is True
        assert dispatcher.get_pool("to-delete") is None

    def test_cannot_delete_default_pool(self, dispatcher):
        """Test cannot delete default pool."""
        result = dispatcher.delete_pool("default")
        assert result is False

    def test_delete_nonexistent_pool(self, dispatcher):
        """Test deleting non-existent pool returns False."""
        result = dispatcher.delete_pool("nonexistent")
        assert result is False

    def test_get_pool(self, dispatcher):
        """Test getting a pool by name."""
        dispatcher.create_pool("my-pool")

        pool = dispatcher.get_pool("my-pool")
        assert pool is not None
        assert pool.name == "my-pool"

    def test_get_default_pool(self, dispatcher):
        """Test getting default pool."""
        pool = dispatcher.get_pool("default")
        assert pool is not None
        assert pool.name == "default"

    def test_get_all_pools(self, dispatcher):
        """Test getting all pools."""
        dispatcher.create_pool("pool-1")
        dispatcher.create_pool("pool-2")

        pools = dispatcher.get_all_pools()

        assert "default" in pools
        assert "pool-1" in pools
        assert "pool-2" in pools


# ==================== ROBOT SELECTION TESTS ====================

class TestRobotSelection:
    """Tests for robot selection strategies."""

    @pytest.fixture
    def dispatcher_with_robots(self, robot_factory):
        """Create dispatcher with robots for selection tests."""
        dispatcher = JobDispatcher(strategy=LoadBalancingStrategy.LEAST_LOADED)

        robots = [
            robot_factory("r1", "Robot 1", current_jobs=0, max_concurrent_jobs=3),
            robot_factory("r2", "Robot 2", current_jobs=1, max_concurrent_jobs=3),
            robot_factory("r3", "Robot 3", current_jobs=2, max_concurrent_jobs=3),
        ]

        for robot in robots:
            dispatcher.register_robot(robot)

        return dispatcher

    def test_select_robot_least_loaded(self, dispatcher_with_robots, sample_job):
        """Test least loaded strategy selects robot with lowest utilization."""
        robot = dispatcher_with_robots.select_robot(sample_job)

        assert robot is not None
        assert robot.id == "r1"  # Has 0 current jobs

    def test_select_robot_round_robin(self, robot_factory, sample_job):
        """Test round robin strategy rotates through robots."""
        dispatcher = JobDispatcher(strategy=LoadBalancingStrategy.ROUND_ROBIN)

        robots = [
            robot_factory("r1", "Robot 1"),
            robot_factory("r2", "Robot 2"),
            robot_factory("r3", "Robot 3"),
        ]

        for robot in robots:
            dispatcher.register_robot(robot)

        selected_ids = set()
        for _ in range(6):
            robot = dispatcher.select_robot(sample_job)
            if robot:
                selected_ids.add(robot.id)

        # Should have cycled through all robots
        assert len(selected_ids) == 3

    def test_select_robot_random(self, robot_factory, sample_job):
        """Test random strategy selects a robot."""
        dispatcher = JobDispatcher(strategy=LoadBalancingStrategy.RANDOM)

        robots = [
            robot_factory("r1", "Robot 1"),
            robot_factory("r2", "Robot 2"),
        ]

        for robot in robots:
            dispatcher.register_robot(robot)

        robot = dispatcher.select_robot(sample_job)

        assert robot is not None
        assert robot.id in ["r1", "r2"]

    def test_select_robot_affinity(self, robot_factory, sample_job):
        """Test affinity strategy prefers robots that ran workflow before."""
        dispatcher = JobDispatcher(strategy=LoadBalancingStrategy.AFFINITY)

        robots = [
            robot_factory("r1", "Robot 1"),
            robot_factory("r2", "Robot 2"),
        ]

        for robot in robots:
            dispatcher.register_robot(robot)

        # Record success for r2 with this workflow
        sample_job.robot_id = "r2"
        dispatcher.record_job_result(sample_job, success=True)
        dispatcher.record_job_result(sample_job, success=True)

        # Clear robot_id so selection is not forced
        sample_job.robot_id = None

        robot = dispatcher.select_robot(sample_job)

        # Should prefer r2 due to affinity
        assert robot is not None
        assert robot.id == "r2"

    def test_select_robot_with_specific_robot_id(self, dispatcher_with_robots, sample_job):
        """Test job with specific robot_id gets that robot."""
        sample_job.robot_id = "r2"

        robot = dispatcher_with_robots.select_robot(sample_job)

        assert robot is not None
        assert robot.id == "r2"

    def test_select_robot_specific_unavailable(self, dispatcher_with_robots, sample_job, robot_factory):
        """Test job with unavailable specific robot returns None."""
        # Add an offline robot
        offline_robot = robot_factory("r-offline", "Offline", status=RobotStatus.OFFLINE)
        dispatcher_with_robots.register_robot(offline_robot)

        sample_job.robot_id = "r-offline"

        robot = dispatcher_with_robots.select_robot(sample_job)

        assert robot is None

    def test_select_robot_from_pool(self, robot_factory, sample_job):
        """Test selecting robot from specific pool."""
        dispatcher = JobDispatcher()

        # Create robots with tags
        prod_robot = robot_factory("r-prod", "Prod Robot", tags=["production"])
        dev_robot = robot_factory("r-dev", "Dev Robot", tags=["development"])

        dispatcher.register_robot(prod_robot)
        dispatcher.register_robot(dev_robot)

        # Create pools
        dispatcher.create_pool("production", tags=["production"])
        dispatcher.create_pool("development", tags=["development"])

        # Select from production pool
        robot = dispatcher.select_robot(sample_job, pool_name="production")

        assert robot is not None
        assert robot.id == "r-prod"

    def test_select_robot_from_empty_pool(self, sample_job):
        """Test selecting from empty pool returns None."""
        dispatcher = JobDispatcher()
        dispatcher.create_pool("empty-pool")

        robot = dispatcher.select_robot(sample_job, pool_name="empty-pool")

        assert robot is None

    def test_select_robot_from_nonexistent_pool(self, sample_job):
        """Test selecting from non-existent pool returns None."""
        dispatcher = JobDispatcher()

        robot = dispatcher.select_robot(sample_job, pool_name="nonexistent")

        assert robot is None

    def test_select_robot_no_available_robots(self, robot_factory, sample_job):
        """Test selection when no robots are available."""
        dispatcher = JobDispatcher()

        # Only add busy/offline robots
        busy = robot_factory("r1", "Busy", status=RobotStatus.BUSY, current_jobs=3, max_concurrent_jobs=3)
        offline = robot_factory("r2", "Offline", status=RobotStatus.OFFLINE)

        dispatcher.register_robot(busy)
        dispatcher.register_robot(offline)

        robot = dispatcher.select_robot(sample_job)

        assert robot is None


# ==================== AFFINITY TRACKING TESTS ====================

class TestAffinityTracking:
    """Tests for job affinity tracking."""

    def test_record_successful_job(self, robot_factory, sample_job):
        """Test recording successful job increases affinity."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1")
        dispatcher.register_robot(robot)

        sample_job.robot_id = "r1"
        dispatcher.record_job_result(sample_job, success=True)

        affinity = dispatcher._affinity[sample_job.workflow_id]["r1"]
        assert affinity == 1

    def test_record_multiple_successes(self, robot_factory, sample_job):
        """Test multiple successes increase affinity."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1")
        dispatcher.register_robot(robot)

        sample_job.robot_id = "r1"
        for _ in range(5):
            dispatcher.record_job_result(sample_job, success=True)

        affinity = dispatcher._affinity[sample_job.workflow_id]["r1"]
        assert affinity == 5

    def test_record_failed_job_no_affinity(self, robot_factory, sample_job):
        """Test failed job doesn't increase affinity."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1")
        dispatcher.register_robot(robot)

        sample_job.robot_id = "r1"
        dispatcher.record_job_result(sample_job, success=False)

        affinity = dispatcher._affinity.get(sample_job.workflow_id, {}).get("r1", 0)
        assert affinity == 0

    def test_record_job_without_robot_id(self, sample_job):
        """Test recording job without robot_id is safe."""
        dispatcher = JobDispatcher()

        sample_job.robot_id = None
        dispatcher.record_job_result(sample_job, success=True)  # Should not raise


# ==================== DISPATCH LOOP TESTS ====================

class TestDispatchLoop:
    """Tests for dispatch loop functionality."""

    @pytest.fixture
    def job_queue(self, sample_job):
        """Create a job queue with a job."""
        queue = JobQueue()
        queue.enqueue(sample_job)
        return queue

    @pytest.mark.asyncio
    async def test_start_stop_dispatcher(self, robot_factory):
        """Test starting and stopping dispatcher."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1")
        dispatcher.register_robot(robot)

        queue = JobQueue()

        await dispatcher.start(queue)
        assert dispatcher._running is True
        assert dispatcher._dispatch_task is not None
        assert dispatcher._health_task is not None

        await dispatcher.stop()
        assert dispatcher._running is False

    @pytest.mark.asyncio
    async def test_dispatch_pending_jobs(self, robot_factory, sample_job):
        """Test dispatching pending jobs to robots."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1")
        dispatcher.register_robot(robot)

        queue = JobQueue()
        queue.enqueue(sample_job)

        # Dispatch callback
        dispatched_jobs = []

        async def on_dispatch(job, robot):
            dispatched_jobs.append((job.id, robot.id))

        dispatcher.set_callbacks(on_job_dispatched=on_dispatch)

        # Manually call dispatch
        await dispatcher._dispatch_pending_jobs(queue)

        assert len(dispatched_jobs) == 1
        assert dispatched_jobs[0][0] == sample_job.id

    @pytest.mark.asyncio
    async def test_dispatch_updates_robot_job_count(self, robot_factory, sample_job):
        """Test dispatching updates robot's job count."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1", current_jobs=0)
        dispatcher.register_robot(robot)

        queue = JobQueue()
        queue.enqueue(sample_job)

        await dispatcher._dispatch_pending_jobs(queue)

        assert robot.current_jobs == 1

    @pytest.mark.asyncio
    async def test_dispatch_with_sync_callback(self, robot_factory, sample_job):
        """Test dispatch works with sync callback."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1")
        dispatcher.register_robot(robot)

        queue = JobQueue()
        queue.enqueue(sample_job)

        # Sync callback
        callback = Mock()
        dispatcher.set_callbacks(on_job_dispatched=callback)

        await dispatcher._dispatch_pending_jobs(queue)

        callback.assert_called_once()


# ==================== HEALTH CHECK TESTS ====================

class TestHealthCheck:
    """Tests for robot health checking."""

    @pytest.mark.asyncio
    async def test_stale_robot_marked_offline(self, robot_factory):
        """Test stale robot is marked offline."""
        dispatcher = JobDispatcher(stale_robot_timeout_seconds=1)

        # Robot with old heartbeat
        robot = robot_factory("r1", "Robot 1")
        robot.last_heartbeat = datetime.utcnow() - timedelta(seconds=10)
        dispatcher.register_robot(robot)

        callback = Mock()
        dispatcher.set_callbacks(on_robot_status_change=callback)

        await dispatcher._check_robot_health()

        assert robot.status == RobotStatus.OFFLINE
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_healthy_robot_not_changed(self, robot_factory):
        """Test healthy robot status is not changed."""
        dispatcher = JobDispatcher(stale_robot_timeout_seconds=60)

        robot = robot_factory("r1", "Robot 1")
        robot.last_heartbeat = datetime.utcnow()
        dispatcher.register_robot(robot)

        callback = Mock()
        dispatcher.set_callbacks(on_robot_status_change=callback)

        await dispatcher._check_robot_health()

        assert robot.status == RobotStatus.ONLINE
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_offline_robot_not_checked(self, robot_factory):
        """Test already offline robot is not checked."""
        dispatcher = JobDispatcher(stale_robot_timeout_seconds=1)

        robot = robot_factory("r1", "Robot 1", status=RobotStatus.OFFLINE)
        robot.last_heartbeat = datetime.utcnow() - timedelta(hours=1)
        dispatcher.register_robot(robot)

        callback = Mock()
        dispatcher.set_callbacks(on_robot_status_change=callback)

        await dispatcher._check_robot_health()

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_string_heartbeat(self, robot_factory):
        """Test health check handles string heartbeat."""
        dispatcher = JobDispatcher(stale_robot_timeout_seconds=1)

        robot = robot_factory("r1", "Robot 1")
        robot.last_heartbeat = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
        dispatcher.register_robot(robot)

        await dispatcher._check_robot_health()

        assert robot.status == RobotStatus.OFFLINE


# ==================== STATISTICS TESTS ====================

class TestDispatcherStatistics:
    """Tests for dispatcher statistics."""

    def test_get_stats_empty(self):
        """Test getting stats with no robots."""
        dispatcher = JobDispatcher()
        stats = dispatcher.get_stats()

        assert stats["total_robots"] == 0
        assert stats["online"] == 0
        assert stats["utilization"] == 0

    def test_get_stats_with_robots(self, robot_factory):
        """Test getting stats with robots."""
        dispatcher = JobDispatcher()

        robots = [
            robot_factory("r1", "Robot 1", status=RobotStatus.ONLINE, current_jobs=1, max_concurrent_jobs=3),
            robot_factory("r2", "Robot 2", status=RobotStatus.BUSY, current_jobs=3, max_concurrent_jobs=3),
            robot_factory("r3", "Robot 3", status=RobotStatus.OFFLINE, current_jobs=0, max_concurrent_jobs=3),
            robot_factory("r4", "Robot 4", status=RobotStatus.ERROR, current_jobs=0, max_concurrent_jobs=3),
        ]

        for robot in robots:
            dispatcher.register_robot(robot)

        stats = dispatcher.get_stats()

        assert stats["total_robots"] == 4
        assert stats["online"] == 1
        assert stats["busy"] == 1
        assert stats["offline"] == 1
        assert stats["error"] == 1
        assert stats["total_capacity"] == 12
        assert stats["current_load"] == 4
        assert stats["utilization"] == pytest.approx(33.33, rel=0.1)

    def test_get_stats_includes_pools(self, robot_factory):
        """Test stats include pool information."""
        dispatcher = JobDispatcher()
        robot = robot_factory("r1", "Robot 1", tags=["production"])
        dispatcher.register_robot(robot)
        dispatcher.create_pool("production", tags=["production"])

        stats = dispatcher.get_stats()

        assert "pools" in stats
        assert "default" in stats["pools"]
        assert "production" in stats["pools"]
