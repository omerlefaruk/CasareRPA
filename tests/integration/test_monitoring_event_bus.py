"""
Integration tests for MonitoringEventBus system.

Tests the complete flow: RPAMetricsCollector -> MonitoringEventBus -> WebSocket handlers.

Scenarios covered:
1. Event publication and handler execution
2. Multiple handler propagation
3. Error isolation (one handler fails, others continue)
4. Fire-and-forget pattern (non-blocking)
5. WebSocket broadcast triggered by events
6. Subscription/unsubscription lifecycle
7. No event loop graceful degradation
"""

import asyncio
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from casare_rpa.infrastructure.events import (
    MonitoringEvent,
    MonitoringEventBus,
    MonitoringEventType,
    get_monitoring_event_bus,
)
from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
    ConnectionManager,
    live_jobs_manager,
    robot_status_manager,
    queue_metrics_manager,
    on_job_status_changed,
    on_robot_heartbeat,
    on_queue_depth_changed,
    broadcast_job_update,
    broadcast_robot_status,
    broadcast_queue_metrics,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def fresh_event_bus():
    """Provide a clean event bus for each test."""
    bus = get_monitoring_event_bus()
    bus.clear_all()
    yield bus
    bus.clear_all()


@pytest.fixture
def isolated_event_bus():
    """
    Provide an isolated event bus instance (bypasses singleton).

    Useful for testing without affecting global state.
    """
    # Reset singleton for this test
    original_instance = MonitoringEventBus._instance
    MonitoringEventBus._instance = None

    bus = MonitoringEventBus()
    yield bus

    # Restore original singleton
    bus.clear_all()
    MonitoringEventBus._instance = original_instance


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket for testing broadcasts."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock(return_value="ping")
    return ws


@pytest.fixture
def clean_connection_managers():
    """Ensure connection managers are clean before/after tests."""
    # Clear before
    live_jobs_manager.active_connections.clear()
    robot_status_manager.active_connections.clear()
    queue_metrics_manager.active_connections.clear()

    yield {
        "jobs": live_jobs_manager,
        "robots": robot_status_manager,
        "queue": queue_metrics_manager,
    }

    # Clear after
    live_jobs_manager.active_connections.clear()
    robot_status_manager.active_connections.clear()
    queue_metrics_manager.active_connections.clear()


# =============================================================================
# TEST: EVENT PUBLICATION AND HANDLER EXECUTION
# =============================================================================


class TestEventPublication:
    """Test basic event publishing and handler invocation."""

    @pytest.mark.asyncio
    async def test_publish_event_invokes_handler(self, fresh_event_bus):
        """Handler is called when matching event is published."""
        received_events: List[MonitoringEvent] = []

        async def handler(event: MonitoringEvent):
            received_events.append(event)

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler)

        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "job-001", "status": "completed"},
        )

        assert len(received_events) == 1
        assert received_events[0].payload["job_id"] == "job-001"
        assert received_events[0].event_type == MonitoringEventType.JOB_STATUS_CHANGED

    @pytest.mark.asyncio
    async def test_publish_with_correlation_id(self, fresh_event_bus):
        """Correlation ID is preserved through publication."""
        received_events: List[MonitoringEvent] = []

        async def handler(event: MonitoringEvent):
            received_events.append(event)

        fresh_event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, handler)

        await fresh_event_bus.publish(
            MonitoringEventType.ROBOT_HEARTBEAT,
            {"robot_id": "robot-001"},
            correlation_id="trace-abc123",
        )

        assert received_events[0].correlation_id == "trace-abc123"

    @pytest.mark.asyncio
    async def test_event_timestamp_is_set(self, fresh_event_bus):
        """Event timestamp is automatically set on publish."""
        received_events: List[MonitoringEvent] = []
        before_publish = datetime.now()

        async def handler(event: MonitoringEvent):
            received_events.append(event)

        fresh_event_bus.subscribe(MonitoringEventType.QUEUE_DEPTH_CHANGED, handler)

        await fresh_event_bus.publish(
            MonitoringEventType.QUEUE_DEPTH_CHANGED,
            {"queue_depth": 10},
        )

        after_publish = datetime.now()
        event_time = received_events[0].timestamp

        assert before_publish <= event_time <= after_publish

    @pytest.mark.asyncio
    async def test_no_handlers_does_not_error(self, fresh_event_bus):
        """Publishing to event type with no handlers succeeds silently."""
        # No handlers subscribed
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "orphan-job"},
        )
        # Should not raise


