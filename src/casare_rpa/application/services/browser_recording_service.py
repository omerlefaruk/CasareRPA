"""
Browser Recording Service - Application layer abstraction for browser recording.

This service wraps browser recording functionality behind domain interfaces,
allowing the Presentation layer to use recording without importing from
infrastructure directly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

from casare_rpa.domain.interfaces import (
    IBrowserRecorder,
    IBrowserRecorderFactory,
    IBrowserWorkflowGenerator,
)

if TYPE_CHECKING:
    from playwright.async_api import Page


def _resolve_recorder_factory(
    factory: IBrowserRecorderFactory | None,
) -> IBrowserRecorderFactory:
    if factory is not None:
        return factory

    from casare_rpa.application.dependency_injection.container import DIContainer

    return cast(
        IBrowserRecorderFactory,
        DIContainer.get_instance().resolve("browser_recorder_factory"),
    )


def _resolve_workflow_generator(
    generator: IBrowserWorkflowGenerator | None,
) -> IBrowserWorkflowGenerator:
    if generator is not None:
        return generator

    from casare_rpa.application.dependency_injection.container import DIContainer

    return cast(
        IBrowserWorkflowGenerator,
        DIContainer.get_instance().resolve("browser_workflow_generator"),
    )


class BrowserRecordingService:
    """
    Application service for browser recording operations.

    Presentation layer should use this service instead of importing directly
    from infrastructure.
    """

    def __init__(
        self,
        recorder_factory: IBrowserRecorderFactory | None = None,
        workflow_generator: IBrowserWorkflowGenerator | None = None,
    ) -> None:
        self._recorder_factory = _resolve_recorder_factory(recorder_factory)
        self._workflow_generator = _resolve_workflow_generator(workflow_generator)
        logger.debug("BrowserRecordingService initialized")

    def create_recorder(self, page: Page) -> IBrowserRecorder:
        """Create a recorder instance bound to the given Playwright page."""
        return self._recorder_factory(page)

    def set_recorder_callbacks(
        self,
        recorder: IBrowserRecorder,
        on_action_recorded: Callable[[Any], None] | None = None,
        on_recording_started: Callable[[], None] | None = None,
        on_recording_stopped: Callable[[], None] | None = None,
    ) -> None:
        """Set callback functions on a recorder instance."""
        recorder.set_callbacks(
            on_action_recorded=on_action_recorded,
            on_recording_started=on_recording_started,
            on_recording_stopped=on_recording_stopped,
        )

    async def start_recording(self, recorder: IBrowserRecorder) -> None:
        """Start recording browser actions."""
        await recorder.start_recording()

    async def stop_recording(self, recorder: IBrowserRecorder) -> list[Any]:
        """Stop recording and return captured actions."""
        return await recorder.stop_recording()

    def is_recording(self, recorder: IBrowserRecorder) -> bool:
        """Check if a recorder is currently recording."""
        return recorder.is_recording

    def generate_workflow_from_actions(
        self,
        actions: list[Any],
        workflow_name: str | None = None,
    ) -> dict[str, Any]:
        """Generate workflow JSON from recorded actions."""
        return self._workflow_generator.generate_workflow_data(actions, workflow_name)


_browser_recording_service: BrowserRecordingService | None = None


def get_browser_recording_service() -> BrowserRecordingService:
    """Get the singleton browser recording service."""
    global _browser_recording_service
    if _browser_recording_service is None:
        _browser_recording_service = BrowserRecordingService()
    return _browser_recording_service


__all__ = [
    "BrowserRecordingService",
    "get_browser_recording_service",
]
