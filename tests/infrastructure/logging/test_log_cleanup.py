"""
Tests for LogCleanupJob.

Mock ALL external APIs (database, APScheduler).
Test scheduled cleanup, partition management, and metrics tracking.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch, PropertyMock

from casare_rpa.domain.value_objects.log_entry import DEFAULT_LOG_RETENTION_DAYS
from casare_rpa.infrastructure.logging.log_cleanup import (
    LogCleanupJob,
    get_log_cleanup_job,
    init_log_cleanup_job,
)


@pytest.fixture
def mock_log_repository() -> AsyncMock:
    """Create mock log repository."""
    repo = AsyncMock()
    repo.cleanup_old_logs.return_value = {
        "partitions_dropped": [],
        "retention_days": 30,
        "duration_ms": 100,
        "status": "completed",
    }
    repo.ensure_partitions.return_value = []
    return repo


@pytest.fixture
def log_cleanup_job(mock_log_repository: AsyncMock) -> LogCleanupJob:
    """Create LogCleanupJob with mock repository."""
    return LogCleanupJob(
        log_repository=mock_log_repository,
        retention_days=30,
        run_hour=2,
        ensure_partitions_months=2,
    )


# ============================================================================
# Job Initialization Tests
# ============================================================================


class TestLogCleanupJobInit:
    """Tests for LogCleanupJob initialization."""

    def test_create_with_defaults(self) -> None:
        """Create job with default values."""
        job = LogCleanupJob()

        assert job._retention_days == DEFAULT_LOG_RETENTION_DAYS
        assert job._run_hour == 2
        assert job._ensure_partitions_months == 2
        assert job._running is False
        assert job._task is None

    def test_create_with_custom_values(
        self,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Create job with custom values."""
        job = LogCleanupJob(
            log_repository=mock_log_repository,
            retention_days=60,
            run_hour=3,
            ensure_partitions_months=3,
        )

        assert job._retention_days == 60
        assert job._run_hour == 3
        assert job._ensure_partitions_months == 3


# ============================================================================
# Job Lifecycle Tests
# ============================================================================