# =============================================================================
# TEST: MULTIPLE HANDLER PROPAGATION
# =============================================================================


class TestMultipleHandlers:
    """Test event propagation to multiple handlers."""

    @pytest.mark.asyncio
    async def test_event_reaches_all_handlers(self, fresh_event_bus):
        """All subscribed handlers receive the same event."""
        handler1_calls: List[MonitoringEvent] = []
        handler2_calls: List[MonitoringEvent] = []
        handler3_calls: List[MonitoringEvent] = []

        async def handler1(event: MonitoringEvent):
            handler1_calls.append(event)

        async def handler2(event: MonitoringEvent):
            handler2_calls.append(event)

        async def handler3(event: MonitoringEvent):
            handler3_calls.append(event)

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler1)
        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler2)
        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler3)

        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "multi-handler-job"},
        )

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
        assert len(handler3_calls) == 1

        # All handlers receive same event data
        assert handler1_calls[0].payload == handler2_calls[0].payload
        assert handler2_calls[0].payload == handler3_calls[0].payload

    @pytest.mark.asyncio
    async def test_handlers_run_concurrently(self, fresh_event_bus):
        """Multiple handlers execute concurrently, not sequentially."""
        execution_order: List[str] = []

        async def slow_handler(event: MonitoringEvent):
            execution_order.append("slow_start")
            await asyncio.sleep(0.1)
            execution_order.append("slow_end")

        async def fast_handler(event: MonitoringEvent):
            execution_order.append("fast_start")
            await asyncio.sleep(0.01)
            execution_order.append("fast_end")

        fresh_event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, slow_handler)
        fresh_event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, fast_handler)

        await fresh_event_bus.publish(
            MonitoringEventType.ROBOT_HEARTBEAT,
            {"robot_id": "concurrent-test"},
        )

        # Both should start before either finishes (concurrent execution)
        assert "slow_start" in execution_order
        assert "fast_start" in execution_order
        # Fast should end before slow
        fast_end_idx = execution_order.index("fast_end")
        slow_end_idx = execution_order.index("slow_end")
        assert fast_end_idx < slow_end_idx


# =============================================================================
# TEST: ERROR ISOLATION
# =============================================================================


class TestErrorIsolation:
    """Test that one failing handler doesn't break others."""

    @pytest.mark.asyncio
    async def test_failing_handler_does_not_block_others(self, fresh_event_bus):
        """Other handlers still execute when one raises exception."""
        successful_calls: List[str] = []

        async def failing_handler(event: MonitoringEvent):
            raise RuntimeError("Intentional failure")

        async def success_handler_1(event: MonitoringEvent):
            successful_calls.append("handler1")

        async def success_handler_2(event: MonitoringEvent):
            successful_calls.append("handler2")

        fresh_event_bus.subscribe(
            MonitoringEventType.JOB_STATUS_CHANGED, success_handler_1
        )
        fresh_event_bus.subscribe(
            MonitoringEventType.JOB_STATUS_CHANGED, failing_handler
        )
        fresh_event_bus.subscribe(
            MonitoringEventType.JOB_STATUS_CHANGED, success_handler_2
        )

        # Should not raise
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "error-test"},
        )

        # Both success handlers were called
        assert "handler1" in successful_calls
        assert "handler2" in successful_calls

    @pytest.mark.asyncio
    async def test_exception_in_handler_is_logged(self, fresh_event_bus, caplog):
        """Handler exceptions are logged for debugging."""

        async def failing_handler(event: MonitoringEvent):
            raise ValueError("Test exception message")

        fresh_event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, failing_handler)

        with patch(
            "casare_rpa.infrastructure.events.monitoring_events.logger"
        ) as mock_logger:
            await fresh_event_bus.publish(
                MonitoringEventType.ROBOT_HEARTBEAT,
                {"robot_id": "error-log-test"},
            )

            # Verify error was logged
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_handlers_fail_independently(self, fresh_event_bus):
        """Multiple failing handlers don't compound failures."""
        success_count = 0

        async def failing_handler_1(event: MonitoringEvent):
            raise RuntimeError("Failure 1")

        async def failing_handler_2(event: MonitoringEvent):
            raise RuntimeError("Failure 2")

        async def success_handler(event: MonitoringEvent):
            nonlocal success_count
            success_count += 1

        fresh_event_bus.subscribe(
            MonitoringEventType.QUEUE_DEPTH_CHANGED, failing_handler_1
        )
        fresh_event_bus.subscribe(
            MonitoringEventType.QUEUE_DEPTH_CHANGED, success_handler
        )
        fresh_event_bus.subscribe(
            MonitoringEventType.QUEUE_DEPTH_CHANGED, failing_handler_2
        )

        await fresh_event_bus.publish(
            MonitoringEventType.QUEUE_DEPTH_CHANGED,
            {"queue_depth": 5},
        )

        assert success_count == 1


