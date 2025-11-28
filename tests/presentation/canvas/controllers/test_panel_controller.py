"""
Comprehensive tests for PanelController.

Tests panel management including:
- Panel visibility toggling
- Bottom panel
- Properties panel
- Variable inspector
- Minimap
- Tab switching
"""

import pytest
from unittest.mock import Mock
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.panel_controller import PanelController


@pytest.fixture
def mock_main_window(qtbot):
    """Create a real QMainWindow with mocked panel methods."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    main_window._bottom_panel = Mock()
    main_window._bottom_panel.setVisible = Mock()
    main_window._properties_panel = Mock()
    main_window._properties_panel.setVisible = Mock()
    main_window._variable_inspector_dock = Mock()
    main_window._variable_inspector_dock.setVisible = Mock()

    # Mock getter methods
    main_window.get_bottom_panel = Mock(return_value=main_window._bottom_panel)
    main_window.get_properties_panel = Mock(return_value=main_window._properties_panel)
    main_window.get_variable_inspector_dock = Mock(
        return_value=main_window._variable_inspector_dock
    )

    return main_window


@pytest.fixture
def panel_controller(mock_main_window):
    """Create a PanelController instance."""
    controller = PanelController(mock_main_window)
    controller.initialize()
    return controller


class TestPanelControllerInitialization:
    """Tests for PanelController initialization."""

    def test_initialization(self, mock_main_window) -> None:
        """Test controller initializes."""
        controller = PanelController(mock_main_window)
        assert controller.main_window == mock_main_window

    def test_cleanup(self, panel_controller) -> None:
        """Test cleanup."""
        panel_controller.cleanup()
        assert not panel_controller.is_initialized


class TestBottomPanel:
    """Tests for bottom panel toggling."""

    def test_toggle_bottom_panel_show(self, panel_controller, mock_main_window) -> None:
        """Test showing bottom panel."""
        signal_emitted = []
        panel_controller.bottom_panel_toggled.connect(
            lambda visible: signal_emitted.append(visible)
        )

        panel_controller.toggle_bottom_panel(True)

        mock_main_window._bottom_panel.setVisible.assert_called_with(True)
        assert len(signal_emitted) == 1
        assert signal_emitted[0] is True

    def test_toggle_bottom_panel_hide(self, panel_controller, mock_main_window) -> None:
        """Test hiding bottom panel."""
        panel_controller.toggle_bottom_panel(False)

        mock_main_window._bottom_panel.setVisible.assert_called_with(False)

    def test_toggle_bottom_panel_not_available(
        self, panel_controller, mock_main_window
    ) -> None:
        """Test toggling when panel not available."""
        mock_main_window._bottom_panel = None

        # Should not raise error
        panel_controller.toggle_bottom_panel(True)


class TestPropertiesPanel:
    """Tests for properties panel toggling."""

    def test_toggle_properties_panel_show(
        self, panel_controller, mock_main_window
    ) -> None:
        """Test showing properties panel."""
        signal_emitted = []
        panel_controller.properties_panel_toggled.connect(
            lambda visible: signal_emitted.append(visible)
        )

        panel_controller.toggle_properties_panel(True)

        mock_main_window._properties_panel.setVisible.assert_called_with(True)
        assert len(signal_emitted) == 1

    def test_toggle_properties_panel_hide(
        self, panel_controller, mock_main_window
    ) -> None:
        """Test hiding properties panel."""
        panel_controller.toggle_properties_panel(False)

        mock_main_window._properties_panel.setVisible.assert_called_with(False)


class TestVariableInspector:
    """Tests for variable inspector toggling."""

    def test_toggle_variable_inspector_show(
        self, panel_controller, mock_main_window
    ) -> None:
        """Test showing variable inspector."""
        signal_emitted = []
        panel_controller.variable_inspector_toggled.connect(
            lambda visible: signal_emitted.append(visible)
        )

        panel_controller.toggle_variable_inspector(True)

        mock_main_window._variable_inspector_dock.setVisible.assert_called_with(True)
        assert len(signal_emitted) == 1

    def test_toggle_variable_inspector_hide(
        self, panel_controller, mock_main_window
    ) -> None:
        """Test hiding variable inspector."""
        panel_controller.toggle_variable_inspector(False)

        mock_main_window._variable_inspector_dock.setVisible.assert_called_with(False)
