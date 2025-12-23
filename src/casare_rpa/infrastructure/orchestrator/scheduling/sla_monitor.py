"""
SLA monitoring for CasareRPA Orchestrator.

Contains SLA tracking, metrics collection, and alerting utilities.
Monitors schedule execution compliance with defined SLAs.
"""

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


class SLAStatus(Enum):
    """SLA compliance status."""

    OK = "ok"
    WARNING = "warning"
    BREACHED = "breached"
    UNKNOWN = "unknown"


@dataclass
class SLAConfig:
    """
    SLA configuration for a schedule.

    Attributes:
        max_duration_seconds: Maximum allowed execution duration
        max_start_delay_seconds: Maximum delay from scheduled time to start
        success_rate_threshold: Minimum success rate percentage (0-100)
        consecutive_failure_limit: Max consecutive failures before alerting
        on_breach: Callback function when SLA is breached
    """

    max_duration_seconds: Optional[int] = None
    max_start_delay_seconds: Optional[int] = 300
    success_rate_threshold: float = 95.0
    consecutive_failure_limit: int = 3
    on_breach: Optional[Callable[[str, str, Any], None]] = None


@dataclass
class ExecutionMetrics:
    """Metrics for a single execution."""

    schedule_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    success: bool = False
    duration_ms: int = 0
    start_delay_ms: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAReport:
    """SLA compliance report for a schedule."""

    schedule_id: str
    schedule_name: str
    status: SLAStatus
    success_rate: float
    success_rate_threshold: float
    average_duration_ms: int
    max_duration_ms: Optional[int]
    consecutive_failures: int
    consecutive_failure_limit: int
    run_count: int
    window_hours: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SLAMonitor:
    """
    Monitors SLA compliance for schedules.

    Tracks execution times, success rates, and triggers alerts on breaches.
    Thread-safe for concurrent access.
    """

    def __init__(self, metrics_retention_limit: int = 1000):
        """
        Initialize SLA monitor.

        Args:
            metrics_retention_limit: Maximum metrics per schedule
        """
        self._metrics: Dict[str, List[ExecutionMetrics]] = defaultdict(list)
        self._active_executions: Dict[str, ExecutionMetrics] = {}
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable[[str, SLAStatus, str], None]] = []
        self._retention_limit = metrics_retention_limit

    def add_alert_callback(self, callback: Callable[[str, SLAStatus, str], None]) -> None:
        """
        Add callback for SLA alerts.

        Args:
            callback: Function called with (schedule_id, status, message)
        """
        self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[str, SLAStatus, str], None]) -> bool:
        """
        Remove an alert callback.

        Args:
            callback: Callback to remove

        Returns:
            True if callback was removed
        """
        try:
            self._alert_callbacks.remove(callback)
            return True
        except ValueError:
            return False

    def record_start(
        self,
        schedule_id: str,
        scheduled_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record execution start.

        Args:
            schedule_id: Schedule ID
            scheduled_time: When execution was scheduled for
            metadata: Optional execution metadata

        Returns:
            Execution tracking ID
        """
        execution_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        start_delay_ms = 0
        if scheduled_time:
            delay = (now - scheduled_time).total_seconds() * 1000
            start_delay_ms = int(max(0, delay))

        metrics = ExecutionMetrics(
            schedule_id=schedule_id,
            started_at=now,
            scheduled_time=scheduled_time,
            start_delay_ms=start_delay_ms,
            metadata=metadata or {},
        )

        with self._lock:
            self._active_executions[execution_id] = metrics

        return execution_id

    def record_completion(
        self,
        execution_id: str,
        success: bool,
        sla_config: Optional[SLAConfig] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ExecutionMetrics]:
        """
        Record execution completion and check SLA.

        Args:
            execution_id: Execution tracking ID from record_start
            success: Whether execution succeeded
            sla_config: SLA configuration for checking
            error_message: Optional error message if failed

        Returns:
            Execution metrics or None if not found
        """
        with self._lock:
            metrics = self._active_executions.pop(execution_id, None)
            if not metrics:
                return None

            metrics.completed_at = datetime.now(timezone.utc)
            metrics.success = success
            metrics.error_message = error_message
            metrics.duration_ms = int(
                (metrics.completed_at - metrics.started_at).total_seconds() * 1000
            )

            self._metrics[metrics.schedule_id].append(metrics)

            # Trim old metrics
            if len(self._metrics[metrics.schedule_id]) > self._retention_limit:
                self._metrics[metrics.schedule_id] = self._metrics[metrics.schedule_id][
                    -self._retention_limit // 2 :
                ]

        if sla_config:
            self._check_sla(metrics, sla_config)

        return metrics

    def record_error(
        self,
        execution_id: str,
        error_message: str,
        sla_config: Optional[SLAConfig] = None,
    ) -> Optional[ExecutionMetrics]:
        """
        Record execution error.

        Args:
            execution_id: Execution tracking ID
            error_message: Error description
            sla_config: SLA configuration for checking

        Returns:
            Execution metrics or None if not found
        """
        return self.record_completion(
            execution_id=execution_id,
            success=False,
            sla_config=sla_config,
            error_message=error_message,
        )

    def _check_sla(self, metrics: ExecutionMetrics, sla: SLAConfig) -> None:
        """Check SLA compliance and trigger alerts if needed."""
        breaches = []

        # Check duration SLA
        if sla.max_duration_seconds:
            max_duration_ms = sla.max_duration_seconds * 1000
            if metrics.duration_ms > max_duration_ms:
                breaches.append(
                    f"Duration {metrics.duration_ms}ms exceeded limit {max_duration_ms}ms"
                )

        # Check start delay SLA
        if sla.max_start_delay_seconds:
            max_delay_ms = sla.max_start_delay_seconds * 1000
            if metrics.start_delay_ms > max_delay_ms:
                breaches.append(
                    f"Start delay {metrics.start_delay_ms}ms exceeded limit {max_delay_ms}ms"
                )

        if breaches:
            message = "; ".join(breaches)
            logger.warning(f"SLA breach for {metrics.schedule_id}: {message}")

            # Notify alert callbacks
            for callback in self._alert_callbacks:
                try:
                    callback(metrics.schedule_id, SLAStatus.BREACHED, message)
                except Exception as e:
                    logger.error(f"SLA alert callback failed: {e}")

            # Call on_breach handler
            if sla.on_breach:
                try:
                    sla.on_breach(metrics.schedule_id, message, metrics)
                except Exception as e:
                    logger.error(f"SLA breach handler failed: {e}")

    def get_metrics(
        self,
        schedule_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[ExecutionMetrics]:
        """
        Get execution metrics for a schedule.

        Args:
            schedule_id: Schedule ID
            since: Only get metrics since this time
            limit: Maximum number of records

        Returns:
            List of execution metrics (newest first)
        """
        with self._lock:
            metrics = self._metrics.get(schedule_id, [])
            if since:
                metrics = [m for m in metrics if m.started_at >= since]
            return list(reversed(metrics[-limit:]))

    def get_active_executions(self) -> Dict[str, ExecutionMetrics]:
        """Get currently active executions."""
        with self._lock:
            return dict(self._active_executions)

    def get_success_rate(
        self,
        schedule_id: str,
        window_hours: int = 24,
    ) -> float:
        """
        Calculate success rate for a schedule.

        Args:
            schedule_id: Schedule ID
            window_hours: Time window to calculate over

        Returns:
            Success rate percentage (0-100)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        metrics = self.get_metrics(schedule_id, since=cutoff)

        if not metrics:
            return 100.0

        success_count = sum(1 for m in metrics if m.success)
        return (success_count / len(metrics)) * 100

    def get_failure_rate(
        self,
        schedule_id: str,
        window_hours: int = 24,
    ) -> float:
        """
        Calculate failure rate for a schedule.

        Args:
            schedule_id: Schedule ID
            window_hours: Time window to calculate over

        Returns:
            Failure rate percentage (0-100)
        """
        return 100.0 - self.get_success_rate(schedule_id, window_hours)

    def get_average_duration(
        self,
        schedule_id: str,
        window_hours: int = 24,
    ) -> int:
        """
        Calculate average execution duration.

        Args:
            schedule_id: Schedule ID
            window_hours: Time window to calculate over

        Returns:
            Average duration in milliseconds
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        metrics = self.get_metrics(schedule_id, since=cutoff)

        if not metrics:
            return 0

        total_duration = sum(m.duration_ms for m in metrics)
        return total_duration // len(metrics)

    def get_percentile_duration(
        self,
        schedule_id: str,
        percentile: float = 95.0,
        window_hours: int = 24,
    ) -> int:
        """
        Calculate percentile execution duration.

        Args:
            schedule_id: Schedule ID
            percentile: Percentile to calculate (0-100)
            window_hours: Time window to calculate over

        Returns:
            Percentile duration in milliseconds
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        metrics = self.get_metrics(schedule_id, since=cutoff)

        if not metrics:
            return 0

        durations = sorted(m.duration_ms for m in metrics)
        idx = int(len(durations) * percentile / 100)
        idx = min(idx, len(durations) - 1)
        return durations[idx]

    def get_execution_count(
        self,
        schedule_id: str,
        window_hours: int = 24,
    ) -> int:
        """
        Get execution count for a schedule.

        Args:
            schedule_id: Schedule ID
            window_hours: Time window to count over

        Returns:
            Number of executions
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        metrics = self.get_metrics(schedule_id, since=cutoff)
        return len(metrics)

    def get_sla_status(
        self,
        schedule_id: str,
        sla_config: SLAConfig,
        window_hours: int = 24,
    ) -> SLAStatus:
        """
        Get current SLA status for a schedule.

        Args:
            schedule_id: Schedule ID
            sla_config: SLA configuration
            window_hours: Time window for calculations

        Returns:
            Current SLA status
        """
        success_rate = self.get_success_rate(schedule_id, window_hours)

        # Check success rate threshold
        if success_rate < sla_config.success_rate_threshold:
            if success_rate < sla_config.success_rate_threshold - 5:
                return SLAStatus.BREACHED
            return SLAStatus.WARNING

        # Check recent failures
        metrics = self.get_metrics(schedule_id, limit=sla_config.consecutive_failure_limit)
        consecutive_failures = 0
        for m in metrics:
            if not m.success:
                consecutive_failures += 1
            else:
                break

        if consecutive_failures >= sla_config.consecutive_failure_limit:
            return SLAStatus.BREACHED

        return SLAStatus.OK

    def generate_report(
        self,
        schedule_id: str,
        schedule_name: str,
        sla_config: SLAConfig,
        window_hours: int = 24,
    ) -> SLAReport:
        """
        Generate SLA compliance report for a schedule.

        Args:
            schedule_id: Schedule ID
            schedule_name: Human-readable schedule name
            sla_config: SLA configuration
            window_hours: Time window for report

        Returns:
            SLA compliance report
        """
        success_rate = self.get_success_rate(schedule_id, window_hours)
        avg_duration = self.get_average_duration(schedule_id, window_hours)
        run_count = self.get_execution_count(schedule_id, window_hours)
        status = self.get_sla_status(schedule_id, sla_config, window_hours)

        # Count consecutive failures
        metrics = self.get_metrics(schedule_id, limit=sla_config.consecutive_failure_limit)
        consecutive_failures = 0
        for m in metrics:
            if not m.success:
                consecutive_failures += 1
            else:
                break

        return SLAReport(
            schedule_id=schedule_id,
            schedule_name=schedule_name,
            status=status,
            success_rate=round(success_rate, 2),
            success_rate_threshold=sla_config.success_rate_threshold,
            average_duration_ms=avg_duration,
            max_duration_ms=(
                sla_config.max_duration_seconds * 1000 if sla_config.max_duration_seconds else None
            ),
            consecutive_failures=consecutive_failures,
            consecutive_failure_limit=sla_config.consecutive_failure_limit,
            run_count=run_count,
            window_hours=window_hours,
        )

    def clear_metrics(self, schedule_id: Optional[str] = None) -> None:
        """
        Clear metrics for a schedule or all schedules.

        Args:
            schedule_id: Specific schedule to clear (None for all)
        """
        with self._lock:
            if schedule_id:
                self._metrics.pop(schedule_id, None)
            else:
                self._metrics.clear()


class SLAAggregator:
    """
    Aggregates SLA metrics across multiple schedules.

    Provides fleet-wide SLA visibility and reporting.
    """

    def __init__(self, sla_monitor: SLAMonitor):
        """
        Initialize SLA aggregator.

        Args:
            sla_monitor: SLAMonitor instance to aggregate from
        """
        self._monitor = sla_monitor

    def get_fleet_success_rate(
        self,
        schedule_ids: List[str],
        window_hours: int = 24,
    ) -> float:
        """
        Calculate aggregate success rate across schedules.

        Args:
            schedule_ids: List of schedule IDs to aggregate
            window_hours: Time window for calculation

        Returns:
            Aggregate success rate percentage
        """
        if not schedule_ids:
            return 100.0

        total_success = 0
        total_count = 0

        for schedule_id in schedule_ids:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
            metrics = self._monitor.get_metrics(schedule_id, since=cutoff)
            total_count += len(metrics)
            total_success += sum(1 for m in metrics if m.success)

        if total_count == 0:
            return 100.0

        return (total_success / total_count) * 100

    def get_fleet_status_summary(
        self,
        schedule_configs: Dict[str, SLAConfig],
        window_hours: int = 24,
    ) -> Dict[SLAStatus, int]:
        """
        Get count of schedules by SLA status.

        Args:
            schedule_configs: Map of schedule ID to SLA config
            window_hours: Time window for status calculation

        Returns:
            Dictionary of status to count
        """
        summary: Dict[SLAStatus, int] = {status: 0 for status in SLAStatus}

        for schedule_id, config in schedule_configs.items():
            status = self._monitor.get_sla_status(schedule_id, config, window_hours)
            summary[status] += 1

        return summary

    def get_worst_performers(
        self,
        schedule_ids: List[str],
        limit: int = 5,
        window_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get schedules with lowest success rates.

        Args:
            schedule_ids: List of schedule IDs to analyze
            limit: Maximum results to return
            window_hours: Time window for analysis

        Returns:
            List of schedules with their success rates
        """
        performers = []

        for schedule_id in schedule_ids:
            success_rate = self._monitor.get_success_rate(schedule_id, window_hours)
            performers.append(
                {
                    "schedule_id": schedule_id,
                    "success_rate": success_rate,
                }
            )

        performers.sort(key=lambda x: x["success_rate"])
        return performers[:limit]

    def get_slowest_performers(
        self,
        schedule_ids: List[str],
        limit: int = 5,
        window_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get schedules with highest average duration.

        Args:
            schedule_ids: List of schedule IDs to analyze
            limit: Maximum results to return
            window_hours: Time window for analysis

        Returns:
            List of schedules with their average durations
        """
        performers = []

        for schedule_id in schedule_ids:
            avg_duration = self._monitor.get_average_duration(schedule_id, window_hours)
            performers.append(
                {
                    "schedule_id": schedule_id,
                    "average_duration_ms": avg_duration,
                }
            )

        performers.sort(key=lambda x: x["average_duration_ms"], reverse=True)
        return performers[:limit]
