import asyncio

import pytest

from casare_rpa.infrastructure.orchestrator.client import (
    OrchestratorClient,
    OrchestratorConfig,
)


class _FakeResponse:
    def __init__(self, status: int, body: str = "error") -> None:
        self.status = status
        self._body = body
        self.headers: dict[str, str] = {}

    async def text(self) -> str:
        return self._body

    async def json(self):
        return {}

    def release(self):
        return None


class _FakePool:
    def __init__(self, statuses: list[int]) -> None:
        self._statuses = list(statuses)
        self.calls: list[int] = []

    async def request(self, _method: str, _url: str, **_kwargs):
        status = self._statuses.pop(0) if self._statuses else 500
        self.calls.append(status)
        return _FakeResponse(status=status)

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_request_does_not_retry_on_500(monkeypatch):
    async def _no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    client = OrchestratorClient(
        OrchestratorConfig(base_url="http://example", ws_url="ws://example", retry_attempts=3)
    )
    fake_pool = _FakePool([500, 500, 500])
    client._http_client._pool = fake_pool
    client._http_client._started = True

    resp = await client._request("GET", "/api/v1/robot-api-keys")

    assert resp is None
    assert fake_pool.calls == [500]


@pytest.mark.asyncio
async def test_request_retries_on_503(monkeypatch):
    async def _no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    client = OrchestratorClient(
        OrchestratorConfig(base_url="http://example", ws_url="ws://example", retry_attempts=3)
    )
    fake_pool = _FakePool([503, 503, 503])
    client._http_client._pool = fake_pool
    client._http_client._started = True

    resp = await client._request("GET", "/api/v1/health")

    assert resp is None
    assert fake_pool.calls == [503, 503, 503]
