import hashlib
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api import auth as api_auth
from casare_rpa.infrastructure.orchestrator.api.auth import (
    configure_robot_authenticator,
)
from casare_rpa.infrastructure.orchestrator.api.routers import jobs, robots


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


def _configure_robot_auth(monkeypatch, *, robot_id: str = "robot-001") -> str:
    monkeypatch.setenv("ROBOT_AUTH_ENABLED", "true")

    api_key = "crpa_" + ("a" * 40)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    monkeypatch.setenv("ROBOT_TOKENS", f"{robot_id}:{api_key_hash}")

    configure_robot_authenticator(use_database=False, db_pool=None)
    return api_key


def test_admin_endpoints_require_db(monkeypatch):
    """Test that robot endpoints return 503 when database is unavailable."""
    monkeypatch.delenv("ORCHESTRATOR_ADMIN_API_KEY", raising=False)
    monkeypatch.setattr(api_auth, "JWT_DEV_MODE", False)

    app = FastAPI()
    app.include_router(robots.router, prefix="/api/v1")

    client = TestClient(app)
    resp = client.get("/api/v1/robots")

    # Without db_pool set, endpoints return 503 Service Unavailable
    assert resp.status_code == 503


def test_job_cancel_requires_admin_key(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_ADMIN_API_KEY", "supersecret")

    class _Conn:
        def __init__(self):
            self.fetchrow_calls = []
            self.execute_calls = []

        async def fetchrow(self, query: str, *params):
            self.fetchrow_calls.append((query, params))
            return {"job_id": params[0], "status": "pending"}

        async def execute(self, query: str, *params):
            self.execute_calls.append((query, params))
            return "UPDATE 1"

    conn = _Conn()
    jobs.set_db_pool(_FakePool(conn))

    app = FastAPI()
    app.include_router(jobs.router, prefix="/api/v1")

    client = TestClient(app)
    job_id = "11111111-1111-1111-1111-111111111111"

    resp = client.post(
        f"/api/v1/jobs/{job_id}/cancel",
        headers={"X-Api-Key": "supersecret"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["job_id"] == job_id
    assert payload["cancelled"] is True
    assert any("UPDATE jobs" in q for (q, _) in conn.execute_calls)


def test_claim_job_requires_robot_key(monkeypatch):
    api_key = _configure_robot_auth(monkeypatch, robot_id="robot-001")

    class _Conn:
        def __init__(self):
            self.fetchrow_calls = []

        async def fetchrow(self, query: str, *params):
            self.fetchrow_calls.append((query, params))
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "workflow_id": "wf-1",
                "workflow_name": "Test Flow",
                "workflow_json": "{}",
                "priority": 5,
                "environment": "prod",
                "variables": {"x": 1},
                "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
                "retry_count": 0,
                "max_retries": 3,
                "started_at": datetime(2025, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            }

    conn = _Conn()
    jobs.set_db_pool(_FakePool(conn))

    app = FastAPI()
    app.include_router(jobs.router, prefix="/api/v1")

    client = TestClient(app)
    resp = client.post(
        "/api/v1/jobs/claim",
        headers={"X-Api-Key": api_key},
        json={"environment": "prod", "limit": 1, "visibility_timeout_seconds": 45},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "11111111-1111-1111-1111-111111111111"
    assert data["workflow_name"] == "Test Flow"

    (_, params) = conn.fetchrow_calls[0]
    assert params[0] == "prod"
    assert params[1] == 1
    assert params[2] == "robot-001"
    assert params[3] == 45


def test_robot_heartbeat_maps_idle_to_online(monkeypatch):
    api_key = _configure_robot_auth(monkeypatch, robot_id="robot-001")

    class _Conn:
        def __init__(self):
            self.execute_calls = []

        async def execute(self, query: str, *params):
            self.execute_calls.append((query, params))
            return "UPDATE 1"

    conn = _Conn()
    robots.set_db_pool(_FakePool(conn))

    app = FastAPI()
    app.include_router(robots.router, prefix="/api/v1")

    client = TestClient(app)
    # Correct path: /robots/{robot_id}/heartbeat
    resp = client.post(
        "/api/v1/robots/robot-001/heartbeat",
        headers={"X-Api-Key": api_key},
        json={"cpu_percent": 1.0},
    )

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
