import pytest

from casare_rpa.infrastructure.orchestrator.client import (
    OrchestratorClient,
    OrchestratorConfig,
)


class _RaisingHttpClient:
    def __init__(self) -> None:
        self.started = False
        self.closed = False

    async def start(self) -> None:
        self.started = True

    async def get(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def close(self) -> None:
        self.closed = True
        self.started = False


@pytest.mark.asyncio
async def test_connect_closes_http_client_on_error():
    client = OrchestratorClient(
        OrchestratorConfig(base_url="http://invalid", ws_url="ws://invalid")
    )
    http_client = _RaisingHttpClient()
    client._http_client = http_client

    ok = await client.connect()

    assert ok is False
    assert client.is_connected is False
    assert http_client.closed is True
