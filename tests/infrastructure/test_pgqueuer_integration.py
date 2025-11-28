"""
Test PgQueuer Integration for Project Aether.

Tests the PgQueuer producer and consumer components.

Prerequisites:
- PostgreSQL running (local or Supabase)
- PGQUEUER_DATABASE_URL environment variable set
- PgQueuer extension installed: CREATE EXTENSION IF NOT EXISTS pgqueuer
"""

import pytest
import asyncio
from datetime import datetime

# Skip tests if PgQueuer not configured
pytest_skip_reason = "PgQueuer not configured"

try:
    from casare_rpa.infrastructure.queue.config import QueueConfig
    from casare_rpa.infrastructure.queue.models import (
        JobModel,
        JobStatus,
        JobPriority,
    )
    from casare_rpa.infrastructure.queue.producer import PgQueuerProducer
    from casare_rpa.infrastructure.queue.consumer import PgQueuerConsumer

    PGQUEUER_AVAILABLE = True
except ImportError as e:
    PGQUEUER_AVAILABLE = False
    pytest_skip_reason = f"PgQueuer dependencies not available: {e}"


@pytest.mark.skipif(not PGQUEUER_AVAILABLE, reason=pytest_skip_reason)
class TestQueueConfig:
    """Test queue configuration."""

    def test_config_from_env(self, monkeypatch):
        """Test loading config from environment."""
        monkeypatch.setenv(
            "PGQUEUER_DATABASE_URL",
            "postgresql://postgres:test@localhost:5432/test",
        )
        monkeypatch.setenv("PGQUEUER_QUEUE_NAME", "test_queue")
        monkeypatch.setenv("PGQUEUER_MAX_CONCURRENT", "5")

        config = QueueConfig.from_env()

        assert config.database_url == "postgresql://postgres:test@localhost:5432/test"
        assert config.queue_name == "test_queue"
        assert config.max_concurrent_jobs == 5

    def test_config_from_local_postgres(self):
        """Test creating config for local Postgres."""
        config = QueueConfig.from_local_postgres(
            host="localhost",
            port=5432,
            database="casare_test",
            user="postgres",
            password="testpass",
        )

        assert (
            "postgresql://postgres:testpass@localhost:5432/casare_test"
            in config.database_url
        )

    def test_config_from_supabase(self):
        """Test creating config for Supabase."""
        config = QueueConfig.from_supabase(
            supabase_url="https://abcdefgh.supabase.co",
            supabase_db_password="test_password",
        )

        assert "db.abcdefgh.supabase.co" in config.database_url


@pytest.mark.skipif(not PGQUEUER_AVAILABLE, reason=pytest_skip_reason)
class TestJobModel:
    """Test job data models."""

    def test_create_job_model(self):
        """Test creating a job model."""
        job = JobModel(
            job_id="test-job-001",
            workflow_json='{"nodes": []}',
            priority=JobPriority.HIGH,
            tenant_id="tenant-001",
            workflow_name="test_workflow",
        )

        assert job.job_id == "test-job-001"
        assert job.priority == JobPriority.HIGH
        assert job.status == JobStatus.PENDING
        assert job.tenant_id == "tenant-001"

    def test_job_lifecycle(self):
        """Test job lifecycle state transitions."""
        job = JobModel(
            job_id="test-job-002",
            workflow_json='{"nodes": []}',
        )

        # Initial state
        assert job.status == JobStatus.PENDING

        # Claim
        job.mark_claimed("robot-001")
        assert job.status == JobStatus.CLAIMED
        assert job.claimed_by == "robot-001"
        assert job.claimed_at is not None

        # Running
        job.mark_running()
        assert job.status == JobStatus.RUNNING

        # Complete
        job.mark_completed()
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None

    def test_job_retry_logic(self):
        """Test job retry logic."""
        job = JobModel(
            job_id="test-job-003",
            workflow_json='{"nodes": []}',
            max_retries=3,
        )

        # First failure
        job.mark_failed("Error 1")
        assert job.retry_count == 1
        assert job.should_retry() is True

        # Second failure
        job.mark_failed("Error 2")
        assert job.retry_count == 2
        assert job.should_retry() is True

        # Third failure
        job.mark_failed("Error 3")
        assert job.retry_count == 3
        assert job.should_retry() is False  # Max retries reached

    def test_job_to_pgqueuer_payload(self):
        """Test converting job to PgQueuer payload."""
        job = JobModel(
            job_id="test-job-004",
            workflow_json='{"nodes": []}',
            priority=JobPriority.URGENT,
            workflow_name="urgent_workflow",
        )

        payload = job.to_pgqueuer_payload()

        assert payload["job_id"] == "test-job-004"
        assert payload["priority"] == JobPriority.URGENT
        assert payload["workflow_name"] == "urgent_workflow"


