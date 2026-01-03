import pytest

from casare_rpa.application.services.browser_recording_service import (
    BrowserRecordingService,
)


class _DummyRecorder:
    def __init__(self) -> None:
        self._is_recording = False
        self.callbacks = {}

    def set_callbacks(
        self,
        *,
        on_action_recorded=None,
        on_recording_started=None,
        on_recording_stopped=None,
    ) -> None:
        self.callbacks = {
            "on_action_recorded": on_action_recorded,
            "on_recording_started": on_recording_started,
            "on_recording_stopped": on_recording_stopped,
        }

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    async def start_recording(self) -> None:
        self._is_recording = True

    async def stop_recording(self) -> list[object]:
        self._is_recording = False
        return [{"action": "x"}]


class _DummyGenerator:
    @staticmethod
    def generate_workflow_data(actions, workflow_name=None):
        return {"workflow_name": workflow_name, "actions": actions}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_browser_recording_service_uses_injected_deps() -> None:
    recorder = _DummyRecorder()

    def recorder_factory(_page):
        return recorder

    service = BrowserRecordingService(
        recorder_factory=recorder_factory,
        workflow_generator=_DummyGenerator,
    )

    created = service.create_recorder(page=object())
    assert created is recorder

    service.set_recorder_callbacks(
        recorder,
        on_action_recorded=lambda _a: None,
        on_recording_started=lambda: None,
        on_recording_stopped=lambda: None,
    )
    assert "on_action_recorded" in recorder.callbacks

    assert service.is_recording(recorder) is False
    await service.start_recording(recorder)
    assert service.is_recording(recorder) is True

    actions = await service.stop_recording(recorder)
    assert service.is_recording(recorder) is False
    assert actions == [{"action": "x"}]

    workflow = service.generate_workflow_from_actions(actions, workflow_name="W")
    assert workflow["workflow_name"] == "W"
    assert workflow["actions"] == actions
