import aiohttp
import pytest

from casare_rpa.infrastructure.orchestrator.client import (
    OrchestratorClient,
    OrchestratorConfig,
)


class _RaisingHealthContext:
    async def __aenter__(self):
        raise aiohttp.ClientError("boom")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, *args, **kwargs):
        self.closed = False
        self.close_called = False

    def get(self, *args, **kwargs):
        return _RaisingHealthContext()

    async def close(self):
        self.close_called = True
        self.closed = True


@pytest.mark.asyncio
async def test_connect_closes_session_on_client_error(monkeypatch):
    fake_session = _FakeSession()

    def _fake_client_session(*args, **kwargs):
        return fake_session

    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session)

    client = OrchestratorClient(
        OrchestratorConfig(base_url="http://invalid", ws_url="ws://invalid")
    )
    ok = await client.connect()

    assert ok is False
    assert client._session is None
    assert fake_session.close_called is True
