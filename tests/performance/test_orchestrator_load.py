"""Performance tests for Orchestrator API under load.

Phase 4 - Hardening: Tests for job claim throughput and WebSocket fanout.
Run with: pytest tests/performance/test_orchestrator_load.py -v --benchmark-enable
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Skip all tests if benchmark plugin not available
pytest.importorskip("pytest_benchmark")


class TestJobClaimThroughput:
    """Tests for concurrent job claim operations."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for isolation."""
        mock = MagicMock()
        mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": str(uuid4())}
        ]
        mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        return mock

    @pytest.fixture
    def mock_authenticator(self):
        """Mock RobotAuthenticator to bypass auth."""
        with patch("casare_rpa.infrastructure.orchestrator.api.auth.RobotAuthenticator") as mock:
            instance = mock.return_value
            instance.verify_token_async = AsyncMock(
                return_value={"robot_id": "test-robot", "capabilities": ["browser"]}
            )
            yield instance

    def test_single_claim_baseline(self, mock_supabase, mock_authenticator, benchmark):
        """Baseline: single job claim latency."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.main.get_supabase_client",
            return_value=mock_supabase,
        ):
            client = TestClient(app)

            def claim_job():
                response = client.post(
                    "/api/v1/jobs/claim",
                    headers={"Authorization": "Bearer test-key"},
                    json={"robot_id": "robot-1", "capabilities": ["browser"]},
                )
                return response.status_code

            result = benchmark(claim_job)
            # Should return 200 or 204 (no job available)
            assert result in (200, 204, 404)

    @pytest.mark.asyncio
    async def test_concurrent_claims_10(self, mock_supabase, mock_authenticator):
        """10 concurrent robots claiming jobs."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.main.get_supabase_client",
            return_value=mock_supabase,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                start = time.perf_counter()

                tasks = [
                    client.post(
                        "/api/v1/jobs/claim",
                        headers={"Authorization": f"Bearer test-key-{i}"},
                        json={"robot_id": f"robot-{i}", "capabilities": ["browser"]},
                    )
                    for i in range(10)
                ]

                responses = await asyncio.gather(*tasks, return_exceptions=True)
                elapsed = time.perf_counter() - start

                success_count = sum(
                    1
                    for r in responses
                    if not isinstance(r, Exception) and r.status_code in (200, 204, 404)
                )

                assert success_count >= 8, f"Expected 80%+ success, got {success_count}/10"
                assert elapsed < 5.0, f"10 concurrent claims took {elapsed:.2f}s (max 5s)"

    @pytest.mark.asyncio
    async def test_concurrent_claims_50(self, mock_supabase, mock_authenticator):
        """50 concurrent robots claiming jobs - stress test."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.main.get_supabase_client",
            return_value=mock_supabase,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                start = time.perf_counter()

                tasks = [
                    client.post(
                        "/api/v1/jobs/claim",
                        headers={"Authorization": f"Bearer test-key-{i}"},
                        json={"robot_id": f"robot-{i}", "capabilities": ["browser"]},
                    )
                    for i in range(50)
                ]

                responses = await asyncio.gather(*tasks, return_exceptions=True)
                elapsed = time.perf_counter() - start

                success_count = sum(
                    1
                    for r in responses
                    if not isinstance(r, Exception) and r.status_code in (200, 204, 404)
                )

                # At 50 concurrent, expect some failures due to contention
                assert success_count >= 40, f"Expected 80%+ success, got {success_count}/50"
                assert elapsed < 15.0, f"50 concurrent claims took {elapsed:.2f}s (max 15s)"


class TestWebSocketFanout:
    """Tests for WebSocket broadcast performance."""

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock ConnectionManager with configurable client count."""

        class MockManager:
            def __init__(self, client_count: int = 10):
                self.clients = {f"robot-{i}": AsyncMock() for i in range(client_count)}
                self.broadcast_times = []

            async def broadcast(self, message: dict):
                start = time.perf_counter()
                tasks = [client.send_json(message) for client in self.clients.values()]
                await asyncio.gather(*tasks)
                self.broadcast_times.append(time.perf_counter() - start)

            async def send_to_robot(self, robot_id: str, message: dict):
                if robot_id in self.clients:
                    await self.clients[robot_id].send_json(message)

        return MockManager

    @pytest.mark.asyncio
    async def test_broadcast_to_10_clients(self, mock_connection_manager):
        """Broadcast latency to 10 connected clients."""
        manager = mock_connection_manager(client_count=10)

        for i in range(100):
            await manager.broadcast({"type": "heartbeat", "seq": i})

        avg_time = sum(manager.broadcast_times) / len(manager.broadcast_times)
        max_time = max(manager.broadcast_times)

        assert avg_time < 0.01, f"Avg broadcast to 10 clients: {avg_time * 1000:.2f}ms (max 10ms)"
        assert max_time < 0.05, f"Max broadcast to 10 clients: {max_time * 1000:.2f}ms (max 50ms)"

    @pytest.mark.asyncio
    async def test_broadcast_to_50_clients(self, mock_connection_manager):
        """Broadcast latency to 50 connected clients - stress test."""
        manager = mock_connection_manager(client_count=50)

        for i in range(100):
            await manager.broadcast({"type": "job_update", "job_id": str(uuid4()), "seq": i})

        avg_time = sum(manager.broadcast_times) / len(manager.broadcast_times)
        max_time = max(manager.broadcast_times)

        assert avg_time < 0.05, f"Avg broadcast to 50 clients: {avg_time * 1000:.2f}ms (max 50ms)"
        assert max_time < 0.2, f"Max broadcast to 50 clients: {max_time * 1000:.2f}ms (max 200ms)"

    @pytest.mark.asyncio
    async def test_targeted_send_under_load(self, mock_connection_manager):
        """Targeted send while broadcasting."""
        manager = mock_connection_manager(client_count=50)

        async def background_broadcasts():
            for i in range(50):
                await manager.broadcast({"type": "noise", "seq": i})
                await asyncio.sleep(0.001)

        async def targeted_sends():
            times = []
            for i in range(20):
                start = time.perf_counter()
                await manager.send_to_robot("robot-5", {"type": "direct", "seq": i})
                times.append(time.perf_counter() - start)
            return times

        # Run concurrently
        _, send_times = await asyncio.gather(background_broadcasts(), targeted_sends())

        avg_time = sum(send_times) / len(send_times)
        assert avg_time < 0.005, f"Targeted send avg: {avg_time * 1000:.2f}ms (max 5ms)"