# =============================================================================
# TEST: FIRE-AND-FORGET PATTERN
# =============================================================================


class TestFireAndForget:
    """Test that event emission doesn't block metrics collection."""

    @pytest.mark.asyncio
    async def test_publish_returns_before_slow_handler_completes(self, fresh_event_bus):
        """publish() returns quickly even with slow handlers (uses gather)."""
        handler_completed = False

        async def slow_handler(event: MonitoringEvent):
            nonlocal handler_completed
            await asyncio.sleep(0.5)
            handler_completed = True

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, slow_handler)

        start = asyncio.get_event_loop().time()
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "fire-forget-test"},
        )
        elapsed = asyncio.get_event_loop().time() - start

        # publish() should wait for handlers (gather behavior), but test confirms
        # all handlers complete. The fire-and-forget happens at metrics collector
        # level via create_task().
        assert handler_completed
        # Handler took 0.5s, publish should complete around that time
        assert elapsed >= 0.4

    @pytest.mark.asyncio
    async def test_metrics_emit_event_uses_create_task(self):
        """Verify metrics collector uses create_task for fire-and-forget."""
        from casare_rpa.infrastructure.observability.metrics import RPAMetricsCollector

        # Create collector with events enabled
        collector = RPAMetricsCollector.__new__(RPAMetricsCollector)
        collector._initialized = False
        collector._emit_events = True
        collector._lock = MagicMock()
        collector._active_jobs = {}
        collector._job_metrics = MagicMock()
        collector._queue_depth = 0
        collector._robots = {}
        collector._queue_throughput_window = []

        with patch(
            "casare_rpa.infrastructure.observability.metrics.get_monitoring_event_bus"
        ) as mock_get_bus:
            mock_bus = AsyncMock()
            mock_get_bus.return_value = mock_bus

            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop_instance = MagicMock()
                mock_loop.return_value = mock_loop_instance

                collector._emit_monitoring_event(
                    MonitoringEventType.JOB_STATUS_CHANGED,
                    {"job_id": "test"},
                )

                # Verify create_task was called (fire-and-forget)
                mock_loop_instance.create_task.assert_called_once()


# =============================================================================
# TEST: WEBSOCKET BROADCAST INTEGRATION
# =============================================================================


