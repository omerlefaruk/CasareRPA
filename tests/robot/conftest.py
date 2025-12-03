"""
Test fixtures for Robot Agent tests.

Provides mocks for PgQueuer and DBOS components, plus fixtures for:
- Robot configuration (RobotConfig, RobotCapabilities)
- Mock consumers and executors
- Sample jobs and workflows
- Audit logger mocks
- Circuit breaker fixtures
"""

import asyncio
import uuid
from pathlib import Path

import pytest
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock


class JobStatus(Enum):
    """Status of a job in PgQueuer."""

    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Job:
    """
    Represents a job from PgQueuer.

    Matches the structure specified in the roadmap for Phase 3.4.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    variables: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    status: JobStatus = JobStatus.PENDING
    claimed_by: Optional[str] = None
    claimed_at: Optional[datetime] = None
    visibility_timeout: int = 30
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MockPgQueuerConsumer:
    """
    Mock PgQueuer consumer for testing.

    Simulates the distributed queue consumer that robots use to
    claim and process jobs. Uses SKIP LOCKED semantics.
    """

    def __init__(
        self,
        postgres_url: str = "postgresql://test",
        robot_id: str = "test-robot",
        batch_size: int = 1,
        visibility_timeout_seconds: int = 30,
    ):
        self.postgres_url = postgres_url
        self.robot_id = robot_id
        self.batch_size = batch_size
        self.visibility_timeout_seconds = visibility_timeout_seconds

        self._jobs: Dict[str, Job] = {}
        self._claimed_jobs: Dict[str, Job] = {}
        self._connected = False
        self._lease_extensions: Dict[str, List[datetime]] = {}
        self._completed_jobs: Dict[str, Dict[str, Any]] = {}
        self._failed_jobs: Dict[str, str] = {}

    async def start(self) -> None:
        """Start the consumer connection."""
        self._connected = True

    async def stop(self) -> None:
        """Stop the consumer connection."""
        self._connected = False

    def add_job(self, job: Job) -> None:
        """Add a job to the queue for testing."""
        self._jobs[job.job_id] = job

    async def claim_job(self) -> Optional[Job]:
        """
        Claim a pending job using SKIP LOCKED semantics.

        Returns:
            Job if one was claimed, None otherwise.
        """
        if not self._connected:
            raise RuntimeError("Consumer not connected")

        for job_id, job in list(self._jobs.items()):
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CLAIMED
                job.claimed_by = self.robot_id
                job.claimed_at = datetime.now(timezone.utc)
                self._claimed_jobs[job_id] = job
                del self._jobs[job_id]
                return job

        return None

    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """Mark a job as completed."""
        if job_id in self._claimed_jobs:
            job = self._claimed_jobs[job_id]
            job.status = JobStatus.COMPLETED
            self._completed_jobs[job_id] = result

    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        if job_id in self._claimed_jobs:
            job = self._claimed_jobs[job_id]
            job.status = JobStatus.FAILED
            self._failed_jobs[job_id] = error

    async def extend_lease(self, job_id: str, extension_seconds: int = 30) -> bool:
        """
        Extend the visibility timeout for a claimed job.

        Returns:
            True if lease was extended.
        """
        if job_id not in self._claimed_jobs:
            return False

        if job_id not in self._lease_extensions:
            self._lease_extensions[job_id] = []

        self._lease_extensions[job_id].append(datetime.now(timezone.utc))
        return True

    async def release_job(self, job_id: str) -> None:
        """Release a claimed job back to the queue."""
        if job_id in self._claimed_jobs:
            job = self._claimed_jobs[job_id]
            job.status = JobStatus.PENDING
            job.claimed_by = None
            job.claimed_at = None
            self._jobs[job_id] = job
            del self._claimed_jobs[job_id]

    def get_lease_extension_count(self, job_id: str) -> int:
        """Get the number of lease extensions for a job."""
        return len(self._lease_extensions.get(job_id, []))

    def simulate_visibility_timeout(self, job_id: str) -> None:
        """Simulate a job's visibility timeout expiring."""
        if job_id in self._claimed_jobs:
            job = self._claimed_jobs[job_id]
            job.status = JobStatus.PENDING
            job.claimed_by = None
            job.claimed_at = None
            self._jobs[job_id] = job
            del self._claimed_jobs[job_id]


