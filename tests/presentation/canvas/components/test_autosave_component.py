"""
Comprehensive tests for AutosaveComponent.

Tests autosave functionality including:
- Timer management
- Settings synchronization
- Autosave execution
- Crash recovery
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import QTimer

from casare_rpa.presentation.canvas.components.autosave_component import (
    AutosaveComponent,
)


@pytest.fixture
def mock_main_window() -> None:
    """Create a mock MainWindow."""
    mock = Mock()
    mock.preferences_saved = Mock()
    mock.preferences_saved.connect = Mock()
    mock.workflow_save = Mock()
    mock.workflow_save.emit = Mock()
    mock.get_current_file = Mock(return_value=None)
    return mock


@pytest.fixture
def autosave_component(mock_main_window) -> None:
    """Create an AutosaveComponent instance."""
    component = AutosaveComponent(mock_main_window)
    component.initialize()
    return component


class TestAutosaveComponentInitialization:
    """Tests for component initialization."""

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_initialization(self, mock_settings, mock_main_window) -> None:
        """Test component initializes."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = False
        mock_settings.return_value = mock_settings_instance

        component = AutosaveComponent(mock_main_window)
        component.initialize()

        assert component.is_initialized()
        assert component._autosave_timer is not None

    def test_cleanup(self, autosave_component) -> None:
        """Test cleanup stops timer."""
        mock_timer = Mock()
        autosave_component._autosave_timer = mock_timer

        autosave_component.cleanup()

        mock_timer.stop.assert_called_once()
        assert autosave_component._autosave_timer is None


class TestTimerManagement:
    """Tests for autosave timer management."""

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_update_timer_autosave_enabled(
        self, mock_settings, autosave_component
    ) -> None:
        """Test updating timer when autosave enabled."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = True
        mock_settings_instance.get_autosave_interval.return_value = 5
        mock_settings.return_value = mock_settings_instance

        mock_timer = Mock()
        autosave_component._autosave_timer = mock_timer

        autosave_component._update_timer_from_settings()

        # Should start timer with 5 minutes = 300000 ms
        mock_timer.start.assert_called_with(300000)

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_update_timer_autosave_disabled(
        self, mock_settings, autosave_component
    ) -> None:
        """Test updating timer when autosave disabled."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = False
        mock_settings.return_value = mock_settings_instance

        mock_timer = Mock()
        autosave_component._autosave_timer = mock_timer

        autosave_component._update_timer_from_settings()

        mock_timer.stop.assert_called_once()

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_update_settings(self, mock_settings, autosave_component) -> None:
        """Test updating settings."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = True
        mock_settings_instance.get_autosave_interval.return_value = 10
        mock_settings.return_value = mock_settings_instance

        mock_timer = Mock()
        autosave_component._autosave_timer = mock_timer

        autosave_component.update_settings()

        mock_timer.stop.assert_called_once()
        mock_timer.start.assert_called_once()


class TestAutosaveExecution:
    """Tests for autosave execution."""

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_on_autosave_disabled(self, mock_settings, autosave_component) -> None:
        """Test autosave when disabled."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = False
        mock_settings.return_value = mock_settings_instance

        mock_timer = Mock()
        autosave_component._autosave_timer = mock_timer

        autosave_component._on_autosave()

        mock_timer.stop.assert_called_once()

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_on_autosave_no_file(
        self, mock_settings, autosave_component, mock_main_window
    ) -> None:
        """Test autosave when no file open."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = True
        mock_settings.return_value = mock_settings_instance

        mock_main_window.get_current_file.return_value = None

        autosave_component._on_autosave()

        # Should not emit save signal
        mock_main_window.workflow_save.emit.assert_not_called()

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_on_autosave_success(
        self, mock_settings, autosave_component, mock_main_window
    ) -> None:
        """Test successful autosave."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = True
        mock_settings.return_value = mock_settings_instance

        mock_main_window.get_current_file.return_value = "/path/to/file.json"

        autosave_component._on_autosave()

        mock_main_window.workflow_save.emit.assert_called_once()

    @patch("casare_rpa.canvas.components.autosave_component.get_settings_manager")
    def test_on_autosave_error(
        self, mock_settings, autosave_component, mock_main_window
    ) -> None:
        """Test autosave with error."""
        mock_settings_instance = Mock()
        mock_settings_instance.is_autosave_enabled.return_value = True
        mock_settings.return_value = mock_settings_instance

        mock_main_window.get_current_file.side_effect = Exception("Error")

        # Should not raise error, just log it
        autosave_component._on_autosave()