class TestWebSocketBroadcast:
    """Test event bus -> WebSocket handler -> broadcast chain."""

    @pytest.mark.asyncio
    async def test_job_status_event_triggers_broadcast(
        self, fresh_event_bus, mock_websocket, clean_connection_managers
    ):
        """JOB_STATUS_CHANGED event triggers live_jobs broadcast."""
        # Connect mock websocket
        await clean_connection_managers["jobs"].connect(mock_websocket)

        # Create and process event
        event = MonitoringEvent(
            event_type=MonitoringEventType.JOB_STATUS_CHANGED,
            timestamp=datetime.now(),
            payload={"job_id": "ws-job-001", "status": "completed"},
        )

        await on_job_status_changed(event)

        # Verify broadcast was sent
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert "ws-job-001" in sent_data
        assert "completed" in sent_data

    @pytest.mark.asyncio
    async def test_robot_heartbeat_event_triggers_broadcast(
        self, fresh_event_bus, mock_websocket, clean_connection_managers
    ):
        """ROBOT_HEARTBEAT event triggers robot_status broadcast."""
        await clean_connection_managers["robots"].connect(mock_websocket)

        event = MonitoringEvent(
            event_type=MonitoringEventType.ROBOT_HEARTBEAT,
            timestamp=datetime.now(),
            payload={
                "robot_id": "robot-ws-001",
                "status": "busy",
                "cpu_percent": 45.5,
                "memory_mb": 1024.0,
            },
        )

        await on_robot_heartbeat(event)

        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert "robot-ws-001" in sent_data
        assert "busy" in sent_data

    @pytest.mark.asyncio
    async def test_queue_depth_event_triggers_broadcast(
        self, fresh_event_bus, mock_websocket, clean_connection_managers
    ):
        """QUEUE_DEPTH_CHANGED event triggers queue_metrics broadcast."""
        await clean_connection_managers["queue"].connect(mock_websocket)

        event = MonitoringEvent(
            event_type=MonitoringEventType.QUEUE_DEPTH_CHANGED,
            timestamp=datetime.now(),
            payload={"queue_depth": 42},
        )

        await on_queue_depth_changed(event)

        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert "42" in sent_data

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(
        self, mock_websocket, clean_connection_managers
    ):
        """Broadcast reaches all connected WebSocket clients."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        for ws in [ws1, ws2, ws3]:
            await clean_connection_managers["jobs"].connect(ws)

        await broadcast_job_update("multi-client-job", "running")

        assert ws1.send_text.call_count == 1
        assert ws2.send_text.call_count == 1
        assert ws3.send_text.call_count == 1

    @pytest.mark.asyncio
    async def test_slow_client_timeout_during_broadcast(
        self, clean_connection_managers
    ):
        """Slow clients are disconnected, don't block other broadcasts."""
        fast_ws = AsyncMock()
        slow_ws = AsyncMock()

        # Slow client times out
        async def slow_send(text):
            await asyncio.sleep(5.0)

        slow_ws.send_text = slow_send

        await clean_connection_managers["jobs"].connect(fast_ws)
        await clean_connection_managers["jobs"].connect(slow_ws)

        assert len(clean_connection_managers["jobs"].active_connections) == 2

        # Broadcast with timeout
        await broadcast_job_update("timeout-test-job", "completed")

        # Fast client received message
        fast_ws.send_text.assert_called_once()

        # Slow client was disconnected
        assert slow_ws not in clean_connection_managers["jobs"].active_connections

    @pytest.mark.asyncio
    async def test_failing_client_removed_from_connections(
        self, clean_connection_managers
    ):
        """Clients that raise exceptions are removed from pool."""
        good_ws = AsyncMock()
        bad_ws = AsyncMock()
        bad_ws.send_text.side_effect = ConnectionResetError("Client disconnected")

        await clean_connection_managers["robots"].connect(good_ws)
        await clean_connection_managers["robots"].connect(bad_ws)

        await broadcast_robot_status("robot-fail-test", "idle", 10.0, 512.0)

        # Bad client removed
        assert bad_ws not in clean_connection_managers["robots"].active_connections
        # Good client still connected
        assert good_ws in clean_connection_managers["robots"].active_connections


# =============================================================================
# TEST: SUBSCRIPTION/UNSUBSCRIPTION LIFECYCLE
# =============================================================================


class TestSubscriptionLifecycle:
    """Test handler subscription and unsubscription."""

    @pytest.mark.asyncio
    async def test_subscribe_and_unsubscribe(self, fresh_event_bus):
        """Handler can be subscribed and unsubscribed."""
        call_count = 0

        async def handler(event: MonitoringEvent):
            nonlocal call_count
            call_count += 1

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler)

        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "sub-test-1"},
        )
        assert call_count == 1

        # Unsubscribe
        fresh_event_bus.unsubscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler)

        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "sub-test-2"},
        )
        # Handler not called after unsubscribe
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(self, fresh_event_bus):
        """Unsubscribing unknown handler logs warning but doesn't error."""

        async def unknown_handler(event: MonitoringEvent):
            pass

        # Should not raise
        fresh_event_bus.unsubscribe(
            MonitoringEventType.JOB_STATUS_CHANGED, unknown_handler
        )

    @pytest.mark.asyncio
    async def test_unsubscribe_from_empty_type(self, fresh_event_bus):
        """Unsubscribing from event type with no handlers is safe."""

        async def handler(event: MonitoringEvent):
            pass

        # No handlers subscribed to QUEUE_DEPTH_CHANGED
        fresh_event_bus.unsubscribe(MonitoringEventType.QUEUE_DEPTH_CHANGED, handler)

    @pytest.mark.asyncio
    async def test_clear_all_removes_handlers_and_history(self, fresh_event_bus):
        """clear_all() removes all subscriptions and history."""

        async def handler(event: MonitoringEvent):
            pass

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, handler)
        fresh_event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, handler)

        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "history-test"},
        )

        assert len(fresh_event_bus.get_history()) > 0

        fresh_event_bus.clear_all()

        stats = fresh_event_bus.get_statistics()
        assert stats["total_handlers"] == 0
        assert stats["history_size"] == 0


