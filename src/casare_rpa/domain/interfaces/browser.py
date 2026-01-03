"""Domain-level browser recording interfaces.

These Protocols allow the application layer to depend on abstractions rather
than importing infrastructure browser implementations directly.
"""

from collections.abc import Callable
from typing import Any, Protocol


class IBrowserRecorder(Protocol):
    """Protocol for a browser action recorder."""

    def set_callbacks(
        self,
        *,
        on_action_recorded: Callable[[Any], None] | None = None,
        on_recording_started: Callable[[], None] | None = None,
        on_recording_stopped: Callable[[], None] | None = None,
    ) -> None:
        """Set callbacks for recording events."""

    @property
    def is_recording(self) -> bool:
        """Whether recording is currently active."""

    async def start_recording(self) -> None:
        """Start recording."""

    async def stop_recording(self) -> list[Any]:
        """Stop recording and return recorded actions."""


class IBrowserRecorderFactory(Protocol):
    """Factory for creating a recorder bound to a browser page."""

    def __call__(self, page: Any) -> IBrowserRecorder:  # pragma: no cover
        """Create a recorder for the given page."""


class IBrowserWorkflowGenerator(Protocol):
    """Protocol for converting recorded actions into workflow JSON."""

    @staticmethod
    def generate_workflow_data(
        actions: list[Any],
        workflow_name: str | None = None,
    ) -> dict[str, Any]:
        """Generate workflow data from recorded actions."""
