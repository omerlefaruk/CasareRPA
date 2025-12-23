"""
CasareRPA Infrastructure: Metric Storage

Storage adapters for metrics data:
- In-memory storage (default, for development)
- Job record storage
- Workflow metrics cache
- Robot metrics cache
- Error tracking storage
- Healing metrics storage
"""

from __future__ import annotations

import statistics
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Generic, List, Optional, TypeVar

from loguru import logger

from casare_rpa.infrastructure.analytics.aggregation_strategies import (
    TimeSeriesDataPoint,
)

T = TypeVar("T")


@dataclass
class JobRecord:
    """Record of a job execution for analytics."""

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_version: str
    robot_id: str
    status: str
    duration_ms: float
    queue_wait_ms: float
    started_at: datetime
    completed_at: datetime | None
    error_type: str | None
    error_message: str | None
    nodes_executed: int
    healing_attempts: int
    healing_successes: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "robot_id": self.robot_id,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "queue_wait_ms": self.queue_wait_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "nodes_executed": self.nodes_executed,
            "healing_attempts": self.healing_attempts,
            "healing_successes": self.healing_successes,
        }


@dataclass
class WorkflowMetricsData:
    """Cached metrics for a workflow."""

    workflow_id: str
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    timeout_executions: int = 0
    last_execution: datetime | None = None
    first_execution: datetime | None = None
    error_breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.failed_executions / self.total_executions) * 100

    def update_from_record(self, record: JobRecord) -> None:
        """Update metrics from a job record."""
        self.total_executions += 1

        if record.status == "completed":
            self.successful_executions += 1
        elif record.status == "failed":
            self.failed_executions += 1
            if record.error_type:
                self.error_breakdown[record.error_type] = (
                    self.error_breakdown.get(record.error_type, 0) + 1
                )
        elif record.status == "cancelled":
            self.cancelled_executions += 1
        elif record.status == "timeout":
            self.timeout_executions += 1

        self.last_execution = record.completed_at
        if self.first_execution is None:
            self.first_execution = record.started_at


@dataclass
class RobotMetricsData:
    """Cached metrics for a robot."""

    robot_id: str
    robot_name: str
    total_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    total_busy_seconds: float = 0.0
    total_idle_seconds: float = 0.0
    total_offline_seconds: float = 0.0
    avg_job_duration_ms: float = 0.0
    jobs_per_hour: float = 0.0
    current_status: str = "offline"
    last_active: datetime | None = None

    @property
    def utilization_percent(self) -> float:
        """Calculate utilization percentage."""
        total = self.total_busy_seconds + self.total_idle_seconds
        if total == 0:
            return 0.0
        return (self.total_busy_seconds / total) * 100

    @property
    def success_rate(self) -> float:
        """Calculate job success rate."""
        if self.total_jobs == 0:
            return 0.0
        return (self.successful_jobs / self.total_jobs) * 100

    @property
    def availability_percent(self) -> float:
        """Calculate availability percentage."""
        total = self.total_busy_seconds + self.total_idle_seconds + self.total_offline_seconds
        if total == 0:
            return 0.0
        online = self.total_busy_seconds + self.total_idle_seconds
        return (online / total) * 100

    def update_from_record(self, record: JobRecord) -> None:
        """Update metrics from a job record."""
        self.total_jobs += 1

        if record.status == "completed":
            self.successful_jobs += 1
        elif record.status == "failed":
            self.failed_jobs += 1

        self.total_busy_seconds += record.duration_ms / 1000
        self.last_active = record.completed_at

        # Running average for job duration
        self.avg_job_duration_ms = (
            self.avg_job_duration_ms * (self.total_jobs - 1) + record.duration_ms
        ) / self.total_jobs


class MetricStorage(ABC, Generic[T]):
    """Base class for metric storage adapters."""

    @abstractmethod
    def add(self, item: T) -> None:
        """Add an item to storage."""
        pass

    @abstractmethod
    def get_all(self) -> list[T]:
        """Get all items."""
        pass

    @abstractmethod
    def get_filtered(
        self,
        filter_func: Callable[[T], bool],
    ) -> list[T]:
        """Get filtered items."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all items."""
        pass


