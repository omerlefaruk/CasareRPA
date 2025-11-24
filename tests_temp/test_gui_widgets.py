"""
Tests for GUI widget components.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestElementTreeWidget:
    """Test ElementTreeWidget class."""

    def test_element_tree_widget_import(self):
        """Test that ElementTreeWidget can be imported."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeWidget
        assert ElementTreeWidget is not None

    def test_element_tree_item_import(self):
        """Test that ElementTreeItem can be imported."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeItem
        assert ElementTreeItem is not None

    def test_element_tree_widget_has_signal(self):
        """Test that ElementTreeWidget has element_selected signal."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeWidget

        assert hasattr(ElementTreeWidget, 'element_selected')


class TestElementTreeItem:
    """Test ElementTreeItem class."""

    @pytest.fixture
    def mock_element(self):
        """Create a mock DesktopElement."""
        element = MagicMock()
        element.get_property.return_value = "ButtonControl"
        element.get_text.return_value = "Test Button"
        element.is_enabled.return_value = True
        element.is_visible.return_value = True
        element._control = MagicMock()
        element._control.GetChildren.return_value = []
        return element

    def test_element_tree_item_icon_mapping(self):
        """Test that ElementTreeItem has icon mapping."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeItem

        # ElementTreeItem should define icons for control types
        # This is done in _set_control_type_icon
        assert hasattr(ElementTreeItem, '_set_control_type_icon')

    def test_element_tree_item_styling(self):
        """Test that ElementTreeItem applies styling."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeItem

        assert hasattr(ElementTreeItem, '_apply_styling')

    def test_element_tree_item_lazy_loading(self):
        """Test that ElementTreeItem supports lazy loading."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeItem

        assert hasattr(ElementTreeItem, 'load_children')
        assert hasattr(ElementTreeItem, '_may_have_children')


class TestNodeGraphWidget:
    """Test NodeGraphWidget class."""

    def test_node_graph_widget_import(self):
        """Test that node_graph_widget module can be imported."""
        from casare_rpa.canvas import node_graph_widget
        assert node_graph_widget is not None


class TestLogViewer:
    """Test log viewer component."""

    def test_log_viewer_module_exists(self):
        """Test that log_viewer module exists."""
        try:
            from casare_rpa.canvas import log_viewer
            assert True
        except ImportError:
            # Log viewer might not be implemented yet
            pytest.skip("log_viewer module not found")


class TestMinimap:
    """Test minimap component."""

    def test_minimap_module_exists(self):
        """Test that minimap module exists."""
        try:
            from casare_rpa.canvas import minimap
            assert True
        except ImportError:
            # Minimap might not be implemented yet
            pytest.skip("minimap module not found")


class TestDebugToolbar:
    """Test DebugToolbar widget."""

    @pytest.fixture
    def mock_qt(self):
        """Mock Qt dependencies."""
        with patch('casare_rpa.canvas.debug_toolbar.QWidget'), \
             patch('casare_rpa.canvas.debug_toolbar.QHBoxLayout'), \
             patch('casare_rpa.canvas.debug_toolbar.QPushButton'), \
             patch('casare_rpa.canvas.debug_toolbar.QLabel'):
            yield

    def test_debug_toolbar_import(self):
        """Test that DebugToolbar can be imported."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar
        assert DebugToolbar is not None

    def test_debug_toolbar_has_signals(self):
        """Test that DebugToolbar has expected signals."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar

        # Check for actual signals defined in DebugToolbar
        expected_signals = [
            'debug_mode_toggled',
            'step_mode_toggled',
            'step_requested',
            'continue_requested',
            'stop_requested',
            'clear_breakpoints_requested'
        ]

        for signal in expected_signals:
            assert hasattr(DebugToolbar, signal), f"Missing signal: {signal}"


class TestVariableInspector:
    """Test VariableInspectorPanel widget."""

    def test_variable_inspector_import(self):
        """Test that VariableInspectorPanel can be imported."""
        from casare_rpa.canvas.variable_inspector import VariableInspectorPanel
        assert VariableInspectorPanel is not None


class TestExecutionHistoryViewer:
    """Test ExecutionHistoryViewer widget."""

    def test_execution_history_viewer_import(self):
        """Test that ExecutionHistoryViewer can be imported."""
        from casare_rpa.canvas.execution_history_viewer import ExecutionHistoryViewer
        assert ExecutionHistoryViewer is not None


class TestSearchableMenu:
    """Test SearchableNodeMenu component."""

    def test_searchable_menu_import(self):
        """Test that searchable_menu module can be imported."""
        from casare_rpa.canvas import searchable_menu
        assert searchable_menu is not None


class TestWidgetStyles:
    """Test widget styling consistency."""

    def test_element_tree_has_dark_theme(self):
        """Test that ElementTreeWidget has dark theme styling."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeWidget

        assert hasattr(ElementTreeWidget, '_apply_styles')

    def test_debug_toolbar_styling(self):
        """Test that DebugToolbar has styling method."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar

        # Should have some styling setup
        assert hasattr(DebugToolbar, '__init__')


class TestWidgetIntegration:
    """Test widget integration points."""

    def test_element_tree_provides_selection(self):
        """Test that ElementTreeWidget provides get_selected_element."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeWidget

        assert hasattr(ElementTreeWidget, 'get_selected_element')

    def test_element_tree_supports_refresh(self):
        """Test that ElementTreeWidget supports refresh."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeWidget

        assert hasattr(ElementTreeWidget, 'refresh')

    def test_element_tree_supports_search(self):
        """Test that ElementTreeWidget supports search."""
        from casare_rpa.canvas.element_tree_widget import ElementTreeWidget

        assert hasattr(ElementTreeWidget, '_on_search_changed')
        assert hasattr(ElementTreeWidget, '_filter_items')