class MockDBOSWorkflowExecutor:
    """
    Mock DBOS workflow executor for testing.

    Simulates durable workflow execution with automatic checkpointing
    and crash recovery.
    """

    def __init__(self):
        self._executions: Dict[str, Dict[str, Any]] = {}
        self._checkpoints: Dict[str, List[str]] = {}
        self._should_fail: bool = False
        self._fail_at_node: Optional[str] = None
        self._execution_delay: float = 0.0
        self._crash_simulation: bool = False

    def set_should_fail(self, should_fail: bool = True) -> None:
        """Configure executor to fail workflow execution."""
        self._should_fail = should_fail

    def set_fail_at_node(self, node_id: Optional[str]) -> None:
        """Configure executor to fail at a specific node."""
        self._fail_at_node = node_id

    def set_execution_delay(self, delay: float) -> None:
        """Set artificial delay for execution (for testing timeouts)."""
        self._execution_delay = delay

    def simulate_crash(self) -> None:
        """Mark that a crash should be simulated during execution."""
        self._crash_simulation = True

    async def execute_workflow(
        self,
        workflow: Any,
        workflow_id: str,
        initial_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow with DBOS durability.

        Returns:
            Execution result with success status and any errors.
        """
        self._executions[workflow_id] = {
            "workflow_id": workflow_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "variables": initial_variables or {},
        }

        if self._execution_delay > 0:
            await asyncio.sleep(self._execution_delay)

        if self._crash_simulation:
            self._crash_simulation = False
            raise RuntimeError("Simulated crash during execution")

        if self._should_fail:
            return {
                "success": False,
                "error": "Workflow execution failed",
                "workflow_id": workflow_id,
            }

        if self._fail_at_node:
            return {
                "success": False,
                "error": f"Failed at node {self._fail_at_node}",
                "workflow_id": workflow_id,
                "failed_node": self._fail_at_node,
            }

        return {
            "success": True,
            "workflow_id": workflow_id,
            "result": {"completed": True},
        }

    def add_checkpoint(self, workflow_id: str, node_id: str) -> None:
        """Record a checkpoint for a workflow."""
        if workflow_id not in self._checkpoints:
            self._checkpoints[workflow_id] = []
        self._checkpoints[workflow_id].append(node_id)

    def get_checkpoints(self, workflow_id: str) -> List[str]:
        """Get checkpoints for a workflow."""
        return self._checkpoints.get(workflow_id, [])

    def has_checkpoint(self, workflow_id: str) -> bool:
        """Check if workflow has any checkpoints."""
        return (
            workflow_id in self._checkpoints and len(self._checkpoints[workflow_id]) > 0
        )


@dataclass
class RobotConfig:
    """
    Configuration for Robot Agent testing.

    Mirrors the config structure from the roadmap.
    """

    robot_id: str = "test-robot-001"
    postgres_url: str = "postgresql://test:test@localhost/test"
    batch_size: int = 1
    poll_interval_seconds: float = 0.1
    max_concurrent_jobs: int = 1
    job_timeout_seconds: int = 60
    heartbeat_interval_seconds: float = 0.5
    lease_extension_seconds: int = 30
    grace_period_seconds: float = 1.0


@pytest.fixture
def robot_config() -> RobotConfig:
    """Provide default robot configuration for tests."""
    return RobotConfig()


@pytest.fixture
def mock_consumer() -> MockPgQueuerConsumer:
    """Provide a mock PgQueuer consumer."""
    return MockPgQueuerConsumer()


@pytest.fixture
def mock_executor() -> MockDBOSWorkflowExecutor:
    """Provide a mock DBOS workflow executor."""
    return MockDBOSWorkflowExecutor()


@pytest.fixture
def sample_job() -> Job:
    """Provide a sample job for testing."""
    return Job(
        job_id="job-001",
        workflow_id="workflow-001",
        workflow_name="Test Workflow",
        workflow_json='{"nodes": [], "connections": []}',
        variables={"input_var": "test_value"},
        priority=5,
    )


@pytest.fixture
def sample_workflow_json() -> str:
    """Provide sample workflow JSON for testing."""
    return """
    {
        "metadata": {
            "name": "Test Workflow",
            "version": "1.0.0"
        },
        "nodes": [
            {
                "id": "start-node",
                "type": "StartNode",
                "properties": {}
            },
            {
                "id": "log-node",
                "type": "LogNode",
                "properties": {"message": "Hello"}
            },
            {
                "id": "end-node",
                "type": "EndNode",
                "properties": {}
            }
        ],
        "connections": [
            {"from_node": "start-node", "from_port": "output", "to_node": "log-node", "to_port": "input"},
            {"from_node": "log-node", "from_port": "output", "to_node": "end-node", "to_port": "input"}
        ]
    }
    """


@pytest.fixture
def multiple_jobs() -> List[Job]:
    """Provide multiple jobs for concurrency testing."""
    return [
        Job(
            job_id=f"job-{i:03d}",
            workflow_id=f"workflow-{i:03d}",
            workflow_name=f"Test Workflow {i}",
            workflow_json='{"nodes": [], "connections": []}',
            priority=i,
        )
        for i in range(5)
    ]


# =============================================================================
# Additional fixtures for RobotAgent and Audit testing
# =============================================================================


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def temp_checkpoint_dir(tmp_path: Path) -> Path:
    """Create temporary checkpoint directory."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir


@pytest.fixture
def temp_audit_dir(tmp_path: Path) -> Path:
    """Create temporary audit log directory."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir


@pytest.fixture
def mock_metrics_collector():
    """Provide a mock MetricsCollector."""
    metrics = Mock()
    metrics.start_resource_monitoring = AsyncMock()
    metrics.stop_resource_monitoring = AsyncMock()
    metrics.start_job = Mock()
    metrics.end_job = Mock()
    metrics.record_node = Mock()
    metrics.get_summary = Mock(
        return_value={
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
        }
    )
    return metrics


@pytest.fixture
def mock_audit_logger():
    """Provide a mock AuditLogger."""
    audit = Mock()
    audit.robot_started = Mock()
    audit.robot_stopped = Mock()
    audit.connection_established = Mock()
    audit.connection_lost = Mock()
    audit.job_started = Mock()
    audit.job_completed = Mock()
    audit.job_failed = Mock()
    audit.job_cancelled = Mock()
    audit.node_started = Mock()
    audit.node_completed = Mock()
    audit.node_failed = Mock()
    audit.checkpoint_saved = Mock()
    audit.checkpoint_restored = Mock()
    audit.circuit_state_changed = Mock()
    audit.log = Mock()
    audit.get_recent = Mock(return_value=[])
    audit.query = Mock(return_value=[])
    return audit


@pytest.fixture
def mock_resource_manager():
    """Provide a mock UnifiedResourceManager."""
    manager = AsyncMock()
    manager.start = AsyncMock()
    manager.stop = AsyncMock()
    manager.acquire_resources_for_job = AsyncMock(return_value={"browser": Mock()})
    manager.release_resources = AsyncMock()
    return manager


@pytest.fixture
def mock_db_pool():
    """Provide a mock database pool."""
    pool = AsyncMock()

    # Create a mock connection context manager
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)

    # Make acquire return async context manager
    async def acquire():
        return mock_conn

    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    return pool


@pytest.fixture
def sample_job_with_workflow():
    """Provide a sample job with a more complete workflow."""
    return Job(
        job_id=f"job-{uuid.uuid4().hex[:8]}",
        workflow_id=f"wf-{uuid.uuid4().hex[:8]}",
        workflow_name="Complete Test Workflow",
        workflow_json="""
        {
            "metadata": {
                "name": "Complete Test Workflow",
                "version": "1.0.0",
                "description": "A workflow for integration testing"
            },
            "nodes": [
                {"id": "start", "type": "StartNode", "properties": {}},
                {"id": "set-var", "type": "SetVariableNode", "properties": {"name": "result", "value": "success"}},
                {"id": "log", "type": "LogNode", "properties": {"message": "{{result}}"}},
                {"id": "end", "type": "EndNode", "properties": {}}
            ],
            "connections": [
                {"from_node": "start", "from_port": "exec_out", "to_node": "set-var", "to_port": "exec_in"},
                {"from_node": "set-var", "from_port": "exec_out", "to_node": "log", "to_port": "exec_in"},
                {"from_node": "log", "from_port": "exec_out", "to_node": "end", "to_port": "exec_in"}
            ]
        }
        """,
        variables={"initial_value": "test"},
        priority=5,
    )


@pytest.fixture
def mock_circuit_breaker():
    """Provide a mock CircuitBreaker."""
    from casare_rpa.robot.circuit_breaker import CircuitState

    cb = Mock()
    cb.name = "test-circuit"
    cb.state = CircuitState.CLOSED
    cb.is_closed = True
    cb.is_open = False
    cb.call = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    cb.reset = AsyncMock()
    cb.force_open = AsyncMock()
    cb.get_status = Mock(
        return_value={
            "name": "test-circuit",
            "state": "closed",
            "failure_count": 0,
        }
    )
    return cb