class InMemoryJobRecordStorage(MetricStorage[JobRecord]):
    """
    In-memory storage for job execution records.

    Thread-safe with automatic pruning.
    """

    def __init__(self, max_records: int = 100000):
        """
        Initialize storage.

        Args:
            max_records: Maximum records to retain.
        """
        self._records: list[JobRecord] = []
        self._lock = Lock()
        self._max_records = max_records

    def add(self, record: JobRecord) -> None:
        """Add a job record."""
        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records :]

    def get_all(self) -> list[JobRecord]:
        """Get all records."""
        with self._lock:
            return list(self._records)

    def get_filtered(
        self,
        filter_func: Callable[[JobRecord], bool],
    ) -> list[JobRecord]:
        """Get filtered records."""
        with self._lock:
            return [r for r in self._records if filter_func(r)]

    def get_by_time_range(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[JobRecord]:
        """Get records within time range."""
        end_time = end_time or datetime.now(UTC)
        start_time = start_time or (end_time - timedelta(hours=24))

        return self.get_filtered(lambda r: start_time <= r.started_at <= end_time)

    def get_by_workflow(
        self,
        workflow_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[JobRecord]:
        """Get records for a specific workflow."""
        records = self.get_by_time_range(start_time, end_time)
        return [r for r in records if r.workflow_id == workflow_id]

    def get_by_robot(
        self,
        robot_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[JobRecord]:
        """Get records for a specific robot."""
        records = self.get_by_time_range(start_time, end_time)
        return [r for r in records if r.robot_id == robot_id]

    def get_by_version(
        self,
        workflow_id: str,
        version: str,
    ) -> list[JobRecord]:
        """Get records for a specific workflow version."""
        return self.get_filtered(
            lambda r: r.workflow_id == workflow_id and r.workflow_version == version
        )

    def clear(self) -> None:
        """Clear all records."""
        with self._lock:
            self._records.clear()


class WorkflowMetricsCache:
    """
    Cache for workflow metrics.

    Maintains aggregated metrics per workflow.
    """

    def __init__(self, max_duration_samples: int = 10000):
        """
        Initialize cache.

        Args:
            max_duration_samples: Max duration samples per workflow.
        """
        self._metrics: dict[str, WorkflowMetricsData] = {}
        self._durations: dict[str, list[float]] = defaultdict(list)
        self._hourly_data: dict[str, list[TimeSeriesDataPoint]] = defaultdict(list)
        self._lock = Lock()
        self._max_duration_samples = max_duration_samples

    def update(self, record: JobRecord) -> None:
        """Update cache from a job record."""
        with self._lock:
            wf_id = record.workflow_id

            # Initialize if needed
            if wf_id not in self._metrics:
                self._metrics[wf_id] = WorkflowMetricsData(
                    workflow_id=wf_id,
                    workflow_name=record.workflow_name,
                )

            # Update metrics
            self._metrics[wf_id].update_from_record(record)

            # Update durations
            self._durations[wf_id].append(record.duration_ms)
            if len(self._durations[wf_id]) > self._max_duration_samples:
                self._durations[wf_id] = self._durations[wf_id][-self._max_duration_samples :]

            # Update hourly data
            self._update_hourly(wf_id, record)

    def _update_hourly(self, workflow_id: str, record: JobRecord) -> None:
        """Update hourly time series data."""
        hour = record.started_at.replace(minute=0, second=0, microsecond=0)
        hourly = self._hourly_data[workflow_id]

        if hourly and hourly[-1].timestamp == hour:
            # Update existing bucket
            hourly[-1].count += 1
            hourly[-1].value = (
                hourly[-1].value * (hourly[-1].count - 1) + record.duration_ms
            ) / hourly[-1].count
        else:
            # New bucket
            hourly.append(
                TimeSeriesDataPoint(
                    timestamp=hour,
                    value=record.duration_ms,
                    count=1,
                )
            )

        # Keep 7 days of hourly data
        if len(hourly) > 168:
            self._hourly_data[workflow_id] = hourly[-168:]

    def get(self, workflow_id: str) -> WorkflowMetricsData | None:
        """Get metrics for a workflow."""
        with self._lock:
            return self._metrics.get(workflow_id)

    def get_all(self) -> list[WorkflowMetricsData]:
        """Get all workflow metrics."""
        with self._lock:
            return list(self._metrics.values())

    def get_durations(self, workflow_id: str) -> list[float]:
        """Get duration samples for a workflow."""
        with self._lock:
            return list(self._durations.get(workflow_id, []))

    def get_hourly_data(
        self,
        workflow_id: str,
        limit: int = 24,
    ) -> list[TimeSeriesDataPoint]:
        """Get hourly time series data."""
        with self._lock:
            data = self._hourly_data.get(workflow_id, [])
            return data[-limit:]

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._metrics.clear()
            self._durations.clear()
            self._hourly_data.clear()


class RobotMetricsCache:
    """
    Cache for robot metrics.

    Maintains aggregated metrics per robot.
    """

    def __init__(self):
        """Initialize cache."""
        self._metrics: dict[str, RobotMetricsData] = {}
        self._lock = Lock()

    def update(self, record: JobRecord) -> None:
        """Update cache from a job record."""
        if not record.robot_id:
            return

        with self._lock:
            robot_id = record.robot_id

            if robot_id not in self._metrics:
                self._metrics[robot_id] = RobotMetricsData(
                    robot_id=robot_id,
                    robot_name=robot_id,
                )

            self._metrics[robot_id].update_from_record(record)

    def get(self, robot_id: str) -> RobotMetricsData | None:
        """Get metrics for a robot."""
        with self._lock:
            return self._metrics.get(robot_id)

    def get_all(self) -> list[RobotMetricsData]:
        """Get all robot metrics."""
        with self._lock:
            return list(self._metrics.values())

    def update_status(self, robot_id: str, status: str) -> None:
        """Update robot status."""
        with self._lock:
            if robot_id in self._metrics:
                self._metrics[robot_id].current_status = status

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._metrics.clear()


class ErrorTrackingStorage:
    """
    Storage for error tracking.

    Tracks error counts globally and per workflow.
    """

    def __init__(self):
        """Initialize storage."""
        self._global_counts: dict[str, int] = defaultdict(int)
        self._workflow_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = Lock()

    def record_error(
        self,
        workflow_id: str,
        error_type: str,
    ) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._global_counts[error_type] += 1
            self._workflow_counts[workflow_id][error_type] += 1

    def get_global_counts(self) -> dict[str, int]:
        """Get global error counts."""
        with self._lock:
            return dict(self._global_counts)

    def get_workflow_counts(self, workflow_id: str) -> dict[str, int]:
        """Get error counts for a workflow."""
        with self._lock:
            return dict(self._workflow_counts.get(workflow_id, {}))

    def get_top_errors(
        self,
        n: int = 10,
        workflow_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get top N errors."""
        with self._lock:
            if workflow_id:
                counts = dict(self._workflow_counts.get(workflow_id, {}))
            else:
                counts = dict(self._global_counts)

        sorted_errors = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]
        total = sum(counts.values())

        return [
            {
                "error_type": err_type,
                "count": count,
                "percentage": round((count / total) * 100, 2) if total > 0 else 0,
            }
            for err_type, count in sorted_errors
        ]

    def clear(self) -> None:
        """Clear all error data."""
        with self._lock:
            self._global_counts.clear()
            self._workflow_counts.clear()


class HealingMetricsStorage:
    """
    Storage for self-healing metrics.

    Tracks healing attempts and successes.
    """

    def __init__(self):
        """Initialize storage."""
        self._by_tier: dict[str, int] = defaultdict(int)
        self._by_workflow: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = Lock()

    def record_healing(
        self,
        workflow_id: str,
        tier: str,
        success: bool,
    ) -> None:
        """Record a healing attempt."""
        with self._lock:
            self._by_tier[tier] += 1
            if success:
                self._by_tier[f"{tier}_success"] += 1

            self._by_workflow[workflow_id]["attempts"] += 1
            if success:
                self._by_workflow[workflow_id]["successes"] += 1

    def record_from_record(self, record: JobRecord) -> None:
        """Record healing metrics from a job record."""
        if record.healing_attempts > 0:
            with self._lock:
                self._by_workflow[record.workflow_id]["attempts"] += record.healing_attempts
                self._by_workflow[record.workflow_id]["successes"] += record.healing_successes

    def get_by_tier(self) -> dict[str, dict[str, Any]]:
        """Get healing metrics by tier."""
        with self._lock:
            tier_data = dict(self._by_tier)

        tiers = ["heuristic", "anchor", "cv"]
        result = {}

        for tier in tiers:
            attempts = tier_data.get(tier, 0)
            successes = tier_data.get(f"{tier}_success", 0)
            result[tier] = {
                "attempts": attempts,
                "successes": successes,
                "success_rate": round((successes / attempts) * 100, 2) if attempts > 0 else 0.0,
            }

        return result

    def get_by_workflow(self, workflow_id: str | None = None) -> dict[str, Any]:
        """Get healing metrics for a workflow or globally."""
        with self._lock:
            if workflow_id:
                data = dict(self._by_workflow.get(workflow_id, {}))
            else:
                data = {
                    "attempts": sum(v.get("attempts", 0) for v in self._by_workflow.values()),
                    "successes": sum(v.get("successes", 0) for v in self._by_workflow.values()),
                }

        attempts = data.get("attempts", 0)
        successes = data.get("successes", 0)

        return {
            "total_attempts": attempts,
            "total_successes": successes,
            "overall_success_rate": round((successes / attempts) * 100, 2) if attempts > 0 else 0.0,
        }

    def clear(self) -> None:
        """Clear all healing data."""
        with self._lock:
            self._by_tier.clear()
            self._by_workflow.clear()


class QueueDepthStorage:
    """
    Storage for queue depth history.

    Maintains time series of queue depths.
    """

    def __init__(self, max_points: int = 1440):
        """
        Initialize storage.

        Args:
            max_points: Maximum data points (default: 24 hours at 1-min intervals).
        """
        self._history: list[TimeSeriesDataPoint] = []
        self._lock = Lock()
        self._max_points = max_points

    def record(self, depth: int) -> None:
        """Record current queue depth."""
        now = datetime.now(UTC)
        with self._lock:
            self._history.append(
                TimeSeriesDataPoint(
                    timestamp=now,
                    value=float(depth),
                )
            )
            if len(self._history) > self._max_points:
                self._history = self._history[-self._max_points :]

    def get_history(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> list[TimeSeriesDataPoint]:
        """Get queue depth history."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        with self._lock:
            filtered = [dp for dp in self._history if dp.timestamp >= cutoff]

        return filtered[-limit:]

    def get_statistics(self, hours: int = 24) -> dict[str, Any]:
        """Get queue depth statistics."""
        history = self.get_history(hours)

        if not history:
            return {
                "current_depth": 0,
                "avg_depth": 0.0,
                "max_depth": 0,
                "min_depth": 0,
            }

        depths = [dp.value for dp in history]

        return {
            "current_depth": int(history[-1].value) if history else 0,
            "avg_depth": round(statistics.mean(depths), 2),
            "max_depth": int(max(depths)),
            "min_depth": int(min(depths)),
        }

    def clear(self) -> None:
        """Clear all history."""
        with self._lock:
            self._history.clear()


class MetricsStorageManager:
    """
    Manager for all metrics storage components.

    Provides unified access to storage adapters.
    """

    def __init__(
        self,
        max_job_records: int = 100000,
        max_duration_samples: int = 10000,
        max_queue_points: int = 1440,
    ):
        """
        Initialize storage manager.

        Args:
            max_job_records: Maximum job records to retain.
            max_duration_samples: Maximum duration samples per workflow.
            max_queue_points: Maximum queue depth data points.
        """
        self.job_records = InMemoryJobRecordStorage(max_records=max_job_records)
        self.workflow_metrics = WorkflowMetricsCache(max_duration_samples=max_duration_samples)
        self.robot_metrics = RobotMetricsCache()
        self.error_tracking = ErrorTrackingStorage()
        self.healing_metrics = HealingMetricsStorage()
        self.queue_depth = QueueDepthStorage(max_points=max_queue_points)

        logger.debug("MetricsStorageManager initialized")

    def record_job(self, record: JobRecord) -> None:
        """
        Record a job execution across all storage components.

        Args:
            record: Job execution record.
        """
        self.job_records.add(record)
        self.workflow_metrics.update(record)
        self.robot_metrics.update(record)

        if record.status == "failed" and record.error_type:
            self.error_tracking.record_error(record.workflow_id, record.error_type)

        self.healing_metrics.record_from_record(record)

    def reset(self) -> None:
        """Reset all storage components."""
        self.job_records.clear()
        self.workflow_metrics.clear()
        self.robot_metrics.clear()
        self.error_tracking.clear()
        self.healing_metrics.clear()
        self.queue_depth.clear()

        logger.info("MetricsStorageManager reset")


__all__ = [
    # Data classes
    "JobRecord",
    "WorkflowMetricsData",
    "RobotMetricsData",
    # Storage classes
    "MetricStorage",
    "InMemoryJobRecordStorage",
    "WorkflowMetricsCache",
    "RobotMetricsCache",
    "ErrorTrackingStorage",
    "HealingMetricsStorage",
    "QueueDepthStorage",
    # Manager
    "MetricsStorageManager",
]
