"""
Tests for SuperNodeMixin.

This test suite covers the SuperNodeMixin that provides dynamic port and widget
management for Super Nodes in the visual layer.

Test Philosophy:
- Mock Qt components (QTimer, widgets, views)
- Mock VisualNode base class methods
- Test the mixin logic in isolation
- Focus on MRO, deferred callbacks, widget filtering

Run: pytest tests/presentation/test_super_node_mixin.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_qtimer():
    """Mock QTimer.singleShot to call callback immediately."""
    with patch(
        "casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin.QTimer"
    ) as mock:
        # Make singleShot call the callback immediately for testing
        def call_immediately(delay, callback):
            callback()

        mock.singleShot.side_effect = call_immediately
        yield mock


@pytest.fixture
def mock_schema():
    """Create a mock NodeSchema for testing."""
    schema = MagicMock()
    schema.properties = [
        MagicMock(name="action", essential=True),
        MagicMock(name="file_path", essential=False),
        MagicMock(name="content", essential=False),
    ]
    # Setup property name attributes
    schema.properties[0].name = "action"
    schema.properties[1].name = "file_path"
    schema.properties[2].name = "content"

    # Setup should_display to return True for action, conditionally for others
    def should_display(prop_name, config):
        if prop_name == "action":
            return True
        action = config.get("action", "")
        if action == "Read File":
            return prop_name == "file_path"
        elif action == "Write File":
            return prop_name in ("file_path", "content")
        return False

    schema.should_display = should_display
    return schema


@pytest.fixture
def mock_port_schema():
    """Create a mock DynamicPortSchema."""
    from casare_rpa.domain.value_objects.dynamic_port_config import (
        DynamicPortSchema,
        ActionPortConfig,
        PortDef,
    )
    from casare_rpa.domain.value_objects.types import DataType

    schema = DynamicPortSchema()
    schema.register(
        "Read File",
        ActionPortConfig.create(
            inputs=[PortDef("file_path", DataType.STRING)],
            outputs=[
                PortDef("content", DataType.STRING),
                PortDef("success", DataType.BOOLEAN),
            ],
        ),
    )
    schema.register(
        "Write File",
        ActionPortConfig.create(
            inputs=[
                PortDef("file_path", DataType.STRING),
                PortDef("content", DataType.STRING),
            ],
            outputs=[
                PortDef("bytes_written", DataType.INTEGER),
                PortDef("success", DataType.BOOLEAN),
            ],
        ),
    )
    return schema


# =============================================================================
# SuperNodeMixin Class Behavior Tests
# =============================================================================


class TestSuperNodeMixinClassAttributes:
    """Tests for SuperNodeMixin class-level attributes."""

    def test_dynamic_port_schema_default_none(self) -> None:
        """Test that DYNAMIC_PORT_SCHEMA defaults to None."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        assert SuperNodeMixin.DYNAMIC_PORT_SCHEMA is None

    def test_mixin_can_be_subclassed(self) -> None:
        """Test that SuperNodeMixin can be used in MRO."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        # Create a test subclass
        class MockVisualNode:
            def set_casare_node(self, node):
                pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        # Verify MRO
        mro_names = [cls.__name__ for cls in TestNode.__mro__]
        assert mro_names[0] == "TestNode"
        assert "SuperNodeMixin" in mro_names
        assert "MockVisualNode" in mro_names


class TestSuperNodeMixinSetCasareNode:
    """Tests for set_casare_node override."""

    def test_set_casare_node_calls_super(self, mock_qtimer) -> None:
        """Test that set_casare_node calls parent implementation."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        # Track if super was called
        super_called = []

        class MockVisualNode:
            def set_casare_node(self, node):
                super_called.append(node)

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        # Mock methods that will be called
        node = TestNode()
        node.get_current_action = MagicMock(return_value=None)
        node._filter_widgets_for_action = MagicMock()

        mock_casare_node = MagicMock()
        node.set_casare_node(mock_casare_node)

        # Verify super was called
        assert len(super_called) == 1
        assert super_called[0] == mock_casare_node

    def test_set_casare_node_triggers_widget_filter(self, mock_qtimer) -> None:
        """Test that set_casare_node triggers widget filtering via QTimer."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            def set_casare_node(self, node):
                pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node.get_current_action = MagicMock(return_value="Read File")
        node._filter_widgets_for_action = MagicMock()

        mock_casare_node = MagicMock()
        node.set_casare_node(mock_casare_node)

        # Verify filter was called (via deferred _apply_initial_widget_filter)
        node._filter_widgets_for_action.assert_called_once_with("Read File")


class TestSuperNodeMixinSetupActionListener:
    """Tests for _setup_action_listener and related methods."""

    def test_setup_action_listener_initializes_storage(self, mock_qtimer) -> None:
        """Test that _setup_action_listener initializes widget storage dicts."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node.get_widget = MagicMock(return_value=None)

        node._setup_action_listener()

        assert hasattr(node, "_hidden_widgets")
        assert hasattr(node, "_widget_values")
        assert isinstance(node._hidden_widgets, dict)
        assert isinstance(node._widget_values, dict)

    def test_setup_action_listener_sets_collapsed_false(self, mock_qtimer) -> None:
        """Test that super nodes start expanded (not collapsed)."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node.get_widget = MagicMock(return_value=None)

        node._setup_action_listener()

        assert hasattr(node, "_collapsed")
        assert node._collapsed is False


class TestSuperNodeMixinOnActionChanged:
    """Tests for _on_action_changed handler."""

    def test_on_action_changed_no_schema_logs_warning(self, mock_qtimer) -> None:
        """Test that changing action with no schema logs warning."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            DYNAMIC_PORT_SCHEMA = None

        node = TestNode()

        # Should not raise, just log warning
        node._on_action_changed("Read File")

    def test_on_action_changed_calls_clear_and_create(
        self, mock_qtimer, mock_port_schema
    ) -> None:
        """Test that action change clears old ports and creates new ones."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        TestNode.DYNAMIC_PORT_SCHEMA = mock_port_schema

        node = TestNode()
        node._clear_dynamic_ports = MagicMock()
        node._create_ports_from_config = MagicMock()
        node._filter_widgets_for_action = MagicMock()
        node.view = None

        node._on_action_changed("Write File")

        node._clear_dynamic_ports.assert_called_once()
        node._create_ports_from_config.assert_called_once()
        node._filter_widgets_for_action.assert_called_once_with("Write File")

    def test_on_action_changed_invalid_action(
        self, mock_qtimer, mock_port_schema
    ) -> None:
        """Test that invalid action logs warning but doesn't crash."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        TestNode.DYNAMIC_PORT_SCHEMA = mock_port_schema

        node = TestNode()
        node._clear_dynamic_ports = MagicMock()

        # Should not raise, config returns None for invalid action
        node._on_action_changed("Invalid Action")

        # Should not have cleared ports since config was None
        node._clear_dynamic_ports.assert_not_called()


