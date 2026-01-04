"""
Tests for NodeSearchV2 - Epic 3.2 Node Search Popup.

Tests the v2 node search popup with PopupWindowBase base class,
THEME_V2/TOKENS_V2 styling, and keyboard navigation.
"""

from unittest.mock import MagicMock, Mock

import pytest
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.popups import (
    NodeSearchResult,
    NodeSearchV2,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_graph():
    """Create a mock NodeGraph with test nodes."""
    graph = MagicMock()

    # Create mock nodes
    mock_nodes = []

    # Browser node - use Browser in name to match category detection
    browser_node = MagicMock()
    browser_node.id.return_value = "browser_1"
    browser_node.get_property.return_value = "browser_1"
    browser_node.name.return_value = "Navigate to URL"
    browser_node.__class__.__name__ = "VisualBrowserNavigateNode"
    mock_nodes.append(browser_node)

    # Desktop node - use Desktop in name to match category detection
    desktop_node = MagicMock()
    desktop_node.id.return_value = "desktop_1"
    desktop_node.get_property.return_value = "desktop_1"
    desktop_node.name.return_value = "Click Desktop Element"
    desktop_node.__class__.__name__ = "VisualDesktopClickNode"
    mock_nodes.append(desktop_node)

    # Variable node - use Variable in name to match category detection
    variable_node = MagicMock()
    variable_node.id.return_value = "var_1"
    variable_node.get_property.return_value = "var_1"
    variable_node.name.return_value = "Set Variable"
    variable_node.__class__.__name__ = "VisualVariableSetNode"
    mock_nodes.append(variable_node)

    # Control flow node - use Control in name to match category detection
    control_node = MagicMock()
    control_node.id.return_value = "control_1"
    control_node.get_property.return_value = "control_1"
    control_node.name.return_value = "If Condition"
    control_node.__class__.__name__ = "VisualControlIfNode"
    mock_nodes.append(control_node)

    graph.all_nodes.return_value = mock_nodes

    # Mock fit_to_selection and clear_selection
    graph.fit_to_selection = Mock()
    graph.clear_selection = Mock()

    return graph


@pytest.fixture
def parent_widget(qtbot):
    """Create a real QWidget parent for testing."""
    widget = QWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def search_popup(mock_graph, parent_widget):
    """Create a NodeSearchV2 instance for testing."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    return popup


# =============================================================================
# Initialization Tests
# =============================================================================


def test_node_search_v2_initialization(mock_graph, parent_widget):
    """Test NodeSearchV2 initializes correctly."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)

    assert popup._graph == mock_graph
    assert popup._all_nodes == []
    assert popup._filtered_nodes == []
    # PopupWindowBase uses _title_label for the title
    assert popup._title == "Find Node"


def test_node_search_v2_default_dimensions(mock_graph, parent_widget):
    """Test default dimensions are set correctly."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)

    assert popup.DEFAULT_WIDTH == 450
    assert popup.DEFAULT_HEIGHT == 400
    assert popup.MIN_WIDTH == 350
    assert popup.MIN_HEIGHT == 250


# =============================================================================
# Signal Tests
# =============================================================================


def test_node_search_v2_node_selected_signal(mock_graph, parent_widget, qtbot):
    """Test node_selected signal is defined."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)

    # Track signal emissions
    signal_emitted = []
    popup.node_selected.connect(lambda node_id: signal_emitted.append(node_id))

    assert hasattr(popup, "node_selected")
    assert signal_emitted == []


# =============================================================================
# Node Loading Tests
# =============================================================================


def test_load_nodes(mock_graph, parent_widget):
    """Test loading nodes from graph."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._load_nodes()

    assert len(popup._all_nodes) == 4

    # Check browser node
    browser_result = next((n for n in popup._all_nodes if n.node_id == "browser_1"), None)
    assert browser_result is not None
    assert browser_result.name == "Navigate to URL"
    assert browser_result.category == "Browser"

    # Check desktop node
    desktop_result = next((n for n in popup._all_nodes if n.node_id == "desktop_1"), None)
    assert desktop_result is not None
    assert desktop_result.category == "Desktop"

    # Check variable node
    var_result = next((n for n in popup._all_nodes if n.node_id == "var_1"), None)
    assert var_result is not None
    assert var_result.category == "Variable"

    # Check control flow node
    control_result = next((n for n in popup._all_nodes if n.node_id == "control_1"), None)
    assert control_result is not None
    assert control_result.category == "Control Flow"


# =============================================================================
# Filtering Tests
# =============================================================================


def test_filter_nodes_empty_query(mock_graph, parent_widget):
    """Test filtering with empty query returns all nodes."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._load_nodes()

    popup._filter_nodes("")

    assert len(popup._filtered_nodes) == 4


def test_filter_nodes_by_name(mock_graph, parent_widget):
    """Test filtering by node name."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._load_nodes()

    popup._filter_nodes("navigate")

    assert len(popup._filtered_nodes) == 1
    assert popup._filtered_nodes[0].node_id == "browser_1"


def test_filter_nodes_by_type(mock_graph, parent_widget):
    """Test filtering by node type."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._load_nodes()

    popup._filter_nodes("variable")

    assert len(popup._filtered_nodes) == 1
    assert popup._filtered_nodes[0].node_id == "var_1"


def test_filter_nodes_case_insensitive(mock_graph, parent_widget):
    """Test filtering is case-insensitive."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._load_nodes()

    popup._filter_nodes("CLICK")

    assert len(popup._filtered_nodes) == 1
    assert popup._filtered_nodes[0].node_id == "desktop_1"


def test_filter_nodes_no_results(mock_graph, parent_widget):
    """Test filtering with no matching results."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._load_nodes()

    popup._filter_nodes("nonexistent")

    assert len(popup._filtered_nodes) == 0


# =============================================================================
# Node Selection Tests
# =============================================================================


def test_select_and_center_node(mock_graph, parent_widget):
    """Test selecting and centering on a node."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup._select_and_center_node("browser_1")

    mock_graph.clear_selection.assert_called_once()

    # Verify the node was selected
    for node in mock_graph.all_nodes():
        if node.get_property("node_id") == "browser_1":
            node.set_selected.assert_called_once_with(True)

    mock_graph.fit_to_selection.assert_called_once()


# =============================================================================
# Keyboard Navigation Tests
# =============================================================================


def test_keyboard_navigation_down(mock_graph, parent_widget):
    """Test Down arrow key moves selection down."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup.show_search()

    initial_row = popup._results_list.currentRow()
    popup._move_selection(1)

    # With 4 nodes, moving down from row 0 should go to row 1
    assert popup._results_list.currentRow() == initial_row + 1


def test_keyboard_navigation_up(mock_graph, parent_widget):
    """Test Up arrow key moves selection up."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup.show_search()

    # Start at row 1
    popup._results_list.setCurrentRow(1)
    popup._move_selection(-1)

    assert popup._results_list.currentRow() == 0


def test_keyboard_navigation_bounds(mock_graph, parent_widget):
    """Test navigation stays within list bounds."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)
    popup.show_search()

    # Try to move up from first item
    popup._results_list.setCurrentRow(0)
    popup._move_selection(-1)
    assert popup._results_list.currentRow() == 0

    # Try to move down from last item
    last_row = popup._results_list.count() - 1
    popup._results_list.setCurrentRow(last_row)
    popup._move_selection(1)
    assert popup._results_list.currentRow() == last_row


# =============================================================================
# Show/Position Tests
# =============================================================================


def test_show_search_loads_nodes(mock_graph, parent_widget):
    """Test show_search loads and displays nodes."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)

    popup.show_search()

    assert len(popup._all_nodes) == 4
    assert popup._results_list.count() == 4


def test_show_search_clears_input(mock_graph, parent_widget):
    """Test show_search clears the search input."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)

    # Type something in search - SearchInput uses set_value/get_value
    popup._search_input.set_value("test")
    popup.show_search()

    assert popup._search_input.get_value() == ""


def test_show_search_focuses_input(mock_graph, parent_widget):
    """Test show_search focuses the search input."""
    popup = NodeSearchV2(graph=mock_graph, parent=parent_widget)

    # Mock the setFocus method on the internal QLineEdit to verify it's called
    # SearchInput stores its QLineEdit in _input
    original_focus = popup._search_input._input.setFocus
    focus_called = []

    def mock_focus():
        focus_called.append(True)
        original_focus()

    popup._search_input._input.setFocus = mock_focus
    popup.show_search()

    # Verify setFocus was called
    assert len(focus_called) > 0


# =============================================================================
# Theme Tests
# =============================================================================


def test_uses_theme_v2_tokens():
    """Test NodeSearchV2 uses THEME_V2/TOKENS_V2."""
    # Verify tokens are accessible
    assert hasattr(THEME_V2, "bg_surface")
    assert hasattr(THEME_V2, "text_primary")
    assert hasattr(TOKENS_V2, "spacing")
    assert hasattr(TOKENS_V2, "radius")


# =============================================================================
# NodeSearchResult Tests
# =============================================================================


def test_node_search_result_dataclass():
    """Test NodeSearchResult is a frozen dataclass."""
    result = NodeSearchResult(
        node_id="test_1", name="Test Node", node_type="VisualTestNode", category="Test"
    )

    assert result.node_id == "test_1"
    assert result.name == "Test Node"
    assert result.node_type == "VisualTestNode"
    assert result.category == "Test"


def test_node_search_result_frozen():
    """Test NodeSearchResult is frozen (immutable)."""
    result = NodeSearchResult(
        node_id="test_1", name="Test Node", node_type="VisualTestNode", category="Test"
    )

    # Attempting to modify should raise AttributeError or FrozenInstanceError
    with pytest.raises((AttributeError, TypeError)):
        result.name = "Modified"
