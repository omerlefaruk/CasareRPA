import aiohttp
import pytest

from casare_rpa.infrastructure.orchestrator.robot_job_consumer import (
    OrchestratorJobConsumer,
    OrchestratorJobConsumerConfig,
)


class _FakeResponse:
    def __init__(self, status: int, json_data, text_data: str = "") -> None:
        self.status = status
        self._json_data = json_data
        self._text_data = text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._json_data

    async def text(self) -> str:
        return self._text_data


class _FakeSession:
    def __init__(self, *args, **kwargs) -> None:
        self.closed = False
        self.close_called = False
        self.headers = kwargs.get("headers") or {}
        self._post_calls = []
        self._responses = {}

    def set_response(self, url: str, response: _FakeResponse) -> None:
        self._responses[url] = response

    @property
    def post_calls(self):
        return list(self._post_calls)

    def post(self, url: str, json=None):
        self._post_calls.append((url, json))
        return self._responses[url]

    async def close(self):
        self.close_called = True
        self.closed = True


@pytest.mark.asyncio
async def test_claim_job_uses_x_api_key_and_parses_payload(monkeypatch):
    fake_session = _FakeSession()

    def _fake_client_session(*args, **kwargs):
        fake_session.headers = kwargs.get("headers") or {}
        return fake_session

    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session)

    config = OrchestratorJobConsumerConfig(
        base_url="https://orch.example",
        api_key="crpa_test_key",
        environment="prod",
        visibility_timeout_seconds=45,
    )
    consumer = OrchestratorJobConsumer(config)

    claim_url = "https://orch.example/api/v1/jobs/claim"
    fake_session.set_response(
        claim_url,
        _FakeResponse(
            200,
            {
                "job_id": "11111111-1111-1111-1111-111111111111",
                "workflow_id": "wf-1",
                "workflow_name": "Test Flow",
                "workflow_json": "{}",
                "priority": 5,
                "environment": "prod",
                "variables": {"x": 1},
                "created_at": "2025-01-01T00:00:00+00:00",
                "claimed_at": "2025-01-01T00:00:01+00:00",
                "retry_count": 0,
                "max_retries": 3,
            },
        ),
    )

    job = await consumer.claim_job()

    assert fake_session.headers["X-Api-Key"] == "crpa_test_key"
    assert job is not None
    assert job.job_id == "11111111-1111-1111-1111-111111111111"
    assert job.workflow_name == "Test Flow"

    (url, payload) = fake_session.post_calls[0]
    assert url == claim_url
    assert payload == {
        "environment": "prod",
        "limit": 1,
        "visibility_timeout_seconds": 45,
    }

    await consumer.stop()
    assert fake_session.close_called is True


@pytest.mark.asyncio
async def test_extend_lease_posts_correct_payload(monkeypatch):
    fake_session = _FakeSession()

    def _fake_client_session(*args, **kwargs):
        fake_session.headers = kwargs.get("headers") or {}
        return fake_session

    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session)

    config = OrchestratorJobConsumerConfig(
        base_url="https://orch.example",
        api_key="crpa_test_key",
    )
    consumer = OrchestratorJobConsumer(config)

    job_id = "11111111-1111-1111-1111-111111111111"
    url = f"https://orch.example/api/v1/jobs/{job_id}/extend-lease"
    fake_session.set_response(url, _FakeResponse(200, {"extended": True}))

    ok = await consumer.extend_lease(job_id, extension_seconds=60)

    assert ok is True
    (called_url, payload) = fake_session.post_calls[0]
    assert called_url == url
    assert payload == {"extension_seconds": 60}

    await consumer.stop()
