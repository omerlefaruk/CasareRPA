import asyncio

import pytest

from casare_rpa.infrastructure.orchestrator.client import (
    OrchestratorClient,
    OrchestratorConfig,
)


class _FakeResponse:
    def __init__(self, status: int, body: str = "error", headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return self._body

    async def json(self):
        return {}


class _FakeSession:
    def __init__(self, statuses: list[int]):
        self._statuses = list(statuses)
        self.calls: list[int] = []

    def request(self, method, url, params=None, json=None):
        status = self._statuses.pop(0) if self._statuses else 500
        self.calls.append(status)
        return _FakeResponse(status=status)


@pytest.mark.asyncio
async def test_request_does_not_retry_on_500(monkeypatch):
    async def _no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    client = OrchestratorClient(
        OrchestratorConfig(
            base_url="http://example", ws_url="ws://example", retry_attempts=3
        )
    )
    client._session = _FakeSession([500, 500, 500])

    resp = await client._request("GET", "/api/v1/robot-api-keys")

    assert resp is None
    assert client._session.calls == [500]


@pytest.mark.asyncio
async def test_request_retries_on_503(monkeypatch):
    async def _no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    client = OrchestratorClient(
        OrchestratorConfig(
            base_url="http://example", ws_url="ws://example", retry_attempts=3
        )
    )
    client._session = _FakeSession([503, 503, 503])

    resp = await client._request("GET", "/api/v1/health")

    assert resp is None
    assert client._session.calls == [503, 503, 503]
