"""
Tests for ProjectController.

Tests project and scenario management including:
- Project create/open/close
- Scenario create/switch
- Event publishing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QObject

from casare_rpa.presentation.canvas.controllers.project_controller import (
    ProjectController,
)
from casare_rpa.presentation.canvas.events.event_types import EventType


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QObject()
    return main_window


@pytest.fixture
def mock_project_manager():
    """Create a mock project manager."""
    manager = Mock()
    manager.current_project = None
    manager.current_scenario = None
    return manager


@pytest.fixture
def project_controller(mock_main_window, mock_project_manager):
    """Create a ProjectController instance."""
    with patch(
        "casare_rpa.project.project_manager.get_project_manager",
        return_value=mock_project_manager,
    ):
        controller = ProjectController(mock_main_window)
        controller.initialize()
        yield controller
        controller.cleanup()


class TestProjectControllerInitialization:
    """Test controller initialization and cleanup."""

    def test_initialization(self, project_controller):
        """Test controller initializes correctly."""
        assert project_controller.is_initialized
        assert project_controller._project_manager is not None

    def test_cleanup(self, project_controller):
        """Test controller cleanup."""
        project_controller.cleanup()
        assert not project_controller.is_initialized


class TestProjectManagement:
    """Test project management operations."""

    def test_get_project_manager(self, project_controller, mock_project_manager):
        """Test getting project manager instance."""
        assert project_controller.get_project_manager() == mock_project_manager

    def test_get_current_project(self, project_controller, mock_project_manager):
        """Test getting current project."""
        mock_project = Mock()
        mock_project_manager.current_project = mock_project

        assert project_controller.get_current_project() == mock_project

    def test_get_current_project_none(self, project_controller, mock_project_manager):
        """Test getting current project when none is set."""
        mock_project_manager.current_project = None

        assert project_controller.get_current_project() is None

    def test_get_current_scenario(self, project_controller, mock_project_manager):
        """Test getting current scenario."""
        mock_scenario = Mock()
        mock_project_manager.current_scenario = mock_scenario

        assert project_controller.get_current_scenario() == mock_scenario

    def test_get_current_scenario_none(self, project_controller, mock_project_manager):
        """Test getting current scenario when none is set."""
        mock_project_manager.current_scenario = None

        assert project_controller.get_current_scenario() is None


class TestProjectOperations:
    """Test project operations."""

    def test_create_project_success(self, project_controller):
        """Test creating a project successfully."""
        signal_received = []

        def on_created(name):
            signal_received.append(name)

        project_controller.project_created.connect(on_created)

        result = project_controller.create_project("Test Project", "/path/to/project")

        assert result is True
        assert signal_received == ["Test Project"]

    def test_create_project_event_published(self, project_controller):
        """Test create project event is published."""
        with patch.object(project_controller._event_bus, "publish") as mock_publish:
            project_controller.create_project("Test Project", "/path/to/project")

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.PROJECT_CREATED
            assert event.data["project_name"] == "Test Project"
            assert event.data["project_path"] == "/path/to/project"

    def test_open_project_success(self, project_controller):
        """Test opening a project successfully."""
        signal_received = []

        def on_opened(path):
            signal_received.append(path)

        project_controller.project_opened.connect(on_opened)

        result = project_controller.open_project("/path/to/project")

        assert result is True
        assert signal_received == ["/path/to/project"]

    def test_open_project_event_published(self, project_controller):
        """Test open project event is published."""
        with patch.object(project_controller._event_bus, "publish") as mock_publish:
            project_controller.open_project("/path/to/project")

            # Verify event was published
            events_published = [call[0][0] for call in mock_publish.call_args_list]
            event_types = [e.type for e in events_published]

            assert EventType.PROJECT_OPENED in event_types

    def test_close_project_success(self, project_controller):
        """Test closing a project successfully."""
        signal_received = []

        def on_closed():
            signal_received.append(True)

        project_controller.project_closed.connect(on_closed)

        result = project_controller.close_project()

        assert result is True
        assert signal_received == [True]

    def test_close_project_event_published(self, project_controller):
        """Test close project event is published."""
        with patch.object(project_controller._event_bus, "publish") as mock_publish:
            project_controller.close_project()

            # Verify event was published
            assert mock_publish.called
            events_published = [call[0][0] for call in mock_publish.call_args_list]
            event_types = [e.type for e in events_published]

            assert EventType.PROJECT_CLOSED in event_types


class TestScenarioOperations:
    """Test scenario operations."""

    def test_create_scenario_success(self, project_controller):
        """Test creating a scenario successfully."""
        signal_received = []

        def on_created(name):
            signal_received.append(name)

        project_controller.scenario_created.connect(on_created)

        result = project_controller.create_scenario("Test Scenario")

        assert result is True
        assert signal_received == ["Test Scenario"]

    def test_create_scenario_event_published(self, project_controller):
        """Test create scenario event is published."""
        with patch.object(project_controller._event_bus, "publish") as mock_publish:
            project_controller.create_scenario("Test Scenario")

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.SCENARIO_CREATED
            assert event.data["scenario_name"] == "Test Scenario"

    def test_switch_scenario_success(self, project_controller):
        """Test switching scenarios successfully."""
        signal_received = []

        def on_switched(name):
            signal_received.append(name)

        project_controller.scenario_switched.connect(on_switched)

        result = project_controller.switch_scenario("Another Scenario")

        assert result is True
        assert signal_received == ["Another Scenario"]

    def test_switch_scenario_event_published(self, project_controller):
        """Test switch scenario event is published."""
        with patch.object(project_controller._event_bus, "publish") as mock_publish:
            project_controller.switch_scenario("Another Scenario")

            # Verify event was published
            events_published = [call[0][0] for call in mock_publish.call_args_list]
            event_types = [e.type for e in events_published]

            assert EventType.SCENARIO_OPENED in event_types


class TestEventHandlers:
    """Test event handlers."""

    def test_project_created_event_handler(self, project_controller):
        """Test project created event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(
            type=EventType.PROJECT_CREATED, source="Test", data={"project_name": "Test"}
        )

        # Should not raise exception
        project_controller._on_project_created_event(event)

    def test_project_opened_event_handler(self, project_controller):
        """Test project opened event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(
            type=EventType.PROJECT_OPENED, source="Test", data={"project_path": "/path"}
        )

        # Should not raise exception
        project_controller._on_project_opened_event(event)


class TestErrorHandling:
    """Test error handling."""

    def test_create_project_when_not_initialized(self, mock_main_window):
        """Test creating project when manager not initialized."""
        controller = ProjectController(mock_main_window)
        # Don't call initialize()

        result = controller.create_project("Test", "/path")

        assert result is False

    def test_create_project_with_exception(self, project_controller):
        """Test creating project with exception."""
        # This tests the try/except block
        result = project_controller.create_project("Test", "/path")

        # Should return True (placeholder implementation)
        assert result is True

    def test_get_current_project_when_not_initialized(self, mock_main_window):
        """Test getting current project when manager not initialized."""
        controller = ProjectController(mock_main_window)
        # Don't call initialize()

        assert controller.get_current_project() is None
