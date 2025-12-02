"""
CasareRPA Infrastructure Layer - System Metrics Collection

Provides system-level metrics collection using psutil:
- CPU usage (per-process and system-wide)
- Memory usage (RSS, VMS, percent)
- Disk I/O statistics
- Network I/O statistics

Thread-safe singleton implementation for efficient resource monitoring.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Optional

from loguru import logger

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None


@dataclass
class ProcessMetrics:
    """Metrics for the current process."""

    cpu_percent: float  # CPU usage percentage (0-100)
    memory_rss_mb: float  # Resident Set Size in MB
    memory_vms_mb: float  # Virtual Memory Size in MB
    memory_percent: float  # Memory usage percentage (0-100)
    num_threads: int  # Number of threads
    num_fds: int  # Number of file descriptors (Unix only)
    open_files: int  # Number of open files


@dataclass
class SystemMetrics:
    """System-wide metrics."""

    cpu_percent: float  # System-wide CPU usage percentage (0-100)
    cpu_count: int  # Number of CPU cores
    memory_total_mb: float  # Total system memory in MB
    memory_available_mb: float  # Available system memory in MB
    memory_percent: float  # System memory usage percentage (0-100)
    disk_read_mb: float  # Total disk read in MB (since boot)
    disk_write_mb: float  # Total disk write in MB (since boot)
    net_sent_mb: float  # Total network bytes sent in MB (since boot)
    net_recv_mb: float  # Total network bytes received in MB (since boot)


class SystemMetricsCollector:
    """
    Thread-safe singleton for collecting system and process metrics.

    Uses psutil to gather CPU, memory, disk, and network statistics.
    Falls back to zero values if psutil is not available.

    Usage:
        collector = SystemMetricsCollector.get_instance()

        # Get current process metrics
        process = collector.get_process_metrics()
        print(f"CPU: {process.cpu_percent}%, Memory: {process.memory_rss_mb}MB")

        # Get system-wide metrics
        system = collector.get_system_metrics()
        print(f"System CPU: {system.cpu_percent}%")
    """

    _instance: Optional["SystemMetricsCollector"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "SystemMetricsCollector":
        """Thread-safe singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "SystemMetricsCollector":
        """Get the singleton instance."""
        return cls()

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._process: Optional["psutil.Process"] = None
        self._last_cpu_call_time: float = 0.0

        if HAS_PSUTIL:
            try:
                self._process = psutil.Process(os.getpid())
                # Initial call to establish baseline for cpu_percent
                self._process.cpu_percent(interval=None)
                logger.debug("SystemMetricsCollector initialized with psutil")
            except Exception as e:
                logger.warning(f"Failed to initialize psutil process: {e}")
                self._process = None
        else:
            logger.warning(
                "psutil not available - system metrics will return zero values"
            )

        self._initialized = True

    def get_process_metrics(self) -> ProcessMetrics:
        """
        Get metrics for the current process.

        Returns:
            ProcessMetrics with current process statistics
        """
        if not HAS_PSUTIL or self._process is None:
            return ProcessMetrics(
                cpu_percent=0.0,
                memory_rss_mb=0.0,
                memory_vms_mb=0.0,
                memory_percent=0.0,
                num_threads=1,
                num_fds=0,
                open_files=0,
            )

        try:
            # CPU percent - non-blocking call (uses time since last call)
            cpu_percent = self._process.cpu_percent(interval=None)

            # Memory info
            mem_info = self._process.memory_info()
            memory_rss_mb = mem_info.rss / (1024 * 1024)
            memory_vms_mb = mem_info.vms / (1024 * 1024)
            memory_percent = self._process.memory_percent()

            # Thread count
            num_threads = self._process.num_threads()

            # File descriptors (Unix only)
            try:
                num_fds = self._process.num_fds()
            except (AttributeError, psutil.AccessDenied):
                # Not available on Windows or access denied
                num_fds = 0

            # Open files
            try:
                open_files = len(self._process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0

            return ProcessMetrics(
                cpu_percent=cpu_percent,
                memory_rss_mb=round(memory_rss_mb, 2),
                memory_vms_mb=round(memory_vms_mb, 2),
                memory_percent=round(memory_percent, 2),
                num_threads=num_threads,
                num_fds=num_fds,
                open_files=open_files,
            )

        except psutil.NoSuchProcess:
            logger.warning("Process no longer exists")
            return ProcessMetrics(
                cpu_percent=0.0,
                memory_rss_mb=0.0,
                memory_vms_mb=0.0,
                memory_percent=0.0,
                num_threads=1,
                num_fds=0,
                open_files=0,
            )
        except Exception as e:
            logger.warning(f"Failed to get process metrics: {e}")
            return ProcessMetrics(
                cpu_percent=0.0,
                memory_rss_mb=0.0,
                memory_vms_mb=0.0,
                memory_percent=0.0,
                num_threads=1,
                num_fds=0,
                open_files=0,
            )

    def get_system_metrics(self) -> SystemMetrics:
        """
        Get system-wide metrics.

        Returns:
            SystemMetrics with system statistics
        """
        if not HAS_PSUTIL:
            return SystemMetrics(
                cpu_percent=0.0,
                cpu_count=1,
                memory_total_mb=0.0,
                memory_available_mb=0.0,
                memory_percent=0.0,
                disk_read_mb=0.0,
                disk_write_mb=0.0,
                net_sent_mb=0.0,
                net_recv_mb=0.0,
            )

        try:
            # CPU - non-blocking call
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count() or 1

            # Memory
            mem = psutil.virtual_memory()
            memory_total_mb = mem.total / (1024 * 1024)
            memory_available_mb = mem.available / (1024 * 1024)
            memory_percent = mem.percent

            # Disk I/O
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    disk_read_mb = disk_io.read_bytes / (1024 * 1024)
                    disk_write_mb = disk_io.write_bytes / (1024 * 1024)
                else:
                    disk_read_mb = 0.0
                    disk_write_mb = 0.0
            except Exception:
                disk_read_mb = 0.0
                disk_write_mb = 0.0

            # Network I/O
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    net_sent_mb = net_io.bytes_sent / (1024 * 1024)
                    net_recv_mb = net_io.bytes_recv / (1024 * 1024)
                else:
                    net_sent_mb = 0.0
                    net_recv_mb = 0.0
            except Exception:
                net_sent_mb = 0.0
                net_recv_mb = 0.0

            return SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_total_mb=round(memory_total_mb, 2),
                memory_available_mb=round(memory_available_mb, 2),
                memory_percent=round(memory_percent, 2),
                disk_read_mb=round(disk_read_mb, 2),
                disk_write_mb=round(disk_write_mb, 2),
                net_sent_mb=round(net_sent_mb, 2),
                net_recv_mb=round(net_recv_mb, 2),
            )

        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                cpu_count=1,
                memory_total_mb=0.0,
                memory_available_mb=0.0,
                memory_percent=0.0,
                disk_read_mb=0.0,
                disk_write_mb=0.0,
                net_sent_mb=0.0,
                net_recv_mb=0.0,
            )

    def get_cpu_percent(self) -> float:
        """
        Get current process CPU usage percentage.

        Convenience method for quick CPU checks.

        Returns:
            CPU usage as percentage (0-100)
        """
        metrics = self.get_process_metrics()
        return metrics.cpu_percent

    def get_memory_mb(self) -> float:
        """
        Get current process memory usage in MB (RSS).

        Convenience method for quick memory checks.

        Returns:
            Memory RSS in megabytes
        """
        metrics = self.get_process_metrics()
        return metrics.memory_rss_mb


# =============================================================================
# Convenience Functions
# =============================================================================


def get_system_metrics_collector() -> SystemMetricsCollector:
    """Get the singleton system metrics collector instance."""
    return SystemMetricsCollector.get_instance()


def get_cpu_percent() -> float:
    """Get current process CPU usage percentage."""
    return get_system_metrics_collector().get_cpu_percent()


def get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    return get_system_metrics_collector().get_memory_mb()