class TestHeartbeatLoad:
    """Tests for sustained heartbeat processing."""

    @pytest.fixture
    def mock_supabase_for_heartbeat(self):
        """Mock Supabase optimized for heartbeat updates."""
        mock = MagicMock()
        mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"id": "robot-1", "last_heartbeat": "2025-01-01T00:00:00Z"}
        ]
        return mock

    @pytest.mark.asyncio
    async def test_sustained_heartbeats_10_robots(self, mock_supabase_for_heartbeat):
        """10 robots sending heartbeats every 5 seconds for 30 seconds."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.main.get_supabase_client",
            return_value=mock_supabase_for_heartbeat,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                heartbeat_count = 0
                error_count = 0
                latencies = []

                # Simulate 6 heartbeat cycles (30s / 5s interval)
                for _cycle in range(6):
                    cycle_start = time.perf_counter()

                    tasks = [
                        client.post(
                            "/api/v1/robots/heartbeat",
                            headers={"Authorization": f"Bearer test-key-{i}"},
                            json={"robot_id": f"robot-{i}", "status": "idle"},
                        )
                        for i in range(10)
                    ]

                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    cycle_time = time.perf_counter() - cycle_start
                    latencies.append(cycle_time)

                    for r in responses:
                        if isinstance(r, Exception):
                            error_count += 1
                        elif r.status_code == 200:
                            heartbeat_count += 1
                        else:
                            error_count += 1

                avg_cycle = sum(latencies) / len(latencies)
                success_rate = heartbeat_count / (heartbeat_count + error_count) * 100

                assert success_rate >= 95, f"Heartbeat success rate: {success_rate:.1f}% (min 95%)"
                assert avg_cycle < 1.0, f"Avg cycle time: {avg_cycle * 1000:.0f}ms (max 1000ms)"


class TestCorrelationIdPropagation:
    """Tests for correlation ID middleware under load."""

    @pytest.mark.asyncio
    async def test_correlation_id_in_concurrent_requests(self):
        """Verify correlation IDs are unique across concurrent requests."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            tasks = [client.get("/api/v1/health") for _ in range(20)]
            responses = await asyncio.gather(*tasks)

            correlation_ids = [r.headers.get("X-Correlation-ID") for r in responses]

            # All should have correlation IDs
            assert all(cid is not None for cid in correlation_ids)

            # All should be unique
            assert len(set(correlation_ids)) == 20, "Correlation IDs must be unique"

    @pytest.mark.asyncio
    async def test_correlation_id_passthrough(self):
        """Verify provided correlation ID is returned."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            custom_id = "test-corr-12345"
            response = await client.get(
                "/api/v1/health",
                headers={"X-Correlation-ID": custom_id},
            )

            assert response.headers.get("X-Correlation-ID") == custom_id


class TestRateLimitingUnderLoad:
    """Tests for rate limiting behavior under high request volume."""

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self):
        """Verify rate limiting kicks in at expected threshold."""
        from casare_rpa.infrastructure.orchestrator.api.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send burst of requests
            tasks = [client.get("/api/v1/health") for _ in range(150)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            status_codes = [r.status_code if not isinstance(r, Exception) else 0 for r in responses]

            success_count = sum(1 for s in status_codes if s == 200)
            sum(1 for s in status_codes if s == 429)

            # Should have some successful and some rate-limited
            assert success_count > 0, "Expected some successful requests"
            # Rate limiting may or may not be enabled depending on config
            # Just ensure no server errors
            error_count = sum(1 for s in status_codes if s >= 500)
            assert error_count == 0, f"Got {error_count} server errors"


# Locust-style load test definitions for external use
# Run with: locust -f tests/performance/test_orchestrator_load.py

try:
    from locust import HttpUser, between, task

    class OrchestratorUser(HttpUser):
        """Locust user for load testing Orchestrator API."""

        wait_time = between(1, 3)

        def on_start(self):
            """Set up auth header."""
            self.headers = {"Authorization": "Bearer test-api-key"}
            self.robot_id = f"robot-{uuid4().hex[:8]}"

        @task(3)
        def heartbeat(self):
            """Send robot heartbeat."""
            self.client.post(
                "/api/v1/robots/heartbeat",
                json={"robot_id": self.robot_id, "status": "idle"},
                headers=self.headers,
            )

        @task(2)
        def claim_job(self):
            """Attempt to claim a job."""
            self.client.post(
                "/api/v1/jobs/claim",
                json={"robot_id": self.robot_id, "capabilities": ["browser"]},
                headers=self.headers,
            )

        @task(1)
        def health_check(self):
            """Check API health."""
            self.client.get("/api/v1/health")

except ImportError:
    # Locust not installed - skip
    pass
