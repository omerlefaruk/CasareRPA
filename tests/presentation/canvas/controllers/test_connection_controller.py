"""
Comprehensive tests for ConnectionController.

Tests connection management including:
- Connection creation
- Connection deletion
- Connection validation
- Auto-connect mode
- Port compatibility
"""

import pytest
from unittest.mock import Mock, patch

from casare_rpa.presentation.canvas.controllers.connection_controller import (
    ConnectionController,
)


@pytest.fixture
def mock_main_window() -> None:
    """Create a mock MainWindow."""
    mock = Mock()
    mock._central_widget = Mock()
    mock._central_widget.graph = Mock()
    return mock


@pytest.fixture
def connection_controller(mock_main_window) -> None:
    """Create a ConnectionController instance."""
    controller = ConnectionController(mock_main_window)
    controller.initialize()
    return controller


class TestConnectionControllerInitialization:
    """Tests for ConnectionController initialization."""

    def test_initialization(self, mock_main_window) -> None:
        """Test controller initializes correctly."""
        controller = ConnectionController(mock_main_window)
        assert controller.main_window == mock_main_window
        assert controller._auto_connect_enabled is False

    def test_cleanup(self, connection_controller) -> None:
        """Test cleanup."""
        connection_controller.cleanup()
        assert not connection_controller.is_initialized()


class TestCreateConnection:
    """Tests for connection creation."""

    def test_create_connection_success(self, connection_controller) -> None:
        """Test creating valid connection."""
        signal_emitted = []
        connection_controller.connection_created.connect(
            lambda src, tgt: signal_emitted.append((src, tgt))
        )

        result = connection_controller.create_connection(
            "node1", "output", "node2", "input"
        )

        assert result is True
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == ("node1", "node2")

    def test_create_connection_self_connection_blocked(
        self, connection_controller
    ) -> None:
        """Test self-connection is blocked."""
        signal_error = []
        connection_controller.connection_validation_error.connect(
            lambda err: signal_error.append(err)
        )

        result = connection_controller.create_connection(
            "node1", "output", "node1", "input"
        )

        assert result is False
        assert len(signal_error) == 1
        assert "itself" in signal_error[0].lower()


class TestDeleteConnection:
    """Tests for connection deletion."""

    def test_delete_connection(self, connection_controller) -> None:
        """Test deleting connection."""
        signal_emitted = []
        connection_controller.connection_deleted.connect(
            lambda src, tgt: signal_emitted.append((src, tgt))
        )

        connection_controller.delete_connection("node1", "node2")

        assert len(signal_emitted) == 1
        assert signal_emitted[0] == ("node1", "node2")


class TestValidateConnection:
    """Tests for connection validation."""

    def test_validate_connection_success(self, connection_controller) -> None:
        """Test validating valid connection."""
        is_valid, error = connection_controller.validate_connection(
            "node1", "output", "node2", "input"
        )

        assert is_valid is True
        assert error is None

    def test_validate_connection_self_connection(self, connection_controller) -> None:
        """Test validation blocks self-connection."""
        is_valid, error = connection_controller.validate_connection(
            "node1", "output", "node1", "input"
        )

        assert is_valid is False
        assert error is not None
        assert "itself" in error.lower()


class TestAutoConnect:
    """Tests for auto-connect mode."""

    def test_toggle_auto_connect_enable(
        self, connection_controller, mock_main_window
    ) -> None:
        """Test enabling auto-connect."""
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.set_acyclic = Mock()

        signal_emitted = []
        connection_controller.auto_connect_toggled.connect(
            lambda enabled: signal_emitted.append(enabled)
        )

        connection_controller.toggle_auto_connect(True)

        assert connection_controller.auto_connect_enabled is True
        assert len(signal_emitted) == 1
        assert signal_emitted[0] is True
        mock_graph.set_acyclic.assert_called_with(True)

    def test_toggle_auto_connect_disable(
        self, connection_controller, mock_main_window
    ) -> None:
        """Test disabling auto-connect."""
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.set_acyclic = Mock()

        connection_controller.toggle_auto_connect(False)

        assert connection_controller.auto_connect_enabled is False
        mock_graph.set_acyclic.assert_called_with(False)

    def test_auto_connect_enabled_property(self, connection_controller) -> None:
        """Test auto_connect_enabled property."""
        assert connection_controller.auto_connect_enabled is False

        connection_controller._auto_connect_enabled = True
        assert connection_controller.auto_connect_enabled is True
