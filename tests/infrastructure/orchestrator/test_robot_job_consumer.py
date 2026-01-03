import pytest

import casare_rpa.infrastructure.orchestrator.robot_job_consumer as job_consumer_module
from casare_rpa.infrastructure.orchestrator.robot_job_consumer import (
    OrchestratorJobConsumer,
    OrchestratorJobConsumerConfig,
)


class _FakeResponse:
    def __init__(self, status: int, json_data, text_data: str = "") -> None:
        self.status = status
        self._json_data = json_data
        self._text_data = text_data

    async def json(self):
        return self._json_data

    async def text(self) -> str:
        return self._text_data

    def release(self):
        return None


class _FakeHttpClient:
    def __init__(self, config) -> None:
        self.config = config
        self.started = False
        self.closed = False
        self._post_calls: list[tuple[str, object]] = []
        self._responses: dict[str, _FakeResponse] = {}

    async def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True

    def set_response(self, url: str, response: _FakeResponse) -> None:
        self._responses[url] = response

    @property
    def post_calls(self):
        return list(self._post_calls)

    async def post(self, url: str, json=None):
        self._post_calls.append((url, json))
        return self._responses[url]


@pytest.mark.asyncio
async def test_claim_job_uses_x_api_key_and_parses_payload(monkeypatch):
    monkeypatch.setattr(job_consumer_module, "UnifiedHttpClient", _FakeHttpClient)

    config = OrchestratorJobConsumerConfig(
        base_url="https://orch.example",
        api_key="crpa_test_key",
        environment="prod",
        visibility_timeout_seconds=45,
    )
    consumer = OrchestratorJobConsumer(config)
    await consumer.start()

    fake_client = consumer._client
    assert fake_client is not None
    assert fake_client.config.default_headers["X-Api-Key"] == "crpa_test_key"

    claim_url = "https://orch.example/api/v1/jobs/claim"
    fake_client.set_response(
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

    assert job is not None
    assert job.job_id == "11111111-1111-1111-1111-111111111111"
    assert job.workflow_name == "Test Flow"

    (url, payload) = fake_client.post_calls[0]
    assert url == claim_url
    assert payload == {
        "environment": "prod",
        "limit": 1,
        "visibility_timeout_seconds": 45,
    }

    await consumer.stop()
    assert fake_client.closed is True


@pytest.mark.asyncio
async def test_extend_lease_posts_correct_payload(monkeypatch):
    monkeypatch.setattr(job_consumer_module, "UnifiedHttpClient", _FakeHttpClient)

    config = OrchestratorJobConsumerConfig(
        base_url="https://orch.example",
        api_key="crpa_test_key",
    )
    consumer = OrchestratorJobConsumer(config)
    await consumer.start()

    fake_client = consumer._client
    assert fake_client is not None

    job_id = "11111111-1111-1111-1111-111111111111"
    url = f"https://orch.example/api/v1/jobs/{job_id}/extend-lease"
    fake_client.set_response(url, _FakeResponse(200, {"extended": True}))

    ok = await consumer.extend_lease(job_id, extension_seconds=60)

    assert ok is True
    (called_url, payload) = fake_client.post_calls[0]
    assert called_url == url
    assert payload == {"extension_seconds": 60}

    await consumer.stop()
    assert fake_client.closed is True
