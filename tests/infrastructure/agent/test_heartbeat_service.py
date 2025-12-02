"""
Tests for HeartbeatService.

Tests cover:
- Happy path: Heartbeat sending, metrics collection, health status
- Sad path: Callback failures, service errors, missing psutil
- Edge cases: Rapid start/stop, consecutive failures, backoff behavior
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.infrastructure.agent.heartbeat_service import (
    HeartbeatService,
    HAS_PSUTIL,
)


# ============================================================================
# Happy Path Tests - Basic Operations
# ============================================================================


class TestHeartbeatServiceCreation:
    """Test HeartbeatService initialization."""

    def test_create_with_defaults(self):
        """Creating service with defaults succeeds."""
        service = HeartbeatService()

        assert service.interval == 30
        assert service.on_heartbeat is None
        assert service.on_failure is None
        assert service.is_running is False
        assert service.total_heartbeats == 0

    def test_create_with_custom_interval(self):
        """Creating service with custom interval succeeds."""
        service = HeartbeatService(interval=60)
        assert service.interval == 60

    def test_create_with_callbacks(
        self, heartbeat_callback, heartbeat_failure_callback
    ):
        """Creating service with callbacks succeeds."""
        service = HeartbeatService(
            interval=15,
            on_heartbeat=heartbeat_callback,
            on_failure=heartbeat_failure_callback,
        )

        assert service.interval == 15
        assert service.on_heartbeat is heartbeat_callback
        assert service.on_failure is heartbeat_failure_callback


class TestHeartbeatServiceStartStop:
    """Test HeartbeatService start/stop operations."""

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self):
        """Starting service sets running flag."""
        service = HeartbeatService(interval=1)

        await service.start()
        assert service.is_running is True

        await service.stop()
        assert service.is_running is False

    @pytest.mark.asyncio
    async def test_stop_clears_task(self):
        """Stopping service clears internal task."""
        service = HeartbeatService(interval=1)

        await service.start()
        assert service._task is not None

        await service.stop()
        assert service._task is None

    @pytest.mark.asyncio
    async def test_double_start_warns_and_returns(self):
        """Starting already running service does not create duplicate tasks."""
        service = HeartbeatService(interval=1)

        await service.start()
        task1 = service._task

        await service.start()  # Should warn and return
        task2 = service._task

        assert task1 is task2  # Same task, not duplicated

        await service.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running_is_safe(self):
        """Stopping non-running service does not raise."""
        service = HeartbeatService(interval=1)

        await service.stop()  # Should not raise
        assert service.is_running is False


class TestHeartbeatServiceSending:
    """Test heartbeat sending functionality."""

    @pytest.mark.asyncio
    async def test_send_immediate_invokes_callback(self, heartbeat_callback):
        """send_immediate() invokes heartbeat callback."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        await service.send_immediate()

        assert len(heartbeat_callback.calls) == 1
        assert "timestamp" in heartbeat_callback.calls[0]
        assert "metrics" in heartbeat_callback.calls[0]
        assert "health" in heartbeat_callback.calls[0]

    @pytest.mark.asyncio
    async def test_heartbeat_data_structure(self, heartbeat_callback):
        """Heartbeat data contains expected fields."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        await service.send_immediate()

        data = heartbeat_callback.calls[0]
        assert "timestamp" in data
        assert "metrics" in data
        assert "health" in data
        assert "system_info" in data
        assert "heartbeat_count" in data

    @pytest.mark.asyncio
    async def test_heartbeat_increments_counter(self, heartbeat_callback):
        """Each heartbeat increments total counter."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        assert service.total_heartbeats == 0

        await service.send_immediate()
        assert service.total_heartbeats == 1

        await service.send_immediate()
        assert service.total_heartbeats == 2

    @pytest.mark.asyncio
    async def test_heartbeat_updates_last_heartbeat(self, heartbeat_callback):
        """Heartbeat updates last_heartbeat timestamp."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        assert service.last_heartbeat is None

        await service.send_immediate()

        assert service.last_heartbeat is not None
        assert isinstance(service.last_heartbeat, datetime)

    @pytest.mark.asyncio
    async def test_heartbeat_resets_consecutive_failures(self, heartbeat_callback):
        """Successful heartbeat resets consecutive failures counter."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        # Simulate previous failures
        service._consecutive_failures = 3

        await service.send_immediate()

        assert service.consecutive_failures == 0