class TestSuperNodeMixinWidgetManagement:
    """Tests for widget hiding and restoring."""

    def test_hide_widget_stores_in_hidden(self) -> None:
        """Test that _hide_widget moves widget to hidden storage."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node._hidden_widgets = {}
        node._widget_values = {}

        # Setup mock view with widgets
        mock_widget = MagicMock()
        node.view = MagicMock()
        node.view._widgets = {"test_widget": mock_widget}
        node.get_property = MagicMock(return_value="test_value")

        node._hide_widget("test_widget")

        # Widget should be moved to hidden storage
        assert "test_widget" in node._hidden_widgets
        assert node._hidden_widgets["test_widget"] == mock_widget
        assert "test_widget" not in node.view._widgets

        # Widget should be set invisible
        mock_widget.setVisible.assert_called_with(False)

    def test_restore_widget_returns_from_hidden(self) -> None:
        """Test that _restore_widget moves widget back from hidden storage."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()

        mock_widget = MagicMock()
        node._hidden_widgets = {"test_widget": mock_widget}
        node._widget_values = {"test_widget": "saved_value"}

        node.view = MagicMock()
        node.view._widgets = {}
        node.set_property = MagicMock()

        node._restore_widget("test_widget")

        # Widget should be moved back to view
        assert "test_widget" in node.view._widgets
        assert node.view._widgets["test_widget"] == mock_widget
        assert "test_widget" not in node._hidden_widgets

        # Widget should be set visible
        mock_widget.setVisible.assert_called_with(True)

        # Value should be restored
        node.set_property.assert_called_with("test_widget", "saved_value")


