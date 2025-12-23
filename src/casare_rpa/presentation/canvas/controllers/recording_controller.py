"""
Recording Controller for CasareRPA.

Manages desktop and browser recording, coordinating between recorder backends
and UI components. Generates workflow nodes from recorded actions.
"""

from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QObject, Signal

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.infrastructure.browser.browser_recorder import (
        BrowserRecordedAction,
        BrowserRecorder,
    )
    from casare_rpa.presentation.canvas.main_window import MainWindow


class RecordingController(BaseController):
    """
    Controller for managing recording operations.

    Coordinates between:
    - DesktopRecorder: Captures mouse/keyboard actions on desktop
    - BrowserRecorder: Captures browser interactions via Playwright
    - RecordingToolbar: UI controls for starting/stopping recording
    - RecordedActionsPanel: Displays and edits recorded actions

    Signals:
        recording_started: Emitted when recording begins (str: recording_type)
        recording_stopped: Emitted when recording ends (list: recorded actions)
        recording_paused: Emitted when recording is paused
        recording_resumed: Emitted when recording resumes
        action_recorded: Emitted when a single action is recorded (dict: action_data)
        workflow_generated: Emitted when workflow is generated (list: node_configs)
    """

    recording_started = Signal(str)  # recording_type: 'desktop' or 'browser'
    recording_stopped = Signal(list)  # List of recorded actions
    recording_paused = Signal()
    recording_resumed = Signal()
    action_recorded = Signal(dict)  # Single action data
    workflow_generated = Signal(list)  # List of node configurations

    def __init__(self, main_window: "MainWindow", parent: QObject | None = None) -> None:
        """
        Initialize the recording controller.

        Args:
            main_window: Reference to main window
            parent: Optional parent QObject
        """
        super().__init__(main_window, parent)

        self._is_recording = False
        self._is_paused = False
        self._recording_type: str | None = None

        self._browser_recorder: BrowserRecorder | None = None
        self._desktop_recorder = None

        self._recorded_actions: list[Any] = []

    def initialize(self) -> None:
        """Initialize controller resources and connections."""
        super().initialize()
        logger.debug("RecordingController initialized")

    def cleanup(self) -> None:
        """Clean up controller resources."""
        if self._is_recording:
            self._stop_recording_internal()
        super().cleanup()

    def set_browser_recorder(self, recorder: "BrowserRecorder") -> None:
        """
        Set the browser recorder instance.

        Args:
            recorder: BrowserRecorder instance to use
        """
        self._browser_recorder = recorder
        recorder.set_callbacks(
            on_action_recorded=self._on_browser_action_recorded,
            on_recording_started=self._on_browser_recording_started,
            on_recording_stopped=self._on_browser_recording_stopped,
        )
        logger.debug("Browser recorder connected to controller")

    def set_desktop_recorder(self, recorder: Any) -> None:
        """
        Set the desktop recorder instance.

        Args:
            recorder: DesktopRecorder instance to use
        """
        self._desktop_recorder = recorder
        logger.debug("Desktop recorder connected to controller")

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._is_recording

    @property
    def is_paused(self) -> bool:
        """Check if recording is paused."""
        return self._is_paused

    @property
    def recording_type(self) -> str | None:
        """Get the current recording type."""
        return self._recording_type

    @property
    def action_count(self) -> int:
        """Get the number of recorded actions."""
        return len(self._recorded_actions)

    async def start_desktop_recording(self) -> bool:
        """
        Start recording desktop actions.

        Returns:
            True if recording started successfully
        """
        if self._is_recording:
            logger.warning("Recording already in progress")
            return False

        if self._desktop_recorder is None:
            logger.error("Desktop recorder not available")
            return False

        try:
            self._recorded_actions.clear()
            self._recording_type = "desktop"
            self._is_recording = True
            self._is_paused = False

            await self._desktop_recorder.start_recording()
            self.recording_started.emit("desktop")
            logger.info("Desktop recording started")
            return True
        except Exception as e:
            logger.error(f"Failed to start desktop recording: {e}")
            self._is_recording = False
            self._recording_type = None
            return False

    async def start_browser_recording(self) -> bool:
        """
        Start recording browser actions.

        Returns:
            True if recording started successfully
        """
        if self._is_recording:
            logger.warning("Recording already in progress")
            return False

        if self._browser_recorder is None:
            logger.error("Browser recorder not available")
            return False

        try:
            self._recorded_actions.clear()
            self._recording_type = "browser"
            self._is_recording = True
            self._is_paused = False

            await self._browser_recorder.start_recording()
            self.recording_started.emit("browser")
            logger.info("Browser recording started")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser recording: {e}")
            self._is_recording = False
            self._recording_type = None
            return False

    async def stop_recording(self) -> list[Any]:
        """
        Stop the current recording.

        Returns:
            List of recorded actions
        """
        if not self._is_recording:
            logger.warning("No recording in progress")
            return []

        return await self._stop_recording_internal()

    async def _stop_recording_internal(self) -> list[Any]:
        """Internal method to stop recording."""
        try:
            if self._recording_type == "browser" and self._browser_recorder:
                await self._browser_recorder.stop_recording()
            elif self._recording_type == "desktop" and self._desktop_recorder:
                await self._desktop_recorder.stop_recording()

            actions = self._recorded_actions.copy()
            self.recording_stopped.emit(actions)
            logger.info(f"Recording stopped with {len(actions)} actions")
            return actions
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return []
        finally:
            self._is_recording = False
            self._is_paused = False
            self._recording_type = None

    def pause_recording(self) -> None:
        """Pause the current recording."""
        if not self._is_recording or self._is_paused:
            return

        self._is_paused = True

        if self._recording_type == "browser" and self._browser_recorder:
            self._browser_recorder.pause()
        elif self._recording_type == "desktop" and self._desktop_recorder:
            if hasattr(self._desktop_recorder, "pause"):
                self._desktop_recorder.pause()

        self.recording_paused.emit()
        logger.debug("Recording paused")

    def resume_recording(self) -> None:
        """Resume the paused recording."""
        if not self._is_recording or not self._is_paused:
            return

        self._is_paused = False

        if self._recording_type == "browser" and self._browser_recorder:
            self._browser_recorder.resume()
        elif self._recording_type == "desktop" and self._desktop_recorder:
            if hasattr(self._desktop_recorder, "resume"):
                self._desktop_recorder.resume()

        self.recording_resumed.emit()
        logger.debug("Recording resumed")

    def _on_browser_action_recorded(self, action: "BrowserRecordedAction") -> None:
        """Handle recorded browser action."""
        self._recorded_actions.append(action)
        action_data = {
            "type": "browser",
            "action_type": action.action_type.value,
            "selector": action.selector,
            "value": action.value,
            "url": action.url,
            "timestamp": action.timestamp,
        }
        self.action_recorded.emit(action_data)

    def _on_browser_recording_started(self) -> None:
        """Handle browser recording started callback."""
        logger.debug("Browser recording started callback received")

    def _on_browser_recording_stopped(self) -> None:
        """Handle browser recording stopped callback."""
        logger.debug("Browser recording stopped callback received")

    def get_recorded_actions(self) -> list[Any]:
        """
        Get all recorded actions.

        Returns:
            List of recorded actions
        """
        return self._recorded_actions.copy()

    def clear_recorded_actions(self) -> None:
        """Clear all recorded actions."""
        self._recorded_actions.clear()
        if self._browser_recorder:
            self._browser_recorder.clear()
        logger.debug("Recorded actions cleared")

    def generate_workflow_nodes(self) -> list[dict[str, Any]]:
        """
        Generate workflow node configurations from recorded actions.

        Returns:
            List of node configuration dictionaries
        """
        if not self._recorded_actions:
            return []

        node_configs = []

        if self._recording_type == "browser" and self._browser_recorder:
            node_configs = self._browser_recorder.to_workflow_nodes()
        elif self._recording_type == "desktop" and self._desktop_recorder:
            if hasattr(self._desktop_recorder, "to_workflow_nodes"):
                node_configs = self._desktop_recorder.to_workflow_nodes()
            else:
                node_configs = self._generate_desktop_nodes()

        if node_configs:
            self.workflow_generated.emit(node_configs)
            logger.info(f"Generated {len(node_configs)} workflow nodes")

        return node_configs

    def _generate_desktop_nodes(self) -> list[dict[str, Any]]:
        """
        Generate desktop workflow nodes from recorded actions.

        Returns:
            List of node configurations
        """
        node_configs = []

        for idx, action in enumerate(self._recorded_actions):
            action_type = getattr(action, "action_type", None)
            if action_type is None:
                continue

            config: dict[str, Any] = {
                "node_id": f"recorded_{idx}",
                "node_type": "",
                "name": f"Recorded Action {idx + 1}",
                "config": {},
            }

            type_str = str(action_type).lower()
            if "click" in type_str:
                config["node_type"] = "ClickNode"
                config["config"]["x"] = getattr(action, "x", 0)
                config["config"]["y"] = getattr(action, "y", 0)
            elif "type" in type_str or "key" in type_str:
                config["node_type"] = "TypeTextNode"
                config["config"]["text"] = getattr(action, "text", "")
            elif "scroll" in type_str:
                config["node_type"] = "ScrollNode"
                config["config"]["direction"] = getattr(action, "direction", "down")
            else:
                config["node_type"] = "GenericActionNode"
                config["config"]["action_data"] = str(action)

            node_configs.append(config)

        return node_configs

    def delete_action(self, index: int) -> bool:
        """
        Delete a recorded action by index.

        Args:
            index: Index of action to delete

        Returns:
            True if action was deleted
        """
        if 0 <= index < len(self._recorded_actions):
            del self._recorded_actions[index]
            logger.debug(f"Deleted action at index {index}")
            return True
        return False

    def reorder_action(self, from_index: int, to_index: int) -> bool:
        """
        Reorder a recorded action.

        Args:
            from_index: Current index of action
            to_index: Target index for action

        Returns:
            True if action was reordered
        """
        if 0 <= from_index < len(self._recorded_actions) and 0 <= to_index < len(
            self._recorded_actions
        ):
            action = self._recorded_actions.pop(from_index)
            self._recorded_actions.insert(to_index, action)
            logger.debug(f"Reordered action from {from_index} to {to_index}")
            return True
        return False

    def get_recording_state(self) -> dict[str, Any]:
        """
        Get comprehensive recording state.

        Returns:
            Dictionary with all recording state information
        """
        return {
            "is_recording": self._is_recording,
            "is_paused": self._is_paused,
            "recording_type": self._recording_type,
            "action_count": len(self._recorded_actions),
            "has_browser_recorder": self._browser_recorder is not None,
            "has_desktop_recorder": self._desktop_recorder is not None,
        }