# ============================================================================
# System Metrics Tests
# ============================================================================


class TestHeartbeatServiceMetrics:
    """Test system metrics collection."""

    def test_get_system_metrics_returns_timestamp(self):
        """System metrics always includes timestamp."""
        service = HeartbeatService()
        metrics = service.get_system_metrics()

        assert "timestamp" in metrics

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not installed")
    def test_get_system_metrics_with_psutil(self):
        """System metrics includes CPU and memory when psutil available."""
        service = HeartbeatService()
        metrics = service.get_system_metrics()

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "memory_used_gb" in metrics
        assert "memory_available_gb" in metrics

    def test_get_system_metrics_without_psutil(self):
        """System metrics handles missing psutil gracefully."""
        with patch.dict("sys.modules", {"psutil": None}):
            with patch(
                "casare_rpa.infrastructure.agent.heartbeat_service.HAS_PSUTIL",
                False,
            ):
                service = HeartbeatService()
                metrics = service.get_system_metrics()

                assert "timestamp" in metrics
                assert "warning" in metrics

    def test_get_system_info_includes_platform(self):
        """System info includes platform information."""
        service = HeartbeatService()
        info = service._system_info

        assert "platform" in info
        assert "platform_release" in info
        assert "python_version" in info
        assert "architecture" in info


class TestHeartbeatServiceHealthStatus:
    """Test health status determination."""

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not installed")
    def test_health_status_returns_valid_value(self):
        """Health status returns one of valid values."""
        service = HeartbeatService()
        status = service.get_health_status()

        assert status in ["healthy", "warning", "critical", "unknown"]

    def test_health_status_without_psutil_returns_unknown(self):
        """Health status returns unknown when psutil missing."""
        with patch(
            "casare_rpa.infrastructure.agent.heartbeat_service.HAS_PSUTIL",
            False,
        ):
            service = HeartbeatService()
            status = service.get_health_status()

            assert status == "unknown"

    def test_health_status_critical_on_high_cpu(self, mock_psutil_high_load):
        """Health status is critical when CPU > 90%."""
        with patch(
            "casare_rpa.infrastructure.agent.heartbeat_service.psutil",
            mock_psutil_high_load,
        ):
            with patch(
                "casare_rpa.infrastructure.agent.heartbeat_service.HAS_PSUTIL",
                True,
            ):
                service = HeartbeatService()
                status = service.get_health_status()

                assert status == "critical"


# ============================================================================
# Sad Path Tests - Failure Handling
# ============================================================================


class TestHeartbeatServiceFailures:
    """Test failure handling in heartbeat service."""

    @pytest.mark.asyncio
    async def test_callback_exception_raises_runtime_error(self):
        """Callback exception is wrapped in RuntimeError."""

        async def failing_callback(data: Dict[str, Any]) -> None:
            raise Exception("Callback failed")

        service = HeartbeatService(
            interval=60,
            on_heartbeat=failing_callback,
        )

        with pytest.raises(RuntimeError, match="Failed to send heartbeat"):
            await service.send_immediate()

    @pytest.mark.asyncio
    async def test_failure_callback_invoked_on_error(self, heartbeat_failure_callback):
        """Failure callback is invoked when heartbeat loop errors."""

        async def failing_callback(data: Dict[str, Any]) -> None:
            raise Exception("Callback failed")

        service = HeartbeatService(
            interval=0.1,  # Fast interval for testing
            on_heartbeat=failing_callback,
            on_failure=heartbeat_failure_callback,
        )

        await service.start()
        await asyncio.sleep(0.3)  # Allow loop to run
        await service.stop()

        # Failure callback should have been called
        assert len(heartbeat_failure_callback.calls) > 0

    @pytest.mark.asyncio
    async def test_consecutive_failures_tracked(self):
        """Consecutive failures are tracked."""
        failure_count = 0

        async def failing_callback(data: Dict[str, Any]) -> None:
            nonlocal failure_count
            failure_count += 1
            raise Exception("Failure")

        def on_failure(e):
            pass

        service = HeartbeatService(
            interval=0.05,
            on_heartbeat=failing_callback,
            on_failure=on_failure,
        )

        await service.start()
        await asyncio.sleep(0.3)
        await service.stop()

        assert service.consecutive_failures > 0

    @pytest.mark.asyncio
    async def test_no_callback_sends_nothing(self):
        """Service without callback does not error."""
        service = HeartbeatService(interval=60)

        # Should not raise
        await service.send_immediate()

        assert service.total_heartbeats == 0  # No callback, no increment