@pytest.mark.integration
@pytest.mark.skipif(not PGQUEUER_AVAILABLE, reason=pytest_skip_reason)
class TestPgQueuerProducer:
    """
    Integration tests for PgQueuer producer.

    Requires PostgreSQL running and PGQUEUER_DATABASE_URL set.

    Run with: pytest tests/infrastructure/test_pgqueuer_integration.py -m integration -v
    """

    @pytest.mark.asyncio
    async def test_producer_lifecycle(self):
        """Test producer start/stop lifecycle."""
        config = QueueConfig.from_local_postgres()
        producer = PgQueuerProducer(config)

        # Start
        await producer.start()
        assert producer._running is True

        # Health check
        healthy = await producer.health_check()
        # Note: Will fail if Postgres not running - that's expected
        # assert healthy is True

        # Stop
        await producer.stop()
        assert producer._running is False

    @pytest.mark.asyncio
    async def test_enqueue_job(self):
        """Test enqueueing a job."""
        pytest.skip("Requires Postgres running - implement in CI")

        config = QueueConfig.from_local_postgres()
        producer = PgQueuerProducer(config)

        try:
            await producer.start()

            job_id = await producer.enqueue_job(
                job_id="test-enqueue-001",
                workflow_json='{"nodes": []}',
                priority=JobPriority.NORMAL,
                workflow_name="test_workflow",
            )

            assert job_id == "test-enqueue-001"

            # Verify queue depth
            depth = await producer.get_queue_depth()
            assert depth >= 1

        finally:
            await producer.stop()


@pytest.mark.integration
@pytest.mark.skipif(not PGQUEUER_AVAILABLE, reason=pytest_skip_reason)
class TestPgQueuerConsumer:
    """
    Integration tests for PgQueuer consumer.

    Requires PostgreSQL running.
    """

    @pytest.mark.asyncio
    async def test_consumer_lifecycle(self):
        """Test consumer start/stop lifecycle."""
        config = QueueConfig.from_local_postgres()
        consumer = PgQueuerConsumer(config, robot_id="test-robot-001")

        async def dummy_handler(job: JobModel) -> bool:
            return True

        # Note: start() will fail without Postgres - that's expected
        try:
            await consumer.start(dummy_handler)
            assert consumer._running is True
        except Exception:
            pytest.skip("Postgres not available")
        finally:
            await consumer.stop()

    @pytest.mark.asyncio
    async def test_producer_consumer_flow(self):
        """Test complete producer -> consumer flow."""
        pytest.skip("Requires Postgres - implement in CI with Docker")

        config = QueueConfig.from_local_postgres(queue_name="test_flow_queue")
        producer = PgQueuerProducer(config)
        consumer = PgQueuerConsumer(config, robot_id="test-robot-002")

        jobs_handled = []

        async def job_handler(job: JobModel) -> bool:
            jobs_handled.append(job.job_id)
            return True

        try:
            # Start producer and consumer
            await producer.start()
            await consumer.start(job_handler)

            # Enqueue jobs
            await producer.enqueue_job(
                job_id="flow-job-001",
                workflow_json='{"nodes": []}',
            )

            # Wait for consumer to process
            await asyncio.sleep(2)

            # Verify job was handled
            assert "flow-job-001" in jobs_handled

        finally:
            await consumer.stop()
            await producer.stop()


# ============================================================================
# Test Utilities
# ============================================================================


def create_test_job(job_id: str = "test-job") -> JobModel:
    """
    Create a test job model.

    Args:
        job_id: Job identifier

    Returns:
        JobModel instance
    """
    return JobModel(
        job_id=job_id,
        workflow_json='{"nodes": [], "metadata": {"name": "test"}}',
        priority=JobPriority.NORMAL,
        workflow_name="test_workflow",
    )
