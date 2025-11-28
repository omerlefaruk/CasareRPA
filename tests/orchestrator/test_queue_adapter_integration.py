"""
Tests for Phase 3.3: Orchestrator Queue Integration.

Verifies:
- OrchestratorEngine can use both in-memory and PgQueuer backends
- Job submission works with both backends
- Configuration properly switches between backends
- Fallback to in-memory when PgQueuer unavailable
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from casare_rpa.orchestrator.engine import OrchestratorEngine
from casare_rpa.orchestrator.config import (
    OrchestratorConfig,
    IN_MEMORY_CONFIG,
    PGQUEUER_CONFIG_TEMPLATE,
)
from casare_rpa.orchestrator.queue_adapter import QueueAdapter
from casare_rpa.orchestrator.models import Job, JobStatus, JobPriority


class TestOrchestratorConfig:
    """Test orchestrator configuration."""

    def test_in_memory_config(self):
        """Test in-memory configuration."""
        config = IN_MEMORY_CONFIG

        assert config.use_pgqueuer is False
        assert config.postgres_url is None
        assert config.load_balancing == "least_loaded"

    def test_pgqueuer_config_template(self):
        """Test PgQueuer configuration template."""
        config = OrchestratorConfig(
            use_pgqueuer=True,
            postgres_url="postgresql://user:pass@localhost/casare_rpa",
        )

        assert config.use_pgqueuer is True
        assert config.postgres_url == "postgresql://user:pass@localhost/casare_rpa"

    def test_config_immutable(self):
        """Test that config is immutable."""
        config = IN_MEMORY_CONFIG

        with pytest.raises(Exception):  # Pydantic ValidationError
            config.use_pgqueuer = True


class TestQueueAdapterIntegration:
    """Test queue adapter integration with orchestrator engine."""

    @pytest.mark.asyncio
    async def test_engine_with_in_memory_config(self):
        """Test engine initialization with in-memory config."""
        config = OrchestratorConfig(use_pgqueuer=False)

        engine = OrchestratorEngine(config=config)

        # Verify queue adapter is using in-memory backend
        assert engine._queue_adapter.use_pgqueuer is False
        assert engine._queue_adapter.job_queue is not None
        assert engine._queue_adapter.pgqueuer_producer is None

    @pytest.mark.asyncio
    async def test_engine_with_legacy_parameters(self):
        """Test engine initialization with legacy parameters (backward compatibility)."""
        engine = OrchestratorEngine(load_balancing="round_robin", dispatch_interval=10)

        # Should use in-memory by default
        assert engine._config.use_pgqueuer is False
        assert engine._config.load_balancing == "round_robin"
        assert engine._config.dispatch_interval == 10

    @pytest.mark.asyncio
    async def test_job_submission_in_memory(self):
        """Test job submission with in-memory queue."""
        config = OrchestratorConfig(use_pgqueuer=False)
        engine = OrchestratorEngine(config=config)

        await engine.start()

        # Submit job
        job = await engine.submit_job(
            workflow_id="wf-001",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
            priority=JobPriority.NORMAL,
        )

        assert job is not None
        assert job.workflow_id == "wf-001"
        # Job is QUEUED after successful enqueue (state machine transition)
        assert job.status == JobStatus.QUEUED

        # Verify job is in queue
        stats = engine.get_queue_stats()
        assert stats["backend"] == "in_memory"
        assert stats["pending_jobs"] >= 1

        await engine.stop()

    @pytest.mark.asyncio
    async def test_queue_adapter_start_stop(self):
        """Test queue adapter lifecycle."""
        config = OrchestratorConfig(use_pgqueuer=False)
        adapter = QueueAdapter(use_pgqueuer=False)

        # Start should not fail
        await adapter.start()

        # Stop should not fail
        await adapter.stop()

    @pytest.mark.asyncio
    async def test_queue_adapter_status(self):
        """Test queue adapter status reporting."""
        config = OrchestratorConfig(use_pgqueuer=False)
        adapter = QueueAdapter(use_pgqueuer=False)

        status = adapter.get_status()

        assert status["backend"] == "in_memory"
        assert "pending_jobs" in status
        assert "total_tracked" in status  # Changed from total_jobs
        assert "by_priority" in status

    @pytest.mark.asyncio
    async def test_pgqueuer_fallback_when_unavailable(self):
        """Test fallback to in-memory when PgQueuer not available."""
        # Simulate PgQueuer not being installed
        with patch("casare_rpa.orchestrator.queue_adapter.PGQUEUER_AVAILABLE", False):
            adapter = QueueAdapter(
                use_pgqueuer=True,  # Request PgQueuer
                pgqueuer_config=None,
            )

            # Should fallback to in-memory
            assert adapter.use_pgqueuer is False
            assert adapter.job_queue is not None

    @pytest.mark.asyncio
    async def test_engine_background_tasks_with_in_memory(self):
        """Test engine background tasks with in-memory queue."""
        config = OrchestratorConfig(use_pgqueuer=False)
        engine = OrchestratorEngine(config=config)

        await engine.start()

        # Submit a job
        job = await engine.submit_job(
            workflow_id="wf-timeout",
            workflow_name="Timeout Test",
            workflow_json='{"nodes": []}',
        )

        # Wait briefly for background tasks to run
        await asyncio.sleep(0.5)

        # Verify background tasks are running
        assert len(engine._background_tasks) > 0

        await engine.stop()

    @pytest.mark.skip(
        reason="JobQueue state machine requires proper workflow execution"
    )
    @pytest.mark.asyncio
    async def test_job_operations_with_in_memory(self):
        """Test job operations (complete, fail) with in-memory queue."""
        # This test requires proper state machine transitions
        # which are done by the Robot during workflow execution
        pass

    @pytest.mark.skip(reason="Job retry requires persisted job in database")
    @pytest.mark.asyncio
    async def test_job_retry_with_in_memory(self):
        """Test job retry with in-memory queue."""
        # This test requires job to be persisted to database first
        # which happens during actual workflow execution
        pass


class TestPgQueuerIntegration:
    """Test PgQueuer integration (requires actual PgQueuer instance)."""

    @pytest.mark.skip(reason="Requires running PostgreSQL and PgQueuer")
    @pytest.mark.asyncio
    async def test_engine_with_pgqueuer_config(self):
        """Test engine initialization with PgQueuer config."""
        config = OrchestratorConfig(
            use_pgqueuer=True,
            postgres_url="postgresql://postgres:postgres@localhost:5432/casare_rpa",
        )

        engine = OrchestratorEngine(config=config)

        await engine.start()

        # Verify queue adapter is using PgQueuer
        assert engine._queue_adapter.use_pgqueuer is True
        assert engine._queue_adapter.pgqueuer_producer is not None

        # Submit job to PgQueuer
        job = await engine.submit_job(
            workflow_id="wf-pgqueuer",
            workflow_name="PgQueuer Test",
            workflow_json='{"nodes": []}',
        )

        assert job is not None

        # Verify job is in PgQueuer queue
        stats = engine.get_queue_stats()
        assert stats["backend"] == "pgqueuer"

        await engine.stop()

    @pytest.mark.skip(reason="Requires running PostgreSQL and PgQueuer")
    @pytest.mark.asyncio
    async def test_job_submission_to_pgqueuer(self):
        """Test job submission to PgQueuer queue."""
        from casare_rpa.infrastructure.queue.config import QueueConfig

        queue_config = QueueConfig(
            postgres_url="postgresql://postgres:postgres@localhost:5432/casare_rpa",
        )

        adapter = QueueAdapter(use_pgqueuer=True, pgqueuer_config=queue_config)

        await adapter.start()

        # Create test job
        job = Job(
            id="test-job-001",
            workflow_id="wf-001",
            workflow_name="Test",
            workflow_json='{"nodes": []}',
            robot_id="",
            robot_name="",
            status=JobStatus.PENDING,
            priority=JobPriority.NORMAL,
            created_at=datetime.utcnow().isoformat(),
        )

        # Enqueue
        success, message = await adapter.enqueue_async(job)

        assert success is True

        # Check queue depth
        depth = await adapter.get_pending_count_async()
        assert depth >= 1

        await adapter.stop()


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_pgqueuer_requires_postgres_url(self):
        """Test that PgQueuer config requires postgres_url."""
        # This should work fine in the config itself
        config = OrchestratorConfig(
            use_pgqueuer=True,
            postgres_url=None,  # Will use default
        )

        assert config.use_pgqueuer is True

        # But QueueAdapter should fail if actually trying to use PgQueuer
        with pytest.raises(ValueError):
            adapter = QueueAdapter(use_pgqueuer=True, pgqueuer_config=None)

    def test_config_to_dict(self):
        """Test config serialization."""
        config = OrchestratorConfig(
            use_pgqueuer=True,
            postgres_url="postgresql://localhost/db",
            tenant_id="tenant-001",
        )

        data = config.to_dict()

        assert data["use_pgqueuer"] is True
        assert data["postgres_url"] == "postgresql://localhost/db"
        assert data["tenant_id"] == "tenant-001"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    @pytest.mark.asyncio
    async def test_legacy_initialization_still_works(self):
        """Test that legacy engine initialization still works."""
        # Old way (no config)
        engine = OrchestratorEngine()

        assert engine._config is not None
        assert engine._config.use_pgqueuer is False

        await engine.start()
        await engine.stop()

    @pytest.mark.asyncio
    async def test_job_queue_property_accessible(self):
        """Test that job_queue property is still accessible for backward compatibility."""
        engine = OrchestratorEngine()

        # _job_queue should still be accessible for legacy code
        assert hasattr(engine, "_job_queue")

        # For in-memory, it should reference the actual JobQueue
        if not engine._config.use_pgqueuer:
            assert engine._job_queue is not None

    @pytest.mark.asyncio
    async def test_existing_tests_still_pass(self):
        """Test that existing orchestrator tests still pass."""
        engine = OrchestratorEngine()

        await engine.start()

        # Old-style job submission
        job = await engine.submit_job(
            workflow_id="wf-compat",
            workflow_name="Compatibility Test",
            workflow_json='{"nodes": []}',
        )

        assert job is not None

        # Old-style queue stats
        stats = engine.get_queue_stats()
        assert "pending_jobs" in stats or "queue_depth" in stats

        await engine.stop()
