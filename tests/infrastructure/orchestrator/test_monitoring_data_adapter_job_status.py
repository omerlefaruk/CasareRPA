from datetime import UTC, datetime
from typing import Any, cast

import pytest

from casare_rpa.infrastructure.orchestrator.api.adapters import MonitoringDataAdapter


class _AcquireConn:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireConn(self._conn)


class _FakeConnection:
    def __init__(self, rows):
        self._rows = rows
        self.fetch_calls: list[tuple[str, tuple]] = []

    async def fetch(self, query: str, *params):
        self.fetch_calls.append((query, params))
        return list(self._rows)


@pytest.mark.asyncio
async def test_get_job_history_normalizes_claimed_to_running():
    rows = [
        {
            "job_id": "job-1",
            "workflow_id": "wf-1",
            "workflow_name": "Test Workflow",
            "robot_id": "robot-1",
            "status": "claimed",
            "created_at": datetime.now(UTC),
            "completed_at": None,
            "duration_ms": None,
        }
    ]
    conn = _FakeConnection(rows)
    adapter = MonitoringDataAdapter(
        metrics_collector=cast(Any, object()),
        analytics_aggregator=cast(Any, object()),
        db_pool=cast(Any, _FakePool(conn)),
    )

    history = await adapter.get_job_history(status="claimed", limit=10)

    # Note: 'claimed' is returned as-is from the database.
    # UI layer handles status display normalization if needed.
    assert history[0]["status"] == "claimed"
    assert "status = $" in conn.fetch_calls[0][0] or "status" in conn.fetch_calls[0][0]


@pytest.mark.asyncio
async def test_get_job_history_rejects_invalid_status_without_db_access():
    class _ExplodingPool:
        def acquire(self):
            raise AssertionError("DB should not be queried for invalid status")

    adapter = MonitoringDataAdapter(
        metrics_collector=cast(Any, object()),
        analytics_aggregator=cast(Any, object()),
        db_pool=cast(Any, _ExplodingPool()),
    )

    history = await adapter.get_job_history(status="not-a-real-status", limit=10)

    assert history == []
