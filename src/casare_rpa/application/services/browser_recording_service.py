"""
Browser Recording Service - Application layer abstraction for browser recording.

This service wraps infrastructure browser recording functionality,
allowing Presentation layer to use it without violating DDD boundaries.
Presentation -> Application -> Infrastructure (correct flow).
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page


class BrowserRecordingService:
    """
    Application service for browser recording operations.

    Abstracts infrastructure-level BrowserRecorder and BrowserWorkflowGenerator
    to maintain Clean Architecture boundaries. Presentation layer should use
    this service instead of importing directly from infrastructure.

    Example:
        service = get_browser_recording_service()
        recorder = await service.create_recorder(page)
        await service.start_recording(recorder)
        actions = await service.stop_recording(recorder)
        workflow = service.generate_workflow_from_actions(actions)
    """

    def __init__(self) -> None:
        """Initialize the browser recording service."""
        self._recorder_class = None
        self._generator_class = None
        logger.debug("BrowserRecordingService initialized")

    def _ensure_recorder_class(self):
        """Lazy load recorder class from infrastructure."""
        if self._recorder_class is None:
            from casare_rpa.infrastructure.browser import BrowserRecorder

            self._recorder_class = BrowserRecorder
        return self._recorder_class

    def _ensure_generator_class(self):
        """Lazy load generator class from infrastructure."""
        if self._generator_class is None:
            from casare_rpa.infrastructure.browser import BrowserWorkflowGenerator

            self._generator_class = BrowserWorkflowGenerator
        return self._generator_class

    def create_recorder(self, page: "Page") -> Any:
        """
        Create a new browser recorder instance for the given page.

        Args:
            page: Playwright Page instance to record from.

        Returns:
            BrowserRecorder instance (typed as Any to avoid infrastructure import).
        """
        recorder_class = self._ensure_recorder_class()
        return recorder_class(page)

    def set_recorder_callbacks(
        self,
        recorder: Any,
        on_action_recorded: Callable | None = None,
        on_recording_started: Callable | None = None,
        on_recording_stopped: Callable | None = None,
    ) -> None:
        """
        Set callback functions on a recorder instance.

        Args:
            recorder: BrowserRecorder instance.
            on_action_recorded: Called when each action is recorded.
            on_recording_started: Called when recording starts.
            on_recording_stopped: Called when recording stops.
        """
        if hasattr(recorder, "set_callbacks"):
            recorder.set_callbacks(
                on_action_recorded=on_action_recorded,
                on_recording_started=on_recording_started,
                on_recording_stopped=on_recording_stopped,
            )

    async def start_recording(self, recorder: Any) -> None:
        """
        Start recording browser actions.

        Args:
            recorder: BrowserRecorder instance to start.

        Raises:
            RuntimeError: If recording is already in progress.
        """
        await recorder.start_recording()

    async def stop_recording(self, recorder: Any) -> list[Any]:
        """
        Stop recording and return captured actions.

        Args:
            recorder: BrowserRecorder instance to stop.

        Returns:
            List of BrowserRecordedAction instances.
        """
        return await recorder.stop_recording()

    def is_recording(self, recorder: Any) -> bool:
        """
        Check if a recorder is currently recording.

        Args:
            recorder: BrowserRecorder instance to check.

        Returns:
            True if recording is in progress.
        """
        return getattr(recorder, "is_recording", False)

    def generate_workflow_from_actions(
        self,
        actions: list[Any],
        workflow_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate workflow JSON from recorded actions.

        Args:
            actions: List of BrowserRecordedAction instances.
            workflow_name: Optional name for the generated workflow.

        Returns:
            Workflow data dictionary with nodes and connections.
        """
        generator_class = self._ensure_generator_class()
        return generator_class.generate_workflow_data(actions, workflow_name)


# Singleton instance
_browser_recording_service: BrowserRecordingService | None = None


def get_browser_recording_service() -> BrowserRecordingService:
    """
    Get the singleton browser recording service.

    Returns:
        BrowserRecordingService singleton instance.
    """
    global _browser_recording_service
    if _browser_recording_service is None:
        _browser_recording_service = BrowserRecordingService()
    return _browser_recording_service


__all__ = [
    "BrowserRecordingService",
    "get_browser_recording_service",
]
