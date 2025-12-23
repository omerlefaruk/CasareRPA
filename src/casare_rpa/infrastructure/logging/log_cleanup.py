"""
LogCleanupJob - Scheduled Job for Log Retention Enforcement.

Runs daily to delete logs older than the retention period and ensure
future partitions exist. Uses PostgreSQL partitioning for efficient
bulk cleanup.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from casare_rpa.domain.value_objects.log_entry import DEFAULT_LOG_RETENTION_DAYS
from casare_rpa.infrastructure.persistence.repositories.log_repository import (
    LogRepository,
)


class LogCleanupJob:
    """
    Scheduled job for log retention management.

    Features:
    - Run daily to drop old log partitions
    - Ensure future partitions exist
    - Track cleanup statistics
    - Configurable retention period

    Usage:
        job = LogCleanupJob(retention_days=30)
        await job.start()  # Runs in background

        # Or run manually
        result = await job.run_cleanup()
    """

    def __init__(
        self,
        log_repository: LogRepository | None = None,
        retention_days: int = DEFAULT_LOG_RETENTION_DAYS,
        run_hour: int = 2,  # Run at 2 AM
        ensure_partitions_months: int = 2,
    ) -> None:
        """
        Initialize log cleanup job.

        Args:
            log_repository: Repository for log operations.
            retention_days: Number of days to retain logs.
            run_hour: Hour of day to run cleanup (0-23).
            ensure_partitions_months: Months ahead to create partitions.
        """
        self._repository = log_repository or LogRepository()
        self._retention_days = retention_days
        self._run_hour = run_hour
        self._ensure_partitions_months = ensure_partitions_months

        self._running = False
        self._task: asyncio.Task | None = None

        # Statistics
        self._last_run: datetime | None = None
        self._last_result: dict[str, Any] | None = None
        self._total_runs = 0
        self._total_partitions_dropped = 0

    async def start(self) -> None:
        """Start the cleanup job scheduler."""
        if self._running:
            logger.warning("LogCleanupJob already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(
            f"LogCleanupJob started (retention={self._retention_days} days, "
            f"run_hour={self._run_hour}:00)"
        )

    async def stop(self) -> None:
        """Stop the cleanup job scheduler."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info(
            f"LogCleanupJob stopped. "
            f"Total runs: {self._total_runs}, "
            f"Total partitions dropped: {self._total_partitions_dropped}"
        )

    async def run_cleanup(self) -> dict[str, Any]:
        """
        Run cleanup manually.

        Returns:
            Dictionary with cleanup results.
        """
        start_time = datetime.now(UTC)
        result = {
            "start_time": start_time.isoformat(),
            "retention_days": self._retention_days,
            "cleanup": None,
            "partitions_ensured": None,
            "error": None,
        }

        try:
            # Step 1: Drop old partitions
            cleanup_result = await self._repository.cleanup_old_logs(self._retention_days)
            result["cleanup"] = cleanup_result

            dropped_count = len(cleanup_result.get("partitions_dropped", []))
            self._total_partitions_dropped += dropped_count

            # Step 2: Ensure future partitions exist
            partitions = await self._repository.ensure_partitions(self._ensure_partitions_months)
            result["partitions_ensured"] = partitions

            # Update statistics
            self._last_run = start_time
            self._last_result = result
            self._total_runs += 1

            duration = (datetime.now(UTC) - start_time).total_seconds()
            result["duration_seconds"] = duration

            logger.info(
                f"Log cleanup completed in {duration:.2f}s. "
                f"Dropped {dropped_count} partitions, "
                f"ensured {len(partitions)} partitions"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Log cleanup failed: {e}")

        return result

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop - runs daily at configured hour."""
        while self._running:
            try:
                # Calculate time until next run
                now = datetime.now(UTC)
                next_run = now.replace(
                    hour=self._run_hour,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

                # If we've passed today's run time, schedule for tomorrow
                if next_run <= now:
                    next_run += timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()

                logger.debug(
                    f"Next log cleanup scheduled for {next_run.isoformat()} "
                    f"(in {wait_seconds / 3600:.1f} hours)"
                )

                # Wait until scheduled time (with periodic checks for shutdown)
                while wait_seconds > 0 and self._running:
                    sleep_time = min(wait_seconds, 60.0)  # Check every minute
                    await asyncio.sleep(sleep_time)
                    wait_seconds -= sleep_time

                # Run cleanup if still running
                if self._running:
                    await self.run_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)

    def get_status(self) -> dict[str, Any]:
        """
        Get job status and statistics.

        Returns:
            Dictionary with status information.
        """
        return {
            "running": self._running,
            "retention_days": self._retention_days,
            "run_hour": self._run_hour,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "last_result": self._last_result,
            "total_runs": self._total_runs,
            "total_partitions_dropped": self._total_partitions_dropped,
        }

    @property
    def retention_days(self) -> int:
        """Get retention period in days."""
        return self._retention_days

    @retention_days.setter
    def retention_days(self, value: int) -> None:
        """
        Set retention period.

        Args:
            value: Days to retain logs (minimum 1).
        """
        if value < 1:
            raise ValueError("Retention days must be at least 1")
        self._retention_days = value
        logger.info(f"Log retention updated to {value} days")


# Singleton instance
_log_cleanup_job: LogCleanupJob | None = None


def get_log_cleanup_job() -> LogCleanupJob:
    """
    Get or create the singleton LogCleanupJob.

    Returns:
        LogCleanupJob instance.
    """
    global _log_cleanup_job
    if _log_cleanup_job is None:
        _log_cleanup_job = LogCleanupJob()
    return _log_cleanup_job


async def init_log_cleanup_job(
    retention_days: int = DEFAULT_LOG_RETENTION_DAYS,
    auto_start: bool = True,
) -> LogCleanupJob:
    """
    Initialize and optionally start the log cleanup job.

    Args:
        retention_days: Days to retain logs.
        auto_start: Whether to start the scheduler.

    Returns:
        LogCleanupJob instance.
    """
    global _log_cleanup_job
    if _log_cleanup_job is None:
        _log_cleanup_job = LogCleanupJob(retention_days=retention_days)

    if auto_start and not _log_cleanup_job._running:
        await _log_cleanup_job.start()

    return _log_cleanup_job


__all__ = [
    "LogCleanupJob",
    "get_log_cleanup_job",
    "init_log_cleanup_job",
]
