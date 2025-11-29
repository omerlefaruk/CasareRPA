"""
Result Collection System for CasareRPA Orchestrator.
Handles job result collection, storage, and analytics.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

from loguru import logger

from casare_rpa.domain.orchestrator.entities import Job, JobStatus


@dataclass
class JobResult:
    """Complete result of a job execution."""

    job_id: str
    workflow_id: str
    workflow_name: str
    robot_id: str
    robot_name: str
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    progress: int = 100
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    error_type: str = ""
    stack_trace: str = ""
    failed_node: str = ""
    logs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if job completed successfully."""
        return self.status == JobStatus.COMPLETED

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "progress": self.progress,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "failed_node": self.failed_node,
            "logs": self.logs,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobResult":
        """Create from dictionary."""
        return cls(
            job_id=data.get("job_id", ""),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", ""),
            robot_id=data.get("robot_id", ""),
            robot_name=data.get("robot_name", ""),
            status=JobStatus(data.get("status", "completed")),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            duration_ms=data.get("duration_ms", 0),
            progress=data.get("progress", 100),
            result_data=data.get("result_data", {}),
            error_message=data.get("error_message", ""),
            error_type=data.get("error_type", ""),
            stack_trace=data.get("stack_trace", ""),
            failed_node=data.get("failed_node", ""),
            logs=data.get("logs", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ExecutionStatistics:
    """Statistics for job executions."""

    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    cancelled: int = 0
    timeout: int = 0
    total_duration_ms: int = 0
    min_duration_ms: int = 0
    max_duration_ms: int = 0
    avg_duration_ms: float = 0.0
    success_rate: float = 0.0

    # Time-based metrics
    executions_per_hour: float = 0.0
    throughput_per_minute: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_executions": self.total_executions,
            "successful": self.successful,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "timeout": self.timeout,
            "total_duration_ms": self.total_duration_ms,
            "min_duration_ms": self.min_duration_ms,
            "max_duration_ms": self.max_duration_ms,
            "avg_duration_ms": self.avg_duration_ms,
            "success_rate": self.success_rate,
            "executions_per_hour": self.executions_per_hour,
            "throughput_per_minute": self.throughput_per_minute,
        }


class ResultCollector:
    """
    Collects and processes job results.

    Handles:
    - Result reception from robots
    - Log aggregation
    - Statistics computation
    - Result persistence
    """

    def __init__(
        self,
        max_results: int = 10000,
        max_logs_per_job: int = 1000,
    ):
        """
        Initialize result collector.

        Args:
            max_results: Maximum results to keep in memory
            max_logs_per_job: Maximum log entries per job
        """
        self._max_results = max_results
        self._max_logs_per_job = max_logs_per_job

        # Storage
        self._results: Dict[str, JobResult] = {}
        self._results_order: List[str] = []  # For LRU eviction
        self._pending_logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Statistics cache
        self._stats_cache: Optional[ExecutionStatistics] = None
        self._stats_cache_time: Optional[datetime] = None
        self._stats_cache_ttl = timedelta(seconds=30)

        # Callbacks
        self._on_result_received: Optional[Callable] = None
        self._on_result_stored: Optional[Callable] = None

        logger.info(f"ResultCollector initialized (max_results={max_results})")

    def set_callbacks(
        self,
        on_result_received: Optional[Callable] = None,
        on_result_stored: Optional[Callable] = None,
    ):
        """Set callbacks for result events."""
        self._on_result_received = on_result_received
        self._on_result_stored = on_result_stored

    async def collect_result(
        self,
        job: Job,
        result_data: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
    ) -> JobResult:
        """
        Collect a successful job result.

        Args:
            job: Completed job
            result_data: Job output data
            duration_ms: Execution duration

        Returns:
            Created JobResult
        """
        job_result = JobResult(
            job_id=job.id,
            workflow_id=job.workflow_id,
            workflow_name=job.workflow_name,
            robot_id=job.robot_id,
            robot_name=job.robot_name,
            status=JobStatus.COMPLETED,
            started_at=job.started_at,
            completed_at=datetime.utcnow(),
            duration_ms=duration_ms or job.duration_ms,
            progress=100,
            result_data=result_data or {},
            logs=self._pending_logs.pop(job.id, []),
        )

        await self._store_result(job_result)
        return job_result

    async def collect_failure(
        self,
        job: Job,
        error_message: str,
        error_type: str = "ExecutionError",
        stack_trace: str = "",
        failed_node: str = "",
    ) -> JobResult:
        """
        Collect a failed job result.

        Args:
            job: Failed job
            error_message: Error description
            error_type: Error type/category
            stack_trace: Stack trace if available
            failed_node: Node that failed

        Returns:
            Created JobResult
        """
        job_result = JobResult(
            job_id=job.id,
            workflow_id=job.workflow_id,
            workflow_name=job.workflow_name,
            robot_id=job.robot_id,
            robot_name=job.robot_name,
            status=JobStatus.FAILED,
            started_at=job.started_at,
            completed_at=datetime.utcnow(),
            duration_ms=job.duration_ms,
            progress=job.progress,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            failed_node=failed_node,
            logs=self._pending_logs.pop(job.id, []),
        )

        await self._store_result(job_result)
        return job_result

    async def collect_cancellation(self, job: Job, reason: str = "") -> JobResult:
        """
        Collect a cancelled job result.

        Args:
            job: Cancelled job
            reason: Cancellation reason

        Returns:
            Created JobResult
        """
        job_result = JobResult(
            job_id=job.id,
            workflow_id=job.workflow_id,
            workflow_name=job.workflow_name,
            robot_id=job.robot_id,
            robot_name=job.robot_name,
            status=JobStatus.CANCELLED,
            started_at=job.started_at,
            completed_at=datetime.utcnow(),
            duration_ms=job.duration_ms,
            progress=job.progress,
            error_message=reason,
            logs=self._pending_logs.pop(job.id, []),
        )

        await self._store_result(job_result)
        return job_result

    async def collect_timeout(self, job: Job) -> JobResult:
        """
        Collect a timed-out job result.

        Args:
            job: Timed-out job

        Returns:
            Created JobResult
        """
        job_result = JobResult(
            job_id=job.id,
            workflow_id=job.workflow_id,
            workflow_name=job.workflow_name,
            robot_id=job.robot_id,
            robot_name=job.robot_name,
            status=JobStatus.TIMEOUT,
            started_at=job.started_at,
            completed_at=datetime.utcnow(),
            duration_ms=job.duration_ms,
            progress=job.progress,
            error_message="Job execution timed out",
            error_type="TimeoutError",
            logs=self._pending_logs.pop(job.id, []),
        )

        await self._store_result(job_result)
        return job_result

    def add_log(
        self,
        job_id: str,
        level: str,
        message: str,
        node_id: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a log entry for a job.

        Args:
            job_id: Job ID
            level: Log level
            message: Log message
            node_id: Associated node ID
            extra: Extra data
        """
        logs = self._pending_logs[job_id]

        if len(logs) >= self._max_logs_per_job:
            # Keep most recent logs
            logs.pop(0)

        logs.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
                "node_id": node_id,
                "extra": extra or {},
            }
        )

    def add_log_batch(self, job_id: str, entries: List[Dict[str, Any]]):
        """
        Add multiple log entries for a job.

        Args:
            job_id: Job ID
            entries: Log entries
        """
        for entry in entries:
            self.add_log(
                job_id=job_id,
                level=entry.get("level", "INFO"),
                message=entry.get("message", ""),
                node_id=entry.get("node_id", ""),
                extra=entry.get("extra"),
            )

    async def _store_result(self, result: JobResult):
        """Store a job result."""
        # Notify callback
        if self._on_result_received:
            try:
                callback_result = self._on_result_received(result)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
            except Exception as e:
                logger.error(f"Result received callback error: {e}")

        # Store
        if result.job_id in self._results:
            # Update existing
            self._results_order.remove(result.job_id)
        else:
            # Check capacity
            while len(self._results) >= self._max_results:
                oldest_id = self._results_order.pop(0)
                del self._results[oldest_id]

        self._results[result.job_id] = result
        self._results_order.append(result.job_id)

        # Invalidate stats cache
        self._stats_cache = None

        # Notify stored callback
        if self._on_result_stored:
            try:
                callback_result = self._on_result_stored(result)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
            except Exception as e:
                logger.error(f"Result stored callback error: {e}")

        logger.debug(f"Stored result for job {result.job_id[:8]}")

    def get_result(self, job_id: str) -> Optional[JobResult]:
        """Get a job result by ID."""
        return self._results.get(job_id)

    def get_results_by_workflow(self, workflow_id: str) -> List[JobResult]:
        """Get all results for a workflow."""
        return [r for r in self._results.values() if r.workflow_id == workflow_id]

    def get_results_by_robot(self, robot_id: str) -> List[JobResult]:
        """Get all results for a robot."""
        return [r for r in self._results.values() if r.robot_id == robot_id]

    def get_recent_results(self, limit: int = 100) -> List[JobResult]:
        """Get most recent results."""
        recent_ids = self._results_order[-limit:]
        return [self._results[job_id] for job_id in reversed(recent_ids)]

    def get_failed_results(self, limit: int = 100) -> List[JobResult]:
        """Get recent failed results."""
        failed = [
            r
            for r in self._results.values()
            if r.status in (JobStatus.FAILED, JobStatus.TIMEOUT)
        ]
        failed.sort(key=lambda r: r.completed_at or datetime.min, reverse=True)
        return failed[:limit]

    def get_statistics(
        self,
        workflow_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> ExecutionStatistics:
        """
        Get execution statistics.

        Args:
            workflow_id: Filter by workflow
            robot_id: Filter by robot
            since: Only include results after this time

        Returns:
            Execution statistics
        """
        # Check cache (only for unfiltered stats)
        if not workflow_id and not robot_id and not since:
            if self._stats_cache and self._stats_cache_time:
                if datetime.utcnow() - self._stats_cache_time < self._stats_cache_ttl:
                    return self._stats_cache

        # Filter results
        results = list(self._results.values())

        if workflow_id:
            results = [r for r in results if r.workflow_id == workflow_id]
        if robot_id:
            results = [r for r in results if r.robot_id == robot_id]
        if since:
            results = [r for r in results if r.completed_at and r.completed_at >= since]

        if not results:
            return ExecutionStatistics()

        # Calculate statistics
        successful = sum(1 for r in results if r.status == JobStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == JobStatus.FAILED)
        cancelled = sum(1 for r in results if r.status == JobStatus.CANCELLED)
        timeout = sum(1 for r in results if r.status == JobStatus.TIMEOUT)

        durations = [r.duration_ms for r in results if r.duration_ms > 0]

        stats = ExecutionStatistics(
            total_executions=len(results),
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            timeout=timeout,
            total_duration_ms=sum(durations),
            min_duration_ms=min(durations) if durations else 0,
            max_duration_ms=max(durations) if durations else 0,
            avg_duration_ms=statistics.mean(durations) if durations else 0.0,
            success_rate=successful / len(results) * 100 if results else 0.0,
        )

        # Calculate throughput
        if results:
            first_time = (
                min(r.started_at for r in results if r.started_at)
                if any(r.started_at for r in results)
                else None
            )
            last_time = (
                max(r.completed_at for r in results if r.completed_at)
                if any(r.completed_at for r in results)
                else None
            )

            if first_time and last_time and last_time > first_time:
                hours = (last_time - first_time).total_seconds() / 3600
                if hours > 0:
                    stats.executions_per_hour = len(results) / hours
                    stats.throughput_per_minute = len(results) / (hours * 60)

        # Cache if unfiltered
        if not workflow_id and not robot_id and not since:
            self._stats_cache = stats
            self._stats_cache_time = datetime.utcnow()

        return stats

    def get_hourly_stats(
        self,
        hours: int = 24,
        workflow_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get hourly statistics.

        Args:
            hours: Number of hours to look back
            workflow_id: Filter by workflow

        Returns:
            List of hourly statistics
        """
        now = datetime.utcnow()
        hourly_data = []

        for i in range(hours):
            hour_start = now - timedelta(hours=i + 1)
            hour_end = now - timedelta(hours=i)

            results = [
                r
                for r in self._results.values()
                if r.completed_at and hour_start <= r.completed_at < hour_end
            ]

            if workflow_id:
                results = [r for r in results if r.workflow_id == workflow_id]

            successful = sum(1 for r in results if r.status == JobStatus.COMPLETED)
            failed = sum(1 for r in results if r.status == JobStatus.FAILED)

            hourly_data.append(
                {
                    "hour": hour_start.strftime("%Y-%m-%d %H:00"),
                    "total": len(results),
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / len(results) * 100 if results else 0.0,
                }
            )

        return list(reversed(hourly_data))

    def get_workflow_stats(self) -> Dict[str, ExecutionStatistics]:
        """Get statistics per workflow."""
        workflows: Dict[str, List[JobResult]] = defaultdict(list)

        for result in self._results.values():
            workflows[result.workflow_id].append(result)

        stats_map = {}
        for workflow_id in workflows:
            stats_map[workflow_id] = self.get_statistics(workflow_id=workflow_id)

        return stats_map

    def get_robot_stats(self) -> Dict[str, ExecutionStatistics]:
        """Get statistics per robot."""
        robots: Dict[str, List[JobResult]] = defaultdict(list)

        for result in self._results.values():
            robots[result.robot_id].append(result)

        stats_map = {}
        for robot_id in robots:
            stats_map[robot_id] = self.get_statistics(robot_id=robot_id)

        return stats_map

    def clear(self):
        """Clear all results."""
        self._results.clear()
        self._results_order.clear()
        self._pending_logs.clear()
        self._stats_cache = None
        logger.info("Result collector cleared")

    @property
    def result_count(self) -> int:
        """Get number of stored results."""
        return len(self._results)

    @property
    def pending_log_count(self) -> int:
        """Get number of jobs with pending logs."""
        return len(self._pending_logs)


class ResultExporter:
    """
    Exports job results to various formats.
    """

    @staticmethod
    def to_json(results: List[JobResult], pretty: bool = False) -> str:
        """Export results to JSON."""
        data = [r.to_dict() for r in results]
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    @staticmethod
    def to_csv(results: List[JobResult]) -> str:
        """Export results to CSV."""
        if not results:
            return ""

        headers = [
            "job_id",
            "workflow_id",
            "workflow_name",
            "robot_id",
            "robot_name",
            "status",
            "started_at",
            "completed_at",
            "duration_ms",
            "error_message",
            "error_type",
        ]

        lines = [",".join(headers)]

        for r in results:
            values = [
                r.job_id,
                r.workflow_id,
                r.workflow_name,
                r.robot_id,
                r.robot_name,
                r.status.value,
                r.started_at.isoformat() if r.started_at else "",
                r.completed_at.isoformat() if r.completed_at else "",
                str(r.duration_ms),
                r.error_message.replace(",", ";").replace("\n", " "),
                r.error_type,
            ]
            lines.append(",".join(values))

        return "\n".join(lines)

    @staticmethod
    def to_summary(results: List[JobResult]) -> Dict[str, Any]:
        """Generate a summary report."""
        if not results:
            return {"total": 0}

        successful = sum(1 for r in results if r.status == JobStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == JobStatus.FAILED)
        cancelled = sum(1 for r in results if r.status == JobStatus.CANCELLED)
        timeout = sum(1 for r in results if r.status == JobStatus.TIMEOUT)

        durations = [r.duration_ms for r in results if r.duration_ms > 0]

        return {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "cancelled": cancelled,
            "timeout": timeout,
            "success_rate": successful / len(results) * 100 if results else 0.0,
            "avg_duration_ms": statistics.mean(durations) if durations else 0,
            "total_duration_ms": sum(durations),
            "unique_workflows": len(set(r.workflow_id for r in results)),
            "unique_robots": len(set(r.robot_id for r in results)),
        }
