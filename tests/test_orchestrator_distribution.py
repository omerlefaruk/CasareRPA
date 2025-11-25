"""Tests for orchestrator workflow distribution system."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from casare_rpa.orchestrator.distribution import (
    DistributionStrategy,
    DistributionRule,
    DistributionResult,
    RobotSelector,
    WorkflowDistributor,
    JobRouter,
)
from casare_rpa.orchestrator.models import Robot, RobotStatus, Job, JobStatus, JobPriority


@pytest.fixture
def sample_robots():
    """Create sample robots for testing."""
    return [
        Robot(
            id="r1", name="Robot 1", status=RobotStatus.ONLINE,
            environment="production", max_concurrent_jobs=2, current_jobs=0,
            tags=["web", "desktop"], metrics={"cpu_percent": 30.0},
        ),
        Robot(
            id="r2", name="Robot 2", status=RobotStatus.ONLINE,
            environment="production", max_concurrent_jobs=2, current_jobs=1,
            tags=["web"], metrics={"cpu_percent": 50.0},
        ),
        Robot(
            id="r3", name="Robot 3", status=RobotStatus.ONLINE,
            environment="staging", max_concurrent_jobs=3, current_jobs=0,
            tags=["desktop", "testing"], metrics={"cpu_percent": 20.0},
        ),
        Robot(
            id="r4", name="Robot 4", status=RobotStatus.OFFLINE,
            environment="production", max_concurrent_jobs=2, current_jobs=0,
            tags=["web"],
        ),
    ]


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    job = Job(
        id="job-001",
        workflow_id="wf-001",
        workflow_name="Test Workflow",
        workflow_json="{}",
        robot_id="",
        priority=JobPriority.NORMAL,
        status=JobStatus.PENDING,
    )
    job.environment = "production"  # Add environment as attribute for distribution
    return job


class TestDistributionStrategy:
    """Tests for DistributionStrategy enum."""

    def test_all_strategies_exist(self):
        """Verify all expected strategies exist."""
        expected = ["ROUND_ROBIN", "LEAST_LOADED", "RANDOM", "CAPABILITY_MATCH", "AFFINITY"]
        for strategy in expected:
            assert hasattr(DistributionStrategy, strategy)


class TestDistributionRule:
    """Tests for DistributionRule dataclass."""

    def test_rule_creation(self):
        """Test creating a distribution rule."""
        rule = DistributionRule(
            name="production-web",
            workflow_pattern="*web*",
            required_tags=["web"],
            preferred_robots=["r1", "r2"],
            excluded_robots=["r4"],
            environment="production",
            strategy=DistributionStrategy.LEAST_LOADED,
            priority_boost=1,
        )

        assert rule.name == "production-web"
        assert rule.workflow_pattern == "*web*"
        assert rule.required_tags == ["web"]
        assert rule.preferred_robots == ["r1", "r2"]
        assert rule.excluded_robots == ["r4"]
        assert rule.environment == "production"
        assert rule.strategy == DistributionStrategy.LEAST_LOADED
        assert rule.priority_boost == 1

    def test_rule_defaults(self):
        """Test rule with default values."""
        rule = DistributionRule(name="default")

        assert rule.workflow_pattern == "*"
        assert rule.required_tags == []
        assert rule.preferred_robots == []
        assert rule.excluded_robots == []
        assert rule.environment is None
        assert rule.strategy == DistributionStrategy.LEAST_LOADED


class TestDistributionResult:
    """Tests for DistributionResult dataclass."""

    def test_successful_result(self):
        """Test successful distribution result."""
        result = DistributionResult(
            success=True,
            job_id="j1",
            robot_id="r1",
            message="Job accepted",
            retry_count=0,
            attempted_robots=["r1"],
        )

        assert result.success is True
        assert result.robot_id == "r1"
        assert result.retry_count == 0

    def test_failed_result(self):
        """Test failed distribution result."""
        result = DistributionResult(
            success=False,
            job_id="j1",
            message="No available robots",
            retry_count=3,
            attempted_robots=["r1", "r2", "r3"],
        )

        assert result.success is False
        assert result.robot_id is None
        assert result.retry_count == 3
        assert len(result.attempted_robots) == 3


class TestRobotSelector:
    """Tests for RobotSelector class."""

    def test_selector_initialization(self):
        """Test selector initialization."""
        selector = RobotSelector()
        assert selector._last_selected == {}
        assert selector._robot_affinity == {}

    def test_select_no_robots(self, sample_job):
        """Test selection with no robots."""
        selector = RobotSelector()
        result = selector.select(sample_job, [])
        assert result is None

    def test_select_filters_offline(self, sample_job, sample_robots):
        """Test that offline robots are filtered."""
        selector = RobotSelector()
        result = selector.select(sample_job, sample_robots)

        assert result is not None
        assert result.status == RobotStatus.ONLINE

    def test_select_filters_by_environment(self, sample_robots):
        """Test filtering by environment."""
        selector = RobotSelector()

        job = Job(
            id="j1", workflow_id="wf1", workflow_name="Test",
            workflow_json="{}", robot_id="",
        )
        job.environment = "staging"

        result = selector.select(job, sample_robots)

        assert result is not None
        assert result.environment == "staging"
        assert result.id == "r3"

    def test_select_filters_by_required_tags(self, sample_job, sample_robots):
        """Test filtering by required tags."""
        selector = RobotSelector()

        result = selector.select(
            sample_job,
            sample_robots,
            required_tags=["desktop"],
        )

        assert result is not None
        assert "desktop" in result.tags

    def test_select_excludes_robots(self, sample_job, sample_robots):
        """Test excluding specific robots."""
        selector = RobotSelector()

        # Exclude r1 (which would normally be selected as least loaded)
        result = selector.select(
            sample_job,
            sample_robots,
            excluded_robots=["r1"],
        )

        assert result is not None
        assert result.id != "r1"

    def test_select_prefers_robots(self, sample_job, sample_robots):
        """Test preferring specific robots."""
        selector = RobotSelector()

        result = selector.select(
            sample_job,
            sample_robots,
            preferred_robots=["r2"],
        )

        assert result is not None
        assert result.id == "r2"

    def test_select_round_robin(self, sample_job, sample_robots):
        """Test round-robin selection."""
        selector = RobotSelector()
        online_robots = [r for r in sample_robots if r.status == RobotStatus.ONLINE and r.environment == "production"]

        selected_ids = []
        for _ in range(6):  # Multiple rounds
            result = selector.select(
                sample_job,
                online_robots,
                strategy=DistributionStrategy.ROUND_ROBIN,
            )
            if result:
                selected_ids.append(result.id)

        # Should rotate through available robots
        assert len(set(selected_ids)) > 1

    def test_select_least_loaded(self, sample_job, sample_robots):
        """Test least-loaded selection."""
        selector = RobotSelector()

        result = selector.select(
            sample_job,
            sample_robots,
            strategy=DistributionStrategy.LEAST_LOADED,
        )

        # r1 has 0 jobs, r2 has 1, so r1 should be selected
        assert result is not None
        assert result.id == "r1"

    def test_select_random(self, sample_job, sample_robots):
        """Test random selection."""
        selector = RobotSelector()
        online_robots = [r for r in sample_robots if r.status == RobotStatus.ONLINE and r.environment == "production"]

        selected_ids = set()
        for _ in range(20):  # Multiple selections
            result = selector.select(
                sample_job,
                online_robots,
                strategy=DistributionStrategy.RANDOM,
            )
            if result:
                selected_ids.add(result.id)

        # Should select different robots (probabilistic)
        assert len(selected_ids) >= 1

    def test_select_affinity(self, sample_robots):
        """Test affinity-based selection."""
        selector = RobotSelector()

        job1 = Job(
            id="j1", workflow_id="wf-specific", workflow_name="Test",
            workflow_json="{}", robot_id="",
        )
        job1.environment = "production"

        # First selection sets affinity
        result1 = selector.select(
            job1,
            sample_robots,
            strategy=DistributionStrategy.AFFINITY,
        )

        assert result1 is not None
        first_robot_id = result1.id

        # Same workflow should go to same robot
        result2 = selector.select(
            job1,
            sample_robots,
            strategy=DistributionStrategy.AFFINITY,
        )

        assert result2 is not None
        assert result2.id == first_robot_id

    def test_clear_affinity(self, sample_robots):
        """Test clearing affinity."""
        selector = RobotSelector()

        job = Job(
            id="j1", workflow_id="wf-1", workflow_name="Test",
            workflow_json="{}", robot_id="",
        )
        job.environment = "production"

        selector.select(job, sample_robots, strategy=DistributionStrategy.AFFINITY)
        assert "wf-1" in selector._robot_affinity

        selector.clear_affinity("wf-1")
        assert "wf-1" not in selector._robot_affinity

    def test_clear_all_affinity(self, sample_robots):
        """Test clearing all affinity."""
        selector = RobotSelector()

        for i in range(3):
            job = Job(
                id=f"j{i}", workflow_id=f"wf-{i}", workflow_name="Test",
                workflow_json="{}", robot_id="",
            )
            job.environment = "production"
            selector.select(job, sample_robots, strategy=DistributionStrategy.AFFINITY)

        assert len(selector._robot_affinity) == 3

        selector.clear_all_affinity()
        assert len(selector._robot_affinity) == 0


class TestWorkflowDistributor:
    """Tests for WorkflowDistributor class."""

    def test_distributor_initialization(self):
        """Test distributor initialization."""
        distributor = WorkflowDistributor(
            max_retries=5,
            retry_delay=10.0,
            distribution_timeout=60.0,
        )

        assert distributor._max_retries == 5
        assert distributor._retry_delay == 10.0
        assert distributor._distribution_timeout == 60.0

    def test_add_rule(self):
        """Test adding distribution rules."""
        distributor = WorkflowDistributor()

        rule = DistributionRule(name="test-rule")
        distributor.add_rule(rule)

        assert len(distributor._rules) == 1
        assert distributor._rules[0].name == "test-rule"

    def test_remove_rule(self):
        """Test removing distribution rules."""
        distributor = WorkflowDistributor()

        rule1 = DistributionRule(name="rule1")
        rule2 = DistributionRule(name="rule2")
        distributor.add_rule(rule1)
        distributor.add_rule(rule2)

        assert len(distributor._rules) == 2

        result = distributor.remove_rule("rule1")
        assert result is True
        assert len(distributor._rules) == 1
        assert distributor._rules[0].name == "rule2"

        result = distributor.remove_rule("nonexistent")
        assert result is False

    def test_clear_rules(self):
        """Test clearing all rules."""
        distributor = WorkflowDistributor()

        for i in range(3):
            distributor.add_rule(DistributionRule(name=f"rule{i}"))

        assert len(distributor._rules) == 3

        distributor.clear_rules()
        assert len(distributor._rules) == 0

    def test_find_matching_rule(self, sample_job):
        """Test finding matching rule."""
        distributor = WorkflowDistributor()

        rule1 = DistributionRule(
            name="web-rule",
            workflow_pattern="*web*",
            environment="production",
        )
        rule2 = DistributionRule(
            name="default-rule",
            workflow_pattern="*",
        )

        distributor.add_rule(rule1)
        distributor.add_rule(rule2)

        # Should match web-rule for web workflow
        web_job = Job(
            id="j1", workflow_id="wf1", workflow_name="Web Scraping",
            workflow_json="{}", robot_id="",
        )
        web_job.environment = "production"
        match = distributor._find_matching_rule(web_job)
        assert match is not None
        assert match.name == "web-rule"

        # Should match default for other workflows
        other_job = Job(
            id="j2", workflow_id="wf2", workflow_name="Data Processing",
            workflow_json="{}", robot_id="",
        )
        other_job.environment = "staging"
        match = distributor._find_matching_rule(other_job)
        assert match is not None
        assert match.name == "default-rule"

    @pytest.mark.asyncio
    async def test_distribute_success(self, sample_job, sample_robots):
        """Test successful job distribution."""
        distributor = WorkflowDistributor()

        send_fn = AsyncMock(return_value={"accepted": True})
        distributor.set_send_job_function(send_fn)

        result = await distributor.distribute(sample_job, sample_robots)

        assert result.success is True
        assert result.robot_id is not None
        send_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_distribute_failure_no_robots(self, sample_job):
        """Test distribution failure with no robots."""
        distributor = WorkflowDistributor()

        send_fn = AsyncMock(return_value={"accepted": True})
        distributor.set_send_job_function(send_fn)

        result = await distributor.distribute(sample_job, [])

        assert result.success is False
        send_fn.assert_not_called()

    @pytest.mark.asyncio
    async def test_distribute_failure_no_send_function(self, sample_job, sample_robots):
        """Test distribution failure without send function."""
        distributor = WorkflowDistributor()

        result = await distributor.distribute(sample_job, sample_robots)

        assert result.success is False
        assert "No send function" in result.message

    @pytest.mark.asyncio
    async def test_distribute_with_retries(self, sample_job, sample_robots):
        """Test distribution with retries on rejection."""
        distributor = WorkflowDistributor(max_retries=2, retry_delay=0.01)

        call_count = [0]
        async def reject_then_accept(robot_id, job):
            call_count[0] += 1
            if call_count[0] < 2:
                return {"accepted": False, "reason": "Busy"}
            return {"accepted": True}

        distributor.set_send_job_function(reject_then_accept)

        result = await distributor.distribute(sample_job, sample_robots)

        assert result.success is True
        assert result.retry_count >= 1

    @pytest.mark.asyncio
    async def test_distribute_callbacks(self, sample_job, sample_robots):
        """Test distribution callbacks."""
        distributor = WorkflowDistributor()

        send_fn = AsyncMock(return_value={"accepted": True})
        distributor.set_send_job_function(send_fn)

        on_success = MagicMock()
        on_failure = MagicMock()
        distributor.set_callbacks(on_success=on_success, on_failure=on_failure)

        await distributor.distribute(sample_job, sample_robots)

        on_success.assert_called_once()
        on_failure.assert_not_called()

    @pytest.mark.asyncio
    async def test_distribute_batch(self, sample_robots):
        """Test batch distribution."""
        distributor = WorkflowDistributor()

        send_fn = AsyncMock(return_value={"accepted": True})
        distributor.set_send_job_function(send_fn)

        jobs = []
        for i in range(5):
            job = Job(
                id=f"j{i}", workflow_id=f"wf{i}", workflow_name=f"Workflow {i}",
                workflow_json="{}", robot_id="",
                priority=JobPriority(i % 3 + 1),
            )
            job.environment = "production"
            jobs.append(job)

        results = await distributor.distribute_batch(jobs, sample_robots)

        assert len(results) == 5
        successful = sum(1 for r in results if r.success)
        assert successful > 0

    def test_get_statistics(self):
        """Test getting distribution statistics."""
        distributor = WorkflowDistributor()

        # Add some history
        distributor._distribution_history = [
            DistributionResult(success=True, job_id=f"j{i}", retry_count=i % 3)
            for i in range(10)
        ]

        stats = distributor.get_statistics()

        assert stats["total_distributions"] == 10
        assert stats["successful"] == 10
        assert stats["failed"] == 0
        assert stats["success_rate"] == 1.0

    def test_get_recent_results(self):
        """Test getting recent results."""
        distributor = WorkflowDistributor()

        for i in range(20):
            distributor._distribution_history.append(
                DistributionResult(success=True, job_id=f"j{i}")
            )

        recent = distributor.get_recent_results(5)

        assert len(recent) == 5
        assert recent[-1].job_id == "j19"


class TestJobRouter:
    """Tests for JobRouter class."""

    def test_router_initialization(self):
        """Test router initialization."""
        router = JobRouter()
        assert router._routes == {}
        assert router._tag_routes == {}
        assert router._fallback_robots == []

    def test_add_route(self):
        """Test adding environment routes."""
        router = JobRouter()

        router.add_route("production", ["r1", "r2"])
        router.add_route("staging", ["r3"])

        assert router._routes["production"] == ["r1", "r2"]
        assert router._routes["staging"] == ["r3"]

    def test_add_tag_route(self):
        """Test adding tag routes."""
        router = JobRouter()

        router.add_tag_route("web", ["r1", "r2"])
        router.add_tag_route("desktop", ["r3"])

        assert router._tag_routes["web"] == ["r1", "r2"]
        assert router._tag_routes["desktop"] == ["r3"]

    def test_set_fallback_robots(self):
        """Test setting fallback robots."""
        router = JobRouter()

        router.set_fallback_robots(["r1", "r2"])

        assert router._fallback_robots == ["r1", "r2"]

    def test_get_eligible_robots_by_environment(self, sample_robots):
        """Test getting eligible robots by environment."""
        router = JobRouter()
        router.add_route("production", ["r1", "r2"])
        router.add_route("staging", ["r3"])

        job = Job(
            id="j1", workflow_id="wf1", workflow_name="Test",
            workflow_json="{}", robot_id="",
        )
        job.environment = "production"

        eligible = router.get_eligible_robots(job, sample_robots)

        assert len(eligible) == 2
        assert all(r.id in ["r1", "r2"] for r in eligible)

    def test_get_eligible_robots_no_matching_route(self, sample_robots):
        """Test getting eligible robots without matching route."""
        router = JobRouter()

        job = Job(
            id="j1", workflow_id="wf1", workflow_name="Test",
            workflow_json="{}", robot_id="",
        )
        job.environment = "unknown"

        # No routes, should return all robots
        eligible = router.get_eligible_robots(job, sample_robots)
        assert len(eligible) == len(sample_robots)

    def test_get_eligible_robots_with_fallback(self, sample_robots):
        """Test getting eligible robots with fallback."""
        router = JobRouter()
        router.set_fallback_robots(["r1"])

        job = Job(
            id="j1", workflow_id="wf1", workflow_name="Test",
            workflow_json="{}", robot_id="",
        )
        job.environment = "unknown"

        eligible = router.get_eligible_robots(job, sample_robots)

        assert len(eligible) == 1
        assert eligible[0].id == "r1"

    def test_clear_routes(self):
        """Test clearing all routes."""
        router = JobRouter()

        router.add_route("prod", ["r1"])
        router.add_tag_route("web", ["r2"])
        router.set_fallback_robots(["r3"])

        router.clear_routes()

        assert router._routes == {}
        assert router._tag_routes == {}
        assert router._fallback_robots == []