# ============================================================================
# Status Reporting Tests
# ============================================================================


class TestHeartbeatServiceStatus:
    """Test status reporting functionality."""

    def test_get_status_when_not_running(self):
        """Status shows not running when service stopped."""
        service = HeartbeatService(interval=30)
        status = service.get_status()

        assert status["running"] is False
        assert status["interval"] == 30
        assert status["last_heartbeat"] is None
        assert status["total_heartbeats"] == 0
        assert status["consecutive_failures"] == 0

    @pytest.mark.asyncio
    async def test_get_status_when_running(self, heartbeat_callback):
        """Status shows running when service active."""
        service = HeartbeatService(
            interval=30,
            on_heartbeat=heartbeat_callback,
        )

        await service.start()
        await service.send_immediate()

        status = service.get_status()

        assert status["running"] is True
        assert status["total_heartbeats"] == 1
        assert status["last_heartbeat"] is not None

        await service.stop()


# ============================================================================
# Async Callback Tests
# ============================================================================


class TestHeartbeatServiceAsyncCallbacks:
    """Test async callback handling."""

    @pytest.mark.asyncio
    async def test_async_callback_awaited(self):
        """Async callbacks are properly awaited."""
        calls = []

        async def async_callback(data: Dict[str, Any]) -> None:
            await asyncio.sleep(0.01)  # Simulate async work
            calls.append(data)

        service = HeartbeatService(
            interval=60,
            on_heartbeat=async_callback,
        )

        await service.send_immediate()

        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_sync_callback_works(self):
        """Sync callbacks work without await."""
        calls = []

        def sync_callback(data: Dict[str, Any]) -> None:
            calls.append(data)

        service = HeartbeatService(
            interval=60,
            on_heartbeat=sync_callback,
        )

        await service.send_immediate()

        assert len(calls) == 1


# ============================================================================
# Edge Cases
# ============================================================================


class TestHeartbeatServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_rapid_start_stop_cycles(self):
        """Rapid start/stop cycles do not cause issues."""
        service = HeartbeatService(interval=1)

        for _ in range(5):
            await service.start()
            await service.stop()

        assert service.is_running is False

    @pytest.mark.asyncio
    async def test_multiple_sends_without_start(self, heartbeat_callback):
        """Multiple send_immediate calls work without start()."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        for _ in range(3):
            await service.send_immediate()

        assert service.total_heartbeats == 3
        assert len(heartbeat_callback.calls) == 3

    @pytest.mark.asyncio
    async def test_heartbeat_count_in_data_matches_total(self, heartbeat_callback):
        """Heartbeat count in data matches total_heartbeats property."""
        service = HeartbeatService(
            interval=60,
            on_heartbeat=heartbeat_callback,
        )

        await service.send_immediate()
        await service.send_immediate()
        await service.send_immediate()

        # Each heartbeat_count should be sequential
        assert heartbeat_callback.calls[0]["heartbeat_count"] == 1
        assert heartbeat_callback.calls[1]["heartbeat_count"] == 2
        assert heartbeat_callback.calls[2]["heartbeat_count"] == 3

    @pytest.mark.asyncio
    async def test_stop_during_sleep_cancels_cleanly(self):
        """Stopping during sleep interval cancels cleanly."""
        service = HeartbeatService(interval=60)  # Long interval

        await service.start()

        # Stop almost immediately (while sleeping in loop)
        await asyncio.sleep(0.1)
        await service.stop()

        assert service.is_running is False

    def test_system_info_cached(self):
        """System info is cached on init (not re-collected)."""
        service = HeartbeatService()

        info1 = service._system_info
        info2 = service._system_info

        assert info1 is info2  # Same object, cached

    @pytest.mark.asyncio
    async def test_failure_callback_exception_handled(self):
        """Exception in failure callback is handled gracefully."""

        async def failing_heartbeat(data: Dict[str, Any]) -> None:
            raise Exception("Heartbeat error")

        def failing_on_failure(error: Exception) -> None:
            raise Exception("Failure callback error")

        service = HeartbeatService(
            interval=0.05,
            on_heartbeat=failing_heartbeat,
            on_failure=failing_on_failure,
        )

        await service.start()
        await asyncio.sleep(0.2)
        await service.stop()

        # Should complete without raising - failure callback error is caught
        assert True
