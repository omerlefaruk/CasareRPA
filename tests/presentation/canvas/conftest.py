"""
Canvas testing fixtures for CasareRPA.

Provides fixtures for testing NodeGraphQt integration, visual nodes,
and connection validation. Supports both headless and Qt environments.

Usage:
    def test_visual_node(mock_graph, visual_node_factory):
        node = visual_node_factory.create("test_node", ports=["input", "output"])
        mock_graph.add_node(node)
        assert node in mock_graph.nodes

    def test_connection_validation(connection_validator, visual_node_factory):
        source = visual_node_factory.create_typed_node(outputs={"data": DataType.STRING})
        target = visual_node_factory.create_typed_node(inputs={"value": DataType.STRING})
        result = connection_validator.validate_connection(source, "data", target, "value")
        assert result.is_valid
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING
from unittest.mock import Mock, MagicMock, PropertyMock

import pytest

# Try to import Qt components - graceful fallback for headless environments
try:
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication

    HAS_QT = True
except ImportError:
    HAS_QT = False
    QObject = object
    Signal = None

# Try to import NodeGraphQt
try:
    from NodeGraphQt import NodeGraph, BaseNode

    HAS_NODEGRAPHQT = True
except ImportError:
    HAS_NODEGRAPHQT = False
    NodeGraph = None
    BaseNode = None

# Import domain types (always available)
from casare_rpa.domain.value_objects.types import DataType, PortType

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.connections.connection_validator import (
        ConnectionValidator,
        ConnectionValidation,
    )
    from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# ============================================================================
# MOCK NODE GRAPH (Headless Fallback)
# ============================================================================


@dataclass
class MockPort:
    """
    Mock port for testing without NodeGraphQt.

    Simulates NodeGraphQt port behavior with name, type, and connections.
    """

    _name: str
    _port_type: str  # "input" or "output"
    _node: Optional["MockVisualNode"] = None
    _connected_ports: List["MockPort"] = field(default_factory=list)
    _color: Tuple[int, int, int, int] = (100, 100, 100, 255)
    _border_color: Tuple[int, int, int, int] = (70, 70, 70, 255)

    def name(self) -> str:
        """Get port name."""
        return self._name

    def node(self) -> Optional["MockVisualNode"]:
        """Get parent node."""
        return self._node

    def connected_ports(self) -> List["MockPort"]:
        """Get list of connected ports."""
        return self._connected_ports.copy()

    def connect_to(self, other: "MockPort") -> bool:
        """Connect to another port."""
        if other not in self._connected_ports:
            self._connected_ports.append(other)
            other._connected_ports.append(self)
            return True
        return False

    def disconnect_from(self, other: "MockPort") -> bool:
        """Disconnect from another port."""
        if other in self._connected_ports:
            self._connected_ports.remove(other)
            other._connected_ports.remove(self)
            return True
        return False

    @property
    def color(self) -> Tuple[int, int, int, int]:
        """Get port color."""
        return self._color

    @color.setter
    def color(self, value: Tuple[int, int, int, int]) -> None:
        """Set port color."""
        self._color = value

    @property
    def border_color(self) -> Tuple[int, int, int, int]:
        """Get port border color."""
        return self._border_color

    @border_color.setter
    def border_color(self, value: Tuple[int, int, int, int]) -> None:
        """Set port border color."""
        self._border_color = value


@dataclass
class MockVisualNode:
    """
    Mock visual node for testing without NodeGraphQt.

    Simulates VisualNode behavior with ports, properties, and type information.
    """

    _name: str = "MockNode"
    _node_id: str = ""
    _input_ports: Dict[str, MockPort] = field(default_factory=dict)
    _output_ports: Dict[str, MockPort] = field(default_factory=dict)
    _port_types: Dict[str, Optional[DataType]] = field(default_factory=dict)
    _properties: Dict[str, Any] = field(default_factory=dict)
    _casare_node: Any = None
    _position: Tuple[float, float] = (0.0, 0.0)
    _selected: bool = False

    def __post_init__(self) -> None:
        """Initialize default properties."""
        if "node_id" not in self._properties:
            self._properties["node_id"] = self._node_id or f"node_{id(self)}"
        if "status" not in self._properties:
            self._properties["status"] = "idle"

    def name(self) -> str:
        """Get node name."""
        return self._name

    def set_name(self, name: str) -> None:
        """Set node name."""
        self._name = name

    def input_ports(self) -> List[MockPort]:
        """Get list of input ports."""
        return list(self._input_ports.values())

    def output_ports(self) -> List[MockPort]:
        """Get list of output ports."""
        return list(self._output_ports.values())

    def get_input(self, name: str) -> Optional[MockPort]:
        """Get input port by name."""
        return self._input_ports.get(name)

    def get_output(self, name: str) -> Optional[MockPort]:
        """Get output port by name."""
        return self._output_ports.get(name)

    def add_input(self, name: str) -> MockPort:
        """Add an input port."""
        port = MockPort(_name=name, _port_type="input", _node=self)
        self._input_ports[name] = port
        return port

    def add_output(self, name: str) -> MockPort:
        """Add an output port."""
        port = MockPort(_name=name, _port_type="output", _node=self)
        self._output_ports[name] = port
        return port

    def add_typed_input(self, name: str, data_type: DataType = DataType.ANY) -> None:
        """Add typed input port."""
        self.add_input(name)
        self._port_types[name] = data_type

    def add_typed_output(self, name: str, data_type: DataType = DataType.ANY) -> None:
        """Add typed output port."""
        self.add_output(name)
        self._port_types[name] = data_type

    def add_exec_input(self, name: str = "exec_in") -> None:
        """Add execution input port."""
        self.add_input(name)
        self._port_types[name] = None  # None marks exec ports

    def add_exec_output(self, name: str = "exec_out") -> None:
        """Add execution output port."""
        self.add_output(name)
        self._port_types[name] = None  # None marks exec ports

    def get_port_type(self, port_name: str) -> Optional[DataType]:
        """Get data type for a port."""
        if port_name in self._port_types:
            return self._port_types[port_name]
        # Default: check for exec port patterns
        port_lower = port_name.lower()
        exec_names = {"exec_in", "exec_out", "exec", "true", "false", "loop_body"}
        if port_lower in exec_names or "exec" in port_lower:
            return None
        return DataType.ANY

    def is_exec_port(self, port_name: str) -> bool:
        """Check if port is an execution port."""
        return self.get_port_type(port_name) is None

    def get_property(self, name: str) -> Any:
        """Get property value."""
        return self._properties.get(name)

    def set_property(self, name: str, value: Any) -> None:
        """Set property value."""
        self._properties[name] = value

    def get_casare_node(self) -> Any:
        """Get linked CasareRPA node."""
        return self._casare_node

    def set_casare_node(self, node: Any) -> None:
        """Set linked CasareRPA node."""
        self._casare_node = node
        if hasattr(node, "node_id"):
            self._properties["node_id"] = node.node_id

    def pos(self) -> Tuple[float, float]:
        """Get node position."""
        return self._position

    def set_pos(self, x: float, y: float) -> None:
        """Set node position."""
        self._position = (x, y)

    def selected(self) -> bool:
        """Check if node is selected."""
        return self._selected

    def set_selected(self, selected: bool) -> None:
        """Set node selection state."""
        self._selected = selected


class MockNodeGraph:
    """
    Mock NodeGraph for testing without full NodeGraphQt.

    Provides minimal graph functionality for unit tests that don't
    require actual Qt rendering.
    """

    def __init__(self) -> None:
        """Initialize mock graph."""
        self._nodes: Dict[str, MockVisualNode] = {}
        self._registered_nodes: Dict[str, type] = {}
        self._session_data: Dict[str, Any] = {}

    @property
    def nodes(self) -> List[MockVisualNode]:
        """Get all nodes in graph."""
        return list(self._nodes.values())

    def all_nodes(self) -> List[MockVisualNode]:
        """Get all nodes in graph."""
        return list(self._nodes.values())

    def add_node(self, node: MockVisualNode) -> None:
        """Add node to graph."""
        node_id = node.get_property("node_id") or f"node_{len(self._nodes)}"
        self._nodes[node_id] = node

    def remove_node(self, node: MockVisualNode) -> None:
        """Remove node from graph."""
        node_id = node.get_property("node_id")
        if node_id in self._nodes:
            del self._nodes[node_id]

    def get_node_by_id(self, node_id: str) -> Optional[MockVisualNode]:
        """Get node by ID."""
        return self._nodes.get(node_id)

    def create_node(
        self, node_type: str, pos: Optional[List[float]] = None
    ) -> Optional[MockVisualNode]:
        """Create a node of the specified type."""
        if node_type not in self._registered_nodes:
            # Create a generic mock node
            node = MockVisualNode(_name=node_type.split(".")[-1])
        else:
            node_cls = self._registered_nodes[node_type]
            node = node_cls()

        if pos:
            node.set_pos(pos[0], pos[1])

        self.add_node(node)
        return node

    def register_node(self, node_cls: type) -> None:
        """Register a node class."""
        identifier = getattr(node_cls, "__identifier__", "casare_rpa")
        name = getattr(node_cls, "NODE_NAME", node_cls.__name__)
        self._registered_nodes[f"{identifier}.{name}"] = node_cls

    def selected_nodes(self) -> List[MockVisualNode]:
        """Get selected nodes."""
        return [n for n in self._nodes.values() if n.selected()]

    def clear_selection(self) -> None:
        """Clear all node selections."""
        for node in self._nodes.values():
            node.set_selected(False)

    def clear_session(self) -> None:
        """Clear the graph."""
        self._nodes.clear()
        self._session_data.clear()

    def delete_node(self, node: MockVisualNode) -> None:
        """Delete a node from the graph."""
        self.remove_node(node)


# ============================================================================
# VISUAL NODE FACTORY
# ============================================================================


class VisualNodeFactory:
    """
    Factory for creating test visual nodes.

    Supports both mock nodes (headless) and real NodeGraphQt nodes (with Qt).
    """

    def __init__(self, use_real_qt: bool = False) -> None:
        """
        Initialize factory.

        Args:
            use_real_qt: If True and Qt is available, create real NodeGraphQt nodes.
        """
        self._use_real_qt = use_real_qt and HAS_QT and HAS_NODEGRAPHQT
        self._node_counter = 0

    def create(
        self,
        name: str = "TestNode",
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        node_id: Optional[str] = None,
    ) -> MockVisualNode:
        """
        Create a basic test node.

        Args:
            name: Node name
            inputs: List of input port names
            outputs: List of output port names
            node_id: Optional node ID (auto-generated if not provided)

        Returns:
            MockVisualNode instance
        """
        self._node_counter += 1
        if node_id is None:
            node_id = f"test_node_{self._node_counter}"

        node = MockVisualNode(_name=name, _node_id=node_id)
        node._properties["node_id"] = node_id

        for port_name in inputs or []:
            node.add_input(port_name)

        for port_name in outputs or []:
            node.add_output(port_name)

        return node

    def create_typed_node(
        self,
        name: str = "TypedTestNode",
        inputs: Optional[Dict[str, DataType]] = None,
        outputs: Optional[Dict[str, DataType]] = None,
        node_id: Optional[str] = None,
    ) -> MockVisualNode:
        """
        Create a node with typed ports.

        Args:
            name: Node name
            inputs: Dict of input port names to DataTypes
            outputs: Dict of output port names to DataTypes
            node_id: Optional node ID

        Returns:
            MockVisualNode with typed ports
        """
        self._node_counter += 1
        if node_id is None:
            node_id = f"typed_node_{self._node_counter}"

        node = MockVisualNode(_name=name, _node_id=node_id)
        node._properties["node_id"] = node_id

        for port_name, data_type in (inputs or {}).items():
            node.add_typed_input(port_name, data_type)

        for port_name, data_type in (outputs or {}).items():
            node.add_typed_output(port_name, data_type)

        return node

    def create_exec_node(
        self,
        name: str = "ExecTestNode",
        exec_inputs: Optional[List[str]] = None,
        exec_outputs: Optional[List[str]] = None,
        data_inputs: Optional[Dict[str, DataType]] = None,
        data_outputs: Optional[Dict[str, DataType]] = None,
        node_id: Optional[str] = None,
    ) -> MockVisualNode:
        """
        Create a node with both exec and data ports.

        Args:
            name: Node name
            exec_inputs: List of exec input port names
            exec_outputs: List of exec output port names
            data_inputs: Dict of data input port names to DataTypes
            data_outputs: Dict of data output port names to DataTypes
            node_id: Optional node ID

        Returns:
            MockVisualNode with exec and data ports
        """
        self._node_counter += 1
        if node_id is None:
            node_id = f"exec_node_{self._node_counter}"

        node = MockVisualNode(_name=name, _node_id=node_id)
        node._properties["node_id"] = node_id

        # Add exec ports
        for port_name in exec_inputs or ["exec_in"]:
            node.add_exec_input(port_name)

        for port_name in exec_outputs or ["exec_out"]:
            node.add_exec_output(port_name)

        # Add data ports
        for port_name, data_type in (data_inputs or {}).items():
            node.add_typed_input(port_name, data_type)

        for port_name, data_type in (data_outputs or {}).items():
            node.add_typed_output(port_name, data_type)

        return node

    def create_start_node(self, node_id: Optional[str] = None) -> MockVisualNode:
        """Create a Start node (exec output only)."""
        return self.create_exec_node(
            name="Start",
            exec_inputs=[],
            exec_outputs=["exec_out"],
            node_id=node_id,
        )

    def create_end_node(self, node_id: Optional[str] = None) -> MockVisualNode:
        """Create an End node (exec input only)."""
        return self.create_exec_node(
            name="End",
            exec_inputs=["exec_in"],
            exec_outputs=[],
            node_id=node_id,
        )

    def create_branch_node(self, node_id: Optional[str] = None) -> MockVisualNode:
        """Create a Branch/If node (condition with true/false outputs)."""
        node = self.create_exec_node(
            name="Branch",
            exec_inputs=["exec_in"],
            exec_outputs=["true", "false"],
            data_inputs={"condition": DataType.BOOLEAN},
            node_id=node_id,
        )
        return node

    def create_loop_node(self, node_id: Optional[str] = None) -> MockVisualNode:
        """Create a For Loop node."""
        node = self.create_exec_node(
            name="ForLoop",
            exec_inputs=["exec_in"],
            exec_outputs=["loop_body", "completed"],
            data_inputs={"items": DataType.LIST},
            data_outputs={"item": DataType.ANY, "index": DataType.INTEGER},
            node_id=node_id,
        )
        return node


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_graph() -> MockNodeGraph:
    """
    Create a headless NodeGraph mock for testing.

    This fixture provides a lightweight graph that works without Qt,
    suitable for unit tests that don't require actual rendering.

    Returns:
        MockNodeGraph instance
    """
    return MockNodeGraph()


@pytest.fixture
def real_graph(qtbot) -> Optional[NodeGraph]:
    """
    Create a real NodeGraphQt graph for integration testing.

    Requires pytest-qt and full Qt environment.
    Returns None if NodeGraphQt is not available.

    Args:
        qtbot: pytest-qt fixture

    Returns:
        NodeGraph instance or None
    """
    if not HAS_NODEGRAPHQT:
        pytest.skip("NodeGraphQt not available")
        return None

    graph = NodeGraph()
    # Widget is created but not shown (headless)
    return graph


@pytest.fixture
def visual_node_factory() -> VisualNodeFactory:
    """
    Create a VisualNodeFactory for generating test nodes.

    Returns:
        VisualNodeFactory instance
    """
    return VisualNodeFactory(use_real_qt=False)


@pytest.fixture
def connection_validator():
    """
    Create a ConnectionValidator instance for testing.

    Returns:
        ConnectionValidator instance

    Raises:
        pytest.skip: If ConnectionValidator is not available
    """
    try:
        from casare_rpa.presentation.canvas.connections.connection_validator import (
            ConnectionValidator,
        )

        return ConnectionValidator()
    except ImportError:
        pytest.skip("ConnectionValidator not available")
        return None


@pytest.fixture
def mock_connection_validator() -> Mock:
    """
    Create a mock ConnectionValidator for unit tests.

    Useful when testing components that use ConnectionValidator
    without needing the full validation logic.

    Returns:
        Mock ConnectionValidator
    """
    mock = Mock()

    # Default to valid connections
    mock_validation = Mock()
    mock_validation.is_valid = True
    mock_validation.result = Mock()
    mock_validation.result.name = "VALID"
    mock_validation.message = "Connection valid"
    mock_validation.source_type = None
    mock_validation.target_type = None

    mock.validate_connection.return_value = mock_validation
    mock.get_compatible_ports.return_value = []
    mock.get_incompatible_ports.return_value = []

    return mock


@pytest.fixture
def sample_workflow_nodes(
    visual_node_factory: VisualNodeFactory,
) -> Dict[str, MockVisualNode]:
    """
    Create a sample set of interconnected workflow nodes.

    Returns dict with:
        - start: Start node
        - click: Click element node (browser action)
        - branch: Branch/If node
        - set_var: Set Variable node
        - end: End node

    Returns:
        Dict mapping node names to MockVisualNode instances
    """
    factory = visual_node_factory

    start = factory.create_start_node(node_id="start_1")

    click = factory.create_exec_node(
        name="ClickElement",
        exec_inputs=["exec_in"],
        exec_outputs=["exec_out"],
        data_inputs={"selector": DataType.STRING},
        data_outputs={"success": DataType.BOOLEAN},
        node_id="click_1",
    )

    branch = factory.create_branch_node(node_id="branch_1")

    set_var = factory.create_exec_node(
        name="SetVariable",
        exec_inputs=["exec_in"],
        exec_outputs=["exec_out"],
        data_inputs={"value": DataType.ANY},
        node_id="set_var_1",
    )

    end = factory.create_end_node(node_id="end_1")

    return {
        "start": start,
        "click": click,
        "branch": branch,
        "set_var": set_var,
        "end": end,
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_connected_nodes(
    factory: VisualNodeFactory,
    graph: MockNodeGraph,
    count: int = 3,
) -> List[MockVisualNode]:
    """
    Create a chain of connected nodes.

    Args:
        factory: VisualNodeFactory instance
        graph: MockNodeGraph to add nodes to
        count: Number of nodes to create

    Returns:
        List of created nodes in order
    """
    nodes = []
    for i in range(count):
        if i == 0:
            node = factory.create_start_node(node_id=f"chain_node_{i}")
        elif i == count - 1:
            node = factory.create_end_node(node_id=f"chain_node_{i}")
        else:
            node = factory.create_exec_node(
                name=f"Node_{i}",
                exec_inputs=["exec_in"],
                exec_outputs=["exec_out"],
                node_id=f"chain_node_{i}",
            )
        graph.add_node(node)
        nodes.append(node)

        # Connect to previous node
        if i > 0:
            prev_node = nodes[i - 1]
            prev_output = prev_node.get_output("exec_out")
            curr_input = node.get_input("exec_in")
            if prev_output and curr_input:
                prev_output.connect_to(curr_input)

    return nodes


def assert_valid_connection(
    validator,
    source_node: MockVisualNode,
    source_port: str,
    target_node: MockVisualNode,
    target_port: str,
) -> None:
    """
    Assert that a connection is valid.

    Args:
        validator: ConnectionValidator instance
        source_node: Source visual node
        source_port: Source port name
        target_node: Target visual node
        target_port: Target port name

    Raises:
        AssertionError: If connection is invalid
    """
    result = validator.validate_connection(
        source_node, source_port, target_node, target_port
    )
    assert result.is_valid, f"Expected valid connection, got: {result.message}"


def assert_invalid_connection(
    validator,
    source_node: MockVisualNode,
    source_port: str,
    target_node: MockVisualNode,
    target_port: str,
    expected_reason: Optional[str] = None,
) -> None:
    """
    Assert that a connection is invalid.

    Args:
        validator: ConnectionValidator instance
        source_node: Source visual node
        source_port: Source port name
        target_node: Target visual node
        target_port: Target port name
        expected_reason: Optional expected error message substring

    Raises:
        AssertionError: If connection is valid or reason doesn't match
    """
    result = validator.validate_connection(
        source_node, source_port, target_node, target_port
    )
    assert not result.is_valid, "Expected invalid connection, but it was valid"
    if expected_reason:
        assert (
            expected_reason.lower() in result.message.lower()
        ), f"Expected reason containing '{expected_reason}', got: {result.message}"
