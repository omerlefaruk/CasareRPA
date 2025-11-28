"""
Tests for SelectorController.

Tests selector/picker functionality including:
- Selector picker start/stop
- Browser element selection
- Workflow recording
- Event publishing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from PySide6.QtCore import QObject

from casare_rpa.presentation.canvas.controllers.selector_controller import (
    SelectorController,
)
from casare_rpa.presentation.canvas.events.event_types import EventType


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QObject()
    main_window.get_current_file = Mock(return_value=None)
    return main_window


@pytest.fixture
def mock_selector_integration():
    """Create a mock selector integration."""
    integration = Mock()
    integration.start_picking = AsyncMock()
    integration.stop_selector_mode = AsyncMock()
    integration.start_recording = AsyncMock()
    integration.initialize_for_page = AsyncMock()
    integration.is_active = False
    integration.is_picking = False
    integration.is_recording = False
    return integration


@pytest.fixture
def selector_controller(mock_main_window, mock_selector_integration):
    """Create a SelectorController instance."""
    with patch(
        "casare_rpa.canvas.selectors.selector_integration.SelectorIntegration",
        return_value=mock_selector_integration,
    ):
        controller = SelectorController(mock_main_window)
        controller.initialize()
        yield controller
        controller.cleanup()


class TestSelectorControllerInitialization:
    """Test controller initialization and cleanup."""

    def test_initialization(self, selector_controller):
        """Test controller initializes correctly."""
        assert selector_controller.is_initialized
        assert selector_controller._selector_integration is not None

    def test_cleanup(self, selector_controller):
        """Test controller cleanup."""
        selector_controller.cleanup()
        assert not selector_controller.is_initialized


class TestSelectorPicking:
    """Test selector picking functionality."""

    @pytest.mark.asyncio
    async def test_start_picker_success(
        self, selector_controller, mock_selector_integration
    ):
        """Test starting picker mode successfully."""
        target_node = Mock()

        await selector_controller.start_picker(target_node, "selector")

        mock_selector_integration.start_picking.assert_called_once_with(
            target_node, "selector"
        )

    @pytest.mark.asyncio
    async def test_start_picker_without_target(
        self, selector_controller, mock_selector_integration
    ):
        """Test starting picker without target node."""
        await selector_controller.start_picker()

        mock_selector_integration.start_picking.assert_called_once_with(
            None, "selector"
        )

    @pytest.mark.asyncio
    async def test_stop_picker(self, selector_controller, mock_selector_integration):
        """Test stopping picker mode."""
        await selector_controller.stop_picker()

        mock_selector_integration.stop_selector_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_recording(
        self, selector_controller, mock_selector_integration
    ):
        """Test starting workflow recording."""
        await selector_controller.start_recording()

        mock_selector_integration.start_recording.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_for_page(
        self, selector_controller, mock_selector_integration
    ):
        """Test initializing selector for Playwright page."""
        mock_page = Mock()

        await selector_controller.initialize_for_page(mock_page)

        mock_selector_integration.initialize_for_page.assert_called_once_with(mock_page)


class TestSelectorPickerState:
    """Test picker state management."""

    def test_is_picker_active_false(
        self, selector_controller, mock_selector_integration
    ):
        """Test picker active check when inactive."""
        mock_selector_integration.is_active = False

        assert not selector_controller.is_picker_active()

    def test_is_picker_active_true(
        self, selector_controller, mock_selector_integration
    ):
        """Test picker active check when active."""
        mock_selector_integration.is_active = True

        assert selector_controller.is_picker_active()

    def test_get_selector_integration(
        self, selector_controller, mock_selector_integration
    ):
        """Test getting selector integration instance."""
        assert (
            selector_controller.get_selector_integration() == mock_selector_integration
        )


class TestSelectorEvents:
    """Test event handling and publishing."""

    def test_selector_picked_signal(self, selector_controller):
        """Test selector picked signal emission."""
        signal_received = []

        def on_picked(selector_value, selector_type):
            signal_received.append((selector_value, selector_type))

        selector_controller.selector_picked.connect(on_picked)
        selector_controller._on_selector_picked("div.class", "css")

        assert signal_received == [("div.class", "css")]

    def test_selector_picked_event_published(self, selector_controller):
        """Test selector picked event is published to EventBus."""
        with patch.object(selector_controller._event_bus, "publish") as mock_publish:
            selector_controller._on_selector_picked("div.class", "css")

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.SELECTOR_PICKED
            assert event.data["selector_value"] == "div.class"
            assert event.data["selector_type"] == "css"

    def test_recording_complete_handler(self, selector_controller):
        """Test recording complete handler."""
        actions = [{"type": "click", "selector": "button"}]

        # Should not raise exception
        selector_controller._on_recording_complete(actions)


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_start_picker_when_not_initialized(self, qtbot):
        """Test starting picker when integration not initialized."""
        main_window = QObject()
        controller = SelectorController(main_window)
        # Don't call initialize()

        # Should not raise exception
        await controller.start_picker()

    @pytest.mark.asyncio
    async def test_start_picker_failure(
        self, selector_controller, mock_selector_integration
    ):
        """Test starting picker with exception."""
        mock_selector_integration.start_picking.side_effect = Exception("Test error")

        # Should not raise exception
        await selector_controller.start_picker()

    def test_is_picker_active_when_not_initialized(self, qtbot):
        """Test is_picker_active when integration not initialized."""
        main_window = QObject()
        controller = SelectorController(main_window)
        # Don't call initialize()

        assert not controller.is_picker_active()
