# CasareRPA Testing Guide

This guide covers the testing strategy, test organization, and best practices for testing CasareRPA.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Organization](#test-organization)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Mocking and Fixtures](#mocking-and-fixtures)
7. [Testing Async Code](#testing-async-code)
8. [Testing Nodes](#testing-nodes)
9. [CI/CD Integration](#cicd-integration)

---

## Testing Philosophy

### Test Pyramid

```
       /\
      /  \
     / E2E \        <- Few, slow, high-confidence
    /--------\
   /          \
  / Integration \   <- Moderate, medium speed
 /--------------\
/                \
/     Unit       \  <- Many, fast, focused
------------------
```

| Type | Count | Speed | Scope |
|------|-------|-------|-------|
| Unit | Many | Fast (ms) | Single function/class |
| Integration | Moderate | Medium (s) | Multiple components |
| E2E | Few | Slow (min) | Full workflow |

### Testing Principles

1. **Test behavior, not implementation**
2. **One assertion per test (ideally)**
3. **Tests should be deterministic**
4. **Tests should be isolated**
5. **Tests should be fast**

---

## Test Organization

### Directory Structure

```
tests/
    conftest.py              # Shared fixtures
    unit/
        conftest.py          # Unit test fixtures
        domain/
            test_entities.py
            test_value_objects.py
        application/
            test_use_cases.py
            test_services.py
        infrastructure/
            test_persistence.py
        nodes/
            browser/
                test_click_node.py
            control_flow/
                test_if_node.py
    integration/
        conftest.py          # Integration fixtures
        test_orchestrator_robot.py
        test_job_queue.py
        test_trigger_system.py
    e2e/
        conftest.py          # E2E fixtures
        test_workflow_execution.py
        test_scheduled_jobs.py
    fixtures/
        workflows/
            simple_click.json
            data_extraction.json
        mocks/
            mock_page.py
```

### Naming Conventions

```python
# Test files
test_<module_name>.py

# Test classes
class Test<ClassName>:

# Test methods
def test_<method>_<scenario>_<expected_result>(self):

# Examples:
def test_submit_job_with_valid_workflow_returns_job(self):
def test_submit_job_with_invalid_id_raises_value_error(self):
def test_execute_when_element_not_found_retries_three_times(self):
```

---

## Unit Testing

### Testing Domain Entities

```python
# tests/unit/domain/test_job.py
import pytest
from datetime import datetime
from casare_rpa.infrastructure.orchestrator.api.models import Job, JobStatus, JobPriority

class TestJob:
    """Unit tests for Job entity."""

    def test_create_job_with_required_fields(self):
        """Test creating job with minimum required fields."""
        job = Job(
            id="job-123",
            workflow_id="wf-456",
            workflow_name="Test Workflow",
            robot_id="robot-789",
        )

        assert job.id == "job-123"
        assert job.status == JobStatus.PENDING
        assert job.priority == JobPriority.NORMAL

    def test_is_terminal_returns_true_for_completed(self):
        """Test is_terminal property for completed job."""
        job = Job(
            id="job-123",
            workflow_id="wf-456",
            workflow_name="Test",
            robot_id="robot-789",
            status=JobStatus.COMPLETED
        )

        assert job.is_terminal is True

    def test_is_terminal_returns_false_for_running(self):
        """Test is_terminal property for running job."""
        job = Job(
            id="job-123",
            workflow_id="wf-456",
            workflow_name="Test",
            robot_id="robot-789",
            status=JobStatus.RUNNING
        )

        assert job.is_terminal is False

    @pytest.mark.parametrize("duration_ms,expected", [
        (0, "-"),
        (5000, "5.0s"),
        (90000, "1.5m"),
        (7200000, "2.0h"),
    ])
    def test_duration_formatted(self, duration_ms, expected):
        """Test duration formatting for various values."""
        job = Job(
            id="job-123",
            workflow_id="wf-456",
            workflow_name="Test",
            robot_id="robot-789",
            duration_ms=duration_ms
        )

        assert job.duration_formatted == expected
```

### Testing Application Use Cases

```python
# tests/unit/application/test_submit_job_use_case.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from casare_rpa.infrastructure.orchestrator.server import OrchestratorEngine
from casare_rpa.infrastructure.orchestrator.api.models import Job, JobPriority

class TestSubmitJob:
    """Unit tests for job submission."""

    @pytest.fixture
    def mock_service(self):
        """Create mock orchestrator service."""
        service = MagicMock()
        service.connect = AsyncMock()
        service.get_robots = AsyncMock(return_value=[])
        service.get_schedules = AsyncMock(return_value=[])
        return service

    @pytest.fixture
    def engine(self, mock_service):
        """Create engine with mock service."""
        return OrchestratorEngine(service=mock_service)

    @pytest.mark.asyncio
    async def test_submit_job_creates_job_with_correct_priority(self, engine):
        """Test that submitted job has correct priority."""
        job = await engine.submit_job(
            workflow_id="wf-123",
            workflow_name="Test",
            workflow_json="{}",
            priority=JobPriority.HIGH
        )

        assert job is not None
        assert job.priority == JobPriority.HIGH
        assert job.status.value == "queued"

    @pytest.mark.asyncio
    async def test_submit_job_rejects_duplicate(self, engine):
        """Test that duplicate jobs are rejected."""
        # First submission
        job1 = await engine.submit_job(
            workflow_id="wf-123",
            workflow_name="Test",
            workflow_json="{}",
            check_duplicate=True
        )

        # Duplicate submission
        job2 = await engine.submit_job(
            workflow_id="wf-123",
            workflow_name="Test",
            workflow_json="{}",
            check_duplicate=True
        )

        assert job1 is not None
        assert job2 is None  # Rejected as duplicate
```

### Testing State Machines

```python
# tests/unit/domain/test_job_state_machine.py
import pytest
from casare_rpa.infrastructure.orchestrator.scheduling.job_assignment import JobStateMachine, JobStateError
from casare_rpa.infrastructure.orchestrator.api.models import Job, JobStatus

class TestJobStateMachine:
    """Unit tests for job state machine."""

    @pytest.fixture
    def pending_job(self):
        """Create a pending job."""
        return Job(
            id="job-123",
            workflow_id="wf-456",
            workflow_name="Test",
            robot_id="robot-789",
            status=JobStatus.PENDING
        )

    def test_valid_transition_pending_to_queued(self, pending_job):
        """Test valid transition from PENDING to QUEUED."""
        job = JobStateMachine.transition(pending_job, JobStatus.QUEUED)
        assert job.status == JobStatus.QUEUED

    def test_invalid_transition_pending_to_running_raises(self, pending_job):
        """Test invalid transition raises JobStateError."""
        with pytest.raises(JobStateError) as exc_info:
            JobStateMachine.transition(pending_job, JobStatus.RUNNING)

        assert "Invalid transition" in str(exc_info.value)

    def test_transition_to_running_sets_started_at(self, pending_job):
        """Test that transitioning to RUNNING sets started_at."""
        pending_job.status = JobStatus.QUEUED
        job = JobStateMachine.transition(pending_job, JobStatus.RUNNING)

        assert job.started_at is not None

    @pytest.mark.parametrize("terminal_status", [
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.TIMEOUT,
        JobStatus.CANCELLED,
    ])
    def test_terminal_states_are_recognized(self, terminal_status):
        """Test that terminal states are correctly identified."""
        assert JobStateMachine.is_terminal(terminal_status) is True

    def test_running_is_not_terminal(self):
        """Test that RUNNING is not a terminal state."""
        assert JobStateMachine.is_terminal(JobStatus.RUNNING) is False
```

---

## Integration Testing

### Testing Orchestrator-Robot Communication

```python
# tests/integration/test_orchestrator_robot.py
import pytest
import asyncio
from casare_rpa.infrastructure.orchestrator.server import OrchestratorServer
from casare_rpa.infrastructure.orchestrator.communication.websocket_server import MessageBuilder

class TestOrchestratorRobotCommunication:
    """Integration tests for orchestrator-robot communication."""

    @pytest.fixture
    async def server(self):
        """Start orchestrator server."""
        server = OrchestratorServer(host="127.0.0.1", port=0)  # Random port
        await server.start()
        yield server
        await server.stop()

    @pytest.fixture
    async def client(self, server):
        """Create WebSocket client."""
        import websockets
        port = server._port
        ws = await websockets.connect(f"ws://127.0.0.1:{port}")
        yield ws
        await ws.close()

    @pytest.mark.asyncio
    async def test_robot_registration(self, server, client):
        """Test robot registration flow."""
        # Send registration
        msg = MessageBuilder.register(
            robot_id="test-robot",
            robot_name="Test Robot",
            environment="test"
        )
        await client.send(msg.to_json())

        # Receive acknowledgment
        response = await asyncio.wait_for(client.recv(), timeout=5.0)
        data = json.loads(response)

        assert data["type"] == "register_ack"
        assert data["payload"]["success"] is True

        # Verify robot is registered
        assert server.is_robot_connected("test-robot")

    @pytest.mark.asyncio
    async def test_heartbeat_updates_last_seen(self, server, client):
        """Test that heartbeat updates robot last_seen."""
        # Register first
        await self._register_robot(client)

        # Send heartbeat
        msg = MessageBuilder.heartbeat(
            robot_id="test-robot",
            status="online",
            current_jobs=0
        )
        await client.send(msg.to_json())

        # Wait for processing
        await asyncio.sleep(0.1)

        # Verify heartbeat updated
        robot = server.get_robot("test-robot")
        assert robot is not None
        assert robot.last_heartbeat is not None

    async def _register_robot(self, client):
        """Helper to register a robot."""
        msg = MessageBuilder.register(
            robot_id="test-robot",
            robot_name="Test Robot",
            environment="test"
        )
        await client.send(msg.to_json())
        await client.recv()  # Consume ack
```

### Testing Job Queue

```python
# tests/integration/test_job_queue.py
import pytest
from casare_rpa.infrastructure.queue.pgqueuer_consumer import JobQueue
from casare_rpa.infrastructure.orchestrator.api.models import Job, JobStatus, JobPriority, Robot

class TestJobQueueIntegration:
    """Integration tests for job queue."""

    @pytest.fixture
    def queue(self):
        """Create job queue."""
        return JobQueue(
            dedup_window_seconds=1,
            default_timeout_seconds=10
        )

    @pytest.fixture
    def sample_jobs(self):
        """Create sample jobs with different priorities."""
        return [
            Job(id="low-1", workflow_id="wf", workflow_name="Low",
                robot_id="", priority=JobPriority.LOW),
            Job(id="high-1", workflow_id="wf", workflow_name="High",
                robot_id="", priority=JobPriority.HIGH),
            Job(id="critical-1", workflow_id="wf", workflow_name="Critical",
                robot_id="", priority=JobPriority.CRITICAL),
        ]

    @pytest.fixture
    def available_robot(self):
        """Create an available robot."""
        return Robot(
            id="robot-1",
            name="Test Robot",
            status="online",
            environment="default",
            max_concurrent_jobs=5,
            current_jobs=0
        )

    def test_dequeue_respects_priority_order(self, queue, sample_jobs, available_robot):
        """Test that higher priority jobs are dequeued first."""
        # Enqueue in random order
        for job in sample_jobs:
            queue.enqueue(job, check_duplicate=False)

        # Dequeue should return in priority order
        job1 = queue.dequeue(available_robot)
        assert job1.id == "critical-1"

        job2 = queue.dequeue(available_robot)
        assert job2.id == "high-1"

        job3 = queue.dequeue(available_robot)
        assert job3.id == "low-1"

    def test_dequeue_returns_none_for_busy_robot(self, queue, sample_jobs):
        """Test that busy robot gets no jobs."""
        queue.enqueue(sample_jobs[0], check_duplicate=False)

        busy_robot = Robot(
            id="robot-1",
            name="Busy Robot",
            status="online",
            max_concurrent_jobs=1,
            current_jobs=1  # At capacity
        )

        job = queue.dequeue(busy_robot)
        assert job is None

    def test_timeout_marks_job_as_timed_out(self, queue, available_robot):
        """Test that timed out jobs are marked correctly."""
        job = Job(id="timeout-1", workflow_id="wf", workflow_name="Test", robot_id="")
        queue.enqueue(job, check_duplicate=False)

        # Dequeue to start running
        running_job = queue.dequeue(available_robot)
        assert running_job is not None

        # Wait for timeout (queue has 10s default)
        import time
        time.sleep(11)

        # Check timeouts
        timed_out = queue.check_timeouts()
        assert "timeout-1" in timed_out

        # Verify status
        updated_job = queue.get_job("timeout-1")
        assert updated_job.status == JobStatus.TIMEOUT
```

---

## End-to-End Testing

### Testing Workflow Execution

```python
# tests/e2e/test_workflow_execution.py
import pytest
import asyncio
from casare_rpa.infrastructure.orchestrator.server import OrchestratorEngine
from casare_rpa.robot.agent import RobotAgent

class TestWorkflowExecution:
    """End-to-end tests for workflow execution."""

    @pytest.fixture
    async def orchestrator(self):
        """Start orchestrator."""
        engine = OrchestratorEngine()
        await engine.start()
        await engine.start_server(host="127.0.0.1", port=18765)
        yield engine
        await engine.stop()

    @pytest.fixture
    async def robot(self, orchestrator):
        """Start robot agent."""
        config = RobotConfig(
            robot_id="test-robot",
            robot_name="E2E Test Robot",
            connection=ConnectionConfig(
                orchestrator_url="ws://127.0.0.1:18765"
            )
        )
        agent = RobotAgent(config)

        # Start in background
        task = asyncio.create_task(agent.start())
        await asyncio.sleep(1)  # Wait for connection

        yield agent

        await agent.stop()
        task.cancel()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_simple_workflow_executes_successfully(self, orchestrator, robot):
        """Test that a simple workflow executes end-to-end."""
        workflow_json = '''
        {
            "nodes": [
                {"id": "start", "type": "basic.start"},
                {"id": "log", "type": "basic.log", "properties": {"message": "Hello E2E"}},
                {"id": "end", "type": "basic.end"}
            ],
            "connections": [
                {"source": "start:output", "target": "log:input"},
                {"source": "log:output", "target": "end:input"}
            ]
        }
        '''

        # Submit job
        job = await orchestrator.submit_job(
            workflow_id="e2e-test-wf",
            workflow_name="E2E Test",
            workflow_json=workflow_json
        )

        assert job is not None

        # Wait for completion
        for _ in range(30):  # 30 second timeout
            await asyncio.sleep(1)
            updated_job = orchestrator._job_queue.get_job(job.id)
            if updated_job and updated_job.is_terminal:
                break

        # Verify completion
        final_job = orchestrator._job_queue.get_job(job.id)
        assert final_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_scheduled_job_executes_on_time(self, orchestrator, robot):
        """Test that scheduled jobs execute on time."""
        from datetime import datetime, timedelta

        # Schedule job for 5 seconds from now
        run_time = datetime.utcnow() + timedelta(seconds=5)

        job = await orchestrator.submit_job(
            workflow_id="scheduled-test",
            workflow_name="Scheduled Test",
            workflow_json='{"nodes": [], "connections": []}',
            scheduled_time=run_time
        )

        # Should not be running yet
        await asyncio.sleep(1)
        current_job = orchestrator._job_queue.get_job(job.id)
        assert current_job.status in [JobStatus.PENDING, JobStatus.QUEUED]

        # Wait for scheduled time
        await asyncio.sleep(10)

        # Should have executed
        final_job = orchestrator._job_queue.get_job(job.id)
        assert final_job.is_terminal
```

---

## Mocking and Fixtures

### Common Fixtures

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_page():
    """Create mock Playwright page."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example")
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.screenshot = AsyncMock()
    return page

@pytest.fixture
def mock_browser(mock_page):
    """Create mock Playwright browser."""
    browser = AsyncMock()
    context = AsyncMock()
    context.new_page = AsyncMock(return_value=mock_page)
    browser.new_context = AsyncMock(return_value=context)
    return browser

@pytest.fixture
def sample_workflow():
    """Create sample workflow JSON."""
    return {
        "version": "3.0",
        "metadata": {"id": "wf-123", "name": "Test Workflow"},
        "nodes": [
            {"id": "start", "type": "basic.start", "position": {"x": 0, "y": 0}},
            {"id": "end", "type": "basic.end", "position": {"x": 200, "y": 0}}
        ],
        "connections": [
            {"source_node": "start", "source_port": "output",
             "target_node": "end", "target_port": "input"}
        ]
    }

@pytest.fixture
def execution_context(mock_page):
    """Create execution context for node testing."""
    return {
        "page": mock_page,
        "browser": MagicMock(),
        "variables": {},
        "job_id": "test-job-123"
    }
```

### Mocking External Services

```python
# tests/unit/conftest.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("casare_rpa.robot.connection.create_client") as mock:
        client = MagicMock()
        client.table.return_value.select.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )
        client.table.return_value.insert.return_value.execute = AsyncMock()
        client.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value='{"type": "heartbeat_ack"}')
    ws.close = AsyncMock()
    return ws
```

---

## Testing Async Code

### Async Test Setup

```python
# tests/conftest.py
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Or use pytest-asyncio's auto mode in pytest.ini/pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"
```

### Testing Async Functions

```python
# tests/unit/test_async_operations.py
import pytest
import asyncio

class TestAsyncOperations:
    """Tests for async operations."""

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test basic async function."""
        result = await some_async_function()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent async operations."""
        results = await asyncio.gather(
            operation1(),
            operation2(),
            operation3()
        )
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_timeout_behavior(self):
        """Test that operation times out correctly."""
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                slow_operation(),
                timeout=0.1
            )

    @pytest.mark.asyncio
    async def test_cancellation(self):
        """Test task cancellation."""
        task = asyncio.create_task(long_running_task())
        await asyncio.sleep(0.1)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
```

---

## Testing Nodes

### Node Test Template

```python
# tests/unit/nodes/browser/test_click_node.py
import pytest
from unittest.mock import AsyncMock
from casare_rpa.nodes.browser.click import ClickNode

class TestClickNode:
    """Unit tests for ClickNode."""

    @pytest.fixture
    def node(self):
        """Create click node with default properties."""
        node = ClickNode()
        node.set_property("selector", "#button")
        node.set_property("timeout", 30000)
        return node

    @pytest.fixture
    def mock_context(self, mock_page):
        """Create execution context."""
        return {
            "page": mock_page,
            "variables": {}
        }

    @pytest.mark.asyncio
    async def test_click_element_success(self, node, mock_context):
        """Test successful element click."""
        mock_context["page"].click = AsyncMock()

        result = await node.execute(mock_context)

        assert result.success is True
        mock_context["page"].click.assert_called_once_with("#button")

    @pytest.mark.asyncio
    async def test_click_element_not_found(self, node, mock_context):
        """Test click when element not found."""
        mock_context["page"].click = AsyncMock(
            side_effect=TimeoutError("Element not found")
        )

        result = await node.execute(mock_context)

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_click_with_variable_selector(self, node, mock_context):
        """Test click with variable in selector."""
        node.set_property("selector", "${button_selector}")
        mock_context["variables"]["button_selector"] = "#dynamic-button"

        result = await node.execute(mock_context)

        assert result.success is True
        mock_context["page"].click.assert_called_with("#dynamic-button")

    def test_validate_requires_selector(self):
        """Test that validation requires selector."""
        node = ClickNode()
        # No selector set

        is_valid, error = node.validate()

        assert is_valid is False
        assert "selector" in error.lower()
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ["3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          playwright install chromium

      - name: Run linting
        run: |
          black --check src/ tests/
          ruff check src/ tests/

      - name: Run unit tests
        run: pytest tests/unit -v --cov=src/casare_rpa

      - name: Run integration tests
        run: pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Test Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow",
    "e2e: marks tests as end-to-end",
    "integration: marks tests as integration tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src/casare_rpa"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

---

## Related Documentation

- [Contributing Guide](CONTRIBUTING.md)
- [System Overview](../architecture/SYSTEM_OVERVIEW.md)
- [API Reference](../api/REST_API_REFERENCE.md)
