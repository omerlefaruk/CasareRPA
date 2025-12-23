"""
Performance metrics system for CasareRPA.

Provides a unified interface for collecting, aggregating, and reporting
performance metrics from all system components including:
- Workflow execution timing
- Node execution statistics
- Resource pool metrics (browser, database, HTTP)
- Memory and CPU usage
- Cache hit rates
"""

import asyncio
import gc
import sys
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Deque, Dict, List, Optional

from loguru import logger

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class MetricType(Enum):
    """Types of metrics tracked."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass(slots=True)
class MetricValue:
    """A single metric measurement."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class TimerContext:
    """Context manager for timing operations."""

    metrics: "PerformanceMetrics"
    name: str
    labels: dict[str, str]
    start_time: float = field(default=0.0, init=False)

    def __enter__(self) -> "TimerContext":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.metrics.record_timing(self.name, elapsed_ms, self.labels)


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution tracking."""

    le: float  # less than or equal
    count: int = 0


class Histogram:
    """Histogram for tracking value distributions."""

    # Default buckets for timing (milliseconds)
    DEFAULT_BUCKETS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

    def __init__(self, buckets: list[float] | None = None) -> None:
        self._buckets = buckets or self.DEFAULT_BUCKETS
        self._bucket_counts = [0] * len(self._buckets)
        self._sum = 0.0
        self._count = 0
        self._min: float | None = None
        self._max: float | None = None

    def observe(self, value: float) -> None:
        """Record an observation."""
        self._sum += value
        self._count += 1

        if self._min is None or value < self._min:
            self._min = value
        if self._max is None or value > self._max:
            self._max = value

        for i, bucket in enumerate(self._buckets):
            if value <= bucket:
                self._bucket_counts[i] += 1

    @property
    def count(self) -> int:
        return self._count

    @property
    def sum(self) -> float:
        return self._sum

    @property
    def mean(self) -> float:
        return self._sum / self._count if self._count > 0 else 0.0

    @property
    def min(self) -> float | None:
        return self._min

    @property
    def max(self) -> float | None:
        return self._max

    def percentile(self, p: float) -> float:
        """Calculate percentile (approximate from buckets)."""
        if self._count == 0:
            return 0.0

        target = self._count * (p / 100)
        cumulative = 0

        for i, count in enumerate(self._bucket_counts):
            cumulative += count
            if cumulative >= target:
                return self._buckets[i]

        return self._buckets[-1]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self._count,
            "sum": self._sum,
            "mean": self.mean,
            "min": self._min,
            "max": self._max,
            "p50": self.percentile(50),
            "p90": self.percentile(90),
            "p99": self.percentile(99),
            "buckets": {
                f"le_{b}": c for b, c in zip(self._buckets, self._bucket_counts, strict=False)
            },
        }


class PerformanceMetrics:
    """
    Centralized performance metrics collection and reporting.

    Features:
    - Multiple metric types (counter, gauge, histogram, timer)
    - Label support for dimensional metrics
    - Time-windowed statistics
    - System resource monitoring (CPU, memory)
    - Integration with existing pools and caches
    """

    _instance: Optional["PerformanceMetrics"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        retention_seconds: float = 3600.0,  # 1 hour
        sample_interval: float = 1.0,  # 1 second
    ) -> None:
        self._retention_seconds = retention_seconds
        self._sample_interval = sample_interval

        # Metric storage
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, Histogram] = defaultdict(Histogram)
        self._timeseries: dict[str, deque[MetricValue]] = defaultdict(
            lambda: deque(maxlen=int(retention_seconds / sample_interval))
        )

        # Node execution tracking
        self._node_timings: dict[str, Histogram] = defaultdict(Histogram)
        self._node_counts: dict[str, int] = defaultdict(int)
        self._node_errors: dict[str, int] = defaultdict(int)

        # Workflow tracking
        self._workflow_timings: Histogram = Histogram()
        self._workflow_counts = {"started": 0, "completed": 0, "failed": 0}

        # System metrics
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None
        self._system_samples: deque[dict[str, float]] = deque(maxlen=60)

        # Callbacks for external metrics
        self._metric_callbacks: list[Callable[[], dict[str, Any]]] = []

        # Lock for thread safety
        self._metrics_lock = threading.Lock()

        # Background task
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @classmethod
    def get_instance(cls) -> "PerformanceMetrics":
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def increment(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter."""
        key = self._make_key(name, labels)
        with self._metrics_lock:
            self._counters[key] += value

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge value."""
        key = self._make_key(name, labels)
        with self._metrics_lock:
            self._gauges[key] = value
            self._timeseries[key].append(MetricValue(name=name, value=value, labels=labels or {}))

    def observe(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        with self._metrics_lock:
            if key not in self._histograms:
                self._histograms[key] = Histogram()
            self._histograms[key].observe(value)

    def record_timing(
        self,
        name: str,
        duration_ms: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a timing measurement."""
        self.observe(f"{name}_duration_ms", duration_ms, labels)

    def time(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> TimerContext:
        """Create a timer context manager."""
        return TimerContext(
            metrics=self,
            name=name,
            labels=labels or {},
        )

    def _make_key(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    # Node execution tracking
    def record_node_start(self, node_type: str, node_id: str) -> None:
        """Record a node starting execution."""
        with self._metrics_lock:
            self._node_counts[node_type] += 1
        self.increment("nodes_started", labels={"type": node_type})

    def record_node_complete(
        self,
        node_type: str,
        node_id: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record a node completing execution."""
        with self._metrics_lock:
            self._node_timings[node_type].observe(duration_ms)
            if not success:
                self._node_errors[node_type] += 1

        labels = {"type": node_type, "status": "success" if success else "error"}
        self.increment("nodes_completed", labels=labels)
        self.record_timing("node_execution", duration_ms, {"type": node_type})

    # Workflow tracking
    def record_workflow_start(self, workflow_id: str) -> None:
        """Record a workflow starting."""
        with self._metrics_lock:
            self._workflow_counts["started"] += 1
        self.increment("workflows_started")

    def record_workflow_complete(
        self,
        workflow_id: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record a workflow completing."""
        with self._metrics_lock:
            self._workflow_timings.observe(duration_ms)
            if success:
                self._workflow_counts["completed"] += 1
            else:
                self._workflow_counts["failed"] += 1

        status = "success" if success else "failed"
        self.increment("workflows_completed", labels={"status": status})
        self.record_timing("workflow_execution", duration_ms)

    # System resource monitoring
    def _sample_system_metrics(self) -> dict[str, float]:
        """Sample current system resource usage."""
        metrics: dict[str, float] = {}

        if self._process and PSUTIL_AVAILABLE:
            try:
                # CPU
                metrics["cpu_percent"] = self._process.cpu_percent()
                metrics["cpu_threads"] = self._process.num_threads()

                # Memory
                mem_info = self._process.memory_info()
                metrics["memory_rss_mb"] = mem_info.rss / (1024 * 1024)
                metrics["memory_vms_mb"] = mem_info.vms / (1024 * 1024)

                # File descriptors (Unix) / Handles (Windows)
                if sys.platform != "win32":
                    metrics["open_files"] = len(self._process.open_files())
                else:
                    metrics["handle_count"] = self._process.num_handles()

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug(f"Failed to sample process metrics: {e}")

            # System-wide metrics
            try:
                metrics["system_cpu_percent"] = psutil.cpu_percent()
                sys_mem = psutil.virtual_memory()
                metrics["system_memory_percent"] = sys_mem.percent
                metrics["system_memory_available_mb"] = sys_mem.available / (1024 * 1024)
            except Exception as e:
                logger.debug(f"Failed to sample system metrics: {e}")

        # Python-specific (gc_objects removed - too expensive, iterates ALL objects)
        metrics["gc_collections"] = sum(gc.get_count())

        return metrics

    def register_callback(
        self,
        callback: Callable[[], dict[str, Any]],
    ) -> None:
        """Register a callback for collecting external metrics."""
        self._metric_callbacks.append(callback)

    def unregister_callback(
        self,
        callback: Callable[[], dict[str, Any]],
    ) -> None:
        """Unregister a metrics callback."""
        if callback in self._metric_callbacks:
            self._metric_callbacks.remove(callback)

    async def start_background_collection(self) -> None:
        """Start background metrics collection."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Started background metrics collection")

    async def stop_background_collection(self) -> None:
        """Stop background metrics collection."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Stopped background metrics collection")

    async def _collection_loop(self) -> None:
        """Background loop for collecting metrics."""
        while self._running:
            try:
                # Sample system metrics
                system_metrics = self._sample_system_metrics()
                with self._metrics_lock:
                    self._system_samples.append(system_metrics)

                # Update gauges
                for name, value in system_metrics.items():
                    self.set_gauge(f"system_{name}", value)

                # Collect from callbacks
                for callback in self._metric_callbacks:
                    try:
                        external_metrics = callback()
                        for name, value in external_metrics.items():
                            if isinstance(value, (int, float)):
                                self.set_gauge(name, float(value))
                    except Exception as e:
                        logger.debug(f"Metrics callback error: {e}")

                await asyncio.sleep(self._sample_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self._sample_interval)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all metrics."""
        with self._metrics_lock:
            summary: dict[str, Any] = {
                "timestamp": datetime.now().isoformat(),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {name: hist.to_dict() for name, hist in self._histograms.items()},
                "nodes": {
                    "execution_counts": dict(self._node_counts),
                    "error_counts": dict(self._node_errors),
                    "timings": {name: hist.to_dict() for name, hist in self._node_timings.items()},
                },
                "workflows": {
                    "counts": self._workflow_counts.copy(),
                    "timings": self._workflow_timings.to_dict(),
                },
            }

            # Latest system metrics
            if self._system_samples:
                summary["system"] = dict(self._system_samples[-1])

            return summary

    def get_node_stats(self, node_type: str | None = None) -> dict[str, Any]:
        """Get statistics for node executions."""
        with self._metrics_lock:
            if node_type:
                return {
                    "type": node_type,
                    "count": self._node_counts.get(node_type, 0),
                    "errors": self._node_errors.get(node_type, 0),
                    "timing": self._node_timings[node_type].to_dict()
                    if node_type in self._node_timings
                    else None,
                }
            else:
                return {
                    node_type: {
                        "count": self._node_counts[node_type],
                        "errors": self._node_errors.get(node_type, 0),
                        "timing": self._node_timings[node_type].to_dict(),
                    }
                    for node_type in self._node_counts
                }

    def get_system_stats(self) -> dict[str, Any]:
        """Get system resource statistics."""
        with self._metrics_lock:
            if not self._system_samples:
                return {}

            # Calculate averages over samples
            metrics_sum: dict[str, float] = defaultdict(float)
            for sample in self._system_samples:
                for name, value in sample.items():
                    metrics_sum[name] += value

            count = len(self._system_samples)
            averages = {name: value / count for name, value in metrics_sum.items()}

            return {
                "current": dict(self._system_samples[-1]) if self._system_samples else {},
                "average": averages,
                "sample_count": count,
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._metrics_lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timeseries.clear()
            self._node_timings.clear()
            self._node_counts.clear()
            self._node_errors.clear()
            self._workflow_timings = Histogram()
            self._workflow_counts = {"started": 0, "completed": 0, "failed": 0}
            self._system_samples.clear()

        logger.info("Performance metrics reset")


# Convenience functions
def get_metrics() -> PerformanceMetrics:
    """Get the global performance metrics instance."""
    return PerformanceMetrics.get_instance()


def time_operation(name: str, labels: dict[str, str] | None = None) -> TimerContext:
    """Create a timer for an operation."""
    return get_metrics().time(name, labels)


__all__ = [
    "MetricType",
    "MetricValue",
    "TimerContext",
    "Histogram",
    "PerformanceMetrics",
    "get_metrics",
    "time_operation",
]