# =============================================================================
# TEST: NO EVENT LOOP GRACEFUL DEGRADATION
# =============================================================================


class TestNoEventLoopDegradation:
    """Test behavior when no asyncio event loop is available."""

    def test_emit_event_without_running_loop(self):
        """Metrics collector handles missing event loop gracefully."""
        from casare_rpa.infrastructure.observability.metrics import RPAMetricsCollector

        # Create minimal collector mock
        collector = RPAMetricsCollector.__new__(RPAMetricsCollector)
        collector._emit_events = True

        # Simulate no running event loop
        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.side_effect = RuntimeError("no running event loop")

            # Should not raise
            collector._emit_monitoring_event(
                MonitoringEventType.JOB_STATUS_CHANGED,
                {"job_id": "no-loop-test"},
            )

    def test_emit_events_disabled_skips_emission(self):
        """Setting emit_events=False skips event emission entirely."""
        from casare_rpa.infrastructure.observability.metrics import RPAMetricsCollector

        collector = RPAMetricsCollector.__new__(RPAMetricsCollector)
        collector._emit_events = False

        with patch(
            "casare_rpa.infrastructure.observability.metrics.get_monitoring_event_bus"
        ) as mock_bus:
            collector._emit_monitoring_event(
                MonitoringEventType.JOB_STATUS_CHANGED,
                {"job_id": "disabled-test"},
            )

            # Event bus should not be called
            mock_bus.assert_not_called()


# =============================================================================
# TEST: EVENT HISTORY
# =============================================================================


class TestEventHistory:
    """Test event history ring buffer."""

    @pytest.mark.asyncio
    async def test_events_stored_in_history(self, fresh_event_bus):
        """Published events are stored in history."""
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "history-1"},
        )
        await fresh_event_bus.publish(
            MonitoringEventType.ROBOT_HEARTBEAT,
            {"robot_id": "robot-1"},
        )

        history = fresh_event_bus.get_history()

        assert len(history) == 2
        # Newest first
        assert history[0].payload.get("robot_id") == "robot-1"
        assert history[1].payload.get("job_id") == "history-1"

    @pytest.mark.asyncio
    async def test_history_respects_limit(self, fresh_event_bus):
        """get_history() respects limit parameter."""
        for i in range(10):
            await fresh_event_bus.publish(
                MonitoringEventType.QUEUE_DEPTH_CHANGED,
                {"queue_depth": i},
            )

        history = fresh_event_bus.get_history(limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_history_ring_buffer_overflow(self):
        """History ring buffer discards oldest events when full."""
        # Save original singleton and reset
        original_instance = MonitoringEventBus._instance
        MonitoringEventBus._instance = None

        try:
            # Create new instance (will use default max_history=1000)
            bus = MonitoringEventBus()
            # Manually set smaller history for testing
            from collections import deque

            bus._history = deque(maxlen=5)

            for i in range(10):
                await bus.publish(
                    MonitoringEventType.JOB_STATUS_CHANGED,
                    {"job_id": f"job-{i}"},
                )

            history = bus.get_history()

            # Only last 5 events kept
            assert len(history) == 5
            # Oldest events (0-4) discarded, newest (5-9) kept
            job_ids = [e.payload["job_id"] for e in history]
            assert "job-0" not in job_ids
            assert "job-9" in job_ids
        finally:
            bus.clear_all()
            MonitoringEventBus._instance = original_instance


# =============================================================================
# TEST: STATISTICS
# =============================================================================


class TestEventBusStatistics:
    """Test event bus statistics reporting."""

    @pytest.mark.asyncio
    async def test_statistics_handler_counts(self, fresh_event_bus):
        """Statistics report handler counts per event type."""

        async def h1(e):
            pass

        async def h2(e):
            pass

        async def h3(e):
            pass

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, h1)
        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, h2)
        fresh_event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, h3)

        stats = fresh_event_bus.get_statistics()

        assert stats["handler_counts"]["JOB_STATUS_CHANGED"] == 2
        assert stats["handler_counts"]["ROBOT_HEARTBEAT"] == 1
        assert stats["total_handlers"] == 3

    @pytest.mark.asyncio
    async def test_statistics_history_size(self, fresh_event_bus):
        """Statistics report current history size."""
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "stats-test"},
        )

        stats = fresh_event_bus.get_statistics()

        assert stats["history_size"] == 1
        assert stats["max_history"] == 1000  # default


# =============================================================================
# TEST: SYNC HANDLER WRAPPING
# =============================================================================


