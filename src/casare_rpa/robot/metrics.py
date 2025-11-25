"""
Execution Metrics for Robot Agent.

Collects and tracks:
- Job execution duration and success rates
- Node-level timing and failure statistics
- Resource utilization metrics
- Connection health metrics
"""

import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from loguru import logger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, resource monitoring disabled")


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""
    node_id: str
    node_type: str
    duration_ms: float
    success: bool
    error_type: Optional[str] = None
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JobMetrics:
    """Metrics for a job execution."""
    job_id: str
    workflow_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    success: bool = False
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    skipped_nodes: int = 0
    retry_count: int = 0
    error_message: Optional[str] = None
    node_metrics: List[NodeMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "workflow_name": self.workflow_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "total_nodes": self.total_nodes,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "skipped_nodes": self.skipped_nodes,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
        }


@dataclass
class ResourceSnapshot:
    """Snapshot of system resource usage."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_percent: Optional[float] = None
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0


class MetricsCollector:
    """
    Collects and aggregates execution metrics.

    Provides real-time and historical metrics for monitoring
    robot health and performance.
    """

    def __init__(
        self,
        history_limit: int = 1000,
        resource_sample_interval: float = 5.0,
    ):
        """
        Initialize metrics collector.

        Args:
            history_limit: Maximum number of job metrics to keep
            resource_sample_interval: Seconds between resource samples
        """
        self.history_limit = history_limit
        self.resource_sample_interval = resource_sample_interval

        # Job metrics history
        self._job_metrics: List[JobMetrics] = []
        self._current_job: Optional[JobMetrics] = None

        # Aggregated statistics
        self._total_jobs = 0
        self._successful_jobs = 0
        self._failed_jobs = 0
        self._total_duration_ms = 0.0

        # Node statistics by type
        self._node_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "total_duration_ms": 0,
                "retry_count": 0,
            }
        )

        # Resource monitoring
        self._resource_history: List[ResourceSnapshot] = []
        self._resource_task: Optional[asyncio.Task] = None
        self._monitoring = False

        # Error tracking
        self._error_counts: Dict[str, int] = defaultdict(int)

        logger.info("Metrics collector initialized")

    # Job-level metrics

    def start_job(
        self,
        job_id: str,
        workflow_name: str,
        total_nodes: int = 0,
    ) -> JobMetrics:
        """
        Start tracking a new job.

        Args:
            job_id: Job identifier
            workflow_name: Name of the workflow
            total_nodes: Total number of nodes in workflow

        Returns:
            JobMetrics instance for this job
        """
        self._current_job = JobMetrics(
            job_id=job_id,
            workflow_name=workflow_name,
            started_at=datetime.now(timezone.utc),
            total_nodes=total_nodes,
        )
        logger.debug(f"Started tracking job {job_id}")
        return self._current_job

    def end_job(
        self,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """
        End tracking current job.

        Args:
            success: Whether job succeeded
            error_message: Error message if failed
        """
        if not self._current_job:
            logger.warning("end_job called with no current job")
            return

        self._current_job.completed_at = datetime.now(timezone.utc)
        self._current_job.duration_ms = (
            (self._current_job.completed_at - self._current_job.started_at).total_seconds() * 1000
        )
        self._current_job.success = success
        self._current_job.error_message = error_message

        # Update aggregates
        self._total_jobs += 1
        self._total_duration_ms += self._current_job.duration_ms

        if success:
            self._successful_jobs += 1
        else:
            self._failed_jobs += 1
            if error_message:
                self._error_counts[error_message[:100]] += 1

        # Store in history
        self._job_metrics.append(self._current_job)
        if len(self._job_metrics) > self.history_limit:
            self._job_metrics.pop(0)

        logger.debug(
            f"Job {self._current_job.job_id} completed: "
            f"success={success}, duration={self._current_job.duration_ms:.0f}ms"
        )

        self._current_job = None

    # Node-level metrics

    def record_node(
        self,
        node_id: str,
        node_type: str,
        duration_ms: float,
        success: bool,
        error_type: Optional[str] = None,
        retry_count: int = 0,
    ):
        """
        Record metrics for a node execution.

        Args:
            node_id: Node identifier
            node_type: Type of the node
            duration_ms: Execution duration in milliseconds
            success: Whether node succeeded
            error_type: Type of error if failed
            retry_count: Number of retries performed
        """
        node_metrics = NodeMetrics(
            node_id=node_id,
            node_type=node_type,
            duration_ms=duration_ms,
            success=success,
            error_type=error_type,
            retry_count=retry_count,
        )

        # Update current job
        if self._current_job:
            self._current_job.node_metrics.append(node_metrics)
            self._current_job.retry_count += retry_count
            if success:
                self._current_job.completed_nodes += 1
            else:
                self._current_job.failed_nodes += 1

        # Update node type statistics
        stats = self._node_stats[node_type]
        stats["total_executions"] += 1
        stats["total_duration_ms"] += duration_ms
        stats["retry_count"] += retry_count
        if success:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
            if error_type:
                self._error_counts[f"{node_type}:{error_type}"] += 1

    def record_node_skipped(self, node_id: str, node_type: str):
        """Record a skipped node."""
        if self._current_job:
            self._current_job.skipped_nodes += 1

    # Resource monitoring

    async def start_resource_monitoring(self):
        """Start background resource monitoring."""
        if not PSUTIL_AVAILABLE:
            logger.warning("Resource monitoring not available (psutil not installed)")
            return

        if self._monitoring:
            return

        self._monitoring = True
        self._resource_task = asyncio.create_task(self._resource_monitor_loop())
        logger.info("Resource monitoring started")

    async def stop_resource_monitoring(self):
        """Stop background resource monitoring."""
        self._monitoring = False
        if self._resource_task:
            self._resource_task.cancel()
            try:
                await self._resource_task
            except asyncio.CancelledError:
                pass
            self._resource_task = None
        logger.info("Resource monitoring stopped")

    async def _resource_monitor_loop(self):
        """Background loop for resource sampling."""
        while self._monitoring:
            try:
                snapshot = self._sample_resources()
                if snapshot:
                    self._resource_history.append(snapshot)
                    # Keep last hour of samples
                    max_samples = int(3600 / self.resource_sample_interval)
                    if len(self._resource_history) > max_samples:
                        self._resource_history.pop(0)
            except Exception as e:
                logger.error(f"Resource sampling error: {e}")

            await asyncio.sleep(self.resource_sample_interval)

    def _sample_resources(self) -> Optional[ResourceSnapshot]:
        """Sample current resource usage."""
        if not PSUTIL_AVAILABLE:
            return None

        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            net_io = psutil.net_io_counters()

            return ResourceSnapshot(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=process.cpu_percent(),
                memory_percent=process.memory_percent(),
                memory_mb=memory_info.rss / (1024 * 1024),
                disk_percent=psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else None,
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
            )
        except Exception as e:
            logger.error(f"Failed to sample resources: {e}")
            return None

    def get_current_resources(self) -> Optional[Dict[str, Any]]:
        """Get current resource usage."""
        snapshot = self._sample_resources()
        if snapshot:
            return {
                "cpu_percent": snapshot.cpu_percent,
                "memory_percent": snapshot.memory_percent,
                "memory_mb": snapshot.memory_mb,
                "disk_percent": snapshot.disk_percent,
            }
        return None

    # Statistics and reporting

    def get_summary(self) -> Dict[str, Any]:
        """Get overall metrics summary."""
        avg_duration = (
            self._total_duration_ms / self._total_jobs
            if self._total_jobs > 0 else 0
        )
        success_rate = (
            self._successful_jobs / self._total_jobs * 100
            if self._total_jobs > 0 else 0
        )

        return {
            "total_jobs": self._total_jobs,
            "successful_jobs": self._successful_jobs,
            "failed_jobs": self._failed_jobs,
            "success_rate_percent": round(success_rate, 2),
            "average_duration_ms": round(avg_duration, 0),
            "total_duration_ms": self._total_duration_ms,
            "current_job": self._current_job.job_id if self._current_job else None,
        }

    def get_node_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics by node type."""
        result = {}
        for node_type, stats in self._node_stats.items():
            total = stats["total_executions"]
            avg_duration = stats["total_duration_ms"] / total if total > 0 else 0
            success_rate = stats["successful"] / total * 100 if total > 0 else 0

            result[node_type] = {
                "total_executions": total,
                "successful": stats["successful"],
                "failed": stats["failed"],
                "success_rate_percent": round(success_rate, 2),
                "average_duration_ms": round(avg_duration, 2),
                "total_retries": stats["retry_count"],
            }
        return result

    def get_error_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common errors."""
        sorted_errors = sorted(
            self._error_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        return [
            {"error": error, "count": count}
            for error, count in sorted_errors
        ]

    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job metrics."""
        recent = self._job_metrics[-limit:]
        return [job.to_dict() for job in reversed(recent)]

    def get_resource_history(
        self,
        minutes: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get resource usage history."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        history = [
            {
                "timestamp": s.timestamp.isoformat(),
                "cpu_percent": s.cpu_percent,
                "memory_percent": s.memory_percent,
                "memory_mb": s.memory_mb,
            }
            for s in self._resource_history
            if s.timestamp >= cutoff
        ]
        return history

    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive metrics report."""
        return {
            "summary": self.get_summary(),
            "node_stats": self.get_node_stats(),
            "top_errors": self.get_error_summary(),
            "recent_jobs": self.get_recent_jobs(),
            "current_resources": self.get_current_resources(),
            "resource_history": self.get_resource_history(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def reset(self):
        """Reset all metrics (for testing)."""
        self._job_metrics.clear()
        self._current_job = None
        self._total_jobs = 0
        self._successful_jobs = 0
        self._failed_jobs = 0
        self._total_duration_ms = 0
        self._node_stats.clear()
        self._resource_history.clear()
        self._error_counts.clear()
        logger.info("Metrics reset")


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