class TestSuperNodeMixinPortManagement:
    """Tests for port clearing and creation."""

    def test_clear_dynamic_ports_preserves_exec(self) -> None:
        """Test that _clear_dynamic_ports keeps exec ports."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()

        # Mock ports
        exec_in = MagicMock()
        exec_in.name.return_value = "exec_in"
        exec_out = MagicMock()
        exec_out.name.return_value = "exec_out"
        data_port = MagicMock()
        data_port.name.return_value = "file_path"

        node.input_ports = MagicMock(return_value=[exec_in, data_port])
        node.output_ports = MagicMock(return_value=[exec_out])
        node.delete_input = MagicMock()
        node.delete_output = MagicMock()

        node._clear_dynamic_ports()

        # Should delete data port but not exec ports
        node.delete_input.assert_called_once_with(data_port)
        node.delete_output.assert_not_called()  # exec_out should be preserved

    def test_create_ports_from_config(self, mock_port_schema) -> None:
        """Test that _create_ports_from_config creates correct ports."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node.add_typed_input = MagicMock()
        node.add_typed_output = MagicMock()

        config = mock_port_schema.get_config("Write File")
        node._create_ports_from_config(config)

        # Should create 2 inputs (file_path, content) and 2 outputs (bytes_written, success)
        assert node.add_typed_input.call_count == 2
        assert node.add_typed_output.call_count == 2


class TestSuperNodeMixinGetCurrentAction:
    """Tests for get_current_action method."""

    def test_get_current_action_returns_value(self) -> None:
        """Test getting current action from widget."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()

        # Setup mock widget with combo box
        mock_combo = MagicMock()
        mock_combo.currentText.return_value = "Write File"

        mock_widget = MagicMock()
        mock_widget.get_custom_widget.return_value = mock_combo

        node.get_widget = MagicMock(return_value=mock_widget)

        result = node.get_current_action()

        assert result == "Write File"

    def test_get_current_action_no_widget(self) -> None:
        """Test get_current_action returns None when widget missing."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node.get_widget = MagicMock(return_value=None)

        result = node.get_current_action()

        assert result is None


class TestSuperNodeMixinGetPortConfig:
    """Tests for get_port_config_for_action method."""

    def test_get_port_config_existing(self, mock_port_schema) -> None:
        """Test getting config for existing action."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        TestNode.DYNAMIC_PORT_SCHEMA = mock_port_schema
        node = TestNode()

        config = node.get_port_config_for_action("Read File")

        assert config is not None
        assert len(config.inputs) == 1
        assert len(config.outputs) == 2

    def test_get_port_config_no_schema(self) -> None:
        """Test getting config when no schema defined."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            DYNAMIC_PORT_SCHEMA = None

        node = TestNode()

        config = node.get_port_config_for_action("Read File")

        assert config is None


# =============================================================================
# Integration-Style Tests (Mocked but More Complete)
# =============================================================================


class TestSuperNodeMixinIntegration:
    """Integration-style tests for SuperNodeMixin behavior."""

    def test_action_change_workflow(self, mock_qtimer, mock_port_schema) -> None:
        """Test complete action change workflow."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        TestNode.DYNAMIC_PORT_SCHEMA = mock_port_schema

        node = TestNode()

        # Setup all required mocks
        node._clear_dynamic_ports = MagicMock()
        node._create_ports_from_config = MagicMock()
        node._filter_widgets_for_action = MagicMock()
        node._configure_port_colors = MagicMock()
        node.view = MagicMock()
        node.view.post_init = MagicMock()

        # Simulate action change from Read to Write
        node._on_action_changed("Write File")

        # Verify complete workflow
        node._clear_dynamic_ports.assert_called_once()
        node._create_ports_from_config.assert_called_once()
        node._filter_widgets_for_action.assert_called_once_with("Write File")

    def test_backward_compatibility_alias(self) -> None:
        """Test _update_widget_visibility_for_action is alias for _filter_widgets_for_action."""
        from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
            SuperNodeMixin,
        )

        class MockVisualNode:
            pass

        class TestNode(SuperNodeMixin, MockVisualNode):
            pass

        node = TestNode()
        node._filter_widgets_for_action = MagicMock()

        # Call the backward compatibility alias
        node._update_widget_visibility_for_action("Test Action")

        # Should delegate to the main method
        node._filter_widgets_for_action.assert_called_once_with("Test Action")