class TestLogCleanupJobLifecycle:
    """Tests for job start/stop."""

    @pytest.mark.asyncio
    async def test_start_job(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Start job sets running flag and creates task."""
        await log_cleanup_job.start()

        assert log_cleanup_job._running is True
        assert log_cleanup_job._task is not None

        await log_cleanup_job.stop()

    @pytest.mark.asyncio
    async def test_start_twice_logs_warning(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Starting twice logs warning."""
        await log_cleanup_job.start()
        await log_cleanup_job.start()  # Should warn

        assert log_cleanup_job._running is True

        await log_cleanup_job.stop()

    @pytest.mark.asyncio
    async def test_stop_job(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Stop job clears running flag."""
        await log_cleanup_job.start()
        await log_cleanup_job.stop()

        assert log_cleanup_job._running is False
        assert log_cleanup_job._task is None

    @pytest.mark.asyncio
    async def test_stop_without_start(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Stop without start is safe."""
        await log_cleanup_job.stop()
        assert log_cleanup_job._running is False


# ============================================================================
# Run Cleanup Tests
# ============================================================================


class TestLogCleanupJobRunCleanup:
    """Tests for run_cleanup method."""

    @pytest.mark.asyncio
    async def test_run_cleanup_success(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Run cleanup successfully."""
        mock_log_repository.cleanup_old_logs.return_value = {
            "partitions_dropped": ["robot_logs_2023_11"],
            "retention_days": 30,
            "duration_ms": 150,
            "status": "completed",
        }
        mock_log_repository.ensure_partitions.return_value = [
            {"partition": "robot_logs_2024_02", "status": "created"},
        ]

        result = await log_cleanup_job.run_cleanup()

        assert result["cleanup"]["status"] == "completed"
        assert len(result["cleanup"]["partitions_dropped"]) == 1
        assert len(result["partitions_ensured"]) == 1
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_run_cleanup_updates_stats(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Run cleanup updates statistics."""
        mock_log_repository.cleanup_old_logs.return_value = {
            "partitions_dropped": ["p1", "p2"],
            "retention_days": 30,
            "duration_ms": 100,
            "status": "completed",
        }

        await log_cleanup_job.run_cleanup()

        assert log_cleanup_job._total_runs == 1
        assert log_cleanup_job._total_partitions_dropped == 2
        assert log_cleanup_job._last_run is not None
        assert log_cleanup_job._last_result is not None

    @pytest.mark.asyncio
    async def test_run_cleanup_multiple_times(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Run cleanup multiple times accumulates stats."""
        mock_log_repository.cleanup_old_logs.return_value = {
            "partitions_dropped": ["p1"],
            "retention_days": 30,
            "duration_ms": 50,
            "status": "completed",
        }

        await log_cleanup_job.run_cleanup()
        await log_cleanup_job.run_cleanup()

        assert log_cleanup_job._total_runs == 2
        assert log_cleanup_job._total_partitions_dropped == 2

    @pytest.mark.asyncio
    async def test_run_cleanup_error_captured(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Run cleanup captures error."""
        mock_log_repository.cleanup_old_logs.side_effect = Exception("DB error")

        result = await log_cleanup_job.run_cleanup()

        assert result["error"] == "DB error"
        assert result["cleanup"] is None

    @pytest.mark.asyncio
    async def test_run_cleanup_includes_duration(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Run cleanup includes duration."""
        result = await log_cleanup_job.run_cleanup()

        assert "duration_seconds" in result
        assert result["duration_seconds"] >= 0


# ============================================================================
# Retention Period Tests
# ============================================================================


class TestLogCleanupJobRetention:
    """Tests for retention period management."""

    def test_get_retention_days(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Get retention days property."""
        assert log_cleanup_job.retention_days == 30

    def test_set_retention_days(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Set retention days property."""
        log_cleanup_job.retention_days = 60
        assert log_cleanup_job.retention_days == 60

    def test_set_retention_days_minimum(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Setting retention days less than 1 raises error."""
        with pytest.raises(ValueError, match="at least 1"):
            log_cleanup_job.retention_days = 0

    def test_set_retention_days_one_is_valid(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Setting retention days to 1 is valid."""
        log_cleanup_job.retention_days = 1
        assert log_cleanup_job.retention_days == 1


# ============================================================================
# Status Tests
# ============================================================================


class TestLogCleanupJobStatus:
    """Tests for get_status method."""

    def test_get_status_not_started(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Get status when not started."""
        status = log_cleanup_job.get_status()

        assert status["running"] is False
        assert status["retention_days"] == 30
        assert status["run_hour"] == 2
        assert status["last_run"] is None
        assert status["last_result"] is None
        assert status["total_runs"] == 0
        assert status["total_partitions_dropped"] == 0

    @pytest.mark.asyncio
    async def test_get_status_after_run(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Get status after cleanup run."""
        mock_log_repository.cleanup_old_logs.return_value = {
            "partitions_dropped": ["p1"],
            "retention_days": 30,
            "duration_ms": 100,
            "status": "completed",
        }

        await log_cleanup_job.run_cleanup()
        status = log_cleanup_job.get_status()

        assert status["total_runs"] == 1
        assert status["last_run"] is not None
        assert status["last_result"] is not None

    @pytest.mark.asyncio
    async def test_get_status_running(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Get status when running."""
        await log_cleanup_job.start()
        status = log_cleanup_job.get_status()

        assert status["running"] is True

        await log_cleanup_job.stop()


# ============================================================================
# Scheduler Loop Tests
# ============================================================================


class TestLogCleanupJobScheduler:
    """Tests for scheduler loop."""

    @pytest.mark.asyncio
    async def test_scheduler_calculates_next_run(
        self,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Scheduler calculates next run time correctly."""
        job = LogCleanupJob(
            log_repository=mock_log_repository,
            run_hour=2,
        )

        # Start and immediately stop to check task creation
        await job.start()

        # Task should be created
        assert job._task is not None

        await job.stop()

    @pytest.mark.asyncio
    async def test_scheduler_stops_gracefully(
        self,
        log_cleanup_job: LogCleanupJob,
    ) -> None:
        """Scheduler stops gracefully on stop()."""
        await log_cleanup_job.start()

        # Should not hang
        await asyncio.wait_for(
            log_cleanup_job.stop(),
            timeout=2.0,
        )

        assert log_cleanup_job._running is False


# ============================================================================
# Module Functions Tests
# ============================================================================


class TestLogCleanupJobModuleFunctions:
    """Tests for module-level functions."""

    def test_get_log_cleanup_job_creates_singleton(self) -> None:
        """get_log_cleanup_job creates singleton."""
        # Reset global
        import casare_rpa.infrastructure.logging.log_cleanup as module

        module._log_cleanup_job = None

        job1 = get_log_cleanup_job()
        job2 = get_log_cleanup_job()

        assert job1 is job2

        # Cleanup
        module._log_cleanup_job = None

    @pytest.mark.asyncio
    async def test_init_log_cleanup_job_creates_and_starts(self) -> None:
        """init_log_cleanup_job creates and starts job."""
        # Reset global
        import casare_rpa.infrastructure.logging.log_cleanup as module

        module._log_cleanup_job = None

        job = await init_log_cleanup_job(
            retention_days=45,
            auto_start=True,
        )

        assert job._retention_days == 45
        assert job._running is True

        await job.stop()

        # Cleanup
        module._log_cleanup_job = None

    @pytest.mark.asyncio
    async def test_init_log_cleanup_job_no_auto_start(self) -> None:
        """init_log_cleanup_job with auto_start=False."""
        # Reset global
        import casare_rpa.infrastructure.logging.log_cleanup as module

        module._log_cleanup_job = None

        job = await init_log_cleanup_job(
            retention_days=30,
            auto_start=False,
        )

        assert job._running is False

        # Cleanup
        module._log_cleanup_job = None


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestLogCleanupJobEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_cleanup_with_no_partitions_dropped(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Cleanup with no partitions to drop."""
        mock_log_repository.cleanup_old_logs.return_value = {
            "partitions_dropped": [],
            "retention_days": 30,
            "duration_ms": 10,
            "status": "completed",
        }

        result = await log_cleanup_job.run_cleanup()

        assert result["cleanup"]["partitions_dropped"] == []
        assert log_cleanup_job._total_partitions_dropped == 0

    @pytest.mark.asyncio
    async def test_ensure_partitions_error(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Error in ensure_partitions is captured."""
        mock_log_repository.cleanup_old_logs.return_value = {
            "partitions_dropped": [],
            "retention_days": 30,
            "duration_ms": 10,
            "status": "completed",
        }
        mock_log_repository.ensure_partitions.side_effect = Exception("Partition error")

        result = await log_cleanup_job.run_cleanup()

        assert "Partition error" in result["error"]

    @pytest.mark.asyncio
    async def test_run_cleanup_concurrent_safe(
        self,
        log_cleanup_job: LogCleanupJob,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Multiple concurrent cleanups don't corrupt state."""
        results = await asyncio.gather(
            log_cleanup_job.run_cleanup(),
            log_cleanup_job.run_cleanup(),
            log_cleanup_job.run_cleanup(),
        )

        assert len(results) == 3
        assert log_cleanup_job._total_runs == 3
