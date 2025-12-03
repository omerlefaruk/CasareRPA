"""
Fixtures for controller tests.

Provides shared mocks for:
- MainWindow and its component accessors
- Qt graph/viewer components
- Panels and docks
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, PropertyMock
from typing import Dict, Any, Optional, List


@pytest.fixture
def mock_graph() -> Mock:
    """
    Mock NodeGraphQt graph object.

    Provides:
    - Node operations (all_nodes, selected_nodes, clear_selection)
    - Viewer access
    - Connection operations
    """
    graph = Mock()
    graph.all_nodes.return_value = []
    graph.selected_nodes.return_value = []
    graph.clear_selection = Mock()

    # Mock viewer
    viewer = Mock()
    viewer.mapFromGlobal = Mock(
        return_value=Mock(x=Mock(return_value=0), y=Mock(return_value=0))
    )
    viewer.mapToScene = Mock(
        return_value=Mock(x=Mock(return_value=100), y=Mock(return_value=100))
    )
    viewer.center_on = Mock()
    viewer.start_live_connection = Mock()
    graph.viewer.return_value = viewer

    # Graph configuration
    graph.set_acyclic = Mock()
    graph.set_import_file_callback = Mock()
    graph.set_import_callback = Mock()
    graph.setup_drag_drop = Mock()

    return graph


@pytest.fixture
def mock_visual_node() -> Mock:
    """
    Mock visual node for graph operations.

    Provides:
    - Position and selection state
    - Port access
    - Casare node reference
    """
    node = Mock()
    node.pos.return_value = (100, 100)
    node.name.return_value = "TestNode"
    node.get_property.return_value = "test_node_id"
    node.set_property = Mock()
    node.set_selected = Mock()
    node.output_ports.return_value = []
    node.input_ports.return_value = []

    # View for opacity changes
    view = Mock()
    view.setOpacity = Mock()
    node.view = view

    # Casare node reference
    casare_node = Mock()
    casare_node.config = {}
    node.get_casare_node = Mock(return_value=casare_node)

    return node


@pytest.fixture
def mock_bottom_panel() -> Mock:
    """
    Mock bottom panel dock widget.

    Provides:
    - Visibility control
    - Tab widget access
    - Validation error retrieval
    """
    panel = Mock()
    panel.isVisible.return_value = False
    panel.setVisible = Mock()
    panel.show = Mock()
    panel.hide = Mock()
    panel.validation_requested = Mock()
    panel.validation_requested.emit = Mock()
    panel.get_validation_errors_blocking.return_value = []
    panel.show_output_tab = Mock()
    panel.show_log_tab = Mock()
    panel.show_variables_tab = Mock()
    panel.show_validation_tab = Mock()
    panel.trigger_validation = Mock()

    # Tab widget
    tab_widget = Mock()
    tab_widget.currentIndex.return_value = 0
    tab_widget.setCurrentIndex = Mock()
    panel._tab_widget = tab_widget

    return panel


@pytest.fixture
def mock_properties_panel() -> Mock:
    """Mock properties panel dock widget."""
    panel = Mock()
    panel.isVisible.return_value = False
    panel.setVisible = Mock()
    panel.show = Mock()
    panel.hide = Mock()
    return panel


@pytest.fixture
def mock_variable_inspector() -> Mock:
    """Mock variable inspector dock."""
    inspector = Mock()
    inspector.isVisible.return_value = False
    inspector.setVisible = Mock()
    inspector.show = Mock()
    inspector.hide = Mock()
    inspector.update_variables = Mock()
    return inspector


@pytest.fixture
def mock_minimap() -> Mock:
    """Mock minimap overlay widget."""
    minimap = Mock()
    minimap.isVisible.return_value = False
    minimap.setVisible = Mock()
    minimap.show = Mock()
    minimap.hide = Mock()
    minimap.height.return_value = 150
    minimap.move = Mock()
    minimap.raise_ = Mock()
    return minimap


@pytest.fixture
def mock_main_window(
    mock_graph,
    mock_bottom_panel,
    mock_properties_panel,
    mock_variable_inspector,
    mock_minimap,
) -> Mock:
    """
    Mock MainWindow with all component accessors.

    Provides:
    - Graph access via get_graph()
    - Panel access via get_*_panel() methods
    - Status display
    - Window title management
    - Action references
    """
    window = Mock()

    # Graph access
    window.get_graph.return_value = mock_graph

    # Panel accessors
    window.get_bottom_panel.return_value = mock_bottom_panel
    window.get_properties_panel.return_value = mock_properties_panel
    window.get_variable_inspector_dock.return_value = mock_variable_inspector
    window.get_minimap.return_value = mock_minimap

    # Status bar
    window.show_status = Mock()

    # Window title
    window.setWindowTitle = Mock()

    # Actions
    window.action_save = Mock()
    window.action_save.setEnabled = Mock()
    window.action_toggle_bottom_panel = Mock()
    window.action_toggle_bottom_panel.setChecked = Mock()
    window.action_toggle_variable_inspector = Mock()
    window.action_toggle_variable_inspector.setChecked = Mock()

    # Workflow data provider
    window._get_workflow_data = Mock(return_value={"nodes": {}, "connections": []})

    # Modified state
    window.set_modified = Mock()

    # Node controller accessor
    node_controller = Mock()
    node_controller.navigate_to_node = Mock()
    window.get_node_controller.return_value = node_controller

    # Central widget
    central_widget = Mock()
    central_widget.height.return_value = 600
    window._central_widget = central_widget

    # Status bar buttons
    window._btn_variables = Mock()
    window._btn_variables.setChecked = Mock()
    window._btn_output = Mock()
    window._btn_output.setChecked = Mock()
    window._btn_log = Mock()
    window._btn_log.setChecked = Mock()
    window._btn_validation = Mock()
    window._btn_validation.setChecked = Mock()

    # Workflow template signal
    window.workflow_new_from_template = Mock()
    window.workflow_new_from_template.emit = Mock()

    return window


@pytest.fixture
def mock_file_dialog(mocker) -> Mock:
    """
    Mock QFileDialog for file operations.

    Returns:
        Mock configured to return test file paths
    """
    dialog = mocker.patch(
        "casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog"
    )
    dialog.getOpenFileName.return_value = ("", "")
    dialog.getSaveFileName.return_value = ("", "")
    return dialog


@pytest.fixture
def mock_message_box(mocker) -> Mock:
    """
    Mock QMessageBox for user prompts.

    Returns:
        Mock configured to return standard button values
    """
    from PySide6.QtWidgets import QMessageBox

    msgbox = mocker.patch(
        "casare_rpa.presentation.canvas.controllers.workflow_controller.QMessageBox"
    )
    msgbox.StandardButton = QMessageBox.StandardButton
    msgbox.question.return_value = QMessageBox.StandardButton.Save
    msgbox.warning.return_value = QMessageBox.StandardButton.Yes
    msgbox.information.return_value = QMessageBox.StandardButton.Ok
    msgbox.critical.return_value = QMessageBox.StandardButton.Ok
    return msgbox
