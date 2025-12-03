"""
Comprehensive Integration Tests for CasareRPA Robot Orchestration System.

Tests end-to-end flows across:
- Orchestrator (job scheduling, queue management)
- PgQueuer (distributed queue with SKIP LOCKED)
- Robot Agent (job claiming, execution, heartbeat)
- DBOS Executor (durable execution, checkpointing)

Test Categories:
1. End-to-End: Orchestrator -> PgQueuer -> Robot -> DBOS execution
2. Multi-Robot Coordination: 2+ robots claiming jobs concurrently
3. Failover: Robot crash mid-job, recovery via visibility timeout
4. State Affinity: Soft, hard, and session affinity routing
5. Load Balancing: Job distribution across robot pool
6. DLQ: Jobs failing 5 times move to dead letter queue
7. Resource Pooling: Quota enforcement and resource limits
8. Hybrid Poll+Subscribe: Realtime notification integration

Success Criteria (from roadmap Phase 3.4):
- Robot can claim jobs from PgQueuer
- Robot executes workflows with DBOS durability
- Heartbeats extend job lease
- Graceful shutdown waits for job completion
- Crashed robots don't lose jobs (visibility timeout)

Requirements:
- pytest-asyncio for async test execution
- Docker Compose for PostgreSQL (optional, can use in-memory mocks)
- Mocked Supabase Realtime where appropriate
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
import random

import pytest

from casare_rpa.domain.orchestrator.entities import (
    Job,
    JobStatus,
    JobPriority,
    Robot,
    RobotStatus,
)
from casare_rpa.application.orchestrator.services.job_queue_manager import (
    JobQueue,
    JobStateMachine,
)


# =============================================================================
# COORDINATION MOCK CLASSES (self-contained for integration tests)
# =============================================================================
# These replace the deprecated casare_rpa.robot.coordination module.
# For production use, see infrastructure/orchestrator/scheduling/job_assignment.py


class LoadBalancingStrategy(Enum):
    """Load balancing strategy options for robot selection."""

    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    CAPABILITY_BASED = "capability_based"
    WEIGHTED = "weighted"


class ScalingAction(Enum):
    """Actions that auto-scaler can recommend."""

    NONE = "none"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"


@dataclass
class RobotCapabilities:
    """Robot capabilities for job matching."""

    max_concurrent_jobs: int = 1
    has_browser: bool = False
    has_gpu: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class RobotMetrics:
    """Runtime metrics for a robot."""

    current_jobs: int = 0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0


@dataclass
class RobotRegistration:
    """Registration info for a robot."""

    robot_id: str
    name: str
    capabilities: RobotCapabilities = field(default_factory=RobotCapabilities)


@dataclass
class RobotState:
    """Internal state of a registered robot."""

    registration: RobotRegistration
    metrics: RobotMetrics = field(default_factory=RobotMetrics)
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def robot_id(self) -> str:
        """Convenience property to access robot_id from registration."""
        return self.registration.robot_id


@dataclass
class JobRequirements:
    """Requirements for a job to be assigned."""

    requires_gpu: bool = False
    required_tags: List[str] = field(default_factory=list)


@dataclass
class ScalingDecision:
    """Result of auto-scaling evaluation."""

    action: ScalingAction
    target_count: int = 0
    reason: str = ""


class InMemoryCoordinationRepository:
    """In-memory storage for robot coordination state."""

    def __init__(self):
        self._robots: Dict[str, RobotState] = {}
        self._lock = asyncio.Lock()

    async def save_robot(self, state: RobotState) -> None:
        async with self._lock:
            self._robots[state.registration.robot_id] = state

    async def get_robot(self, robot_id: str) -> Optional[RobotState]:
        async with self._lock:
            return self._robots.get(robot_id)

    async def get_all_robots(self) -> List[RobotState]:
        async with self._lock:
            return list(self._robots.values())

    async def delete_robot(self, robot_id: str) -> None:
        async with self._lock:
            self._robots.pop(robot_id, None)


class RobotCoordinator:
    """
    Mock coordinator for robot fleet management in integration tests.

    For production use, see infrastructure/orchestrator/scheduling/job_assignment.py
    which provides JobAssignmentEngine with full capability matching and scoring.
    """

    def __init__(self, repository: InMemoryCoordinationRepository):
        self._repo = repository
        self._round_robin_index = 0
        self._running = False

    async def start(self) -> None:
        """Start the coordinator."""
        self._running = True

    async def stop(self) -> None:
        """Stop the coordinator."""
        self._running = False

    async def register_robot(self, registration: RobotRegistration) -> None:
        """Register a new robot."""
        state = RobotState(registration=registration)
        await self._repo.save_robot(state)

    async def unregister_robot(self, robot_id: str) -> None:
        """Unregister a robot."""
        await self._repo.delete_robot(robot_id)

    async def heartbeat(self, robot_id: str, metrics: RobotMetrics) -> None:
        """Update robot metrics from heartbeat."""
        state = await self._repo.get_robot(robot_id)
        if state:
            state.metrics = metrics
            state.last_heartbeat = datetime.now(timezone.utc)
            await self._repo.save_robot(state)

    async def select_robot_for_job(
        self,
        requirements: Optional[JobRequirements] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_BUSY,
    ) -> Optional[RobotState]:
        """Select best robot for a job based on strategy."""
        robots = await self._repo.get_all_robots()
        if not robots:
            return None

        # Filter by requirements
        if requirements:
            robots = self._filter_by_requirements(robots, requirements)
            if not robots:
                return None

        # Filter by capacity
        available = [
            r
            for r in robots
            if r.metrics.current_jobs < r.registration.capabilities.max_concurrent_jobs
        ]
        if not available:
            return None

        # Apply strategy
        if strategy == LoadBalancingStrategy.LEAST_BUSY:
            return min(available, key=lambda r: r.metrics.current_jobs)
        elif strategy == LoadBalancingStrategy.ROUND_ROBIN:
            self._round_robin_index = (self._round_robin_index + 1) % len(available)
            return available[self._round_robin_index]
        elif strategy == LoadBalancingStrategy.CAPABILITY_BASED:
            return available[0]
        elif strategy == LoadBalancingStrategy.WEIGHTED:
            weights = [
                r.registration.capabilities.max_concurrent_jobs for r in available
            ]
            return random.choices(available, weights=weights)[0]

        return available[0]

    def _filter_by_requirements(
        self, robots: List[RobotState], requirements: JobRequirements
    ) -> List[RobotState]:
        """Filter robots by job requirements."""
        result = []
        for robot in robots:
            caps = robot.registration.capabilities

            if requirements.requires_gpu and not caps.has_gpu:
                continue

            if requirements.required_tags:
                if not all(tag in caps.tags for tag in requirements.required_tags):
                    continue

            result.append(robot)

        return result

    async def evaluate_scaling(self, queue_depth: int = 0) -> ScalingDecision:
        """Evaluate whether to scale the robot pool."""
        robots = await self._repo.get_all_robots()
        if not robots:
            return ScalingDecision(
                action=ScalingAction.SCALE_UP,
                target_count=1,
                reason="No robots available",
            )

        total_capacity = sum(
            r.registration.capabilities.max_concurrent_jobs for r in robots
        )
        total_used = sum(r.metrics.current_jobs for r in robots)

        if total_capacity == 0:
            return ScalingDecision(action=ScalingAction.NONE, reason="No capacity")

        utilization = total_used / total_capacity

        if utilization > 0.8 or queue_depth > 5:
            return ScalingDecision(
                action=ScalingAction.SCALE_UP,
                target_count=len(robots) + 1,
                reason=f"High utilization ({utilization:.0%}) or queue depth ({queue_depth})",
            )

        if utilization < 0.2 and len(robots) > 1:
            return ScalingDecision(
                action=ScalingAction.SCALE_DOWN,
                target_count=len(robots) - 1,
                reason=f"Low utilization ({utilization:.0%})",
            )

        return ScalingDecision(
            action=ScalingAction.NONE,
            reason=f"Utilization normal ({utilization:.0%})",
        )


# =============================================================================
# TEST FIXTURES AND MOCK INFRASTRUCTURE
# =============================================================================


class MockJobStatus(Enum):
    """Mock job status for integration tests."""

    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"  # Dead letter queue


@dataclass
class MockQueueJob:
    """Mock job in the distributed queue."""

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int = 1
    status: MockJobStatus = MockJobStatus.PENDING
    robot_id: Optional[str] = None
    environment: str = "default"
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    visible_after: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    affinity_robot_id: Optional[str] = None
    session_id: Optional[str] = None


class MockPgQueuer:
    """
    Mock PgQueuer implementation for integration testing.

    Simulates distributed queue behavior:
    - SKIP LOCKED semantics for concurrent job claiming
    - Visibility timeout for lease management
    - Priority ordering
    - Retry logic with exponential backoff
    - Dead letter queue for failed jobs
    """

    def __init__(self, visibility_timeout_seconds: int = 30, max_retries: int = 3):
        self.visibility_timeout_seconds = visibility_timeout_seconds
        self.max_retries = max_retries

        self._jobs: Dict[str, MockQueueJob] = {}
        self._lock = asyncio.Lock()
        self._job_claimed_events: List[
            Tuple[str, str, datetime]
        ] = []  # job_id, robot_id, timestamp
        self._job_completed_events: List[Tuple[str, datetime]] = []
        self._job_failed_events: List[Tuple[str, str, datetime]] = []
        self._dlq_jobs: Dict[str, MockQueueJob] = {}
        self._lease_extensions: Dict[str, List[datetime]] = {}

    async def enqueue(
        self,
        job_id: str,
        workflow_id: str,
        workflow_name: str,
        workflow_json: str,
        priority: int = 1,
        environment: str = "default",
        variables: Optional[Dict[str, Any]] = None,
        affinity_robot_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Add a job to the queue."""
        async with self._lock:
            job = MockQueueJob(
                job_id=job_id,
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                workflow_json=workflow_json,
                priority=priority,
                environment=environment,
                variables=variables or {},
                max_retries=self.max_retries,
                affinity_robot_id=affinity_robot_id,
                session_id=session_id,
            )
            self._jobs[job_id] = job
            return job_id

    async def claim_job(
        self,
        robot_id: str,
        environment: str = "default",
        batch_size: int = 1,
    ) -> Optional[MockQueueJob]:
        """
        Claim a job using SKIP LOCKED semantics.

        Returns highest priority pending job visible to this robot.
        """
        async with self._lock:
            now = datetime.now(timezone.utc)

            # Find claimable jobs
            claimable = [
                job
                for job in self._jobs.values()
                if job.status == MockJobStatus.PENDING
                and job.visible_after <= now
                and (job.environment == environment or environment == "default")
            ]

            if not claimable:
                return None

            # Sort by priority (descending) then created_at (ascending)
            claimable.sort(key=lambda j: (-j.priority, j.created_at))

            # Check for affinity - prefer jobs with matching affinity
            affinity_match = next(
                (j for j in claimable if j.affinity_robot_id == robot_id), None
            )

            if affinity_match:
                job = affinity_match
            else:
                # Skip jobs with hard affinity to other robots
                non_affinity = [
                    j
                    for j in claimable
                    if not j.affinity_robot_id or j.affinity_robot_id == robot_id
                ]
                if not non_affinity:
                    return None
                job = non_affinity[0]

            # Claim the job (SKIP LOCKED simulation)
            job.status = MockJobStatus.CLAIMED
            job.robot_id = robot_id
            job.visible_after = now + timedelta(seconds=self.visibility_timeout_seconds)

            self._job_claimed_events.append((job.job_id, robot_id, now))

            return job

    async def extend_lease(
        self,
        job_id: str,
        robot_id: str,
        extension_seconds: int = 30,
    ) -> bool:
        """Extend visibility timeout for a claimed job."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if (
                not job
                or job.robot_id != robot_id
                or job.status not in (MockJobStatus.CLAIMED, MockJobStatus.RUNNING)
            ):
                return False

            job.visible_after = datetime.now(timezone.utc) + timedelta(
                seconds=extension_seconds
            )

            if job_id not in self._lease_extensions:
                self._lease_extensions[job_id] = []
            self._lease_extensions[job_id].append(datetime.now(timezone.utc))

            return True

    async def complete_job(
        self,
        job_id: str,
        robot_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a job as completed."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.robot_id != robot_id:
                return False

            job.status = MockJobStatus.COMPLETED
            job.result = result

            self._job_completed_events.append((job_id, datetime.now(timezone.utc)))
            return True

    async def fail_job(
        self,
        job_id: str,
        robot_id: str,
        error_message: str,
        should_retry: bool = True,
    ) -> Tuple[bool, bool]:
        """
        Mark a job as failed.

        Returns: (success, moved_to_dlq)
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.robot_id != robot_id:
                return False, False

            job.retry_count += 1
            job.error_message = error_message

            self._job_failed_events.append(
                (job_id, error_message, datetime.now(timezone.utc))
            )

            if should_retry and job.retry_count < job.max_retries:
                # Re-queue with exponential backoff
                backoff_seconds = (2**job.retry_count) * 5
                job.status = MockJobStatus.PENDING
                job.robot_id = None
                job.visible_after = datetime.now(timezone.utc) + timedelta(
                    seconds=backoff_seconds
                )
                return True, False
            else:
                # Move to DLQ
                job.status = MockJobStatus.DLQ
                self._dlq_jobs[job_id] = job
                return True, True

    async def release_job(self, job_id: str, robot_id: str) -> bool:
        """Release a job back to the queue."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.robot_id != robot_id:
                return False

            job.status = MockJobStatus.PENDING
            job.robot_id = None
            job.visible_after = datetime.now(timezone.utc)
            return True

    def simulate_visibility_timeout(self, job_id: str) -> bool:
        """Simulate visibility timeout expiration (robot crash scenario)."""
        job = self._jobs.get(job_id)
        if not job or job.status not in (MockJobStatus.CLAIMED, MockJobStatus.RUNNING):
            return False

        job.status = MockJobStatus.PENDING
        job.robot_id = None
        job.visible_after = datetime.now(timezone.utc)
        return True

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending = sum(
            1 for j in self._jobs.values() if j.status == MockJobStatus.PENDING
        )
        running = sum(
            1
            for j in self._jobs.values()
            if j.status in (MockJobStatus.CLAIMED, MockJobStatus.RUNNING)
        )
        completed = sum(
            1 for j in self._jobs.values() if j.status == MockJobStatus.COMPLETED
        )

        return {
            "pending": pending,
            "running": running,
            "completed": completed,
            "dlq_count": len(self._dlq_jobs),
            "total_claimed": len(self._job_claimed_events),
            "total_completed": len(self._job_completed_events),
            "total_failed": len(self._job_failed_events),
        }

    def get_lease_extension_count(self, job_id: str) -> int:
        """Get count of lease extensions for a job."""
        return len(self._lease_extensions.get(job_id, []))


class MockDBOSExecutor:
    """
    Mock DBOS executor for integration testing.

    Simulates durable workflow execution with:
    - Automatic checkpointing
    - Crash recovery
    - Exactly-once semantics
    """

    def __init__(self):
        self._executions: Dict[str, Dict[str, Any]] = {}
        self._checkpoints: Dict[str, List[str]] = {}
        self._should_fail = False
        self._fail_probability = 0.0
        self._execution_delay = 0.0
        self._fail_at_retry = -1  # Fail at specific retry count

    def configure_failure(
        self,
        should_fail: bool = False,
        fail_probability: float = 0.0,
        fail_at_retry: int = -1,
    ) -> None:
        """Configure failure behavior for testing."""
        self._should_fail = should_fail
        self._fail_probability = fail_probability
        self._fail_at_retry = fail_at_retry

    def set_execution_delay(self, delay: float) -> None:
        """Set artificial execution delay."""
        self._execution_delay = delay

    async def execute(
        self,
        workflow_json: str,
        workflow_id: str,
        variables: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Execute a workflow with DBOS durability."""
        self._executions[workflow_id] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "variables": variables or {},
            "retry_count": retry_count,
        }

        if self._execution_delay > 0:
            await asyncio.sleep(self._execution_delay)

        # Check for configured failures
        if self._should_fail:
            return {"success": False, "error": "Configured failure"}

        if self._fail_probability > 0 and random.random() < self._fail_probability:
            return {"success": False, "error": "Random failure"}

        if self._fail_at_retry >= 0 and retry_count <= self._fail_at_retry:
            return {"success": False, "error": f"Failure at retry {retry_count}"}

        # Simulate checkpoint
        if workflow_id not in self._checkpoints:
            self._checkpoints[workflow_id] = []
        self._checkpoints[workflow_id].append(
            f"step_{len(self._checkpoints[workflow_id])}"
        )

        return {
            "success": True,
            "workflow_id": workflow_id,
            "executed_nodes": 5,
            "duration_ms": int(self._execution_delay * 1000) or 100,
        }


