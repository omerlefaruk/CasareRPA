"""
Heartbeat Service for Robot Agent.

Sends periodic heartbeats to the orchestrator with system metrics.
Monitors connection health and triggers reconnection on failures.
"""

import asyncio
import platform
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    pass

# Optional psutil for detailed metrics
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not installed - system metrics will be limited")


class HeartbeatService:
    """
    Service for sending periodic heartbeats to orchestrator.

    Collects system metrics (CPU, memory, disk) and sends them
    along with heartbeat messages to keep the connection alive
    and report robot health.

    Attributes:
        interval: Seconds between heartbeats
        on_heartbeat: Callback to send heartbeat message
        on_failure: Callback when heartbeat fails
    """

    def __init__(
        self,
        interval: int = 30,
        on_heartbeat: Callable[[dict[str, Any]], None] | None = None,
        on_failure: Callable[[Exception], None] | None = None,
    ):
        """
        Initialize heartbeat service.

        Args:
            interval: Seconds between heartbeats (default: 30)
            on_heartbeat: Async callback to send heartbeat data
            on_failure: Callback when heartbeat sending fails
        """
        self.interval = interval
        self.on_heartbeat = on_heartbeat
        self.on_failure = on_failure

        self._running = False
        self._task: asyncio.Task | None = None
        self._last_heartbeat: datetime | None = None
        self._consecutive_failures = 0
        self._total_heartbeats = 0

        # Cached system info (doesn't change)
        self._system_info = self._get_system_info()

    def _get_system_info(self) -> dict[str, Any]:
        """Get static system information."""
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

        if HAS_PSUTIL:
            try:
                info["cpu_count_logical"] = psutil.cpu_count(logical=True)
                info["cpu_count_physical"] = psutil.cpu_count(logical=False)
                info["memory_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
            except Exception as e:
                logger.warning(f"Failed to get CPU/memory info: {e}")

        return info

    def get_system_metrics(self) -> dict[str, Any]:
        """
        Get current system metrics.

        Returns:
            Dictionary with CPU, memory, disk usage percentages.
            Returns empty metrics if psutil is not available.
        """
        metrics: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if not HAS_PSUTIL:
            metrics["warning"] = "psutil not installed - metrics unavailable"
            return metrics

        try:
            # CPU usage (averaged over 0.1 second)
            metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)

            # Memory usage
            mem = psutil.virtual_memory()
            metrics["memory_percent"] = mem.percent
            metrics["memory_used_gb"] = round(mem.used / (1024**3), 2)
            metrics["memory_available_gb"] = round(mem.available / (1024**3), 2)

            # Disk usage for main drive
            try:
                if platform.system() == "Windows":
                    disk = psutil.disk_usage("C:\\")
                else:
                    disk = psutil.disk_usage("/")
                metrics["disk_percent"] = disk.percent
                metrics["disk_used_gb"] = round(disk.used / (1024**3), 2)
                metrics["disk_free_gb"] = round(disk.free / (1024**3), 2)
            except Exception as e:
                logger.debug(f"Failed to get disk metrics: {e}")

            # Network I/O (since boot)
            try:
                net = psutil.net_io_counters()
                metrics["net_bytes_sent"] = net.bytes_sent
                metrics["net_bytes_recv"] = net.bytes_recv
            except Exception as e:
                logger.debug(f"Failed to get network metrics: {e}")

            # Process count
            try:
                metrics["process_count"] = len(psutil.pids())
            except Exception:
                pass

            # System uptime
            try:
                boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=UTC)
                uptime_seconds = (datetime.now(UTC) - boot_time).total_seconds()
                metrics["uptime_hours"] = round(uptime_seconds / 3600, 2)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    def get_health_status(self) -> str:
        """
        Determine overall health status based on metrics.

        Returns:
            Health status: "healthy", "warning", or "critical"
        """
        if not HAS_PSUTIL:
            return "unknown"

        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent

            if cpu > 90 or mem > 90:
                return "critical"
            elif cpu > 70 or mem > 80:
                return "warning"
            return "healthy"
        except Exception:
            return "unknown"

    async def start(self) -> None:
        """Start the heartbeat loop."""
        if self._running:
            logger.warning("Heartbeat service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Heartbeat service started (interval: {self.interval}s)")

    async def stop(self) -> None:
        """Stop the heartbeat loop gracefully."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info(f"Heartbeat service stopped (sent {self._total_heartbeats} heartbeats)")

    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(self.interval)

                if not self._running:
                    break

                await self._send_heartbeat()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_failures += 1
                logger.error(f"Heartbeat error (consecutive: {self._consecutive_failures}): {e}")

                if self.on_failure:
                    try:
                        self.on_failure(e)
                    except Exception as callback_error:
                        logger.error(f"Heartbeat failure callback error: {callback_error}")

                # Exponential backoff on repeated failures
                if self._consecutive_failures >= 3:
                    backoff = min(30, 2 ** (self._consecutive_failures - 2))
                    logger.warning(f"Multiple heartbeat failures, backing off {backoff}s")
                    await asyncio.sleep(backoff)

    async def _send_heartbeat(self) -> None:
        """Send a single heartbeat."""
        if not self.on_heartbeat:
            logger.debug("No heartbeat callback configured")
            return

        heartbeat_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "metrics": self.get_system_metrics(),
            "health": self.get_health_status(),
            "system_info": self._system_info,
            "heartbeat_count": self._total_heartbeats + 1,
        }

        try:
            # Call the callback (could be sync or async)
            result = self.on_heartbeat(heartbeat_data)
            if asyncio.iscoroutine(result):
                await result

            self._last_heartbeat = datetime.now(UTC)
            self._consecutive_failures = 0
            self._total_heartbeats += 1

            logger.debug(f"Heartbeat sent (#{self._total_heartbeats})")

        except Exception as e:
            raise RuntimeError(f"Failed to send heartbeat: {e}") from e

    async def send_immediate(self) -> None:
        """Send an immediate heartbeat outside the regular schedule."""
        await self._send_heartbeat()

    @property
    def is_running(self) -> bool:
        """Check if heartbeat service is running."""
        return self._running

    @property
    def last_heartbeat(self) -> datetime | None:
        """Get timestamp of last successful heartbeat."""
        return self._last_heartbeat

    @property
    def total_heartbeats(self) -> int:
        """Get total number of heartbeats sent."""
        return self._total_heartbeats

    @property
    def consecutive_failures(self) -> int:
        """Get count of consecutive heartbeat failures."""
        return self._consecutive_failures

    def get_status(self) -> dict[str, Any]:
        """Get heartbeat service status."""
        return {
            "running": self._running,
            "interval": self.interval,
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
            "total_heartbeats": self._total_heartbeats,
            "consecutive_failures": self._consecutive_failures,
        }
