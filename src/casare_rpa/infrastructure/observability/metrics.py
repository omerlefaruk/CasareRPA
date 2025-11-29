"""
CasareRPA - Infrastructure: RPA-Specific Metrics Collection

Specialized metrics collectors for RPA operations including:
- Job execution metrics (duration, success rate, queue wait time)
- Robot utilization metrics (busy/idle ratio, concurrent jobs)
- Queue metrics (depth, throughput, backpressure)
- Node execution metrics (per-type latency, failure rate)
- Self-healing metrics (healing attempts, success rate)
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Generator, List, Optional

from loguru import logger

from casare_rpa.infrastructure.observability.telemetry import (
    TelemetryProvider,
    get_meter,
    OTEL_AVAILABLE,
)
from casare_rpa.infrastructure.events import (
    get_monitoring_event_bus,
    MonitoringEventType,
)

if OTEL_AVAILABLE:
    from opentelemetry.metrics import Observation


class JobStatus(str, Enum):
    """Job execution status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class RobotStatus(str, Enum):
    """Robot status values."""

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class JobMetrics:
    """Aggregated job metrics for a time window."""

    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    total_duration_seconds: float = 0.0
    total_queue_wait_seconds: float = 0.0
    total_nodes_executed: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate job success rate."""
        if self.total_jobs == 0:
            return 0.0
        return self.completed_jobs / self.total_jobs * 100

    @property
    def average_duration_seconds(self) -> float:
        """Calculate average job duration."""
        completed = self.completed_jobs + self.failed_jobs
        if completed == 0:
            return 0.0
        return self.total_duration_seconds / completed

    @property
    def average_queue_wait_seconds(self) -> float:
        """Calculate average queue wait time."""
        if self.total_jobs == 0:
            return 0.0
        return self.total_queue_wait_seconds / self.total_jobs


@dataclass
class RobotMetrics:
    """Aggregated robot metrics."""

    robot_id: str
    status: RobotStatus = RobotStatus.IDLE
    jobs_completed: int = 0
    jobs_failed: int = 0
    total_busy_seconds: float = 0.0
    total_idle_seconds: float = 0.0
    last_job_at: Optional[datetime] = None
    current_job_id: Optional[str] = None
    current_job_started_at: Optional[datetime] = None

    @property
    def utilization_percent(self) -> float:
        """Calculate robot utilization percentage."""
        total = self.total_busy_seconds + self.total_idle_seconds
        if total == 0:
            return 0.0
        return self.total_busy_seconds / total * 100

    @property
    def success_rate(self) -> float:
        """Calculate job success rate for this robot."""
        total = self.jobs_completed + self.jobs_failed
        if total == 0:
            return 0.0
        return self.jobs_completed / total * 100


class RPAMetricsCollector:
    """
    Centralized metrics collector for RPA operations.

    Provides a high-level API for recording RPA-specific metrics and
    maintains internal state for observable gauges.

    Usage:
        collector = RPAMetricsCollector.get_instance()
        collector.record_job_start("job-123", "workflow-A")
        # ... job execution ...
        collector.record_job_complete("job-123", success=True, duration=45.2)
    """

    _instance: Optional["RPAMetricsCollector"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "RPAMetricsCollector":
        """Thread-safe singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RPAMetricsCollector":
        """Get the singleton instance."""
        return cls()

    def __init__(self, emit_events: bool = True) -> None:
        """
        Initialize the metrics collector.

        Args:
            emit_events: Whether to emit monitoring events (set False for testing)
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._lock = Lock()
        self._emit_events = emit_events

        # Job tracking
        self._active_jobs: Dict[str, Dict[str, Any]] = {}
        self._job_metrics = JobMetrics()

        # Robot tracking
        self._robots: Dict[str, RobotMetrics] = {}

        # Queue tracking
        self._queue_depth: int = 0
        self._queue_throughput_window: List[float] = []  # timestamps of dequeues

        # Node execution tracking (per type)
        self._node_metrics: Dict[str, Dict[str, Any]] = {}

        # Self-healing tracking
        self._healing_attempts: int = 0
        self._healing_successes: int = 0

        # Initialize OTel instrument attributes to None
        self._job_queue_wait_histogram: Optional[Any] = None
        self._job_retry_counter: Optional[Any] = None
        self._node_latency_histogram: Optional[Any] = None
        self._healing_attempt_counter: Optional[Any] = None
        self._healing_success_counter: Optional[Any] = None
        self._browser_pool_active: Optional[Any] = None
        self._active_jobs_gauge: Optional[Any] = None
        self._queue_throughput_gauge: Optional[Any] = None

        # OTel instruments (may be None if not initialized)
        self._init_instruments()

        self._initialized = True

    def _init_instruments(self) -> None:
        """Initialize OpenTelemetry metric instruments."""
        meter = get_meter("casare_rpa.metrics")
        if not meter:
            logger.debug("Meter not available, metrics will not be exported")
            return

        # Job metrics
        self._job_queue_wait_histogram = meter.create_histogram(
            name="casare_rpa.job.queue_wait_time",
            description="Time jobs spend waiting in queue before execution",
            unit="s",
        )

        self._job_retry_counter = meter.create_counter(
            name="casare_rpa.job.retry.count",
            description="Number of job retry attempts",
            unit="1",
        )

        # Node metrics
        self._node_latency_histogram = meter.create_histogram(
            name="casare_rpa.node.latency",
            description="Node execution latency by type",
            unit="ms",
        )

        # Self-healing metrics
        self._healing_attempt_counter = meter.create_counter(
            name="casare_rpa.healing.attempt.count",
            description="Number of self-healing attempts",
            unit="1",
        )

        self._healing_success_counter = meter.create_counter(
            name="casare_rpa.healing.success.count",
            description="Number of successful self-healing operations",
            unit="1",
        )

        # Browser pool metrics
        self._browser_pool_active = meter.create_up_down_counter(
            name="casare_rpa.browser_pool.active",
            description="Number of active browser instances",
            unit="1",
        )

        # Observable gauges with callbacks
        def active_jobs_callback(options: Any) -> Generator[Any, None, None]:
            yield Observation(value=len(self._active_jobs))

        self._active_jobs_gauge = meter.create_observable_gauge(
            name="casare_rpa.job.active",
            description="Number of currently executing jobs",
            unit="1",
            callbacks=[active_jobs_callback],
        )

        def queue_throughput_callback(options: Any) -> Generator[Any, None, None]:
            # Calculate throughput over last minute
            now = time.time()
            one_minute_ago = now - 60
            recent = [t for t in self._queue_throughput_window if t > one_minute_ago]
            self._queue_throughput_window = recent  # Cleanup old entries
            yield Observation(value=len(recent))

        self._queue_throughput_gauge = meter.create_observable_gauge(
            name="casare_rpa.queue.throughput",
            description="Jobs processed per minute",
            unit="1/min",
            callbacks=[queue_throughput_callback],
        )

        logger.debug("RPA metrics instruments initialized")

    def _emit_monitoring_event(
        self,
        event_type: MonitoringEventType,
        payload: Dict[str, Any],
    ) -> None:
        """
        Emit a monitoring event (fire-and-forget).

        Args:
            event_type: Type of monitoring event
            payload: Event payload data
        """
        if not self._emit_events:
            return

        try:
            import asyncio

            event_bus = get_monitoring_event_bus()

            # Fire-and-forget: create task but don't await
            # This prevents blocking the metrics collector
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(event_bus.publish(event_type, payload))
            except RuntimeError:
                # No event loop running - silently skip
                logger.debug("No event loop - skipping monitoring event emission")
        except Exception as e:
            # Never let event emission break metrics collection
            logger.warning(f"Failed to emit monitoring event: {e}")

    # =========================================================================
    # Job Metrics
    # =========================================================================

    def record_job_enqueue(
        self,
        job_id: str,
        workflow_name: str,
        priority: int = 10,
    ) -> None:
        """
        Record a job being added to the queue.

        Args:
            job_id: Unique job identifier
            workflow_name: Name of the workflow
            priority: Job priority level
        """
        with self._lock:
            self._queue_depth += 1
            self._active_jobs[job_id] = {
                "workflow_name": workflow_name,
                "priority": priority,
                "enqueued_at": time.time(),
                "started_at": None,
                "status": JobStatus.PENDING,
            }

        TelemetryProvider.get_instance().update_queue_depth(self._queue_depth)
        logger.debug(f"Job enqueued: {job_id}, queue depth: {self._queue_depth}")

        # Emit queue depth changed event
        self._emit_monitoring_event(
            MonitoringEventType.QUEUE_DEPTH_CHANGED,
            {
                "queue_depth": self._queue_depth,
                "job_id": job_id,
                "workflow_name": workflow_name,
                "priority": priority,
            },
        )

    def record_job_start(
        self,
        job_id: str,
        robot_id: Optional[str] = None,
    ) -> None:
        """
        Record a job starting execution.

        Args:
            job_id: Unique job identifier
            robot_id: ID of the robot executing the job
        """
        workflow_name = None
        with self._lock:
            if job_id in self._active_jobs:
                job = self._active_jobs[job_id]
                now = time.time()
                job["started_at"] = now
                job["robot_id"] = robot_id
                job["status"] = JobStatus.RUNNING
                workflow_name = job["workflow_name"]

                # Calculate queue wait time
                queue_wait = now - job["enqueued_at"]
                self._job_metrics.total_queue_wait_seconds += queue_wait

                if self._job_queue_wait_histogram:
                    self._job_queue_wait_histogram.record(
                        queue_wait,
                        {
                            "workflow.name": job["workflow_name"],
                            "job.priority": str(job["priority"]),
                        },
                    )

                self._queue_depth = max(0, self._queue_depth - 1)

            # Update robot status
            if robot_id:
                self._update_robot_status(robot_id, RobotStatus.BUSY, job_id)

        TelemetryProvider.get_instance().update_queue_depth(self._queue_depth)

        # Emit job status changed event
        self._emit_monitoring_event(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {
                "job_id": job_id,
                "workflow_name": workflow_name,
                "status": JobStatus.RUNNING.value,
                "robot_id": robot_id,
                "queue_depth": self._queue_depth,
            },
        )

    def record_job_complete(
        self,
        job_id: str,
        success: bool,
        duration_seconds: float,
        nodes_executed: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record a job completing execution.

        Args:
            job_id: Unique job identifier
            success: Whether the job completed successfully
            duration_seconds: Total execution duration
            nodes_executed: Number of nodes executed
            error_message: Error message if failed
        """
        robot_id = None
        workflow_name = "unknown"
        with self._lock:
            job = self._active_jobs.pop(job_id, None)
            robot_id = job.get("robot_id") if job else None
            workflow_name = job.get("workflow_name", "unknown") if job else "unknown"

            self._job_metrics.total_jobs += 1
            self._job_metrics.total_duration_seconds += duration_seconds
            self._job_metrics.total_nodes_executed += nodes_executed

            if success:
                self._job_metrics.completed_jobs += 1
            else:
                self._job_metrics.failed_jobs += 1

            # Update robot status
            if robot_id:
                self._update_robot_status(robot_id, RobotStatus.IDLE, None)
                robot = self._robots.get(robot_id)
                if robot:
                    if success:
                        robot.jobs_completed += 1
                    else:
                        robot.jobs_failed += 1
                    robot.last_job_at = datetime.now()

            # Record throughput
            self._queue_throughput_window.append(time.time())

        # Record to TelemetryProvider
        TelemetryProvider.get_instance().record_job_duration(
            duration_seconds=duration_seconds,
            workflow_name=workflow_name,
            job_id=job_id,
            success=success,
            robot_id=robot_id,
        )

        # Emit job status changed event
        final_status = JobStatus.COMPLETED if success else JobStatus.FAILED
        self._emit_monitoring_event(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {
                "job_id": job_id,
                "workflow_name": workflow_name,
                "status": final_status.value,
                "robot_id": robot_id,
                "duration_seconds": duration_seconds,
                "nodes_executed": nodes_executed,
                "success": success,
                "error_message": error_message,
            },
        )

    def record_job_retry(
        self,
        job_id: str,
        attempt_number: int,
        reason: str,
    ) -> None:
        """
        Record a job retry attempt.

        Args:
            job_id: Unique job identifier
            attempt_number: Current retry attempt number
            reason: Reason for retry
        """
        with self._lock:
            if job_id in self._active_jobs:
                self._active_jobs[job_id]["status"] = JobStatus.RETRYING
                self._active_jobs[job_id]["retry_count"] = attempt_number

        if self._job_retry_counter:
            self._job_retry_counter.add(
                1,
                {
                    "job.id": job_id,
                    "retry.attempt": str(attempt_number),
                    "retry.reason": reason,
                },
            )

    def record_job_cancel(self, job_id: str, reason: str = "user_requested") -> None:
        """
        Record a job cancellation.

        Args:
            job_id: Unique job identifier
            reason: Cancellation reason
        """
        with self._lock:
            job = self._active_jobs.pop(job_id, None)
            if job:
                self._job_metrics.cancelled_jobs += 1
                robot_id = job.get("robot_id")
                if robot_id:
                    self._update_robot_status(robot_id, RobotStatus.IDLE, None)

    # =========================================================================
    # Robot Metrics
    # =========================================================================

    def register_robot(self, robot_id: str) -> None:
        """
        Register a robot for metrics tracking.

        Args:
            robot_id: Unique robot identifier
        """
        with self._lock:
            if robot_id not in self._robots:
                self._robots[robot_id] = RobotMetrics(robot_id=robot_id)
                logger.debug(f"Robot registered for metrics: {robot_id}")

    def unregister_robot(self, robot_id: str) -> None:
        """
        Unregister a robot from metrics tracking.

        Args:
            robot_id: Unique robot identifier
        """
        with self._lock:
            self._robots.pop(robot_id, None)

    def _update_robot_status(
        self,
        robot_id: str,
        status: RobotStatus,
        job_id: Optional[str],
    ) -> None:
        """Update robot status and track time in each state."""
        if robot_id not in self._robots:
            self._robots[robot_id] = RobotMetrics(robot_id=robot_id)

        robot = self._robots[robot_id]
        now = datetime.now()

        # Calculate time in previous state
        if robot.current_job_started_at:
            duration = (now - robot.current_job_started_at).total_seconds()
            if robot.status == RobotStatus.BUSY:
                robot.total_busy_seconds += duration
            else:
                robot.total_idle_seconds += duration

        # Update to new state
        robot.status = status
        robot.current_job_id = job_id
        robot.current_job_started_at = now

        # Update global utilization metrics
        self._update_global_utilization()

        # Emit robot heartbeat event
        self._emit_monitoring_event(
            MonitoringEventType.ROBOT_HEARTBEAT,
            {
                "robot_id": robot_id,
                "status": status.value,
                "current_job_id": job_id,
                "jobs_completed": robot.jobs_completed,
                "jobs_failed": robot.jobs_failed,
                "utilization_percent": robot.utilization_percent,
                # TODO: Get actual CPU/memory from system metrics
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
            },
        )

    def _update_global_utilization(self) -> None:
        """Calculate and update global robot utilization."""
        if not self._robots:
            return

        active_count = sum(
            1 for r in self._robots.values() if r.status == RobotStatus.BUSY
        )
        total_count = len(self._robots)
        utilization = (active_count / total_count * 100) if total_count > 0 else 0.0

        TelemetryProvider.get_instance().update_robot_utilization(
            utilization_percent=utilization,
            active_robots=active_count,
        )

    def get_robot_metrics(self, robot_id: str) -> Optional[RobotMetrics]:
        """Get metrics for a specific robot."""
        return self._robots.get(robot_id)

    def get_all_robot_metrics(self) -> Dict[str, RobotMetrics]:
        """Get metrics for all registered robots."""
        return self._robots.copy()

    # =========================================================================
    # Node Metrics
    # =========================================================================

    @contextmanager
    def track_node_execution(
        self,
        node_type: str,
        node_id: str,
    ) -> Generator[None, None, None]:
        """
        Context manager for tracking node execution.

        Args:
            node_type: Type of node (e.g., "ClickNode")
            node_id: Unique node identifier

        Usage:
            with collector.track_node_execution("ClickNode", "node-123"):
                await node.execute(ctx)
        """
        start_time = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._record_node_metrics(node_type, node_id, success, duration_ms)

    def _record_node_metrics(
        self,
        node_type: str,
        node_id: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """Record node execution metrics."""
        with self._lock:
            if node_type not in self._node_metrics:
                self._node_metrics[node_type] = {
                    "total_executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_duration_ms": 0.0,
                }

            metrics = self._node_metrics[node_type]
            metrics["total_executions"] += 1
            metrics["total_duration_ms"] += duration_ms
            if success:
                metrics["successful"] += 1
            else:
                metrics["failed"] += 1

        if self._node_latency_histogram:
            self._node_latency_histogram.record(
                duration_ms,
                {
                    "node.type": node_type,
                    "node.success": str(success).lower(),
                },
            )

        TelemetryProvider.get_instance().record_node_execution(
            node_type=node_type,
            node_id=node_id,
            success=success,
            duration_ms=duration_ms,
        )

    def get_node_metrics(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get aggregated metrics for a node type."""
        return self._node_metrics.get(node_type)

    def get_all_node_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get aggregated metrics for all node types."""
        return self._node_metrics.copy()

    # =========================================================================
    # Self-Healing Metrics
    # =========================================================================

    def record_healing_attempt(
        self,
        selector: str,
        healing_strategy: str,
        success: bool,
        fallback_selector: Optional[str] = None,
    ) -> None:
        """
        Record a self-healing attempt.

        Args:
            selector: Original selector that failed
            healing_strategy: Strategy used (e.g., "attribute_fallback", "anchor")
            success: Whether healing succeeded
            fallback_selector: The selector that worked (if successful)
        """
        with self._lock:
            self._healing_attempts += 1
            if success:
                self._healing_successes += 1

        if self._healing_attempt_counter:
            self._healing_attempt_counter.add(
                1,
                {
                    "healing.strategy": healing_strategy,
                    "healing.success": str(success).lower(),
                },
            )

        if success and self._healing_success_counter:
            self._healing_success_counter.add(
                1,
                {
                    "healing.strategy": healing_strategy,
                },
            )

        if success:
            logger.info(
                f"Self-healing succeeded: {selector} -> {fallback_selector} "
                f"using {healing_strategy}"
            )
        else:
            logger.warning(
                f"Self-healing failed for selector: {selector} "
                f"using strategy: {healing_strategy}"
            )

    def get_healing_stats(self) -> Dict[str, Any]:
        """Get self-healing statistics."""
        with self._lock:
            success_rate = (
                (self._healing_successes / self._healing_attempts * 100)
                if self._healing_attempts > 0
                else 0.0
            )
            return {
                "total_attempts": self._healing_attempts,
                "successes": self._healing_successes,
                "failures": self._healing_attempts - self._healing_successes,
                "success_rate": success_rate,
            }

    # =========================================================================
    # Browser Pool Metrics
    # =========================================================================

    def record_browser_acquired(self) -> None:
        """Record a browser being acquired from pool."""
        if self._browser_pool_active:
            self._browser_pool_active.add(1)

    def record_browser_released(self) -> None:
        """Record a browser being returned to pool."""
        if self._browser_pool_active:
            self._browser_pool_active.add(-1)

    # =========================================================================
    # Aggregation Methods
    # =========================================================================

    def get_job_metrics(self) -> JobMetrics:
        """Get aggregated job metrics."""
        return self._job_metrics

    def get_queue_depth(self) -> int:
        """Get current queue depth."""
        return self._queue_depth

    def get_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active jobs."""
        return self._active_jobs.copy()

    def reset_metrics(self) -> None:
        """Reset all collected metrics (useful for testing)."""
        with self._lock:
            self._job_metrics = JobMetrics()
            self._active_jobs.clear()
            self._queue_depth = 0
            self._queue_throughput_window.clear()
            self._node_metrics.clear()
            self._healing_attempts = 0
            self._healing_successes = 0

        logger.debug("Metrics reset")


# =============================================================================
# Convenience Functions
# =============================================================================


def get_metrics_collector() -> RPAMetricsCollector:
    """Get the singleton metrics collector instance."""
    return RPAMetricsCollector.get_instance()
