import pytest

from casare_rpa.application.use_cases.generate_workflow import GenerateWorkflowUseCase


class _DummyLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _DummyLLMManager:
    def __init__(self, *, content: str) -> None:
        self._content = content
        self.calls: list[dict[str, object]] = []

    async def completion(self, **kwargs):
        self.calls.append(dict(kwargs))
        return _DummyLLMResponse(self._content)


class _DummyManifestProvider:
    def __init__(self, markdown: str = "MANIFEST") -> None:
        self.markdown = markdown

    def get_compact_markdown(self) -> str:
        return self.markdown


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workflow_use_case_uses_injected_ports() -> None:
    llm = _DummyLLMManager(
        content='{"metadata":{"name":"Test"},"nodes":{},"connections":[]}',
    )
    manifest_provider = _DummyManifestProvider(markdown="NODES...")

    use_case = GenerateWorkflowUseCase(
        llm_manager=llm,
        node_manifest_provider=manifest_provider,
    )

    workflow = await use_case.execute(query="Hello")

    assert "start_node" in workflow.nodes
    assert "end_node" in workflow.nodes
    assert llm.calls
    assert "system_prompt" in llm.calls[0]
    assert "NODES..." in str(llm.calls[0]["system_prompt"])