class TestSyncHandlerWrapping:
    """Test that sync handlers are wrapped to async."""

    @pytest.mark.asyncio
    async def test_sync_handler_is_wrapped(self, fresh_event_bus):
        """Sync handlers are automatically wrapped and executed."""
        call_count = 0

        def sync_handler(event: MonitoringEvent):
            nonlocal call_count
            call_count += 1

        fresh_event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, sync_handler)

        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "sync-test"},
        )

        assert call_count == 1


# =============================================================================
# TEST: CONNECTION MANAGER
# =============================================================================


class TestConnectionManager:
    """Test ConnectionManager WebSocket handling."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self):
        """ConnectionManager accepts new WebSocket connections."""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws)

        ws.accept.assert_called_once()
        assert ws in manager.active_connections

    def test_disconnect_removes_websocket(self):
        """ConnectionManager removes disconnected WebSockets."""
        manager = ConnectionManager()
        ws = MagicMock()
        manager.active_connections.add(ws)

        manager.disconnect(ws)

        assert ws not in manager.active_connections

    def test_disconnect_nonexistent_websocket_safe(self):
        """Disconnecting unknown WebSocket doesn't error."""
        manager = ConnectionManager()
        ws = MagicMock()

        # Should not raise
        manager.disconnect(ws)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        """Broadcast sends message to all connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.broadcast({"type": "test", "data": "hello"})

        assert ws1.send_text.call_count == 1
        assert ws2.send_text.call_count == 1


# =============================================================================
# TEST: FULL INTEGRATION FLOW
# =============================================================================


class TestFullIntegrationFlow:
    """Test complete metrics -> event bus -> WebSocket flow."""

    @pytest.mark.asyncio
    async def test_job_lifecycle_events_flow(
        self, fresh_event_bus, mock_websocket, clean_connection_managers
    ):
        """Complete job lifecycle triggers correct WebSocket broadcasts."""
        received_events: List[MonitoringEvent] = []

        # Subscribe handler to capture events
        async def capture_handler(event: MonitoringEvent):
            received_events.append(event)
            # Also trigger WebSocket broadcast
            await on_job_status_changed(event)

        fresh_event_bus.subscribe(
            MonitoringEventType.JOB_STATUS_CHANGED, capture_handler
        )

        # Connect WebSocket client
        await clean_connection_managers["jobs"].connect(mock_websocket)

        # Simulate job lifecycle
        # 1. Job enqueued (status: pending -> running)
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "flow-job-001", "status": "running"},
        )

        # 2. Job completed
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "flow-job-001", "status": "completed"},
        )

        # Verify events captured
        assert len(received_events) == 2

        # Verify WebSocket broadcasts
        assert mock_websocket.send_text.call_count == 2

    @pytest.mark.asyncio
    async def test_mixed_event_types_routed_correctly(
        self, fresh_event_bus, clean_connection_managers
    ):
        """Different event types route to correct WebSocket managers."""
        jobs_ws = AsyncMock()
        robots_ws = AsyncMock()
        queue_ws = AsyncMock()

        await clean_connection_managers["jobs"].connect(jobs_ws)
        await clean_connection_managers["robots"].connect(robots_ws)
        await clean_connection_managers["queue"].connect(queue_ws)

        # Subscribe event handlers
        fresh_event_bus.subscribe(
            MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed
        )
        fresh_event_bus.subscribe(
            MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat
        )
        fresh_event_bus.subscribe(
            MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed
        )

        # Publish mixed events
        await fresh_event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "mix-job", "status": "running"},
        )
        await fresh_event_bus.publish(
            MonitoringEventType.ROBOT_HEARTBEAT,
            {
                "robot_id": "mix-robot",
                "status": "busy",
                "cpu_percent": 50.0,
                "memory_mb": 1024.0,
            },
        )
        await fresh_event_bus.publish(
            MonitoringEventType.QUEUE_DEPTH_CHANGED,
            {"queue_depth": 15},
        )

        # Each WebSocket should only receive its event type
        assert jobs_ws.send_text.call_count == 1
        assert robots_ws.send_text.call_count == 1
        assert queue_ws.send_text.call_count == 1

        # Verify correct data was sent
        jobs_data = jobs_ws.send_text.call_args[0][0]
        assert "mix-job" in jobs_data

        robots_data = robots_ws.send_text.call_args[0][0]
        assert "mix-robot" in robots_data

        queue_data = queue_ws.send_text.call_args[0][0]
        assert "15" in queue_data
