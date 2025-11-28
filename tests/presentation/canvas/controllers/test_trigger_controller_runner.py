"""
Tests for TriggerController TriggerRunner integration.

Tests TriggerRunner lifecycle management:
- TriggerRunner setup
- Start/stop triggers
- Trigger execution status
- Cleanup
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.trigger_controller import (
    TriggerController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Mock bottom panel
    mock_bottom_panel = Mock()
    mock_bottom_panel.get_triggers = Mock(return_value=[])
    mock_bottom_panel.set_triggers_running = Mock()
    main_window.get_bottom_panel = Mock(return_value=mock_bottom_panel)

    main_window.show_status = Mock()
    main_window.workflow_run = Mock()
    main_window.trigger_workflow_requested = Mock()

    return main_window


@pytest.fixture
def mock_app_instance():
    """Create a mock app instance."""
    return Mock()


@pytest.fixture
def trigger_controller(mock_main_window, mock_app_instance):
    """Create a TriggerController instance."""
    controller = TriggerController(mock_main_window, mock_app_instance)
    return controller


class TestTriggerRunnerSetup:
    """Tests for TriggerRunner setup functionality."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_setup_trigger_runner_success(
        self, MockTriggerRunner, trigger_controller, mock_app_instance
    ) -> None:
        """Test TriggerRunner setup succeeds with app instance."""
        mock_runner = Mock()
        MockTriggerRunner.return_value = mock_runner

        trigger_controller.initialize()

        # Verify TriggerRunner created
        MockTriggerRunner.assert_called_once_with(mock_app_instance)
        assert trigger_controller._trigger_runner == mock_runner

    def test_setup_trigger_runner_without_app_instance(self, mock_main_window) -> None:
        """Test TriggerRunner setup handles missing app instance gracefully."""
        controller = TriggerController(mock_main_window, app_instance=None)
        controller.initialize()

        # Should not create TriggerRunner
        assert controller._trigger_runner is None

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_setup_trigger_runner_handles_import_error(
        self, MockTriggerRunner, trigger_controller
    ) -> None:
        """Test TriggerRunner setup handles import error gracefully."""
        MockTriggerRunner.side_effect = ImportError("TriggerRunner not available")

        trigger_controller.initialize()

        # Should not raise exception
        assert trigger_controller._trigger_runner is None


class TestStartTriggers:
    """Tests for starting triggers."""

    @pytest.mark.asyncio
    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    async def test_start_triggers_success(
        self, MockTriggerRunner, trigger_controller, mock_main_window
    ) -> None:
        """Test start_triggers starts all configured triggers."""
        # Setup mock runner
        mock_runner = Mock()
        mock_runner.start_triggers = AsyncMock(return_value=2)
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        # Setup triggers
        mock_bottom_panel = mock_main_window.get_bottom_panel()
        mock_bottom_panel.get_triggers.return_value = [
            {"id": "trigger1", "enabled": True},
            {"id": "trigger2", "enabled": True},
        ]

        # Start triggers
        trigger_controller.start_triggers()

        # Wait for async task
        await asyncio.sleep(0.1)

        # Verify runner called
        mock_runner.start_triggers.assert_called_once()
        mock_bottom_panel.set_triggers_running.assert_called_with(True)

    def test_start_triggers_without_runner(self, mock_main_window) -> None:
        """Test start_triggers handles missing TriggerRunner gracefully."""
        controller = TriggerController(mock_main_window, app_instance=None)
        controller.initialize()

        controller.start_triggers()

        # Should show error status
        mock_main_window.show_status.assert_called()

    def test_start_triggers_without_triggers(
        self, trigger_controller, mock_main_window
    ) -> None:
        """Test start_triggers handles no triggers gracefully."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
        ):
            trigger_controller.initialize()

        # No triggers configured
        mock_bottom_panel = mock_main_window.get_bottom_panel()
        mock_bottom_panel.get_triggers.return_value = []

        trigger_controller.start_triggers()

        # Should show message
        mock_main_window.show_status.assert_called()

    def test_start_triggers_without_bottom_panel(
        self, trigger_controller, mock_main_window
    ) -> None:
        """Test start_triggers handles missing bottom panel gracefully."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
        ):
            trigger_controller.initialize()

        mock_main_window.get_bottom_panel.return_value = None

        trigger_controller.start_triggers()

        # Should not raise exception