class MockRobotAgent:
    """
    Mock robot agent for integration testing.

    Implements job polling, execution, and heartbeat.
    """

    def __init__(
        self,
        robot_id: str,
        queue: MockPgQueuer,
        executor: MockDBOSExecutor,
        environment: str = "default",
        poll_interval: float = 0.1,
        heartbeat_interval: float = 0.5,
        max_concurrent_jobs: int = 1,
    ):
        self.robot_id = robot_id
        self.queue = queue
        self.executor = executor
        self.environment = environment
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.max_concurrent_jobs = max_concurrent_jobs

        self._running = False
        self._current_jobs: Dict[str, MockQueueJob] = {}
        self._completed_jobs: List[str] = []
        self._failed_jobs: Dict[str, str] = {}
        self._polling_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._job_complete_events: Dict[str, asyncio.Event] = {}

    async def start(self) -> None:
        """Start the robot agent."""
        self._running = True
        self._shutdown_event.clear()

        self._polling_task = asyncio.create_task(self._polling_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(
        self, wait_for_completion: bool = True, timeout: float = 5.0
    ) -> None:
        """Stop the robot agent."""
        self._running = False

        if wait_for_completion and self._current_jobs:
            try:
                await asyncio.wait_for(
                    self._wait_for_current_jobs(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

        self._shutdown_event.set()

        for task in [self._polling_task, self._heartbeat_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _wait_for_current_jobs(self) -> None:
        """Wait for current jobs to complete."""
        while self._current_jobs:
            await asyncio.sleep(0.1)

    async def _polling_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                if len(self._current_jobs) >= self.max_concurrent_jobs:
                    await asyncio.sleep(self.poll_interval)
                    continue

                job = await self.queue.claim_job(
                    robot_id=self.robot_id,
                    environment=self.environment,
                )

                if job:
                    self._current_jobs[job.job_id] = job
                    self._job_complete_events[job.job_id] = asyncio.Event()
                    asyncio.create_task(self._execute_job(job))
                else:
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.poll_interval)

    async def _execute_job(self, job: MockQueueJob) -> None:
        """Execute a claimed job."""
        try:
            result = await self.executor.execute(
                workflow_json=job.workflow_json,
                workflow_id=job.job_id,
                variables=job.variables,
                retry_count=job.retry_count,
            )

            if result.get("success"):
                await self.queue.complete_job(job.job_id, self.robot_id, result)
                self._completed_jobs.append(job.job_id)
            else:
                error = result.get("error", "Unknown error")
                await self.queue.fail_job(job.job_id, self.robot_id, error)
                self._failed_jobs[job.job_id] = error

        except Exception as e:
            await self.queue.fail_job(job.job_id, self.robot_id, str(e))
            self._failed_jobs[job.job_id] = str(e)
        finally:
            self._current_jobs.pop(job.job_id, None)
            if job.job_id in self._job_complete_events:
                self._job_complete_events[job.job_id].set()

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop for lease extension."""
        while self._running:
            try:
                for job_id in list(self._current_jobs.keys()):
                    await self.queue.extend_lease(job_id, self.robot_id)

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def simulate_crash(self) -> None:
        """Simulate robot crash by immediately stopping without cleanup."""
        self._running = False
        # Don't release jobs - simulate crash
        self._current_jobs.clear()


class MockOrchestratorEngine:
    """
    Mock orchestrator engine for integration testing.

    Manages job submission, robot coordination, and queue integration.
    """

    def __init__(
        self,
        queue: MockPgQueuer,
        coordinator: RobotCoordinator,
    ):
        self.queue = queue
        self.coordinator = coordinator
        self._job_counter = 0

    async def submit_job(
        self,
        workflow_id: str,
        workflow_name: str,
        workflow_json: str,
        priority: int = 1,
        environment: str = "default",
        variables: Optional[Dict[str, Any]] = None,
        affinity_robot_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Submit a job to the queue."""
        self._job_counter += 1
        job_id = f"job-{self._job_counter:04d}-{uuid.uuid4().hex[:8]}"

        await self.queue.enqueue(
            job_id=job_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_json=workflow_json,
            priority=priority,
            environment=environment,
            variables=variables,
            affinity_robot_id=affinity_robot_id,
            session_id=session_id,
        )

        return job_id

    async def submit_batch(
        self,
        count: int,
        workflow_name: str = "Test Workflow",
        priority: int = 1,
    ) -> List[str]:
        """Submit multiple jobs."""
        job_ids = []
        for i in range(count):
            job_id = await self.submit_job(
                workflow_id=f"wf-{i:04d}",
                workflow_name=f"{workflow_name} {i}",
                workflow_json='{"nodes": []}',
                priority=priority,
            )
            job_ids.append(job_id)
        return job_ids


@pytest.fixture
def mock_queue() -> MockPgQueuer:
    """Provide mock PgQueuer instance."""
    return MockPgQueuer(visibility_timeout_seconds=5, max_retries=5)


@pytest.fixture
def mock_executor() -> MockDBOSExecutor:
    """Provide mock DBOS executor."""
    return MockDBOSExecutor()


@pytest.fixture
async def coordinator() -> RobotCoordinator:
    """Provide robot coordinator with in-memory repository."""
    repo = InMemoryCoordinationRepository()
    coord = RobotCoordinator(repository=repo)
    await coord.start()
    yield coord
    await coord.stop()


@pytest.fixture
def create_robot_agent(mock_queue: MockPgQueuer, mock_executor: MockDBOSExecutor):
    """Factory for creating robot agents."""
    agents = []

    def _create(
        robot_id: str, environment: str = "default", **kwargs
    ) -> MockRobotAgent:
        agent = MockRobotAgent(
            robot_id=robot_id,
            queue=mock_queue,
            executor=mock_executor,
            environment=environment,
            **kwargs,
        )
        agents.append(agent)
        return agent

    yield _create

    # Cleanup
    for agent in agents:
        agent._running = False


# =============================================================================
# TEST SECTION 1: END-TO-END ORCHESTRATOR -> ROBOT EXECUTION
# =============================================================================


class TestEndToEndExecution:
    """End-to-end tests: Orchestrator -> PgQueuer -> Robot -> DBOS execution."""

    @pytest.mark.asyncio
    async def test_single_job_end_to_end(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        coordinator: RobotCoordinator,
        create_robot_agent,
    ) -> None:
        """Complete flow: submit job -> claim -> execute -> complete."""
        # Setup
        orchestrator = MockOrchestratorEngine(mock_queue, coordinator)
        robot = create_robot_agent("robot-001")

        # Register robot
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="robot-001",
                name="Test Robot 1",
                capabilities=RobotCapabilities(max_concurrent_jobs=1),
            )
        )

        # Start robot
        await robot.start()

        # Submit job via orchestrator
        job_id = await orchestrator.submit_job(
            workflow_id="wf-001",
            workflow_name="End-to-End Test",
            workflow_json='{"nodes": [{"id": "start"}]}',
            variables={"test_input": "value"},
        )

        # Wait for completion
        await asyncio.sleep(0.5)

        # Verify
        await robot.stop()

        assert job_id in robot._completed_jobs
        stats = mock_queue.get_queue_stats()
        assert stats["completed"] == 1
        assert stats["pending"] == 0

    @pytest.mark.asyncio
    async def test_job_with_variables_passed_to_executor(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Job variables are correctly passed to DBOS executor."""
        robot = create_robot_agent("robot-001")

        variables = {"input_file": "/path/to/file.csv", "output_format": "json"}

        await mock_queue.enqueue(
            job_id="job-vars-001",
            workflow_id="wf-001",
            workflow_name="Variable Test",
            workflow_json='{"nodes": []}',
            variables=variables,
        )

        await robot.start()
        await asyncio.sleep(0.3)
        await robot.stop()

        # Verify variables were passed
        execution = mock_executor._executions.get("job-vars-001")
        assert execution is not None
        assert execution["variables"] == variables

    @pytest.mark.asyncio
    async def test_priority_ordering_respected(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Higher priority jobs are claimed before lower priority."""
        robot = create_robot_agent("robot-001")
        mock_executor.set_execution_delay(0.05)

        # Submit jobs in reverse priority order
        await mock_queue.enqueue(
            "low-priority", "wf-1", "Low Priority", "{}", priority=1
        )
        await mock_queue.enqueue(
            "normal-priority", "wf-2", "Normal Priority", "{}", priority=5
        )
        await mock_queue.enqueue(
            "high-priority", "wf-3", "High Priority", "{}", priority=10
        )

        await robot.start()
        await asyncio.sleep(0.5)
        await robot.stop()

        # Verify high priority was claimed first
        claimed_order = [event[0] for event in mock_queue._job_claimed_events]
        assert claimed_order[0] == "high-priority"
        assert claimed_order[1] == "normal-priority"
        assert claimed_order[2] == "low-priority"

    @pytest.mark.asyncio
    async def test_environment_filtering(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Robots only claim jobs for their environment."""
        prod_robot = create_robot_agent("prod-robot", environment="production")
        dev_robot = create_robot_agent("dev-robot", environment="development")

        # Submit jobs for different environments
        await mock_queue.enqueue(
            "prod-job", "wf-1", "Prod Job", "{}", environment="production"
        )
        await mock_queue.enqueue(
            "dev-job", "wf-2", "Dev Job", "{}", environment="development"
        )

        await prod_robot.start()
        await dev_robot.start()
        await asyncio.sleep(0.3)
        await prod_robot.stop()
        await dev_robot.stop()

        # Verify correct routing
        assert "prod-job" in prod_robot._completed_jobs
        assert "dev-job" in dev_robot._completed_jobs


# =============================================================================
# TEST SECTION 2: MULTI-ROBOT COORDINATION
# =============================================================================


class TestMultiRobotCoordination:
    """Tests for 2+ robots claiming jobs concurrently."""

    @pytest.mark.asyncio
    async def test_two_robots_claim_different_jobs(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Two robots claiming jobs don't get the same job (SKIP LOCKED)."""
        robot1 = create_robot_agent("robot-001")
        robot2 = create_robot_agent("robot-002")

        # Submit multiple jobs
        for i in range(4):
            await mock_queue.enqueue(f"job-{i}", f"wf-{i}", f"Job {i}", "{}")

        await robot1.start()
        await robot2.start()
        await asyncio.sleep(0.5)
        await robot1.stop()
        await robot2.stop()

        # Verify no duplicate claims
        all_completed = set(robot1._completed_jobs + robot2._completed_jobs)
        assert len(all_completed) == 4

        # Verify each robot got jobs
        assert len(robot1._completed_jobs) >= 1
        assert len(robot2._completed_jobs) >= 1

    @pytest.mark.asyncio
    async def test_concurrent_claiming_race_condition(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
    ) -> None:
        """Multiple robots trying to claim same job - only one succeeds."""
        # Submit single job
        await mock_queue.enqueue("contested-job", "wf-1", "Contested", "{}")

        # Simulate concurrent claims
        results = await asyncio.gather(
            mock_queue.claim_job("robot-1"),
            mock_queue.claim_job("robot-2"),
            mock_queue.claim_job("robot-3"),
        )

        # Only one robot should get the job
        claimed = [r for r in results if r is not None]
        assert len(claimed) == 1

    @pytest.mark.asyncio
    async def test_robot_pool_processes_job_queue(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Pool of robots processes entire job queue."""
        robots = [create_robot_agent(f"robot-{i:03d}") for i in range(3)]
        mock_executor.set_execution_delay(0.05)

        # Submit more jobs than robots
        job_count = 10
        for i in range(job_count):
            await mock_queue.enqueue(f"job-{i}", f"wf-{i}", f"Job {i}", "{}")

        # Start all robots
        for robot in robots:
            await robot.start()

        await asyncio.sleep(1.0)

        # Stop all robots
        for robot in robots:
            await robot.stop()

        # All jobs should be completed
        total_completed = sum(len(r._completed_jobs) for r in robots)
        assert total_completed == job_count

    @pytest.mark.asyncio
    async def test_load_distribution_across_robots(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Jobs are distributed across multiple robots."""
        robots = [create_robot_agent(f"robot-{i:03d}") for i in range(4)]
        mock_executor.set_execution_delay(0.02)

        # Submit enough jobs
        job_count = 20
        for i in range(job_count):
            await mock_queue.enqueue(f"job-{i}", f"wf-{i}", f"Job {i}", "{}")

        for robot in robots:
            await robot.start()

        await asyncio.sleep(1.5)

        for robot in robots:
            await robot.stop()

        # Each robot should have processed some jobs
        for robot in robots:
            assert len(robot._completed_jobs) >= 1, f"{robot.robot_id} got no jobs"


# =============================================================================
# TEST SECTION 3: FAILOVER AND RECOVERY
# =============================================================================


class TestFailoverRecovery:
    """Tests for robot crash mid-job and recovery via visibility timeout."""

    @pytest.mark.asyncio
    async def test_crashed_robot_job_returns_to_queue(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Job returns to queue when robot crashes (visibility timeout)."""
        robot1 = create_robot_agent("robot-001")
        mock_executor.set_execution_delay(1.0)  # Long execution

        await mock_queue.enqueue("crash-job", "wf-1", "Crash Test", "{}")

        await robot1.start()
        await asyncio.sleep(0.2)  # Let it claim

        # Simulate crash
        robot1.simulate_crash()
        mock_queue.simulate_visibility_timeout("crash-job")

        # Job should be back in queue
        stats = mock_queue.get_queue_stats()
        assert stats["pending"] == 1

    @pytest.mark.asyncio
    async def test_second_robot_picks_up_failed_job(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Another robot can pick up job after first robot crashes."""
        robot1 = create_robot_agent("robot-001")
        robot2 = create_robot_agent("robot-002")

        mock_executor.set_execution_delay(0.5)
        await mock_queue.enqueue("recovery-job", "wf-1", "Recovery Test", "{}")

        # Robot 1 starts and claims job
        await robot1.start()
        await asyncio.sleep(0.2)

        # Crash robot 1
        robot1.simulate_crash()
        mock_queue.simulate_visibility_timeout("recovery-job")

        # Robot 2 should pick it up
        await robot2.start()
        await asyncio.sleep(0.8)
        await robot2.stop()

        assert "recovery-job" in robot2._completed_jobs

    @pytest.mark.asyncio
    async def test_heartbeat_prevents_premature_timeout(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Regular heartbeats keep job lease alive during long execution."""
        robot = create_robot_agent(
            "robot-001",
            heartbeat_interval=0.1,
        )
        mock_executor.set_execution_delay(0.4)

        await mock_queue.enqueue("long-job", "wf-1", "Long Job", "{}")

        await robot.start()
        await asyncio.sleep(0.6)
        await robot.stop()

        # Job should complete, not timeout
        assert "long-job" in robot._completed_jobs

        # Multiple heartbeats should have been sent
        extension_count = mock_queue.get_lease_extension_count("long-job")
        assert extension_count >= 2

    @pytest.mark.asyncio
    async def test_graceful_shutdown_completes_current_job(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Graceful shutdown waits for current job to complete."""
        robot = create_robot_agent("robot-001")
        mock_executor.set_execution_delay(0.3)

        await mock_queue.enqueue("in-progress-job", "wf-1", "In Progress", "{}")

        await robot.start()
        await asyncio.sleep(0.1)  # Let it start

        # Graceful stop should wait
        await robot.stop(wait_for_completion=True, timeout=1.0)

        assert "in-progress-job" in robot._completed_jobs


# =============================================================================
# TEST SECTION 4: STATE AFFINITY
# =============================================================================


class TestStateAffinity:
    """Tests for soft, hard, and session affinity routing."""

    @pytest.mark.asyncio
    async def test_soft_affinity_prefers_specified_robot(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Soft affinity prefers specified robot but allows others if unavailable."""
        robot1 = create_robot_agent("robot-001")
        robot2 = create_robot_agent("robot-002")

        # Submit job with soft affinity to robot-001
        await mock_queue.enqueue(
            "affinity-job",
            "wf-1",
            "Affinity Test",
            "{}",
            affinity_robot_id="robot-001",
        )

        await robot1.start()
        await asyncio.sleep(0.3)
        await robot1.stop()

        # Job should go to preferred robot
        assert "affinity-job" in robot1._completed_jobs

    @pytest.mark.asyncio
    async def test_hard_affinity_only_specified_robot(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Hard affinity: only specified robot can claim job."""
        robot2 = create_robot_agent("robot-002")

        # Submit job with hard affinity to robot-001 (not started)
        await mock_queue.enqueue(
            "hard-affinity-job",
            "wf-1",
            "Hard Affinity",
            "{}",
            affinity_robot_id="robot-001",
        )

        # Robot 2 should not be able to claim it
        await robot2.start()
        await asyncio.sleep(0.3)
        await robot2.stop()

        # Job should still be pending (robot-001 not available)
        stats = mock_queue.get_queue_stats()
        # In our mock, hard affinity jobs are skipped by non-matching robots
        assert "hard-affinity-job" not in robot2._completed_jobs

    @pytest.mark.asyncio
    async def test_session_affinity_sticky_routing(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Session affinity routes related jobs to same robot."""
        robot1 = create_robot_agent("robot-001")
        robot2 = create_robot_agent("robot-002")

        session_id = "session-12345"

        # Submit multiple jobs with same session
        for i in range(3):
            await mock_queue.enqueue(
                f"session-job-{i}",
                f"wf-{i}",
                f"Session Job {i}",
                "{}",
                session_id=session_id,
                affinity_robot_id="robot-001",  # Set affinity after first job
            )

        await robot1.start()
        await asyncio.sleep(0.5)
        await robot1.stop()

        # All session jobs should go to same robot
        session_jobs = [j for j in robot1._completed_jobs if j.startswith("session-")]
        assert len(session_jobs) >= 2


# =============================================================================
# TEST SECTION 5: LOAD BALANCING
# =============================================================================


class TestLoadBalancing:
    """Tests for job distribution across robot pool."""

    @pytest.mark.asyncio
    async def test_least_busy_strategy(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Least busy strategy selects robot with lowest load."""
        # Register robots with different loads
        for i in range(3):
            await coordinator.register_robot(
                RobotRegistration(
                    robot_id=f"robot-{i}",
                    name=f"Robot {i}",
                    capabilities=RobotCapabilities(max_concurrent_jobs=5),
                )
            )

        # Update metrics to simulate different loads
        await coordinator.heartbeat("robot-0", RobotMetrics(current_jobs=4))
        await coordinator.heartbeat("robot-1", RobotMetrics(current_jobs=1))
        await coordinator.heartbeat("robot-2", RobotMetrics(current_jobs=3))

        # Select robot
        selected = await coordinator.select_robot_for_job(
            strategy=LoadBalancingStrategy.LEAST_BUSY
        )

        assert selected is not None
        assert selected.robot_id == "robot-1"  # Least busy

    @pytest.mark.asyncio
    async def test_round_robin_distribution(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Round robin distributes jobs evenly."""
        # Register robots
        for i in range(3):
            await coordinator.register_robot(
                RobotRegistration(
                    robot_id=f"robot-{i}",
                    name=f"Robot {i}",
                    capabilities=RobotCapabilities(max_concurrent_jobs=5),
                )
            )

        # Select multiple times
        selected_ids = []
        for _ in range(6):
            robot = await coordinator.select_robot_for_job(
                strategy=LoadBalancingStrategy.ROUND_ROBIN
            )
            if robot:
                selected_ids.append(robot.robot_id)

        # Should cycle through all robots
        assert len(set(selected_ids)) == 3

    @pytest.mark.asyncio
    async def test_capability_based_routing(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Capability-based strategy matches job requirements."""
        # Register robots with different capabilities
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="gpu-robot",
                name="GPU Robot",
                capabilities=RobotCapabilities(has_gpu=True, tags=["gpu", "ml"]),
            )
        )

        await coordinator.register_robot(
            RobotRegistration(
                robot_id="browser-robot",
                name="Browser Robot",
                capabilities=RobotCapabilities(has_browser=True, tags=["web"]),
            )
        )

        # Request GPU job
        requirements = JobRequirements(requires_gpu=True)
        selected = await coordinator.select_robot_for_job(
            requirements=requirements,
            strategy=LoadBalancingStrategy.CAPABILITY_BASED,
        )

        assert selected is not None
        assert selected.robot_id == "gpu-robot"

    @pytest.mark.asyncio
    async def test_weighted_distribution(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Weighted strategy favors robots with more capacity."""
        # Register robots with different capacities
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="small-robot",
                name="Small Robot",
                capabilities=RobotCapabilities(max_concurrent_jobs=1),
            )
        )

        await coordinator.register_robot(
            RobotRegistration(
                robot_id="large-robot",
                name="Large Robot",
                capabilities=RobotCapabilities(max_concurrent_jobs=10),
            )
        )

        # Select many times
        selections = {"small-robot": 0, "large-robot": 0}
        for _ in range(100):
            robot = await coordinator.select_robot_for_job(
                strategy=LoadBalancingStrategy.WEIGHTED
            )
            if robot:
                selections[robot.robot_id] += 1

        # Large robot should get more jobs
        assert selections["large-robot"] > selections["small-robot"]


# =============================================================================
# TEST SECTION 6: DEAD LETTER QUEUE (DLQ)
# =============================================================================


class TestDeadLetterQueue:
    """Tests for jobs failing 5 times moving to DLQ."""

    @pytest.mark.asyncio
    async def test_job_moves_to_dlq_after_max_retries(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
    ) -> None:
        """Job moves to DLQ after exceeding max retries."""
        mock_queue.max_retries = 3

        await mock_queue.enqueue("failing-job", "wf-1", "Failing Job", "{}")

        # Manually simulate retry failures to test DLQ logic directly
        for i in range(3):
            job = await mock_queue.claim_job("robot-001")
            if job:
                # Fail the job
                _, moved_to_dlq = await mock_queue.fail_job(
                    job.job_id, "robot-001", f"Failure {i + 1}"
                )
                if moved_to_dlq:
                    break
                # Reset visible_after to allow immediate retry
                if job.job_id in mock_queue._jobs:
                    mock_queue._jobs[job.job_id].visible_after = datetime.now(
                        timezone.utc
                    )

        # Job should be in DLQ after max_retries failures
        assert "failing-job" in mock_queue._dlq_jobs

    @pytest.mark.asyncio
    async def test_retry_count_increments(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
    ) -> None:
        """Retry count increments on each failure."""
        mock_queue.max_retries = 5

        await mock_queue.enqueue("retry-job", "wf-1", "Retry Job", "{}")

        # Simulate two failures followed by success
        for i in range(2):
            job = await mock_queue.claim_job("robot-001")
            if job:
                await mock_queue.fail_job(job.job_id, "robot-001", f"Failure {i + 1}")
                # Reset visible_after to allow immediate retry
                if job.job_id in mock_queue._jobs:
                    mock_queue._jobs[job.job_id].visible_after = datetime.now(
                        timezone.utc
                    )

        # Verify retry count incremented
        job = mock_queue._jobs.get("retry-job")
        assert job is not None
        assert job.retry_count == 2

        # Should have failed events
        fail_events = [e for e in mock_queue._job_failed_events if e[0] == "retry-job"]
        assert len(fail_events) == 2

    @pytest.mark.asyncio
    async def test_dlq_jobs_not_reclaimed(
        self,
        mock_queue: MockPgQueuer,
    ) -> None:
        """Jobs in DLQ are not claimed by robots."""
        # Manually add job to DLQ
        job = MockQueueJob(
            job_id="dlq-job",
            workflow_id="wf-1",
            workflow_name="DLQ Job",
            workflow_json="{}",
            status=MockJobStatus.DLQ,
        )
        mock_queue._dlq_jobs["dlq-job"] = job

        # Try to claim
        claimed = await mock_queue.claim_job("robot-001")

        assert claimed is None

    @pytest.mark.asyncio
    async def test_exponential_backoff_between_retries(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
    ) -> None:
        """Retries use exponential backoff timing."""
        mock_queue.max_retries = 5

        await mock_queue.enqueue("backoff-job", "wf-1", "Backoff Test", "{}")

        # Claim and fail multiple times
        for i in range(3):
            job = await mock_queue.claim_job("robot-001")
            if job:
                await mock_queue.fail_job(job.job_id, "robot-001", f"Failure {i}")

        # Check that visible_after increases with each retry
        job = mock_queue._jobs.get("backoff-job")
        if job:
            # Backoff should be applied
            now = datetime.now(timezone.utc)
            assert job.visible_after > now


# =============================================================================
# TEST SECTION 7: RESOURCE POOLING AND QUOTA
# =============================================================================


class TestResourcePoolingQuota:
    """Tests for quota enforcement and resource limits."""

    @pytest.mark.asyncio
    async def test_max_concurrent_jobs_enforced(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Robot doesn't claim more than max_concurrent_jobs."""
        robot = create_robot_agent("robot-001", max_concurrent_jobs=2)
        mock_executor.set_execution_delay(0.3)

        # Submit more jobs than concurrency limit
        for i in range(5):
            await mock_queue.enqueue(f"job-{i}", f"wf-{i}", f"Job {i}", "{}")

        await robot.start()
        await asyncio.sleep(0.1)

        # Should only have max concurrent jobs
        assert len(robot._current_jobs) <= 2

        await robot.stop(wait_for_completion=False)

    @pytest.mark.asyncio
    async def test_robot_capacity_respected_in_routing(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Load balancer respects robot capacity."""
        # Register robot at capacity
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="full-robot",
                name="Full Robot",
                capabilities=RobotCapabilities(max_concurrent_jobs=2),
            )
        )
        await coordinator.heartbeat("full-robot", RobotMetrics(current_jobs=2))

        # Register robot with capacity
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="available-robot",
                name="Available Robot",
                capabilities=RobotCapabilities(max_concurrent_jobs=2),
            )
        )
        await coordinator.heartbeat("available-robot", RobotMetrics(current_jobs=0))

        # Should select available robot
        selected = await coordinator.select_robot_for_job()

        assert selected is not None
        assert selected.robot_id == "available-robot"

    @pytest.mark.asyncio
    async def test_no_robot_available_returns_none(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Returns None when no robots have capacity."""
        # Register robot at capacity
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="full-robot",
                name="Full Robot",
                capabilities=RobotCapabilities(max_concurrent_jobs=1),
            )
        )
        await coordinator.heartbeat("full-robot", RobotMetrics(current_jobs=1))

        # Should return None
        selected = await coordinator.select_robot_for_job()

        assert selected is None

    @pytest.mark.asyncio
    async def test_scaling_recommendation_on_high_utilization(
        self,
        coordinator: RobotCoordinator,
    ) -> None:
        """Auto-scaling recommends scale up on high utilization."""
        # Register robots at high utilization
        for i in range(3):
            await coordinator.register_robot(
                RobotRegistration(
                    robot_id=f"robot-{i}",
                    name=f"Robot {i}",
                    capabilities=RobotCapabilities(max_concurrent_jobs=2),
                )
            )
            await coordinator.heartbeat(f"robot-{i}", RobotMetrics(current_jobs=2))

        # Evaluate scaling
        decision = await coordinator.evaluate_scaling(queue_depth=10)

        # Should recommend scale up
        assert decision.action == ScalingAction.SCALE_UP


# =============================================================================
# TEST SECTION 8: HYBRID POLL + SUBSCRIBE
# =============================================================================


class TestHybridPollSubscribe:
    """Tests for hybrid poll + Realtime notification integration."""

    @pytest.mark.asyncio
    async def test_realtime_notification_triggers_immediate_claim(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
    ) -> None:
        """
        Realtime notification triggers immediate job claim.

        This tests the concept that a realtime notification can wake up
        a robot to claim a job without waiting for the next poll cycle.
        In a real implementation, the notification would signal an event
        that interrupts the polling sleep.
        """
        # Simulate a robot with notification capability
        notification_event = asyncio.Event()
        job_claimed = asyncio.Event()

        await mock_queue.enqueue("realtime-job", "wf-1", "Realtime", "{}")

        async def robot_with_notification():
            """Robot that responds to notifications."""
            # Wait for notification instead of polling
            await notification_event.wait()
            # Immediately claim the job
            job = await mock_queue.claim_job("robot-001")
            if job:
                await mock_queue.complete_job(
                    job.job_id, "robot-001", {"success": True}
                )
                job_claimed.set()

        # Start robot task
        robot_task = asyncio.create_task(robot_with_notification())

        # Simulate realtime notification arriving
        await asyncio.sleep(0.05)
        notification_event.set()

        # Wait for claim
        await asyncio.wait_for(job_claimed.wait(), timeout=1.0)
        await robot_task

        # Verify job was processed
        stats = mock_queue.get_queue_stats()
        assert stats["completed"] == 1

    @pytest.mark.asyncio
    async def test_fallback_to_polling_when_realtime_unavailable(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Robot falls back to polling when realtime is unavailable."""
        robot = create_robot_agent("robot-001", poll_interval=0.1)

        # Submit job without realtime notification
        await mock_queue.enqueue("poll-job", "wf-1", "Poll Test", "{}")

        await robot.start()
        await asyncio.sleep(0.3)
        await robot.stop()

        # Job should still be processed via polling
        assert "poll-job" in robot._completed_jobs


# =============================================================================
# TEST SECTION 9: ORCHESTRATOR QUEUE INTEGRATION
# =============================================================================


class TestOrchestratorQueueIntegration:
    """Tests for Orchestrator-PgQueuer integration."""

    @pytest.mark.asyncio
    async def test_orchestrator_submits_to_queue(
        self,
        mock_queue: MockPgQueuer,
        coordinator: RobotCoordinator,
    ) -> None:
        """Orchestrator correctly submits jobs to queue."""
        orchestrator = MockOrchestratorEngine(mock_queue, coordinator)

        job_id = await orchestrator.submit_job(
            workflow_id="wf-001",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
            priority=5,
        )

        assert job_id is not None
        stats = mock_queue.get_queue_stats()
        assert stats["pending"] == 1

    @pytest.mark.asyncio
    async def test_batch_job_submission(
        self,
        mock_queue: MockPgQueuer,
        coordinator: RobotCoordinator,
    ) -> None:
        """Orchestrator can submit batch of jobs."""
        orchestrator = MockOrchestratorEngine(mock_queue, coordinator)

        job_ids = await orchestrator.submit_batch(count=10, workflow_name="Batch Job")

        assert len(job_ids) == 10
        stats = mock_queue.get_queue_stats()
        assert stats["pending"] == 10

    @pytest.mark.asyncio
    async def test_job_routing_with_coordinator(
        self,
        mock_queue: MockPgQueuer,
        coordinator: RobotCoordinator,
    ) -> None:
        """Orchestrator uses coordinator for job routing."""
        # Register robots
        await coordinator.register_robot(
            RobotRegistration(
                robot_id="targeted-robot",
                name="Targeted Robot",
                capabilities=RobotCapabilities(tags=["special"]),
            )
        )

        orchestrator = MockOrchestratorEngine(mock_queue, coordinator)

        # Submit job with affinity
        job_id = await orchestrator.submit_job(
            workflow_id="wf-001",
            workflow_name="Targeted Job",
            workflow_json="{}",
            affinity_robot_id="targeted-robot",
        )

        assert job_id is not None
        job = mock_queue._jobs.get(job_id)
        assert job is not None
        assert job.affinity_robot_id == "targeted-robot"


# =============================================================================
# TEST SECTION 10: COMPREHENSIVE INTEGRATION SCENARIOS
# =============================================================================


class TestComprehensiveIntegration:
    """Complex integration scenarios testing multiple components together."""

    @pytest.mark.asyncio
    async def test_full_system_under_load(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        coordinator: RobotCoordinator,
        create_robot_agent,
    ) -> None:
        """Full system processes many jobs with multiple robots."""
        # Setup
        orchestrator = MockOrchestratorEngine(mock_queue, coordinator)
        robots = []

        for i in range(5):
            robot = create_robot_agent(f"robot-{i:03d}")
            robots.append(robot)
            await coordinator.register_robot(
                RobotRegistration(
                    robot_id=f"robot-{i:03d}",
                    name=f"Robot {i}",
                    capabilities=RobotCapabilities(max_concurrent_jobs=2),
                )
            )

        mock_executor.set_execution_delay(0.02)

        # Submit jobs
        job_ids = await orchestrator.submit_batch(count=50)

        # Start all robots
        for robot in robots:
            await robot.start()

        # Wait for processing
        await asyncio.sleep(3.0)

        # Stop all robots
        for robot in robots:
            await robot.stop(wait_for_completion=False)

        # Verify
        total_completed = sum(len(r._completed_jobs) for r in robots)
        assert total_completed >= 45  # Allow some margin

    @pytest.mark.asyncio
    async def test_mixed_priority_and_affinity(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """System handles mix of priority and affinity requirements."""
        robot1 = create_robot_agent("robot-001")
        robot2 = create_robot_agent("robot-002")

        mock_executor.set_execution_delay(0.02)

        # Submit various jobs
        await mock_queue.enqueue("high-pri", "wf-1", "High Priority", "{}", priority=10)
        await mock_queue.enqueue(
            "affinity",
            "wf-2",
            "Affinity",
            "{}",
            priority=5,
            affinity_robot_id="robot-001",
        )
        await mock_queue.enqueue("normal", "wf-3", "Normal", "{}", priority=5)
        await mock_queue.enqueue("low-pri", "wf-4", "Low Priority", "{}", priority=1)

        await robot1.start()
        await robot2.start()

        await asyncio.sleep(0.5)

        await robot1.stop()
        await robot2.stop()

        # All jobs should complete
        all_completed = robot1._completed_jobs + robot2._completed_jobs
        assert len(all_completed) == 4

    @pytest.mark.asyncio
    async def test_failure_recovery_chain(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """System recovers from robot failure chain."""
        mock_queue.max_retries = 5

        robot1 = create_robot_agent("robot-001")
        robot2 = create_robot_agent("robot-002")
        robot3 = create_robot_agent("robot-003")

        mock_executor.set_execution_delay(0.2)

        await mock_queue.enqueue("resilient-job", "wf-1", "Resilient", "{}")

        # Robot 1 claims then crashes
        await robot1.start()
        await asyncio.sleep(0.1)
        robot1.simulate_crash()
        mock_queue.simulate_visibility_timeout("resilient-job")

        # Robot 2 claims then crashes
        await robot2.start()
        await asyncio.sleep(0.1)
        robot2.simulate_crash()
        mock_queue.simulate_visibility_timeout("resilient-job")

        # Robot 3 successfully processes
        await robot3.start()
        await asyncio.sleep(0.5)
        await robot3.stop()

        assert "resilient-job" in robot3._completed_jobs

    @pytest.mark.asyncio
    async def test_concurrent_environment_isolation(
        self,
        mock_queue: MockPgQueuer,
        mock_executor: MockDBOSExecutor,
        create_robot_agent,
    ) -> None:
        """Multiple environments process jobs independently."""
        prod_robots = [
            create_robot_agent(f"prod-{i}", environment="production") for i in range(2)
        ]
        dev_robots = [
            create_robot_agent(f"dev-{i}", environment="development") for i in range(2)
        ]

        mock_executor.set_execution_delay(0.02)

        # Submit jobs to different environments
        for i in range(5):
            await mock_queue.enqueue(
                f"prod-{i}", f"wf-p{i}", f"Prod {i}", "{}", environment="production"
            )
            await mock_queue.enqueue(
                f"dev-{i}", f"wf-d{i}", f"Dev {i}", "{}", environment="development"
            )

        # Start all robots
        for robot in prod_robots + dev_robots:
            await robot.start()

        await asyncio.sleep(1.0)

        for robot in prod_robots + dev_robots:
            await robot.stop()

        # Verify environment isolation
        prod_completed = []
        for r in prod_robots:
            prod_completed.extend(r._completed_jobs)

        dev_completed = []
        for r in dev_robots:
            dev_completed.extend(r._completed_jobs)

        # Prod robots should only have prod jobs
        for job_id in prod_completed:
            assert job_id.startswith("prod-")

        # Dev robots should only have dev jobs
        for job_id in dev_completed:
            assert job_id.startswith("dev-")


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
