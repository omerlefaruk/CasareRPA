# Controller Testing Reference

Templates for testing Canvas UI controllers.

## Controller Test Template

```python
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from casare_rpa.presentation.canvas.controllers.{controller_name} import {ControllerName}

@pytest.fixture
def mock_graph():
    graph = MagicMock()
    graph.add_node = MagicMock()
    graph.remove_node = MagicMock()
    graph.selected_nodes = MagicMock(return_value=[])
    return graph

@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.emit = MagicMock()
    bus.subscribe = MagicMock()
    return bus

@pytest.fixture
def controller(mock_graph, mock_event_bus):
    return {ControllerName}(mock_graph, mock_event_bus)

class Test{ControllerName}:
    def test_initialization(self, controller, mock_graph, mock_event_bus):
        assert controller.graph == mock_graph
        assert controller.event_bus == mock_event_bus

    def test_subscribes_to_events(self, mock_event_bus):
        controller = {ControllerName}(MagicMock(), mock_event_bus)
        assert mock_event_bus.subscribe.call_count > 0

    def test_handle_primary_action(self, controller, mock_graph):
        controller.handle_action("test_data")
        mock_graph.some_method.assert_called_once()

    def test_emits_event_on_action(self, controller, mock_event_bus):
        controller.handle_action("test_data")
        mock_event_bus.emit.assert_called()
        call_args = mock_event_bus.emit.call_args[0]
        assert call_args[0] == "expected_event_name"

    def test_error_handling(self, controller, mock_graph):
        mock_graph.some_method.side_effect = RuntimeError("Test error")
        # Should not raise, should handle internally
        controller.handle_action("test_data")
```

## NodeController Testing

```python
class TestNodeController:
    def test_add_node_creates_visual_node(self, controller, mock_graph):
        node_type = "ClickNode"
        position = (100, 200)

        controller.add_node(node_type, position)

        mock_graph.add_node.assert_called_once()
        call_args = mock_graph.add_node.call_args
        assert call_args[0][0] == node_type
        assert call_args[0][1] == position

    def test_remove_node_emits_event(self, controller, mock_event_bus):
        node_id = "test_node_123"

        controller.remove_node(node_id)

        mock_event_bus.emit.assert_called()
        event_name = mock_event_bus.emit.call_args[0][0]
        assert event_name == "node_removed"

    @patch('casare_rpa.nodes.registry.NODE_REGISTRY')
    def test_get_available_node_types(self, mock_registry, controller):
        mock_registry.keys.return_value = [
            'ClickNode', 'TypeTextNode', 'ScreenshotNode'
        ]

        types = controller.get_available_node_types()

        assert len(types) == 3
        assert 'ClickNode' in types
```

## GraphController Testing

```python
class TestGraphController:
    def test_connect_nodes_validates_ports(self, controller):
        from_node = MagicMock()
        to_node = MagicMock()
        from_port = "output"
        to_port = "input"

        result = controller.connect_nodes(from_node, from_port, to_node, to_port)

        # Verify validation and connection logic
        assert result is True  # or assert specific behavior

    def test_auto_layout_positions_nodes(self, controller, mock_graph):
        nodes = [
            MagicMock(id='node1', category='control_flow'),
            MagicMock(id='node2', category='browser'),
            MagicMock(id='node3', category='data'),
        ]

        controller.auto_layout(nodes)

        # Verify nodes positioned without overlap
        positions = [n.position for n in nodes]
        # Assert positioning logic
```

## PropertyController Testing

```python
class TestPropertyController:
    def test_update_property_validates_type(self, controller):
        node = MagicMock()
        property_name = "timeout"
        value = "30000"  # String for INTEGER property

        result = controller.update_property(node, property_name, value)

        # Verify type conversion
        assert result is True
        # Assert property was converted to int

    def test_update_property_emits_change_event(self, controller, mock_event_bus):
        node = MagicMock(id='test_node')

        controller.update_property(node, 'name', 'New Name')

        mock_event_bus.emit.assert_called()
        event_data = mock_event_bus.emit.call_args[0][1]
        assert event_data['node_id'] == 'test_node'
        assert event_data['property'] == 'name'
```