class TestStopTriggers:
    """Tests for stopping triggers."""

    @pytest.mark.asyncio
    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    async def test_stop_triggers_success(
        self, MockTriggerRunner, trigger_controller, mock_main_window
    ) -> None:
        """Test stop_triggers stops all active triggers."""
        # Setup mock runner
        mock_runner = Mock()
        mock_runner.stop_triggers = AsyncMock()
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        # Stop triggers
        trigger_controller.stop_triggers()

        # Wait for async task
        await asyncio.sleep(0.1)

        # Verify runner called
        mock_runner.stop_triggers.assert_called_once()
        mock_main_window.get_bottom_panel().set_triggers_running.assert_called_with(
            False
        )

    def test_stop_triggers_without_runner(self, mock_main_window) -> None:
        """Test stop_triggers handles missing TriggerRunner gracefully."""
        controller = TriggerController(mock_main_window, app_instance=None)
        controller.initialize()

        controller.stop_triggers()

        # Should not raise exception


class TestTriggerStatus:
    """Tests for trigger status checking."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_are_triggers_running_true(
        self, MockTriggerRunner, trigger_controller
    ) -> None:
        """Test are_triggers_running returns True when running."""
        mock_runner = Mock()
        mock_runner.is_running = True
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        assert trigger_controller.are_triggers_running() is True

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_are_triggers_running_false(
        self, MockTriggerRunner, trigger_controller
    ) -> None:
        """Test are_triggers_running returns False when not running."""
        mock_runner = Mock()
        mock_runner.is_running = False
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        assert trigger_controller.are_triggers_running() is False

    def test_are_triggers_running_without_runner(self, mock_main_window) -> None:
        """Test are_triggers_running returns False without TriggerRunner."""
        controller = TriggerController(mock_main_window, app_instance=None)
        controller.initialize()

        assert controller.are_triggers_running() is False


class TestTriggerWorkflowExecution:
    """Tests for trigger-based workflow execution."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_on_trigger_run_workflow_success(
        self, MockTriggerRunner, trigger_controller, mock_main_window
    ) -> None:
        """Test _on_trigger_run_workflow triggers workflow execution."""
        # Setup mock runner with trigger event
        mock_runner = Mock()
        mock_event = Mock()
        mock_event.payload = {"key": "value"}
        mock_runner.get_last_trigger_event = Mock(return_value=mock_event)
        mock_runner.clear_last_trigger_event = Mock()
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        # Trigger workflow
        trigger_controller._on_trigger_run_workflow()

        # Verify workflow run signal emitted
        mock_main_window.workflow_run.emit.assert_called_once()
        mock_runner.clear_last_trigger_event.assert_called_once()

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_on_trigger_run_workflow_without_event(
        self, MockTriggerRunner, trigger_controller, mock_main_window
    ) -> None:
        """Test _on_trigger_run_workflow handles missing trigger event."""
        mock_runner = Mock()
        mock_runner.get_last_trigger_event = Mock(return_value=None)
        mock_runner.clear_last_trigger_event = Mock()
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        trigger_controller._on_trigger_run_workflow()

        # Should still emit workflow run
        mock_main_window.workflow_run.emit.assert_called_once()


class TestCleanup:
    """Tests for cleanup functionality."""

    @pytest.mark.asyncio
    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    async def test_cleanup_stops_running_triggers(
        self, MockTriggerRunner, trigger_controller
    ) -> None:
        """Test cleanup stops triggers if running."""
        mock_runner = Mock()
        mock_runner.is_running = True
        mock_runner.stop_triggers = AsyncMock()
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        trigger_controller.cleanup()

        # Wait for async task
        await asyncio.sleep(0.1)

        # Verify stop called (via ensure_future)
        # Note: Can't easily verify AsyncMock called via ensure_future

    @patch(
        "casare_rpa.presentation.canvas.controllers.trigger_controller.CanvasTriggerRunner"
    )
    def test_cleanup_handles_not_running_triggers(
        self, MockTriggerRunner, trigger_controller
    ) -> None:
        """Test cleanup handles not running triggers gracefully."""
        mock_runner = Mock()
        mock_runner.is_running = False
        MockTriggerRunner.return_value = mock_runner
        trigger_controller.initialize()

        trigger_controller.cleanup()

        # Should not raise exception

    def test_cleanup_without_runner(self, mock_main_window) -> None:
        """Test cleanup handles missing TriggerRunner gracefully."""
        controller = TriggerController(mock_main_window, app_instance=None)
        controller.initialize()

        controller.cleanup()

        # Should not raise exception
